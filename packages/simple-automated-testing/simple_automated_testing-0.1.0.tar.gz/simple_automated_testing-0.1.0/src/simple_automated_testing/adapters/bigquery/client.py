from __future__ import annotations

from typing import Sequence

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from simple_automated_testing.adapters.bigquery.interface import BigQueryClient
from simple_automated_testing.contracts.transport import QueryResult, SchemaDef, SchemaField


class BigQueryAdapter(BigQueryClient):
    def __init__(self, project_id: str, location: str | None = None, credentials_path: str | None = None) -> None:
        if credentials_path:
            self._client = bigquery.Client.from_service_account_json(
                credentials_path,
                project=project_id,
                location=location,
            )
        else:
            self._client = bigquery.Client(project=project_id, location=location)

    def fetch_schema(self, table: str) -> SchemaDef:
        table_ref = self._client.get_table(table)
        fields = [SchemaField(name=f.name, type=f.field_type, mode=f.mode) for f in table_ref.schema]
        return SchemaDef(fields=fields)

    def run_query(self, sql: str, max_rows: int = 20) -> QueryResult:
        job = self._client.query(sql)
        result_iter = job.result()
        rows = [dict(row.items()) for _, row in zip(range(max_rows), result_iter)]
        total_rows = result_iter.total_rows
        row_count = total_rows if total_rows is not None else len(rows)
        scalar_value = None
        if rows and len(rows[0]) == 1:
            scalar_value = next(iter(rows[0].values()))
        return QueryResult(rows=rows, row_count=row_count, scalar_value=scalar_value, query_summary=f"rows={row_count}")

    def table_exists(self, table: str) -> bool:
        try:
            self._client.get_table(table)
            return True
        except NotFound:
            return False

    def list_tables(self, dataset: str) -> Sequence[str]:
        dataset_ref = self._client.dataset(dataset)
        tables = self._client.list_tables(dataset_ref)
        return [table.table_id for table in tables]
