from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from simple_automated_testing.contracts.models import AssertionResult
from simple_automated_testing.contracts.transport import ApiResponse


class ApiValidator(ABC):
    @abstractmethod
    def validate(self, response: ApiResponse, assertions: List[Dict[str, Any]]) -> List[AssertionResult]:
        raise NotImplementedError
