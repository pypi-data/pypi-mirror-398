"""
MEXC P2P OpenAPI v1.2 Async Client
"""

import hmac
import hashlib
import json
import time
from typing import Optional, Literal, Callable
from decimal import Decimal
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel
from xync_schema import models
from xync_schema.enums import AgentStatus, UserStatus

from xync_client.Mexc.etype.order import (
    CreateUpdateAdRequest,
    CreateAdResponse,
    AdListResponse,
    MarketAdListResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    OrderListResponse,
    ConfirmPaidRequest,
    BaseResponse,
    ReleaseCoinRequest,
    OrderDetailResponse,
    ServiceSwitchRequest,
    ListenKeyResponse,
    ConversationResponse,
    ChatMessagesResponse,
    UploadFileResponse,
    ReceivedChatMessage,
    WSRequest,
    WSMethod,
    SendTextMessage,
    SendImageMessage,
    SendVideoMessage,
    SendFileMessage,
    ChatMessageType,
)


# ============ Client ============
class MEXCP2PApiClient:
    """Асинхронный клиент для MEXC P2P API v1.2"""

    BASE_URL = "https://api.mexc.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session: Optional[aiohttp.ClientSession] = aiohttp.ClientSession()

    def _generate_signature(self, query_string: str) -> str:
        """Генерация HMAC SHA256 подписи"""
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    async def _request(
        self, method: str, endpoint: str, params: Optional[dict] = None, data: Optional[BaseModel] = None
    ) -> dict:
        """Базовый метод для HTTP запросов"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        params = params or {}
        # Формирование query string для подписи
        params["recvWindow"] = 5000
        params["timestamp"] = int(time.time() * 1000)
        params = {k: v for k, v in sorted(params.items())}

        query_string = urlencode(params, doseq=True).replace("+", "%20")
        signature = self._generate_signature(query_string)

        params["signature"] = signature

        headers = {"X-MEXC-APIKEY": self.api_key}
        if method in ("POST", "PUT", "PATCH"):
            headers["Content-Type"] = "application/json"

        url = f"{self.BASE_URL}{endpoint}"

        json_data = data.model_dump(exclude_none=True) if data else None

        async with self.session.request(method, url, params=params, json=json_data, headers=headers) as response:
            return await response.json()

    # ============ Advertisement Methods ============

    async def create_or_update_ad(self, request: CreateUpdateAdRequest) -> CreateAdResponse:
        """Создание или обновление объявления"""
        result = await self._request("POST", "/api/v3/fiat/merchant/ads/save_or_update", data=request)
        return CreateAdResponse(**result)

    async def get_my_ads(
        self,
        coin_id: Optional[str] = None,
        adv_status: Optional[str] = None,
        merchant_id: Optional[str] = None,
        fiat_unit: Optional[str] = None,
        side: Optional[str] = None,
        kyc_level: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> AdListResponse:
        """Получение списка моих объявлений с пагинацией"""
        params = {"page": page, "limit": limit}

        if coin_id:
            params["coinId"] = coin_id
        if adv_status:
            params["advStatus"] = adv_status
        if merchant_id:
            params["merchantId"] = merchant_id
        if fiat_unit:
            params["fiatUnit"] = fiat_unit
        if side:
            params["side"] = side
        if kyc_level:
            params["kycLevel"] = kyc_level
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        result = await self._request("GET", "/api/v3/fiat/merchant/ads/pagination", params=params)
        return AdListResponse(**result)

    async def get_market_ads(
        self,
        fiat_unit: str,
        coin_id: str,
        country_code: Optional[str] = None,
        side: Optional[str] = None,
        amount: Optional[Decimal] = None,
        quantity: Optional[Decimal] = None,
        pay_method: Optional[str] = None,
        block_trade: Optional[bool] = None,
        allow_trade: Optional[bool] = None,
        have_trade: Optional[bool] = None,
        follow: Optional[bool] = None,
        page: int = 1,
    ) -> MarketAdListResponse:
        """Получение рыночных объявлений"""
        params = {"fiatUnit": fiat_unit, "coinId": coin_id, "page": page}

        if country_code:
            params["countryCode"] = country_code
        if side:
            params["side"] = side
        if amount:
            params["amount"] = str(amount)
        if quantity:
            params["quantity"] = str(quantity)
        if pay_method:
            params["payMethod"] = pay_method
        if block_trade is not None:
            params["blockTrade"] = block_trade
        if allow_trade is not None:
            params["allowTrade"] = allow_trade
        if have_trade is not None:
            params["haveTrade"] = have_trade
        if follow is not None:
            params["follow"] = follow

        result = await self._request("GET", "/api/v3/fiat/market/ads/pagination", params=params)
        return not result["code"] and MarketAdListResponse(**result)

    # ============ Order Methods ============
    async def create_order(self, request: CreateOrderRequest) -> CreateOrderResponse:
        """Создание ордера (захват объявления)"""
        result = await self._request("POST", "/api/v3/fiat/merchant/order/deal", data=request)
        return CreateOrderResponse(**result)

    async def get_my_orders(
        self,
        start_time: int,
        end_time: int,
        coin_id: Optional[str] = None,
        adv_order_no: Optional[str] = None,
        side: Optional[str] = None,
        order_deal_state: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> OrderListResponse:
        """Получение моих ордеров (только как maker)"""
        params = {"startTime": start_time, "endTime": end_time, "page": page, "limit": limit}

        if coin_id:
            params["coinId"] = coin_id
        if adv_order_no:
            params["advOrderNo"] = adv_order_no
        if side:
            params["side"] = side
        if order_deal_state:
            params["orderDealState"] = order_deal_state

        result = await self._request("GET", "/api/v3/fiat/merchant/order/pagination", params=params)
        return OrderListResponse(**result)

    async def get_market_orders(
        self,
        coin_id: Optional[str] = None,
        adv_order_no: Optional[str] = None,
        side: Optional[str] = None,
        order_deal_state: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> OrderListResponse:
        """Получение всех ордеров (как maker и taker)"""
        params = {"page": page, "limit": limit}

        if coin_id:
            params["coinId"] = coin_id
        if adv_order_no:
            params["advOrderNo"] = adv_order_no
        if side:
            params["side"] = side
        if order_deal_state:
            params["orderDealState"] = order_deal_state
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        result = await self._request("GET", "/api/v3/fiat/market/order/pagination", params=params)
        return OrderListResponse(**result)

    async def confirm_paid(self, request: ConfirmPaidRequest) -> BaseResponse:
        """Подтверждение оплаты"""
        result = await self._request("POST", "/api/v3/fiat/confirm_paid", data=request)
        return BaseResponse(**result)

    async def release_coin(self, request: ReleaseCoinRequest) -> BaseResponse:
        """Релиз криптовалюты"""
        result = await self._request("POST", "/api/v3/fiat/release_coin", data=request)
        return BaseResponse(**result)

    async def get_order_detail(self, adv_order_no: str) -> OrderDetailResponse:
        """Получение деталей ордера"""
        params = {"advOrderNo": adv_order_no}

        result = await self._request("GET", "/api/v3/fiat/order/detail", params=params)
        return OrderDetailResponse(**result)

    # ============ Service Methods ============
    async def switch_service(self, request: ServiceSwitchRequest) -> BaseResponse:
        """Открытие/закрытие торговли"""
        result = await self._request("POST", "/api/v3/fiat/merchant/service/switch", data=request)
        return BaseResponse(**result)

    # ============ WebSocket Methods ============
    async def generate_listen_key(self) -> ListenKeyResponse:
        """Генерация listenKey для WebSocket"""
        result = await self._request("POST", "/api/v3/userDataStream")
        return ListenKeyResponse(**result)

    async def get_listen_key(self) -> ListenKeyResponse:
        """Получение существующего listenKey"""
        result = await self._request("GET", "/api/v3/userDataStream")
        return ListenKeyResponse(**result)

    # ============ Chat Methods ============
    async def get_chat_conversation(self, order_no: str) -> ConversationResponse:
        """Получение ID чат-сессии для ордера"""
        params = {"orderNo": order_no}

        result = await self._request("GET", "/api/v3/fiat/retrieveChatConversation", params=params)
        return ConversationResponse(**result)

    async def get_chat_messages(
        self,
        conversation_id: int,
        page: int = 1,
        limit: int = 20,
        chat_message_type: Optional[str] = None,
        message_id: Optional[int] = None,
        sort: Literal["DESC", "ASC"] = "DESC",
    ) -> ChatMessagesResponse:
        """Получение истории чата с пагинацией"""
        params = {"conversationId": conversation_id, "page": page, "limit": limit, "sort": sort}

        if chat_message_type:
            params["chatMessageType"] = chat_message_type
        if message_id:
            params["id"] = message_id

        result = await self._request("GET", "/api/v3/fiat/retrieveChatMessageWithPagination", params=params)
        return ChatMessagesResponse(**result)

    async def upload_file(self, file_data: bytes, filename: str) -> UploadFileResponse:
        """Загрузка файла"""
        if not self.session:
            raise RuntimeError("Client not initialized.")

        timestamp = self._get_timestamp()
        query_string = f"timestamp={timestamp}"
        signature = self._generate_signature(query_string)

        url = f"{self.BASE_URL}/api/v3/fiat/uploadFile"
        params = {"timestamp": timestamp, "signature": signature}

        headers = {"X-MEXC-APIKEY": self.api_key}

        form = aiohttp.FormData()
        form.add_field("file", file_data, filename=filename)

        async with self.session.post(url, params=params, data=form, headers=headers) as response:
            result = await response.json()

        return UploadFileResponse(**result)

    async def download_file(self, file_id: str) -> dict:
        """Скачивание файла"""
        params = {"fileId": file_id}

        result = await self._request("GET", "/api/v3/fiat/downloadFile", params=params)
        return result


"""
MEXC P2P WebSocket Client для чата
"""


class MEXCWebSocketClient:
    """
    Асинхронный WebSocket клиент для MEXC P2P
    Поддерживает:
    - Автоматический heartbeat (PING/PONG)
    - Переподключение при разрыве соединения
    """

    WS_URL = "wss://wbs.mexc.com/ws"
    PING_INTERVAL = 5  # секунды
    PING_TIMEOUT = 60  # если нет PONG 60 сек - разрыв

    def __init__(
        self,
        ws_token: str,
        on_message: Optional[Callable[[ReceivedChatMessage], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        auto_reconnect: bool = True,
    ):
        """
        Args:
            ws_token: Ключ авторизации
            on_message: Callback для входящих сообщений
            on_error: Callback для ошибок
            on_close: Callback при закрытии соединения
            auto_reconnect: Автоматическое переподключение
        """
        self.wsToken = ws_token
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.auto_reconnect = auto_reconnect

        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._last_pong_time = 0

    @property
    def is_connected(self) -> bool:
        """Проверка активного соединения"""
        return self._ws is not None and not self._ws.closed

    async def connect(self):
        """Установка WebSocket соединения"""
        if self.is_connected:
            return

        url = f"{self.WS_URL}?wsToken={self.wsToken}&platform=web"

        self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(url)
            self._running = True
            self._last_pong_time = asyncio.get_event_loop().time()

            # Запуск фоновых задач
            self._ping_task = asyncio.create_task(self._heartbeat_loop())
            self._receive_task = asyncio.create_task(self._receive_loop())

            print("✓ WebSocket connected")

        except Exception as e:
            await self._cleanup()
            raise Exception(f"Failed to connect WebSocket: {e}")

    async def disconnect(self):
        """Закрытие WebSocket соединения"""
        self._running = False

        if self._ping_task:
            self._ping_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()

        await self._cleanup()

        if self.on_close:
            self.on_close()

        print("✓ WebSocket disconnected")

    async def _cleanup(self):
        """Очистка ресурсов"""
        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

        self._ws = None
        self._session = None

    async def _send_raw(self, request: WSRequest):
        """Отправка сырого WebSocket сообщения"""
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")

        message = request.model_dump_json()
        await self._ws.send_str(message)

    async def _heartbeat_loop(self):
        """Фоновая задача для PING/PONG"""
        try:
            while self._running and self.is_connected:
                await asyncio.sleep(self.PING_INTERVAL)

                # Проверка таймаута PONG
                current_time = asyncio.get_event_loop().time()
                if current_time - self._last_pong_time > self.PING_TIMEOUT:
                    print("⚠ PING timeout, reconnecting...")
                    if self.auto_reconnect:
                        await self._reconnect()
                    else:
                        await self.disconnect()
                    break

                # Отправка PING
                await self._send_ping()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
            if self.on_error:
                self.on_error(e)

    async def _receive_loop(self):
        """Фоновая задача для получения сообщений"""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"❌ WebSocket error: {self._ws.exception()}")
                    break

                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                    print("⚠ WebSocket closed by server")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Receive loop error: {e}")
            if self.on_error:
                self.on_error(e)

        finally:
            # Переподключение при разрыве
            if self._running and self.auto_reconnect:
                print("⚠ Connection lost, reconnecting...")
                await self._reconnect()
            else:
                await self.disconnect()

    async def _handle_message(self, data: str):
        """Обработка входящего сообщения"""
        try:
            response = json.loads(data)

            method = response.get("method")

            # PONG ответ
            if method == "PING":
                self._last_pong_time = asyncio.get_event_loop().time()
                if response.get("data") == "PONG":
                    print("♥ PONG received")
                    pass

            # Входящее сообщение
            elif method == "RECEIVE_MESSAGE":
                if response.get("success") and self.on_message:
                    message_data = json.loads(response.get("data", "{}"))
                    message = ReceivedChatMessage(**message_data)
                    self.on_message(message)

            # Ответ на отправку
            elif method == "SEND_MESSAGE":
                if not response.get("success"):
                    print(f"⚠ Send failed: {response.get('msg')}")

        except Exception as e:
            print(f"❌ Error handling message: {e}")
            if self.on_error:
                self.on_error(e)

    async def _reconnect(self):
        """Переподключение WebSocket"""
        print("🔄 Reconnecting...")
        await self._cleanup()

        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(retry_delay * (attempt + 1))
                await self.connect()
                print("✓ Reconnected successfully")
                return

            except Exception as e:
                print(f"❌ Reconnect attempt {attempt + 1} failed: {e}")

        print("❌ Failed to reconnect after max retries")
        await self.disconnect()

    async def _send_ping(self):
        """Отправка PING"""
        request = WSRequest(method=WSMethod.PING)
        await self._send_raw(request)
        print(end="p")


# ============ WebSocket Client ============
class MEXCP2PWebSocketClient:
    """
    Асинхронный WebSocket клиент для чата MEXC P2P

    Поддерживает:
    - Отправку/получение текстовых сообщений
    - Отправку/получение медиа (изображения, видео, файлы)
    - Автоматический heartbeat (PING/PONG)
    - Переподключение при разрыве соединения
    """

    WS_URL = "wss://fiat.mexc.com/ws"
    PING_INTERVAL = 5  # секунды
    PING_TIMEOUT = 60  # если нет PONG 60 сек - разрыв

    def __init__(
        self,
        listen_key: str,
        conversation_id: int = None,
        on_message: Optional[Callable[[ReceivedChatMessage], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        auto_reconnect: bool = True,
    ):
        """
        Args:
            listen_key: Ключ авторизации (из HTTP API)
            conversation_id: ID чат-сессии
            on_message: Callback для входящих сообщений
            on_error: Callback для ошибок
            on_close: Callback при закрытии соединения
            auto_reconnect: Автоматическое переподключение
        """
        self.listen_key = listen_key
        self.conversation_id = conversation_id
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.auto_reconnect = auto_reconnect

        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._ping_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._last_pong_time = 0

    @property
    def is_connected(self) -> bool:
        """Проверка активного соединения"""
        return self._ws is not None and not self._ws.closed

    async def connect(self):
        """Установка WebSocket соединения"""
        if self.is_connected:
            return

        url = f"{self.WS_URL}?listenKey={self.listen_key}"
        if self.conversation_id:
            url += f"&conversationId={self.conversation_id}"

        self._session = aiohttp.ClientSession()

        try:
            self._ws = await self._session.ws_connect(url)
            self._running = True
            self._last_pong_time = asyncio.get_event_loop().time()

            # Запуск фоновых задач
            self._ping_task = asyncio.create_task(self._heartbeat_loop())
            self._receive_task = asyncio.create_task(self._receive_loop())

            print(f"✓ WebSocket connected to conversation {self.conversation_id}")

        except Exception as e:
            await self._cleanup()
            raise Exception(f"Failed to connect WebSocket: {e}")

    async def disconnect(self):
        """Закрытие WebSocket соединения"""
        self._running = False

        if self._ping_task:
            self._ping_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()

        await self._cleanup()

        if self.on_close:
            self.on_close()

        print("✓ WebSocket disconnected")

    async def _cleanup(self):
        """Очистка ресурсов"""
        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

        self._ws = None
        self._session = None

    async def _send_raw(self, request: WSRequest):
        """Отправка сырого WebSocket сообщения"""
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")

        message = request.model_dump_json()
        await self._ws.send_str(message)

    async def _heartbeat_loop(self):
        """Фоновая задача для PING/PONG"""
        try:
            while self._running and self.is_connected:
                await asyncio.sleep(self.PING_INTERVAL)

                # Проверка таймаута PONG
                current_time = asyncio.get_event_loop().time()
                if current_time - self._last_pong_time > self.PING_TIMEOUT:
                    print("⚠ PING timeout, reconnecting...")
                    if self.auto_reconnect:
                        await self._reconnect()
                    else:
                        await self.disconnect()
                    break

                # Отправка PING
                await self._send_ping()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Heartbeat error: {e}")
            if self.on_error:
                self.on_error(e)

    async def _receive_loop(self):
        """Фоновая задача для получения сообщений"""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"❌ WebSocket error: {self._ws.exception()}")
                    break

                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                    print("⚠ WebSocket closed by server")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Receive loop error: {e}")
            if self.on_error:
                self.on_error(e)

        finally:
            # Переподключение при разрыве
            if self._running and self.auto_reconnect:
                print("⚠ Connection lost, reconnecting...")
                await self._reconnect()
            else:
                await self.disconnect()

    async def _handle_message(self, data: str):
        """Обработка входящего сообщения"""
        try:
            response = json.loads(data)

            method = response.get("method")

            # PONG ответ
            if method == "PING":
                self._last_pong_time = asyncio.get_event_loop().time()
                if response.get("data") == "PONG":
                    print("♥ PONG received")
                    pass

            # Входящее сообщение
            elif method == "RECEIVE_MESSAGE":
                if response.get("success") and self.on_message:
                    message_data = json.loads(response.get("data", "{}"))
                    message = ReceivedChatMessage(**message_data)
                    self.on_message(message)

            # Ответ на отправку
            elif method == "SEND_MESSAGE":
                if not response.get("success"):
                    print(f"⚠ Send failed: {response.get('msg')}")

        except Exception as e:
            print(f"❌ Error handling message: {e}")
            if self.on_error:
                self.on_error(e)

    async def _reconnect(self):
        """Переподключение WebSocket"""
        print("🔄 Reconnecting...")
        await self._cleanup()

        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(retry_delay * (attempt + 1))
                await self.connect()
                print("✓ Reconnected successfully")
                return

            except Exception as e:
                print(f"❌ Reconnect attempt {attempt + 1} failed: {e}")

        print("❌ Failed to reconnect after max retries")
        await self.disconnect()

    async def _send_ping(self):
        """Отправка PING"""
        request = WSRequest(method=WSMethod.PING)
        await self._send_raw(request)
        print(end="p")

    # ============ Public Message Sending Methods ============

    async def send_text(self, content: str) -> bool:
        """
        Отправка текстового сообщения

        Args:
            content: Текст сообщения

        Returns:
            bool: Успешность отправки
        """
        message = SendTextMessage(content=content, conversationId=self.conversation_id)

        request = WSRequest(method=WSMethod.SEND_MESSAGE, params=message.model_dump())

        try:
            await self._send_raw(request)
            return True
        except Exception as e:
            print(f"❌ Failed to send text: {e}")
            return False

    async def send_image(self, image_url: str, thumb_url: str) -> bool:
        """
        Отправка изображения

        Args:
            image_url: URL полного изображения
            thumb_url: URL превью

        Returns:
            bool: Успешность отправки
        """
        message = SendImageMessage(imageUrl=image_url, imageThumbUrl=thumb_url, conversationId=self.conversation_id)

        request = WSRequest(method=WSMethod.SEND_MESSAGE, params=message.model_dump_json())

        try:
            await self._send_raw(request)
            return True
        except Exception as e:
            print(f"❌ Failed to send image: {e}")
            return False

    async def send_video(self, video_url: str, thumb_url: str) -> bool:
        """
        Отправка видео

        Args:
            video_url: URL видео
            thumb_url: URL превью

        Returns:
            bool: Успешность отправки
        """
        message = SendVideoMessage(videoUrl=video_url, imageThumbUrl=thumb_url, conversationId=self.conversation_id)

        request = WSRequest(method=WSMethod.SEND_MESSAGE, params=message.model_dump_json())

        try:
            await self._send_raw(request)
            return True
        except Exception as e:
            print(f"❌ Failed to send video: {e}")
            return False

    async def send_file(self, file_url: str) -> bool:
        """
        Отправка файла

        Args:
            file_url: URL файла

        Returns:
            bool: Успешность отправки
        """
        message = SendFileMessage(fileUrl=file_url, conversationId=self.conversation_id)

        request = WSRequest(method=WSMethod.SEND_MESSAGE, params=message.model_dump_json())

        try:
            await self._send_raw(request)
            return True
        except Exception as e:
            print(f"❌ Failed to send file: {e}")
            return False

    async def send_message(
        self,
        content: Optional[str] = None,
        image_url: Optional[str] = None,
        image_thumb_url: Optional[str] = None,
        video_url: Optional[str] = None,
        file_url: Optional[str] = None,
    ) -> bool:
        """
        Универсальная отправка сообщения (автоопределение типа)

        Args:
            content: Текст (для TEXT)
            image_url: URL изображения (для IMAGE)
            image_thumb_url: URL превью (для IMAGE/VIDEO)
            video_url: URL видео (для VIDEO)
            file_url: URL файла (для FILE)

        Returns:
            bool: Успешность отправки
        """
        if content:
            return await self.send_text(content)
        elif image_url and image_thumb_url:
            return await self.send_image(image_url, image_thumb_url)
        elif video_url and image_thumb_url:
            return await self.send_video(video_url, image_thumb_url)
        elif file_url:
            return await self.send_file(file_url)
        else:
            raise ValueError("No valid message content provided")


# ============ Context Manager для удобства ============
class MEXCP2PChatSession:
    """
    Высокоуровневая обертка для чат-сессии
    Автоматически управляет HTTP и WebSocket клиентами
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        order_no: str,
        on_message: Optional[Callable[[ReceivedChatMessage], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        auto_reconnect: bool = True,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.order_no = order_no
        self.on_message = on_message
        self.on_error = on_error
        self.auto_reconnect = auto_reconnect

        self.http_client: Optional[MEXCP2PApiClient] = None
        self.ws_client: Optional[MEXCP2PWebSocketClient] = None
        self.conversation_id: Optional[int] = None

    async def __aenter__(self):
        # Инициализация HTTP клиента
        self.http_client = MEXCP2PApiClient(self.api_key, self.api_secret)
        await self.http_client.__aenter__()

        # Получение conversation ID
        conv_response = await self.http_client.get_chat_conversation(self.order_no)
        self.conversation_id = conv_response.data.get("conversationId")

        if not self.conversation_id:
            raise ValueError("Failed to get conversation ID")

        # Генерация listenKey
        listen_key_response = await self.http_client.generate_listen_key()
        listen_key = listen_key_response.listenKey

        # Подключение WebSocket
        self.ws_client = MEXCP2PWebSocketClient(
            listen_key=listen_key,
            conversation_id=self.conversation_id,
            on_message=self.on_message,
            on_error=self.on_error,
            auto_reconnect=self.auto_reconnect,
        )

        await self.ws_client.connect()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws_client:
            await self.ws_client.disconnect()

        if self.http_client:
            await self.http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def send_text(self, text: str) -> bool:
        """Отправка текста"""
        return await self.ws_client.send_text(text)

    async def send_image(self, image_url: str, thumb_url: str) -> bool:
        """Отправка изображения"""
        return await self.ws_client.send_image(image_url, thumb_url)

    async def send_video(self, video_url: str, thumb_url: str) -> bool:
        """Отправка видео"""
        return await self.ws_client.send_video(video_url, thumb_url)

    async def send_file(self, file_url: str) -> bool:
        """Отправка файла"""
        return await self.ws_client.send_file(file_url)

    async def upload_and_send_file(self, file_data: bytes, filename: str) -> bool:
        """
        Загрузка файла через HTTP API и отправка в чат

        Args:
            file_data: Бинарные данные файла
            filename: Имя файла

        Returns:
            bool: Успешность операции
        """
        # Загрузка файла
        upload_response = await self.http_client.upload_file(file_data, filename)

        if upload_response.code != 0:
            print(f"❌ File upload failed: {upload_response.msg}")
            return False

        file_id = upload_response.data.get("fileId")

        # Получение URL файла
        download_response = await self.http_client.download_file(file_id)

        if download_response.get("code") != 0:
            print("❌ File URL retrieval failed")
            return False

        file_url = download_response["data"]["fileUrl"]

        # Отправка в чат
        return await self.send_file(file_url)

    async def get_message_history(self, limit: int = 20, page: int = 1) -> list[ReceivedChatMessage]:
        """
        Получение истории сообщений

        Args:
            limit: Количество сообщений
            page: Номер страницы

        Returns:
            List[ReceivedChatMessage]: Список сообщений
        """
        response = await self.http_client.get_chat_messages(
            conversation_id=self.conversation_id, page=page, limit=limit
        )

        messages_data = response.data.get("messages", [])
        return [ReceivedChatMessage(**msg) for msg in messages_data]


# ============ Usage Examples ============
async def example_simple_chat():
    """Простой пример чата"""

    def on_message(msg: ReceivedChatMessage):
        if msg.type == ChatMessageType.TEXT:
            print(f"📩 [{msg.fromNickName}]: {msg.content}")
        elif msg.type == ChatMessageType.IMAGE:
            print(f"📷 [{msg.fromNickName}] sent image: {msg.imageUrl}")
        elif msg.type == ChatMessageType.VIDEO:
            print(f"🎥 [{msg.fromNickName}] sent video: {msg.videoUrl}")
        elif msg.type == ChatMessageType.FILE:
            print(f"📎 [{msg.fromNickName}] sent file: {msg.fileUrl}")

    def on_error(error: Exception):
        print(f"❌ Error: {error}")

    api_key = "your_api_key"
    api_secret = "your_api_secret"
    order_no = "your_order_no"

    async with MEXCP2PChatSession(
        api_key=api_key,
        api_secret=api_secret,
        order_no=order_no,
        on_message=on_message,
        on_error=on_error,
        auto_reconnect=True,
    ) as chat:
        # Отправка текста
        await chat.send_text("Hello! How are you?")

        # Получение истории
        history = await chat.get_message_history(limit=10)
        print(f"📜 Loaded {len(history)} messages from history")

        # Держим соединение открытым
        await asyncio.sleep(60)


async def example_manual_websocket():
    """Пример ручного управления WebSocket"""

    api_key = "your_api_key"
    api_secret = "your_api_secret"

    # Получаем listenKey и conversation_id через HTTP API
    async with MEXCP2PApiClient(api_key, api_secret) as http_client:
        # Получение conversation ID
        conv = await http_client.get_chat_conversation("order_123")
        conversation_id = conv.data["conversationId"]

        # Получение listenKey
        key_response = await http_client.generate_listen_key()
        listen_key = key_response.listenKey

        # Создание WebSocket клиента
        def on_message(msg: ReceivedChatMessage):
            print(f"Received: {msg.content}")

        ws_client = MEXCP2PWebSocketClient(
            listen_key=listen_key, conversation_id=conversation_id, on_message=on_message, auto_reconnect=True
        )

        await ws_client.connect()

        try:
            # Отправка сообщений
            await ws_client.send_text("Test message 1")
            await asyncio.sleep(1)
            await ws_client.send_text("Test message 2")

            # Ожидание входящих сообщений
            await asyncio.sleep(30)

        finally:
            await ws_client.disconnect()


async def example_file_sending():
    """Пример отправки файла"""

    api_key = "your_api_key"
    api_secret = "your_api_secret"
    order_no = "your_order_no"

    async with MEXCP2PChatSession(api_key=api_key, api_secret=api_secret, order_no=order_no) as chat:
        # Загрузка и отправка файла
        with open("document.pdf", "rb") as f:
            file_data = f.read()

        success = await chat.upload_and_send_file(file_data=file_data, filename="document.pdf")

        if success:
            print("✓ File sent successfully")
        else:
            print("❌ Failed to send file")


async def example_bot():
    """Пример простого бота для автоответов"""

    async def handle_message(msg: ReceivedChatMessage):
        # Игнорируем свои сообщения
        if msg.self_:
            return

        # Автоответ на текст
        if msg.type == ChatMessageType.TEXT:
            if "price" in msg.content.lower():
                await chat.send_text("Our current price is 70,000 USD")
            elif "hello" in msg.content.lower():
                await chat.send_text("Hello! How can I help you?")

    api_key = "your_api_key"
    api_secret = "your_api_secret"
    order_no = "your_order_no"

    async with MEXCP2PChatSession(
        api_key=api_key, api_secret=api_secret, order_no=order_no, on_message=handle_message, auto_reconnect=True
    ) as chat:
        # Бот работает бесконечно
        while True:
            await asyncio.sleep(1)


# ============ Usage Example ============
async def main():
    # Выбери пример для запуска:

    # asyncio.run(example_simple_chat())
    # asyncio.run(example_manual_websocket())
    # asyncio.run(example_file_sending())
    # asyncio.run(example_bot())

    """Пример использования клиента"""
    from x_model import init_db
    from xync_client.loader import TORM

    await init_db(TORM, True)

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

    async with MEXCP2PApiClient(agent.auth["key"], agent.auth["sec"]) as client:
        # Генерация listenKey для WebSocket
        listen_key = await client.generate_listen_key()
        print(f"ListenKey: {listen_key.listenKey}")

        # await ws_prv(listen_key.listenKey)
        # Получение рыночных объявлений
        # market_ads = await client.get_market_ads(
        #     fiat_unit="RUB", coin_id="128f589271cb4951b03e71e6323eb7be", side=Side.SELL.name, page=1
        # )

        # print(f"Found {len(market_ads.data)} ads")

        # Создание ордера
        # if market_ads.data:
        #     first_ad = market_ads.data[0]
        #     order_request = CreateOrderRequest(advNo=first_ad.advNo, amount=Decimal("100"), userConfirmPaymentId=123)
        #
        #     order_response = await client.create_order(order_request)
        #     print(f"Created order: {order_response.data}")
        #
        # # Получение деталей ордера
        # order_detail = await client.get_order_detail("order_id_here")
        # print(f"Order state: {order_detail.data.state}")

        # Создание WebSocket клиента
        def on_message(msg: ReceivedChatMessage):
            print(f"Received: {msg.content}")

        ws_client = MEXCWebSocketClient(
            ws_token="d9381d8193ad0859f1ea240041bd7004493d2030a4b4a2c861e4fd9c1b08fdcc",
            on_message=on_message,
            auto_reconnect=True,
        )

        await ws_client.connect()

        try:
            # Отправка сообщений
            wsr = WSRequest(method="SUBSCRIPTION", params=["otc@private.p2p.orders.pb"], id=12)

            await ws_client._send_raw(wsr)

            # Ожидание входящих сообщений
            await asyncio.sleep(12)

        finally:
            await ws_client.disconnect()

        # # Создание объявления
        # ad_request = CreateUpdateAdRequest(
        #     payTimeLimit=15,
        #     initQuantity=100,
        #     price=87,
        #     coinId="5989b56ba96a43599dbeeca5bb053f43",
        #     side=Side.BUY.name,
        #     fiatUnit="USD",
        #     payMethod="1",
        #     minSingleTransAmount=500,
        #     maxSingleTransAmount=150000,
        #     userAllTradeCountMin=0,
        #     userAllTradeCountMax=100,
        # )
        # ad_response = await client.create_or_update_ad(ad_request)
        # print(f"Created ad: {ad_response.data}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
