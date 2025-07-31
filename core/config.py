from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []
    POSTGRES_DSN: PostgresDsn = "postgresql+asyncpg://user:pass@localhost:5432/tg_gifts"
    TELETHON_API_ID: str
    TELETHON_API_HASH: str
    TELETHON_SESSION_STRING: str
    TARGET_CHANNELS: List[int] = []
    CHECK_INTERVAL: int = 300
    MAX_GIFT_PRICE: float = 5000.0

    @validator('ADMIN_IDS', 'TARGET_CHANNELS', pre=True)
    def parse_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',') if x.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()