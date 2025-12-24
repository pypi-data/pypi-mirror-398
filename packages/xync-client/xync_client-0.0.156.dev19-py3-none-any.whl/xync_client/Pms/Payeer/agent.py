import time
from collections import defaultdict
from copy import copy
from itertools import groupby

import undetected_chromedriver as uc
import websockets

from aiohttp import ClientResponse
from asyncio import run, sleep
from base64 import b64encode
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from datetime import datetime, timedelta
from hashlib import sha256
from json import dumps, loads
from math import ceil
from os import urandom
from payeer_api import PayeerAPI
from re import search
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlencode
from x_client.aiohttp import Client
from xync_bot import XyncBot
from xync_schema import models

from xync_client.loader import PAY_TOKEN


def encrypt_data(data: dict, md5digest: bytes):
    # Convert data to JSON string (equivalent to json_encode)
    bdata = dumps(data).encode()

    # Generate random IV (16 bytes for AES)
    iv = urandom(16)

    # Pad or truncate key to 32 bytes
    if len(md5digest) < 32:
        md5digest = md5digest.ljust(32, b"\0")  # Pad with null bytes
    elif len(md5digest) > 32:
        md5digest = md5digest[:32]  # Truncate to 32 bytes

    # Apply PKCS7 padding
    padder = padding.PKCS7(128).padder()  # 128 bits = 16 bytes block size
    padded_data = padder.update(bdata)
    padded_data += padder.finalize()

    # Create cipher
    cipher = Cipher(AES(md5digest), CBC(iv))
    encryptor = cipher.encryptor()

    # Encrypt
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return iv + ciphertext


rep = {
    "USDT": "UST",
    "DOGE": "DOG",
    "DASH": "DAA",
    "MANA": "MA2",
    "METIS": "ME2",
    "AUDIO": "AU2",
    "MASK": "MA3",
    "SUPER": "SU2",
    "USDP": "US2",
}


class PmAgentClient(Client):
    host = "payeer.com/"
    headers = {
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    cookies = {"isAuthorized": "true"}
    api: PayeerAPI
    pages: dict[str, str] = {
        "login": f"https://{host}en/auth/",
        "home": f"https://{host}en/account/",
    }
    _ceils: tuple[float, float]

    balances: dict[str, float] = {}  # {cur: available}
    orders: dict[int, dict] = defaultdict()  # {(quote, cur): (price, amount)}
    orders_dict: dict[str, dict[str, dict]] = defaultdict()  # {(quote, cur): (price, amount)}

    def __init__(self, agent: models.PmAgent, bot: XyncBot = None):
        self.agent = agent
        self.bot = bot
        super().__init__(self.host, cookies=self.agent.state["cookies"])
        # if api_id := agent.auth.get("api_id"):
        #     self.api = PayeerAPI(agent.auth["email"], api_id, agent.auth["api_sec"])
        # if trade_id := agent.auth.get("trade_id"):
        #     self.tapi = PayeerTradeAPI(trade_id, agent.auth["trade_sec"])
        # create_task(self.heartbeat())

    async def login(self):
        async def _save():
            self.agent.state["cookies"] = {c["name"]: c["value"] for c in cd.get_cookies() if c["name"] == "PHPSESSID"}
            self.agent.state["sessid"] = search(r"'bitrix_sessid':'([0-9a-f]{32})'", cd.page_source).group(1)
            if not self.agent.auth.get("UserID"):
                self.agent.auth["UserID"] = search(r"/?UserID=(\d{7,8})&", cd.page_source).group(1)
            await self.agent.save()
            super().__init__(self.host, cookies=self.agent.state["cookies"])

        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")  # for Chrome >= 109
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-oopr-debug-crash-dump")
        options.add_argument("--no-crash-upload")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-low-res-tiling")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        cd = uc.Chrome(
            options=options,
            headless=False,
            browser_executable_path="/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
        )
        wait = WebDriverWait(cd, timeout=15)
        cd.get("https://payeer.com/en/")
        wait.until(ec.invisibility_of_element_located((By.TAG_NAME, "lottie-player")))
        login_link = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "button.button_empty")))
        login_link.click()
        email_field = wait.until(ec.presence_of_element_located((By.NAME, "email")))
        email_field.send_keys(self.agent.auth.get("email"))
        password_field = wait.until(ec.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(self.agent.auth.get("password"))
        login_button = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "login-form__login-btn.step1")))
        await sleep(1)
        login_button.click()
        await sleep(4)
        # check if logged in
        if not cd.current_url.startswith(self.pages["login"]):
            if cd.current_url.startswith(self.pages["home"]):
                return await _save()
        # we are NOT logged in
        login_button.click()
        await sleep(1)
        if (v := cd.find_elements(By.CLASS_NAME, "form-input-top")) and v[0].text == "Введите проверочный код":
            code = input("Email code: ")
            actions = ActionChains(cd)
            for char in code:
                actions.send_keys(char).perform()
            step2_button = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "login-form__login-btn.step2")))
            step2_button.click()
        # check if logged in
        if not cd.current_url.startswith(self.pages["login"]):
            if cd.current_url.startswith(self.pages["home"]):
                return await _save()
        # we are NOT logged in
        await self.bot.send(193017646, "Payeer not logged in", photo=cd.get_screenshot_as_png())
        cd.quit()
        raise Exception("Payeer not logged in")

    async def heartbeat(self):
        """Фоновая задача для PING/PONG"""
        url = "bitrix/components/payeer/account.info2/templates/top2/ajax.php"
        params = {"action": "balance2", "sessid": self.agent.state["sessid"], "_": int(time.time() * 1000)}
        resp = await self.session.get(url, params=params)
        if not resp.content.total_bytes:  # check
            await self.login()
            params["sessid"] = self.agent.state["sessid"]
        while self.agent.active:
            await sleep(30)
            params["_"] = int(time.time() * 1000)
            bb = await self._get("bitrix/components/payeer/account.info2/templates/top2/ajax.php", params)
            avlb = {c: fb for c, b in bb["balance"].items() if (fb := float(".".join([b[0].replace(",", ""), b[1]])))}
            print(avlb, end=" ")
            await self.agent.refresh_from_db()
        await self.stop()

    async def send(self, recip: str, amount: float, cur_id: int) -> int | list:
        cur = await models.Cur[cur_id]
        data = {
            "payout_method": 1136053,
            "template_pay": "",
            "param_ACCOUNT_NUMBER": recip,
            "comment": "",
            "protect_code": "",
            "protect_day": 1,
            "sum_receive": amount,
            "curr_receive": cur.ticker,
            "sum_pay": round(amount * 1.005, 2),
            "curr_pay": cur.ticker,
            "mfa_code": "",
            "master_key": "",
            "block": 0,
            "ps": 1136053,
            "sign": "",
            "output_type": "list",
            "fee_0": "N",
            "sessid": self.agent.state["sessid"],
        }
        url = "bitrix/components/payeer/account.send.08_18/templates/as_add11/ajax.php?action=output"
        res = await self._post(url, form_data=data)
        if res["success"]:
            return res["id"]
        return res["error"]

    async def check_in(self, amount: float, cur: str, dt: datetime = None, tid: int = None) -> dict[int, float]:
        history = self.api.history(type="incoming", count=10)
        if tid:
            return (t := history.get(tid)) and {t["id"]: float(t["creditedAmount"])}
        return {
            h["id"]: float(h["creditedAmount"])
            for h in history.values()
            if (
                amount <= float(h["creditedAmount"]) <= ceil(amount)
                and h["creditedCurrency"] == cur
                and datetime.fromisoformat(h["date"]) > dt - timedelta(minutes=3)  # +180(tz)-5 # todo: wrong tz
            )
        }

    async def ws(self, quote: str, fiat: str):  # pair="UST_RUB"
        pair = "_".join(rep.get(c, c[:2] + "1") if len(c) > 3 else c for c in [quote, fiat])
        uid = self.agent.auth["UserID"]
        psid = self.agent.state["cookies"]["PHPSESSID"]
        ws_url = f"wss://payeer.com/wss/socket.io/?UserID={uid}&auth_hash={psid}&EIO=4&transport=websocket"
        _sig = None
        bids: dict[float, float] = {}
        asks: dict[float, float] = {}
        async with websockets.connect(ws_url) as websocket:
            while resp := await websocket.recv():
                if resp.startswith("0"):
                    await websocket.send("40")
                elif resp.startswith("40"):
                    _sig = loads(resp.lstrip("40"))["sid"]
                    await websocket.send('42["pair change",{"pair":"' + pair + '"}]')
                elif resp == "2":  # ping?
                    await websocket.send("3")  # pong?
                elif (resp := resp.lstrip("42")) and resp.startswith("["):
                    data = loads(resp)
                    topic, data = data.pop(0), data.pop(0)
                    if topic == "toall":
                        if dif := data["data"].get("diff"):  # это обновление стакана (мейкеры изменили ставки)
                            am_acc = 0
                            bid_list = [
                                (float(p), am, am_acc := am_acc + am)
                                for p, a, r, _ in dif[0]
                                if (am := float(a)) > 2 and am_acc < 500
                            ]
                            old_bids: dict[float, float] = copy(bids)
                            bids = {price: amount for price, amount, acc in bid_list}
                            bids_dif = {p: ad for p, a in bids.items() if round(ad := a - old_bids.get(p, 0), 2)}
                            am_acc = 0
                            ask_list = [
                                (float(p), am, am_acc := am_acc + am)
                                for p, a, r, _ in dif[1]
                                if (am := float(a)) > 2 and am_acc < 500
                            ]
                            old_asks: dict[float, float] = copy(asks)
                            asks = {price: amount for price, amount, acc in ask_list}
                            asks_dif = {p: ad for p, a in asks.items() if round(ad := a - old_asks.get(p, 0), 2)}

                            self._ceils = bid_list[0][0], ask_list[0][0]
                            base = round(sum(self._ceils) / 2, 3)
                            spread = self._ceils[0] - self._ceils[1]
                            pspread = spread / base * 100
                            print(round(base, 4), round(spread, 2), f"{pspread:.2f}%")
                            print(bids, bids_dif)
                            print(asks, asks_dif)
                        elif data["handler"] == "onTradeHistory":
                            side = int(data["data"]["history"][0][1])
                            hist = {
                                time: {float(h[2]): float(h[3]) for h in g}
                                for time, g in groupby(data["data"]["history"], key=lambda x: x[0])
                            }
                            print(side, hist)
                            # (asks if side else bids)
                else:
                    raise ValueError(resp)

    async def get_ceils(self) -> tuple[float, float]:  # inside ceils + fee
        return self._ceils[0] * (1 + self.agent.pm.fee), self._ceils[1] * (1 - self.agent.pm.fee)

    @staticmethod
    def form_redirect(topup: models.TopUp) -> tuple[str, dict | None]:
        m_shop = str(topup.topupable.auth["id"])
        m_orderid = str(topup.id)
        m_amount = "{0:.2f}".format(topup.amount * 0.01)
        m_curr = topup.cur.ticker
        m_desc = b64encode(b"XyncPay top up").decode()
        m_key = topup.topupable.auth["sec"]
        data = [m_shop, m_orderid, m_amount, m_curr, m_desc]
        # # additional
        # m_params = {
        #     'success_url': 'https://xync.net/topup?success=1',
        #     'fail_url': 'https://xync.net/topup?success=0',
        #     'status_url': 'https://xync.net/topup',
        #     'reference': {'var1': '1'},
        # }
        #
        # key = md5(m_orderid.to_bytes()).digest()
        #
        # base64url_encode(encrypt_data(params, key))
        #
        # data.append(m_params)
        # # additional

        data.append(m_key)

        sign = sha256(":".join(data).encode()).hexdigest().upper()

        params = {
            "m_shop": m_shop,
            "m_orderid": m_orderid,
            "m_amount": m_amount,
            "m_curr": m_curr,
            "m_desc": m_desc,
            "m_sign": sign,
            # 'm_params': m_params,
            # 'm_cipher_method': 'AES-256-CBC-IV',
            "form[ps]": "2609",
            "form[curr[2609]]": m_curr,
        }
        url = "https://payeer.com/merchant/?" + urlencode(params)
        return url, None

    def get_topup(self, tid: str) -> dict:
        hi = self.api.get_history_info(tid)
        ti = self.api.shop_order_info(hi["params"]["SHOP_ID"], hi["params"]["ORDER_ID"])["info"]
        return ti["status"] == "execute" and {
            "pmid": ti["id"],
            "from_acc": hi["params"]["ACCOUNT_NUMBER"],
            "oid": hi["params"]["ORDER_ID"],
            "amount": int(float(ti["sumOut"]) * 100),
            "ts": datetime.strptime(ti["dateCreate"], "%d.%m.%Y %H:%M:%S") - timedelta(hours=3),
        }

    async def _proc(self, resp: ClientResponse, bp=None) -> dict | str:
        if resp.status == 200:
            await resp.read()
            # noinspection PyProtectedMember
            return loads(resp._body.strip())  # payeer bug: returns json with content-type=html
        raise Exception(resp)

    async def balance_load(self):
        self.balances = await self.tapi.acc()

    async def orders_load(self):
        self.orders = {
            int(oid): {
                "ts": o["date"],
                "pair": o["pair"].split("_"),
                "is_sell": o["action"] == "sell",
                "amount": float(o["amount"]),
                "price": float(o["price"]),
                "value": float(o["value"]),
                "amount_proc": float(o["amount_processed"]),
                "value_proc": float(o["value_processed"]),
            }
            for oid, o in (await self.tapi.orders()).items()
        }


async def main():
    from x_model import init_db
    from xync_client.loader import TORM

    cn = await init_db(TORM, True)
    agent = await models.PmAgent.get_or_none(pm__norm="payeer", user_id=1).prefetch_related("user", "pm")
    # tapi = PayeerTradeAPI(agent.auth['trade_id'], agent.auth['trade_sec'])
    # b = await tapi.acc()
    # rub_am, usdt_am = b['RUB']['available'], b['USDT']['available']
    # r = await tapi.trade('USDT_RUB', False, 10, 118.01)
    bbot = XyncBot(PAY_TOKEN, cn)
    cl: PmAgentClient = agent.client(bbot)
    await cl.ws("USDT", "RUB")

    while agent.active:
        await sleep(75)
        await cl.send("P1135398755", 10, 1)
        await agent.refresh_from_db()
    await cl.stop()


if __name__ == "__main__":
    run(main())
