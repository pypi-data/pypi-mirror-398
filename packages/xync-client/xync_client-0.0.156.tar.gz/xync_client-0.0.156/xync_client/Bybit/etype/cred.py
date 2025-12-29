from pydantic import BaseModel

from xync_client.Abc.xtype import CredExOut


class PaymentItem(BaseModel):
    view: bool
    name: str
    label: str
    placeholder: str
    type: str
    maxLength: str
    required: bool


class BasePaymentConf(BaseModel):
    paymentType: int
    paymentName: str


class PaymentConfig(BasePaymentConf):
    class PaymentTemplateItem(BaseModel):
        labelDialect: str
        placeholderDialect: str
        fieldName: str

    paymentDialect: str
    paymentTemplateItem: list[PaymentTemplateItem]


class PaymentConfigVo(BasePaymentConf):
    checkType: int
    sort: int
    addTips: str
    itemTips: str
    online: int
    items: list[dict[str, str | bool]]


class PaymentTerm(CredExOut):
    id: str  # int
    realName: str
    paymentType: int  # int
    bankName: str
    branchName: str
    accountNo: str
    qrcode: str
    visible: int
    payMessage: str
    firstName: str
    lastName: str
    secondLastName: str
    clabe: str
    debitCardNumber: str
    mobile: str
    businessName: str
    concept: str
    online: str = None
    paymentExt1: str
    paymentExt2: str
    paymentExt3: str
    paymentExt4: str
    paymentExt5: str
    paymentExt6: str
    paymentTemplateVersion: int


class MyPaymentTerm(PaymentTerm):
    paymentConfig: PaymentConfig
    realNameVerified: bool


class CredEpyd(PaymentTerm):
    securityRiskToken: str = ""


class MyCredEpyd(CredEpyd):  # todo: заменить везде где надо CredEpyd -> MyCredEpyd
    countNo: str
    hasPaymentTemplateChanged: bool
    paymentConfigVo: PaymentConfigVo  # only for my cred
    realNameVerified: bool
    channel: str
    currencyBalance: list[str]
