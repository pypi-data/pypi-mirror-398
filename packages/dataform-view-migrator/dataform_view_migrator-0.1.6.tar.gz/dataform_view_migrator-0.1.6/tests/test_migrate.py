from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from dataform_view_migrator import migrate as mig
from dataform_view_migrator.config import Config


def make_cfg(tmp_path: Path, location: str | None = "US") -> Config:
    return Config(
        source_project="proj",
        dest=tmp_path,
        datasets_include=None,
        datasets_exclude=None,
        location=location,
        ext="sqlx",
        overwrite="force",
        add_dataform_header=True,
        header_description="CREATED BY DATAFORM. custom",
        header_tags=["t1"],
        dataset_folders=None,
        dry_run=False,
    )


def test_migrate_writes_files_with_header_using_info_schema(tmp_path: Path) -> None:
    """When location is set, migration uses INFORMATION_SCHEMA and writes headers."""
    cfg = make_cfg(tmp_path, location="US")

    def fake_views_from_info_schema(project: str, location: str, include, exclude):
        assert project == "proj"
        assert location == "US"
        return [("dataset_a", "view_a", "SELECT 1;")]

    with patch.object(mig, "views_from_information_schema", fake_views_from_info_schema):
        results = mig.migrate(cfg, dry_run=False)
    assert len(results) == 1
    out = results[0]
    assert out.action == "created"
    path = out.path
    text = path.read_text(encoding="utf-8")
    assert 'type: "view"' in text
    assert 'schema: "dataset_a"' in text
    assert 'name: "view_a"' in text
    assert 'description: "CREATED BY DATAFORM. custom"' in text
    assert 'tags: ["t1"]' in text
    assert "SELECT 1;" in text


def test_migrate_dry_run_reports_actions(tmp_path: Path) -> None:
    """Dry-run returns would-create/skip/update without writing files."""
    cfg = make_cfg(tmp_path, location="US")

    # Pre-create one file to trigger would-update
    pre_dir = tmp_path / "dataset_b"
    pre_dir.mkdir(parents=True, exist_ok=True)
    pre_file = pre_dir / "view_b.sqlx"
    pre_file.write_text("old", encoding="utf-8")

    def fake_views_from_info_schema(project: str, location: str, include, exclude):
        return [("dataset_a", "view_a", "SELECT 1;"), ("dataset_b", "view_b", "SELECT 2;")]

    with patch.object(mig, "views_from_information_schema", fake_views_from_info_schema):
        results = mig.migrate(cfg, dry_run=True)
    actions = {r.view: r.action for r in results}
    assert actions["view_a"].startswith("would-")
    assert actions["view_b"].startswith("would-")
    # Ensure no writes occurred in dry-run for view_a
    assert not (tmp_path / "dataset_a" / "view_a.sqlx").exists()


def test_results_dataframe_has_expected_columns(tmp_path: Path) -> None:
    """results_dataframe returns a usable Polars DataFrame with all columns."""
    cfg = make_cfg(tmp_path, location="US")

    def fake_views_from_info_schema(project: str, location: str, include, exclude):
        return [("d1", "v1", "SELECT 1"), ("d2", "v2", "SELECT 2")]

    with patch.object(mig, "views_from_information_schema", fake_views_from_info_schema):
        res = mig.migrate(cfg, dry_run=True)
    df = mig.results_dataframe(res)
    assert set(df.columns) == {"dataset", "view", "action", "path", "error"}
    assert df.height == 2


def test_migrate_api_discovery_path_writes_files(tmp_path: Path) -> None:
    """When no location is set, use API discovery path and write content."""
    cfg = make_cfg(tmp_path, location=None)

    # Patch BigQuery client and discovery + fetch to avoid network
    with patch.object(mig.bigquery, "Client") as MockClient, \
         patch.object(mig, "discover_views", lambda *_: [("ds1", "v1"), ("ds2", "v2")]), \
         patch.object(
             mig,
             "fetch_view_query",
             lambda client, ref: "SELECT 42" if ref.endswith(".v1") else "SELECT 99",
         ):
        MockClient.return_value = MagicMock(project="proj")
        results = mig.migrate(cfg, dry_run=False)
    assert {r.view for r in results} == {"v1", "v2"}
    for r in results:
        text = r.path.read_text(encoding="utf-8")
        assert "config {" in text  # header present
        assert "SELECT" in text
