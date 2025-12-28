"""local loader"""

from dotenv import load_dotenv
from os import getenv as env

load_dotenv()

if _ := env("API_HOST"):
    API_URL = "https://" + _
if _ := env("APP_HOST"):
    APP_URL = "https://" + _
PG_DSN = (
    f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', '0.0.0.0')}"
    f":{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"
)
TOKEN = env("TOKEN")
TORM = {
    "connections": {"default": PG_DSN},
    "apps": {"models": {"models": ["aerich.models"]}},
    "use_tz": False,
    "timezone": "UTC",
}
