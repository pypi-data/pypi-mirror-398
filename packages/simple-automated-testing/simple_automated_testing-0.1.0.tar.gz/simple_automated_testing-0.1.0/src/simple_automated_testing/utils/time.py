from __future__ import annotations

from datetime import datetime, timezone
import uuid


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return str(uuid.uuid4())
