from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import typer
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery

from . import __version__
from .config import load_config, read_config_value
from .migrate import migrate, results_dataframe, summarize

app = typer.Typer(add_completion=False, help=(
    "Export BigQuery view SQL to a Dataform project folder.\n\n"
    "Use 'ping-bq' to verify auth; 'migrate-views' to perform export."
))


def _version_callback(value: bool) -> None:
    """Print the package version and exit if requested.

    Parameters
    ----------
    value: bool
        When True, prints the version and exits immediately.
    """
    if value:
        typer.echo(__version__)
        raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Show brief usage when no subcommand is provided.

    Prints a short quickstart with common commands and displays the
    current package version. Subcommands still run normally.
    """
    if ctx.invoked_subcommand is not None:
        return

    usage = f"""
Dataform View Migrator v{__version__}

Usage:
  dataform-view-migrator --version
  dataform-view-migrator ping-bq [--project <id>] [--config dataform_view_migrator.toml]
  dataform-view-migrator migrate-views [options]

Notes:
  - Options fall back to dataform_view_migrator.toml when omitted.
  - Use --help on any command for full details.

Examples:
  dataform-view-migrator ping-bq --project my-proj
  dataform-view-migrator migrate-views --config dataform_view_migrator.toml --dry-run
""".rstrip()
    typer.echo(usage)


@app.command("ping-bq")
def ping_bq(
    project: str | None = typer.Option(
        None,
        "--project",
        help="Project to use (overrides config and environment defaults)",
    ),
    location: str | None = typer.Option(
        None,
        "--location",
        help="BigQuery region to verify (e.g., US, EU). Overrides config.",
    ),
    config: str | None = typer.Option(
        "dataform_view_migrator.toml",
        help="Path to TOML config to read default project/location",
    ),
) -> None:
    """Create a BigQuery client, verify access, and print the project.

    Project resolution order:
    1) --project flag (if provided)
    2) source_project in TOML (if --config points to a file with it)
    3) ADC/environment defaults
    """
    try:
        resolved = project
        loc = location
        if config and Path(config).exists():
            proj_from_file = read_config_value(Path(config), "source_project")
            if resolved is None and proj_from_file:
                resolved = str(proj_from_file)
            if loc is None:
                loc_from_file = read_config_value(Path(config), "location")
                if loc_from_file:
                    loc = str(loc_from_file)

        client = bigquery.Client(project=resolved) if resolved else bigquery.Client()

        # If a location is provided (flag or config), verify via INFORMATION_SCHEMA in that region
        if loc:
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            query = f"SELECT 1 FROM `region-{loc}`.INFORMATION_SCHEMA.SCHEMATA LIMIT 1"
            _ = client.query(query, job_config=job_config, location=loc)
            typer.echo(f"BigQuery project: {client.project}")
        else:
            # Otherwise verify via dataset listing (API discovery path)
            ds_iter = client.list_datasets(project=client.project, max_results=1)
            for _ in ds_iter.pages:
                break
            typer.echo(f"BigQuery project: {client.project}")
    except GoogleAPIError as exc:
        typer.echo(f"BigQuery client error: {exc}")
        raise typer.Exit(code=1) from exc
    raise typer.Exit(code=0)


@app.command("migrate-views")
def migrate_views(
    source_project: str | None = typer.Option(
        None,
        help="GCP project hosting the views (falls back to config)",
    ),
    dest: str | None = typer.Option(
        None,
        help="Destination Dataform project path (falls back to config)",
    ),
    datasets: str | None = typer.Option(
        None,
        help="Comma-separated dataset list to include",
    ),
    exclude_datasets: str | None = typer.Option(
        None,
        help="Comma-separated dataset list to exclude",
    ),
    location: str | None = typer.Option(None, help="BigQuery location, e.g., US or EU (falls back to config)"),
    ext: str | None = typer.Option(
        None,
        help="Output extension: sqlx or sql (falls back to config)",
    ),
    overwrite: str | None = typer.Option(
        None,
        help="Write policy: skip | backup | force (falls back to config)",
    ),
    add_dataform_header: bool | None = typer.Option(
        None,
        "--add-dataform-header/--no-add-dataform-header",
        help="Prepend a Dataform config header to each file (falls back to config)",
    ),
    dry_run: bool | None = typer.Option(
        None,
        "--dry-run/--no-dry-run",
        help="Show actions without writing files (falls back to config)",
    ),
    config: str | None = typer.Option(
        "dataform_view_migrator.toml",
        help="Path to TOML config (flags override values)",
    ),
) -> None:
    """Discover BigQuery VIEWs and write SQL files under the Dataform path.

    Reads defaults from TOML, applies CLI overrides, migrates views via
    INFORMATION_SCHEMA when a location is provided, or via the table API
    otherwise. Prints a summary and returns a non-zero exit code if any
    per-view failures occur.
    """
    # Parse lists
    def _split_csv(s: str | None) -> list[str] | None:
        """Split a comma-separated string into a list, or None for empty input."""
        if not s:
            return None
        vals = [v.strip() for v in s.split(",")]
        return [v for v in vals if v]

    include = _split_csv(datasets)
    exclude = _split_csv(exclude_datasets)

    cfg_path = Path(config) if config else None
    try:
        cfg = load_config(
            cfg_path,
            overrides={
                "source_project": source_project,
                "dest": dest,
                "datasets_include": include,
                "datasets_exclude": exclude,
                "location": location,
                "ext": ext,
                "overwrite": overwrite,
                "add_dataform_header": add_dataform_header,
                "dry_run": dry_run,
            },
        )
    except Exception as exc:
        typer.echo(f"Invalid configuration: {exc}")
        raise typer.Exit(code=2) from exc

    try:
        effective_dry_run = cfg.dry_run if dry_run is None else dry_run
        results = migrate(cfg, dry_run=effective_dry_run)
    except Exception as exc:
        typer.echo(f"Migration failed: {exc}")
        raise typer.Exit(code=1) from exc

    # Print full results DataFrame with wider path column, then a compact summary
    pl.Config.set_tbl_rows(-1)
    pl.Config.set_tbl_width_chars(300)
    if hasattr(pl.Config, "set_fmt_str_lengths"):
        pl.Config.set_fmt_str_lengths(200)  # avoid truncating long paths
    df = results_dataframe(results)
    typer.echo("Results:")
    typer.echo(df)
    typer.echo("")
    typer.echo(summarize(results))

    failed = any(r.action == "failed" for r in results)
    if failed:
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


if __name__ == "__main__":  # pragma: no cover
    # Allow `python -m dataform_view_migrator.cli`
    sys.exit(app())
