from __future__ import annotations

import time
from typing import Any, Callable, Dict, List

from simple_automated_testing.adapters.api.interface import ApiClient
from simple_automated_testing.adapters.bigquery.interface import BigQueryClient
from simple_automated_testing.contracts.models import StepResult
from simple_automated_testing.core.steps import (
    run_api_test,
    run_bq_data_test,
    run_bq_schema_test,
    run_openapi_parse,
)
from simple_automated_testing.core.pipeline import Pipeline, from_dict
from simple_automated_testing.core.polling import wait_until


def _run_test(
    step: Dict[str, Any],
    config: Dict[str, Any],
    api_client: ApiClient,
    bq_client: BigQueryClient | None,
    get_bq_client: Callable[[Dict[str, Any]], BigQueryClient | None] | None,
) -> StepResult:
    step_type = step.get("type")
    current_bq_client = bq_client
    if step_type in {"bigquery.schema", "bigquery.data"} and get_bq_client is not None:
        current_bq_client = get_bq_client(step)
    if step_type == "api":
        return run_api_test(step, config, api_client)
    if step_type == "openapi.parse":
        return run_openapi_parse(step)
    if step_type == "bigquery.schema":
        if current_bq_client is None:
            raise RuntimeError("未設定 BigQuery 連線資訊")
        return run_bq_schema_test(step, current_bq_client)
    if step_type == "bigquery.data":
        if current_bq_client is None:
            raise RuntimeError("未設定 BigQuery 連線資訊")
        return run_bq_data_test(step, current_bq_client)
    return StepResult(
        step_id=step.get("name", "unknown"),
        name=step.get("name", "unknown"),
        status="failed",
        duration_ms=0,
        assertions=[],
        error="未知的測試類型",
    )


def run_pipeline(
    pipeline_def: Dict[str, Any],
    config: Dict[str, Any],
    api_client: ApiClient,
    bq_client: BigQueryClient | None,
    get_bq_client: Callable[[Dict[str, Any]], BigQueryClient | None] | None = None,
) -> List[StepResult]:
    pipeline: Pipeline = from_dict(pipeline_def)
    results: List[StepResult] = []

    for step in pipeline.steps:
        start = time.time()
        if step.type == "waitUntil":
            test_def = step.payload.get("test")
            if not isinstance(test_def, dict):
                result = StepResult(
                    step_id=step.name,
                    name=step.name,
                    status="failed",
                    duration_ms=0,
                    assertions=[],
                    error="waitUntil 缺少 test 定義",
                )
            else:
                interval_ms = step.payload.get("intervalMs", 1000)
                timeout_ms = step.payload.get("timeoutMs")
                max_attempts = step.payload.get("maxAttempts")

                def _call():
                    return _run_test(test_def, config, api_client, bq_client, get_bq_client)

                success, attempts, last_result = wait_until(
                    _call,
                    lambda r: r.status == "passed",
                    interval_ms=interval_ms,
                    timeout_ms=timeout_ms,
                    max_attempts=max_attempts,
                )
                status = "passed" if success else "failed"
                error = None if success else f"waitUntil 超時或未達條件（attempts={attempts}）"
                result = StepResult(
                    step_id=step.name,
                    name=step.name,
                    status=status,
                    duration_ms=0,
                    assertions=last_result.assertions if last_result else [],
                    error=error,
                )
        else:
            result = _run_test(step.payload, config, api_client, bq_client, get_bq_client)

        result.duration_ms = int((time.time() - start) * 1000)
        results.append(result)

        if pipeline.mode == "failFast" and result.status != "passed":
            break

    return results
