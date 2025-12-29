"""
Project generator for scaffolding FastAPI projects.
"""

import subprocess
from pathlib import Path

from fastapi_doctor.config import (
    APP_DIRECTORIES,
    BASE_DEPENDENCIES,
    DATABASE_DRIVERS,
    DatabaseType,
)
from fastapi_doctor.generators.file_writer import FileWriter
from fastapi_doctor.templates import (
    get_api_init_template,
    get_api_routes_template,
    get_auth_router_template,
    get_config_template,
    get_core_init_template,
    get_cors_middleware_template,
    get_dev_template,
    get_env_template,
    get_index_html_template,
    get_lifespan_template,
    get_logging_template,
    get_main_template,
    get_middlewares_init_template,
    get_root_route_template,
    get_session_template,
    get_templates_init_template,
    get_utils_init_template,
    get_v1_init_template,
    get_v1_router_template,
    get_visual_template,
)


class ProjectGenerator:
    """Orchestrates the generation of a FastAPI project structure."""

    def __init__(
        self,
        project_name: str,
        database_type: DatabaseType = "sqlite",
        current_dir: Path | None = None,
    ) -> None:
        """
        Initialize the project generator.

        Args:
            project_name: Name of the project to create.
            database_type: Type of database to configure.
            current_dir: Base directory for project creation (defaults to cwd).
        """
        self.project_name = project_name
        self.database_type = database_type
        self.current_dir = current_dir or Path.cwd()

        # Handle "." as project name (use current directory name)
        if project_name == ".":
            self.name = self.current_dir.name
            self.project_path = self.current_dir
        else:
            self.name = project_name.strip()
            self.project_path = self.current_dir / self.name

        self.app_path = self.project_path / "app"
        self.writer: FileWriter | None = None

    def generate(self) -> Path:
        """
        Generate the complete project structure.

        Returns:
            Path to the created project.
        """
        self._create_project_directory()
        self._init_uv_project()
        self._install_dependencies()
        self._create_app_directories()
        self._cleanup_default_files()

        # Initialize writer for app directory
        self.writer = FileWriter(self.app_path)

        self._write_env_file()
        self._write_core_files()
        self._write_middleware_files()
        self._write_template_files()
        self._write_utils_files()
        self._write_api_files()
        self._write_database_files()
        self._write_dev_file()

        return self.app_path

    def _create_project_directory(self) -> None:
        """Create the main project directory if needed."""
        if self.project_name != ".":
            self.project_path.mkdir(parents=True, exist_ok=True)

    def _init_uv_project(self) -> None:
        """Initialize the UV project."""
        subprocess.run(
            ["uv", "init"],
            cwd=self.project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _install_dependencies(self) -> None:
        """Install project dependencies using UV."""
        deps = self._get_dependencies()
        subprocess.run(
            ["uv", "add", *deps],
            cwd=self.project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _get_dependencies(self) -> list[str]:
        """Get the list of dependencies based on database type."""
        deps = BASE_DEPENDENCIES.copy()
        deps.extend(DATABASE_DRIVERS.get(self.database_type, []))
        return deps

    def _create_app_directories(self) -> None:
        """Create the app directory structure."""
        self.app_path.mkdir(parents=True, exist_ok=True)
        for directory in APP_DIRECTORIES:
            (self.app_path / directory).mkdir(parents=True, exist_ok=True)

    def _cleanup_default_files(self) -> None:
        """Remove default files created by UV init."""
        default_main = self.project_path / "main.py"
        if default_main.exists():
            default_main.unlink()

    def _write_env_file(self) -> None:
        """Write the .env file to the project root."""
        env_path = self.project_path / ".env"
        env_path.write_text(get_env_template(), encoding="utf-8")

    def _write_core_files(self) -> None:
        """Write core module files."""
        assert self.writer is not None
        self.writer.write("main.py", get_main_template())
        self.writer.write("core/__init__.py", get_core_init_template())
        self.writer.write("core/config.py", get_config_template())
        self.writer.write("core/logging.py", get_logging_template())

    def _write_middleware_files(self) -> None:
        """Write middleware module files."""
        assert self.writer is not None
        self.writer.write("middlewares/__init__.py", get_middlewares_init_template())
        self.writer.write("middlewares/cors_middleware.py", get_cors_middleware_template())

    def _write_template_files(self) -> None:
        """Write template module files (Jinja2 templates)."""
        assert self.writer is not None
        self.writer.write("templates/__init__.py", get_templates_init_template())
        self.writer.write("templates/index.html", get_index_html_template())
        self.writer.write("templates/root_route.py", get_root_route_template())
        self.writer.write("templates/visual.py", get_visual_template())

    def _write_utils_files(self) -> None:
        """Write utils module files."""
        assert self.writer is not None
        self.writer.write("utils/__init__.py", get_utils_init_template())
        self.writer.write("utils/lifespan_manager.py", get_lifespan_template())

    def _write_api_files(self) -> None:
        """Write API module files."""
        assert self.writer is not None
        self.writer.write("api/__init__.py", get_api_init_template())
        self.writer.write("api/routes.py", get_api_routes_template())
        self.writer.write("api/v1/__init__.py", get_v1_init_template())
        self.writer.write("api/v1/v1_router.py", get_v1_router_template())
        self.writer.write("api/v1/auth/auth_router.py", get_auth_router_template())

    def _write_database_files(self) -> None:
        """Write database module files."""
        assert self.writer is not None
        self.writer.write("database/session.py", get_session_template())

    def _write_dev_file(self) -> None:
        """Write the dev.py file to the project root."""
        dev_path = self.project_path / "dev.py"
        dev_path.write_text(get_dev_template(), encoding="utf-8")

