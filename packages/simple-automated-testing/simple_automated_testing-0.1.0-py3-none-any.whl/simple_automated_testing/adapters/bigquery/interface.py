from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from simple_automated_testing.contracts.transport import QueryResult, SchemaDef


class BigQueryClient(ABC):
    @abstractmethod
    def fetch_schema(self, table: str) -> SchemaDef:
        raise NotImplementedError

    @abstractmethod
    def run_query(self, sql: str, max_rows: int = 20) -> QueryResult:
        raise NotImplementedError

    @abstractmethod
    def table_exists(self, table: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_tables(self, dataset: str) -> Sequence[str]:
        raise NotImplementedError
