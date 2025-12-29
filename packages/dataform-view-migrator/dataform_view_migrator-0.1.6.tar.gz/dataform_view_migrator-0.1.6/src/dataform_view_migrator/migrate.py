from __future__ import annotations

import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from google.cloud import bigquery

from .bq import discover_views, fetch_view_query, views_from_information_schema
from .config import Config

SANITIZE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _sanitize(name: str) -> str:
    """Return a filesystem-safe name by replacing unsafe characters."""
    return SANITIZE_RE.sub("_", name).strip("._") or "unnamed"


def _dataset_folder(dataset_id: str, cfg: Config) -> Path:
    """Map a dataset ID to its output subfolder, honoring config overrides."""
    if cfg.dataset_folders and dataset_id in cfg.dataset_folders:
        return Path(cfg.dataset_folders[dataset_id])
    return Path(dataset_id)


def _header(cfg: Config, dataset_id: str, view_id: str) -> str:
    """Return a Dataform header for this dataset/view when enabled.

    When enabled, emits a Dataform config block. The description and tags are
    included only if provided by configuration (no implicit defaults).
    """
    if not cfg.add_dataform_header:
        return ""
    def _escape(val: str) -> str:
        """Escape double quotes and backslashes for inclusion in header values."""
        return val.replace("\\", "\\\\").replace('"', '\\"')

    desc_raw = cfg.header_description
    desc = _escape(desc_raw.strip()) if desc_raw else ""

    lines = [
        "config {",
        '  type: "view",',
        f'  schema: "{_escape(dataset_id)}",',
        f'  name: "{_escape(view_id)}",',
    ]
    if desc:
        lines.append(f'  description: "{desc}",')

    if cfg.header_tags:
        tags_literal = ", ".join([f'"{_escape(t)}"' for t in cfg.header_tags])
        lines.append(f"  tags: [{tags_literal}]")
    lines.append("}")
    return "\n".join(lines) + "\n\n"


def _ensure_dir(path: Path) -> None:
    """Create directory tree for ``path`` if it does not exist."""
    os.makedirs(path, exist_ok=True)


def _backup_path(path: Path) -> Path:
    """Return a non-conflicting backup path for ``path`` (e.g., .bak, .bak.N)."""
    base = Path(str(path) + ".bak")
    if not base.exists():
        return base
    i = 1
    while True:
        candidate = Path(str(path) + f".bak.{i}")
        if not candidate.exists():
            return candidate
        i += 1


@dataclass
class Result:
    """Outcome of migrating a single view into a file."""
    dataset: str
    view: str
    path: Path
    action: str  # created | updated | skipped | failed | would-create | would-update | would-skip
    error: str | None = None


def migrate(cfg: Config, dry_run: bool = False) -> list[Result]:
    """Migrate BigQuery views to files under the configured destination.

    Uses INFORMATION_SCHEMA when a location is provided; otherwise falls back
    to the table API. Honors overwrite policy and supports dry-run.
    """
    results: list[Result] = []
    client = bigquery.Client(project=cfg.source_project)

    include = cfg.datasets_include or []
    exclude = cfg.datasets_exclude or []

    # Prefer INFORMATION_SCHEMA for efficiency when location is provided
    if cfg.location:
        triples = views_from_information_schema(cfg.source_project, cfg.location, include, exclude)
        iterable = ((ds, view, sql) for ds, view, sql in triples)
    else:
        # Fall back to API discovery and per-view fetch
        iterable = (
            (ds, view, fetch_view_query(client, f"{cfg.source_project}.{ds}.{view}"))
            for ds, view in discover_views(cfg.source_project, include, exclude, cfg.location)
        )

    for dataset_id, view_id, sql in iterable:
        safe_ds = _sanitize(dataset_id)
        safe_view = _sanitize(view_id)
        rel_dir = _dataset_folder(safe_ds, cfg)
        out_dir = (cfg.dest / rel_dir).resolve()
        out_path = out_dir / f"{safe_view}.{cfg.ext}"

        action: str
        try:
            # Compose content
            content = (_header(cfg, dataset_id, view_id) + sql).rstrip() + "\n"

            if dry_run:
                if out_path.exists():
                    action = "would-update" if cfg.overwrite in {"backup", "force"} else "would-skip"
                else:
                    action = "would-create"
                results.append(Result(dataset_id, view_id, out_path, action))
                continue

            _ensure_dir(out_dir)
            if out_path.exists():
                if cfg.overwrite == "skip":
                    action = "skipped"
                elif cfg.overwrite == "backup":
                    bak = _backup_path(out_path)
                    out_path.replace(bak)
                    out_path.write_text(content, encoding="utf-8")
                    action = "updated"
                elif cfg.overwrite == "force":
                    out_path.write_text(content, encoding="utf-8")
                    action = "updated"
                else:
                    action = "skipped"
            else:
                out_path.write_text(content, encoding="utf-8")
                action = "created"

            results.append(Result(dataset_id, view_id, out_path, action))
        except Exception as exc:  # capture per-view failures
            results.append(Result(dataset_id, view_id, out_path if 'out_path' in locals() else Path(""),
                                  "failed", str(exc)))

    return results


def summarize(results: Sequence[Result]) -> str:
    """Return a compact tabular summary of actions grouped by type."""
    df = results_dataframe(results)
    totals = df.group_by("action").len().sort("action")
    return f"Actions by type:\n{totals}"


def results_dataframe(results: Sequence[Result]) -> pl.DataFrame:
    """Build a Polars DataFrame listing per-view migration results.

    Columns: dataset, view, action, path, error.
    """
    rows = [
        {
            "dataset": r.dataset,
            "view": r.view,
            "action": r.action,
            "path": str(r.path),
            "error": r.error or "",
        }
        for r in results
    ]
    return pl.DataFrame(rows)
