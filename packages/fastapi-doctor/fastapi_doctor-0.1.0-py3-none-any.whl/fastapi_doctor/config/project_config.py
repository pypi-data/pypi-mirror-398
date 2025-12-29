"""
Project configuration constants and mappings.
"""

from typing import Literal

# Type alias for supported database types
DatabaseType = Literal["sqlite", "postgresql", "mysql"]

# Base dependencies required for all projects
BASE_DEPENDENCIES: list[str] = [
    "fastapi",
    "jinja2",
    "pydantic-settings",
    "scalar-fastapi",
    "uvicorn",
]

# Database-specific driver dependencies
DATABASE_DRIVERS: dict[DatabaseType, list[str]] = {
    "sqlite": ["aiosqlite", "sqlmodel"],
    "postgresql": ["asyncpg", "sqlmodel"],
    "mysql": ["asyncmy", "sqlmodel"],
}

# Directory structure for the app folder
APP_DIRECTORIES: list[str] = [
    "api",
    "api/v1",
    "api/v1/auth",
    "core",
    "database",
    "middlewares",
    "models",
    "schemas",
    "services",
    "utils",
    "templates",
]

