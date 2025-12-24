from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List

from simple_automated_testing.adapters.api.client import HttpxApiClient
from simple_automated_testing.adapters.api.interface import ApiClient
from simple_automated_testing.adapters.bigquery.client import BigQueryAdapter
from simple_automated_testing.adapters.bigquery.interface import BigQueryClient
from simple_automated_testing.config.discovery import discover_pipelines, discover_tests
from simple_automated_testing.config.identity import (
    IdentityResolutionError,
    build_identity_index,
    get_identities,
    resolve_identity_or_error,
)
from simple_automated_testing.config.loader import ConfigLoadError, load_config
from simple_automated_testing.config.validation import ConfigError, validate_config
from simple_automated_testing.contracts.models import RunResult, StepResult
from simple_automated_testing.core.pipeline_runner import run_pipeline
from simple_automated_testing.core.steps import (
    ExecutionError,
    run_api_test,
    run_bq_data_test,
    run_bq_schema_test,
    run_openapi_parse,
)
from simple_automated_testing.reporting.human import render_human_html, render_human_summary
from simple_automated_testing.reporting.junit import render_junit
from simple_automated_testing.utils.report_paths import resolve_report_path
from simple_automated_testing.utils.time import now_utc_iso, new_run_id


def _resolve_pipeline(config: Dict[str, Any], pipeline: Dict[str, Any] | None, pipeline_id: str | None) -> Dict[str, Any] | None:
    if pipeline is not None:
        return pipeline
    if pipeline_id:
        for item in discover_pipelines(config):
            if item.get("id") == pipeline_id:
                return item
        raise ExecutionError(f"找不到 pipeline: {pipeline_id}")
    return None


def _write_report(path: str, content: str) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


def _resolve_bq_client_for_test(
    test_def: Dict[str, Any],
    config: Dict[str, Any],
    bq_client: BigQueryClient | None,
    identity_map: Dict[str, Dict[str, Any]],
    default_identity_name: str | None,
    client_cache: Dict[str, BigQueryClient],
) -> BigQueryClient | None:
    if bq_client is not None:
        return bq_client
    if not config.get("bigQuery"):
        return None

    try:
        identity_name, identity = resolve_identity_or_error(test_def, identity_map, default_identity_name)
    except IdentityResolutionError as exc:
        raise ExecutionError(str(exc)) from exc

    cached = client_cache.get(identity_name)
    if cached is not None:
        return cached

    bigquery_cfg = config.get("bigQuery", {})
    client = BigQueryAdapter(
        project_id=bigquery_cfg.get("projectId"),
        location=bigquery_cfg.get("location"),
        credentials_path=identity.get("serviceAccountKeyPath"),
    )
    client_cache[identity_name] = client
    return client


def _execute(
    config: Dict[str, Any],
    pipeline: Dict[str, Any] | None,
    pipeline_id: str | None,
    api_client: ApiClient | None,
    bq_client: BigQueryClient | None,
) -> RunResult:
    pipeline_def = _resolve_pipeline(config, pipeline, pipeline_id)
    tests_def = discover_tests(config) if pipeline_def is None else []
    if not pipeline_def and not tests_def:
        raise ExecutionError("沒有可執行的測試或 pipeline")

    if api_client is None:
        api_client = HttpxApiClient(timeout_ms=config.get("apiRetry", {}).get("timeoutMs", 10000))
    identity_map, default_identity_name = build_identity_index(get_identities(config))
    bq_client_cache: Dict[str, BigQueryClient] = {}

    run_id = new_run_id()
    started_at = now_utc_iso()
    step_results: List[StepResult] = []

    if pipeline_def is not None:
        step_results = run_pipeline(
            pipeline_def,
            config,
            api_client,
            bq_client,
            get_bq_client=lambda test_def: _resolve_bq_client_for_test(
                test_def,
                config,
                bq_client,
                identity_map,
                default_identity_name,
                bq_client_cache,
            ),
        )
    else:
        for step in tests_def:
            step_type = step.get("type")
            start = time.time()
            if step_type == "api":
                result = run_api_test(step, config, api_client)
            elif step_type == "openapi.parse":
                result = run_openapi_parse(step)
            elif step_type == "bigquery.schema":
                current_bq_client = _resolve_bq_client_for_test(
                    step,
                    config,
                    bq_client,
                    identity_map,
                    default_identity_name,
                    bq_client_cache,
                )
                if current_bq_client is None:
                    raise ExecutionError("未設定 BigQuery 連線資訊")
                result = run_bq_schema_test(step, current_bq_client)
            elif step_type == "bigquery.data":
                current_bq_client = _resolve_bq_client_for_test(
                    step,
                    config,
                    bq_client,
                    identity_map,
                    default_identity_name,
                    bq_client_cache,
                )
                if current_bq_client is None:
                    raise ExecutionError("未設定 BigQuery 連線資訊")
                result = run_bq_data_test(step, current_bq_client)
            else:
                result = StepResult(
                    step_id=step.get("name", "unknown"),
                    name=step.get("name", "unknown"),
                    status="failed",
                    duration_ms=0,
                    assertions=[],
                    error="未知的測試類型",
                )
            result.duration_ms = int((time.time() - start) * 1000)
            step_results.append(result)

    finished_at = now_utc_iso()
    status = "failed" if any(step.status == "failed" for step in step_results) else "passed"

    run_result = RunResult(
        run_id=run_id,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        steps=step_results,
    ).with_counts()

    openapi_summary = _build_openapi_summary(step_results)
    if openapi_summary:
        run_result.artifacts["openApiSummary"] = openapi_summary

    reporting = config.get("reporting", {})
    if reporting.get("humanSummary", True):
        summary = render_human_summary(run_result)
        run_result.artifacts["humanSummary"] = summary
    if reporting.get("humanReportEnabled", True):
        html_content = render_human_html(run_result)
        if not html_content.strip():
            raise ExecutionError("人類報告內容為空，無法儲存")
        output_dir = reporting.get("humanReportOutputDir")
        file_name = reporting.get("humanReportFileName")
        try:
            report_path = resolve_report_path(output_dir, file_name)
        except ValueError as exc:
            raise ExecutionError(str(exc)) from exc
        report_path.write_text(html_content, encoding="utf-8")
        run_result.artifacts["humanReportPath"] = str(report_path)
    if reporting.get("junitEnabled", True):
        junit_content = render_junit(run_result)
        junit_path = reporting.get("junitOutputPath", "./test-results/junit.xml")
        _write_report(junit_path, junit_content)
        run_result.artifacts["junitReportPath"] = os.path.abspath(junit_path)

    return run_result


def _build_openapi_summary(steps: List[StepResult]) -> str | None:
    lines: List[str] = []
    for step in steps:
        if step.details:
            lines.append(f"OpenAPI parse summary: {step.name}")
            lines.extend(step.details)
    return "\n".join(lines) if lines else None


def run(
    config_path: str,
    pipeline: Dict[str, Any] | None = None,
    pipeline_id: str | None = None,
    api_client: ApiClient | None = None,
    bq_client: BigQueryClient | None = None,
) -> RunResult:
    try:
        config = validate_config(load_config(config_path))
    except (ConfigLoadError, ConfigError) as exc:
        raise ExecutionError(str(exc)) from exc

    return _execute(config, pipeline, pipeline_id, api_client, bq_client)


def run_with_config(
    config: Dict[str, Any],
    pipeline: Dict[str, Any] | None = None,
    pipeline_id: str | None = None,
    api_client: ApiClient | None = None,
    bq_client: BigQueryClient | None = None,
) -> RunResult:
    try:
        validated = validate_config(config)
    except ConfigError as exc:
        raise ExecutionError(str(exc)) from exc

    return _execute(validated, pipeline, pipeline_id, api_client, bq_client)
