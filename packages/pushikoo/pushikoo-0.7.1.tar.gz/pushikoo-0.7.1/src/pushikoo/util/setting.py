from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BeforeValidator, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

CRON_SCHEDULER_MAX_WORKERS = 10
DATA_DIR = Path("./data")
CACHE_DIR = DATA_DIR / ".cache"
FILE_DIR = DATA_DIR / "files"

IMAGE_LINK_DEFAULT_EXPIRE_SECOND = 100 * 365 * 24 * 3600

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FILE_DIR.mkdir(parents=True, exist_ok=True)


def _parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list):
        return v
    raise ValueError(v)


def _parse_str_list(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    if isinstance(v, list):
        return [str(i).strip() for i in v if str(i).strip()]
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 11589

    SECRET_TOKENS: list[str] = Field(default_factory=list)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    ENVIRONMENT: Literal["local", "staging", "production"] = "production"

    # ------------------------------------------------------------------
    # Raw host values loaded from environment variables
    # These represent the *direct* values from .env (or default values),
    # and should never be used directly by business logic.
    # Instead, the public computed fields (BACKEND_BASE_HOST / FRONTEND_BASE_HOST)
    # determine the effective host based on ENVIRONMENT.
    # Pattern:
    #     - In local/staging → use these raw env values
    #     - In production → ignore these and derive from _BASE_HOST automatically

    raw_backend_host: str = Field(
        default="http://127.0.0.1:11589", alias="BACKEND_BASE_HOST"
    )
    raw_frontend_host: str = Field(
        default="http://127.0.0.1:3000", alias="FRONTEND_BASE_HOST"
    )
    raw_base_host: str = Field(default="https://your.website.com", alias="BASE_HOST")

    raw_cors_origins: Annotated[list[AnyUrl] | str, BeforeValidator(_parse_cors)] = (
        Field(
            default_factory=list,
            alias="CORS_ORIGINS",
        )
    )
    # ------------------------------------------------------------------

    # OIDC / SSO configuration
    SSO_CLIENT_ID: str | None = None
    SSO_CLIENT_SECRET: str | None = None
    SSO_ISSUER_URL: str | None = None
    ADMIN_USERS: Annotated[list[str] | str, BeforeValidator(_parse_str_list)] = Field(
        default_factory=list
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def BACKEND_BASE_HOST(self) -> str:
        if self.ENVIRONMENT == "production":
            return self.raw_base_host
        return self.raw_backend_host

    @computed_field  # type: ignore[prop-decorator]
    @property
    def FRONTEND_BASE_HOST(self) -> str:
        if self.ENVIRONMENT == "production":
            return self.raw_base_host
        return self.raw_frontend_host

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CORS_ORIGINS(self) -> list[str]:
        if self.ENVIRONMENT == "local":
            return ["*"]
        return [str(origin).rstrip("/") for origin in self.raw_cors_origins] + [
            self.FRONTEND_BASE_HOST
        ]


settings = Settings()  # type: ignore
