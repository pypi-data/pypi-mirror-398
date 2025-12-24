from __future__ import annotations

from typing import Any, Dict, List


def api_test(
    name: str,
    target: str,
    path: str,
    method: str = "GET",
    headers: Dict[str, str] | None = None,
    body: Any | None = None,
    assertions: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    return {
        "type": "api",
        "name": name,
        "target": target,
        "path": path,
        "method": method,
        "headers": headers or {},
        "body": body,
        "assertions": assertions or [],
    }


def bq_schema_test(name: str, table: str, expected_schema: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "type": "bigquery.schema",
        "name": name,
        "table": table,
        "expectedSchema": expected_schema,
    }


def bq_data_test(name: str, sql: str, rule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "bigquery.data",
        "name": name,
        "sql": sql,
        "rule": rule,
    }


def openapi_assertion(spec_path: str | None = None, name: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"type": "openapi"}
    if name:
        payload["name"] = name
    if spec_path:
        payload["specPath"] = spec_path
    return payload


def pipeline(steps: List[Dict[str, Any]], pipeline_id: str | None = None, name: str | None = None) -> Dict[str, Any]:
    return {
        "id": pipeline_id or "pipeline",
        "name": name or pipeline_id or "pipeline",
        "steps": steps,
        "mode": "failFast",
    }
