from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "intelligent-model-router"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql+asyncpg://router:router@localhost:5432/model_router"
    database_url_sync: str = "postgresql://router:router@localhost:5432/model_router"
    redis_url: str = "redis://localhost:6379/0"

    provider_a_api_key: str = ""
    provider_b_api_key: str = ""
    use_mock_providers: bool = True

    default_model_id: str = "model-small"
    seed_demo_data: bool = True

    max_input_chars: int = 100_000
    api_key_prefix: str = "imr_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
