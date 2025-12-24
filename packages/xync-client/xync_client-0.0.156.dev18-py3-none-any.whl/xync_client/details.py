import asyncio
from xync_client.loader import TORM
from x_model import init_db
from xync_schema import models
import re
from typing import List, Dict

details = ["дай(те)?", "номер", "рек(и|визиты)", "карту", "банк(и|а)?", "куда", "(на )?как(ой|ую)", "актуал"]

begging = ["вз (лайк|отзыв)", "взаим(о|ный)?", "отзыву?", "like", "лайкни"]

greetings = [
    "привет(ствую|ик)?",
    "здаровa?",
    "здоров(а|енько)",
    "здравствуй(те)?",
    "Добрый ?(день|вечер)?",
    "h(i|ello)",
    "сал(ют|лам)",
    "ку",
    "йо",
    "хай",
    "добро пожаловать",
]


async def search_messages(phrases_to_find) -> List[Dict[str, str]]:
    _ = await init_db(TORM, True)
    msgs = await models.Msg.all().values("txt")
    patterns = [re.compile(rf"\b{phrase}\b", re.IGNORECASE) for phrase in phrases_to_find]
    results = []
    for msg in msgs:
        if not msg["txt"]:
            continue
        for pattern in patterns:
            if pattern.search(msg["txt"]):
                results.append({pattern.pattern: msg["txt"]})
    for i in results:
        print(i)
    return results


if __name__ == "__main__":
    asyncio.run(search_messages(greetings))
