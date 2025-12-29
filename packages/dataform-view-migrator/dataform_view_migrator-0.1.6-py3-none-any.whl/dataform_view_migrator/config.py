from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# tomllib in 3.11+, tomli backport in 3.10
try:  # pragma: no cover - import guard
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - import guard
    import tomli as _toml  # type: ignore


@dataclass
class Config:
    """Runtime configuration for migrating BigQuery views to Dataform files.

    Attributes mirror CLI flags and TOML keys. Paths are stored as-is; the
    caller is responsible for resolving them.
    """
    source_project: str
    dest: Path
    datasets_include: list[str] | None = None
    datasets_exclude: list[str] | None = None
    location: str | None = None
    ext: str = "sqlx"
    overwrite: str = "skip"  # skip | backup | force
    add_dataform_header: bool = True
    header_description: str = ""
    header_tags: list[str] | None = None
    dry_run: bool = False
    dataset_folders: dict[str, str] | None = None


def _read_toml(path: Path) -> dict:
    """Read a TOML file from ``path`` and return a dictionary."""
    with path.open("rb") as f:
        return _toml.load(f)


def read_config_value(config_path: Path, key: str) -> Any:
    """Read a value from the TOML config by dot-delimited key.

    Examples
    - key="source_project"
    - key="location"
    - key="dataform_header.description"

    Raises
    ------
    FileNotFoundError
        When the config file does not exist.
    KeyError
        When the key path does not exist in the file.
    Any exception raised by TOML parsing is propagated.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    data = _read_toml(config_path)
    cur: Any = data
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"Missing config key: {key}")
        cur = cur[part]
    return cur


def load_config(config_path: Path | None, overrides: dict) -> Config:
    """Load configuration from TOML and apply CLI overrides.

    Parameters
    ----------
    config_path
        Optional path to a TOML file; ignored if None or missing.
    overrides
        Values supplied by the CLI, taking precedence over TOML content.

    Returns
    -------
    Config
        A validated configuration object with defaults applied.
    """
    data: dict = {}
    if config_path and config_path.exists():
        data = _read_toml(config_path)

    # Base values from file
    source_project = str(data.get("source_project", ""))
    dest = Path(data.get("dest", "")) if data.get("dest") else Path("")
    datasets_include = list(data.get("datasets_include", []) or []) or None
    datasets_exclude = list(data.get("datasets_exclude", []) or []) or None
    location = data.get("location") or None
    ext = str(data.get("ext", "sqlx"))
    overwrite = str(data.get("overwrite", "skip"))
    add_header = bool(data.get("add_dataform_header", False))
    header_description = str(
        data.get("dataform_header", {}).get("description", "")
    )
    header_tags_val = data.get("dataform_header", {}).get("tags")
    header_tags = list(header_tags_val) if header_tags_val else None
    dry_run_val = data.get("dry_run")
    dry_run = bool(dry_run_val) if dry_run_val is not None else False
    dataset_folders = dict(data.get("dataset_folders", {}) or {}) or None

    # Apply overrides from CLI flags
    if overrides.get("source_project"):
        source_project = str(overrides["source_project"])  # type: ignore[index]
    if overrides.get("dest"):
        dest = Path(str(overrides["dest"]))  # type: ignore[index]
    if overrides.get("location"):
        location = str(overrides["location"])  # type: ignore[index]
    if overrides.get("ext"):
        ext = str(overrides["ext"])  # type: ignore[index]
    if overrides.get("overwrite"):
        overwrite = str(overrides["overwrite"])  # type: ignore[index]
    if overrides.get("add_dataform_header") is not None:
        add_header = bool(overrides["add_dataform_header"])  # type: ignore[index]
    if overrides.get("dry_run") is not None:
        dry_run = bool(overrides["dry_run"])  # type: ignore[index]

    # CLI-provided include/exclude lists replace file values if present
    if "datasets_include" in overrides and overrides["datasets_include"] is not None:
        datasets_include = list(overrides["datasets_include"])  # type: ignore[assignment]
    if "datasets_exclude" in overrides and overrides["datasets_exclude"] is not None:
        datasets_exclude = list(overrides["datasets_exclude"])  # type: ignore[assignment]

    if not source_project:
        raise ValueError("source_project is required (config or CLI)")
    if not dest:
        raise ValueError("dest is required (config or CLI)")
    if ext not in {"sql", "sqlx"}:
        raise ValueError("ext must be 'sql' or 'sqlx'")
    if overwrite not in {"skip", "backup", "force"}:
        raise ValueError("overwrite must be one of: skip, backup, force")

    return Config(
        source_project=source_project,
        dest=dest,
        datasets_include=datasets_include,
        datasets_exclude=datasets_exclude,
        location=location,
        ext=ext,
        overwrite=overwrite,
        add_dataform_header=add_header,
        header_description=header_description,
        header_tags=header_tags,
        dataset_folders=dataset_folders,
        dry_run=dry_run,
    )
