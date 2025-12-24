"""Utility to locate and instantiate AoC solutions."""

from __future__ import annotations

import importlib
import sys

import typer

from pysleigh.base import Base
from pysleigh.context import get_context


def load_solution(year: int, day: int) -> Base:  # pragma: no mutate
    """Import and instantiate a solution class for the requested day."""
    context = get_context()
    root = str(context.project_root)
    if root not in sys.path:
        sys.path.insert(0, root)

    module_name = f"solutions.year_{year}.solution_{year}_day_{day:02d}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        typer.echo(f"Could not find module {module_name!r}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        solution_cls = module.Solution  # type: ignore[attr-defined]
    except AttributeError as exc:
        typer.echo(f"Module {module_name!r} does not define a 'Solution' class.", err=True)
        raise typer.Exit(code=1) from exc

    return solution_cls(year=year, day=day)
