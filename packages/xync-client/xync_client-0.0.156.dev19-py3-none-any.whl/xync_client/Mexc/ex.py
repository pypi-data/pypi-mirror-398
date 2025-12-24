from asyncio import run

from pyro_client.client.file import FileClient
from x_model import init_db
import requests
from xync_client.loader import TORM, NET_TOKEN

from xync_client.Abc.Ex import BaseExClient
from xync_client.Abc.xtype import PmEx, MapOfIdsList, GetAds
from xync_client.Mexc.etype import pm, ad

from xync_schema import xtype
from xync_schema import models
from xync_schema.models import Ex


class ExClient(BaseExClient):
    logo_headers = {
        "accept-language": "ru,en;q=0.9",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-site": "none",  # work from CURL, not work from aiohttp with no this header
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }
    logo_pre_url = "www.mexc.com/api/file/download"

    async def _pms(self, cur) -> list[pm.PmE]:
        pms = requests.get("https://p2p.mexc.com/api/payment/method", params={"currency": cur}).json()
        return [pm.PmE(**_pm) for _pm in pms["data"]]

    # 19: Список поддерживаемых валют тейкера
    async def curs(self) -> dict[str, xtype.CurEx]:  # {cur.ticker: cur}
        _curs = requests.get("https://p2p.mexc.com/api/common/currency").json()
        return {
            cur["currency"]: xtype.CurEx(exid=cur["currency"], ticker=cur["currency"], scale=cur["scale"])
            for cur in _curs["data"]
        }

    # 20: Список платежных методов
    async def pms(self, cur: models.Cur = None) -> dict[int | str, PmEx]:  # {pm.exid: pm}
        all_pms = {}
        for cur in (await self.curs()).values():
            pms = await self._pms(cur.ticker)
            for p in pms:
                all_pms[p.id] = PmEx(exid=p.id, name=p.name, logo=p.icon)
        return all_pms

    # 21: Список платежных методов по каждой валюте
    async def cur_pms_map(self) -> MapOfIdsList:  # {cur.exid: [pm.exid]}
        return {cur.exid: [pm.id for pm in await self._pms(cur.ticker)] for cur in (await self.curs()).values()}

    # 22: Список торгуемых монет (с ограничениям по валютам, если есть)
    async def coins(self) -> dict[str, xtype.CoinEx]:  # {coin.ticker: coin}
        coins = requests.get("https://p2p.mexc.com/api/common/coins").json()
        return {
            coin["coinId"]: xtype.CoinEx(exid=coin["coinId"], ticker=coin["coinName"], scale=coin["quantityScale"])
            for coin in coins["data"]
        }

    # 23: Список пар валюта/монет
    async def pairs(self) -> tuple[MapOfIdsList, MapOfIdsList]:
        coins = (await self.coins()).keys()
        curs = (await self.curs()).keys()
        p = {cur: {c for c in coins} for cur in curs}
        return p, p

    async def x2e_pm(self, xid: int, cur_id: int = None) -> str:  # pmex.exid
        if not self.pm_x2e.get(xid):
            fltr = dict(pm_id=xid, ex=self.ex)
            if cur_id:
                cur = await models.Cur[cur_id]
                pmexs = await models.PmEx.filter(**fltr)
                self.pm_x2e[xid] = [pmex.exid for pmex in pmexs if pmex.name.endswith(f"({cur.ticker})")][0]
            else:
                self.pm_x2e[xid] = (await models.PmEx.get(**fltr)).exid
        return self.pm_x2e[xid]

    async def x2e_req_ads(self, xreq: GetAds) -> ad.AdsReq:
        coin_id, _ = await self.x2e_coin(xreq.coin_id)
        cur_id, _, __ = await self.x2e_cur(xreq.cur_id)
        ereq = ad.AdsReq(
            coinId=coin_id,
            currency=cur_id,
            tradeType="SELL" if xreq.is_sell else "BUY",
            payMethod=",".join([await self.x2e_pm(pm_id, cur_id=xreq.cur_id) for pm_id in xreq.pm_ids]),
        )
        if xreq.amount:
            ereq.amount = str(xreq.amount)
        # todo: all kwargs
        return ereq

    # 24: Список объяв по (buy/sell, cur, coin, pm)
    async def _ads(
        self, req: ad.AdsReq, lim: int = None, vm_filter: bool = False, **kwargs
    ) -> list[ad.Ad]:  # {ad.id: ad}
        resp = requests.get("https://p2p.mexc.com/api/market", params=req.model_dump())
        return [ad.Ad(**_ad) for _ad in resp.json()["data"]]


async def main():
    _ = await init_db(TORM)
    async with FileClient(NET_TOKEN) as b:
        ex = await Ex.get(name="Mexc")
        cl: ExClient = ex.client(b)
        # await ex.curexs.filter(cur__ticker="EUR")
        # await cl.set_pms()
        # await cl.set_coinexs()
        coinex = await models.CoinEx.get(ex=cl.ex, coin_id=1)
        _ads = await cl.ads(coinex.exid, "RUB", True, ["5"])
        _cr = await cl.curs()
        _cn = await cl.coins()
        await cl.set_pairs()
        _pms = await cl.pms()
        await cl.stop()


if __name__ == "__main__":
    run(main())
