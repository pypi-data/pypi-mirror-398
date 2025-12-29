# Design

Concise architecture and code structure for the Dataform View Migrator.

## Goals / Non‑Goals
- Goals: export BigQuery VIEW SQL to a Dataform repo with predictable layout, safe write policies, and clear reporting; flags override config.
- Non‑goals: SQL rewriting (e.g., `ref()`), Dataform compilation, table migration, schema management, complex formatting.

## Module Map
- `src/dataform_view_migrator/cli.py`: Typer CLI entry.
  - Commands: `ping-bq`, `migrate-views`; prints quickstart when run without subcommand.
  - Loads config via `load_config`; applies flag overrides; formats Polars results; sets exit codes.
- `src/dataform_view_migrator/config.py`: configuration layer.
  - `Config` dataclass (source_project, dest, filters, location, ext, overwrite, header options, dry_run, dataset_folders).
  - `load_config(path, overrides)`: TOML parse + precedence + validation.
  - `read_config_value(path, key)`: dot-key lookup for selective reads.
- `src/dataform_view_migrator/bq.py`: BigQuery access.
  - `discover_views(project, include, exclude, location)`: list datasets/tables; filter `VIEW`.
  - `fetch_view_query(client, table_ref)`: return view SQL (with property fallback).
  - `views_from_information_schema(project, location, include, exclude)`: regional INFORMATION_SCHEMA query.
- `src/dataform_view_migrator/migrate.py`: migration engine.
  - Write policy helpers: `_sanitize`, `_dataset_folder`, `_ensure_dir`, `_backup_path`.
  - Header helper: `_header(cfg, dataset_id, view_id)`.
  - Types: `Result(dataset, view, path, action, error)`.
  - Orchestration: `migrate(cfg, dry_run=False)`, `results_dataframe`, `summarize`.

## Data Flow
- `ping-bq`
  - Resolve project from flags → TOML → ADC; if `--location`, run regional INFORMATION_SCHEMA dry-run; else list a dataset page; print project.
- `migrate-views`
  1) Load `Config` (flags override TOML). 2) Pick discovery path: INFORMATION_SCHEMA when `location` set; else API listing. 3) For each view: fetch SQL, build optional header, decide action per overwrite policy, write or simulate (dry-run). 4) Collect `Result`s; print table and grouped summary; exit non‑zero if any failures.

## Key Policies
- Overwrite: `skip` (default, no changes), `backup` (rename existing to `.bak[.N]`, then write), `force` (overwrite in place).
- Dry-run: never write; actions reported as `would-create`/`would-update`/`would-skip`.
- Layout: `dest/<dataset>/<view>.<ext>`; `ext` default `sqlx`.
- Dataset folders: optional mapping via `dataset_folders` in TOML.
- Header: optional Dataform `config { type: "view" }` with schema/name; optional description/tags.
- Precedence: explicit flags → TOML → environment/ADC.

## Error Handling
- BigQuery errors surfaced with actionable messages (auth/project/perm); CLI returns non‑zero on failure.
- Per‑view exceptions recorded in `Result.error`; run continues and summary highlights failures.
- Filesystem: include paths in messages; never clobber unless `backup` or `force`.

## Extension Points
- Header: add fields or templates without changing defaults.
- SQL: optional formatting or transforms can be introduced behind flags.
- Output: support alternative layouts or naming strategies via config.

## Testing Notes
- Unit test: config precedence/validation, header rendering, overwrite policy decisions, sanitization and folder mapping.
- BigQuery: mock clients for discovery and view SQL; reserve smoke tests for opt‑in runs.
