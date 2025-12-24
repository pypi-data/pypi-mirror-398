"""Runtime context for PySleigh operations."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Optional

from pysleigh.paths import PathConfig


@dataclass(frozen=True)
class AoCContext:
    """Holds configuration for a single PySleigh invocation."""

    project_root: Path

    @cached_property
    def paths(self) -> PathConfig:
        """Return the path helpers anchored to the project root."""
        return PathConfig(self.project_root)


_current_context: Optional[AoCContext] = None


def get_context() -> AoCContext:
    """Return the globally configured context, defaulting to the current workdir."""
    global _current_context
    if _current_context is None:
        _current_context = AoCContext(Path.cwd())
    return _current_context


def set_context(context: AoCContext) -> None:
    """Set the context used by PySleigh components."""
    global _current_context
    _current_context = context


def reset_context() -> None:
    """Reset the cached context (useful for tests)."""
    global _current_context
    _current_context = None
