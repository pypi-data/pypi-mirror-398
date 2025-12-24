"""Session helpers for authenticated AoC requests."""

from __future__ import annotations

import os

import typer


def get_session_token() -> str:
    """Return the `SESSION_TOKEN` cookie required by Advent of Code."""
    token = os.environ.get("SESSION_TOKEN")
    if not token:
        typer.echo(
            "SESSION_TOKEN environment variable not set.\n"
            "Find your 'session' cookie in browser dev tools and export it, e.g.:\n"
            "  export SESSION_TOKEN='...'",
            err=True,
        )
        raise typer.Exit(code=1)
    return token
