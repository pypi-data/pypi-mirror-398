"""
API module templates: routes.py, v1_router.py, auth_router.py
"""


def get_api_init_template() -> str:
    """Return the __init__.py template for the api module."""
    return '''\
from .routes import router

__all__ = ["router"]
'''


def get_api_routes_template() -> str:
    """Return the routes.py template for the main API router."""
    return '''\
from fastapi import APIRouter

from app.api.v1 import v1_router

router = APIRouter(prefix="/api")

router.include_router(v1_router)
'''


def get_v1_init_template() -> str:
    """Return the __init__.py template for the v1 module."""
    return '''\
from .v1_router import router as v1_router

__all__ = ["v1_router"]
'''


def get_v1_router_template() -> str:
    """Return the v1_router.py template for API version 1."""
    return '''\
from fastapi import APIRouter

from app.api.v1.auth.auth_router import router as auth_router

router = APIRouter(prefix="/v1")


@router.get("/status", tags=["V1 Status"])
async def v1_status():
    return {"status": "v1 ok"}


router.include_router(auth_router)
'''


def get_auth_router_template() -> str:
    """Return the auth_router.py template for authentication routes."""
    return '''\
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/status")
async def status():
    return {"status": "ok"}
'''

