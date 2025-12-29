"""
Miscellaneous templates: .env, dev.py, lifespan_manager.py
"""


def get_env_template() -> str:
    """Return the .env template for environment variables."""
    return '''\
APP_NAME="FastAPI Doctor"
DESCRIPTION="Scaffold your fastapi project structure easily"
VERSION="0.1.0"
PORT=8000
ALLOWED_ORIGINS="localhost,127.0.0.1"
ALLOWED_METHODS="*"
ALLOWED_HEADERS="*"
DATABASE_URL="sqlite+aiosqlite:///./scaffold.db"
DEBUG=True
'''


def get_dev_template() -> str:
    """Return the dev.py template for development server."""
    return '''\
import uvicorn

def main():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == '__main__':
    main()
'''


def get_utils_init_template() -> str:
    """Return the __init__.py template for the utils module."""
    return '''\
from .lifespan_manager import lifespan

__all__ = ["lifespan"]
'''


def get_lifespan_template() -> str:
    """Return the lifespan_manager.py template for application lifecycle."""
    return '''\
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    await engine.dispose()
'''

