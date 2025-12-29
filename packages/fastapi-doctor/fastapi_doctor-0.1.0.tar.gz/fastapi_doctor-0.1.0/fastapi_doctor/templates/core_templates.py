"""
Core module templates: main.py, config.py, logging.py
"""


def get_main_template() -> str:
    """Return the main.py template for the FastAPI application."""
    return '''\
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.routes import router as api_router
from app.core import settings, setup_logging
from app.middlewares import add_cors_middleware
from app.templates import root_route
from app.utils import lifespan


def get_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url=False,
        redoc_url=False,
        lifespan=lifespan,
    )

    add_cors_middleware(app)

    app.include_router(root_route)

    @app.get("/docs", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
        )

    app.include_router(api_router)

    return app


app = get_app()
'''


def get_core_init_template() -> str:
    """Return the __init__.py template for the core module."""
    return '''\
from .config import settings
from .logging import setup_logging

__all__ = ["settings", "setup_logging"]
'''


def get_config_template() -> str:
    """Return the config.py template for settings management."""
    return '''\
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # ── App ─────────────────────────────
    APP_NAME: str = Field(
        "",
        description="Name OF The App",
        validation_alias="APP_NAME",
    )
    DESCRIPTION: str = Field(
        "",
        description="Description of the app",
        validation_alias="DESCRIPTION",
    )
    VERSION: str = Field(
        "0.0.1", description="Version of the app", validation_alias="VERSION"
    )


    # ── Debug ────────────────────────────
    DEBUG: bool = Field(
        False, description="Debug mode", validation_alias="DEBUG"
    )
    # ── CORS ────────────────────────────
    ALLOWED_ORIGINS: str = Field(
        description="Allowed origins", validation_alias="ALLOWED_ORIGINS"
    )
    ALLOWED_METHODS: str = Field(
        description="Allowed methods", validation_alias="ALLOWED_METHODS"
    )
    ALLOWED_HEADERS: str = Field(
        description="Allowed headers", validation_alias="ALLOWED_HEADERS"
    )

    # ── Database ─────────────────────────
    DATABASE_URL: str = Field(
        description="Database URL", validation_alias="DATABASE_URL"
    )

    # ── Server ──────────────────────────
    HOST: str = Field(
        "0.0.0.0", description="Host of the server", validation_alias="HOST"
    )
    PORT: int = Field(8000, description="Port of the server", validation_alias="PORT")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
'''


def get_logging_template() -> str:
    """Return the logging.py template for logging configuration."""
    return '''\
import logging
import sys

from app.core import settings

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
)


def setup_logging() -> None:
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Clear existing handlers (important for reloads)
    root_logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root_logger.addHandler(handler)

    # Reduce noise from third-party libs
    logging.getLogger("uvicorn.access").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("uvicorn.error").setLevel(
        logging.DEBUG if settings.DEBUG else logging.INFO
    )
    logging.getLogger("asyncio").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )
'''

