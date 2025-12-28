from datetime import datetime
from tsdbpy import logger
import re
import traceback
from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Union, Sequence
import psycopg
from psycopg import errors
from tsdbpy.db_utils import (
    commit_if_needed, rollback_silent, parse_json_field, to_json_field, OperationResult
)

# ---------------- 常量与数据结构 ----------------
_TAG_SELECT_COLUMNS = (
    "tag_id, tag_name, metric_id, positive_error, negative_error, source_id, "
    "source_tagname, description, created_at, updated_at, is_deleted"
)

@dataclass(slots=True)
class TagInfo:
    # 通过 metadata 标记哪些字段允许在 update 接口中被修改
    tag_id: Optional[int] = field(default=None)  # 主键不可修改
    tag_name: str = field(default="")           # 名称不可在此接口中修改（如需改名应走新流程）
    metric_id: Optional[int] = field(default=None, metadata={"updatable": True})
    positive_error: Optional[float] = field(default=None, metadata={"updatable": True})
    negative_error: Optional[float] = field(default=None, metadata={"updatable": True})
    source_id: Optional[int] = field(default=None, metadata={"updatable": True})
    source_tagname: Optional[str] = field(default=None, metadata={"updatable": True})
    description: Optional[Dict] = field(default_factory=dict, metadata={"updatable": True})
    created_at: Optional[datetime] = field(default=None)  # 只读
    updated_at: Optional[datetime] = field(default=None)  # 只读
    is_deleted: bool = field(default=False, metadata={"updatable": True})

    def __repr__(self) -> str:  # 简洁 repr 便于日志
        return f"TagInfo(tag_id={self.tag_id}, tag_name='{self.tag_name}', source_id={self.source_id})"

    def __str__(self) -> str:
        parts = [
            f"TagInfo(",
            f"  tag_id        = {self.tag_id}",
            f"  tag_name      = '{self.tag_name}'",
            f"  metric_id     = {self.metric_id}",
            f"  pos_error     = {self.positive_error}",
            f"  neg_error     = {self.negative_error}",
            f"  source_id     = {self.source_id}",
            f"  source_tag    = '{self.source_tagname}'",
            f"  description   = {self.description or '{}'}",
            f"  created_at    = {self.created_at.isoformat() if self.created_at else None}",
            f"  updated_at    = {self.updated_at.isoformat() if self.updated_at else None}",
            f"  is_deleted    = {self.is_deleted}",
            f")"
        ]
        return "\n".join(parts)

def validate_tag_name(tag_name: str) -> tuple[bool, str]:
    """校验 tag_name（数据库字段已为 text，放宽原 ltree 限制）
    规则（可按需调整）：
    1. 非空（去除首尾空白后）
    2. 长度 <= 1024
    3. 不含控制字符
    """
    if tag_name is None:
        return False, "标签名不能为空"
    name = tag_name.strip()
    if not name:
        return False, "标签名去除首尾空白后为空"
    if len(name) > 1024:
        return False, "标签名过长（超过1024字符）"
    if re.search(r"[\x00-\x1F\x7F]", name):
        return False, "标签名包含控制字符"
    return True, ""

# ======================= 统一结果/过滤结构 =======================
# OperationResult 统一迁移至 db_utils.OperationResult[T]


@dataclass(slots=True)
class TagFilter:
    names: Optional[Sequence[str]] = None
    ids: Optional[Sequence[int]] = None
    source_id: Optional[int] = None
    include_deleted: bool = True
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: str = "tag_id"  # 或 tag_name

TAG_UPDATABLE_FIELDS = frozenset(
    f.name for f in fields(TagInfo) if f.metadata.get("updatable")
)

def list_tag_updatable_fields() -> List[str]:
    """返回允许通过 update_tag_fields 更新的字段列表(按名称排序)。"""
    return sorted(TAG_UPDATABLE_FIELDS)

def is_tag_field_updatable(field_name: str) -> bool:
    """判断给定字段是否允许被 update_tag_fields 修改。"""
    return field_name in TAG_UPDATABLE_FIELDS

def _row_to_taginfo(row) -> TagInfo:
    return TagInfo(
        tag_id=row[0], tag_name=row[1], metric_id=row[2], positive_error=row[3], negative_error=row[4],
    source_id=row[5], source_tagname=row[6], description=parse_json_field(row[7], fallback_key="desc"),
        created_at=row[8], updated_at=row[9], is_deleted=row[10]
    )
    
def get_tags(
    conn: psycopg.Connection,
    flt: TagFilter,
) -> List[TagInfo]:
    """
    返回满足过滤条件的标签列表。
    注意: names / ids 使用 set 去重后顺序丢失，最终结果顺序由 order_by 决定。
    """
    where: List[str] = []
    params: List = []
    if flt.ids:
        where.append("tag_id = ANY(%s)")
        params.append(list({int(i) for i in flt.ids}))
    if flt.names:
        where.append("tag_name = ANY(%s)")
        params.append(list({str(n) for n in flt.names}))
    if flt.source_id is not None:
        where.append("source_id = %s")
        params.append(flt.source_id)
    if not flt.include_deleted:
        where.append("is_deleted = FALSE")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = "tag_id" if flt.order_by not in {"tag_id", "tag_name"} else flt.order_by
    limit_sql = ""
    if flt.limit is not None:
        limit_sql += " LIMIT %s"
        params.append(flt.limit)
    if flt.offset is not None:
        limit_sql += " OFFSET %s"
        params.append(flt.offset)
    sql = f"SELECT {_TAG_SELECT_COLUMNS} FROM public.tags {where_sql} ORDER BY {order_sql}{limit_sql}"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
        rst =  [_row_to_taginfo(r) for r in rows]
        logger.debug(f"get_tags 返回 {len(rst)} 条记录")
        return rst
    except Exception:
        logger.error(f"get_tags 失败:\n{traceback.format_exc()}")
        return []

def get_tag(
    conn: psycopg.Connection,
    *,
    tag_id: Optional[int] = None,
    tag_name: Optional[str] = None,
) -> Optional[TagInfo]:
    flt = TagFilter(ids=[tag_id] if tag_id is not None else None, names=[tag_name] if tag_name else None, limit=1)
    res = get_tags(conn, flt)
    return res[0] if res else None

def get_all_tags(
    conn: psycopg.Connection,
    *,
    include_deleted: bool = True,
) -> List[TagInfo]:
    """获取全部标签的便捷封装。"""
    flt = TagFilter(include_deleted=include_deleted)
    return get_tags(conn, flt)

def resolve_tag_ids(
    conn: psycopg.Connection,
    names: Sequence[str],
) -> List[Optional[int]]:
    """按输入顺序解析 tag_name -> tag_id。

    行为变化: 不再抛出缺失异常；若某个名称未找到则在对应位置返回 None，保证
    返回列表长度与输入 names 等长且一一对应。

    参数:
        names: 需解析的标签名序列（可包含重复，结果同样按顺序/重复对齐）。
    返回:
        List[Optional[int]]: 对应 tag_id 或 None。
    """
    if not names:
            return []
    # 去重查询数据库（底层 get_tags 内部也会去重顺序不保留，这里只用来构建映射）
    tags = get_tags(conn, TagFilter(names=names, include_deleted=True))
    mapping = {t.tag_name: t.tag_id for t in tags if t.tag_id is not None}
    # 按原顺序映射，缺失填 None
    return [mapping.get(n) for n in names]

def insert_new_tag(
    conn: psycopg.Connection,
    tag: TagInfo,
    *,
    validate: bool = True,
    commit: bool = True,
) -> OperationResult[TagInfo]:
    """创建/写入单个标签（C 或 UPSERT 基础）并返回 OperationResult。

    行为:
      - validate=True 时先校验 tag_name 合法性。
      - 如果要插入的tag_name在数据库中已经存在则插入失败。
      
    返回 OperationResult:
      ok=True  -> affected=1, data=TagInfo(含回填 tag_id/created_at/updated_at)
      ok=False -> error 含原因
    """
    if validate:
        ok, msg = validate_tag_name(tag.tag_name)
        if not ok:
            logger.error(f"标签名非法: {msg}")
            return OperationResult(False, error=msg)
        tag.tag_name = tag.tag_name.strip()

    sql = (
        "INSERT INTO public.tags (tag_name, metric_id, positive_error, negative_error, source_id, "
        "source_tagname, description, is_deleted) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
        "RETURNING tag_id, created_at, updated_at"
    )

    params = (
        tag.tag_name,
        tag.metric_id,
        tag.positive_error,
        tag.negative_error,
        tag.source_id,
        tag.source_tagname,
        to_json_field(tag.description),  # 保留空 dict
        tag.is_deleted,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        if not row:
            logger.warning("插入失败: 未返回 tag_id")
            return OperationResult(False, error="插入失败: 未返回 tag_id")
        tag.tag_id, tag.created_at, tag.updated_at = row
        if commit:
            commit_if_needed(conn)
        logger.info(f"插入标签成功: {tag.tag_name} id={tag.tag_id}")
        return OperationResult(True, affected=1, data=tag)
    except errors.UniqueViolation:
        if commit:
            rollback_silent(conn)
        logger.info(f"insert_new_tag 冲突: tag_name={tag.tag_name}")
        return OperationResult(False, error="标签已存在")
    except Exception:
        if commit:
            rollback_silent(conn)
        logger.error(f"insert_new_tag 异常:\n{traceback.format_exc()}")
        return OperationResult(False, error="异常: 请查看日志")

def update_tag_fields(
    conn: psycopg.Connection,
    tag_name: str,
    updates: Dict[str, Union[str, int, float, bool, Dict, None]],
    *,
    commit: bool = True,
) -> OperationResult[TagInfo]:
    """按字段更新（只允许 TAG_UPDATABLE_FIELDS 集合内的字段）。
    
    特性:
      - 传入的字段名若不在允许集合中将被忽略。
      - 值可为 None；当值为 None 时对应列将被更新为 NULL。
      - description:
          * 若传入为 dict，则序列化为 JSON。
          * 若传入为字符串，原样写入（调用方应自行保证格式一致性）。
          * 若传入为 None，则置为 NULL。
    返回:
      OperationResult (data 为更新后的 TagInfo)。
    """
    if not updates:
        return OperationResult(False, error="未指定需更新字段")

    # 保留值为 None 的字段（表示置 NULL），仅过滤不允许的字段
    filtered: Dict[str, Union[str, int, float, bool, Dict, None]] = {
        k: v for k, v in updates.items() if k in TAG_UPDATABLE_FIELDS
    }
    if not filtered:
        return OperationResult(False, error="没有可更新字段")

    set_parts: List[str] = []
    params: List = []
    for k, v in filtered.items():
        if k == "description":
            # 兼容 dict/None/str 三种输入：str 会尝试解析为 JSON，失败则包一层 {"desc": v}
            if v is None:
                v = None
            elif isinstance(v, dict):
                v = to_json_field(v)
            elif isinstance(v, str):
                v = to_json_field(parse_json_field(v, fallback_key="desc"))
            else:
                return OperationResult(False, error="description 仅支持 dict/None/str")
        set_parts.append(f"{k}=%s")
        params.append(v)

    sql = (
        f"UPDATE public.tags SET {', '.join(set_parts)} "
        f"WHERE tag_name=%s RETURNING {_TAG_SELECT_COLUMNS}"
    )
    params.append(tag_name)

    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            row = cur.fetchone()
        if not row:
            logger.warning(f"更新失败: 未找到标签 {tag_name}")
            return OperationResult(False, error="未找到标签")
        if commit:
            commit_if_needed(conn)
        taginfo = _row_to_taginfo(row)
        logger.info(f"更新标签成功: {tag_name}")
        return OperationResult(True, affected=1, data=taginfo)
    except Exception:
        if commit:
            rollback_silent(conn)
        logger.error(f"update_tag_fields 异常:\n{traceback.format_exc()}")
        return OperationResult(False, error="异常: 请查看日志")
    
def update_desc(
    conn: psycopg.Connection, 
    tag_name: str, 
    new_desc: str, 
    *, 
    commit: bool = True, 
) -> OperationResult[TagInfo]:
    """更新标签描述信息。

    参数:
      tag_name: 标签名称。
      new_desc: 新的描述信息。
      commit: 是否在函数内部提交。
    """
    return update_tag_fields(conn, 
                            tag_name, 
                            {"description": {"desc": new_desc}}, 
                            commit=commit)

def set_tag_deleted(
    conn: psycopg.Connection,
    tag_name: str,
    *,
    deleted: bool = True,
    commit: bool = True,
) -> OperationResult[TagInfo]:
    """设置标签删除状态(软删除/恢复)。

    deleted=True  -> 标记为删除
    deleted=False -> 恢复
    内部复用 update_tag_fields 统一行为。
    """
    return update_tag_fields(conn, tag_name, {"is_deleted": deleted}, commit=commit)

def get_tags_advanced(
    conn: psycopg.Connection,
    *,
    tag_name_list: Optional[Sequence[str]] = None,
    tag_id_list: Optional[Sequence[int]] = None,
    include_deleted: bool = False,
) -> List[Optional[TagInfo]]:
    """按名称列表或ID列表批量查询，并保持输入顺序逐项返回。
    
    约束:
      1. 只能二选一：要么提供 tag_name_list，要么提供 tag_id_list，不能同时都提供且非空。
      2. 结果列表长度与输入列表相同；对应元素不存在时返回 None。
      3. include_deleted=True 时包含软删除记录。
    
    返回:
      List[Optional[TagInfo]]: 与输入一一对应；未找到的位置为 None。
    """
    has_names = bool(tag_name_list)
    has_ids = bool(tag_id_list)
    if has_names and has_ids:
        raise ValueError("只能通过 tag_name_list 或 tag_id_list 之一进行查询，不能同时提供")
    if not has_names and not has_ids:
        return []

    if has_names:
        # 批量查询（底层会去重，不保证顺序），再映射回输入顺序
        rows = get_tags(
            conn,
            TagFilter(names=tag_name_list, include_deleted=include_deleted),
        )
        mapping = {t.tag_name: t for t in rows}
        # 逐项填充，未命中为 None
        return [mapping.get(name) for name in tag_name_list]  # type: ignore[arg-type]

    # has_ids 情况
    rows = get_tags(
        conn,
        TagFilter(ids=tag_id_list, include_deleted=include_deleted),
    )
    mapping = {t.tag_id: t for t in rows if t.tag_id is not None}
    return [mapping.get(int(tid)) if tid is not None else None for tid in tag_id_list]  # type: ignore[arg-type]

