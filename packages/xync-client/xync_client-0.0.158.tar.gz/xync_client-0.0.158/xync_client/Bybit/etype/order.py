from enum import IntEnum
from typing import Literal, ClassVar

from pydantic import BaseModel

from xync_client.Abc.xtype import RemapBase
from xync_client.Bybit.etype.cred import CredEpyd, PaymentTerm as CredPaymentTerm, PaymentConfigVo


class Topic(IntEnum):
    OTC_USER_CHAT_MSG = 1
    OTC_ORDER_STATUS_V2 = 2
    OTC_ORDER_STATUS = 3
    SELLER_CANCEL_CHANGE = 4


class Status(IntEnum):
    ws_new = 1
    # chain = 5  # waiting for chain (only web3)
    created = 10  # waiting for buyer to pay
    paid = 20  # waiting for seller to release
    appealed_by_seller = 30  # appealing
    # appealed_by_buyer = 30  # the same appealing
    canceled = 40  # order cancelled
    completed = 50  # order finished
    # a = 60  # paying (only when paying online)
    # a = 70  # pay fail (only when paying online)
    # a = 80  # exception cancelled (the coin convert to other coin only hotswap)
    # a = 90  # waiting for buyer to select tokenId
    appeal_disputed = 100  # objectioning
    appeal_dispute_disputed = 110  # waiting for the user to raise an objection


class TakeAdReq(BaseModel):
    ad_id: int | str
    amount: float
    is_sell: bool
    pm_id: int
    coin_id: int
    cur_id: int
    quantity: float | None = None
    price: float | None = None


class OrderRequest(BaseModel):
    class Side(IntEnum):
        BUY = 0
        SALE = 1

    itemId: str
    tokenId: str
    currencyId: str
    side: Literal["0", "1"]  # 0 покупка, # 1 продажа
    curPrice: str
    quantity: str
    amount: str
    flag: Literal["amount", "quantity"]
    version: str = "1.0"
    securityRiskToken: str = ""
    isFromAi: bool = False


class OrderSellRequest(OrderRequest):
    paymentId: str
    paymentType: str


class PreOrderResp(BaseModel):
    id: str  # bigint
    price: str  # float .cur.scale
    lastQuantity: str  # float .coin.scale
    curPrice: str  # hex 32
    lastPrice: str  # float .cur.scale # future
    isOnline: bool
    lastLogoutTime: str  # timestamp(0)+0
    payments: list[str]  # list[int]
    status: Literal[10, 15, 20]
    paymentTerms: list  # empty
    paymentPeriod: Literal[15, 30, 60]
    totalAmount: str  # float .cur.scale
    minAmount: str  # float .cur.scale
    maxAmount: str  # float .cur.scale
    minQuantity: str  # float .coin.scale
    maxQuantity: str  # float .coin.scale
    itemPriceAvailableTime: str  # timestamp(0)+0
    itemPriceValidTime: Literal["45000"]
    itemType: Literal["ORIGIN"]
    shareItem: bool  # False


class OrderResp(BaseModel):
    orderId: str
    isNeedConfirm: bool
    confirmId: str = ""
    success: bool
    securityRiskToken: str = ""
    riskTokenType: Literal["challenge", ""] = ""
    riskVersion: Literal["1", "2", ""] = ""
    needSecurityRisk: bool
    isBulkOrder: bool
    confirmed: str = None
    delayTime: str


class CancelOrderReq(BaseModel):
    orderId: str
    cancelCode: Literal["cancelReason_transferFailed"] = "cancelReason_transferFailed"
    cancelRemark: str = ""
    voucherPictures: str = ""


class JudgeInfo(BaseModel):
    autoJudgeUnlockTime: str
    dissentResult: str
    preDissent: str
    postDissent: str


class Extension(BaseModel):
    isDelayWithdraw: bool
    delayTime: str
    startTime: str


class AppraiseInfo(BaseModel):
    anonymous: str
    appraiseContent: str
    appraiseId: str
    appraiseType: str
    modifyFlag: str
    updateDate: str


class PaymentTerm(CredPaymentTerm):
    paymentConfigVo: PaymentConfigVo
    ruPaymentPrompt: bool


class _BaseOrder(RemapBase):
    _remap: ClassVar[dict[str, dict]] = {"status": {}}

    id: int
    userId: int
    createDate: int
    side: Literal[0, 1]  # int: 0 покупка, 1 продажа (именно для меня - апи агента, и пох мейкер я или тейкер)
    status: Literal[*[s.value for s in Status]]


class _BaseChange(_BaseOrder):
    makerUserId: int
    appealedTimes: int
    totalAppealedTimes: int


class OrderItem(_BaseOrder):
    tokenId: str
    orderType: Literal[
        "ORIGIN", "SMALL_COIN", "WEB3"
    ]  # str: ORIGIN: normal p2p order, SMALL_COIN: HotSwap p2p order, WEB3: web3 p2p order
    amount: str
    currencyId: str
    price: str
    notifyTokenQuantity: str
    notifyTokenId: str
    fee: str
    targetNickName: str
    targetUserId: str  # не я
    selfUnreadMsgCount: str
    transferLastSeconds: str
    appealLastSeconds: str
    sellerRealName: str
    buyerRealName: str
    judgeInfo: JudgeInfo
    unreadMsgCount: str
    extension: Extension
    bulkOrderFlag: bool


class OrderFull(OrderItem):
    itemId: int
    makerUserId: str
    targetAccountId: str
    targetFirstName: str
    targetSecondName: str
    targetUserAuthStatus: int
    targetConnectInformation: str
    payerRealName: str
    tokenName: str
    quantity: str
    payCode: str
    paymentType: int
    transferDate: str
    paymentTermList: list[CredEpyd]
    remark: str
    recentOrderNum: int
    recentExecuteRate: int
    appealContent: str
    appealType: int
    appealNickName: str
    canAppeal: str
    totalAppealTimes: str
    paymentTermResult: CredEpyd
    confirmedPayTerm: CredEpyd
    appealedTimes: str
    orderFinishMinute: int
    makerFee: str
    takerFee: str
    showContact: bool
    contactInfo: list[str]
    tokenBalance: str
    fiatBalance: str
    updateDate: str
    judgeType: str
    canReport: bool
    canReportDisagree: bool
    canReportType: list[str]
    canReportDisagreeType: list[str]
    appraiseStatus: str
    appraiseInfo: AppraiseInfo
    canReportDisagreeTypes: list[str]
    canReportTypes: list[str]
    middleToken: str
    beforePrice: str
    beforeQuantity: str
    beforeToken: str
    alternative: str
    appealUserId: str
    cancelResponsible: str
    chainType: str
    chainAddress: str
    tradeHashCode: str
    estimatedGasFee: str
    gasFeeTokenId: str
    tradingFeeTokenId: str
    onChainInfo: str
    transactionId: str
    displayRefund: str
    chainWithdrawLastSeconds: str
    chainTransferLastSeconds: str
    orderSource: str
    cancelReason: str
    sellerCancelExamineRemainTime: str
    needSellerExamineCancel: bool
    couponCurrencyAmount: str
    totalCurrencyAmount: str
    usedCoupon: bool  # bool: 1: used, 2: no used
    couponTokenId: str
    couponQuantity: str
    completedOrderAppealCount: int
    totalCompletedOrderAppealCount: int
    realOrderStatus: int
    appealVersion: int
    helpType: str
    appealFlowStatus: str
    appealSubStatus: str
    targetUserType: str
    targetUserDisplays: list[str]
    appealProcessChangeFlag: bool
    appealNegotiationNode: int


class Message(BaseModel):
    id: str
    accountId: str
    message: str
    msgType: Literal[
        0, 1, 2, 5, 6, 7, 8
    ]  # int: 0: system message, 1: text (user), 2: image (user), 5: text (admin), 6: image (admin), 7: pdf (user), 8: video (user)
    msgCode: int
    createDate: str
    isRead: Literal[0, 1]  # int: 1: read, 0: unread
    contentType: Literal["str", "pic", "pdf", "video"]
    roleType: str
    userId: str
    orderId: str
    msgUuid: str
    nickName: str
    read: Literal[0, 1]
    fileName: str
    onlyForCustomer: int | None = None


class StatusChange(_BaseChange):
    appealVersion: int = None


class CountDown(_BaseChange):
    cancelType: Literal["ACTIVE", "TIMEOUT", ""]


class _BaseMsg(BaseModel):
    userId: int
    orderId: int
    message: str = None
    msgUuid: str
    msgUuId: str
    createDate: str
    contentType: str
    roleType: Literal["user", "sys", "alarm", "customer_support"]


class Receive(_BaseMsg):
    id: int
    msgCode: int
    onlyForCustomer: int | None = None


class Read(_BaseMsg):
    readAmount: int
    read: Literal["101", "110", "11", "111"]
    orderStatus: Status


class SellerCancelChange(BaseModel):
    userId: int
    makerUserId: int
    id: str
    createDate: int
