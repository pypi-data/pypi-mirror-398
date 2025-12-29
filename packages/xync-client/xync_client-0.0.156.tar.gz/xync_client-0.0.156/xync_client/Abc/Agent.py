import logging
from abc import abstractmethod
from asyncio import create_task, sleep
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel
from pyro_client.client.file import FileClient
from x_client import df_hdrs
from x_client.aiohttp import Client as HttpClient
from xync_bot import XyncBot
from xync_client.Abc.PmAgent import PmAgentClient

from xync_client.Abc.InAgent import BaseInAgentClient

from xync_client.Bybit.etype.order import TakeAdReq
from xync_schema import models
from xync_schema.models import OrderStatus, Coin, Cur, Ad, AdStatus, Actor, Agent
from xync_schema.xtype import BaseAd

from xync_client.Abc.Ex import BaseExClient
from xync_client.Abc.xtype import CredExOut, BaseOrderReq, BaseAdUpdate, AdUpd, GetAds
from xync_client.Gmail import GmClient


class BaseAgentClient(HttpClient, BaseInAgentClient):
    actor: Actor
    agent: Agent
    bbot: XyncBot
    fbot: FileClient
    ex_client: BaseExClient
    orders: dict[int, tuple[models.Order, BaseModel]] = {}  # pending
    pm_clients: dict[int, PmAgentClient]  # {pm_id: PmAgentClient}
    api: HttpClient
    cred_x2e: dict[int, int] = {}
    cred_e2x: dict[int, int] = {}

    def __init__(
        self,
        agent: Agent,  # agent.actor.person.user
        ex_client: BaseExClient,
        fbot: FileClient,
        bbot: XyncBot,
        pm_clients: dict[int, PmAgentClient] = None,
        headers: dict[str, str] = df_hdrs,
        cookies: dict[str, str] = None,
        proxy: models.Proxy = None,
    ):
        self.bbot = bbot
        self.fbot = fbot
        self.agent: Agent = agent
        self.actor: Actor = agent.actor
        self.gmail = agent.actor.person.user.gmail and GmClient(agent.actor.person.user)
        self.ex_client: BaseExClient = ex_client
        self.pm_clients: dict[int, PmAgentClient] = defaultdict()
        super().__init__(self.actor.ex.host_p2p, headers, cookies, proxy)  #  and proxy.str()
        # start
        create_task(self.start())

    async def x2e_cred(self, cred_id: int) -> int:  # cred.exid
        if not self.cred_x2e.get(cred_id):
            self.cred_x2e[cred_id] = (await models.CredEx.get(cred_id=cred_id)).exid
            self.cred_e2x[self.cred_x2e[cred_id]] = cred_id
        return self.cred_x2e[cred_id]

    async def e2x_cred(self, exid: int) -> int:  # cred.id
        if not self.cred_e2x.get(exid):
            self.cred_e2x[exid] = (await models.CredEx.get(exid=exid, ex=self.ex_client.ex)).cred_id
            self.cred_x2e[self.cred_e2x[exid]] = exid
        return self.cred_e2x[exid]

    async def start(self):
        if self.agent.status & 1:  # race
            for race in await models.Race.filter(started=True, road__ad__maker_id=self.agent.actor_id).prefetch_related(
                "road__ad__pair_side__pair__cur", "road__credexs__cred"
            ):
                create_task(self.racing(race))
        if self.agent.status & 2:  # listen
            await self.start_listen()

    async def racing(self, race: models.Race):
        pair = race.road.ad.pair_side.pair
        taker_side: int = not race.road.ad.pair_side.is_sell
        # конвертим наши параметры гонки в ex-овые для конкретной биржи текущего агента
        coinex: models.CoinEx = await models.CoinEx.get(coin_id=pair.coin_id, ex=self.actor.ex).prefetch_related("coin")
        curex: models.CurEx = await models.CurEx.get(cur_id=pair.cur_id, ex=self.actor.ex).prefetch_related("cur")
        creds = [c.cred for c in race.road.credexs]
        pm_ids = [pm.id for pm in race.road.ad.pms]
        pmexs: list[models.PmEx] = [pmex for pm in race.road.ad.pms for pmex in pm.pmexs if pmex.ex_id == 4]
        post_pm_ids = {c.cred.ovr_pm_id for c in race.road.credexs if c.cred.ovr_pm_id}
        post_pmexs = set(await models.PmEx.filter(pm_id__in=post_pm_ids, ex=self.actor.ex).prefetch_related("pm"))

        k = (-1) ** taker_side  # on_buy=1, on_sell=-1
        sleep_sec = 3  # 1 if set(pms) & {"volet"} and coinex.coin_id == 1 else 5
        _lstat, volume = None, 0

        # погнали цикл гонки
        while self.actor.person.user.status > 0:  # todo: separate agents, not whole user.activity
            # подгружаем из бд обновления по текущей гонке
            await race.refresh_from_db()
            if not race.started:  # пока выключена
                await sleep(5)
                continue

            # конверт бд int фильтровочной суммы в float конкретной биржи
            amt = race.filter_amount * 10**-curex.cur.scale if race.filter_amount else None
            ceils = await self.get_ceils(coinex, curex, pmexs, 0.003, 0, amt, post_pmexs)
            race.ceil = int(ceils[taker_side] * 10**curex.scale)
            await race.save()

            last_vol = volume
            if taker_side:  # гонка в стакане продажи - мы покупаем монету за ФИАТ
                fiat = max(await models.Fiat.filter(cred_id__in=[c.id for c in creds]), key=lambda x: x.amount)
                volume = (fiat.amount * 10**-curex.cur.scale) / (race.road.ad.price * 10**-curex.scale)
            else:  # гонка в стакане покупки - мы продаем МОНЕТУ за фиат
                asset = await models.Asset.get(addr__actor=self.actor, addr__coin_id=coinex.coin_id)
                volume = asset.free * 10**-coinex.scale
            volume = str(round(volume, coinex.scale))
            get_ads_req = GetAds(
                coin_id=pair.coin_id, cur_id=pair.cur_id, is_sell=bool(taker_side), pm_ids=pm_ids, amount=amt, limit=50
            )
            try:
                ads: list[Ad] = await self.ex_client.ads(get_ads_req)
            except Exception:
                await sleep(1)
                ads: list[Ad] = await self.ads(coinex, curex, taker_side, pmexs, amt, 50, race.vm_filter, post_pmexs)

            self.overprice_filter(ads, race.ceil * 10**-curex.scale, k)  # обрезаем сверху все ads дороже нашего потолка

            if not ads:
                print(coinex.exid, curex.exid, taker_side, "no ads!")
                await sleep(15)
                continue
            # определяем наше текущее место в уже обрезанном списке ads
            if not (cur_plc := [i for i, ad in enumerate(ads) if int(ad.userId) == self.actor.exid]):
                logging.warning(f"No racing in {pmexs[0].name} {'-' if taker_side else '+'}{coinex.exid}/{curex.exid}")
                await sleep(15)
                continue
            (cur_plc,) = cur_plc  # может упасть если в списке > 1 наш ad
            [(await self.ex_client.cond_load(ad, race.road.ad.pair_side, True))[0] for ad in ads[:cur_plc]]
            # rivals = [
            #     (await models.RaceStat.update_or_create({"place": plc, "price": ad.price, "premium": ad.premium}, ad=ad))[
            #         0
            #     ]
            #     for plc, ad in enumerate(rads)
            # ]
            mad: Ad = ads.pop(cur_plc)
            # if (
            #     not (lstat := lstat or await race.stats.order_by("-created_at").first())
            #     or lstat.place != cur_plc
            #     or lstat.price != float(mad.price)
            #     or set(rivals) != set(await lstat.rivals)
            # ):
            #     lstat = await models.RaceStat.create(race=race, place=cur_plc, price=mad.price, premium=mad.premium)
            #     await lstat.rivals.add(*rivals)
            if not ads:
                await sleep(60)
                continue
            if not (cad := self.get_cad(ads, race.ceil * 10**-curex.scale, k, race.target_place, cur_plc)):
                continue
            new_price = round(float(cad.price) - k * step(mad, cad, curex.scale), curex.scale)
            if (
                float(mad.price) == new_price and volume == last_vol
            ):  # Если место уже нужное или нужная цена и так уже стоит
                print(
                    f"{'v' if taker_side else '^'}{mad.price}",
                    end=f"[{race.ceil * 10**-curex.scale}+{cur_plc}] ",
                    flush=True,
                )
                await sleep(sleep_sec)
                continue
            if cad.priceType:  # Если цена конкурента плавающая, то повышаем себе не цену, а %
                new_premium = (float(mad.premium) or float(cad.premium)) - k * step(mad, cad, 2)
                # if float(mad.premium) == new_premium:  # Если нужный % и так уже стоит
                #     if mad.priceType and cur_plc != race.target_place:
                #         new_premium -= k * step(mad, cad, 2)
                #     elif volume == last_vol:
                #         print(end="v" if taker_side else "^", flush=True)
                #         await sleep(sleep_sec)
                #         continue
                mad.premium = str(round(new_premium, 2))
            mad.priceType = cad.priceType
            mad.quantity = volume
            mad.maxAmount = str(2_000_000 if curex.cur_id == 1 else 40_000)
            # req = AdUpdateRequest.model_validate(
            #     {
            #         **mad.model_dump(),
            #         "price": str(round(new_price, curex.scale)),
            #         "paymentIds": [str(cx.exid) for cx in race.road.credexs],
            #     }
            # )
            # try:
            #     print(
            #         f"c{race.ceil * 10**-curex.scale}+{cur_plc} {coinex.coin.ticker}{'-' if taker_side else '+'}{req.price}{curex.cur.ticker}"
            #         f"{[pm.norm for pm in race.road.ad.pms]}{f'({req.premium}%)' if req.premium != '0' else ''} "
            #         f"t{race.target_place} ;",
            #         flush=True,
            #     )
            #     _res = self.ad_upd(req)
            # except FailedRequestError as e:
            #     if ExcCode(e.status_code) == ExcCode.FixPriceLimit:
            #         if limits := re.search(
            #             r"The fixed price set is lower than ([0-9]+\.?[0-9]{0,2}) or higher than ([0-9]+\.?[0-9]{0,2})",
            #             e.message,
            #         ):
            #             req.price = limits.group(1 if taker_side else 2)
            #             if req.price != mad.price:
            #                 _res = self.ad_upd(req)
            #         else:
            #             raise e
            #     elif ExcCode(e.status_code) == ExcCode.InsufficientBalance:
            #         asset = await models.Asset.get(addr__actor=self.actor, addr__coin_id=coinex.coin_id)
            #         req.quantity = str(round(asset.free * 10**-coinex.scale, coinex.scale))
            #         _res = self.ad_upd(req)
            #     elif ExcCode(e.status_code) == ExcCode.RareLimit:
            #         if not (
            #             sads := [
            #                 ma
            #                 for ma in self.my_ads(False)
            #                 if (
            #                     ma.currencyId == curex.exid
            #                     and ma.tokenId == coinex.exid
            #                     and taker_side != ma.side
            #                     and set(ma.payments) == set([pe.exid for pe in pmexs])
            #                 )
            #             ]
            #         ):
            #             logging.error(f"Need reserve Ad {'sell' if taker_side else 'buy'} {coinex.exid}/{curex.exid}")
            #             await sleep(90)
            #             continue
            #         self.ad_del(ad_id=int(mad.id))
            #         req.id = sads[0].id
            #         req.actionType = "ACTIVE"
            #         self.api.update_ad(**req.model_dump())
            #         logging.warning(f"Ad#{mad.id} recreated")
            #     # elif ExcCode(e.status_code) == ExcCode.Timestamp:
            #     #     await sleep(3)
            #     else:
            #         raise e
            # except (ReadTimeoutError, ConnectionDoesNotExistError):
            #     logging.warning("Connection failed. Restarting..")
            await sleep(6)

    async def get_books(
        self,
        coinex: models.CoinEx,
        curex: models.CurEx,
        pmexs: list[models.PmEx],
        amount: int,
        post_pmexs: list[models.PmEx] = None,
    ) -> tuple[list[Ad], list[Ad]]:
        buy: list[Ad] = await self.ads(coinex, curex, False, pmexs, amount, 40, False, post_pmexs)
        sell: list[Ad] = await self.ads(coinex, curex, True, pmexs, amount, 30, False, post_pmexs)
        return buy, sell

    async def get_spread(
        self, bb: list[Ad], sb: list[Ad], perc: float, place: int = 0
    ) -> tuple[tuple[float, float], float, int] | None:
        if len(bb) and len(sb):
            buy_price, sell_price = float(bb[place].price), float(sb[place].price)
            half_spread = (buy_price - sell_price) / (buy_price + sell_price)
            if half_spread * 2 < perc:
                return await self.get_spread(bb, sb, perc, place)
            return (buy_price, sell_price), half_spread, place
        return None

    async def get_ceils(
        self,
        coinex: models.CoinEx,
        curex: models.CurEx,
        pmexs: list[models.PmEx],
        min_prof=0.02,
        place: int = 0,
        amount: int = None,
        post_pmexs: set[models.PmEx] = None,
    ) -> tuple[float, float]:  # todo: refact to Pairex
        for pmc_id in {pmx.pm_id for pmx in pmexs} | set(self.pm_clients.keys()):
            if ceils := self.pm_clients[pmc_id].get_ceils():
                return ceils
        bb, sb = await self.get_books(coinex, curex, pmexs, amount, post_pmexs)
        perc = list(post_pmexs or pmexs)[0].pm.fee * 0.0001 + min_prof
        (bf, sf), _hp, _zplace = await self.get_spread(bb, sb, perc, place)
        mdl = (bf + sf) / 2  # middle price
        bc, sc = mdl + mdl * (perc / 2), mdl - mdl * (perc / 2)
        return bc, sc

    async def mad_upd(self, mad: Ad, attrs: dict, cxids: list[str]):
        if not [setattr(mad, k, v) for k, v in attrs.items() if getattr(mad, k) != v]:
            print(end="v" if mad.side else "^", flush=True)
            return await sleep(5)
        # req = AdUpdateRequest.model_validate({**mad.model_dump(), "paymentIds": cxids})
        # try:
        #     return self.ad_upd(req)
        # except FailedRequestError as e:
        #     if ExcCode(e.status_code) == ExcCode.FixPriceLimit:
        #         if limits := re.search(
        #             r"The fixed price set is lower than ([0-9]+\.?[0-9]{0,2}) or higher than ([0-9]+\.?[0-9]{0,2})",
        #             e.message,
        #         ):
        #             return await self.mad_upd(mad, {"price": limits.group(1 if mad.side else 2)}, cxids)
        #     elif ExcCode(e.status_code) == ExcCode.RareLimit:
        #         await sleep(180)
        #     else:
        #         raise e
        # except (ReadTimeoutError, ConnectionDoesNotExistError):
        #     logging.warning("Connection failed. Restarting..")
        # print("-" if mad.side else "+", end=req.price, flush=True)
        await sleep(60)

    def overprice_filter(self, ads: list[Ad], ceil: float, k: Literal[-1, 1]):
        # вырезаем ads с ценами выше потолка
        if ads and (ceil - float(ads[0].price)) * k > 0:
            if int(ads[0].userId) != self.actor.exid:
                ads.pop(0)
                self.overprice_filter(ads, ceil, k)

    def get_cad(self, ads: list[Ad], ceil: float, k: Literal[-1, 1], target_place: int, cur_plc: int) -> Ad:
        if not ads:
            return None
        # чью цену будем обгонять, предыдущей или слещующей объявы?
        # cad: Ad = ads[place] if cur_plc > place else ads[cur_plc]
        # переделал пока на жесткую установку целевого места, даже если текущее выше:
        if len(ads) <= target_place:
            logging.error(f"target place {target_place} not found in ads {len(ads)}-lenght list")
            target_place = len(ads) - 1
        cad: Ad = ads[target_place]
        # а цена обгоняемой объявы не выше нашего потолка?
        if (float(cad.price) - ceil) * k <= 0:
            # тогда берем следующую
            ads.pop(target_place)
            cad = self.get_cad(ads, ceil, k, target_place, cur_plc)
        # todo: добавить фильтр по лимитам min-max
        return cad

    # 0: Получшение ордеров в статусе status, по монете coin, в валюте coin, в направлении is_sell: bool
    @abstractmethod
    async def get_orders(
        self, status: OrderStatus = OrderStatus.created, coin: Coin = None, cur: Cur = None, is_sell: bool = None
    ) -> list: ...

    # 1: [T] Запрос на старт сделки
    @abstractmethod
    async def order_request(self, order_req: BaseOrderReq) -> dict: ...

    # async def start_order(self, order: Order) -> OrderOutClient:
    #     return OrderOutClient(self, order)

    # 1N: [M] - Запрос мейкеру на сделку
    @abstractmethod
    async def order_request_ask(self) -> dict: ...  # , ad: Ad, amount: float, pm: Pm, taker: Agent

    # 2N: [M] - Уведомление об отмене запроса на сделку
    @abstractmethod
    async def request_canceled_notify(self) -> int: ...  # id

    # # # Cred
    @property
    @abstractmethod
    def fiat_pyd(self) -> BaseModel.__class__: ...

    @abstractmethod
    def fiat_args2pyd(
        self, exid: int | str, cur: str, detail: str, name: str, fid: int, typ: str, extra=None
    ) -> fiat_pyd: ...

    # 25: Список реквизитов моих платежных методов
    @abstractmethod
    async def creds(self) -> list[CredExOut]: ...  # {credex.exid: {cred}}

    # Создание реквизита на бирже
    async def cred_new(self, cred: models.Cred) -> models.CredEx: ...

    # await models.Actor.get_or_create({"name": cred.exid}, ex=self.ex_client.ex, exid=self.agent.actor.exid)
    # cred_db: Cred = (await self.cred_pyd2db(cred, self.agent.user_id))[0]
    # if not (credex := models.CredEx.get_or_none(cred=cred_db, ex=self.agent.ex)):
    #     credex, _ = models.CredEx.update_or_create({}, cred=cred_db, ex=self.agent.ex)
    # return credex

    # 27: Редактирование реквизита моего платежного метода
    @abstractmethod
    async def cred_upd(self, cred: models.Cred, exid: int) -> models.CredEx: ...

    # 28: Удаление реквизита моего платежного метода
    @abstractmethod
    async def cred_del(self, exid: int) -> int: ...

    # # # Ad
    # 29: Список моих объявлений
    @abstractmethod
    async def my_ads(self, status: AdStatus = None) -> list[BaseAd]: ...

    @abstractmethod
    async def x2e_req_ad_upd(self, xreq: AdUpd) -> BaseAdUpdate: ...

    # 30: Создание объявления
    @abstractmethod
    async def ad_new(self, ad: BaseAd) -> Ad: ...

    async def ad_upd(self, xreq: AdUpd) -> Ad:
        xreq.credexs = await models.CredEx.filter(
            ex_id=self.actor.ex_id,
            cred__pmcur__pm_id__in=xreq.pm_ids,
            cred__pmcur__cur_id=xreq.cur_id,
            cred__person_id=self.actor.person_id,
        ).prefetch_related("cred__pmcur")
        # xreq.credexs = credexs
        ereq = await self.x2e_req_ad_upd(xreq)
        return await self._ad_upd(ereq)

    # 31: Редактирование объявления
    @abstractmethod
    async def _ad_upd(self, ad: BaseAdUpdate) -> Ad: ...

    # 32: Удаление
    @abstractmethod
    async def ad_del(self, ad_id: int) -> bool: ...

    # 33: Вкл/выкл объявления
    @abstractmethod
    async def ad_switch(self, offer_id: int, active: bool) -> bool: ...

    # 34: Вкл/выкл всех объявлений
    @abstractmethod
    async def ads_switch(self, active: bool) -> bool: ...

    # # # User
    # 35: Получить объект юзера по его ид
    @abstractmethod
    async def get_user(self, user_id) -> dict: ...

    # 36: Отправка сообщения юзеру с приложенным файлом
    @abstractmethod
    async def send_user_msg(self, msg: str, file=None) -> bool: ...

    # 37: (Раз)Блокировать юзера
    @abstractmethod
    async def block_user(self, is_blocked: bool = True) -> bool: ...

    # 38: Поставить отзыв юзеру
    @abstractmethod
    async def rate_user(self, positive: bool) -> bool: ...

    # 39: Балансы моих монет
    @abstractmethod
    async def my_assets(self) -> dict: ...

    @abstractmethod
    async def take_ad(self, req: TakeAdReq): ...

    # Сохранение объявления (с Pm/Cred-ами) в бд
    # async def ad_pydin2db(self, ad_pydin: AdSaleIn | AdBuyIn) -> Ad:
    #     ad_db = await self.ex_client.ad_pydin2db(ad_pydin)
    #     await ad_db.credexs.add(*getattr(ad_pydin, "credexs_", []))
    #     await ad_db.pmexs.add(*getattr(ad_pydin, "pmexs_", []))
    #     return ad_db

    # @staticmethod
    # async def cred_e2db(cred_in: BaseUpd, banks: list[str] = None) -> bool:
    #     cred_db, _ = await models.Cred.update_or_create(**cred_in.df_unq())
    #     credex_in = models.CredEx.validate({"exid": cred_in.id, "cred_id": cred_db.id})
    #     credex_db, _ = await models.CredEx.update_or_create(**credex_in.df_unq())
    #     if banks:  # only for SBP
    #         await cred_db.banks.add(*[await PmExBank.get(exid=b) for b in banks])
    #     return True

    @abstractmethod
    async def _start_listen(self): ...

    @abstractmethod
    async def load_pending_orders(self): ...

    async def start_listen(self):
        create_task(self._start_listen())
        await self.load_pending_orders()


def step_is_need(mad, cad) -> bool:
    # todo: пока не решен непонятный кейс, почему то конкурент по всем параметрам слабже, но в списке ранжируется выше.
    #  текущая версия: recentExecuteRate округляется до целого, но на бэке байбита его дробная часть больше
    return (
        bool(set(cad.authTag) & {"VA2", "BA"})
        or cad.recentExecuteRate > mad.recentExecuteRate
        or (
            cad.recentExecuteRate
            == mad.recentExecuteRate  # and cad.finishNum > mad.finishNum # пока прибавляем для равных
        )
    )


def step(mad, cad, scale: int = 2) -> float:
    return float(int(step_is_need(mad, cad)) * 10**-scale).__round__(scale)
