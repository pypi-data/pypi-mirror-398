"""Core exports for PySleigh."""

from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path
from typing import Final

__all__ = ["cli", "__version__"]


def _read_version() -> str:  # pragma: no mutate
    """Return the installed package version, falling back to pyproject for editable installs."""
    try:
        return metadata.version("pysleigh")
    except metadata.PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        if pyproject.exists():
            with pyproject.open("rb") as file:
                try:
                    return tomllib.load(file)["project"]["version"]
                except Exception:  # pragma: no cover - malformed pyproject is non-standard
                    pass
    return "0.0.0"  # pragma: no cover - unreachable in normal environments


__version__: Final[str] = _read_version()
