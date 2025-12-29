# Agent Guide for dataform_view_migrator

This repository uses uv for dependency management and targets Python 3.10+.
The goal: export all BigQuery view SQL definitions and write them into a
Dataform project at a provided path, with predictable layout and safe writes.

## Expectations for the Agent
- Respect `dataform_view_migrator.toml` if present. CLI flags should override
  config values at runtime.
- Keep changes focused and minimal. Prefer small, composable functions.
- Use type hints throughout. Prefer explicit imports over `from x import *`.
- Handle errors clearly (auth issues, missing datasets, permissions, write
  conflicts) and return actionable messages.
- Default behavior should be safe: do not overwrite files unless configured.

## Project Conventions
- Package layout: `src/dataform_view_migrator/`
- CLI entry: `dataform-view-migrator` (also runnable via `python -m package`)
- Dependencies: `google-cloud-bigquery`, `polars`, `typer`
- Runtime auth: Application Default Credentials (ADC) by default.
- Configuration: TOML file at repo root `dataform_view_migrator.toml`

## CLI
- `migrate-views`: Discover BigQuery VIEWs and emit files under Dataform path.
  - Flags (override config):
    - `--source-project <id>`
    - `--datasets <a,b,c>` / `--exclude-datasets <x,y>`
    - `--location <region>` (e.g., `US`, `EU`)
    - `--dest <path>` (Dataform repo path)
    - `--ext <sql|sqlx>` (default: `sqlx`)
    - `--overwrite <skip|backup|force>` (default: `skip`)
    - `--add-dataform-header` (default based on config)
    - `--dry-run`
 - `ping-bq`: Verify ADC/auth and project resolution.

## File Layout in Dataform (defaults)
- `dest/<dataset>/<view_name>.sqlx`
- Optional header (if enabled) for Dataform:
  ```
  config { type: "view" }
  ```
  Additional header fields (e.g., schema) are controlled by config.

## Implementation Outline
- Discovery: list datasets → list tables (type VIEW) → fetch `view.query`.
- Transform: optionally add Dataform header; no refactoring of SQL by default.
- Write: create directories; honor overwrite policy; allow backup strategy.
- Report: produce a summary (Polars DataFrame) of created/updated/skipped.

## Testing and Validation
- Prefer small unit tests around discovery and write policy logic.
- For live BigQuery calls, keep an opt-in smoke test or use mocks.
- Avoid adding unrelated tooling unless requested (e.g., ruff/mypy/pytest).

## Style Notes
- Keep functions ≤ ~50 lines where practical.
- Avoid one-letter variable names. Use descriptive names.
- Do not introduce new top-level tools without request.

## Approvals & Batching
- Treat user-provided blanket approval as permission to batch related multi-file edits into a single patch, rather than requesting per-file approvals.
- Prefer one patch per feature/refactor to minimize approval prompts and keep history clean.
- Do not perform destructive actions (e.g., mass deletions, resets) outside the explicit scope of a task, even with blanket approval.
- This file cannot change sandbox or approval policy; it documents expected agent behavior. Follow the current session’s sandbox/approval settings.
