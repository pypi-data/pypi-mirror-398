import importlib
import sys
from pathlib import Path

import typer

from nlbone.adapters.db import Base, init_sync_engine, sync_ping

init_db_command = typer.Typer(help="Database utilities")


def _import_target(target: str):
    """Import a module or call a bootstrap function if using 'module:function' syntax."""
    if ":" in target:
        mod_name, attr = target.split(":", 1)
        mod = importlib.import_module(mod_name)
        getattr(mod, attr)()
    else:
        importlib.import_module(target)


@init_db_command.command("init")
def init_db(
    drop: bool = typer.Option(False, "--drop", help="Drop all tables before creating them"),
    models: list[str] = typer.Option(
        None,
        "--models",
        "-m",
        help=(
            "List of modules or bootstrap functions to import before create_all. "
            "For example: app.models or app.bootstrap:register_models"
        ),
    ),
    add_cwd: bool = typer.Option(
        True,
        "--add-cwd/--no-add-cwd",
        help=("Add the current working directory to sys.path so imports work relative to the host project root."),
    ),
):
    """Create (and optionally drop) the database schema."""

    if add_cwd:
        sys.path.insert(0, str(Path.cwd()))

    for target in models or []:
        _import_target(target)

    engine = init_sync_engine()
    if drop:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    typer.echo("✅ DB schema initialized.")


@init_db_command.command("ping")
def ping():
    """Health check."""
    sync_ping()
    typer.echo("✅ DB connection OK")


@init_db_command.command("migrate")
def migrate():
    """Placeholder for migration trigger (Alembic, etc.)."""
    typer.echo("ℹ️  Hook your migration tool here.")
