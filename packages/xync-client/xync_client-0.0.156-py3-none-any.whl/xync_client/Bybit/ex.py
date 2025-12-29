import json
from asyncio import run

from pyro_client.client.file import FileClient
from x_client import df_hdrs
from x_model import init_db
from xync_schema import models, xtype
from xync_schema.enums import AdStatus, AgentStatus
from xync_schema.models import Ex, Agent

from xync_client.Abc.Ex import BaseExClient
from xync_client.loader import NET_TOKEN
from xync_client.Bybit.etype import ad
from xync_client.Abc.xtype import PmEx, MapOfIdsList, GetAds
from xync_client.loader import TORM


class ExClient(BaseExClient):  # Bybit client
    host = "api2.bybit.com"
    headers = df_hdrs  # rewrite token for public methods
    agent: Agent = None

    async def _get_auth_cks(self) -> dict[str, str]:
        if not self.agent:
            self.agent = (
                await Agent.filter(actor__ex=self.ex, status__gt=AgentStatus.off).prefetch_related("actor").first()
            )
        return self.agent.auth["cookies"]

    @staticmethod
    def ad_status(status: int) -> AdStatus:
        return {
            10: AdStatus.active,
            20: AdStatus.defActive,
            30: AdStatus.soldOut,
        }[status]

    async def _get_config(self):
        resp = await self._get("/fiat/p2p/config/initial")
        return resp["result"]  # todo: tokens, pairs, ...

    # 19: Список поддерживаемых валют тейкера
    async def curs(self) -> dict[int, xtype.CurEx]:
        config = await self._get_config()
        return {
            c["currencyId"]: xtype.CurEx(exid=c["currencyId"], ticker=c["currencyId"], scale=c["scale"])
            for c in config["currencies"]
        }

    # 20: Список платежных методов
    async def pms(self, cur: models.Cur = None) -> dict[int | str, PmEx]:
        self.session.cookie_jar.update_cookies(await self._get_auth_cks())
        pms = await self._post("/fiat/otc/configuration/queryAllPaymentList/")
        self.session.cookie_jar.clear()

        pms = pms["result"]["paymentConfigVo"]
        return {pm["paymentType"]: PmEx(exid=pm["paymentType"], name=pm["paymentName"]) for pm in pms}

    # 21: Список платежных методов по каждой валюте
    async def cur_pms_map(self) -> MapOfIdsList:
        self.session.cookie_jar.update_cookies(await self._get_auth_cks())
        pms = await self._post("/fiat/otc/configuration/queryAllPaymentList/")
        return json.loads(pms["result"]["currencyPaymentIdMap"])

    # 22: Список торгуемых монет (с ограничениям по валютам, если есть)
    async def coins(self) -> dict[str, xtype.CoinEx]:
        config = await self._get_config()
        coinexs = {}
        for c in config["symbols"]:
            coinexs[c["tokenId"]] = xtype.CoinEx(
                exid=c["tokenId"], ticker=c["tokenId"], minimum=c["tokenMinQuote"], scale=c["token"]["scale"]
            )
        return coinexs

    # 23: Список пар валюта/монет
    async def pairs(self) -> tuple[MapOfIdsList, MapOfIdsList]:
        config = await self._get_config()
        cc: dict[str, set[str]] = {}
        for c in config["symbols"]:
            cc[c["currencyId"]] = cc.get(c["currencyId"], set()) | {c["tokenId"]}
        return cc, cc

    # 24: Список объяв по (buy/sell, cur, coin, pm)
    async def _ads(self, req: ad.AdsReq, post_pmexs: set[models.PmEx] = None) -> list[ad.Ad]:
        if post_pmexs:
            req.payment = []
            req.size = str(min(1000, int(req.size) * 25))
        res = await self._post("/fiat/otc/item/online/", req.model_dump())
        ads = [ad.Ad(**_ad) for _ad in res["result"]["items"]]
        if post_pmexs:
            post_pmexids = {p.exid for p in post_pmexs}
            ads = [
                ad
                for ad in ads
                if (set(ad.payments) & post_pmexids or [True for px in post_pmexs if px.pm.norm in ad.remark.lower()])
            ]
        return ads


async def main():
    _ = await init_db(TORM, True)
    ex = await Ex.get(name="Bybit")
    bot: FileClient = FileClient(NET_TOKEN)
    # await bot.start()
    cl = ExClient(ex, bot)
    # await cl.set_pms()
    # await cl.set_coins()
    # await cl.set_pairs()
    x_ads_req = GetAds(coin_id=1, cur_id=1, is_sell=True, pm_ids=[330, 366, 1853], amount=1000)
    _ads = await cl.ads(x_ads_req)
    # await bot.stop()
    await cl.close()


if __name__ == "__main__":
    run(main())
