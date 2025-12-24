import logging
import re
from asyncio import create_task
from datetime import datetime, timedelta
from bybit_p2p import P2P
from pyro_client.client.file import FileClient
from tortoise.exceptions import IntegrityError
from tortoise.timezone import now
from xync_bot import XyncBot
from xync_schema.models import Agent

from xync_client.Bybit.agent import AgentClient
from xync_client.Bybit.ex import ExClient

from xync_schema import models
from xync_schema.enums import OrderStatus

from xync_client.Bybit.etype.order import (
    StatusChange,
    CountDown,
    SellerCancelChange,
    Read,
    Receive,
    OrderFull,
    OrderItem,
    Status,
)


class InAgentClient(AgentClient):
    actor: models.Actor
    agent: models.Agent
    api: P2P
    ex_client: ExClient

    orders: dict[int, models.Order] = {}

    def __init__(self, agent: Agent, ex_client: ExClient, fbot: FileClient, bbot: XyncBot, **kwargs):
        super().__init__(agent, ex_client, fbot, bbot, **kwargs)
        create_task(self.load_pending_orders())

    async def load_pending_orders(self):
        po: dict[int, OrderItem] = await self.get_pending_orders()
        if isinstance(po, int):  # если код ошибки вместо результата
            raise ValueError(po)
        self.orders = {o.exid: o for o in await models.Order.filter(exid__in=po.keys())}
        for oid in po.keys() - self.orders.keys():
            fo = self.api.get_order_details(orderId=oid)
            self.orders[oid] = await self.create_order_db(fo)

    async def proc(self, data: dict):
        match data.get("topic"):
            case "OTC_ORDER_STATUS":
                match data["type"]:
                    case "STATUS_CHANGE":
                        upd = StatusChange.model_validate(data["data"])

                        if order_db := self.orders.get(upd.id):
                            order_db.status = OrderStatus[Status(data["status"]).name]
                            await order_db.save()
                        order = self.api.get_order_details(orderId=upd.id)
                        order = OrderFull.model_validate(order["result"])
                        order_db = await models.Order.get_or_none(
                            exid=order.id, ad__exid=order.itemId
                        ) or await self.create_order(order)
                        match upd.status:
                            case Status.ws_new:
                                logging.info(f"Order {order.id} created at {order.createDate}")
                                # сразу уменьшаем доступный остаток монеты/валюты
                                await self.money_upd(order_db)
                                if upd.side:  # я покупатель - ждем мою оплату
                                    _dest = order.paymentTermList[0].accountNo
                                    if not re.match(r"^([PpРр])\d{7,10}\b", _dest):
                                        return
                                    await order_db.fetch_related("ad__pair_side__pair", "cred__pmcur__cur")
                                    await self.send_payment(order_db)
                            case Status.created:
                                if upd.side == 0:  # ждем когда покупатель оплатит
                                    if not (pmacdx := await self.get_pma_by_cdex(order)):
                                        return
                                    pma, cdx = pmacdx
                                    am, tid = await pma.check_in(
                                        float(order.amount),
                                        cdx.cred.pmcur.cur.ticker,
                                        # todo: почему в московском час.поясе?
                                        datetime.fromtimestamp(float(order.transferDate) / 1000),
                                    )
                                    if not tid:
                                        logging.info(f"Order {order.id} created at {order.createDate}, not paid yet")
                                        return
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
                                        return

                                    # если висят незавершенные продажи с такой же суммой
                                    pos = (await self.get_orders_active(1))["result"]
                                    pos = [
                                        o
                                        for o in pos.get("items", [])
                                        if (
                                            o["amount"] == order.amount
                                            and o["id"] != upd.id
                                            and int(order.createDate) < int(o["createDate"]) + 15 * 60 * 1000
                                            # get full_order from o, and cred or pm from full_order:
                                            and self.api.get_order_details(orderId=o["id"])["result"][
                                                "paymentTermList"
                                            ][0]["accountNo"]
                                            == order.paymentTermList[0].accountNo
                                        )
                                    ]
                                    curex = await models.CurEx.get(cur__ticker=order.currencyId, ex=self.ex_client.ex)
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
                                        return

                                    # !!! ОТПРАВЛЯЕМ ДЕНЬГИ !!!
                                    self.api.release_assets(orderId=upd.id)
                                    logging.info(
                                        f"Order {order.id} created, paid before #{tid}:{am} at {order.createDate}, and RELEASED at {now()}"
                                    )
                                elif upd.side == 1:  # я покупатель - ждем мою оплату
                                    return  # logging.warning(f"Order {order.id} PAID at {now()}: {int_am}")
                                else:
                                    ...
                                # todo: check is always canceling
                                # await order_db.update_from_dict({"status": OrderStatus.canceled}).save()
                                # logging.info(f"Order {order.id} canceled at {datetime.now()}")

                            case Status.wait_for_seller:
                                if order_db.status == OrderStatus.paid:
                                    return
                                await order_db.update_from_dict(
                                    {
                                        "status": OrderStatus.paid,
                                        "payed_at": datetime.fromtimestamp(float(order.transferDate) / 1000),
                                    }
                                ).save()
                                logging.info(f"Order {order.id} payed at {order_db.payed_at}")

                            case Status.appealed:
                                # todo: appealed by WHO? щас наугад стоит by_seller
                                await order_db.update_from_dict(
                                    {
                                        "status": OrderStatus.appealed_by_seller,
                                        "appealed_at": datetime.fromtimestamp(float(order.updateDate) / 1000),
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
                                        "confirmed_at": datetime.fromtimestamp(float(order.updateDate) / 1000),
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
                        return
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
                return
            case "SELLER_CANCEL_CHANGE":
                upd = SellerCancelChange.model_validate(data["data"])
            case None:
                if not data.get("success"):
                    logging.error(data, "NOT SUCCESS!")
                else:
                    return  # success login, subscribes, input
            case _:
                logging.warning(data, "UNKNOWN TOPIC")
        ...
        if not upd:
            logging.warning(data, "NOT PROCESSED UPDATE")
