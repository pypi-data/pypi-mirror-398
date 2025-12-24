from dotenv import load_dotenv
from os import getenv as env
from xync_schema import models

load_dotenv()

NET_TOKEN = env("NET_TOKEN")
PAY_TOKEN = env("PAY_TOKEN")
PG_DSN = f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', 'xyncdbs')}:{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"
TORM = {
    "connections": {"default": PG_DSN},
    "apps": {"models": {"models": [models, "aerich.models"]}},
    "use_tz": False,
    "timezone": "UTC",
}
GP = env("GP")
PRX = env("PRX")
TG_API_ID = env("TG_API_ID")
TG_API_HASH = env("TG_API_HASH")
WSToken = env("WST")
