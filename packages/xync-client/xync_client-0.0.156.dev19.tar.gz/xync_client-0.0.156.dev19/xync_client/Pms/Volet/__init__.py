import logging
import re
from asyncio import run
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256

from PGram import Bot
from playwright.async_api import async_playwright, Page, Locator, Position, Playwright, Browser  # , FloatRect
from pyotp import TOTP

# noinspection PyProtectedMember
from playwright._impl._errors import TimeoutError
from pyro_client.client.user import UserClient
from pyrogram.handlers import MessageHandler
from tortoise.timezone import now
from xync_schema import models
from xync_schema.enums import UserStatus
from xync_schema.models import Cur, User, PmAgent, Cred, PmCur, Fiat, TopUp, Transfer

from xync_client.Abc.PmAgent import PmAgentClient
from xync_client.Gmail import GmClient
from xync_client.Pms.Volet.api import APIClient
from xync_client.loader import PAY_TOKEN


class CaptchaException(Exception): ...


class OtpNotSetException(Exception): ...


class NoCodeException(Exception): ...


class NoMailException(Exception): ...


def parse_transaction_info(text: str) -> dict[str, str] | None:
    # Поиск ID транзакции
    transaction_id_match = re.search(r"Transaction ID:\s*([\w-]+)", text)
    # Поиск суммы и валюты
    amount_match = re.search(r"Amount:\s*([+-]?[0-9]*\.?[0-9]+)\s*([A-Z]+)", text)
    # Поиск email отправителя
    sender_email_match = re.search(r"Sender:\s*([\w.-]+@[\w.-]+)", text)

    if transaction_id_match and amount_match and sender_email_match:
        return {
            "transaction_id": transaction_id_match.group(1),
            "amount": amount_match.group(1),
            "currency": amount_match.group(2),
            "sender_email": sender_email_match.group(1),
        }
    return None


class Client(PmAgentClient):
    class Pages(StrEnum):
        base = "https://account.volet.com/"
        LOGIN = base + "login"
        OTP_LOGIN = base + "login/otp"
        # HOME = base + "pages/transaction"
        SEND = base + "pages/transfer/wallet"

    async def check_in(
        self, amount: int | Decimal | float, cur: str, dt: datetime, tid: str | int = None
    ) -> float | None:
        return await (self.api.check_by_id(tid) if tid else self.api.check_by_amount(amount, cur))

    async def proof(self) -> bytes:
        pass

    uid: int
    agent: PmAgent
    abot: Bot
    ubot: UserClient
    api: APIClient
    page: Page
    gmail: GmClient
    norm: str = "payeer"
    pages: type(StrEnum) = Pages
    with_userbot: bool = True

    def __init__(self, agent: PmAgent, browser: Browser, abot: Bot):
        super().__init__(agent, browser, abot)
        self.gmail = GmClient(agent.user)
        self.api = APIClient(self.agent.auth["api"], self.agent.auth["password"], self.agent.auth["login"])

    @staticmethod
    def form_redirect(topup: TopUp) -> tuple[str, dict | None]:
        ac_account_email = topup.topupable.auth["ac_account_email"]
        ac_sci_name = topup.topupable.auth["ac_sci_name"]
        ac_order_id = str(topup.id)
        ac_amount = "{0:.2f}".format(topup.amount * 0.01)
        ac_currency = topup.cur.ticker
        ac_comments = "XyncPay top up"
        secret = topup.topupable.auth["secret"]
        data = [ac_account_email, ac_sci_name, ac_amount, ac_currency, secret, ac_order_id]

        ac_sign = sha256(":".join(data).encode()).hexdigest()

        params = {
            "ac_account_email": ac_account_email,
            "ac_sci_name": ac_sci_name,
            "ac_amount": ac_amount,
            "ac_currency": ac_currency,
            "ac_order_id": ac_order_id,
            "ac_sign": ac_sign,
            "ac_comments": ac_comments,
        }
        url = "https://account.volet.com/sci/"
        return url, params

    def get_topup(self, tid: str) -> dict:
        t = self.api.check_by_id(tid)
        return t["status"] == "COMPLETED" and {
            "pmid": t["id"],
            "from_acc": t["walletSrcId"],
            "oid": t["orderId"],
            "amount": int(t["amount"] * 100),
            "ts": t["updatedTime"],
        }

    async def wait_for_code(self, uid: int, topic: str, hg: tuple[MessageHandler, int]) -> str:
        code = await self.ubot.wait_from(uid, topic, hg)
        return code and code[-6:]

    async def _login(self):
        ll = self.page.locator("input#j_username")
        await ll.fill(self.agent.auth["login"])
        await self.page.locator("input#j_password").fill(self.agent.auth["password"])
        await self.page.wait_for_timeout(300)
        await ll.click()
        await ll.press(key="ArrowLeft")
        await ll.blur()
        volet_bot_id, topic = 243630567, "otp_login"
        await self.page.locator("input#loginToAdvcashButton", has_text="log in").hover()
        hg = self.ubot.subscribe_for(volet_bot_id, topic)
        await self.page.locator("input#loginToAdvcashButton:not([disabled])", has_text="log in").click()
        await self.page.wait_for_url(self.pages.OTP_LOGIN)
        if not (code := await self.wait_for_code(volet_bot_id, topic, hg)):
            await self.ubot.receive("no login code", photo=await self.page.screenshot())
            raise NoCodeException(self.agent.user_id)
        await self.page.locator("input#otpId").fill(code)
        await self.page.click("input#checkOtpButton")
        await self.page.wait_for_url(self.pages.SEND, wait_until="domcontentloaded")
        # save state
        # noinspection PyTypeChecker
        self.agent.state = await self.page.context.storage_state()
        await self.agent.save()

    async def send(self, t: Transfer) -> tuple[str, bytes] | float:
        dest, cur = t.order.cred.detail, t.order.cred.pmcur.cur.ticker
        amount = round(t.order.amount * 10**-t.order.cred.pmcur.cur.scale, t.order.cred.pmcur.cur.scale)
        self.last_active = now()
        curs_map = {"RUB": "Ruble"}
        await self.go(self.pages.SEND, False)
        await self.page.click("[class=combobox-account]")
        await self.page.click(f'[class=rf-ulst-itm] b:has-text("{curs_map[cur]}")')
        await self.page.wait_for_selector(f"#srcCurrency:has-text('{cur}')")
        await self.page.fill("#srcAmount", str(amount))
        dw = self.page.locator("#destWalletId")
        await dw.fill(dest)
        await dw.blur()
        await self.page.wait_for_selector(f"#destCurrency:has-text('{cur}')")
        volet_bot_id, topic = 243630567, "otp_send"
        hg = self.ubot.subscribe_for(volet_bot_id, topic)
        await self.page.locator("form#mainForm input[type=submit]", has_text="continue").click()
        # todo: check success confirming
        if otp := self.agent.auth.get("otp"):
            totp = TOTP(otp)
            code = totp.now()
        elif self.agent.user.username.session:
            if not (code := await self.wait_for_code(volet_bot_id, topic, hg)):
                if 1:  # todo: Is mail_confirm required?
                    if _mcr := await self.gmail.volet_confirm(amount, t.updated_at):
                        ...
                        # todo: click Continue
                    if not (code := await self.wait_for_code(volet_bot_id, topic, hg)):
                        code = await self.wait_for_code(volet_bot_id, topic, hg)
            if not code:
                await self.receive("no send trans code", photo=await self.page.screenshot())
                raise NoCodeException(self.agent.user_id)
        else:
            raise OtpNotSetException(self.agent.user_id)
        await self.page.fill("#securityValue", code)
        await self.page.locator("input[type=submit]", has_text="confirm").click()
        await self.page.wait_for_url(self.pages.SEND)
        tid = await self.page.text_content("ul.p-confirmation-info dl.success>dd")
        await self.page.get_by_role("heading").click()
        slip = await self.page.screenshot(clip={"x": 440, "y": 205, "width": 440, "height": 415})
        await self.receive(f"{amount} to {dest} sent", photo=slip)
        return tid, slip

    async def go(self, url: Pages, commit: bool = True):
        try:
            await self.page.goto(url, wait_until="commit" if commit else "domcontentloaded")
            if len(await self.page.content()) < 1000:  # todo: fix captcha symptom
                await self.captcha_click()
        except Exception as e:
            await self.receive(repr(e), photo=await self.page.screenshot())
            raise e

    async def send_cap_help(self, xcap: Locator):
        if await xcap.count():
            bb = await xcap.bounding_box(timeout=2000)
            byts = await self.page.screenshot(clip=bb)
            await self.receive("put x, y", photo=byts)
            txt = await self.ubot.wait_from(self.uid, "xy", timeout=59)  # todo: fix
            for xy in txt.split(";"):
                px, py = xy
                x, y = bb["x"] + bb["width"] * int(px) / 100, bb["y"] + bb["height"] * int(py) / 100
                await xcap.click(position=Position(x=x, y=y))
            await self.page.wait_for_timeout(1100)
            await self.send_cap_help(xcap)
            # if await (nxt := self.page.locator('button', has_text="Next")).count():
            #     await nxt.click()

    async def captcha_click(self):
        captcha_url = self.page.url
        cbx = self.page.frame_locator("#main-iframe").frame_locator("iframe").first.locator("div#checkbox")
        await cbx.wait_for(state="visible"), await self.page.wait_for_timeout(500)
        await cbx.click(delay=94)
        xcap = self.page.frame_locator("#main-iframe").frame_locator("iframe").last.locator("div.challenge-view")
        if await xcap.count():
            await self.send_cap_help(xcap)
        try:
            await self.page.wait_for_url(lambda url: url != captcha_url, wait_until="commit")
        except TimeoutError:  # if page no changed -> captcha is undone
            await self.page.screenshot()
            raise CaptchaException(self.page.url)

    async def wait_for_payments(self, interval: int = 29):
        while (await User[self.agent.user_id]).status >= UserStatus.ACTIVE:
            await self.page.reload()
            await self.page.wait_for_timeout(interval * 1000)

    async def upd_balances(self, cur: Cur = None):
        """
        :return: dict {"account number": amount, ...}
        """
        res = self.api.get_balances()
        creds = [
            (
                (
                    await Cred.update_or_create(
                        {"detail": k},
                        pmcur=(await PmCur.get_or_create(pm__norm="volet", cur=await Cur.get(ticker=t)))[0],
                        person_id=self.agent.user.person_id,
                    )
                )[0],
                a,
            )
            for k, (t, a) in res.items()
            if not cur or cur.ticker == t
        ]
        [await Fiat.update_or_create({"amount": amount}, cred=cred) for cred, amount in creds]


async def _test():
    from x_model import init_db
    from xync_client.loader import TORM

    _ = await init_db(TORM, True)
    logging.basicConfig(level=logging.INFO)
    abot = Bot(PAY_TOKEN)
    playwright: Playwright = await async_playwright().start()

    try:
        o = await models.Order.create(ad_id=7, exid=1, amount=900, cred_id=522, taker_id=419)
        await o.fetch_related("cred__pmcur__cur", "ad")
        pma = await models.PmAgent.get(
            active=True,
            auth__isnull=False,
            pm_id=o.cred.pmcur.pmex_exid,
            user__person__actors=o.ad.maker_id,
            user__status=UserStatus.ACTIVE,
        ).prefetch_related("pm", "user__gmail", "user__username__session")
        t = models.Transfer(amount=9, created_at=now(), order=o)
        pcl: Client = pma.client(abot)
        pcl = await pcl.start(playwright, True, True)
        await pcl.send(t)
        await pcl.wait_for_payments()
    except TimeoutError as te:
        await pcl.receive(repr(te), photo=await pcl.page.screenshot())
        raise te
    finally:
        await pcl.stop()


if __name__ == "__main__":
    run(_test())
