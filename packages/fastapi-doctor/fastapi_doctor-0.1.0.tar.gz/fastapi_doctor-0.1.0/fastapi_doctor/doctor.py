"""
FastAPI Doctor CLI - Scaffold your FastAPI project structure easily.
"""

from typing import Optional

import typer
from typer import Argument, Exit, Typer, echo

from fastapi_doctor.config import DatabaseType
from fastapi_doctor.generators import ProjectGenerator

app = Typer(
    name="FastAPI Doctor",
    help="Scaffold your fastapi project structure easily",
    invoke_without_command=True,
)


@app.callback()
def main(ctx: typer.Context) -> None:
    """
    Scaffold your fastapi project structure easily.
    Show help in case of error or no command is provided.
    """
    if ctx.invoked_subcommand is None:
        echo(ctx.get_help())


@app.command()
def new(
    ctx: typer.Context,
    project_name: Optional[str] = Argument(None, help="Name of the project to create"),
    database_type: DatabaseType = typer.Option(
        default="sqlite", help="Type of database to use", show_default=True
    ),
) -> None:
    """
    Create a new FastAPI project.
    """
    if project_name is None:
        echo(ctx.get_help())
        return

    if project_name.isspace():
        echo("Project name cannot be empty")
        echo(ctx.get_help())
        return

    generator = ProjectGenerator(
        project_name=project_name,
        database_type=database_type,
    )

    project_path = generator.generate()

    echo(f"Project created successfully at {project_path}")


@app.command()
def add(
    ctx: typer.Context,
    module_name: Optional[str] = Argument(None, help="Name of the module to add"),
) -> None:
    """
    Add a new module to the project.
    Generate the necessary files and folders for the new module.
    """
    if module_name is None:
        echo(ctx.get_help())
        raise Exit(1)

    echo(f"Adding module {module_name} to the project...")


@app.command()
def serve() -> None:
    """
    Serve the project using uvicorn.
    """
    echo("Serving the project...")
