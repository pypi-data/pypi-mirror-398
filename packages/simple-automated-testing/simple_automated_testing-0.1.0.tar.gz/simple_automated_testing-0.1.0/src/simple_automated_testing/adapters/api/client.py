from __future__ import annotations

from typing import Any, Dict

import httpx

from simple_automated_testing.adapters.api.interface import ApiClient
from simple_automated_testing.contracts.transport import ApiResponse


class HttpxApiClient(ApiClient):
    def __init__(self, timeout_ms: int) -> None:
        self._timeout = timeout_ms / 1000

    def send(self, method: str, url: str, headers: Dict[str, str], json_body: Any | None) -> ApiResponse:
        response = httpx.request(method, url, headers=headers, json=json_body, timeout=self._timeout)
        content_type = response.headers.get("content-type")
        return ApiResponse(
            status=response.status_code,
            headers={k.lower(): v for k, v in response.headers.items()},
            body_bytes=response.content,
            content_type=content_type,
        )
