import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _guess_env_file() -> str | None:
    try:
        explicit = os.getenv("NLBONE_ENV_FILE")
        if explicit:
            return explicit

        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            return str(cwd_env)

        for i in range(0, 8):
            p = Path.cwd().resolve().parents[i]
            f = p / ".env"
            if f.exists():
                return str(f)
    except Exception as e:
        raise Exception("Failed to guess env file path!") from e


def read_from_os_env() -> bool:
    raw = os.getenv("NLBONE_ENV") or os.getenv("ENV") or os.getenv("ENVIRONMENT")
    if not raw:
        return False
    return raw.strip().lower() in {"prod", "production", "stage", "staging"}


class Settings(BaseSettings):
    # ---------------------------
    # App
    # ---------------------------
    PORT: int = 8000
    ENV: Literal["local", "dev", "staging", "prod"] = Field(default="local")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(default="INFO")
    LOG_JSON: bool = Field(default=True)

    SNOWFLAKE_WORKER_ID: int = Field(default=1)
    SNOWFLAKE_DATACENTER_ID: int = Field(default=1)

    AUDIT_DEFAULT_ENABLE: bool = False

    # ---------------------------
    # HTTP / Timeouts
    # ---------------------------
    HTTP_TIMEOUT_SECONDS: float = Field(default=10.0)

    # ---------------------------
    # Keycloak / Auth
    # ---------------------------
    KEYCLOAK_SERVER_URL: AnyHttpUrl = Field(default="https://keycloak.local/auth")
    KEYCLOAK_REALM_NAME: str = Field(default="numberland")
    KEYCLOAK_CLIENT_ID: str = Field(default="nlbone")
    KEYCLOAK_CLIENT_SECRET: SecretStr = Field(default=SecretStr("dev-secret"))
    PRICING_API_SECRET: str = ""

    AUTH_SERVICE_URL: AnyHttpUrl = Field(default="https://auth.numberland.ir")
    CLIENT_ID: str = Field(default="", validation_alias=AliasChoices("KEYCLOAK_CLIENT_ID"))
    CLIENT_SECRET: SecretStr = Field(default="", validation_alias=AliasChoices("KEYCLOAK_CLIENT_SECRET"))

    # ---------------------------
    # Database
    # ---------------------------
    POSTGRES_DB_DSN: str = Field(default="postgresql+asyncpg://user:pass@localhost:5432/nlbone")
    DB_ECHO: bool = Field(default=False)
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)

    # ---------------------------
    # Messaging / Cache
    # ---------------------------
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_BACKEND: Literal["memory", "redis"] = Field(default="memory")
    CACHE_DEFAULT_TTL_S: int = Field(default=300)

    # --- Event bus / Outbox ---
    EVENT_BUS_BACKEND: Literal["inmemory"] = Field(default="inmemory")
    OUTBOX_ENABLED: bool = Field(default=False)
    OUTBOX_POLL_INTERVAL_MS: int = Field(default=500)

    # ---------------------------
    # UPLOADCHI
    # ---------------------------
    UPLOADCHI_BASE_URL: AnyHttpUrl = Field(default="https://uploadchi.numberland.ir/v1/files")
    UPLOADCHI_TOKEN: SecretStr = Field(default="")

    # ---------------------------
    # PERCOLATE
    # ---------------------------
    ELASTIC_PERCOLATE_URL: str = Field(default="http://localhost:9200")
    ELASTIC_PERCOLATE_USER: str = Field(default="")
    ELASTIC_PERCOLATE_PASS: SecretStr = Field(default="")

    # ---------------------------
    # Pricing
    # ---------------------------
    PRICING_SERVICE_URL: AnyHttpUrl = Field(default="https://pricing.numberland.ir/v1")

    # ---------------------------
    # Crypto
    # ---------------------------
    FERNET_KEY: str = Field(default="")

    RABBITMQ_URL: str = Field(default="", description="amqp(s)://user:pass@host:5672/vhost")
    RABBITMQ_TICKETING_EXCHANGE: str = "crm_stage.ticket"
    RABBITMQ_TICKETING_ROUTING_KEY_CREATE_V1: str = "crm_stage.ticket.create.v1"

    PROJECT_LOCALE_PATH: str = ""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def load(cls, env_file: str | None = None) -> "Settings":
        if read_from_os_env():
            return cls()
        return cls(_env_file=env_file or _guess_env_file())


@lru_cache(maxsize=4)
def get_settings(env_file: str | None = None) -> Settings:
    """
    Cached settings for fast access across the app.
    Usage:
        from nlbone.config.settings import get_settings
        settings = get_settings()
    """
    return Settings.load(env_file)
