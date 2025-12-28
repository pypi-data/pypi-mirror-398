"""
source_function.py
------------------
提供 source 表的函数式 CRUD API，风格对齐 tag_function.py。
"""

from datetime import datetime
from tsdbpy import logger
import traceback
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Sequence
import psycopg
from tsdbpy.db_utils import (
	commit_if_needed, rollback_silent, parse_json_field, to_json_field, OperationResult
)

# ======================= 枚举定义 =======================
from enum import Enum
class SourceStatus(Enum):
	ACTIVE = "ACTIVE"
	INACTIVE = "INACTIVE"
	DISABLED = "DISABLED"

class SourceProtocol(Enum):
	OPC_UA = "OPC-UA"
	OPC_DA = "OPC-DA"
	MODBUS = "MODBUS"

def to_status_enum(status: Union[SourceStatus, str, int, None]) -> Optional[str]:
	if status is None:
		return None
	if isinstance(status, SourceStatus):
		return status.value
	elif isinstance(status, str):
		valid = [s.value for s in SourceStatus]
		return status if status in valid else None
	elif isinstance(status, int):
		if status == 1:
			return SourceStatus.ACTIVE.value
		elif status == 0:
			return SourceStatus.INACTIVE.value
		elif status == -1:
			return SourceStatus.DISABLED.value
		else:
			return SourceStatus.ACTIVE.value
	return None

def from_status_enum(status_str: Optional[str]) -> Optional[SourceStatus]:
	if not status_str:
		return None
	try:
		return SourceStatus(status_str)
	except ValueError:
		return None

def to_protocol_enum(protocol: Union[SourceProtocol, str, int, None]) -> Optional[str]:
	if protocol is None:
		return None
	if isinstance(protocol, SourceProtocol):
		return protocol.value
	elif isinstance(protocol, str):
		valid = [p.value for p in SourceProtocol]
		return protocol if protocol in valid else None
	elif isinstance(protocol, int):
		if protocol == 1:
			return SourceProtocol.OPC_UA.value
		elif protocol == 2:
			return SourceProtocol.OPC_DA.value
		elif protocol == 3:
			return SourceProtocol.MODBUS.value
		else:
			return SourceProtocol.OPC_UA.value
	return None

def from_protocol_enum(protocol_str: Optional[str]) -> Optional[SourceProtocol]:
	if not protocol_str:
		return None
	try:
		return SourceProtocol(protocol_str)
	except ValueError:
		return None

# ======================= 数据结构 =======================
@dataclass(slots=True)
class SourceInfo:
	source_id: Optional[int] = None
	source_name: str = ""
	source_type: str = ""
	interval_msec: int = 1000
	status: SourceStatus = SourceStatus.ACTIVE
	protocol: Optional[SourceProtocol] = None
	endpoint: str = ""
	auth_config: Optional[Dict] = field(default_factory=dict)
	conn_policy: Optional[Dict] = field(default_factory=dict)
	description: Optional[Dict] = field(default_factory=dict)
	created_at: Optional[datetime] = None
	updated_at: Optional[datetime] = None

	def __repr__(self):
		return f"SourceInfo(source_id={self.source_id}, source_name='{self.source_name}', type='{self.source_type}')"

# ======================= 统一结果/过滤结构 =======================

@dataclass(slots=True)
class SourceFilter:
	ids: Optional[Sequence[int]] = None
	names: Optional[Sequence[str]] = None
	status: Optional[Sequence[Union[SourceStatus, str]]] = None
	protocol: Optional[Sequence[Union[SourceProtocol, str]]] = None
	limit: Optional[int] = None
	offset: Optional[int] = None
	order_by: str = "source_id"

# ======================= 内部工具 =======================
_SOURCE_SELECT_COLUMNS = (
	"source_id, source_name, source_type, interval_msec, status, protocol, endpoint, "
	"auth_config, conn_policy, created_at, updated_at, description"
)

def _row_to_sourceinfo(row) -> SourceInfo:
	return SourceInfo(
		source_id=row[0],
		source_name=row[1],
		source_type=row[2],
		interval_msec=row[3],
		status=from_status_enum(row[4]),
		protocol=from_protocol_enum(row[5]),
		endpoint=row[6],
	auth_config=parse_json_field(row[7], fallback_key="value"),
	conn_policy=parse_json_field(row[8], fallback_key="value"),
		created_at=row[9],
		updated_at=row[10],
	description=parse_json_field(row[11], fallback_key="value"),
	)

def _validate_source_name(name: str) -> tuple[bool, str]:
	if name is None:
		return False, "source_name 不能为空"
	name2 = name.strip()
	if not name2:
		return False, "source_name 去除空白后为空"
	if len(name2) > 255:
		return False, "source_name 过长(>255)"
	return True, ""

# ======================= 查询 =======================
def get_sources(
	conn: psycopg.Connection,
	flt: SourceFilter,
) -> List[SourceInfo]:
	where: List[str] = []
	params: List = []
	if flt.ids:
		where.append("source_id = ANY(%s)")
		params.append(list({int(i) for i in flt.ids}))
	if flt.names:
		where.append("source_name = ANY(%s)")
		params.append(list({str(n) for n in flt.names}))
	if flt.status:
		status_vals = [to_status_enum(s) for s in flt.status if to_status_enum(s) is not None]
		if status_vals:
			where.append("status = ANY(%s)")
			params.append(status_vals)
	if flt.protocol:
		proto_vals = [to_protocol_enum(p) for p in flt.protocol if to_protocol_enum(p) is not None]
		if proto_vals:
			where.append("protocol = ANY(%s)")
			params.append(proto_vals)
	where_sql = ("WHERE " + " AND ".join(where)) if where else ""
	order_sql = "source_id" if flt.order_by not in {"source_id", "source_name"} else flt.order_by
	limit_sql = ""
	if flt.limit is not None:
		limit_sql += " LIMIT %s"
		params.append(flt.limit)
	if flt.offset is not None:
		limit_sql += " OFFSET %s"
		params.append(flt.offset)
	sql = f"SELECT {_SOURCE_SELECT_COLUMNS} FROM public.sources {where_sql} ORDER BY {order_sql}{limit_sql}"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			rows = cur.fetchall()
		rst = [_row_to_sourceinfo(r) for r in rows]
		logger.debug(f"get_sources 返回 {len(rst)} 条记录")
		return rst
	except Exception:
		logger.error(f"get_sources 失败:\n{traceback.format_exc()}")
		return []

def get_source(
	conn: psycopg.Connection,
	*,
	source_id: Optional[int] = None,
	source_name: Optional[str] = None,
) -> Optional[SourceInfo]:
	flt = SourceFilter(ids=[source_id] if source_id is not None else None, names=[source_name] if source_name else None, limit=1)
	res = get_sources(conn, flt)
	return res[0] if res else None

def get_all_sources(
	conn: psycopg.Connection,
) -> List[SourceInfo]:
	return get_sources(conn, SourceFilter())

def resolve_source_ids(
	conn: psycopg.Connection,
	names: Sequence[str],
) -> List[Optional[int]]:
	if not names:
		return []
	rows = get_sources(conn, SourceFilter(names=names))
	mapping = {s.source_name: s.source_id for s in rows if s.source_id is not None}
	return [mapping.get(n) for n in names]

# ======================= 新增 =======================
def insert_new_source(
	conn: psycopg.Connection,
	source: SourceInfo,
	*,
	validate: bool = True,
	commit: bool = True,
) -> OperationResult[SourceInfo]:
	if validate:
		ok, msg = _validate_source_name(source.source_name)
		if not ok:
			return OperationResult(False, error=msg)
		source.source_name = source.source_name.strip()

	sql = (
		"INSERT INTO public.sources (source_name, source_type, interval_msec, status, protocol, endpoint, "
		"auth_config, conn_policy, description) "
		"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING source_id, created_at, updated_at"
	)
	params = (
		source.source_name,
		source.source_type,
		source.interval_msec,
		to_status_enum(source.status),
		to_protocol_enum(source.protocol),
		source.endpoint,
		to_json_field(source.auth_config),
		to_json_field(source.conn_policy),
		to_json_field(source.description),
	)
	try:
		with conn.cursor() as cur:
			cur.execute(sql, params)
			row = cur.fetchone()
		if not row:
			logger.warning("插入失败: 未返回 source_id")
			return OperationResult(False, error="插入失败: 未返回 source_id")
		source.source_id, source.created_at, source.updated_at = row
		if commit:
			commit_if_needed(conn)
		logger.info(f"插入数据源成功: {source.source_name} id={source.source_id}")
		return OperationResult(True, affected=1, data=source)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"insert_new_source 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

# ======================= 更新 =======================
_SOURCE_JSON_FIELDS = {"auth_config", "conn_policy", "description"}
_SOURCE_ENUM_STATUS = "status"
_SOURCE_ENUM_PROTOCOL = "protocol"
_SOURCE_UPDATABLE_FIELDS = _SOURCE_JSON_FIELDS | {"source_type", "interval_msec", "endpoint", "source_name", _SOURCE_ENUM_STATUS, _SOURCE_ENUM_PROTOCOL}

def update_source_fields(
	conn: psycopg.Connection,
	source_id: int,
	updates: Dict[str, Union[str, int, Dict, SourceStatus, SourceProtocol, None]],
	*,
	commit: bool = True,
) -> OperationResult[SourceInfo]:
	if not updates:
		return OperationResult(False, error="未指定需更新字段")
	filtered = {k: v for k, v in updates.items() if k in _SOURCE_UPDATABLE_FIELDS}
	if not filtered:
		return OperationResult(False, error="没有可更新字段")

	set_parts: List[str] = []
	params: List = []
	for k, v in filtered.items():
		if k in _SOURCE_JSON_FIELDS:
			if v is None:
				params.append(None)
			elif isinstance(v, dict):
				params.append(to_json_field(v))
			else:
				if isinstance(v, str):
					params.append(to_json_field(parse_json_field(v, fallback_key="value")))
				else:
					return OperationResult(False, error=f"字段 {k} 仅支持 dict/None/str")
		elif k == _SOURCE_ENUM_STATUS:
			params.append(to_status_enum(v))
		elif k == _SOURCE_ENUM_PROTOCOL:
			params.append(to_protocol_enum(v))
		else:
			params.append(v)
		set_parts.append(f"{k}=%s")

	set_parts.append("updated_at=now()")
	sql = f"UPDATE public.sources SET {', '.join(set_parts)} WHERE source_id=%s RETURNING {_SOURCE_SELECT_COLUMNS}"
	params.append(source_id)

	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到数据源")
		if commit:
			commit_if_needed(conn)
		info = _row_to_sourceinfo(row)
		logger.info(f"更新数据源成功: id={source_id}")
		return OperationResult(True, affected=1, data=info)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"update_source_fields 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

def set_source_status(
	conn: psycopg.Connection,
	source_id: int,
	status: Union[SourceStatus, str, int],
	*,
	commit: bool = True,
) -> OperationResult[SourceInfo]:
	return update_source_fields(conn, source_id, {"status": status}, commit=commit)

# ======================= 删除 =======================
def delete_source(
	conn: psycopg.Connection,
	source_id: int,
	*,
	commit: bool = True,
) -> OperationResult[int]:
	sql = "DELETE FROM public.sources WHERE source_id=%s RETURNING source_id"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, (source_id,))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到数据源")
		if commit:
			commit_if_needed(conn)
		logger.info(f"删除数据源成功: id={source_id}")
		return OperationResult(True, affected=1, data=source_id)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"delete_source 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

