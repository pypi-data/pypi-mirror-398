"""
Middleware module templates: cors_middleware.py
"""


def get_middlewares_init_template() -> str:
    """Return the __init__.py template for the middlewares module."""
    return '''\
from .cors_middleware import add_cors_middleware

__all__ = ["add_cors_middleware"]
'''


def get_cors_middleware_template() -> str:
    """Return the cors_middleware.py template for CORS configuration."""
    return '''\
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings


def add_cors_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS.split(","),
        allow_headers=settings.ALLOWED_HEADERS.split(","),
    )
'''

