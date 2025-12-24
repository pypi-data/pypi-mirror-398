from typing import Literal

from pydantic import BaseModel, RootModel
from xync_schema.xtype import BaseAd

from xync_client.Abc.xtype import BaseAdUpdate


class TradeRule(BaseModel):
    title: str
    titleValue: str | None = None
    content: str
    inputType: int
    inputValue: str
    hint: str
    contentCode: Literal["PAY", "MERCHANT"]
    contentType: int | None = None
    sort: int


TradeRulesV2 = RootModel[list[TradeRule]]


class AdsUpd(BaseAdUpdate):
    tradeType: int
    coinId: int
    currency: int
    minTradeLimit: float
    maxTradeLimit: float
    tradeCount: float
    password: str = ""
    payTerm: int
    isFixed: Literal["off", "on"]
    premium: float
    isAutoReply: Literal["off", "on"]
    takerAcceptOrder: int
    isPayCode: Literal["off", "on"]
    verifyCapitalStatus: str = None  # todo: check if int
    receiveAccounts: str
    deviation: int
    isTakerLimit: Literal["off", "on"]
    takerRealLevel: Literal["off", "on"]
    takerIsPhoneBind: Literal["off", "on"]
    takerIsMerchant: Literal["off", "on"]
    takerIsPayment: Literal["off", "on"]
    blockType: int
    session: int
    chargeType: bool
    apiVersion: int
    channel: str
    tradeRulesV2: str  # TradeRulesV2
    securityToken: str | None = ""
    fixedPrice: float | None = None
    autoReplyContent: str | None = ""


class AdsReq(BaseModel):
    coinId: int
    currency: int
    tradeType: Literal["sell", "buy"]
    payMethod: str
    currPage: int = 1
    acceptOrder: int = 0
    blockType: Literal["general"] = "general"
    online: int = 1
    range: int = 0
    amount: str = ""  # float
    onlyTradable: str = "false"  # bool
    isFollowed: str = "false"  # bool


class PayMethod(BaseModel):
    payMethodId: int
    name: str
    color: str | None = None
    isRecommend: bool | None = None


class PayName(BaseModel):
    bankType: int
    id: int


class Resp(BaseAd):
    blockType: int
    chargeType: bool
    coinId: int
    currency: int
    gmtSort: int
    id: int
    isCopyBlock: bool
    isFollowed: bool
    isOnline: bool
    isTrade: bool
    isVerifyCapital: bool
    maxTradeLimit: float
    merchantLevel: int
    minTradeLimit: float
    orderCompleteRate: str
    payMethod: str
    payMethods: list[PayMethod]
    payName: str  # list[PayName] # приходит массив объектов внутри строки
    payTerm: int
    price: float
    takerAcceptAmount: str
    takerAcceptOrder: int
    takerLimit: int
    thumbUp: int
    totalTradeOrderCount: int
    tradeCount: float
    tradeMonthTimes: int
    tradeType: int
    uid: int
    userName: str
    merchantTags: list[int] | None
    labelName: str | None = None
    seaViewRoom: str | None = None
