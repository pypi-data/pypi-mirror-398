from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from simple_automated_testing.contracts.transport import ApiResponse


class ApiClient(ABC):
    @abstractmethod
    def send(self, method: str, url: str, headers: Dict[str, str], json_body: Any | None) -> ApiResponse:
        raise NotImplementedError
