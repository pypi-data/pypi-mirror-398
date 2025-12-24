from __future__ import annotations

import json
from typing import Any, Dict

from simple_automated_testing.adapters.api.client import HttpxApiClient
from simple_automated_testing.adapters.api.interface import ApiClient
from simple_automated_testing.adapters.bigquery.interface import BigQueryClient
from simple_automated_testing.contracts.models import AssertionResult, Diff, StepResult
from simple_automated_testing.contracts.transport import SchemaDef, SchemaField
from simple_automated_testing.core.retry import retry_call
from simple_automated_testing.validators.api.assertions import DefaultApiValidator
from simple_automated_testing.validators.api.openapi import (
    OpenApiError,
    load_openapi_spec,
    summarize_endpoints,
    validate_response_body,
)
from simple_automated_testing.validators.bigquery.data_rules import DefaultDataValidator
from simple_automated_testing.validators.bigquery.schema import DefaultSchemaValidator


class ExecutionError(RuntimeError):
    pass


def _find_api_target(config: Dict[str, Any], target_id: str) -> Dict[str, Any]:
    for target in config.get("apiTargets") or []:
        if target.get("id") == target_id:
            return target
    raise ExecutionError(f"找不到 API target: {target_id}")


def _build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _summarize_assertions(assertions) -> str | None:
    for assertion in assertions:
        for diff in assertion.diffs:
            return f"{diff.rule}: {diff.message}"
    return None


def run_api_test(test: Dict[str, Any], config: Dict[str, Any], api_client: ApiClient) -> StepResult:
    target = _find_api_target(config, test.get("target"))
    url = _build_url(target.get("baseUrl"), test.get("path", ""))
    headers = {**(target.get("defaultHeaders") or {}), **(test.get("headers") or {})}
    method = test.get("method", "GET")

    retry_cfg = config.get("apiRetry", {})
    timeout_ms = retry_cfg.get("timeoutMs", 10000)

    def _call():
        if isinstance(api_client, HttpxApiClient):
            api_client._timeout = timeout_ms / 1000  # noqa: SLF001 - internal tuning for core
        return api_client.send(method, url, headers, test.get("body"))

    response = retry_call(_call, retry_cfg.get("maxAttempts", 1), retry_cfg.get("intervalMs", 0))
    assertions = test.get("assertions", [])
    standard_assertions = [item for item in assertions if item.get("type") != "openapi"]
    openapi_assertions = [item for item in assertions if item.get("type") == "openapi"]

    validator = DefaultApiValidator()
    results = validator.validate(response, standard_assertions)

    if openapi_assertions:
        _ensure_json_value(response)
        for assertion in openapi_assertions:
            results.append(_run_openapi_assertion(assertion, response, test, config))

    passed = all(a.passed for a in results)
    status = "passed" if passed else "failed"
    return StepResult(
        step_id=test.get("name", "api"),
        name=test.get("name", "api"),
        status=status,
        duration_ms=0,
        assertions=results,
        error=None if passed else _summarize_assertions(results),
    )


def run_openapi_parse(test: Dict[str, Any]) -> StepResult:
    name = test.get("name", "openapi-parse")
    try:
        spec_path = test.get("specPath")
        if not spec_path:
            raise ExecutionError("openapi.parse 缺少 specPath")
        spec = load_openapi_spec(spec_path)
        details = summarize_endpoints(spec)
        if not details:
            details = ["未解析到任何端點"]
        return StepResult(
            step_id=name,
            name=name,
            status="passed",
            duration_ms=0,
            assertions=[],
            error=None,
            details=details,
        )
    except (OpenApiError, ExecutionError) as exc:
        return StepResult(
            step_id=name,
            name=name,
            status="failed",
            duration_ms=0,
            assertions=[],
            error=str(exc),
        )


def run_bq_schema_test(test: Dict[str, Any], bq_client: BigQueryClient) -> StepResult:
    expected_fields = [
        SchemaField(name=item.get("name"), type=item.get("type"), mode=item.get("mode", "NULLABLE"))
        for item in test.get("expectedSchema", [])
    ]
    expected = SchemaDef(fields=expected_fields)
    actual = bq_client.fetch_schema(test.get("table"))
    validator = DefaultSchemaValidator()
    assertions = validator.validate(actual, expected)
    passed = all(a.passed for a in assertions)
    status = "passed" if passed else "failed"
    return StepResult(
        step_id=test.get("name", "bq-schema"),
        name=test.get("name", "bq-schema"),
        status=status,
        duration_ms=0,
        assertions=assertions,
        error=None if passed else _summarize_assertions(assertions),
    )


def run_bq_data_test(test: Dict[str, Any], bq_client: BigQueryClient) -> StepResult:
    sql = test.get("sql")
    rule = test.get("rule") or {}
    result = bq_client.run_query(sql)
    validator = DefaultDataValidator()
    assertion = validator.validate(rule, result)
    passed = assertion.passed
    status = "passed" if passed else "failed"
    return StepResult(
        step_id=test.get("name", "bq-data"),
        name=test.get("name", "bq-data"),
        status=status,
        duration_ms=0,
        assertions=[assertion],
        error=None if passed else _summarize_assertions([assertion]),
    )


def _ensure_json_value(response) -> None:
    content_type = response.content_type or response.headers.get("content-type")
    if response.json_value is not None:
        return
    if not content_type or "json" not in content_type.lower():
        return
    try:
        response.json_value = json.loads(response.body_bytes.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - depends on payload
        response.json_error = str(exc)


def _run_openapi_assertion(
    assertion: Dict[str, Any],
    response,
    test: Dict[str, Any],
    config: Dict[str, Any],
) -> AssertionResult:
    name = assertion.get("name", "openapi")
    spec_path = assertion.get("specPath") or test.get("openApiSpecPath") or config.get("openApiSpecPath")
    if not spec_path:
        return _openapi_failure(name, "缺少 openApiSpecPath", expected="openApiSpecPath", actual=None)

    path = test.get("path")
    method = test.get("method", "GET")
    if not path:
        return _openapi_failure(name, "API 測試缺少 path", expected="path", actual=None)
    if not method:
        return _openapi_failure(name, "API 測試缺少 method", expected="method", actual=None)

    content_type = response.content_type or response.headers.get("content-type")
    if not content_type:
        return _openapi_failure(name, "回應缺少 content-type", expected="content-type", actual=None)
    if response.json_value is None:
        message = response.json_error or "回應非 JSON"
        return _openapi_failure(name, message, expected="JSON response", actual=None)

    target = {
        "path": path,
        "method": method,
        "statusCode": response.status,
        "contentType": content_type,
    }

    try:
        spec = load_openapi_spec(spec_path)
        diffs = validate_response_body(spec, target, response.json_value)
    except OpenApiError as exc:
        return _openapi_failure(name, str(exc), expected="OpenAPI spec", actual=None)

    passed = not diffs
    return AssertionResult(name=name, passed=passed, diffs=diffs)


def _openapi_failure(name: str, message: str, expected: Any, actual: Any) -> AssertionResult:
    return AssertionResult(
        name=name,
        passed=False,
        diffs=[Diff(rule="openapi", message=message, expected=expected, actual=actual)],
    )
