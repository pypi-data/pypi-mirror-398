import importlib.metadata as md
import re
from pathlib import Path

import typer
from alembic import command
from fastapi_cli.cli import dev as fastapi_dev
from fastapi_cli.cli import run as fastapi_run

from .utils.alembic import get_alembic_config
from .utils.project import get_settings
from .utils.templating import copy_templates, to_canonical

TEMPLATE_DIR = Path(__file__).parent / "templates"

app = typer.Typer()


# Bootstrap specific commands


def validate_module_name(value: str) -> str:
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", value):
        raise typer.BadParameter(
            "Module name must be a valid Python identifier (letters, digits, "
            "underscores, not starting with a digit)."
        )
    return value


@app.command()
def init(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        prompt="Project name",
        help="The name of your new project.",
    ),
    description: str = typer.Option(
        None,
        "--description",
        "-d",
        prompt="Project description",
        help="Description of your project.",
    ),
    module_name: str = typer.Option(
        None,
        "--module-name",
        prompt="Project module name",
        help="The module name of your project.",
        callback=validate_module_name,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite existing files",
    ),
):
    canonical = to_canonical(name)
    target_dir = Path.cwd()

    version = md.version("he_kit")

    context = {
        "project_name": name,
        "canonical_name": canonical,
        "module_name": module_name,
        "description": description,
        "kit_version": version,
    }

    try:
        paths = copy_templates(TEMPLATE_DIR, target_dir, context, force)
        for path in paths:
            typer.echo(f"Created file '{path}'.")
        typer.echo(f"Created project '{name}' in {target_dir.resolve()}.")
    except FileExistsError as e:
        typer.secho(str(e), fg="red", err=True)


@app.command()
def settings():
    """Locate and print discovered project settings object."""
    try:
        settings = get_settings()
        for name, value in settings.model_dump().items():
            typer.echo(f"{name} = {value}")
    except Exception as e:
        typer.secho(str(e), fg="red", err=True)


# FastAPI wrappers


app.command("dev")(fastapi_dev)

app.command("run")(fastapi_run)

# Alembic wrappers


@app.command()
def makemigrations(message: str = typer.Argument("auto", help="Revision message")):
    """Autogenerate a new Alembic revision."""
    cfg = get_alembic_config()
    command.revision(cfg, message=message, autogenerate=True)
    typer.echo("Revision created.")


@app.command()
def migrate():
    """Apply all database migrations (upgrade to latest)."""
    cfg = get_alembic_config()
    command.upgrade(cfg, "head")
    typer.echo("Database upgraded to latest revision.")


@app.command()
def downgrade(
    revision: str = typer.Argument(
        "-1", help="Target revision (e.g., base, -1, abc123)"
    ),
):
    """Downgrade the database to a previous revision."""
    cfg = get_alembic_config()
    command.downgrade(cfg, revision)
    typer.echo(f"Database downgraded to {revision}.")


@app.command()
def history():
    """Show migration history."""
    cfg = get_alembic_config()
    command.history(cfg)


if __name__ == "__main__":
    app()
