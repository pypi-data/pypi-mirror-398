"""
units_function.py
-----------------
提供 units 表的函数式 CRUD API，风格参考 tag_function.py。
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

# ======================= 数据结构 =======================
@dataclass(slots=True)
class UnitInfo:
	unit_id: Optional[int] = None
	unit_name: str = ""
	unit_name_zh: str = ""
	description: Optional[Dict] = field(default_factory=dict)
	created_at: Optional[datetime] = None
	updated_at: Optional[datetime] = None

	def __repr__(self):
		return f"UnitInfo(unit_id={self.unit_id}, unit_name='{self.unit_name}', unit_name_zh='{self.unit_name_zh}')"

# OperationResult 统一迁移至 db_utils.OperationResult[T]

@dataclass(slots=True)
class UnitsFilter:
	ids: Optional[Sequence[int]] = None
	names: Optional[Sequence[str]] = None
	limit: Optional[int] = None
	offset: Optional[int] = None
	order_by: str = "unit_id"

# ======================= 内部工具 =======================
_UNIT_SELECT_COLUMNS = (
	"unit_id, unit_name, unit_name_zh, description, created_at, updated_at"
)

def _row_to_unitinfo(row) -> UnitInfo:
	return UnitInfo(
		unit_id=row[0],
		unit_name=row[1],
		unit_name_zh=row[2],
	description=parse_json_field(row[3], fallback_key="desc"),
		created_at=row[4],
		updated_at=row[5],
	)

def _validate_unit_name(name: str) -> tuple[bool, str]:
	if name is None:
		return False, "unit_name 不能为空"
	name2 = name.strip()
	if not name2:
		return False, "unit_name 去除空白后为空"
	if len(name2) > 255:
		return False, "unit_name 过长(>255)"
	return True, ""

# ======================= 查询 =======================
def get_units(
	conn: psycopg.Connection,
	flt: UnitsFilter,
) -> List[UnitInfo]:
	where: List[str] = []
	params: List = []
	if flt.ids:
		where.append("unit_id = ANY(%s)")
		params.append(list({int(i) for i in flt.ids}))
	if flt.names:
		where.append("unit_name = ANY(%s)")
		params.append(list({str(n) for n in flt.names}))
	where_sql = ("WHERE " + " AND ".join(where)) if where else ""
	order_sql = "unit_id" if flt.order_by not in {"unit_id", "unit_name"} else flt.order_by
	limit_sql = ""
	if flt.limit is not None:
		limit_sql += " LIMIT %s"
		params.append(flt.limit)
	if flt.offset is not None:
		limit_sql += " OFFSET %s"
		params.append(flt.offset)
	sql = f"SELECT {_UNIT_SELECT_COLUMNS} FROM public.units {where_sql} ORDER BY {order_sql}{limit_sql}"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			rows = cur.fetchall()
		rst = [_row_to_unitinfo(r) for r in rows]
		logger.debug(f"get_units 返回 {len(rst)} 条记录")
		return rst
	except Exception:
		logger.error(f"get_units 失败:\n{traceback.format_exc()}")
		return []

def get_unit(
	conn: psycopg.Connection,
	*,
	unit_id: Optional[int] = None,
	unit_name: Optional[str] = None,
) -> Optional[UnitInfo]:
	flt = UnitsFilter(ids=[unit_id] if unit_id is not None else None, names=[unit_name] if unit_name else None, limit=1)
	res = get_units(conn, flt)
	return res[0] if res else None

def get_all_units(
	conn: psycopg.Connection,
) -> List[UnitInfo]:
	return get_units(conn, UnitsFilter())

def resolve_unit_ids(
	conn: psycopg.Connection,
	names: Sequence[str],
) -> List[Optional[int]]:
	if not names:
		return []
	rows = get_units(conn, UnitsFilter(names=names))
	mapping = {u.unit_name: u.unit_id for u in rows if u.unit_id is not None}
	return [mapping.get(n) for n in names]

# ======================= 新增 =======================
def insert_new_unit(
	conn: psycopg.Connection,
	unit: UnitInfo,
	*,
	validate: bool = True,
	commit: bool = True,
) -> OperationResult[UnitInfo]:
	if validate:
		ok, msg = _validate_unit_name(unit.unit_name)
		if not ok:
			return OperationResult(False, error=msg)
		unit.unit_name = unit.unit_name.strip()

	sql = (
		"INSERT INTO public.units (unit_name, unit_name_zh, description) "
		"VALUES (%s,%s,%s) RETURNING unit_id, created_at, updated_at"
	)
	params = (
		unit.unit_name,
		unit.unit_name_zh,
		to_json_field(unit.description),
	)
	try:
		with conn.cursor() as cur:
			cur.execute(sql, params)
			row = cur.fetchone()
		if not row:
			logger.warning("插入失败: 未返回 unit_id")
			return OperationResult(False, error="插入失败: 未返回 unit_id")
		unit.unit_id, unit.created_at, unit.updated_at = row
		if commit:
			commit_if_needed(conn)
		logger.info(f"插入单位成功: {unit.unit_name} id={unit.unit_id}")
		return OperationResult(True, affected=1, data=unit)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"insert_new_unit 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

# ======================= 更新 =======================
_UNIT_JSON_FIELDS = {"description"}
_UNIT_UPDATABLE_FIELDS = _UNIT_JSON_FIELDS | {"unit_name", "unit_name_zh"}

def update_unit_fields(
	conn: psycopg.Connection,
	unit_id: int,
	updates: Dict[str, Union[str, Dict, None]],
	*,
	commit: bool = True,
) -> OperationResult[UnitInfo]:
	if not updates:
		return OperationResult(False, error="未指定需更新字段")
	filtered = {k: v for k, v in updates.items() if k in _UNIT_UPDATABLE_FIELDS}
	if not filtered:
		return OperationResult(False, error="没有可更新字段")

	set_parts: List[str] = []
	params: List = []
	for k, v in filtered.items():
		if k in _UNIT_JSON_FIELDS:
			if v is None:
				params.append(None)
			elif isinstance(v, dict):
				params.append(to_json_field(v))
			else:
				if isinstance(v, str):
					params.append(to_json_field(parse_json_field(v, fallback_key="desc")))
				else:
					return OperationResult(False, error=f"字段 {k} 仅支持 dict/None/str")
		else:
			params.append(v)
		set_parts.append(f"{k}=%s")

	set_parts.append("updated_at=now()")
	sql = f"UPDATE public.units SET {', '.join(set_parts)} WHERE unit_id=%s RETURNING {_UNIT_SELECT_COLUMNS}"
	params.append(unit_id)

	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到单位")
		if commit:
			commit_if_needed(conn)
		info = _row_to_unitinfo(row)
		logger.info(f"更新单位成功: id={unit_id}")
		return OperationResult(True, affected=1, data=info)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"update_unit_fields 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

# ======================= 删除 =======================
def delete_unit(
	conn: psycopg.Connection,
	unit_id: int,
	*,
	commit: bool = True,
) -> OperationResult[int]:
	sql = "DELETE FROM public.units WHERE unit_id=%s RETURNING unit_id"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, (unit_id,))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到单位")
		if commit:
			commit_if_needed(conn)
		logger.info(f"删除单位成功: id={unit_id}")
		return OperationResult(True, affected=1, data=unit_id)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"delete_unit 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")


