from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPORT_DIR = "report"
DEFAULT_FILE_NAME = "human-report.html"


def resolve_report_path(output_dir: str | None, file_name: str | None, base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    target_dir = _resolve_output_dir(output_dir, base)
    normalized_name = _normalize_file_name(file_name)
    return _ensure_unique_path(target_dir / normalized_name)


def _resolve_output_dir(output_dir: str | None, base: Path) -> Path:
    if output_dir:
        raw_dir = Path(output_dir).expanduser()
        if not raw_dir.is_absolute():
            raw_dir = base / raw_dir
    else:
        raw_dir = base / DEFAULT_REPORT_DIR

    target_dir = raw_dir.resolve()
    if target_dir.exists() and not target_dir.is_dir():
        raise ValueError(f"報告資料夾不是目錄：{target_dir}")

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"無法建立或存取報告資料夾：{target_dir}") from exc

    return target_dir


def _normalize_file_name(file_name: str | None) -> str:
    if file_name is None or not str(file_name).strip():
        return DEFAULT_FILE_NAME
    return Path(str(file_name)).name


def _ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stem = path.stem or "human-report"
    suffix = path.suffix
    candidate = path.with_name(f"{stem}-{stamp}{suffix}")
    if not candidate.exists():
        return candidate

    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{stem}-{stamp}-{counter}{suffix}")
        counter += 1
    return candidate
