# PySleigh

`pysleigh` is a Typer-driven CLI assistant for Advent of Code. It keeps all IO, scaffolding, runs, and submissions beside your solutions and gives you dry-run previews before any change lands on disk or on the AoC website.

## How the CLI behaves
- Every command runs in a clear scope: you point it at a project root and a year/day, then ask it to fetch input, fetch the article, run or test a solution, submit an answer, or scaffold files.
- Actions follow the “scope → action → artifact” pattern: they operate on one concern, do a single thing, and report the created or updated artifact (inputs, articles, answers, solution templates).
- Dry-run flags (`--dry-run`) appear on each command so you can observe what would change without touching your repo or the Advent of Code site.
- Helper modules (`paths`, `context`, `loader`, `session`) stay outside the CLI decorators so the commands remain declarative and easier to script or test.

## Key commands
- `pysleigh data fetch-input <year> <day>` downloads the day’s input (supports `--overwrite`, `--dry-run`).
- `pysleigh data fetch-article <year> <day>` saves the article HTML plus a title line so scaffolding knows the correct header.
- `pysleigh data refresh-answers <year> <day>` reruns your solution, rewrites `answers/year_{n}/answer_{n}_day_{d}.txt`, or dry-runs the write.
- `pysleigh solution run|test|submit` executes, validates, or submits your solution; they log each step, honor dry-run, and explain success/failure details.
- `pysleigh solution scaffold <year> <day>` bootstraps a template under `solutions/year_{n}/solution_{n}_day_{d}.py` using the guessed title. `pysleigh solution prepare` batches input/article fetch plus scaffold with optional overwrites.
- `pysleigh verify answers <year> <day>` checks your outputs against cached answers (optional `--part`), prints timings, and records status/timing metadata in `answers/year_{n}/metadata_year_{n}.json` (toggle with `--metadata/--no-metadata`). Metadata is grouped as `{ "<year>": { "DD": {...} } }` with boolean statuses and timings in milliseconds to keep merges sane.
- `pysleigh version` prints the installed PySleigh version (read dynamically from package metadata or your local `pyproject.toml` when running editable installs).

## Installation & invocation
- Install straight from PyPI (`pip install pysleigh`) or, for hacking on the CLI, use `pip install -e .`.
- Run `pysleigh` directly once it’s on your PATH, or wrap it in `uv` (`uv run pysleigh -- solution run 2023 1`) to isolate dependencies and leverage tooling helpers.
- Use `--project-root /path/to/advent-of-code-python` (or `PYSLEIGH_PROJECT_ROOT=/path`) when invoking the CLI from outside your AoC repo so the built-in `PathConfig` can resolve inputs, answers, and article directories. The CLI will echo when it switches project roots for a subcommand so you can confirm which tree it is mutating.

## Configuration
- `PathConfig` expects the usual layout (`inputs/year_{n}/input_{n}_day_{d}.txt`, `articles/year_{n}/article_{n}_day_{d}.md`, `answers/year_{n}/answer_{n}_day_{d}.txt`, `solutions/year_{n}/solution_{n}_day_{d}.py`). Commands will create missing parent directories automatically.
- Set `SESSION_TOKEN` before running networked commands:
  ```bash
  export SESSION_TOKEN="$(security find-generic-password -s adventofcode -w)"
  ```
  Any secure credential store (`security`, `pass`, `keyring`, etc.) works; combine it with `direnv`, `dotenv`, or `uv` secrets so the token never appears in source control. PySleigh reports a clear error if the variable is missing or empty.
- Dry-run flags on every command let you confirm submit candidates, file writes, and fetches before touching the file system or AoC.

## Development & testing
- `pytest --cov=src --cov-report=term-missing` runs the suite; tests mirror the CLI modules so behavior stays aligned with production commands.
- Lint via `ruff check .` and type-check with `ty check` (configured in `pyproject.toml`), keeping 100-char lines and Python 3.12 typing idioms.
- Mutation testing via `mutmut run` is recommended after behavior changes—the existing suite already kills every mutant in commands/loaders/session helpers.
