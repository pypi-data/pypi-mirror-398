from datetime import datetime
from typing import Optional, Any, Dict, Generic, TypeVar
from dataclasses import dataclass
import json
import psycopg
from psycopg.types.json import Json


def commit_if_needed(conn: psycopg.Connection) -> None:
    if not conn.autocommit:
        conn.commit()

def rollback_silent(conn: psycopg.Connection) -> None:
    if not conn.autocommit:
        try:
            conn.rollback()
        except Exception:
            pass

def parse_json_field(raw: Any, *, fallback_key: str = "desc") -> Dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {fallback_key: raw}
    return {"value": raw}

def to_json_field(value: Optional[Dict]) -> Optional[Json]:
    if value is None:
        return None
    return Json(value)

def normalize_write_time(write_time: Optional[datetime | int | float]) -> datetime:
    # 获取本地时区
    local_tz = datetime.now().astimezone().tzinfo

    if write_time is None:
        result = datetime.now(local_tz)
    elif isinstance(write_time, (int, float)):
        result = datetime.fromtimestamp(write_time, tz=local_tz)
    elif isinstance(write_time, datetime):
        # 如果已有 tzinfo，转换到本地时区；否则假定是 naive 本地时间
        if write_time.tzinfo is None:
            result = write_time.replace(tzinfo=local_tz)
        else:
            result = write_time.astimezone(local_tz)
    else:
        raise TypeError(f"Unsupported write_time type: {type(write_time)}")

    return result.replace(microsecond=0)

# ---------------- Result Types ----------------
T = TypeVar("T")

@dataclass(slots=True)
class OperationResult(Generic[T]):
    ok: bool
    affected: int = 0
    data: Optional[T] = None
    error: str = ""