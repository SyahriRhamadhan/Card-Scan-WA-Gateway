from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "cardscan-backend"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    ocr_lang: str = "eng"
    ocrspace_api_key: str = "helloworld"
    ocrspace_endpoint: str = "https://api.ocr.space/parse/image"

    wa_gateway_base_url: str = ""
    wa_gateway_send_path: str = "/api/v2/messages/text"
    wa_gateway_token: str | None = None
    default_whatsapp_to: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
