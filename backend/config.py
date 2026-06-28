from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve .env relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    database_url: str
    mapbox_token: str = ""
    geocoding_api_key: str = ""

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
