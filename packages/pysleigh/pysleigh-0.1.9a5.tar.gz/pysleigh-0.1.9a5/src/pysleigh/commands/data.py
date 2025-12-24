"""Typer commands for fetching AoC data artifacts."""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path

import requests
import typer
from markdownify import markdownify

from pysleigh.context import get_context
from pysleigh.session import get_session_token

_ARTICLE_SECTION_RE = re.compile(r"<article\b[^>]*>.*?</article>", re.IGNORECASE | re.DOTALL)
_ANSWER_RE = re.compile(
    r"Your puzzle answer was\s*<code>(?P<answer>.*?)</code>", re.IGNORECASE | re.DOTALL
)

data_app = typer.Typer(help="Manage inputs, articles, and answers.")


def _resolve_article_title(html: str, day: int) -> str:
    start_tag = "<h2>"
    end_tag = "</h2>"
    start_idx = html.find(start_tag)
    end_idx = html.find(end_tag, start_idx + len(start_tag))
    if start_idx == -1 or end_idx == -1:
        return f"--- Day {day}: ??? ---"
    return html[start_idx + len(start_tag) : end_idx].strip()


def _extract_article_section(html: str) -> str:
    """Return every <article> block (joined) or the raw HTML if not found."""
    sections = [match.group(0) for match in _ARTICLE_SECTION_RE.finditer(html) if match.group(0)]
    if sections:
        return "\n\n".join(sections)
    start_idx = html.lower().find("<article")
    return html[start_idx:] if start_idx != -1 else html


def _markdownify_article(html: str) -> str:
    """Convert the provided HTML fragment into Markdown."""
    markdown = markdownify(html, heading_style="ATX")
    lines = (line.rstrip() for line in markdown.splitlines())
    return "\n".join(lines).strip()


def _ensure_parent(path: Path) -> None:
    """Ensure the target directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _extract_answers_from_html(html: str, day: int) -> tuple[str | None, str | None]:
    """Return part 1/2 answers found in the AoC article HTML."""
    answers = [unescape(match.group("answer")).strip() for match in _ANSWER_RE.finditer(html)]
    part_1 = answers[0] if answers else None
    part_2 = answers[1] if len(answers) > 1 else None

    if part_2 is None and day == 25:
        part_2 = "Merry Christmas!"

    return part_1, part_2


def _read_answer_file(path: Path) -> tuple[str | None, str | None]:
    """Read existing answers from disk."""
    if not path.exists():
        return None, None
    lines = path.read_text().splitlines()
    part_1 = lines[0].strip() if len(lines) >= 1 and lines[0].strip() else None
    part_2 = lines[1].strip() if len(lines) >= 2 and lines[1].strip() else None
    return part_1, part_2


def _merge_answers(
    existing: tuple[str | None, str | None],
    found: tuple[str | None, str | None],
    overwrite: bool,
) -> tuple[str | None, str | None]:
    """Combine existing answers with newly discovered ones."""
    existing_1, existing_2 = existing
    found_1, found_2 = found

    final_1 = existing_1
    final_2 = existing_2

    if overwrite or existing_1 is None:
        final_1 = found_1 if found_1 is not None else existing_1
    if overwrite or existing_2 is None:
        final_2 = found_2 if found_2 is not None else existing_2

    return final_1, final_2


@data_app.command("fetch-input")
def fetch_input(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite existing input file if it exists.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print what would be done, but do not fetch or write anything.",
    ),
) -> None:
    """Fetch the input text for a specific day from Advent of Code."""
    paths = get_context().paths
    url = f"https://adventofcode.com/{year}/day/{day}/input"
    path = paths.input_path(year, day)

    if dry_run:
        typer.echo(
            f"[data/input] (dry-run) Would fetch input from {url} "
            f"and write to {path} (overwrite={overwrite})"
        )
        return

    session = get_session_token()
    typer.echo(f"[data/input] Fetching input from {url}")
    response = requests.get(url, cookies={"session": session}, timeout=10)
    response.raise_for_status()

    if path.exists() and not overwrite:
        typer.echo(f"[data/input] Skipping existing file (use --overwrite to replace): {path}")
        raise typer.Exit(code=0)

    _ensure_parent(path)
    path.write_text(response.text)
    typer.echo(f"[data/input] Saved to {path}")


@data_app.command("fetch-article")
def fetch_article(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite existing article file if it exists.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print what would be done, but do not fetch or write anything.",
    ),
) -> None:
    """Fetch the article HTML for a specific day and store it locally."""
    paths = get_context().paths
    url = f"https://adventofcode.com/{year}/day/{day}"
    path = paths.article_path(year, day)

    if dry_run:
        typer.echo(
            f"[data/article] (dry-run) Would fetch article from {url} "
            f"and write to {path} (overwrite={overwrite})"
        )
        return

    session = get_session_token()
    typer.echo(f"[data/article] Fetching article from {url}")
    response = requests.get(url, cookies={"session": session}, timeout=10)
    response.raise_for_status()
    html = response.text
    article_section = _extract_article_section(html)
    title_source = article_section if "<h2" in article_section.lower() else html
    title_line = _resolve_article_title(title_source, day)
    markdown_body = _markdownify_article(article_section)
    if not markdown_body:
        markdown_body = _markdownify_article(html)
    if not markdown_body:
        markdown_body = "(Article content could not be extracted.)"

    if path.exists() and not overwrite:
        typer.echo(f"[data/article] Skipping existing file (use --overwrite): {path}")
        raise typer.Exit(code=0)

    _ensure_parent(path)
    content = f"{title_line}\n\n{markdown_body}\n"
    path.write_text(content)
    typer.echo(f"[data/article] Saved to {path}")


@data_app.command("refresh-answers")
def refresh_answers(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite existing answers file when refetching.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be fetched without performing network calls or writes.",
    ),
) -> None:
    """Refresh answers from the AoC site (aliases fetch-answer)."""
    try:  # allow direct invocation without Typer converting options
        from typer.models import OptionInfo

        if isinstance(overwrite, OptionInfo):
            overwrite = bool(overwrite.default)
    except Exception:  # pragma: no cover - defensive opt-in for Typer internals
        pass

    fetch_answer(year=year, day=day, overwrite=overwrite, dry_run=dry_run)


@data_app.command("fetch-answer")
def fetch_answer(
    year: int = typer.Argument(..., help="AoC year."),
    day: int = typer.Argument(..., help="AoC day."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite existing stored answers when new values are found.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be fetched and written without making network calls or writes.",
    ),
) -> None:
    """Fetch answers from the AoC page and persist them to the answers file."""
    paths = get_context().paths
    url = f"https://adventofcode.com/{year}/day/{day}"
    target = paths.answer_path(year, day)

    prefix = "[data/fetch-answer]"

    if dry_run:
        typer.echo(
            f"{prefix} (dry-run) Would fetch answers from {url} "
            f"and write to {target} (overwrite={overwrite})"
        )
        return

    session = get_session_token()
    typer.echo(f"{prefix} Fetching answers from {url}")
    response = requests.get(url, cookies={"session": session}, timeout=10)
    response.raise_for_status()

    part_1, part_2 = _extract_answers_from_html(response.text, day)
    if part_1 is None and part_2 is None:
        typer.echo(f"{prefix} No answers found on the page; nothing to write.")
        raise typer.Exit(code=1)

    existing = _read_answer_file(target)
    merged_1, merged_2 = _merge_answers(existing, (part_1, part_2), overwrite)

    _ensure_parent(target)
    line1 = merged_1 or ""
    line2 = merged_2 or ""
    target.write_text(f"{line1}\n{line2}\n")

    typer.echo(f"{prefix} Saved answers: Part 1={line1!r}, Part 2={line2!r} -> {target}")
