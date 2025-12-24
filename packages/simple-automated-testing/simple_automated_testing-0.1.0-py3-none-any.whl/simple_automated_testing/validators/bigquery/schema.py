from __future__ import annotations

from typing import List

from simple_automated_testing.contracts.models import AssertionResult, Diff
from simple_automated_testing.contracts.transport import SchemaDef
from simple_automated_testing.validators.bigquery.interface import BigQuerySchemaValidator


class DefaultSchemaValidator(BigQuerySchemaValidator):
    def validate(self, actual: SchemaDef, expected: SchemaDef) -> List[AssertionResult]:
        actual_map = {field.name: field for field in actual.fields}
        diffs: List[Diff] = []

        for exp in expected.fields:
            act = actual_map.get(exp.name)
            if act is None:
                diffs.append(
                    Diff(rule="schema.missing", message="缺少欄位", expected=exp.name, actual=None)
                )
                continue
            if act.type.upper() != exp.type.upper() or act.mode.upper() != exp.mode.upper():
                diffs.append(
                    Diff(
                        rule="schema.mismatch",
                        message="欄位型別或必要性不符",
                        expected={"type": exp.type, "mode": exp.mode},
                        actual={"type": act.type, "mode": act.mode},
                    )
                )

        passed = len(diffs) == 0
        return [AssertionResult(name="schema", passed=passed, diffs=diffs)]
