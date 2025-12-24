from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from simple_automated_testing.contracts.models import AssertionResult
from simple_automated_testing.contracts.transport import QueryResult, SchemaDef


class BigQuerySchemaValidator(ABC):
    @abstractmethod
    def validate(self, actual: SchemaDef, expected: SchemaDef) -> List[AssertionResult]:
        raise NotImplementedError


class BigQueryDataValidator(ABC):
    @abstractmethod
    def validate(self, rule: Dict[str, Any], result: QueryResult) -> AssertionResult:
        raise NotImplementedError
