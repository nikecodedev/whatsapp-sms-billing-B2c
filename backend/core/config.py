from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "QUESH"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://quesh:quesh@localhost:5432/quesh"
    DATABASE_URL_SYNC: str = "postgresql://quesh:quesh@localhost:5432/quesh"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Claude AI
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Z-API (WhatsApp)
    ZAPI_INSTANCE_ID: str = ""
    ZAPI_TOKEN: str = ""
    ZAPI_CLIENT_TOKEN: str = ""
    ZAPI_BASE_URL: str = "https://api.z-api.io"

    # Twilio (SMS + Voice — same account, voice needs a voice-capable number)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_VOICE_FROM_NUMBER: str = ""  # Falls back to TWILIO_FROM_NUMBER if empty
    TWILIO_VOICE_LANGUAGE: str = "pt-BR"
    TWILIO_VOICE_NAME: str = "Polly.Camila-Neural"  # Brazilian Portuguese neural voice
    # Public base URL Twilio uses to fetch TwiML and post status callbacks.
    # Must be reachable from the public internet (use ngrok in local dev).
    PUBLIC_BASE_URL: str = ""  # Falls back to APP_BASE_URL if empty

    # Asaas (Payments)
    ASAAS_API_KEY: str
    ASAAS_BASE_URL: str = "https://api.asaas.com/v3"

    # App base URL (for payment link shortener redirect)
    APP_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
