from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, NonNegativeInt, Field, PositiveInt


class C2COrder(BaseModel):
    cancelCountDown: NonNegativeInt
    consultCancelCountDown: NonNegativeInt


class OrderItem(BaseModel):
    orderId: int
    counterpartUid: PositiveInt
    counterpartNickName: str
    counterpartIsOnline: bool
    counterpartOrderCount: NonNegativeInt
    counterpartLastTradeTime: NonNegativeInt  # timestamp in ms
    counterpartMerchantLevel: NonNegativeInt
    counterpartThumbUp: NonNegativeInt
    counterpartRocketAmount: NonNegativeInt | None
    counterpartPrimeLevel: str = Field(pattern=r"^Prime\d+$")
    counterpartRecentWithdrawTime: PositiveInt | None  # timestamp in ms
    side: Literal[0, 1]  # 0=buy, 1=sell
    tradeMode: Literal[1, 2]  # предполагаемые значения
    runMode: Literal[1, 2]  # предполагаемые значения
    quoteAssetName: str = Field(min_length=1, max_length=10)
    cryptoAssetName: str = Field(min_length=1, max_length=10)
    amount: Decimal = Field(gt=0, decimal_places=2)
    quantity: Decimal = Field(gt=0)
    quote: Decimal = Field(gt=0, decimal_places=2)
    orderStatus: NonNegativeInt
    c2cOrder: C2COrder = None
    inNegotiation: bool


class ModelField(BaseModel):
    fieldId: str
    name: str
    fieldType: Literal["payee", "pay_account", "bank", "sub_bank", "qr_code"]
    index: PositiveInt
    maxLength: int | None = None
    required: bool | None = None
    copyable: bool
    remindWord: str | None = None
    valueType: str | None = None
    value: str
    nameList: list | None = None
    remindWordList: list | None = None


class PaymentMethod(BaseModel):
    id: PositiveInt
    userName: str = Field(min_length=1)
    bankType: PositiveInt
    bankNumber: str
    bankName: str | None = None
    bankAddress: str | None = None
    qrCode: str | None = None
    color: str = Field(pattern=r"^#[0-9A-F]{6}$")
    payMethodName: str = Field(min_length=1)
    paymentStatus: Literal[1]
    modelFieldsList: list[ModelField]


class OrderInfo(BaseModel):
    orderId: PositiveInt
    orderNo: PositiveInt
    uid: PositiveInt
    nickName: str = Field(min_length=1)
    realName: str | None = None
    roleName: Literal["maker", "taker"]
    side: Literal[0, 1]
    runMode: Literal[1]
    tradeMode: Literal[1]
    liquidDivision: Literal[3]
    sideName: Literal["buy", "sell"]
    quoteAssetId: PositiveInt
    quoteAssetType: Literal[1]
    quoteAssetName: str = Field(min_length=1, max_length=10)
    quoteAssetSymbol: str
    cryptoAssetId: PositiveInt
    cryptoAssetType: Literal[2]
    cryptoAssetName: str = Field(min_length=1, max_length=10)
    cryptoAssetSymbol: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    quantity: Decimal = Field(gt=0)
    quote: Decimal = Field(gt=0, decimal_places=2)
    orderStatus: NonNegativeInt
    gmtCreate: PositiveInt
    gmtModified: PositiveInt
    areaType: Literal[1]
    appealCountDown: NonNegativeInt


class OtherInfo(BaseModel):
    uid: PositiveInt
    nickName: str = Field(min_length=1)
    realName: str | None = None
    gmtCreate: PositiveInt
    merchantLevel: NonNegativeInt
    realTradeCountBuy: NonNegativeInt
    realTradeCountSell: NonNegativeInt
    registerTime: PositiveInt
    isPhoneBind: bool
    marginAssetId: NonNegativeInt
    marginAssetName: str | None = None
    marginAmount: NonNegativeInt
    appealMonthTimes: NonNegativeInt
    appealMonthWinTimes: NonNegativeInt
    isOnline: bool
    isSeniorAuth: bool
    orderCompleteRate: Decimal = Field(ge=0, le=100, decimal_places=2)
    tradeMonthCount: NonNegativeInt
    tradeCount: NonNegativeInt
    releaseTime: NonNegativeInt
    buyCompleteRate: Decimal = Field(ge=0, le=100, decimal_places=2)
    buyCancelTimeAvg: Decimal = Field(ge=0, decimal_places=2)
    thumbUp: NonNegativeInt
    merchantTags: str | None = None
    totalUserTradeCount: NonNegativeInt
    totalTradeOrderCount: NonNegativeInt
    totalTradeOrderCancelCount: NonNegativeInt
    orderBuyCompleteRate: Decimal = Field(ge=0, le=100, decimal_places=2)
    orderSellCompleteRate: Decimal = Field(ge=0, le=100, decimal_places=2)
    totalOrderCompleteRate: Decimal = Field(ge=0, le=100, decimal_places=2)
    counterpartRocketAmount: int | None = None
    counterpartPrimeLevel: str = Field(pattern=r"^Prime\d+$")
    counterpartRecentWithdrawTime: PositiveInt | None = None
    counterpartOrderCount: NonNegativeInt
    counterpartLastTradeTime: NonNegativeInt


class Fee(BaseModel):
    feeType: Literal[1]
    feeStatus: Literal[1, 2]
    fee: Decimal = Field(ge=0)
    feeName: str = Field(min_length=1)


class FeeInfo(BaseModel):
    totalFee: Decimal = Field(ge=0)
    feeList: list[Fee]


class OrderTag(BaseModel):
    isSoonLock: Literal[1, 2]
    isPremature: Literal[1, 2]
    isAppeal: Literal[1, 2]
    specialCancelFlag: Literal[1, 2]
    isPhone: Literal[1, 2]
    now: PositiveInt
    isAppealPremature: Literal[1, 2]
    isFollowed: bool
    isShield: bool
    negotiationStatus: int | None = None


class C2COrderDetail(BaseModel):
    matchPayId: int | None = None
    payTerm: PositiveInt
    payCode: str | None = None
    quote: Decimal = Field(gt=0, decimal_places=2)
    amount: Decimal = Field(gt=0, decimal_places=2)
    quantity: Decimal = Field(gt=0)
    quoteAssetName: str = Field(min_length=1)
    cryptoAssetName: str = Field(min_length=1)
    buyPayAccount: PositiveInt | None
    gmtPay: PositiveInt | None
    gmtResetCancel: PositiveInt | None = None
    orderStatus: NonNegativeInt
    cancelCountDown: NonNegativeInt
    consultCancelCountDown: NonNegativeInt
    waitCompletedCountDown: NonNegativeInt
    areaType: Literal[1]
    acceptStatus: Literal[0, 1]
    appCountDown: NonNegativeInt
    appMaxCountDown: NonNegativeInt


class OrderSnapshot(BaseModel):
    tradeInstructionStatus: Literal["INIT", "COMPLETED"]  # добавь другие статусы


class OrderFull(BaseModel):
    orderInfo: OrderInfo
    otherInfo: OtherInfo
    paymentMethod: list[PaymentMethod]
    feeInfo: FeeInfo
    orderTag: OrderTag
    c2cOrder: C2COrderDetail
    inNegotiation: bool
    takerEvaluateStatus: Literal[0, 1]
    orderSnapshot: OrderSnapshot
