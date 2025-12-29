from xync_client.Bybit.etype.cred import PaymentTerm
from xync_schema.models import CredEx, PmEx

from xync_client.Abc.Order import BaseOrderClient


class OrderClient(BaseOrderClient):
    # 5: Перевод сделки в состояние "оплачено", c отправкой чека
    async def mark_payed(self, payterm: PaymentTerm = None, receipt: bytes = None):
        if payterm:
            pt = str(payterm.paymentType)
            pid = payterm.id
        else:
            pmx = await PmEx.get(pm__pmcurs__id=self.order.cred.pmcur_id, ex=self.agent_client.ex_client.ex)
            pt = pmx.exid
            cdx = await CredEx.get(cred_id=self.order.cred_id, ex=self.agent_client.ex_client.ex)
            pid = str(cdx.exid)
        self.agent_client.api.mark_as_paid(orderId=str(self.order.exid), paymentType=pt, paymentId=pid)

    # 6: Отмена одобренной сделки
    async def cancel_order(self) -> bool: ...

    # 7: Подтвердить получение оплаты
    async def confirm(self):
        self.agent_client.api.release_assets(orderId=str(self.order.exid))

    # 9, 10: Подать аппеляцию cо скриншотом/видео/файлом
    async def start_appeal(self, file) -> bool: ...

    # 11, 12: Встречное оспаривание полученной аппеляции cо скриншотом/видео/файлом
    async def dispute_appeal(self, file) -> bool: ...

    # 15: Отмена аппеляции
    async def cancel_appeal(self) -> bool: ...

    # 16: Отправка сообщения юзеру в чат по ордеру с приложенным файлом
    async def send_order_msg(self, msg: str, file=None) -> bool: ...

    # 17: Отправка сообщения по апелляции
    async def send_appeal_msg(self, file, msg: str = None) -> bool: ...

    # Загрузка файла
    async def _upload_file(self, order_id: int, path_to_file: str): ...
