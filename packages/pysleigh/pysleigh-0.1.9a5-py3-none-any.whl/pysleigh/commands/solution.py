"""Typer commands for running, testing, and submitting solutions."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests
import typer

from pysleigh.commands import data as data_commands
from pysleigh.context import get_context
from pysleigh.loader import load_solution
from pysleigh.paths import PathConfig
from pysleigh.session import get_session_token

solution_app = typer.Typer(help="Work with solutions (run, test, submit, scaffold).")


def _load_expected_answers(paths: PathConfig, year: int, day: int) -> tuple[str | None, str | None]:
    """Return stored answers for the requested day, if available."""
    path = paths.answer_path(year, day)
    if not path.exists():
        typer.echo(f"[solution/test] No answers file found at {path}")
        return None, None

    lines = path.read_text().splitlines()
    part_1 = lines[0].strip() if len(lines) >= 1 and lines[0].strip() else None
    part_2 = lines[1].strip() if len(lines) >= 2 and lines[1].strip() else None
    return part_1, part_2


def _write_answer_to_file(
    paths: PathConfig, year: int, day: int, part: int, answer: str, dry_run: bool
) -> None:
    """Update the answers file for the specified part, respecting dry runs."""
    path = paths.answer_path(year, day)
    existing_1: str | None = None
    existing_2: str | None = None

    if path.exists():
        lines = path.read_text().splitlines()
        if len(lines) >= 1 and lines[0].strip():
            existing_1 = lines[0].strip()
        if len(lines) >= 2 and lines[1].strip():
            existing_2 = lines[1].strip()

    missing_part_one = existing_1 is None
    missing_part_two = existing_2 is None

    if part == 1:
        existing_1 = answer
    elif part == 2:
        existing_2 = answer

    line1 = existing_1 or ""
    line2 = existing_2 or ""

    if dry_run:
        typer.echo(
            f"[solution/submit] (dry-run) Would update answers file {path} with:\n"
            f"  Part 1: {line1!r}\n"
            f"  Part 2: {line2!r}"
        )
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{line1}\n{line2}\n")
    if part == 2 and missing_part_one:
        typer.echo("[solution/submit] Recorded part 2 without existing part 1.")
    if part == 1 and missing_part_two:
        typer.echo("[solution/submit] Part 2 is still unset; future submissions can fill it in.")
    typer.echo(f"[solution/submit] Updated answers file: {path}")


@solution_app.command("run")
def run_solution(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    part: Optional[int] = typer.Option(
        None,
        "--part",
        min=1,
        max=2,
        help="Part to run (1 or 2). If omitted, runs both.",
    ),
    timing: bool = typer.Option(
        False,
        "--timing/--no-timing",
        help="Print timing information.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be run without actually executing solution code.",
    ),
) -> None:
    """Run a solution for the requested day and optionally display timing."""
    if dry_run:
        typer.echo(
            f"[solution/run] (dry-run) Would run solution for Year {year}, Day {day:02d}, "
            f"part={part}, timing={timing}"
        )
        return

    solution = load_solution(year, day)
    solution.run(part=part, output=True, timing=timing)


@solution_app.command("test")
def test_solution(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    part: Optional[int] = typer.Option(
        None,
        "--part",
        min=1,
        max=2,
        help="Part to test (1 or 2). If omitted, tests both.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be tested without executing solution code.",
    ),
) -> None:
    """Compare a solution's answers against the stored values."""
    paths = get_context().paths
    if dry_run:
        typer.echo(f"[solution/test] (dry-run) Would test Year {year}, Day {day:02d}, part={part}")
        return

    expected_1, expected_2 = _load_expected_answers(paths, year, day)
    solution = load_solution(year, day)
    actual_1, actual_2 = solution.run(output=False)

    ok = True

    def check(label: str, expected: str | None, actual: str | None) -> None:
        nonlocal ok
        if expected is None:
            typer.echo(f"[solution/test] {label}: no expected answer stored, skipping.")
            return
        if actual is None:
            typer.echo(f"[solution/test] {label}: no actual answer produced.")
            ok = False
            return
        if str(actual) == str(expected):
            typer.echo(f"[solution/test] {label}: OK ({actual})")
        else:
            typer.echo(f"[solution/test] {label}: FAIL (expected {expected!r}, got {actual!r})")
            ok = False

    if part in (1, None):
        check("Part 1", expected_1, actual_1)
    if part in (2, None):
        check("Part 2", expected_2, actual_2)

    if not ok:
        raise typer.Exit(code=1)


@solution_app.command("submit")
def submit_solution(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    part: int = typer.Option(
        ...,
        "--part",
        min=1,
        max=2,
        help="Part to submit (1 or 2).",
    ),
    answer: Optional[str] = typer.Option(
        None,
        "--answer",
        help="Answer to submit. If omitted, compute from local solution.",
    ),
    refresh_article: bool = typer.Option(
        True,
        "--refresh-article/--no-refresh-article",
        help="Refetch article after a correct submission.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be submitted without sending anything.",
    ),
) -> None:
    """Submit an answer to Advent of Code and update local artifacts."""
    paths = get_context().paths
    computed_answer: Optional[str] = answer

    if computed_answer is None:
        solution = load_solution(year, day)
        part_1, part_2 = solution.run(output=False)
        computed_answer = part_1 if part == 1 else part_2
        if computed_answer is None:
            typer.echo(
                f"[solution/submit] No answer available for part {part} to submit.", err=True
            )
            raise typer.Exit(code=1)
    computed_answer = str(computed_answer)

    url = f"https://adventofcode.com/{year}/day/{day}/answer"

    if dry_run:
        typer.echo(
            f"[solution/submit] (dry-run) Would submit answer={computed_answer!r} "
            f"for Year {year}, Day {day:02d}, Part {part} to {url}"
        )
        _write_answer_to_file(paths, year, day, part, computed_answer, dry_run=True)
        if refresh_article:
            path = paths.article_path(year, day)
            typer.echo(f"[solution/submit] (dry-run) Would refresh article file: {path}")
        return

    session = get_session_token()
    data = {"level": str(part), "answer": computed_answer}

    typer.echo(f"[solution/submit] Submitting answer for Year {year}, Day {day}, Part {part}")
    response = requests.post(url, cookies={"session": session}, data=data, timeout=10)
    response.raise_for_status()

    html = response.text
    is_correct = "That's the right answer" in html
    is_too_low = "Your answer is too low" in html
    is_too_high = "Your answer is too high" in html
    is_already_done = "Did you already complete it" in html or "already complete it" in html

    typer.echo("[solution/submit] Server response summary:")
    if is_correct:
        typer.echo("  ✅ That's the right answer!")
    elif is_too_low:
        typer.echo("  ❌ Your answer is too low.")
    elif is_too_high:
        typer.echo("  ❌ Your answer is too high.")
    elif is_already_done:
        typer.echo("  ℹ️  It looks like this part is already solved.")
    else:
        typer.echo("  ℹ️  Could not confidently parse result, check the website.")

    snippet = html.split("<article", 1)[-1] if "<article" in html else html
    snippet = snippet[:600]
    typer.echo("\n[solution/submit] Response snippet:")
    typer.echo(snippet)
    typer.echo("")

    if is_correct or is_already_done:
        _write_answer_to_file(paths, year, day, part, computed_answer, dry_run=False)

        if is_correct and refresh_article:
            from pysleigh.commands.data import fetch_article

            fetch_article(
                year=year,
                day=day,
                overwrite=True,
                dry_run=False,
            )


SCAFFOLD_TEMPLATE = '''"""Solution for Advent of Code {year}, Day {day:02d}: {title}."""

from __future__ import annotations

from typing import Any

from pysleigh.base import Base


Input = Any  # TODO: refine the parsed-input type for this day


class Solution(Base[Input]):
    """Solution for Advent of Code {year}, Day {day:02d}: {title}."""

    def parse_input(self) -> Input:
        """Parse the raw input data into a structured form."""
        data = self._raw_input
        # TODO: convert the raw input string into a structured value
        # NOTE: will be stored as self.data
        return data

    def solve_part_one(self) -> Any:
        """Compute the answer for part one."""
        # TODO: implement part one.
        raise NotImplementedError

    def solve_part_two(self) -> Any:
        """Compute the answer for part two."""
        # TODO: implement part two.
        raise NotImplementedError
'''


def _guess_solution_title(paths: PathConfig, year: int, day: int) -> str:
    """Return a best-effort title extracted from the article header."""
    article_path = paths.article_path(year, day)
    if not article_path.exists():
        return f"Day {day:02d}"

    first_line = article_path.read_text().splitlines()[0].strip()
    if ":" in first_line:
        _, rest = first_line.split(":", 1)
        title = rest.replace("---", "").strip()
        return title or f"Day {day:02d}"

    return first_line or f"Day {day:02d}"


def _scaffold_solution_file(
    paths: PathConfig, year: int, day: int, force: bool, dry_run: bool
) -> Path:
    """Create or report a solution template file for the requested day."""
    year_dir = paths.project_root / "solutions" / f"year_{year}"
    target = year_dir / f"solution_{year}_day_{day:02d}.py"

    if target.exists() and not force:
        typer.echo(
            "[solution/scaffold] Refusing to overwrite existing file: "
            f"{target}\nUse --force to overwrite.",
            err=True,
        )
        raise typer.Exit(code=1)

    if dry_run:
        typer.echo(
            f"[solution/scaffold] (dry-run) Would create template at {target} (force={force})"
        )
        return target

    year_dir.mkdir(parents=True, exist_ok=True)
    title = _guess_solution_title(paths, year, day)
    content = SCAFFOLD_TEMPLATE.format(year=year, day=day, title=title)
    target.write_text(content)
    typer.echo(f"[solution/scaffold] Created template: {target}")
    return target


@solution_app.command("scaffold")
def scaffold_solution(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    force: bool = typer.Option(
        False,
        "--force/--no-force",
        help="Overwrite existing solution file if it exists.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be created without writing the file.",
    ),
) -> None:
    """Create a solution template file for a given day."""
    paths = get_context().paths
    _scaffold_solution_file(paths, year, day, force=force, dry_run=dry_run)


@solution_app.command("prepare")
def prepare_solution(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    overwrite_input: bool = typer.Option(
        False,
        "--overwrite-input/--no-overwrite-input",
        help="Overwrite existing input file, if any.",
    ),
    overwrite_article: bool = typer.Option(
        False,
        "--overwrite-article/--no-overwrite-article",
        help="Overwrite existing article file, if any.",
    ),
    force_scaffold: bool = typer.Option(
        False,
        "--force-scaffold/--no-force-scaffold",
        help="Overwrite existing solution file, if any.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show all steps without performing network calls or writes.",
    ),
) -> None:
    """Prepare inputs, article, and solution template for a specific day."""
    paths = get_context().paths
    typer.echo(f"[solution/prepare] Preparing Year {year}, Day {day:02d}")

    data_commands.fetch_input(
        year=year,
        day=day,
        overwrite=overwrite_input,
        dry_run=dry_run,
    )

    data_commands.fetch_article(
        year=year,
        day=day,
        overwrite=overwrite_article,
        dry_run=dry_run,
    )

    _scaffold_solution_file(
        paths,
        year,
        day,
        force=force_scaffold,
        dry_run=dry_run,
    )
