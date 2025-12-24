from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ApiResponse:
    status: int
    headers: Dict[str, str]
    body_bytes: bytes
    content_type: Optional[str] = None
    json_value: Optional[Any] = None
    json_error: Optional[str] = None


@dataclass(slots=True)
class SchemaField:
    name: str
    type: str
    mode: str


@dataclass(slots=True)
class SchemaDef:
    fields: List[SchemaField] = field(default_factory=list)


@dataclass(slots=True)
class QueryResult:
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    scalar_value: Optional[Any] = None
    query_summary: Optional[str] = None
