from __future__ import annotations

from typing import Any, Dict, List

from simple_automated_testing.config.identity import build_identity_index, get_identities, resolve_identity_name


class ConfigError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def _ensure_unique(items: List[Dict[str, Any]], key: str, label: str, errors: List[str]) -> None:
    seen = set()
    for item in items:
        value = item.get(key)
        if value in seen:
            errors.append(f"{label} 的 {key} 重複：{value}")
        if value is not None:
            seen.add(value)


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    project_name = config.get("projectName")
    if not project_name or not isinstance(project_name, str):
        errors.append("projectName 為必填字串")

    api_targets = config.get("apiTargets") or []
    if api_targets:
        if not isinstance(api_targets, list):
            errors.append("apiTargets 必須為陣列")
        else:
            for target in api_targets:
                if not isinstance(target, dict):
                    errors.append("apiTargets 必須為物件陣列")
                    continue
                if not target.get("id"):
                    errors.append("apiTargets.id 為必填")
                if not target.get("baseUrl"):
                    errors.append("apiTargets.baseUrl 為必填")
            _ensure_unique(api_targets, "id", "apiTargets", errors)

    bigquery = config.get("bigQuery")
    if bigquery is not None:
        if not isinstance(bigquery, dict):
            errors.append("bigQuery 必須為物件")
        else:
            if not bigquery.get("projectId"):
                errors.append("bigQuery.projectId 為必填")
            if not bigquery.get("dataset"):
                errors.append("bigQuery.dataset 為必填")

    raw_identities = config.get("identities")
    identities = get_identities(config)
    if raw_identities is not None and not isinstance(raw_identities, list):
        errors.append("identities 必須為陣列")
    if identities:
        for identity in identities:
            if not isinstance(identity, dict):
                errors.append("identities 必須為物件陣列")
                continue
            name = identity.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append("identities.name 為必填")
            if "isDefault" in identity and not isinstance(identity.get("isDefault"), bool):
                errors.append("identities.isDefault 必須為布林")
            key_path = identity.get("serviceAccountKeyPath")
            if not isinstance(key_path, str) or not key_path.strip():
                errors.append("identities.serviceAccountKeyPath 為必填")
        if len(identities) > 50:
            errors.append("identities 數量上限為 50")
        _ensure_unique(identities, "name", "identities", errors)
        default_identities = [identity for identity in identities if identity.get("isDefault") is True]
        if len(default_identities) > 1:
            errors.append("identities.isDefault 僅允許一個")

    reporting = config.setdefault("reporting", {})
    if not isinstance(reporting, dict):
        errors.append("reporting 必須為物件")
    else:
        reporting.setdefault("junitEnabled", True)
        reporting.setdefault("junitOutputPath", "./test-results/junit.xml")
        reporting.setdefault("humanSummary", True)
        reporting.setdefault("humanReportEnabled", True)
        if not isinstance(reporting.get("humanReportEnabled"), bool):
            errors.append("reporting.humanReportEnabled 必須為布林")
        if "humanReportOutputDir" in reporting:
            output_dir = reporting.get("humanReportOutputDir")
            if not isinstance(output_dir, str) or not output_dir.strip():
                errors.append("reporting.humanReportOutputDir 必須為非空字串")
        if "humanReportFileName" in reporting:
            file_name = reporting.get("humanReportFileName")
            if not isinstance(file_name, str) or not file_name.strip():
                errors.append("reporting.humanReportFileName 必須為非空字串")

    openapi_spec_path = config.get("openApiSpecPath")
    if openapi_spec_path is not None:
        if not isinstance(openapi_spec_path, str) or not openapi_spec_path.strip():
            errors.append("openApiSpecPath 必須為非空字串")

    api_retry = config.setdefault("apiRetry", {})
    if not isinstance(api_retry, dict):
        errors.append("apiRetry 必須為物件")
    else:
        api_retry.setdefault("maxAttempts", 1)
        api_retry.setdefault("timeoutMs", 10000)
        api_retry.setdefault("intervalMs", 0)

    tests = config.get("tests") or []
    if tests:
        if not isinstance(tests, list):
            errors.append("tests 必須為陣列")
        else:
            identity_map, default_name = build_identity_index(identities)
            for test_def in tests:
                if not isinstance(test_def, dict):
                    errors.append("tests 必須為物件陣列")
                    continue
                test_type = test_def.get("type")
                if test_type in {"bigquery.schema", "bigquery.data"}:
                    identity_name = test_def.get("identity")
                    if identity_name is not None and not isinstance(identity_name, str):
                        errors.append("tests.identity 必須為字串")
                        continue
                    resolved_name = resolve_identity_name(test_def, default_name)
                    if resolved_name is None:
                        errors.append("未指定 Identity 且沒有預設 Identity")
                        continue
                    if resolved_name not in identity_map:
                        errors.append(f"tests.identity 不存在：{resolved_name}")

    if errors:
        raise ConfigError(errors)

    return config
