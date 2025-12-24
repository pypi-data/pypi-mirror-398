from __future__ import annotations

from typing import Any, Dict, List


def discover_tests(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    tests = config.get("tests")
    if not tests:
        return []
    if not isinstance(tests, list):
        raise ValueError("tests 必須為陣列")
    return tests


def discover_pipelines(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    pipelines = config.get("pipelines")
    if not pipelines:
        return []
    if not isinstance(pipelines, list):
        raise ValueError("pipelines 必須為陣列")
    return pipelines
