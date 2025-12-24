from pyro_client.client.file import FileClient
from xync_bot import XyncBot

from xync_client.Abc.Agent import BaseAgentClient
from asyncio import run
from x_model import init_db
from xync_schema.models import Agent, Ex

from xync_client.Okx.ex import ExClient
from xync_client.loader import NET_TOKEN, PAY_TOKEN


class AgentClient(BaseAgentClient):
    async def my_fiats(self):
        response = await self._get("/v3/c2c/receiptAccounts")
        fiats = response["data"]
        return {
            fiat["type"]: field["value"] for fiat in fiats for field in fiat["fields"] if field["key"] == "accountNo"
        }


async def main():
    from xync_client.loader import TORM

    cn = await init_db(TORM)
    ex = await Ex.get(name="Okx")
    agent = await Agent.get(actor__ex=ex).prefetch_related("actor__ex", "actor__person__user__gmail")
    fbot = FileClient(NET_TOKEN)
    ecl: ExClient = ex.client(fbot)
    abot = XyncBot(PAY_TOKEN, cn)
    cl = agent.client(ecl, fbot, abot)

    _fiats = await cl.my_fiats()

    await cl.stop()


if __name__ == "__main__":
    run(main())
