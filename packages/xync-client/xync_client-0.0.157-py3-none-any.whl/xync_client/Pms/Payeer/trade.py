import hashlib
import hmac

from json import dumps
from time import time

from x_client.aiohttp import Client

maker_fee = 0.01
taker_fee = 0.095


class PayeerTradeAPI(Client):
    sec: bytes

    def __init__(self, key: str, sec: str):
        self.sec = sec.encode()
        super().__init__("payeer.com/", headers={"API-ID": key})

    async def _req(self, method: str, data: dict):
        h = hmac.new(self.sec, digestmod=hashlib.sha256)
        data["ts"] = int(time() * 1000)
        sdata = method + dumps(data)
        h.update(sdata.encode())
        sign = h.hexdigest()
        return await self._post("api/trade/" + method, data, hdrs={"API-SIGN": sign})

    async def acc(self) -> dict[str, dict[str, float]]:
        res = await self._req("account", {})
        return res["success"] and {c: b for c, b in res["balances"].items() if b["total"]}

    async def orders(self) -> dict[str, dict]:
        res = await self._req("my_orders", {})
        return res["success"] and res["items"]

    async def pairs(self) -> dict:
        res = await self._get("api/trade/info")
        return res["success"] and {
            p: {
                k: v for k, v in d.items() if k in ("price_prec", "min_price", "max_price", "amount_prec", "value_prec")
            }
            for p, d in res["pairs"].items()
        }

    async def trade(self, pair: str, sell: bool, amount: float, price: float) -> tuple[int, int]:
        data = {
            "pair": pair,
            "type": "limit",
            "action": "sell" if sell else "buy",
            "price": price,
            "amount": amount,
        }
        res = await self._req("order_create", data)
        return res["success"] and (res["order_id"], int(time()) + 60)

    async def cancel(self, oid: int) -> bool:
        res = await self._req("order_cancel", {"order_id": oid})
        return res["success"]
