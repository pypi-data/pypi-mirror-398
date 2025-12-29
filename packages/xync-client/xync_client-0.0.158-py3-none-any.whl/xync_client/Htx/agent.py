import re
from json import dumps
from time import time
from urllib.parse import quote

from aiohttp import ClientResponse
from pyro_client.client.file import FileClient
from x_client import df_hdrs
from x_client.aiohttp import Client
from xync_bot import XyncBot

from xync_client.Abc.xtype import AdUpd, GetAds
from xync_client.Htx.etype.order import OrderItem, OrderFull
from xync_client.loader import NET_TOKEN, PAY_TOKEN, TORM

from xync_schema.enums import AdStatus, PmType, OrderStatus
from xync_schema import models
from xync_client.Abc.Agent import BaseAgentClient
from xync_client.Htx.etype import test, ad

import logging

url_ads_req = "https://otc-cf.huobi.com/v1/data/trade-market"
url_ads_web = "https://www.huobi.com/en-us/fiat-crypto/trade/"
url_my_ads = "https://otc-api.trygofast.com/v1/data/trade-list?pageSize=50"
url_my_ad = "/-/x/otc/v1/otc/trade/"  # + id
url_my_bals = "https://www.huobi.com/-/x/otc/v1/capital/balance"
url_paccs = "https://www.huobi.com/-/x/otc/v1/user/receipt-account"


class Public(Client):
    url_ads_web = "https://www.huobi.com/en-us/fiat-crypto/trade/"


class AgentClient(BaseAgentClient):
    headers = {"portal": "web"} | df_hdrs

    async def login(self):
        t = int(time() * 1000)
        resp = await self._get("/-/x/uc/uc/open/ticket/get", {"t": t})
        if resp.get("data") is None:
            ...
        if ticket := resp["data"].get("ticket"):
            resp = await self._post("/-/x/otc/v1/user/login", form_data={"ticket": ticket, "type": "WEB"})
            if resp["success"]:
                self.agent.auth["headers"]["Token"] = resp["data"]
                await self.agent.save(update_fields=["auth"])
                self.session.headers["Token"] = resp["data"]

    async def creds(self) -> list[test.CredEpyd]:
        resp = await self._get("/-/x/otc/v1/user/receipt-account")
        return [test.CredEpyd(**cred) for cred in resp["data"]]

    async def cred_del(self, cred_id: int) -> int:
        data = {"id": str(cred_id), "password": self.actor.agent.auth["password"]}

        cred_del = await self._post("/-/x/otc/v1/user/receipt-account/remove", data=data)
        if cred_del["message"] == "Success":
            await (await models.CredEx.get(exid=cred_id)).delete()
            return cred_id
        else:
            logging.error(cred_del)

    async def dynamicModelInfo(self, pids: str):
        resp = await self._get("/-/x/otc/v1/user/receipt-account/dynamicModelInfo", {"payMethodIds": pids})
        return resp["data"]["modelFields"]

    async def cred_new(self, cred: models.Cred) -> models.CredEx:
        pmcur = await cred.pmcur
        exid = str(await models.PmEx.get(pm_id=pmcur.pmex_exid, ex=self.ex_client.ex).values_list("exid", flat=True))
        field_map = {
            "payee": "name",
            "bank": "extra",
            "sub_bank": "extra",
            "pay_account": "detail",
        }
        fields = {f["fieldType"]: f["fieldId"] for f in await self.dynamicModelInfo(exid)}
        # Данные, где modelFields теперь список ModelField
        data = {
            "payMethod": exid,
            "password": self.actor.agent.auth["password"],
            "modelFields": dumps(
                [{"fieldId": fid, "fieldType": ft, "value": getattr(cred, field_map[ft])} for ft, fid in fields.items()]
            ),
        }
        resp = await self._post("/-/x/otc/v1/user/receipt-account/addByDynamicModel", data=data)
        if not resp["success"]:
            logging.exception(resp["message"])
        res = test.Result(**resp)
        credex, _ = await models.CredEx.update_or_create({"cred": cred, "ex": self.ex}, exid=res.data.id)
        return credex

    async def cred_upd(self, cred: models.Cred, exid: int) -> models.CredEx:
        pmcur = await cred.pmcur
        _exid = str(await models.PmEx.get(pm_id=pmcur.pmex_exid, ex=self.ex_client.ex).values_list("exid", flat=True))
        field_map = {
            "payee": "name",
            "bank": "extra",
            "sub_bank": "extra",
            "pay_account": "detail",
        }
        fields = {f["fieldType"]: f["fieldId"] for f in await self.dynamicModelInfo(_exid)}
        # Данные, где modelFields теперь список ModelField
        data = {
            "payMethod": exid,
            "password": self.actor.agent.auth["headers"]["password"],
            "modelFields": dumps(
                [{"fieldId": fid, "fieldType": ft, "value": getattr(cred, field_map[ft])} for ft, fid in fields.items()]
            ),
            "id": exid,
        }
        await self._post("/-/x/otc/v1/user/receipt-account/modifyByDynamicModel", data=data)
        cred_ids = await models.Cred.filter(credexs__exid=exid).values_list("id", flat=True)
        await models.Cred.filter(id__in=cred_ids).update(name=cred.name, detail=cred.detail)
        return await models.CredEx.filter(exid=exid).first()

    # 0
    async def get_orders(
        self,
        stauts: OrderStatus = OrderStatus.created,
        coin: models.Coin = None,
        cur: models.Cur = None,
        is_sell: bool = None,
    ) -> list[OrderItem]:
        resp = await self._get("/-/x/otc/v1/trade/order/process", {"needTradeCount": "true"})
        if resp["success"]:
            return [OrderItem(**o) for o in resp["data"]]
        return []

    async def get_order(self, oid: int) -> OrderFull | None:
        resp = await self._get("/-/x/otc/v1/trade/order", {"orderId": oid})
        if resp["success"]:
            o = OrderFull(**resp["data"])
            return o
        return None

    async def recv(self, order: OrderItem):
        if order.orderStatus:
            ...
        else:
            ...

    async def start_listen(self):
        """Фоновая задача для ловли входящих ордеров"""
        while True:
            [await self.recv(o) for o in await self.get_orders()]
            await sleep(9)

    async def order_request(self, ad_id: int, amount: float) -> dict:
        pass

    async def my_fiats(self, cur: models.Cur = None) -> list[dict]:
        pass

    # async def fiat_new(self, fiat: FiatNew) -> Fiat.pyd():
    #     pass

    async def fiat_upd(self, detail: str = None, typ: PmType = None) -> bool:
        pass

    async def fiat_del(self, fiat_id: int) -> bool:
        pass

    async def my_ads(self) -> list[dict]:
        res = await self._get(url_my_ads)
        ads: [] = res["data"]
        if (pages := res["totalPage"]) > 1:
            for p in range(2, pages + 1):
                ads += (await self._get(url_my_ads, {"currPage": p})).get("data", False)
        return ads

    async def ad_new(
        self,
        coin: models.Coin,
        cur: models.Cur,
        is_sell: bool,
        pms: list[models.Pm],
        price: float,
        is_float: bool = True,
        min_fiat: int = None,
        details: str = None,
        autoreply: str = None,
        status: AdStatus = AdStatus.active,
    ) -> models.Ad:
        pass

    async def x2e_req_ad_upd(self, xreq: AdUpd) -> ad.AdsUpd:
        creds = [
            ad.TradeRule(
                content="Payment method-%s",
                contentCode="PAY",
                hint="Please enter",
                inputType=0,
                inputValue=cx.cred.detail,
                sort=1,
                title="【Payment related】",
                titleValue=(await models.PmEx.get(pm_id=cx.cred.pmcur.pm_id, ex=self.ex_client.ex)).name,
            )
            for cx in xreq.credexs
        ]
        trade_rules = ad.TradeRulesV2(
            [
                *creds,
                ad.TradeRule(
                    content="",
                    contentCode="MERCHANT",
                    hint="Please enter",
                    inputType=0,
                    inputValue="",
                    sort=4,
                    title="【Merchant Tips】",
                ),
            ]
        ).model_dump_json(exclude_none=True)
        coin_id, coin_scale = await self.ex_client.x2e_coin(xreq.coin_id)
        cur_id, cur_scale, minimum = await self.ex_client.x2e_cur(xreq.cur_id)
        return ad.AdsUpd(
            id=xreq.id,
            tradeType=int(xreq.is_sell),
            coinId=int(coin_id),
            currency=int(cur_id),
            minTradeLimit=minimum,
            maxTradeLimit=round(xreq.amount - 10**-cur_scale, cur_scale),
            tradeCount=round(xreq.quantity or xreq.amount / xreq.price, coin_scale),
            password=self.agent.auth["pass"],
            payTerm=15,
            premium=0.00,
            isFixed="on",
            fixedPrice=round(xreq.price, cur_scale),
            isAutoReply="off",
            takerAcceptOrder=0,
            isPayCode="off",
            receiveAccounts=",".join([str(cx.exid) for cx in xreq.credexs]),
            deviation=0,
            isTakerLimit="on",
            takerIsMerchant="on",
            takerRealLevel="off",
            takerIsPhoneBind="off",
            takerIsPayment="on",
            blockType=1,
            session=1,
            chargeType=False,
            apiVersion=4,
            channel="web",
            tradeRulesV2=quote(trade_rules),
        )

    async def _ad_upd(self, req: ad.AdsUpd, hdrs: dict[str, str] = None) -> dict:
        res = await self._post(self.url_my_ad + str(req.id), form_data=req.model_dump(exclude_none=True), hdrs=hdrs)
        if res["code"] == 200:
            return res["data"]
        elif res["code"] == 605:
            hdrs = {"x-dialog-trace-id": res["extend"]["traceId"]}
            return await self._ad_upd(req, hdrs)
        elif res["code"] == 1010:
            if (match := re.search(r"Available amount ([\d.]+)", res["message"])) and (qty := match.group(1)):
                req.tradeCount = float(qty)
                return await self._ad_upd(req, hdrs)
        elif res["code"] == 401:
            raise Exception(res)
        raise BaseException(res)

    async def ad_del(self) -> bool:
        pass

    async def ad_switch(self) -> bool:
        pass

    async def ads_switch(self) -> bool:
        pass

    async def get_user(self, user_id: int) -> dict:
        user = (await self._get(f"/-/x/otc/v1/user/{user_id}/info"))["data"]
        return user

    async def send_user_msg(self, msg: str, file=None) -> bool:
        pass

    async def block_user(self, is_blocked: bool = True) -> bool:
        pass

    async def rate_user(self, positive: bool) -> bool:
        pass

    # 39
    async def my_assets(self) -> dict:
        assets = await self._get(url_my_bals)
        return {c["coinId"]: c["total"] for c in assets["data"] if c["total"]}

    async def _get_auth_hdrs(self) -> dict[str, str]:
        pass

    base_url = ""
    middle_url = ""

    url_ads_req = "https://otc-cf.huobi.com/v1/data/trade-market"
    url_my_ads = "https://otc-api.trygofast.com/v1/data/trade-list?pageSize=50"
    url_my_ad = "/-/x/otc/v1/otc/trade/"  # + id
    url_my_bals = "https://www.huobi.com/-/x/otc/v1/capital/balance"
    url_paccs = "https://www.huobi.com/-/x/otc/v1/user/receipt-account"

    async def _proc(self, resp: ClientResponse, bp: dict | str = None) -> dict | str:
        if (await resp.json()).get("code") == 401:
            await self.login()
            return await self.METHS[resp.method](self, resp.url.path, bp)
        return await super()._proc(resp, bp)


async def _test():
    from x_model import init_db

    cn = await init_db(TORM, True)
    ex = await models.Ex[9]
    filebot = FileClient(NET_TOKEN)
    ecl = ex.client(filebot)
    agent = (
        await models.Agent.filter(actor__ex=ex, auth__isnull=False)
        .prefetch_related(
            "actor__ex",
            "actor__person__user__gmail",
            "actor__my_ads__my_ad__race",
            "actor__my_ads__pair_side__pair__cur",
            "actor__my_ads__pms",
        )
        .first()
    )
    cl: AgentClient = agent.client(ecl, filebot, XyncBot(PAY_TOKEN, cn))
    # cred = await models.Cred[89]
    # _ = await cl.cred_new(cred)
    # _creds = await cl.creds()
    # _ = await cl.cred_del(16984748)

    while True:
        breq = GetAds(coin_id=1, cur_id=1, is_sell=False, pm_ids=[366])
        sreq = GetAds(coin_id=1, cur_id=1, is_sell=True, pm_ids=[366])
        breq_upd = AdUpd(id=1185713, price=87.01, **{**breq.model_dump(), "amount": 100000.01})
        sreq_upd = AdUpd(id=1188929, price=98.99, **{**sreq.model_dump(), "amount": 200000.01})

        bads: list[ad.Resp] = await cl.ex_client.ads(breq)
        sads: list[ad.Resp] = await cl.ex_client.ads(sreq)
        bceil = 101.11
        sceil = 151
        bads = [a for a in bads if a.price < bceil and a.tradeCount > 10 and (a.maxTradeLimit - a.minTradeLimit > 800)]
        sads = [a for a in sads if a.price > sceil and a.tradeCount > 10 and (a.maxTradeLimit - a.minTradeLimit > 800)]

        if len(bads) > 1:
            if bads[0].uid == cl.actor.exid:
                if round(bads[0].price - bads[1].price, 2) > 0.01:
                    breq_upd.price = bads[1].price + 0.01
                    await cl.ad_upd(breq_upd)
                    print(end="!", flush=True)
            elif bads[0].price < bceil:
                breq_upd.price = bads[0].price + 0.01
                await cl.ad_upd(breq_upd)
                print(end="!", flush=True)

        if len(sads) > 1:
            if sads[0].uid == cl.actor.exid:
                if round(sads[1].price - sads[0].price, 2) > 0.01:
                    sreq_upd.price = sads[1].price - 0.01
                    await cl.ad_upd(sreq_upd)
                    print(end="!", flush=True)
            elif sads[0].price > sceil:
                sreq_upd.price = sads[0].price - 0.01
                await cl.ad_upd(sreq_upd)
                print(end="!", flush=True)

        if (pos := await cl.get_orders()) and (po := pos.pop(0)):
            if po.side:  # is_sell
                po.amount  # check
            else:  # buy
                order: OrderFull = await cl.get_order(po.orderId)
                if ps := [pm.bankNumber for pm in order.paymentMethod if pm.bankType in [24]]:
                    if match := re.search(r"^[PpРр]\d{7,10}\b", ps[0]):
                        match.group()

        print(end=".", flush=True)
        await sleep(9)

    await cl.stop()


if __name__ == "__main__":
    from asyncio import run, sleep

    run(_test())
