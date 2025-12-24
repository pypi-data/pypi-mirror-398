"""Command entrypoints for PySleigh Typer apps."""

from pysleigh.commands import data as data_commands
from pysleigh.commands import solution as solution_commands

__all__ = ["data_commands", "solution_commands"]
