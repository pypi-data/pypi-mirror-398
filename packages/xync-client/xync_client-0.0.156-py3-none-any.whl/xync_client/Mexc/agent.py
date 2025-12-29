import json
import logging
from asyncio import run, sleep, create_task
from hashlib import md5
from urllib.parse import quote
from uuid import uuid4

import websockets
from blackboxprotobuf import protobuf_to_json
from pyro_client.client.file import FileClient
from xync_bot import XyncBot

from xync_client.Mexc.api import MEXCP2PApiClient
from xync_client.Mexc.etype import ad

from xync_client.Abc.xtype import GetAds, AdUpd
from xync_client.Bybit.etype.order import TakeAdReq
from xync_client.Mexc.etype.order import OrderDetail

from xync_client.loader import PAY_TOKEN, NET_TOKEN
from xync_schema import models
from xync_schema.enums import UserStatus, AgentStatus

from xync_client.Abc.Agent import BaseAgentClient


class AgentClient(BaseAgentClient):
    i: int = 5
    headers = {
        # "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru,en;q=0.9",
        "Language:": "ru-RU",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }
    api: MEXCP2PApiClient

    @staticmethod
    async def _heartbeat(ws):
        """Фоновая задача для PING/PONG"""
        while True:
            await sleep(25)
            await ws.send('{"method":"PING"}')

    async def _ws_key(self):
        self.i = 13 if self.i > 9999 else self.i + 1
        hdrs = self.agent.auth["headers"] | {
            "trochilus-trace-id": "c7831459-3bb2-4aa7-bf5d-9ff2adef0c08-0062",
            "ucenter-token": self.agent.auth["cookies"]["u_id"],
        }
        # resp = get("https://www.mexc.com/ucenter/api/ws_token", headers=hdrs, cookies=self.agent.auth['cookies'])
        resp = await self._get("/ucenter/api/ws_token", hdrs=hdrs)
        self.wkk = resp["data"]["wsToken"]

    async def ws_prv(self):
        await self._ws_key()
        url = f"wss://wbs.mexc.com/ws?wsToken={self.wkk}"
        async with websockets.connect(url) as ws:
            create_task(self._heartbeat(ws))
            await ws.send('{"method":"SUBSCRIPTION","params":["otc@private.p2p.orders.pb"],"id":12}')
            await ws.send('{"method":"SUBSCRIPTION","params":["common@private.risk.result.pb"],"id":11}')
            while resp := await ws.recv():
                try:
                    data: dict = json.loads(resp)
                except UnicodeDecodeError:
                    msg, typedef = protobuf_to_json(resp)
                    data = json.loads(msg)
                    await self.recv(data)
                if data.get("msg") == "PONG":
                    print(end="p")
                else:
                    logging.warning(data)

    async def recv(self, data: dict):
        if data["1"] == "otc@private.p2p.orders.pb":
            o = data["218"]["1"]
            order: OrderDetail = (await self.api.get_order_detail(o["1"])).data
            if order.side == "SELL":
                if order.state == "NOT_PAID":
                    ...
            elif order.side == "BUY":
                if order.state == "PAID":
                    ...
        ...

    async def _take_ad(self, req: TakeAdReq):
        self.i = 33 if self.i > 9998 else self.i + 2
        hdrs = self.headers | {"trochilus-trace-id": f"{uuid4()}-{self.i:04d}"}
        auth = {
            "p0": self.actor.agent.auth["p0"],
            "k0": self.actor.agent.auth["k0"],
            "chash": self.actor.agent.auth["chash"],
            "mtoken": self.actor.agent.auth["deviceId"],
            "mhash": md5(self.actor.agent.auth["deviceId"].encode()).hexdigest(),
        }
        data = {
            "scene": "TRADE_BUY",
            "quantity": req.quantity,
            "amount": req.amount,
            "orderId": req.ad_id,
            "authVersion": "v2",
            "deviceId": auth["mtoken"],
        }
        res = await self._post("/api/platform/p2p/api/verify/second_auth/risk/scene", json=data, hdrs=hdrs)
        data = {
            "amount": req.amount,
            "authVersion": "v2",
            "orderId": req.ad_id,
            "price": req.price,
            "ts": int(1761155700.8372989 * 1000),
            "userConfirmPaymentId" if req.is_sell else "userConfirmPayMethodId": req.pm_id,
        }
        self.i = 33 if self.i > 9999 else self.i + 1
        hdrs = self.headers | {"trochilus-trace-id": f"{uuid4()}-{self.i:04d}"}
        res = await self._post("/api/platform/p2p/api/order/deal?mhash=" + auth["mhash"], data=auth | data, hdrs=hdrs)
        return res["data"]

    async def x2e_req_ad_upd(self, xreq: AdUpd) -> ad.AdUpd:
        coin_id, coin_scale = await self.ex_client.x2e_coin(xreq.coin_id)
        cur_id, cur_scale, minimum = await self.ex_client.x2e_cur(xreq.cur_id)
        ereq = ad.AdUpd(
            id=xreq.id,
            price=round(xreq.price, cur_scale),
            coinId=coin_id,
            currency=cur_id,
            tradeType="SELL" if xreq.is_sell else "BUY",
            deviceId=self.agent.auth["deviceId"],
            payment=",".join([str(cdx.exid) for cdx in xreq.credexs]),
            priceType=0,
            minTradeLimit=minimum,
            maxTradeLimit=round(xreq.max_amount or xreq.amount - 10**-cur_scale, cur_scale),
            quantity=round(xreq.quantity or xreq.amount / xreq.price, coin_scale),
        )
        if xreq.cond:
            ereq.autoResponse = quote(xreq.cond)
        # todo: all kwargs
        return ereq

    async def _ad_upd(self, req: ad.AdUpd):
        self.i = 33 if self.i > 9999 else self.i + 1
        hdrs = self.headers | {"trochilus-trace-id": f"{uuid4()}-{self.i:04d}"}
        res = await self._put("/api/platform/p2p/api/merchant/order", form_data=req.model_dump(), hdrs=hdrs)
        return res["code"]


async def main():
    from x_model import init_db
    from xync_client.loader import TORM

    cn = await init_db(TORM, True)

    ex = await models.Ex[12]
    agent = (
        await models.Agent.filter(
            actor__ex=ex,
            status__gte=AgentStatus.race,
            auth__isnull=False,
            actor__person__user__status=UserStatus.ACTIVE,
            actor__person__user__pm_agents__isnull=False,
        )
        .prefetch_related("actor__ex", "actor__person__user__gmail")
        .first()
    )
    bbot = XyncBot(PAY_TOKEN, cn)
    fbot = FileClient(NET_TOKEN)
    ecl = ex.client(fbot)
    cl: AgentClient = agent.client(ecl, fbot, bbot)
    cl.api = MEXCP2PApiClient(agent.auth["key"], agent.auth["sec"])
    create_task(cl.ws_prv())

    while True:
        bceil = 106
        sceil = 124.98
        breq = GetAds(coin_id=1, cur_id=1, is_sell=False, pm_ids=[366])
        sreq = GetAds(coin_id=1, cur_id=1, is_sell=True, pm_ids=[366])
        breq_upd = AdUpd(
            id="a1574183931501582340", price=87, **{**breq.model_dump(), "amount": 11000.01}, max_amount=4370
        )  # + 1 cent
        sreq_upd = AdUpd(id="a1594624084590445568", price=150, **{**sreq.model_dump(), "amount": 30000.01})

        await sleep(5)
        bads: list[ad.Ad] = await cl.ex_client.ads(breq)
        if bads[0].price >= sceil:
            bad: ad.Ad = bads.pop(0)
            await cl.bbot.send(
                193017646,
                f"price: {bad.price}\nnick: {bad.merchant.nickName}\nmax:{bad.maxPayLimit}"
                f"\nqty: {bad.availableQuantity} [{bad.minTradeLimit}-{bad.maxTradeLimit}]",
            )
            # am = min(bad.maxTradeLimit, max(10000.0, bad.minTradeLimit))
            # req = TakeAdReq(
            #     ad_id=bad.exid,
            #     amount=am,
            #     pm_id=366,
            #     is_sell=False,
            #     coin_id=1,
            #     cur_id=1,
            # )
            # ord_resp: OrderResp = await cl.take_ad(req)

        bads = [
            a
            for a in bads
            if a.price <= bceil and a.availableQuantity > 20 and (a.maxTradeLimit - a.minTradeLimit > 1000)
        ]
        if len(bads) > 1:
            if bads[0].merchant.nickName == cl.actor.name:
                if round(bads[0].price - bads[1].price, 2) > 0.01:
                    breq_upd.price = bads[1].price + 0.01
                    if _ := await cl.ad_upd(breq_upd):
                        await sleep(5, print(_, flush=True))
                    print(end="!", flush=True)
            elif bads[0].price != (trgt_price := bads[0].price + 0.01):
                breq_upd.price = trgt_price
                if _ := await cl.ad_upd(breq_upd):
                    await sleep(5, print(_, flush=True))
                print(end="!", flush=True)

        await sleep(5)
        sads: list[ad.Ad] = await cl.ex_client.ads(sreq)
        if sads[0].price <= bceil:
            sad: ad.Ad = sads.pop(0)
            await cl.bbot.send(
                193017646,
                f"price: {sad.price}\nnick: {sad.merchant.nickName}\nmax:{sad.maxPayLimit}"
                f"\nqty: {sad.availableQuantity} [{sad.minTradeLimit}-{sad.maxTradeLimit}]",
            )
            # am = min(sad.maxTradeLimit, max(10000.0, sad.minTradeLimit))
            # req = TakeAdReq(
            #     ad_id=sad.exid,
            #     amount=am,
            #     pm_id=366,
            #     is_sell=False,
            #     coin_id=1,
            #     cur_id=1,
            # )
            # ord_resp: OrderResp = await cl.take_ad(req)

        sads = [
            a
            for a in sads
            if a.price >= sceil and a.availableQuantity > 20 and (a.maxTradeLimit - a.minTradeLimit > 1000)
        ]
        if len(sads) > 1:
            if sads[0].merchant.nickName == cl.actor.name:
                if round(sads[1].price - sads[0].price, 2) > 0.01:
                    sreq_upd.price = sads[1].price - 0.01
                    if _ := await cl.ad_upd(sreq_upd):
                        await sleep(15, print(_, flush=True))
                        continue
                    print(end="!", flush=True)
                    continue
            elif sads[0].price > sceil:
                sreq_upd.price = sads[0].price - 0.01
                if _ := await cl.ad_upd(sreq_upd):
                    await sleep(15, print(_, flush=True))
                    continue
                print(end="!", flush=True)
                continue

        print(end=".", flush=True)

    req = TakeAdReq(ad_id="a1574088909645125632", amount=500, pm_id=366, cur_id=1, price=85.8, is_sell=True)
    res = await cl.take_ad(req)
    print(res)


if __name__ == "__main__":
    run(main())
