from __future__ import annotations

import json
from typing import Any, Dict, List

from simple_automated_testing.contracts.models import AssertionResult, Diff
from simple_automated_testing.contracts.transport import ApiResponse
from simple_automated_testing.validators.api.interface import ApiValidator


def _get_json_path(data: Any, path: str) -> Any:
    node = data
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            raise KeyError(path)
    return node


def _to_type(value: Any) -> str:
    return type(value).__name__


class DefaultApiValidator(ApiValidator):
    def validate(self, response: ApiResponse, assertions: List[Dict[str, Any]]) -> List[AssertionResult]:
        results: List[AssertionResult] = []
        json_value = response.json_value
        if json_value is None and response.content_type and "json" in response.content_type:
            try:
                json_value = json.loads(response.body_bytes.decode("utf-8"))
            except Exception as exc:  # pragma: no cover - depends on payload
                response.json_error = str(exc)

        for assertion in assertions:
            kind = assertion.get("type")
            name = assertion.get("name", kind)
            diffs: List[Diff] = []
            passed = True

            if kind == "status_code":
                expected = assertion.get("expected")
                if response.status != expected:
                    passed = False
                    diffs.append(Diff(rule="status_code", message="狀態碼不符", expected=expected, actual=response.status))
            elif kind == "header_exists":
                header = assertion.get("header")
                if header is None or header.lower() not in response.headers:
                    passed = False
                    diffs.append(Diff(rule="header_exists", message="缺少 header", expected=header, actual=list(response.headers)))
            elif kind == "header_equals":
                header = assertion.get("header")
                expected = assertion.get("expected")
                actual = response.headers.get(header.lower()) if header else None
                if actual != expected:
                    passed = False
                    diffs.append(Diff(rule="header_equals", message="header 值不符", expected=expected, actual=actual))
            elif kind in {"json_exists", "json_equals", "json_type"}:
                path = assertion.get("path")
                if json_value is None:
                    passed = False
                    diffs.append(Diff(rule=kind, message="回應非 JSON", expected=path, actual=response.json_error))
                else:
                    try:
                        actual_value = _get_json_path(json_value, path)
                        if kind == "json_equals":
                            expected = assertion.get("expected")
                            if actual_value != expected:
                                passed = False
                                diffs.append(
                                    Diff(rule="json_equals", message="JSON 欄位值不符", expected=expected, actual=actual_value)
                                )
                        elif kind == "json_type":
                            expected = assertion.get("expected")
                            actual_type = _to_type(actual_value)
                            if actual_type != expected:
                                passed = False
                                diffs.append(
                                    Diff(rule="json_type", message="JSON 欄位型別不符", expected=expected, actual=actual_type)
                                )
                    except KeyError:
                        passed = False
                        diffs.append(Diff(rule=kind, message="JSON 欄位不存在", expected=path, actual=None))
            elif kind == "text_contains":
                expected = assertion.get("expected")
                body = response.body_bytes.decode("utf-8", errors="replace")
                if expected not in body:
                    passed = False
                    diffs.append(Diff(rule="text_contains", message="文字內容未包含", expected=expected, actual=body[:200]))
            else:
                passed = False
                diffs.append(Diff(rule="unknown", message="未知斷言類型", expected=kind, actual=None))

            results.append(AssertionResult(name=name, passed=passed, diffs=diffs))

        return results
