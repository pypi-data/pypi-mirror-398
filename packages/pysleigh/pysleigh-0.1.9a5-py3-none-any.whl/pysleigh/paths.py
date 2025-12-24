"""Filesystem layout helpers for PySleigh commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathConfig:
    """Encapsulate the AoC repository filesystem layout."""

    project_root: Path

    def __post_init__(self) -> None:
        """Resolve the configured project root immediately."""
        object.__setattr__(self, "project_root", self.project_root.resolve())

    @property
    def input_root(self) -> Path:
        """Return the top-level inputs directory."""
        return self.project_root / "inputs"

    @property
    def article_root(self) -> Path:
        """Return the top-level articles directory."""
        return self.project_root / "articles"

    @property
    def answer_root(self) -> Path:
        """Return the top-level answers directory."""
        return self.project_root / "answers"

    @property
    def solution_root(self) -> Path:
        """Return the top-level solutions directory."""
        return self.project_root / "solutions"

    def metadata_path(self, year: int) -> Path:
        """Return the path to the metadata file for a given year."""
        return self.answer_root / f"year_{year}/metadata_year_{year}.json"

    def input_path(self, year: int, day: int) -> Path:
        """Return the path to the requested input file."""
        return self.input_root / f"year_{year}/input_{year}_day_{day:02d}.txt"

    def article_path(self, year: int, day: int) -> Path:
        """Return the path to the requested article file."""
        return self.article_root / f"year_{year}/article_{year}_day_{day:02d}.md"

    def answer_path(self, year: int, day: int) -> Path:
        """Return the path to the requested answers file."""
        return self.answer_root / f"year_{year}/answer_{year}_day_{day:02d}.txt"

    def solution_path(self, year: int, day: int) -> Path:
        """Return the path to the requested solution file."""
        return self.solution_root / f"solution_{year}_day_{day:02d}.py"
