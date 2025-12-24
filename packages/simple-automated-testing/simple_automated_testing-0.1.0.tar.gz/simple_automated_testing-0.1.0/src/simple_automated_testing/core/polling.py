from __future__ import annotations

import time
from typing import Callable, Tuple, TypeVar


T = TypeVar("T")


def wait_until(
    fn: Callable[[], T],
    condition: Callable[[T], bool],
    interval_ms: int,
    timeout_ms: int | None = None,
    max_attempts: int | None = None,
) -> Tuple[bool, int, T | None]:
    attempts = 0
    start = time.time()
    last_result: T | None = None

    while True:
        attempts += 1
        last_result = fn()
        if condition(last_result):
            return True, attempts, last_result
        if max_attempts is not None and attempts >= max_attempts:
            return False, attempts, last_result
        if timeout_ms is not None and (time.time() - start) * 1000 >= timeout_ms:
            return False, attempts, last_result
        if interval_ms > 0:
            time.sleep(interval_ms / 1000)
