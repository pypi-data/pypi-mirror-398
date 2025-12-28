"""
metrics_function.py
-------------------
提供 metrics 表的函数式 CRUD API，风格参考 tag_function.py。
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
class MetricsInfo:
	metric_id: Optional[int] = None
	metric_name: str = ""
	metric_name_zh: str = ""
	unit_id: Optional[int] = None
	description: Optional[Dict] = field(default_factory=dict)
	created_at: Optional[datetime] = None
	updated_at: Optional[datetime] = None

	def __repr__(self):
		return f"MetricsInfo(metric_id={self.metric_id}, metric_name='{self.metric_name}', unit_id={self.unit_id})"

# OperationResult 统一迁移至 db_utils.OperationResult[T]

@dataclass(slots=True)
class MetricsFilter:
	ids: Optional[Sequence[int]] = None
	names: Optional[Sequence[str]] = None
	unit_ids: Optional[Sequence[int]] = None
	limit: Optional[int] = None
	offset: Optional[int] = None
	order_by: str = "metric_id"

# ======================= 内部工具 =======================
_METRIC_SELECT_COLUMNS = (
	"metric_id, metric_name, metric_name_zh, unit_id, description, created_at, updated_at"
)

def _row_to_metricsinfo(row) -> MetricsInfo:
	return MetricsInfo(
		metric_id=row[0],
		metric_name=row[1],
		metric_name_zh=row[2],
		unit_id=row[3],
		description=parse_json_field(row[4], fallback_key="desc"),
		created_at=row[5],
		updated_at=row[6],
	)

def _validate_metric_name(name: str) -> tuple[bool, str]:
	if name is None:
		return False, "metric_name 不能为空"
	name2 = name.strip()
	if not name2:
		return False, "metric_name 去除空白后为空"
	if len(name2) > 255:
		return False, "metric_name 过长(>255)"
	return True, ""

# ======================= 查询 =======================
def get_metrics(
	conn: psycopg.Connection,
	flt: MetricsFilter,
) -> List[MetricsInfo]:
	where: List[str] = []
	params: List = []
	if flt.ids:
		where.append("metric_id = ANY(%s)")
		params.append(list({int(i) for i in flt.ids}))
	if flt.names:
		where.append("metric_name = ANY(%s)")
		params.append(list({str(n) for n in flt.names}))
	if flt.unit_ids:
		where.append("unit_id = ANY(%s)")
		params.append(list({int(i) for i in flt.unit_ids}))
	where_sql = ("WHERE " + " AND ".join(where)) if where else ""
	order_sql = "metric_id" if flt.order_by not in {"metric_id", "metric_name"} else flt.order_by
	limit_sql = ""
	if flt.limit is not None:
		limit_sql += " LIMIT %s"
		params.append(flt.limit)
	if flt.offset is not None:
		limit_sql += " OFFSET %s"
		params.append(flt.offset)
	sql = f"SELECT {_METRIC_SELECT_COLUMNS} FROM public.metrics {where_sql} ORDER BY {order_sql}{limit_sql}"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			rows = cur.fetchall()
		rst = [_row_to_metricsinfo(r) for r in rows]
		logger.debug(f"get_metrics 返回 {len(rst)} 条记录")
		return rst
	except Exception:
		logger.error(f"get_metrics 失败:\n{traceback.format_exc()}")
		return []

def get_metric(
	conn: psycopg.Connection,
	*,
	metric_id: Optional[int] = None,
	metric_name: Optional[str] = None,
) -> Optional[MetricsInfo]:
	flt = MetricsFilter(ids=[metric_id] if metric_id is not None else None, names=[metric_name] if metric_name else None, limit=1)
	res = get_metrics(conn, flt)
	return res[0] if res else None

def get_all_metrics(
	conn: psycopg.Connection,
) -> List[MetricsInfo]:
	return get_metrics(conn, MetricsFilter())

def resolve_metric_ids(
	conn: psycopg.Connection,
	names: Sequence[str],
) -> List[Optional[int]]:
	if not names:
		return []
	rows = get_metrics(conn, MetricsFilter(names=names))
	mapping = {m.metric_name: m.metric_id for m in rows if m.metric_id is not None}
	return [mapping.get(n) for n in names]

# ======================= 新增 =======================
def insert_new_metric(
	conn: psycopg.Connection,
	metric: MetricsInfo,
	*,
	validate: bool = True,
	commit: bool = True,
) -> OperationResult[MetricsInfo]:
	if validate:
		ok, msg = _validate_metric_name(metric.metric_name)
		if not ok:
			return OperationResult(False, error=msg)
		metric.metric_name = metric.metric_name.strip()

	sql = (
		"INSERT INTO public.metrics (metric_name, metric_name_zh, unit_id, description) "
		"VALUES (%s,%s,%s,%s) RETURNING metric_id, created_at, updated_at"
	)
	params = (
		metric.metric_name,
		metric.metric_name_zh,
		metric.unit_id,
		to_json_field(metric.description),
	)
	try:
		with conn.cursor() as cur:
			cur.execute(sql, params)
			row = cur.fetchone()
		if not row:
			logger.warning("插入失败: 未返回 metric_id")
			return OperationResult(False, error="插入失败: 未返回 metric_id")
		metric.metric_id, metric.created_at, metric.updated_at = row
		if commit:
			commit_if_needed(conn)
		logger.info(f"插入指标成功: {metric.metric_name} id={metric.metric_id}")
		return OperationResult(True, affected=1, data=metric)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"insert_new_metric 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

# ======================= 更新 =======================
_METRIC_JSON_FIELDS = {"description"}
_METRIC_UPDATABLE_FIELDS = _METRIC_JSON_FIELDS | {"metric_name", "metric_name_zh", "unit_id"}

def update_metric_fields(
	conn: psycopg.Connection,
	metric_id: int,
	updates: Dict[str, Union[str, int, Dict, None]],
	*,
	commit: bool = True,
) -> OperationResult[MetricsInfo]:
	if not updates:
		return OperationResult(False, error="未指定需更新字段")
	filtered = {k: v for k, v in updates.items() if k in _METRIC_UPDATABLE_FIELDS}
	if not filtered:
		return OperationResult(False, error="没有可更新字段")

	set_parts: List[str] = []
	params: List = []
	for k, v in filtered.items():
		if k in _METRIC_JSON_FIELDS:
			if v is None:
				params.append(None)
			elif isinstance(v, dict):
				params.append(to_json_field(v))
			else:
				# 允许传入 str：尝试解析为 json，否则作为描述包装
				if isinstance(v, str):
					params.append(to_json_field(parse_json_field(v, fallback_key="desc")))
				else:
					return OperationResult(False, error=f"字段 {k} 仅支持 dict/None/str")
		else:
			params.append(v)
		set_parts.append(f"{k}=%s")

	set_parts.append("updated_at=now()")
	sql = f"UPDATE public.metrics SET {', '.join(set_parts)} WHERE metric_id=%s RETURNING {_METRIC_SELECT_COLUMNS}"
	params.append(metric_id)

	try:
		with conn.cursor() as cur:
			cur.execute(sql, tuple(params))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到指标")
		if commit:
			commit_if_needed(conn)
		info = _row_to_metricsinfo(row)
		logger.info(f"更新指标成功: id={metric_id}")
		return OperationResult(True, affected=1, data=info)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"update_metric_fields 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

# ======================= 删除 =======================
def delete_metric(
	conn: psycopg.Connection,
	metric_id: int,
	*,
	commit: bool = True,
) -> OperationResult[int]:
	sql = "DELETE FROM public.metrics WHERE metric_id=%s RETURNING metric_id"
	try:
		with conn.cursor() as cur:
			cur.execute(sql, (metric_id,))
			row = cur.fetchone()
		if not row:
			return OperationResult(False, error="未找到指标")
		if commit:
			commit_if_needed(conn)
		logger.info(f"删除指标成功: id={metric_id}")
		return OperationResult(True, affected=1, data=metric_id)
	except Exception:
		if commit:
			rollback_silent(conn)
		logger.error(f"delete_metric 异常:\n{traceback.format_exc()}")
		return OperationResult(False, error="异常: 请查看日志")

