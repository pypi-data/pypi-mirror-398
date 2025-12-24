from pydantic import BaseModel, Field
from xync_schema.xtype import BaseAd
from typing import Optional, Literal


class Merchant(BaseModel):
    nickName: str
    imId: str
    memberId: str
    registry: int  # timestamp in milliseconds
    vipLevel: int
    greenDiamond: bool
    emailAuthentication: bool
    smsAuthentication: bool
    identityVerification: bool
    lastOnlineTime: int  # timestamp in milliseconds
    badge: str
    merchantType: str


class MerchantStatistics(BaseModel):
    totalBuyCount: int
    totalSellCount: int
    doneLastMonthCount: int
    goodRate: Optional[str] = None
    lastMonthCompleteRate: str  # decimal as string
    completeRate: str  # decimal as string
    avgHandleTime: float
    avgBuyHandleTime: float
    avgSellHandleTime: float


class AdsReq(BaseModel):
    coinId: str  # hex
    currency: str  # hex
    tradeType: Literal["SELL", "BUY"]

    payMethod: str = ""  # int,int
    amount: str = ""  # int
    page: int = 1

    blockTrade: str = "false"  # bool
    # countryCode: str = ""
    follow: str = "false"
    haveTrade: str = "false"
    adsType: int = 1
    allowTrade: str = "false"


class Ad(BaseAd):
    exid: str | None = Field(alias="id")
    price: float
    availableQuantity: float
    coinName: str
    countryCode: str
    updateTime: int  # timestamp in milliseconds
    currency: str
    tradeType: int
    payMethod: str
    merchant: Merchant
    merchantStatistics: MerchantStatistics
    expirationTime: int  # in minutes?
    autoResponse: str
    tradeTerms: str
    minTradeLimit: float
    maxTradeLimit: float
    kycLevel: int
    requireMobile: bool
    fiatCount: int
    fiatCountLess: int
    maxPayLimit: int
    orderPayCount: int
    exchangeCount: int
    minRegisterDate: int
    blockTrade: bool
    tags: str


class AdUpd(BaseAd):
    id: str
    price: float
    coinId: str  # hex
    currency: str
    tradeType: Literal["SELL", "BUY"]
    payment: str
    minTradeLimit: float
    quantity: float
    maxTradeLimit: float
    deviceId: str
    autoResponse: str = ""  # quote("P1132998804")

    tradeTerms: str = ""
    priceType: int = 0

    adsType: int = 1
    allowSys: str = "true"  # bool
    apiVersion: str = "1.0.0"
    authVersion: str = "v2"
    blockTrade: str = "false"
    countryCode: str = "RU"
    display: int = 1  # bool
    exchangeCount: int = 0
    expirationTime: int = 15
    fiatCount: int = 0
    fiatCountLess: int = 0
    kycLevel: Literal["PRIMARY"] = "PRIMARY"
    maxPayLimit: int = 0
    minRegisterDate: int = 0
    requireMobile: str = "false"  # bool
    securityOrderPaymentInfo: str = ""
