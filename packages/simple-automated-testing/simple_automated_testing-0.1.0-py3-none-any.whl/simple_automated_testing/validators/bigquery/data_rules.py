from __future__ import annotations

from typing import Any, Dict

from simple_automated_testing.contracts.models import AssertionResult, Diff
from simple_automated_testing.contracts.transport import QueryResult
from simple_automated_testing.validators.bigquery.interface import BigQueryDataValidator


class DefaultDataValidator(BigQueryDataValidator):
    def validate(self, rule: Dict[str, Any], result: QueryResult) -> AssertionResult:
        rule_type = rule.get("type")
        diffs: list[Diff] = []
        passed = True

        if rule_type == "row_count.equals":
            expected = rule.get("expected")
            if result.row_count != expected:
                passed = False
                diffs.append(Diff(rule=rule_type, message="列數不符", expected=expected, actual=result.row_count))
        elif rule_type == "row_count.min":
            expected = rule.get("expected")
            if result.row_count < expected:
                passed = False
                diffs.append(Diff(rule=rule_type, message="列數不足", expected=expected, actual=result.row_count))
        elif rule_type == "row_count.max":
            expected = rule.get("expected")
            if result.row_count > expected:
                passed = False
                diffs.append(Diff(rule=rule_type, message="列數超出上限", expected=expected, actual=result.row_count))
        elif rule_type == "row_count.between":
            min_value = rule.get("min")
            max_value = rule.get("max")
            if min_value is None or max_value is None:
                passed = False
                diffs.append(Diff(rule=rule_type, message="缺少 min/max", expected=None, actual=None))
            elif not (min_value <= result.row_count <= max_value):
                passed = False
                diffs.append(
                    Diff(rule=rule_type, message="列數不在範圍內", expected=f"{min_value}-{max_value}", actual=result.row_count)
                )
        elif rule_type == "query.result_equals":
            expected = rule.get("expected")
            if result.scalar_value != expected:
                passed = False
                diffs.append(
                    Diff(rule=rule_type, message="查詢結果不符", expected=expected, actual=result.scalar_value)
                )
        elif rule_type == "query.result_between":
            min_value = rule.get("min")
            max_value = rule.get("max")
            actual = result.scalar_value
            if actual is None or min_value is None or max_value is None:
                passed = False
                diffs.append(Diff(rule=rule_type, message="查詢結果或範圍缺失", expected=None, actual=actual))
            elif not (min_value <= actual <= max_value):
                passed = False
                diffs.append(
                    Diff(rule=rule_type, message="查詢結果不在範圍內", expected=f"{min_value}-{max_value}", actual=actual)
                )
        elif rule_type == "query.non_empty":
            if result.row_count == 0:
                passed = False
                diffs.append(Diff(rule=rule_type, message="查詢結果為空", expected=">0", actual=0))
        elif rule_type == "query.empty":
            if result.row_count != 0:
                passed = False
                diffs.append(Diff(rule=rule_type, message="查詢結果非空", expected=0, actual=result.row_count))
        else:
            passed = False
            diffs.append(Diff(rule="unsupported", message="未支援的規則", expected=rule_type, actual=None))

        return AssertionResult(name=rule.get("name", rule_type), passed=passed, diffs=diffs)
