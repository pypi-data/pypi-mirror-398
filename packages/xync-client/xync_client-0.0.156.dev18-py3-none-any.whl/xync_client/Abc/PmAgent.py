from abc import abstractmethod, ABCMeta
from asyncio import get_running_loop
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from PGram import Bot
from playwright.async_api import Page, Browser
from pyro_client.client.file import FileClient
from pyro_client.client.user import UserClient
from tortoise.timezone import now

from xync_schema.enums import UserStatus
from xync_schema.models import PmAgent, User, Transfer

from xync_client.Abc.HasAbotUid import HasAbotUid


class LoginFailedException(Exception): ...


class PmAgentClient(HasAbotUid, metaclass=ABCMeta):
    class Pages(StrEnum):
        base = "https://host"
        LOGIN = base + "login"
        SEND = base + "send"
        OTP_LOGIN = base + "login/otp"

    browser: Browser
    norm: str
    agent: PmAgent
    ubot: FileClient | UserClient = None
    page: Page
    pages: type(StrEnum) = Pages
    last_active: datetime = now()
    with_userbot: bool = False
    _is_started: bool = False

    async def start(self) -> "PmAgentClient":
        if self.with_userbot:
            self.ubot = UserClient(self.uid)
            await self.ubot.start()
        # noinspection PyTypeChecker
        context = await self.browser.new_context(storage_state=self.agent.state)
        self.page = await context.new_page()
        await self.page.goto(self.pages.SEND, wait_until="commit")  # Оптимистично переходим сразу на страницу отправки
        if self.page.url.startswith(self.pages.LOGIN):  # Если перебросило на страницу логина
            await self._login()  # Логинимся
        if not self.page.url.startswith(self.pages.SEND):  # Если в итоге не удалось попасть на отправку
            await self.receive(self.norm + " not logged in!", photo=await self.page.screenshot())
            raise LoginFailedException(f"User {self.agent.user_id} has not logged in")
        loop = get_running_loop()
        self.last_active = now()
        loop.create_task(self._idle())  # Бесконечно пасёмся в фоне на странице отправки, что бы куки не протухли
        self._is_started = True
        return self

    def get_topup(self, tid: str) -> dict: ...

    async def _idle(self):  # todo: не мешать другим процессам, обновлять на другой вкладке?
        while (await User.get(username_id=self.uid)).status >= UserStatus.ACTIVE:
            await self.page.wait_for_timeout(30 * 1000)
            if self.last_active < now() - timedelta(minutes=1):
                await self.page.reload(wait_until="commit")
                self.last_active = now()
        await self.receive(self.norm + " stoped")
        await self.stop()

    async def stop(self):
        # save state
        # noinspection PyTypeChecker
        self.agent.state = await self.page.context.storage_state()
        await self.agent.save()
        # closing
        await self.abot.stop()
        if self.ubot:
            await self.ubot.stop()
        await self.page.context.close()
        await self.page.context.browser.close()
        self._is_started = False

    @abstractmethod
    async def _login(self): ...

    @abstractmethod
    async def send(self, t: Transfer) -> tuple[int, bytes] | float: ...

    @abstractmethod  # проверка поступления определенной суммы за последние пол часа (минимум), return точную сумму
    async def check_in(
        self, amount: int | Decimal | float, cur: str, dt: datetime, tid: str | int = None
    ) -> float | None: ...

    @abstractmethod  # видео входа в аккаунт, и переход в историю поступлений за последние сутки (минимум)
    async def proof(self) -> bytes: ...

    def __init__(self, agent: PmAgent, browser: Browser, abot: Bot):
        self.agent = agent
        self.browser = browser
        self.abot = abot
        self.uid = agent.user.username_id
        self.norm = agent.pm.norm
