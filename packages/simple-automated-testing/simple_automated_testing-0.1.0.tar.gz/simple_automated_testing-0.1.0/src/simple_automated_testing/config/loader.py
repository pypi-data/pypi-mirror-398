from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml


_ENV_PREFIX = "SIMPLE_TEST_"


class ConfigLoadError(RuntimeError):
    pass


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    overrides = {
        "projectName": os.getenv(f"{_ENV_PREFIX}PROJECT_NAME"),
        "bigQuery.projectId": os.getenv(f"{_ENV_PREFIX}BQ_PROJECT_ID"),
        "bigQuery.dataset": os.getenv(f"{_ENV_PREFIX}BQ_DATASET"),
        "bigQuery.location": os.getenv(f"{_ENV_PREFIX}BQ_LOCATION"),
        "reporting.junitEnabled": os.getenv(f"{_ENV_PREFIX}JUNIT_ENABLED"),
        "reporting.junitOutputPath": os.getenv(f"{_ENV_PREFIX}JUNIT_OUTPUT_PATH"),
        "reporting.humanSummary": os.getenv(f"{_ENV_PREFIX}HUMAN_SUMMARY"),
        "reporting.humanReportEnabled": os.getenv(f"{_ENV_PREFIX}HUMAN_REPORT_ENABLED"),
        "reporting.humanReportOutputDir": os.getenv(f"{_ENV_PREFIX}HUMAN_REPORT_OUTPUT_DIR"),
        "reporting.humanReportFileName": os.getenv(f"{_ENV_PREFIX}HUMAN_REPORT_FILE_NAME"),
    }

    for key, value in overrides.items():
        if value is None:
            continue
        if key in {"reporting.junitEnabled", "reporting.humanSummary", "reporting.humanReportEnabled"}:
            value = _parse_bool(value)
        _set_nested(config, key.split("."), value)

    json_overrides = os.getenv(f"{_ENV_PREFIX}OVERRIDES_JSON")
    if json_overrides:
        try:
            payload = json.loads(json_overrides)
        except json.JSONDecodeError as exc:
            raise ConfigLoadError("SIMPLE_TEST_OVERRIDES_JSON 不是有效 JSON") from exc
        if isinstance(payload, dict):
            config = _deep_merge(config, payload)

    return config


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _set_nested(config: Dict[str, Any], path: list[str], value: Any) -> None:
    node = config
    for part in path[:-1]:
        node = node.setdefault(part, {})
    node[path[-1]] = value


def load_config(path: str) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigLoadError(f"設定檔不存在：{path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigLoadError("設定檔 YAML 解析失敗") from exc

    if not isinstance(data, dict):
        raise ConfigLoadError("設定檔內容必須為 YAML 物件")

    data = _apply_env_overrides(data)
    return data
