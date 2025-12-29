from dotenv import load_dotenv
from os import getenv as env

from xync_schema import models

load_dotenv()

PG_DSN = (
    f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', 'dbs')}"
    f":{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"
)
TOKEN = env("TOKEN")
API_URL = "https://" + env("API_DOMAIN")
WH_URL = API_URL + "/wh/" + TOKEN

TORM = {
    "connections": {"default": PG_DSN},
    "apps": {"models": {"models": [models, "aerich.models"]}},
    "use_tz": False,
    "timezone": "UTC",
}

glob = object
