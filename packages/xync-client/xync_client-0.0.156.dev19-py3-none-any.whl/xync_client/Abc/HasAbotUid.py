from PGram import Bot
from aiogram.types import Message


class HasAbotUid:
    abot: Bot
    uid: int

    async def receive(self, text: str, photo: bytes = None, video: bytes = None) -> Message:
        return await self.abot.send(self.uid, txt=text, photo=photo, video=video)
