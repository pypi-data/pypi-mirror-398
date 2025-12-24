"""Typer commands for verifying solutions against cached answers."""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

import typer

from pysleigh.context import get_context
from pysleigh.loader import load_solution

verify_app = typer.Typer(
    help="Verify cached answers against local solutions, capture timings, and log metadata."
)


def _execute_with_timing(func: Callable[[], Any]) -> tuple[str | None, float]:
    """Run a callable, returning its stringified result and elapsed seconds."""  # pragma: no cover
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    return (None if result is None else str(result)), elapsed


def _format_ms(duration: float | None) -> str:
    """Render a duration in milliseconds or mark it unavailable."""
    return "n/a" if duration is None else f"{duration * 1000:.3f} ms"


def _write_metadata_record(  # pragma: no cover - exercised via verify_answers integration
    year: int,
    day: int,
    title: str,
    part_status: dict[int, str | None],
    part_timings: dict[int, float | None],
) -> None:
    """Persist verification metadata keyed by year then day."""
    paths = get_context().paths
    metadata_path = paths.metadata_path(year)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def _status_to_bool(status: str | None) -> bool | None:
        if status == "ok":
            return True
        if status in ("mismatch", "missing"):
            return False
        return None

    def _load_existing_metadata() -> dict[str, Any]:
        try:
            if metadata_path.exists():
                return json.loads(metadata_path.read_text())
        except json.JSONDecodeError:  # pragma: no cover - exercised via invalid test fixture
            return {}
        return {}

    def _normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
        r"""Normalize to {"<year>": {"DD": {...}}} preserving other years if present."""
        year_key = str(year)

        def _coerce_entry(value: dict[str, Any]) -> dict[str, Any]:
            part1_status = value.get("part1_status")
            part2_status = value.get("part2_status")
            if not isinstance(part1_status, bool):
                part1_status = _status_to_bool(part1_status)
            if not isinstance(part2_status, bool):
                part2_status = _status_to_bool(part2_status)
            return {
                "title": value.get("title"),
                "part1_status": part1_status,
                "part1_time_ms": value.get("part1_time_ms"),
                "part2_status": part2_status,
                "part2_time_ms": value.get("part2_time_ms"),
            }

        # Already keyed by year
        if isinstance(raw, dict) and year_key in raw:
            maybe_days = raw.get(year_key)
            if isinstance(maybe_days, dict):
                coerced = {
                    k: _coerce_entry(v) for k, v in maybe_days.items() if isinstance(v, dict)
                }
                raw[year_key] = coerced
                return raw

        # Legacy {\"year\": <y>, \"days\": {...}}
        if isinstance(raw, dict) and "days" in raw and isinstance(raw["days"], dict):
            coerced = {k: _coerce_entry(v) for k, v in raw["days"].items() if isinstance(v, dict)}
            return {year_key: coerced}

        # Legacy direct day keys
        days: dict[str, Any] = {}
        if isinstance(raw, dict):
            for key, value in raw.items():
                if not isinstance(value, dict):
                    continue
                day_key = key if len(str(key)) == 2 else f"{int(key):02d}"
                days[day_key] = _coerce_entry(value)
        return {year_key: days}

    metadata = _normalize_metadata(_load_existing_metadata())

    year_key = str(year)
    metadata.setdefault(year_key, {})

    day_key = f"{day:02d}"
    year_entries = metadata[year_key]
    entry = dict(year_entries.get(day_key) or {})
    entry.update(
        {
            "title": title,
            "part1_status": entry.get("part1_status"),
            "part1_time_ms": entry.get("part1_time_ms"),
            "part2_status": entry.get("part2_status"),
            "part2_time_ms": entry.get("part2_time_ms"),
        }
    )

    if part_status.get(1) is not None:
        entry["part1_status"] = _status_to_bool(part_status[1])
        part1_duration = part_timings.get(1)
        entry["part1_time_ms"] = None if part1_duration is None else round(part1_duration * 1000, 3)
    if part_status.get(2) is not None:
        entry["part2_status"] = _status_to_bool(part_status[2])
        part2_duration = part_timings.get(2)
        entry["part2_time_ms"] = None if part2_duration is None else round(part2_duration * 1000, 3)

    year_entries[day_key] = entry
    metadata[year_key] = year_entries
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))


def _resolve_title(paths, year: int, day: int, solution: Any) -> str:  # pragma: no cover
    """Resolve the puzzle title preferring article, then metadata, then solution."""
    article_path = paths.article_path(year, day)
    if article_path.exists():
        first_nonempty: str | None = None
        with article_path.open("r") as file:
            for line in file:
                header = line.strip()
                if not header:
                    continue
                header = header.lstrip("#").strip()
                header = header.strip("- ").strip()
                if first_nonempty is None:
                    first_nonempty = header.replace("---", "").strip("- ").strip()
                if ":" in header:
                    _, remainder = header.split(":", 1)
                    cleaned = remainder.replace("---", "").strip("- ").strip()
                    if cleaned:
                        return cleaned
        if first_nonempty:
            return first_nonempty

    metadata_path = paths.metadata_path(year)
    if metadata_path.exists():
        try:
            raw = json.loads(metadata_path.read_text())
            day_key = f"{day:02d}"
            year_entry = raw.get(str(year), {})
            if isinstance(year_entry, dict):
                day_entry = year_entry.get(day_key, {})
                title = day_entry.get("title")
                if title:
                    return str(title)
            legacy_day_entry = raw.get(day_key, {})
            if isinstance(legacy_day_entry, dict):
                title = legacy_day_entry.get("title")
                if title:
                    return str(title)
        except Exception:
            pass

    sol_doc = getattr(solution, "__doc__", None)
    if sol_doc:
        for raw_line in sol_doc.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if ":" in line:
                prefix, remainder = line.split(":", 1)
                if str(day) in prefix and str(year) in prefix:
                    cleaned = remainder.replace("---", "").strip("- ").strip(". ").strip()
                    if cleaned:
                        return cleaned
                cleaned = remainder.strip()
                if prefix.lower().startswith("day") and cleaned:
                    return cleaned
            if line.lower().startswith("solution for advent of code") and ":" in line:
                _, remainder = line.split(":", 1)
                cleaned = remainder.replace("---", "").strip("- ").strip(". ").strip()
                if cleaned:
                    return cleaned

    meta_title = getattr(solution, "_title", None)
    if meta_title:
        return str(meta_title)

    return f"Day {day:02d}"


@verify_app.command("answers")
def verify_answers(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    part: Optional[int] = typer.Option(
        None,
        "--part",
        min=1,
        max=2,
        help="Part to verify (1 or 2). If omitted, verifies both.",
    ),
    timing: bool = typer.Option(
        True,
        "--timing/--no-timing",
        help="Display timing and record durations in metadata.",
    ),
    metadata: bool = typer.Option(
        True,
        "--metadata/--no-metadata",
        help="Write verification status/timing metadata.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be verified without executing solution code.",
    ),
) -> None:
    """Compare cached answers with the local solution outputs and record metadata."""
    paths = get_context().paths

    try:  # allow direct invocation without Typer converting options
        from typer.models import OptionInfo

        if isinstance(part, OptionInfo):
            part = part.default
    except Exception:  # pragma: no cover - defensive for non-Typer callers
        pass

    if dry_run:
        typer.echo(f"(dry-run) Would verify Year {year}, Day {day:02d}, part={part}")
        return

    from pysleigh.commands.solution import _load_expected_answers  # imported lazily for reuse

    expected_1, expected_2 = _load_expected_answers(paths, year, day)
    if expected_1 is None and expected_2 is None:
        typer.echo(f"No cached answers found for Year {year}, Day {day:02d}.")
        raise typer.Exit(code=1)

    solution = load_solution(year, day)

    title = _resolve_title(paths, year, day, solution)
    typer.echo(f"--- Year {year} Day {day:02d}: {title} ---")

    actual_1: str | None = None
    actual_2: str | None = None
    timing_1: float | None = None
    timing_2: float | None = None

    if part in (1, None):
        actual_1, timing_1 = _execute_with_timing(solution.solve_part_one)
    if part in (2, None):
        actual_2, timing_2 = _execute_with_timing(solution.solve_part_two)

    ok = True
    part_status: dict[int, str | None] = {1: None, 2: None}
    part_timings: dict[int, float | None] = {1: timing_1, 2: timing_2}

    def check(
        label: str,
        part_number: int,
        expected: str | None,
        actual: str | None,
        duration: float | None,
    ) -> None:
        nonlocal ok
        status: str
        timing_suffix = f" [{_format_ms(duration)}]" if timing else ""
        if expected is None:
            typer.echo(f"{label}: skipped (no cached answer).")
            status = "skipped"
        elif actual is None:
            typer.echo(f"{label}: missing actual output.")
            ok = False
            status = "missing"
        elif str(actual) == str(expected):
            typer.echo(f"{label}: OK ({actual}){timing_suffix}")
            status = "ok"
        else:
            typer.echo(
                f"{label}: MISMATCH (cached {expected!r} vs actual {actual!r}){timing_suffix}"
            )
            ok = False
            status = "mismatch"

        part_status[part_number] = status

    if part in (1, None):
        check("Part One", 1, expected_1, actual_1, timing_1)
    if part in (2, None):
        check("Part Two", 2, expected_2, actual_2, timing_2)

    if metadata:
        _write_metadata_record(
            year=year,
            day=day,
            title=title,
            part_status=part_status,
            part_timings=part_timings,
        )

    if not ok:
        raise typer.Exit(code=1)
