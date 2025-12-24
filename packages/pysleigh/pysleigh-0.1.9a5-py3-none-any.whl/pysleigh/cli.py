"""Typer CLI composition for PySleigh."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from pysleigh import __version__
from pysleigh.commands import data as data_commands
from pysleigh.commands import solution as solution_commands
from pysleigh.commands import verify as verify_commands
from pysleigh.context import AoCContext, get_context, set_context

app = typer.Typer(
    help="Advent of Code helper CLI with data fetch, solution helpers, verification, and metadata."
)
app.add_typer(data_commands.data_app, name="data")
app.add_typer(solution_commands.solution_app, name="solution")
app.add_typer(verify_commands.verify_app, name="verify")


def _version_callback(show_version: bool) -> None:
    """Display the installed PySleigh version and exit early."""
    if not show_version:
        return
    typer.echo(f"PySleigh {__version__}")
    raise typer.Exit()


@app.command("version", help="Show the installed PySleigh version.")
def version_command() -> None:
    """Emit the current PySleigh version."""
    typer.echo(f"PySleigh {__version__}")


@app.callback(invoke_without_command=True)
def main(  # pragma: no cover - CLI bootstrapping
    ctx: typer.Context,
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        envvar="PYSLEIGH_PROJECT_ROOT",
        help="Path to the Advent of Code repository to operate on.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_eager=True,
        callback=_version_callback,
        help="Show the installed PySleigh version and exit.",
    ),
) -> None:
    """Set context when subcommands run; otherwise show readiness."""
    resolved_root = (project_root or Path.cwd()).expanduser().resolve()
    if ctx.invoked_subcommand:
        try:
            current_root = get_context().project_root
        except Exception:
            current_root = None

        set_context(AoCContext(resolved_root))
        ctx.obj = {"project_root": resolved_root}
        if current_root and current_root != resolved_root:
            typer.echo(f"[pysleigh] Project root updated: {current_root} -> {resolved_root}")
        elif not current_root:
            typer.echo(f"[pysleigh] Project root set to {resolved_root}")
    if ctx.invoked_subcommand:
        return
    else:
        typer.echo("PySleigh CLI is ready. Use --help for commands.")
