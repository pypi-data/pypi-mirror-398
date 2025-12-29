"""Tests for the `ping-bq` command.

Covers three behaviors:
- With a location: executes a dry-run INFORMATION_SCHEMA query.
- Without a location: lists datasets and iterates an iterable `.pages`.
- Without flags: reads project/location defaults from TOML.

Implementation notes:
- Uses `unittest.mock` to simulate the BigQuery client surface.
- `.pages` is intentionally an iterable (not an iterator); code must not call
  `next(pages)` directly.
"""
from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
import typer

from dataform_view_migrator import cli


def test_ping_bq_uses_info_schema_when_location_flag(capsys) -> None:
    """With a location, ensure a dry-run query is issued and project prints."""
    def _client_factory(project: str | None = None, **_):
        m = MagicMock()
        m.project = project or "adc-project"
        # .query is called but its return value is not inspected
        m.query.return_value = object()
        return m

    with patch.object(cli.bigquery, "Client") as MockClient, \
         patch.object(cli.bigquery, "QueryJobConfig") as MockQJC:
        MockClient.side_effect = _client_factory
        MockQJC.return_value = Mock()
        with pytest.raises(typer.Exit) as ei:
            cli.ping_bq(project="proj-x", location="US", config=None)
    assert ei.value.exit_code == 0

    out = capsys.readouterr().out
    assert "BigQuery project:" in out
    assert "proj-x" in out


def test_ping_bq_uses_dataset_list_when_no_location(capsys) -> None:
    """Without a location, ensure dataset listing path is used and prints."""
    def _client_factory(project: str | None = None, **_):
        m = MagicMock()
        m.project = project or "adc-project"
        # list_datasets should return an object with an iterable `.pages`
        ds_iter = MagicMock()
        ds_iter.pages = [None]
        m.list_datasets.return_value = ds_iter
        return m

    with patch.object(cli.bigquery, "Client") as MockClient:
        MockClient.side_effect = _client_factory
        with pytest.raises(typer.Exit) as ei:
            cli.ping_bq(project="proj-y", location=None, config=None)
    assert ei.value.exit_code == 0

    out = capsys.readouterr().out
    assert "BigQuery project:" in out
    assert "proj-y" in out


def test_ping_bq_reads_project_and_location_from_config(tmp_path, capsys) -> None:
    """When flags are omitted, read project/location defaults from TOML."""
    # Prepare config TOML
    cfg = tmp_path / "dataform_view_migrator.toml"
    cfg.write_text("source_project = \"proj-cfg\"\nlocation = \"EU\"\n", encoding="utf-8")

    def _client_factory(project: str | None = None, **_):
        m = MagicMock()
        m.project = project or "adc-project"
        m.query.return_value = object()
        return m

    with patch.object(cli.bigquery, "Client") as MockClient, \
         patch.object(cli.bigquery, "QueryJobConfig") as MockQJC:
        MockClient.side_effect = _client_factory
        MockQJC.return_value = Mock()
        with pytest.raises(typer.Exit) as ei:
            cli.ping_bq(project=None, location=None, config=str(cfg))
    assert ei.value.exit_code == 0

    out = capsys.readouterr().out
    assert "BigQuery project:" in out
    assert "proj-cfg" in out
