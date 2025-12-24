from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def retry_call(fn: Callable[[], T], max_attempts: int, interval_ms: int) -> T:
    attempt = 0
    last_error: Exception | None = None
    while attempt < max_attempts:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # pragma: no cover - passthrough for network/SDK errors
            last_error = exc
            if attempt >= max_attempts:
                raise
            if interval_ms > 0:
                time.sleep(interval_ms / 1000)
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_call 未執行任何嘗試")
