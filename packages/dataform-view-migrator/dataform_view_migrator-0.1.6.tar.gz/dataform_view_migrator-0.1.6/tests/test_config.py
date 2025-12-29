from __future__ import annotations

from pathlib import Path

import pytest

from dataform_view_migrator.config import load_config


def write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_config_uses_toml_and_overrides(tmp_path: Path) -> None:
    """load_config reads TOML defaults and applies CLI overrides with validation."""
    cfg_path = tmp_path / "dataform_view_migrator.toml"
    write_toml(
        cfg_path,
        """
        source_project = "proj-a"
        dest = "dest_dir"
        location = "US"
        ext = "sqlx"
        overwrite = "skip"
        add_dataform_header = true
        [dataform_header]
        description = "CREATED BY DATAFORM. extra"
        tags = ["x", "y"]
        """.strip(),
    )

    cfg = load_config(cfg_path, overrides={})
    assert cfg.source_project == "proj-a"
    assert str(cfg.dest).endswith("dest_dir")
    assert cfg.location == "US"
    assert cfg.ext == "sqlx"
    assert cfg.overwrite == "skip"
    assert cfg.add_dataform_header is True
    assert cfg.header_description == "CREATED BY DATAFORM. extra"
    assert cfg.header_tags == ["x", "y"]

    # Overrides take precedence
    cfg2 = load_config(
        cfg_path,
        overrides={
            "source_project": "proj-b",
            "location": "EU",
            "ext": "sql",
            "overwrite": "force",
            "add_dataform_header": False,
        },
    )
    assert cfg2.source_project == "proj-b"
    assert cfg2.location == "EU"
    assert cfg2.ext == "sql"
    assert cfg2.overwrite == "force"
    assert cfg2.add_dataform_header is False


def test_load_config_requires_required_fields(tmp_path: Path) -> None:
    """Missing source_project or dest should raise validation errors."""
    cfg_path = tmp_path / "config.toml"
    write_toml(cfg_path, "location = \"US\"\n")

    with pytest.raises(ValueError):
        load_config(cfg_path, overrides={})
