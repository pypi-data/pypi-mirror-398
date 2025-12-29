from __future__ import annotations

from collections.abc import Iterable, Sequence

from google.cloud import bigquery


def discover_views(
    source_project: str,
    datasets: Iterable[str] | None,
    exclude: Iterable[str] | None,
    location: str | None,
) -> Iterable[tuple[str, str]]:
    """Yield (dataset_id, view_id) for all views in the project.

    Applies include/exclude dataset filters if provided. The ``location``
    parameter is present for signature parity but not used by this API path.
    """
    client = bigquery.Client(project=source_project)
    include_set = set(datasets or [])
    exclude_set = set(exclude or [])

    ds_iter = client.list_datasets(project=source_project)
    for ds in ds_iter:
        ds_id = ds.dataset_id
        if include_set and ds_id not in include_set:
            continue
        if ds_id in exclude_set:
            continue

        tables = client.list_tables(f"{source_project}.{ds_id}")
        for t in tables:
            if getattr(t, "table_type", "").upper() != "VIEW":
                continue
            yield (ds_id, t.table_id)


def fetch_view_query(client, table_ref: str) -> str:
    """Return the SQL backing a BigQuery view given its table reference."""
    table = client.get_table(table_ref)
    query = getattr(table, "view_query", None)
    if not query:
        query = table._properties.get("view", {}).get("query")  # type: ignore[attr-defined]
    if not query:
        raise RuntimeError(f"View query not found for table: {table_ref}")
    return str(query)


def views_from_information_schema(
    project: str,
    location: str,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Return (dataset, view_name, view_definition) using INFORMATION_SCHEMA.

    Queries ``region-<location>``.INFORMATION_SCHEMA.VIEWS and applies
    optional include/exclude dataset filters via query parameters.
    """
    client = bigquery.Client(project=project)

    query = [
        "SELECT table_schema, table_name, view_definition",
        f"FROM `region-{location}`.INFORMATION_SCHEMA.VIEWS",
        "WHERE 1=1",
    ]
    params = []
    if include:
        query.append("AND table_schema IN UNNEST(@include)")
        params.append(bigquery.ArrayQueryParameter("include", "STRING", list(include)))
    if exclude:
        query.append("AND table_schema NOT IN UNNEST(@exclude)")
        params.append(bigquery.ArrayQueryParameter("exclude", "STRING", list(exclude)))

    job = client.query(
        "\n".join(query),
        job_config=bigquery.QueryJobConfig(query_parameters=params),
        location=location,
    )
    rows = list(job.result())
    out: list[tuple[str, str, str]] = []
    for r in rows:
        ds = r.table_schema
        name = r.table_name
        sql = r.view_definition
        out.append((str(ds), str(name), str(sql)))
    return out
