import asyncio
import json
import logging
import re
from asyncio import sleep, gather
from asyncio.tasks import create_task
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from enum import IntEnum
from hashlib import sha256
from http.client import HTTPException
from math import floor
from typing import Literal
from uuid import uuid4

import pyotp
import websockets
from aiohttp.http_exceptions import HttpProcessingError
from bybit_p2p import P2P
from bybit_p2p._exceptions import FailedRequestError
from payeer_api import PayeerAPI
from pydantic import ValidationError
from pyro_client.client.file import FileClient
from tortoise import BaseDBAsyncClient
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.functions import Count
from tortoise.signals import post_save
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from x_client import df_hdrs
from x_model import init_db
from x_model.func import ArrayAgg
from xync_bot import XyncBot

from xync_client.Bybit.ex import ExClient
from xync_schema import models
from xync_schema.enums import OrderStatus, AgentStatus

from xync_schema.models import Actor, PmCur, Agent

from xync_client.Abc.Agent import BaseAgentClient
from xync_client.Abc.xtype import FlatDict, BaseOrderReq, AdUpd, GetAds
from xync_client.Bybit.etype.ad import AdPostRequest, AdUpdateRequest, Ad, AdStatus, MyAd
from xync_client.Bybit.etype.cred import CredEpyd
from xync_client.Bybit.etype.order import (
    OrderRequest,
    PreOrderResp,
    OrderResp,
    CancelOrderReq,
    OrderItem,
    OrderFull,
    Message,
    Status,
    OrderSellRequest,
    TakeAdReq,
    StatusChange,
    CountDown,
    Receive,
    Read,
    SellerCancelChange,
)
from xync_client.Pms.Payeer.agent import PmAgentClient
from xync_client.loader import TORM, NET_TOKEN, PAY_TOKEN, PRX


class NoMakerException(Exception):
    pass


class ShareException(Exception):
    pass


class AgentClient(BaseAgentClient):  # Bybit client
    headers = df_hdrs | {"accept-language": "ru-RU"}
    sec_hdrs: dict[str, str]
    # rewrite token for public methods
    api: P2P
    last_ad_id: list[str] = []
    update_ad_body = {
        "priceType": "1",
        "premium": "118",
        "quantity": "0.01",
        "minAmount": "500",
        "maxAmount": "3500000",
        "paymentPeriod": "30",
        "remark": "",
        "price": "398244.84",
        "paymentIds": ["3162931"],
        "tradingPreferenceSet": {
            "isKyc": "1",
            "hasCompleteRateDay30": "0",
            "completeRateDay30": "",
            "hasOrderFinishNumberDay30": "0",
            "orderFinishNumberDay30": "0",
            "isMobile": "0",
            "isEmail": "0",
            "hasUnPostAd": "0",
            "hasRegisterTime": "0",
            "registerTimeThreshold": "0",
            "hasNationalLimit": "0",
            "nationalLimit": "",
        },
        "actionType": "MODIFY",
        "securityRiskToken": "",
    }

    def __init__(
        self,
        agent: Agent,
        ex_client: ExClient,
        fbot: FileClient,
        bbot: XyncBot,
        pm_clients: dict[int, PmAgentClient] = None,
        **kwargs,
    ):
        super().__init__(agent, ex_client, fbot, bbot, pm_clients, **kwargs)
        self.sec_hdrs = {
            "accept-language": "ru,en;q=0.9",
            "gdfp": agent.auth["Risktoken"],
            "tx-id": agent.auth["Risktoken"],
        }
        self.api = P2P(testnet=False, api_key=agent.auth["key"], api_secret=agent.auth["sec"])
        self.hist: dict | None = None
        self.completed_orders: list[int] | None = None

    """ Private METHs"""

    async def fiat_new(self, payment_type: int, real_name: str, account_number: str) -> FlatDict | None:
        method1 = await self._post(
            "/x-api/fiat/otc/user/payment/new_create",
            {"paymentType": payment_type, "realName": real_name, "accountNo": account_number, "securityRiskToken": ""},
        )
        if srt := method1["result"]["securityRiskToken"]:
            await self._check_2fa(srt)
            method2 = await self._post(
                "/x-api/fiat/otc/user/payment/new_create",
                {
                    "paymentType": payment_type,
                    "realName": real_name,
                    "accountNo": account_number,
                    "securityRiskToken": srt,
                },
            )
            return method2
        else:
            return logging.exception(method1)

    def get_payment_method(self, fiat_id: int) -> CredEpyd:
        return self.creds()[fiat_id]

    def creds(self) -> dict[int, CredEpyd]:
        data = self.api.get_user_payment_types()
        if data["ret_code"] > 0:
            return data
        return {credex["id"]: CredEpyd.model_validate(credex) for credex in data["result"]}

    async def cred_epyd2db(self, ecdx: CredEpyd, pers_id: int = None, cur_id: int = None) -> models.CredEx | None:
        if ecdx.paymentType in (416,):  # what is 416??
            return None
        if not (
            pmex := await models.PmEx.get_or_none(exid=ecdx.paymentType, ex=self.ex_client.ex).prefetch_related(
                "pm__curs"
            )
        ):
            raise HTTPException(f"No PmEx {ecdx.paymentType} on ex#{self.ex_client.ex.name}", 404)
        if cred_old := await models.Cred.get_or_none(credexs__exid=ecdx.id, credexs__ex=self.actor.ex).prefetch_related(
            "pmcur"
        ):
            cur_id = cred_old.pmcur.cur_id
        elif not cur_id:  # is new Cred
            cur_id = (
                pmex.pm.df_cur_id
                or await self.guess_cur(ecdx, len(pmex.pm.curs) > 1 and pmex.pm.curs)
                or (pmex.pm.country_id and (await pmex.pm.country).cur_id)
                # or (ecdx.currencyBalance and await models.Cur.get_or_none(ticker=ecdx.currencyBalance[0]))  # это че еще за хуйня?
            )
        if not cur_id:
            raise Exception(f"Set default cur for {pmex.name}")
        if not (pmcur := await models.PmCur.get_or_none(cur_id=cur_id, pm_id=pmex.pm_id)):
            raise HTTPException(f"No PmCur with cur#{cur_id} and pm#{ecdx.paymentType}", 404)
        xtr = ecdx.branchName
        if ecdx.bankName:
            xtr += (" | " if xtr else "") + ecdx.bankName
        elif ecdx.payMessage:
            xtr += (" | " if xtr else "") + ecdx.payMessage
        elif ecdx.qrcode:
            xtr += (" | " if xtr else "") + ecdx.qrcode
        elif ecdx.paymentExt1:
            xtr += (" | " if xtr else "") + ecdx.paymentExt1
        try:
            cred_db, _ = await models.Cred.update_or_create(
                {
                    "name": ecdx.realName,
                    "extra": xtr,
                },
                pmcur=pmcur,
                person_id=pers_id or self.actor.person_id,
                detail=ecdx.accountNo or ecdx.payMessage,
            )
            if cred_db.ovr_pm_id is None and (cred_db.detail.startswith("XyncPay") or xtr.startswith("XyncPay")):
                cred_db.ovr_pm_id = 0
                await cred_db.save()
            credex_in = models.CredEx.validate({"exid": ecdx.id, "cred_id": cred_db.id, "ex_id": self.actor.ex.id})
            credex_db, _ = await models.CredEx.update_or_create(**credex_in.df_unq())
        except IntegrityError as e:
            raise e
        return credex_db

    async def guess_cur(self, ecdx: CredEpyd, curs: list[models.Cur]):
        mbs = ecdx.bankName.split(", ")
        mbs += ecdx.branchName.split(" / ")
        mbs = {mb.lower(): mb for mb in mbs}
        if (
            pms := await models.Pm.filter(Q(join_type="OR", pmexs__name__in=mbs.values(), norm__in=mbs.keys()))
            .group_by("pmcurs__cur_id", "pmcurs__cur__ticker")
            .annotate(ccnt=Count("id"), names=ArrayAgg("norm"))
            .order_by("-ccnt", "pmcurs__cur__ticker")
            .values("pmcurs__cur_id", "names", "ccnt")
        ):
            return pms[0]["pmcurs__cur_id"]
        curs = {c.ticker: c.id for c in curs or await models.Cur.all()}
        for cur, cid in curs.items():
            if re.search(re.compile(rf"\({cur}\)$"), ecdx.bankName):
                return cid
            if re.search(re.compile(rf"\({cur}\)$"), ecdx.branchName):
                return cid
            if re.search(re.compile(rf"\({cur}\)$"), ecdx.accountNo):
                return cid
            if re.search(re.compile(rf"\({cur}\)$"), ecdx.payMessage):
                return cid
            if re.search(re.compile(rf"\({cur}\)$"), ecdx.paymentExt1):
                return cid
        return None

    # 25: Список реквизитов моих платежных методов
    async def set_creds(self) -> list[models.CredEx]:
        credexs_epyd: dict[int, CredEpyd] = self.creds()
        credexs: list[models.CredEx] = [await self.cred_epyd2db(f) for f in credexs_epyd.values()]
        return credexs

    async def ott(self):
        t = await self._post("/x-api/user/private/ott")
        return t

    # 27
    async def fiat_upd(self, fiat_id: int, detail: str, name: str = None) -> dict:
        fiat = self.get_payment_method(fiat_id)
        fiat.realName = name
        fiat.accountNo = detail
        result = await self._post("/x-api/fiat/otc/user/payment/new_update", fiat.model_dump(exclude_none=True))
        srt = result["result"]["securityRiskToken"]
        await self._check_2fa(srt)
        fiat.securityRiskToken = srt
        result2 = await self._post("/fiat/otc/user/payment/new_update", fiat.model_dump(exclude_none=True))
        return result2

    # 28
    async def fiat_del(self, fiat_id: int) -> dict | str:
        data = {"id": fiat_id, "securityRiskToken": ""}
        method = await self._post("/x-api/fiat/otc/user/payment/new_delete", data)
        srt = method["result"]["securityRiskToken"]
        await self._check_2fa(srt)
        data["securityRiskToken"] = srt
        delete = await self._post("/x-api/fiat/otc/user/payment/new_delete", data)
        return delete

    async def switch_ads(self, new_status: AdStatus) -> dict:
        data = {"workStatus": new_status.name}  # todo: переделать на апи, там status 0 -> 1
        res = await self._post("/x-api/fiat/otc/maker/work-config/switch", data)
        return res

    @staticmethod
    def get_rate(list_ads: list) -> float:
        ads = [ad for ad in list_ads if set(ad["payments"]) - {"5", "51"}]
        return float(ads[0]["price"])

    def my_ads(self, active: bool = True, page: int = 1) -> list[MyAd]:
        resp = self.api.get_ads_list(size="30", page=str(page), status=AdStatus.active if active else AdStatus.sold_out)
        ads = [MyAd.model_validate(ad) for ad in resp["result"]["items"]]
        if resp["result"]["count"] > 30 * page:
            ads.extend(self.my_ads(active, page + 1))
        return ads

    async def export_my_ads(self, active: bool = None) -> int:  # upserted)
        ads = self.my_ads(True)
        if not active:
            ads += self.my_ads(False)
        for ad in ads:
            ad_db = await self.ex_client.ad_load(ad, maker=self.actor)
            mad_db, _ = await models.MyAd.update_or_create(ad=ad_db)
            exids = [pt.id for pt in ad.paymentTerms]
            credexs = await models.CredEx.filter(ex_id=self.actor.ex_id, exid__in=exids).prefetch_related("cred")
            await mad_db.credexs.add(*credexs)
            # share
            if [cx for cx in credexs if cx.cred.ovr_pm_id == 0]:
                try:
                    await self.ad_share(mad_db.id)
                except ShareException as e:
                    logging.warning(e.args[0])
                await sleep(1)

        return len(ads)

    async def ad_share(self, maid: int):
        myad = await models.MyAd.get(id=maid).prefetch_related("ad")
        if myad.hex and myad.shared_at + timedelta(minutes=55) > now():  # check expired
            # check validity
            data = await self._post("/x-api/fiat/otc/item/shareItem/info", {"shareCode": myad.hex.hex()})
            if data["ret_code"] == 0:
                return myad.get_url()
        data = await self._post("/x-api/fiat/otc/item/share", {"itemId": str(myad.ad.exid)})
        if data["ret_code"] == 912300058:
            raise ShareException(f"Объява {myad.id}:{myad.ad.id}:{myad.ad.exid} выключена")
        if data["ret_code"] == 912300059:
            raise ShareException("Торговля выключена")
        if data["ret_code"] != 0:  # Новая ошибка
            raise ShareException(data)
        url = data["result"]["shareLink"]
        resp = await self.session.get(url)
        hx = resp.url.query["by_web_link"].replace(models.MyAd.WEB, "")
        await models.MyAd.filter(id=maid).update(hex=bytes.fromhex(hx), shared_at=now())
        await myad.refresh_from_db()
        return myad.get_url()

    def get_security_token_create(self):
        data = self._post("/x-api/fiat/otc/item/create", self.create_ad_body)
        if data["ret_code"] == 912120019:  # Current user can not to create add as maker
            raise NoMakerException(data)
        security_risk_token = data["result"]["securityRiskToken"]
        return security_risk_token

    async def _check_2fa(self, risk_token) -> int:
        data = {"risk_token": risk_token}
        res = await self._post("/x-api/user/public/risk/components", data, hdrs=self.sec_hdrs)
        if res["ret_msg"] != "success":
            raise HTTPException("get")
        cres = sorted(res["result"]["component_list"], key=lambda c: c["component_id"], reverse=True)
        vdata = {
            "risk_token": risk_token,
            "component_list": {c["component_id"]: await self.__get_2fa(c["component_id"], risk_token) for c in cres},
        }
        res = await self._post("/x-api/user/public/risk/verify", vdata, hdrs=self.sec_hdrs)
        if er_code := res["ret_code"] or res["result"]["ret_code"]:  # если код не 0, значит ошибка
            logging.error("Wrong 2fa, wait 5 secs and retry..")
            await sleep(5)
            return await self._check_2fa(risk_token)
        return er_code

    async def __get_2fa(
        self, typ: Literal["google2fa", "email_verify", "payment_password_verify", "phone_verify"], rt: str = None
    ):
        res = {"ret_msg": "success"}
        if typ != "google2fa":
            data = {"risk_token": rt, "component_id": typ}
            res = await self._post("/x-api/user/public/risk/send/code", data, hdrs=self.sec_hdrs)
        if res["ret_msg"] == "success":
            if typ == "google2fa":
                bybit_secret = self.agent.auth["2fa"]
                totp = pyotp.TOTP(bybit_secret)
                return totp.now()
            elif typ == "email_verify":
                return self.gmail.bybit_code()
            elif typ == "payment_password_verify":
                hp = sha256(self.agent.auth["pass"].encode()).hexdigest()
                return hp
        elif cool_down := int(res["result"]["cool_down"]):
            await sleep(cool_down)
            return self.__get_2fa(typ, rt)
        raise Exception("2fa fail")

    def get_ad(self, aid: int) -> Ad:
        return Ad(**self.api.get_ad_details(itemId=aid)["result"])

    def _post_ad(self, risk_token: str):
        self.create_ad_body.update({"securityRiskToken": risk_token})
        data = self._post("/x-api/fiat/otc/item/create", self.create_ad_body)
        return data

    # создание объявлений
    def post_create_ad(self, token: str):
        result__check_2fa = self._check_2fa(token)
        assert result__check_2fa["ret_msg"] == "success", "2FA code wrong"

        result_add_ad = self._post_ad(token)
        if result_add_ad["ret_msg"] != "SUCCESS":
            print("Wrong 2fa on Ad creating, wait 9 secs and retry..")
            sleep(9)
            return self._post_create_ad(token)
        self.last_ad_id.append(result_add_ad["result"]["itemId"])

    def ad_new(self, ad: AdPostRequest):
        data = self.api.post_new_ad(**ad.model_dump())
        return data["result"]["itemId"] if data["ret_code"] == 0 else data

    async def _ad_upd(self, req: AdUpd):
        upd = AdUpdateRequest({})
        params = upd.model_dump()
        data = self.api.update_ad(**params)
        return data["result"] if data["ret_code"] == 0 else data

    def get_security_token_update(self) -> str:
        self.update_ad_body["id"] = self.last_ad_id
        data = self._post("/x-api/fiat/otc/item/update", self.update_ad_body)
        security_risk_token = data["result"]["securityRiskToken"]
        return security_risk_token

    def post_update_ad(self, token):
        result__check_2fa = self._check_2fa(token)
        assert result__check_2fa["ret_msg"] == "success", "2FA code wrong"

        result_update_ad = self.update_ad(token)
        if result_update_ad["ret_msg"] != "SUCCESS":
            print("Wrong 2fa on Ad updating, wait 10 secs and retry..")
            sleep(10)
            return self._post_update_ad(token)
        # assert result_update_ad['ret_msg'] == 'SUCCESS', "Ad isn't updated"

    def update_ad(self, risk_token: str):
        self.update_ad_body.update({"securityRiskToken": risk_token})
        data = self._post("/x-api/fiat/otc/item/update", self.update_ad_body)
        return data

    def ad_del(self, ad_id: int):
        data = self.api.remove_ad(itemId=ad_id)
        return data

    async def __preorder_request(self, ad_id: int) -> PreOrderResp:
        res = await self._post("/x-api/fiat/otc/item/simple", json={"item_id": str(ad_id)})
        if res["ret_code"] == 0:
            res = res["result"]
        return PreOrderResp.model_validate(res)

    async def _order_request(self, bor: BaseOrderReq) -> OrderResp:
        por: PreOrderResp = await self.__preorder_request(bor.ad_id)
        req = OrderRequest(
            itemId=por.id,
            tokenId=bor.coin_exid,
            currencyId=bor.cur_exid,
            side="1" if bor.is_sell else "0",
            amount=f"{bor.fiat_amount:.2f}".rstrip("0").rstrip("."),
            curPrice=por.curPrice,
            quantity=str(round(bor.fiat_amount / float(por.price), bor.coin_scale)),
            flag="amount",
            # online="0"
        )
        if bor.is_sell:
            credex = await models.CredEx.get(
                cred__person_id=self.actor.person_id,
                cred__pmcur__pm__pmexs__exid=[pp for pp in por.payments if pp == bor.pmex_exid][0],  # bor.pmex_exid
                cred__pmcur__pm__pmexs__ex_id=self.ex_client.ex.id,
                cred__pmcur__cur__ticker=bor.cur_exid,
            )
            req = OrderSellRequest(**req.model_dump(), paymentType=bor.pmex_exid, paymentId=str(credex.exid))
        # вот непосредственно сам запрос на ордер
        return await self.__order_create(req, bor)

    async def __order_create(self, req: OrderRequest | OrderSellRequest, bor: BaseOrderReq) -> OrderResp:
        hdrs = {"Risktoken": self.sec_hdrs["gdfp"]}
        res: dict = await self._post("/x-api/fiat/otc/order/create", json=req.model_dump(), hdrs=hdrs)
        if res["ret_code"] == 0:
            resp = OrderResp.model_validate(res["result"])
        elif res["ret_code"] == 10001:
            logging.error(req.model_dump(), "POST", self.session._base_url)
            raise HTTPException()
        elif res["ret_code"] == 912120030 or res["ret_msg"] == "The price has changed, please try again later.":
            resp = await self._order_request(bor)
        else:
            logging.exception(res)
        if not resp.orderId and resp.needSecurityRisk:
            if rc := await self._check_2fa(resp.securityRiskToken):
                await self.bbot.send(self.actor.person.user.username_id, f"Bybit 2fa: {rc}")
                raise Exception(f"Bybit 2fa: {rc}")
            # еще раз уже с токеном
            req.securityRiskToken = resp.securityRiskToken
            resp = await self.__order_create(req, bor)
        return resp

    async def cancel_order(self, order_id: str) -> bool:
        cr = CancelOrderReq(orderId=order_id)
        res = await self._post("/x-api/fiat/otc/order/cancel", cr.model_dump())
        return res["ret_code"] == 0

    async def get_order_info(self, order_id: str) -> OrderFull:
        data = await self._post("/x-api/fiat/otc/order/info", json={"orderId": order_id})
        return OrderFull.model_validate(data["result"])

    def get_chat_msg(self, order_id):
        data = self._post("/x-api/fiat/otc/order/message/listpage", json={"orderId": order_id, "size": 100})
        msgs = [
            {"text": msg["message"], "type": msg["contentType"], "role": msg["roleType"], "user_id": msg["userId"]}
            for msg in data["result"]["result"]
            if msg["roleType"] not in ("sys", "alarm")
        ]
        return msgs

    def block_user(self, user_id: str):
        return self._post("/x-api/fiat/p2p/user/add_block_user", {"blockedUserId": user_id})

    def unblock_user(self, user_id: str):
        return self._post("/x-api/fiat/p2p/user/delete_block_user", {"blockedUserId": user_id})

    def user_review_post(self, order_id: str):
        return self._post(
            "/x-api/fiat/otc/order/appraise/modify",
            {
                "orderId": order_id,
                "anonymous": "0",
                "appraiseType": "1",  # тип оценки 1 - хорошо, 0 - плохо. При 0 - обязательно указывать appraiseContent
                "appraiseContent": "",
                "operateType": "ADD",  # при повторном отправлять не 'ADD' -> а 'EDIT'
            },
        )

    def my_reviews(self):
        return self._post(
            "/x-api/fiat/otc/order/appraiseList",
            {"makerUserId": self.actor.exid, "page": "1", "size": "10", "appraiseType": "1"},  # "0" - bad
        )

    async def get_pending_orders(
        self, side: int = None, status: int = None, begin_time: int = None, end_time: int = None, token_id: str = None
    ):
        res = await self._post(
            "/x-api/fiat/otc/order/pending/simplifyList",
            {
                "status": status,
                "tokenId": token_id,
                "beginTime": begin_time,
                "endTime": end_time,
                "side": side,  # 1 - продажа, 0 - покупка
                "page": 1,
                "size": 20,
            },
        )
        if res["ret_code"] == 0:
            return {o.id: OrderItem(**o) for o in res["result"]["items"]}
        return res["ret_code"]

    def get_orders_done(self, begin_time: int, end_time: int, status: int, side: int, token_id: str):
        return self._post(
            "/x-api/fiat/otc/order/simplifyList",
            {
                "status": status,  # 50 - завершено
                "tokenId": token_id,
                "beginTime": begin_time,
                "endTime": end_time,
                "side": side,  # 1 - продажа, 0 - покупка
                "page": 1,
                "size": 10,
            },
        )

    async def create_order_db(self, order: OrderFull) -> models.Order:
        curex = await models.CurEx.get_or_none(ex=self.ex_client.ex, exid=order.currencyId).prefetch_related("cur")
        cur_scale = (curex.scale if curex.scale is not None else curex.cur.scale) if curex else 2
        coinex = await models.CoinEx.get(ex=self.ex_client.ex, exid=order.tokenId).prefetch_related("coin")
        coin_scale = coinex.scale if coinex.scale is not None else coinex.cur.scale
        sb_names = order.sellerRealName, order.buyerRealName
        im_maker = int(int(order.makerUserId) == self.actor.exid)
        taker_id = (order.userId, order.targetUserId)[im_maker]
        taker_name = sb_names[order.side]  # todo: double check
        taker_person = await self.ex_client.person_name_update(taker_name, taker_id)
        seller_person = (
            self.actor.person
            if order.side
            else await self.ex_client.person_name_update(order.sellerRealName, int(order.targetUserId))
        )
        taker_nick = (self.actor.name, order.targetNickName)[im_maker]  # todo: check
        ad_db = await models.Ad.get(exid=order.itemId)
        if not ad_db:
            ad = self.get_ad(order.itemId)
            # ad_db, cond_isnew = await self.ex_client.cond_load(ad, force=True, rname=maker_name[order.side])
            ad_db = await self.ex_client.ad_load(ad, maker=self.actor)
        ecredex: CredEpyd = order.confirmedPayTerm

        if ecredex.paymentType == 0 and im_maker and order.side:
            ecredex = order.paymentTermList[0]
        if ecredex.paymentType:
            if ecredex.paymentType == 51:
                ecredex.accountNo = ecredex.accountNo.replace("p", "P").replace("р", "P").replace("Р", "P")
                # if not re.match(r"^([Pp])\d{7,10}$", ecredex.accountNo):
                #     msgs = self.api.get_chat_messages(orderId=order.id, size=100)["result"]["result"]
                #     msgs = [m["message"] for m in msgs if m["roleType"] == "user" and m["userId"] == order.targetUserId]
                #     msgs = [g.group() for m in msgs if (g := re.match(r"([PpРр])\d{7,10}\b", m))]
                #     crd = await models.Cred.get_or_none(
                #         detail=ecredex.accountNo, credexs__exid=ecredex.id, credexs__ex=self.ex_client.ex
                #     )
                #     if not msgs and re.match(r"^\d{7,10}$", ecredex.accountNo):
                #         ecredex.accountNo = "P" + ecredex.accountNo
                #     elif msgs:
                #         ecredex.accountNo = msgs[-1]
                #     else:
                #         ...
                #     if crd:
                #         crd.detail = ecredex.accountNo
                #         await crd.save(update_fields=["detail"])
            if not (credex := await models.CredEx.get_or_none(exid=ecredex.id, ex=self.ex_client.ex)):
                # cur_id = await Cur.get(ticker=ad.currencyId).values_list('id', flat=True)
                # await self.cred_epyd2db(ecredex, ad_db.maker.person_id, cur_id)
                if (
                    await PmCur.filter(
                        pm__pmexs__ex=self.ex_client.ex,
                        pm__pmexs__exid=ecredex.paymentType,
                        cur__ticker=order.currencyId,
                    ).count()
                    != 1
                ):
                    ...
                if not (
                    pmcur := await PmCur.get_or_none(
                        pm__pmexs__ex=self.ex_client.ex,
                        pm__pmexs__exid=ecredex.paymentType,
                        cur__ticker=order.currencyId,
                    )
                ):
                    ...
                if not (
                    crd := await models.Cred.get_or_none(pmcur=pmcur, person=seller_person, detail=ecredex.accountNo)
                ):
                    extr = ", ".join(
                        x
                        for xtr in [
                            ecredex.bankName,
                            ecredex.branchName,
                            ecredex.qrcode,
                            ecredex.payMessage,
                            ecredex.paymentExt1,
                        ]
                        if (x := xtr.strip())
                    )
                    crd = await models.Cred.create(
                        detail=ecredex.accountNo,
                        pmcur=pmcur,
                        person=seller_person,
                        name=ecredex.realName,
                        extra=extr,
                    )
                credex = await models.CredEx.create(exid=ecredex.id, ex=self.ex_client.ex, cred=crd)
        try:
            taker, _ = await Actor.get_or_create(
                {"name": taker_nick, "person": taker_person}, ex=self.ex_client.ex, exid=taker_id
            )
        except IntegrityError as e:
            logging.error(e)
        odb, _ = await models.Order.update_or_create(
            {
                "amount": float(order.amount) * 10**cur_scale,
                "quantity": float(order.quantity) * 10**coin_scale,
                "status": OrderStatus[Status(order.status).name],
                "created_at": ms2utc(order.createDate),
                "payed_at": order.transferDate != "0" and ms2utc(order.transferDate) or None,
                "confirmed_at": Status(order.status) == Status.completed and ms2utc(order.transferDate) or None,
                "appealed_at": order.status == 30 and ms2utc(order.transferDate) or None,
                "cred_id": ecredex.paymentType and credex.cred_id or None,
                "taker": taker,
                "ad": ad_db,
            },
            exid=order.id,
        )
        if order.status == Status.completed and ecredex.paymentType == 51:
            await odb.fetch_related("cred", "transfer")
            if odb.cred.detail != ecredex.accountNo:
                ...
            frm = (odb.created_at + timedelta(minutes=180 - 1)).isoformat(sep=" ").split("+")[0]
            to = ((odb.payed_at or odb.created_at) + timedelta(minutes=180 + 30)).isoformat(sep=" ").split("+")[0]
            tsa = [
                t
                for tid, t in (self.hist.items() if self.hist else [])
                if (ecredex.accountNo == t["to"] and t["from"] != "@merchant" and frm < t["date"] < to)
            ]
            buyer_person = (
                self.actor.person
                if not order.side
                else await self.ex_client.person_name_update(order.buyerRealName, int(order.targetUserId))
            )
            ts = [t for t in tsa if floor(fa := float(order.amount)) <= float(t["creditedAmount"]) <= round(fa)]
            if len(ts) != 1:
                if len(tsa) > 1:
                    summ = sum(float(t["creditedAmount"]) for t in tsa)
                    if floor(fa) <= summ <= round(fa):
                        for tr in tsa:
                            am = int(float(tr["creditedAmount"]) * 100)
                            await models.Transfer.create(
                                pmid=tr["id"], order=odb, amount=am, sender_acc=tr["from"], created_at=tr["date"]
                            )
            else:
                bcred, _ = await models.Cred.get_or_create(
                    {"detail": ts[0]["from"]}, person=buyer_person, pmcur_id=odb.cred.pmcur_id
                )
                am = int(float(ts[0]["creditedAmount"]) * 100)
                try:
                    await models.Transfer.create(
                        pmid=ts[0]["id"], order=odb, amount=am, sender_acc=ts[0]["from"], created_at=ts[0]["date"]
                    )
                except IntegrityError as e:
                    logging.error(e)
            ...

        await odb.fetch_related("ad")
        return odb

    async def get_api_orders(
        self,
        page: int = 1,
        begin_time: int = None,
        end_time: int = None,
        status: int = None,
        side: int = None,
        token_id: str = None,
    ):
        try:
            lst = self.api.get_orders(
                page=page,
                # status=status,  # 50 - завершено
                # tokenId=token_id,
                # beginTime=begin_time,
                # endTime=end_time,
                # side=side, # 1 - продажа, 0 - покупка
                size=30,
            )
        except FailedRequestError as e:
            if e.status_code == 10000:
                await sleep(9)
                await self.get_api_orders(page, begin_time, end_time)  # , status, side, token_id)
        ords = {int(o["id"]): OrderItem.model_validate(o) for o in lst["result"]["items"]}
        for oid, o in ords.items():
            if o.status != Status.completed.value or oid in self.completed_orders:
                continue
            fo = self.api.get_order_details(orderId=o.id)
            order = OrderFull.model_validate(fo["result"])
            order_db = await self.create_order_db(order)
            await sleep(1)
            dmsgs = self.api.get_chat_messages(orderId=oid, size=200)["result"]["result"][::-1]
            msgs = [Message.model_validate(m) for m in dmsgs if m["msgType"] in (1, 2, 7, 8)]
            if order_db.ad.auto_msg:
                msgs and msgs.pop(0)
            msgs_db = [
                models.Msg(
                    order=order_db,
                    read=m.isRead,
                    to_maker=m.userId != order.makerUserId,
                    **({"txt": m.message} if m.msgType == 1 else {"file": await self.ex_client.file_upsert(m.message)}),
                    sent_at=int(m.createDate[:-3]),
                )
                for m in msgs
            ]
            _ = await models.Msg.bulk_create(msgs_db, ignore_conflicts=True)
        logging.info(f"orders page#{page} imported ok!")
        if len(ords) == 30:
            await self.get_api_orders(page + 1, begin_time, end_time, status, side, token_id)

    # async def order_stat(self, papi: PayeerAPI):
    #     for t in papi.history():
    #         os = self.api.get_orders(page=1, size=30)

    # @staticmethod
    # def premium_up(mad: Ad, cad: Ad, k: Literal[-1, 1]):
    #     mpc, mpm, cpc, cpm = Decimal(mad.price), Decimal(mad.premium), Decimal(cad.price), Decimal(cad.premium)
    #     new_premium = cpm - k * step(mad, cad, 2)
    #     if Decimal(mad.premium) == new_premium:  # Если нужный % и так уже стоит
    #         raise ValueError("wrong premium", mad, cad)
    #     if round(cpc * new_premium / cpm, 2) == m
    #     mad.premium = new_premium.to_eng_string()

    async def take_ad(self, req: TakeAdReq):
        if req.price and req.is_sell and req.cur_:
            ...  # todo call the get_ad_details() only if lack of data
        # res = self.api.get_ad_details(itemId=req.ad_id)["result"]
        # ad: Ad = Ad.model_validate(res)
        # pmexs = await models.PmEx.filter(ex_id=self.actor.ex_id, pm_id=req.pm_id)
        # if len(pmexs) > 1:
        #     pmexs = [p for p in pmexs if p.exid in ad.payments]
        #
        # # todo: map pm->cred_pattern
        # pmexid = exids.pop() if (exids := set(ad.payments) & set(px.exid for px in pmexs)) else "40"
        pmexid = str(req.pm_id)
        coinex = await models.CoinEx.get(coin_id=req.coin_id, ex=self.ex_client.ex)
        curex = await models.CurEx.get(cur_id=req.cur_id, ex=self.ex_client.ex)

        # if ad.side: # продажа, я (тейкер) покупатель
        #     pmexs = await models.PmEx.filter(ex_id=self.actor.ex_id, pm_id=req.pm_id)
        #     if len(pmexs) > 1:
        #         pmexs = [p for p in pmexs if p.name.endswith(f" ({ad.currencyId})")]
        # else:
        #     pmexs = await models.CredEx.filter(
        #         ex_id=self.actor.ex_id, cred__person_id=self.actor.person_id,
        #         cred__pmcur__pm_id=req.pm_id, cred__pmcur__cur__ticker=ad.currencyId
        #    )
        # req.pm_id = pmexs[0].exid
        # req.quantity = round(req.amount / float(ad.price) - 0.00005, 4)  # todo: to get the scale from coinEx

        bor = BaseOrderReq(
            ad_id=str(req.ad_id),
            fiat_amount=req.amount,
            is_sell=req.is_sell,
            cur_exid=curex.exid,
            coin_exid=coinex.exid,
            coin_scale=coinex.scale,
            pmex_exid=pmexid,
        )
        resp: OrderResp = await self._order_request(bor)
        return resp

    async def watch_payeer(self, mcs: dict[int, "AgentClient"]):
        await models.CoinEx.get(coin_id=1, ex=self.actor.ex).prefetch_related("coin")
        await models.CurEx.get(cur_id=1, ex=self.actor.ex).prefetch_related("cur")
        post_pmexs = set(await models.PmEx.filter(pm_id=366, ex=self.actor.ex).prefetch_related("pm"))
        i = 0
        while True:
            try:
                breq = GetAds(coin_id=1, cur_id=1, is_sell=False, limit=50)
                bs = await self.ex_client.ads(breq, post_pmexs=post_pmexs)
                bs = [b for b in bs if float(b.price) < 100 or int(b.userId) in mcs.keys()]
                if bs:
                    ad: Ad = bs[0]
                    await self.bbot.send(
                        193017646,
                        f"price: {ad.price}\nnick: {ad.nickName}\nprice: {ad.price}"
                        f"\nqty: {ad.quantity} [{ad.minAmount}-{ad.maxAmount}]",
                    )
                    am = min(float(ad.maxAmount), max(8000 + i, float(ad.minAmount)))
                    req = TakeAdReq(
                        ad_id=ad.id,
                        amount=am,
                        pm_id=14,
                        is_sell=False,
                        coin_id=1,
                        cur_id=1,
                    )
                    ord_resp: OrderResp = await self.take_ad(req)
                    # order: OrderFull = OrderFull(**self.api.get_order_details(orderId=ord_resp.orderId)["result"])
                    order: OrderFull = await self.get_order_info(ord_resp.orderId)
                    odb = await self.create_order_db(order)
                    t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
                    await t.fetch_related("order__cred__pmcur__cur")
                    # res = await self.pm_clients[366].send(t)
                    await sleep(2)
                    self.api.mark_as_paid(
                        orderId=str(odb.exid),
                        paymentType=str(order.paymentTermList[0].paymentType),  # pmex.exid
                        paymentId=order.paymentTermList[0].id,  # credex.exid
                    )
                    await sleep(3)
                    if int(ad.userId) in mcs:
                        mcs[int(ad.userId)].api.release_assets(orderId=order.id)

                await sleep(5)

                sreq = GetAds(coin_id=1, cur_id=1, is_sell=True, limit=50, kwargs={"post_pmexs": post_pmexs})
                ss = await self.ex_client.ads(sreq, post_pmexs=post_pmexs)
                ss = [s for s in ss if float(s.price) > 92 or int(s.userId) in mcs.keys()]
                if ss:
                    ad: Ad = ss[0]
                    await self.bbot.send(
                        193017646,
                        f"price: {ad.price}\nnick: {ad.nickName}\nprice: {ad.price}"
                        f"\nqty: {ad.quantity} [{ad.minAmount}-{ad.maxAmount}]",
                    )
                    am = min(float(ad.maxAmount), max(10000 + i, float(ad.minAmount)))
                    req = TakeAdReq(
                        ad_id=ad.id,
                        amount=am,
                        pm_id=14,
                        is_sell=True,
                        coin_id=1,
                        cur_id=1,
                    )
                    ord_resp: OrderResp = await self.take_ad(req)
                    # order: OrderFull = OrderFull(**self.api.get_order_details(orderId=ord_resp.orderId)["result"])
                    order: OrderFull = await self.get_order_info(ord_resp.orderId)
                    odb = await self.create_order_db(order)
                    # t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
                    # await t.fetch_related("order__cred__pmcur__cur")
                    # res = await self.pm_clients[366].check_in(t)
                    await sleep(2)
                    if int(ad.userId) in mcs:
                        mcs[int(ad.userId)].api.mark_as_paid(
                            orderId=str(odb.exid),
                            paymentType=str(order.paymentTermList[0].paymentType),  # pmex.exid
                            paymentId=order.paymentTermList[0].id,  # credex.exid
                        )
                    await sleep(3)
                    self.api.release_assets(orderId=order.id)
                await sleep(5)

            except Exception as e:
                logging.exception(e)
                await sleep(30)
            except HttpProcessingError as e:
                logging.error(e)
            print(end=".", flush=True)
            i += 1
            await sleep(5)

    async def boost_acc(self):
        await sleep(45)
        for i in range(10):
            am = 500 + i
            req = TakeAdReq(ad_id="1856989782009487360", amount=am, pm_id=366)
            ord_resp: OrderResp = await self.take_ad(req)
            order: OrderFull = OrderFull(**self.api.get_order_details(orderId=ord_resp.orderId)["result"])
            odb = await self.create_order_db(order)
            t = await models.Transfer(order=odb, amount=odb.amount, updated_at=now())
            await t.fetch_related("order__cred__pmcur__cur")
            await self.pm_clients[366].send(t)
        ...

    pm_clients: dict[int, PmAgentClient]

    async def start_listen(self):
        t = await self.ott()
        ts = int(float(t["time_now"]) * 1000)
        await self.ws_prv(self.agent.auth["cookies"]["deviceId"], t["result"], ts)

    # 3N: [T] - Уведомление об одобрении запроса на сделку
    async def request_accepted_notify(self) -> int: ...  # id

    async def ws_prv(self, did: str, tok: str, ts: int):
        u = f"wss://ws2.bybit.com/private?appid=bybit&os=web&deviceid={did}&timestamp={ts}"
        async with websockets.connect(u) as websocket:
            auth_msg = json.dumps({"req_id": did, "op": "login", "args": [tok]})
            await websocket.send(auth_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"SUPER_DEAL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"OTC_ORDER_STATUS"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"WEB_THREE_SELL"}']})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "input", "args": ["FIAT_OTC_TOPIC", '{"topic":"APPEALED_CHANGE"}']})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-eftd-complete-privilege-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.cashier.order-savings-product-event"]})
            await websocket.send(sub_msg)
            sub_msg = json.dumps({"op": "subscribe", "args": ["fiat.deal-core.order-savings-complete-event"]})
            await websocket.send(sub_msg)

            sub_msg = json.dumps({"op": "subscribe", "args": ["FIAT_OTC_TOPIC", "FIAT_OTC_ONLINE_TOPIC"]})
            await websocket.send(sub_msg)
            while resp := await websocket.recv():
                if data := json.loads(resp):
                    upd, order_db = None, None
                    logging.info(f" {now().strftime('%H:%M:%S')} upd: {data.get('topic')}:{data.get('type')}")
                    match data.get("topic"):
                        case "OTC_ORDER_STATUS":
                            match data["type"]:
                                case "STATUS_CHANGE":
                                    try:
                                        upd = StatusChange.model_validate(data["data"])
                                    except ValidationError as e:
                                        logging.error(e)
                                        logging.error(data["data"])
                                    order = self.api.get_order_details(orderId=upd.id)
                                    order = OrderFull.model_validate(order["result"])
                                    order_db = await models.Order.get_or_none(
                                        exid=order.id, ad__exid=order.itemId
                                    ) or await self.create_order_db(order)
                                    match upd.status:
                                        case Status.created:
                                            logging.info(f"Order {order.id} created at {order.createDate}")
                                            # сразу уменьшаем доступный остаток монеты/валюты
                                            await self.money_upd(order_db)
                                            if upd.side:  # я покупатель - ждем мою оплату
                                                _dest = order.paymentTermList[0].accountNo
                                                if not re.match(r"^([PpРр])\d{7,10}\b", _dest):
                                                    continue
                                                await order_db.fetch_related("ad__pair_side__pair", "cred__pmcur__cur")
                                                await self.send_payment(order_db)
                                        case Status.wait_for_buyer:
                                            if upd.side == 0:  # ждем когда покупатель оплатит
                                                if not (pmacdx := await self.get_pma_by_cdex(order)):
                                                    continue
                                                pma, cdx = pmacdx
                                                am, tid = await pma.check_in(
                                                    float(order.amount),
                                                    cdx.cred.pmcur.cur.ticker,
                                                    # todo: почему в московском час.поясе?
                                                    datetime.fromtimestamp(float(order.transferDate) / 1000),
                                                )
                                                if not tid:
                                                    logging.info(
                                                        f"Order {order.id} created at {order.createDate}, not paid yet"
                                                    )
                                                    continue
                                                try:
                                                    t, is_new = await models.Transfer.update_or_create(
                                                        dict(
                                                            amount=int(float(order.amount) * 100),
                                                            order=order_db,
                                                        ),
                                                        pmid=tid,
                                                    )
                                                except IntegrityError as e:
                                                    logging.error(tid)
                                                    logging.error(order)
                                                    logging.exception(e)

                                                if not is_new:  # если по этому платежу уже отпущен другая продажа
                                                    continue

                                                # если висят незавершенные продажи с такой же суммой
                                                pos = (await self.get_pending_orders(1))["result"]
                                                pos = [
                                                    o
                                                    for o in pos.get("items", [])
                                                    if (
                                                        o["amount"] == order.amount
                                                        and o["id"] != upd.id
                                                        and int(order.createDate)
                                                        < int(o["createDate"]) + 15 * 60 * 1000
                                                        # get full_order from o, and cred or pm from full_order:
                                                        and self.api.get_order_details(orderId=o["id"])["result"][
                                                            "paymentTermList"
                                                        ][0]["accountNo"]
                                                        == order.paymentTermList[0].accountNo
                                                    )
                                                ]
                                                curex = await models.CurEx.get(
                                                    cur__ticker=order.currencyId, ex=self.ex_client.ex
                                                )
                                                pos_db = await models.Order.filter(
                                                    exid__not=order.id,
                                                    cred_id=order_db.cred_id,
                                                    amount=int(float(order.amount) * 10**curex.scale),
                                                    status__not_in=[OrderStatus.completed, OrderStatus.canceled],
                                                    created_at__gt=now() - timedelta(minutes=15),
                                                )
                                                if pos or pos_db:
                                                    await self.ex_client.bot.send(
                                                        f"[Duplicate amount!]"
                                                        f"(https://www.bybit.com/ru-RU/p2p/orderList/{order.id})",
                                                        self.actor.person.user.username_id,
                                                    )
                                                    logging.warning("Duplicate amount!")
                                                    continue

                                                # !!! ОТПРАВЛЯЕМ ДЕНЬГИ !!!
                                                self.api.release_assets(orderId=upd.id)
                                                logging.info(
                                                    f"Order {order.id} created, paid before #{tid}:{am} at {order.createDate}, and RELEASED at {now()}"
                                                )
                                            elif upd.side == 1:  # я покупатель - ждем мою оплату
                                                continue  # logging.warning(f"Order {order.id} PAID at {now()}: {int_am}")
                                            else:
                                                ...
                                            # todo: check is always canceling
                                            # await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                                            # logging.info(f"Order {order.id} canceled at {datetime.now()}")

                                        case Status.wait_for_seller:
                                            if order_db.status == OrderStatus.paid:
                                                continue
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.paid,
                                                    "payed_at": datetime.fromtimestamp(
                                                        float(order.transferDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            logging.info(f"Order {order.id} payed at {order_db.payed_at}")

                                        case Status.appealed:
                                            # todo: appealed by WHO? щас наугад стоит by_seller
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.appealed_by_seller,
                                                    "appealed_at": datetime.fromtimestamp(
                                                        float(order.updateDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            logging.info(f"Order {order.id} appealed at {order_db.appealed_at}")

                                        case Status.canceled:
                                            await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                                            logging.info(f"Order {order.id} canceled at {datetime.now()}")
                                            await self.money_upd(order_db)

                                        case Status.completed:
                                            await order_db.update_from_dict(
                                                {
                                                    "status": OrderStatus.completed,
                                                    "confirmed_at": datetime.fromtimestamp(
                                                        float(order.updateDate) / 1000
                                                    ),
                                                }
                                            ).save()
                                            await self.money_upd(order_db)

                                        case _:
                                            logging.warning(f"Order {order.id} UNKNOWN STATUS {datetime.now()}")
                                case "COUNT_DOWN":
                                    upd = CountDown.model_validate(data["data"])
                                case _:
                                    self.listen(data)
                        case "OTC_USER_CHAT_MSG":
                            match data["type"]:
                                case "RECEIVE":
                                    upd = Receive.model_validate(data["data"])
                                    if order_db := await models.Order.get_or_none(
                                        exid=upd.orderId, ad__maker__ex=self.actor.ex
                                    ).prefetch_related("ad__pair_side__pair", "cred__pmcur__cur"):
                                        im_taker = order_db.taker_id == self.actor.id
                                        im_buyer = order_db.ad.pair_side.is_sell == im_taker
                                        if order_db.ad.auto_msg != upd.message and upd.roleType == "user":
                                            msg, _ = await models.Msg.update_or_create(
                                                {
                                                    "to_maker": upd.userId == self.actor.exid and im_taker,
                                                    "sent_at": datetime.fromtimestamp(float(upd.createDate) / 1000),
                                                },
                                                txt=upd.message,
                                                order=order_db,
                                            )
                                            if not upd.message:
                                                ...
                                            if im_buyer and (g := re.match(r"^[PpРр]\d{7,10}\b", upd.message)):
                                                if not order_db.cred.detail.startswith(dest := g.group()):
                                                    order_db.cred.detail = dest
                                                    await order_db.save()
                                                await self.send_payment(order_db)
                                case "READ":
                                    upd = Read.model_validate(data["data"])
                                    # if upd.status not in (StatusWs.created, StatusWs.canceled, 10, StatusWs.completed):
                                    if upd.orderStatus in (
                                        Status.wait_for_buyer,
                                    ):  # todo: тут приходит ордер.статус=10, хотя покупатель еще не нажал оплачено
                                        order = self.api.get_order_details(orderId=upd.orderId)["result"]
                                        order = OrderFull.model_validate(order)

                                case "CLEAR":
                                    continue
                                case _:
                                    self.listen(data)
                        case "OTC_USER_CHAT_MSG_V2":
                            # match data["type"]:
                            #     case "RECEIVE":
                            #         upd = Receive.model_validate(data["data"])
                            #     case "READ":
                            #         upd = Read.model_validate(data["data"])
                            #     case "CLEAR":
                            #         pass
                            #     case _:
                            #         self.listen(data)
                            continue
                        case "SELLER_CANCEL_CHANGE":
                            upd = SellerCancelChange.model_validate(data["data"])
                        case None:
                            if not data.get("success"):
                                logging.error(data, "NOT SUCCESS!")
                            else:
                                continue  # success login, subscribes, input
                        case _:
                            logging.warning(data, "UNKNOWN TOPIC")
                    ...
                    if not upd:
                        logging.warning(data, "NOT PROCESSED UPDATE")

    async def money_upd(self, odb: models.Order):
        # обновляем остаток монеты
        await odb.fetch_related("ad__pair_side__pair", "ad__my_ad__credexs__cred__fiat", "cred__pmcur", "transfer")
        ass = await models.Asset.get(addr__coin_id=odb.ad.pair_side.pair.coin_id, addr__actor=self.actor)
        # обновляем остаток валюты
        im_maker = odb.ad.maker_id == self.actor.id
        im_seller = odb.ad.pair_side.is_sell == im_maker
        if im_maker:
            if _fiats := [cx.cred.fiat for cx in odb.ad.my_ad.credexs if cx.cred.fiat]:
                fiat = _fiats[0]
                await fiat.fetch_related("cred__pmcur__pm")
            else:
                raise ValueError(odb, "No Fiat")
        elif im_seller:  # im taker
            fltr = dict(cred__person_id=self.actor.person_id)
            fltr |= (
                {"cred__ovr_pm_id": odb.cred.ovr_pm_id, "cred__pmcur__cur_id": odb.cred.pmcur.cur_id}
                if odb.cred.ovr_pm_id
                else {"cred__pmcur_id": odb.cred.pmcur_id}
            )
            if not (fiat := await models.Fiat.get_or_none(**fltr).prefetch_related("cred__pmcur__pm")):
                raise ValueError(odb, "No Fiat")
        fee = round(odb.amount * (fiat.cred.pmcur.pm.fee or 0) * 0.0001)
        # k = int(im_seller) * 2 - 1  # im_seller: 1, im_buyer: -1
        if odb.status == OrderStatus.created:
            if im_seller:
                ass.free -= odb.quantity
                ass.freeze += odb.quantity
            else:  # я покупатель
                fiat.amount -= odb.amount + fee
        elif odb.status == OrderStatus.completed:
            if im_seller:
                fiat.amount += odb.amount
            else:  # я покупатель
                ass.free += odb.quantity
        elif odb.status == OrderStatus.canceled:
            if im_seller:
                ass.free += odb.quantity
                ass.freeze -= odb.quantity
            else:  # я покупатель
                fiat.amount += odb.amount + fee
        else:
            logging.exception(odb.id, f"STATUS: {odb.status.name}")
        await ass.save(update_fields=["free", "freeze"])
        await fiat.save(update_fields=["amount"])
        logging.info(f"Order #{odb.id} {odb.status.name}. Fiat: {fiat.amount}, Asset: {ass.free}")

    async def send_payment(self, order_db: models.Order):
        if order_db.status != OrderStatus.created:
            return
        fmt_am = round(order_db.amount * 10**-2, 2)
        pma, cur = await self.get_pma_by_pmex(order_db)
        async with in_transaction():
            # отмечаем ордер на бирже "оплачен"
            pmex = await models.PmEx.get(pm_id=order_db.cred.pmcur.pm_id, ex=self.actor.ex)
            credex = await models.CredEx.get(cred=order_db.cred, ex=self.actor.ex)
            self.api.mark_as_paid(
                orderId=str(order_db.exid),
                paymentType=pmex.exid,  # pmex.exid
                paymentId=str(credex.exid),  # credex.exid
            )
            # проверяем не отправляли ли мы уже перевод по этому ордеру
            if t := await models.Transfer.get_or_none(order=order_db, amount=order_db.amount):
                await pma.bot.send(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!",
                    self.actor.person.user.username_id,
                )
                raise Exception(
                    f"Order# {order_db.exid}: Double send {fmt_am}{cur} to {order_db.cred.detail} #{t.pmid}!"
                )

            # ставим в бд статус "оплачен"
            order_db.status = OrderStatus.paid
            order_db.payed_at = datetime.now(timezone.utc)
            await order_db.save()
            # создаем перевод в бд
            t = models.Transfer(order=order_db, amount=order_db.amount, updated_at=now())
            # отправляем деньги
            tid, img = await pma.send(t)
            t.pmid = tid
            await t.save()
            await self.send_receipt(str(order_db.exid), tid)  # отправляем продавцу чек
            logging.info(f"Order {order_db.exid} PAID at {datetime.now()}: {fmt_am}!")

    async def send_receipt(self, oexid: str, tid: int) -> tuple[PmAgentClient | None, models.CredEx] | None:
        try:
            if res := self.api.upload_chat_file(upload_file=f"tmp/{tid}.png").get("result"):
                await sleep(0.5)
                self.api.send_chat_message(orderId=oexid, contentType="pic", message=res["url"], msgUuid=uuid4().hex)
        except Exception as e:
            logging.error(e)
        await sleep(0.5)
        self.api.send_chat_message(orderId=oexid, contentType="str", message=f"#{tid}", msgUuid=uuid4().hex)

    async def get_pma_by_cdex(self, order: OrderFull) -> tuple[PmAgentClient | None, models.CredEx] | None:
        cdxs = await models.CredEx.filter(
            ex=self.ex_client.ex,
            exid__in=[ptl.id for ptl in order.paymentTermList],
            cred__person=self.actor.person,
        ).prefetch_related("cred__pmcur__cur")
        pmas = [pma for cdx in cdxs if (pma := self.pm_clients.get(cdx.cred.pmcur.pm_id))]
        if not len(pmas):
            # raise ValueError(order.paymentTermList, f"No pm_agents for {order.paymentTermList[0].paymentType}")
            return None
        elif len(pmas) > 1:
            logging.error(order.paymentTermList, f">1 pm_agents for {cdxs[0].cred.pmcur.pm_id}")
        else:
            return pmas[0], cdxs[0]

    async def get_pma_by_pmex(self, order_db: models.Order) -> tuple[PmAgentClient, str]:
        pma = self.pm_clients.get(order_db.cred.pmcur.pm_id)
        if pma:
            return pma, order_db.cred.pmcur.cur.ticker
        logging.error(f"No pm_agents for {order_db.cred.pmcur.pm_id}")

    @staticmethod
    def listen(data: dict | None):
        # print(data)
        ...


def ms2utc(msk_ts_str: str):
    return datetime.fromtimestamp(int(msk_ts_str) / 1000, timezone(timedelta(hours=3), name="MSK"))


def detailed_diff(str1, str2):
    matcher = SequenceMatcher(None, str1, str2)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.append(str1[i1:i2])
        elif tag == "delete":
            result.append(f"[-{str1[i1:i2]}]")
        elif tag == "insert":
            result.append(f"[+{str2[j1:j2]}]")
        elif tag == "replace":
            result.append(f"[{str1[i1:i2]}→{str2[j1:j2]}]")

    return "".join(result)


class ExcCode(IntEnum):
    FixPriceLimit = 912120022
    RareLimit = 912120050
    InsufficientBalance = 912120024
    Timestamp = 10002
    IP = 10010
    Quantity = 912300019
    PayMethod = 912300013
    Unknown = 912300014


@post_save(models.Race)
async def race_upserted(
    _cls: type[models.Race], race: models.Race, created: bool, _db: BaseDBAsyncClient, _updated: list[str]
):
    logging.warning(f"Race {race.id} is now upserted")
    asyncio.all_tasks()
    if created:
        ...
    else:  # параметры гонки изменены
        ...


async def main():
    logging.basicConfig(level=logging.INFO)
    cn = await init_db(TORM)

    agent = (
        await models.Agent.filter(actor__ex_id=4, auth__isnull=False, status__gt=AgentStatus.off, id=2)
        .prefetch_related(
            "actor__ex",
            "actor__person__user__gmail",
            "actor__my_ads__my_ad__race",
            "actor__my_ads__pair_side__pair__cur",
            "actor__my_ads__pms",
        )
        .first()
    )
    filebot = FileClient(NET_TOKEN)
    # await filebot.start()
    # b.add_handler(MessageHandler(cond_start_handler, command("cond")))
    ex = await models.Ex.get(name="Bybit")
    ecl: ExClient = ex.client(filebot)
    abot = XyncBot(PAY_TOKEN, cn)
    # pmas = await models.PmAgent.filter(active=True, user_id=1).prefetch_related("pm", "user__gmail")
    # pm_clients = {pma.pm_id: pma.client(abot) for pma in pmas}
    prx = PRX and "http://" + PRX
    cl: AgentClient = agent.client(ecl, filebot, abot, proxy=prx)

    # req = TakeAdReq(ad_id=1955696985964089344, amount=504, pm_id=128)
    # await cl.take_ad(req)

    # await cl.actual_cond()
    # cl.get_api_orders(),  # 10, 1738357200000, 1742504399999

    # await cl.ex_client.set_pairs()
    # await cl.ex_client.set_pms()

    # await cl.set_creds()
    # await cl.export_my_ads()

    my_ad = await models.MyAd[5]
    await cl.ad_share(my_ad.id)
    await cl.start_listen()

    ms = await models.Agent.filter(
        actor__ex_id=4, auth__isnull=False, status__gt=AgentStatus.off, actor__person__user__id__in=[3]
    ).prefetch_related(
        "actor__ex",
        "actor__person__user__gmail",
        "actor__my_ads__my_ad__race",
        "actor__my_ads__pair_side__pair__cur",
        "actor__my_ads__pms",
    )
    mcs = {m.actor.exid: m.client(ecl, filebot, abot) for m in ms}

    await gather(
        # create_task(cl.start()),
        create_task(cl.watch_payeer(mcs)),
    )
    # ensure_future(cl.start(True))
    # await cl.boost_acc()

    # создание гонок по мои активным объявам:
    # for ma in cl.my_ads():
    #     my_ad = await models.MyAd.get(ad__exid=ma.id).prefetch_related('ad__pms', 'ad__pair_side__pair')
    #     race, _ = await models.Race.update_or_create(
    #         {"started": True, "vm_filter": True, "target_place": 5},
    #         road=my_ad
    #     )

    # for name in names:
    #     s, _ = await models.Synonym.update_or_create(typ=SynonymType.name, txt=name)
    #     await s.curs.add(rub.cur)

    pauth = (await models.PmAgent[1]).auth
    papi = PayeerAPI(pauth["email"], pauth["api_id"], pauth["api_sec"])
    hist: dict = papi.history(count=1000)
    hist |= papi.history(count=1000, append=list(hist.keys())[-1])
    hist |= papi.history(count=1000, append=list(hist.keys())[-1])
    cl.hist = hist

    # cl.completed_orders = await models.Order.filter(status=OrderStatus.completed, transfer__isnull=False).values_list(
    #     "exid", flat=True
    # )
    # await cl.get_api_orders()  # 43, 1741294800000, 1749157199999)

    # await cl.cancel_order(res.orderId)
    await filebot.stop()
    await cl.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down")
