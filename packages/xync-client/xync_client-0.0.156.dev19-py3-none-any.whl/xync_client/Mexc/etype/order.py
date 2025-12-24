from enum import IntEnum
from typing import Optional, Literal

from pydantic import BaseModel, Field

# ============ Enums ============
Side = Literal["BUY", "SELL"]


class AdvStatus(IntEnum):
    CLOSE = 0
    OPEN = 1
    DELETE = 2
    LOW_STOCK = 3


class OrderDealState(IntEnum):
    NOT_PAID = 0
    PAID = 1
    WAIT_PROCESS = 2
    PROCESSING = 3
    DONE = 4
    CANCEL = 5
    INVALID = 6
    REFUSE = 7
    TIMEOUT = 8


class NotifyType(IntEnum):
    SMS = 0
    MAIL = 1
    GA = 2


# ============ Request Models ============
class CreateUpdateAdRequest(BaseModel):
    advNo: Optional[str] = None
    payTimeLimit: int
    initQuantity: float
    supplyQuantity: Optional[float] = None
    price: float
    coinId: str
    countryCode: Optional[str] = None
    side: str
    advStatus: Optional[str] = None
    allowSys: Optional[bool] = None
    fiatUnit: str
    payMethod: str
    autoReplyMsg: Optional[str] = None
    tradeTerms: Optional[str] = None
    minSingleTransAmount: float
    maxSingleTransAmount: float
    kycLevel: Optional[str] = None
    requireMobile: Optional[bool] = None
    userAllTradeCountMin: int
    userAllTradeCountMax: int
    exchangeCount: Optional[int] = None
    maxPayLimit: Optional[int] = None
    buyerRegDaysLimit: Optional[int] = None
    creditAmount: Optional[float] = None
    blockTrade: Optional[bool] = None
    deviceId: Optional[str] = None


class CreateOrderRequest(BaseModel):
    advNo: str
    amount: Optional[float] = None
    tradableQuantity: Optional[float] = None
    userConfirmPaymentId: int
    userConfirmPayMethodId: Optional[int] = None
    deviceId: Optional[str] = None


class ConfirmPaidRequest(BaseModel):
    advOrderNo: str
    payId: int


class ReleaseCoinRequest(BaseModel):
    advOrderNo: str
    notifyType: Optional[str] = None
    notifyCode: Optional[str] = None


class ServiceSwitchRequest(BaseModel):
    open: bool


# ============ Response Models ============
class BaseResponse(BaseModel):
    code: int
    msg: str


class PaymentInfo(BaseModel):
    id: int
    payMethod: int
    bankName: str = None
    account: str = None
    bankAddress: str = None
    payee: str = None
    extend: str = None


class MerchantInfo(BaseModel):
    nickName: str
    imId: str
    memberId: str
    registry: int
    vipLevel: int
    greenDiamond: bool
    emailAuthentication: bool
    smsAuthentication: bool
    identityVerification: bool
    lastOnlineTime: int
    badge: str
    merchantType: str


class MerchantStatistics(BaseModel):
    totalBuyCount: int
    totalSellCount: int
    doneLastMonthCount: int
    avgBuyHandleTime: float
    avgSellHandleTime: float
    lastMonthCompleteRate: str
    completeRate: str
    avgHandleTime: float


2


class Advertisement(BaseModel):
    advNo: str
    payTimeLimit: int
    quantity: int = None
    price: float
    initAmount: float = None
    frozenQuantity: float = None
    availableQuantity: float
    coinId: str = None
    coinName: str
    countryCode: str
    commissionRate: float = None
    advStatus: str = None
    side: str
    createTime: int = None
    updateTime: int
    fiatUnit: str
    feeType: int = None
    autoReplyMsg: str
    tradeTerms: str
    payMethod: str
    paymentInfo: list[PaymentInfo]
    minSingleTransAmount: float
    maxSingleTransAmount: float
    kycLevel: Literal["PRIMARY", "ADVANCED"]
    requireMobile: bool
    userAllTradeCountMax: int
    userAllTradeCountMin: int
    exchangeCount: int
    maxPayLimit: int
    buyerRegDaysLimit: int
    blockTrade: bool


class MarketAdvertisement(Advertisement):
    merchant: MerchantInfo
    merchantStatistics: MerchantStatistics
    orderPayCount: int
    tags: str


class PageInfo(BaseModel):
    total: int
    currPage: int
    pageSize: int
    totalPage: int


class UserInfo(BaseModel):
    nickName: str


class Order(BaseModel):
    advNo: str
    advOrderNo: str
    tradableQuantity: float
    price: float
    amount: float
    coinName: str
    state: Literal["DONE", "PAID", "NOT_PAID", "PROCESSING"]
    payTimeLimit: int
    side: Side
    fiatUnit: str
    createTime: int
    updateTime: int
    userInfo: UserInfo
    complained: bool
    blockUser: bool = None
    unreadCount: int
    complainId: Optional[str] = None


class OrderDetail(Order):
    paymentInfo: list[PaymentInfo]
    allowComplainTime: int = None
    confirmPaymentInfo: PaymentInfo
    userInfo: dict
    userFiatStatistics: dict = None
    spotCount: int = None


class CreateAdResponse(BaseResponse):
    data: str  # advNo


class AdListResponse(BaseResponse):
    data: list[Advertisement]
    page: PageInfo


class MarketAdListResponse(BaseResponse):
    data: list[MarketAdvertisement]
    page: PageInfo


class CreateOrderResponse(BaseResponse):
    data: str  # advOrderNo


class OrderListResponse(BaseResponse):
    data: list[Order]
    page: PageInfo


class OrderDetailResponse(BaseResponse):
    data: OrderDetail


class ListenKeyResponse(BaseModel):
    listenKey: str


class ConversationResponse(BaseResponse):
    data: dict


class ChatMessage(BaseModel):
    id: int
    content: Optional[str] = None
    createTime: str
    fromNickName: str
    fromUserId: str
    type: int
    imageUrl: Optional[str] = None
    imageThumbUrl: Optional[str] = None
    videoUrl: Optional[str] = None
    fileUrl: Optional[str] = None
    self_: bool = Field(alias="self")
    conversationId: int


class ChatMessagesResponse(BaseResponse):
    data: dict


class UploadFileResponse(BaseResponse):
    data: dict


# ============ WebSocket Message Models ============
class ChatMessageType(IntEnum):
    TEXT = 1
    IMAGE = 2
    VIDEO = 3
    FILE = 4


class WSMethod(str):
    SUBSCRIPTION = "SUBSCRIPTION"
    UNSUBSCRIPTION = "UNSUBSCRIPTION"
    SEND_MESSAGE = "SEND_MESSAGE"
    RECEIVE_MESSAGE = "RECEIVE_MESSAGE"
    PING = "PING"


class SendTextMessage(BaseModel):
    """Отправка текстового сообщения"""

    content: str
    conversationId: int
    type: int = ChatMessageType.TEXT


class SendImageMessage(BaseModel):
    """Отправка изображения"""

    imageUrl: str
    imageThumbUrl: str
    conversationId: int
    type: int = ChatMessageType.IMAGE


class SendVideoMessage(BaseModel):
    """Отправка видео"""

    videoUrl: str
    imageThumbUrl: str  # превью видео
    conversationId: int
    type: int = ChatMessageType.VIDEO


class SendFileMessage(BaseModel):
    """Отправка файла"""

    fileUrl: str
    conversationId: int
    type: int = ChatMessageType.FILE


class WSRequest(BaseModel):
    """Базовая структура WebSocket запроса"""

    method: str
    params: dict | list[str] | None = None
    id: int = None


class WSBaseResponse(BaseModel):
    """Базовый ответ WebSocket"""

    success: bool
    method: str
    msg: str
    data: Optional[str] = None


class ReceivedChatMessage(BaseModel):
    """Полученное сообщение из чата"""

    id: int
    content: Optional[str] = None
    conversationId: int
    type: int
    imageUrl: Optional[str] = None
    imageThumbUrl: Optional[str] = None
    videoUrl: Optional[str] = None
    fileUrl: Optional[str] = None
    createTime: str
    self_: bool = Field(alias="self")
    fromUserId: str
    fromNickName: str
