# Development

This document covers development setup, tooling, and project structure.

## Prerequisites
- Python 3.10+
- `uv` installed: https://docs.astral.sh/uv/

## Environment

- Create/sync environment (auto-creates venv if needed):
  - `uv sync`
- Run the CLI locally:
  - `uv run dataform-view-migrator --help`
  - `uv run python -m dataform_view_migrator -- --help`

## Linting & Formatting (Ruff)
- Install dev tools (if using optional dev group):
  - `uv sync --group dev`
- Lint:
  - `uv run ruff check .`
- Autofix (safe fixes):
  - `uv run ruff check . --fix`
- Format:
  - `uv run ruff format .`

## Tests
- Run tests:
  - `uv run pytest -q`
- Prefer small unit tests for discovery, write policy, and config behavior.
- For BigQuery calls, use mocks or explicit opt-in smoke tests.

## Project Layout
- `pyproject.toml` — project metadata, dependencies, console script
- `src/dataform_view_migrator/` — package source
  - `cli.py` — Typer app and commands
  - `config.py` — TOML loading and CLI override logic
  - `bq.py` — BigQuery discovery helpers
  - `migrate.py` — transformation and write policies
  - `__main__.py` — `python -m` entrypoint
  - `__init__.py` — version
- `dataform_view_migrator.example.toml` — sample configuration
- `DESIGN.md` — design notes

## Conventions
- Type hints throughout; avoid wildcard imports.
- Keep functions small and composable (≈≤50 lines when practical).
- Handle errors clearly with actionable messages.
- Default to safe writes; do not overwrite unless configured (`overwrite` policy).

