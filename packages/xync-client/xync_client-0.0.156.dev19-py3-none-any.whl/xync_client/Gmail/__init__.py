import logging
import pickle
import re
from base64 import urlsafe_b64decode
from datetime import datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from requests import get
from xync_schema.models import User, Gmail

from xync_client.Abc.HasAbotUid import HasAbotUid
from xync_client.loader import TORM

# Область доступа
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmClient(HasAbotUid):
    service: Resource

    def __init__(self, user: User):
        """Авторизация и создание сервиса Gmail API"""
        creds = None
        # Файл token.pickle хранит токены доступа пользователя
        if user.gmail.token:
            creds = pickle.loads(user.gmail.token)

        # Если нет валидных credentials, запрашиваем авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(user.gmail.auth, SCOPES)
                creds = flow.run_local_server(port=0)

            # Сохраняем credentials для следующего запуска
            user.gmail.token = pickle.dumps(creds)

        self.service = build("gmail", "v1", credentials=creds)
        self.uid = user.username_id

    def _get_last_email(self, sender_email, subject_keyword=None):
        """
        Получить последнее письмо от определенного отправителя

        Args:
            sender_email: email отправителя (например, 'example@gmail.com')
            subject_keyword: ключевое слово в теме (опционально)
        """

        def _get_email_body(payload):
            """Извлечь текст письма из payload"""
            if "body" in payload and "data" in payload["body"]:
                return urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
            return ""

        # Формируем поисковый запрос
        query = f"from:{sender_email}"
        if subject_keyword:
            query += f" subject:{subject_keyword}"

        # Ищем письма с этим запросом
        results = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=1,  # Только последнее письмо
            )
            .execute()
        )

        if not (messages := results.get("messages", [])):
            logging.warning("Письма не найдены")
            return None

        # Получаем полную информацию о письме
        message_id = messages[0]["id"]
        message = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()

        # Извлекаем заголовки
        headers = message["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "Нет темы")
        from_email = next((h["value"] for h in headers if h["name"] == "From"), "Неизвестно")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "Неизвестно")

        # Извлекаем текст письма
        body = _get_email_body(message["payload"])

        return {"id": message_id, "subject": subject, "from": from_email, "date": date, "body": body}

    async def volet_confirm(self, amount: float, dt: datetime):
        if email := self._get_last_email("noreply@volet.com", "Please Confirm Withdrawal"):  # "Volet.com"
            date = datetime.strptime(email["date"].split(",")[1].split(" +")[0], "%d %b %Y %H:%M:%S")
            if match := re.search(r"Amount: <b>([\d.]+) [A-Z]{3}</b>", email["body"]):
                amt = float(match.group(1))
            if match := re.search(r"https://account\.volet\.com/verify/([a-f0-9-]+)", email["body"]):
                token = match.group(1)

        if email and amount == amt and date > dt and token:
            get(f"https://account.volet.com/verify/{token}")
            return True

        await self.receive("А нет запросов от волета")
        return False

    async def bybit_code(self, dt: datetime) -> str | None:
        if email := self._get_last_email("Bybit", "[Bybit]Security Code for Your Bybit Account"):
            date = datetime.strptime(email["date"].split(",")[1].split(" +")[0], "%d %b %Y %H:%M:%S")
            if match := re.search(r'<span style="font-size:28pt;color:#ff9c2e">(\d{6})</span>', email["body"]):
                code = match.group(1)

        if email and date > dt and code:
            get(f"https://account.volet.com/verify/{code}")
            return code

        await self.receive("А нет запросов от волета")
        return None


async def _test():
    from x_model import init_db

    _ = await init_db(TORM)

    gm = await Gmail.get(id=1).prefetch_related("user__username")
    gmc = GmClient(gm)
    await gmc.volet_confirm(amount=90, dt=datetime.now())


if __name__ == "__main__":
    from asyncio import run

    run(_test())
