from typing import Optional, Literal, Union, List
from datetime import datetime
import time
import psycopg
from tsdbpy import logger
import traceback
from tsdbpy.enums import Quality
from tsdbpy.db_utils import commit_if_needed, rollback_silent, normalize_write_time
import math

#-----------------read data from tsdb tsdata table-----------------
def fetch_tsdata_raw(
    conn: psycopg.Connection,
    tag_ids: list[int],
    start: datetime,
    end: datetime
) -> list[tuple[int, int, float]]:
    """返回原始查询结果 [(timestamp_sec, tag_id, value), ...]"""
    sql = """
        SELECT FLOOR(EXTRACT(EPOCH FROM time_stamp))::int AS ts_sec, tag_id, value, value_quality
        FROM public.tsdata
        WHERE tag_id = ANY(%s) AND time_stamp BETWEEN %s AND %s
        ORDER BY tag_id, time_stamp ASC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (tag_ids, start, end))
        rows = cur.fetchall()
    if not conn.autocommit:
        conn.rollback()
    return rows

def is_value_quality_good(q) -> bool:
    """质量为 None 或高位为 GOOD 时返回 True。"""
    if q is None:
        return True
    if isinstance(q, Quality):
        return q == Quality.HIGH_GOOD
    if isinstance(q, int):
        try:
            return (q & Quality.HIGH_MASK.value) == Quality.HIGH_GOOD.value
        except Exception:
            return False
    return False

def fetch_tsdata_aligned_list(
    conn: psycopg.Connection,
    tag_ids: list[int],
    start: datetime,
    end: datetime,
) -> tuple[list[int], list[list[float]]]:
    """返回时间戳列表 + 二维值列表"""
    if not tag_ids:
        logger.warning("fetch_tsdata_aligned_list: tag_ids 为空，返回空数据")
        return [], []
    t0_total = time.perf_counter()
    n_tags = len(tag_ids)
    
    t0_sql = time.perf_counter()
    rows = fetch_tsdata_raw(conn, tag_ids, start, end)
    t1_sql = time.perf_counter()
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    times = list(range(start_ts, end_ts + 1))
    n_times = len(times)
    values = [[math.nan for _ in tag_ids] for _ in times]
    
    if not rows:
        return times, values

    tag_id_to_col = {tag_id: i for i, tag_id in enumerate(tag_ids)}
    for ts_sec, tag_id, value, quality in rows:
        # 仅在质量为 GOOD 或 None 时返回数据
        if not is_value_quality_good(quality):
            continue
        row_idx = ts_sec - start_ts
        if 0 <= row_idx < n_times:
            col_idx = tag_id_to_col[tag_id]
            values[row_idx][col_idx] = value
    
    t1_total = time.perf_counter()    
    if (t1_total - t0_total) * 1000 > 1000:
        logger.info(
            f"[fetch_tsdata_aligned_list] | total: {(t1_total - t0_total)*1000:.1f} ms | "
            f"SQL: {(t1_sql - t0_sql)*1000:.1f} ms | list: {(t1_total - t1_sql)*1000:.1f} ms | "
            f"tags: {n_tags} | seconds: {n_times} | points: {n_tags * n_times}"
        )
    return times, values

def align_time_range(start: datetime, end: datetime, step: int, offset: int = 0):
    """
    对齐时间范围到 step 的整数倍边界（如分钟/小时/天），可选 offset（如 ts=0 表示 UTC 0点，对应北京时间 8点）

    - step: 60 秒（分钟）、3600 秒（小时）、86400 秒（天）
    - offset: 如果为 8*3600，则天对齐为每天 08:00（北京时间）
    """
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())

    # 加 offset 后 floor 对齐
    aligned_start_ts = ((start_ts - offset) // step) * step + offset
    aligned_end_ts = ((end_ts - offset) // step) * step + offset

    return aligned_start_ts, aligned_end_ts

def fetch_aggregated_tsdata_raw(
    conn: psycopg.Connection,
    table: Literal["tsdata_minutely", "tsdata_hourly", "tsdata_daily"],
    value_column: Literal["first_value", "avg_value", "max_value", "min_value"],
    tag_ids: list[int],
    start: datetime,
    end: datetime
) -> list[tuple[int, int, float]]:
    """返回原始聚合查询结果 [(timestamp_sec, tag_id, value), ...]"""
    # 静态映射时间列
    time_columns = {
        "tsdata_minutely": "bucket_minute",
        "tsdata_hourly": "bucket_hour",
        "tsdata_daily": "bucket_day",
    }
    base_table = table.replace("public.", "")
    time_column = time_columns.get(base_table)
    if not time_column:
        raise ValueError(f"未知的聚合表名：{table}")

    sql = f"""
        SELECT EXTRACT(EPOCH FROM {time_column})::int AS ts_sec, tag_id, {value_column}
        FROM public.{base_table}
        WHERE tag_id = ANY(%s) AND {time_column} BETWEEN %s AND %s
        ORDER BY {time_column} ASC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (tag_ids, start, end))
        rows = cur.fetchall()
    if not conn.autocommit:
        conn.rollback()
    return rows

def fetch_aggregated_tsdata_aligned_list(
    conn: psycopg.Connection,
    table: Literal["tsdata_minutely", "tsdata_hourly", "tsdata_daily"],
    value_column: Literal["first_value", "avg_value", "max_value", "min_value"],
    tag_ids: list[int],
    start: datetime,
    end: datetime,
) -> tuple[list[int], list[list[float]]]:
    """List 版：返回时间戳列表 + 二维值列表"""
    if not tag_ids:
        logger.warning("fetch_aggregated_tsdata_aligned_list: tag_ids 为空")
        return [], []

    t0_total = time.perf_counter()
    n_tags = len(tag_ids)

    # 各表采样间隔
    step, offset = {
        "tsdata_minutely": (60, 0),
        "tsdata_hourly": (3600, 0),
        "tsdata_daily": (86400, 0),
    }.get(table.replace("public.", ""), (60, 0))

    start_ts, end_ts = align_time_range(start, end, step=step, offset=offset)
    times = list(range(start_ts, end_ts + 1, step))
    n_times = len(times)
    values = [[math.nan for _ in tag_ids] for _ in times]

    t0_sql = time.perf_counter()
    rows = fetch_aggregated_tsdata_raw(conn, table, value_column, tag_ids, start, end)
    t1_sql = time.perf_counter()

    if rows:
        tag_id_to_col = {tag_id: i for i, tag_id in enumerate(tag_ids)}
        for ts_sec, tag_id, value in rows:
            row_idx = (ts_sec - start_ts) // step
            if 0 <= row_idx < n_times:
                col_idx = tag_id_to_col[tag_id]
                values[row_idx][col_idx] = value

    t1_total = time.perf_counter()
    if (t1_total - t0_total) * 1000 > 1000:
        logger.info(
            f"[fetch_aggregated_tsdata_aligned_list] | total: {(t1_total - t0_total)*1000:.1f} ms | "
            f"SQL: {(t1_sql - t0_sql)*1000:.1f} ms | list: {(t1_total - t1_sql)*1000:.1f} ms | "
            f"tags: {n_tags} | steps: {n_times} | points: {n_tags * n_times}"
        )

    return times, values


#-----------------write data to tsdb tsdata table-----------------
def _normalize_write_time(write_time: Optional[Union[datetime, int, float]]) -> datetime:
    """兼容旧函数名，内部转调公共实现。"""
    return normalize_write_time(write_time)

# 全局缓存质量码映射表
QUALITY_STR_MAP = {
    "GOOD": None,
    "BAD": Quality.HIGH_BAD.value,
    "INVALID": Quality.HIGH_INVALID.value,  
    "UNCERTAIN": Quality.HIGH_UNCERTAIN.value,
}

def _normalize_quality(q: Union[str, int, None, Quality]) -> Optional[int]:
    """
    标准化质量码：
    - None / "GOOD" / Quality.HIGH_GOOD 都返回 None（表示默认 good）
    - "BAD" 或 Quality.HIGH_BAD 返回其值
    - int 值原样返回
    - 其他非法输入按UNCERTAIN处理
    """
    if q is None:
        return None
    if isinstance(q, str):
        q_upper = q.strip().upper()
        return QUALITY_STR_MAP.get(q_upper, Quality.HIGH_UNCERTAIN.value)
    if isinstance(q, Quality):
        return None if q == Quality.HIGH_GOOD else q.value
    if isinstance(q, int):
        return q
    return Quality.HIGH_UNCERTAIN.value

def write_tsdata(
        conn: psycopg.Connection, 
        tag_ids: List[int], 
        values: List[float], 
        qualities: Optional[List[Union[str, int, None]]] = None,
        write_time: Optional[datetime] = None,
        batch_size: int = 1000,  # 新增批处理大小参数
    ) -> tuple[bool, int]:
    """
    批量写入 OPC 数据到 public.tsdata 表。

    参数:
        tag_ids: tag_id 列表
        values: 每个 tag 对应的值
        qualities: 每个 tag 对应的质量码，None表示good
        write_time: 写入时间（默认使用当前时间）
        batch_size: 批处理大小，大数据集时分批写入
        
    返回:
        (success: bool, count: int)
        - success: 是否全部写入成功
        - count: 实际写入的数据条数（不含空值或错误项）
    """
    
    # 快速长度检查
    n_items = len(tag_ids)
    if n_items != len(values) or (qualities and len(qualities) != n_items):
        logger.error("输入列表长度不一致")
        return False, 0
    
    if n_items == 0:
        logger.warning("没有可写入的数据")
        return True, 0

    write_time = _normalize_write_time(write_time)

    # 向量化质量码处理
    if qualities is None:
        normalized_qualities = [None] * n_items
    else:
        # 预分配列表，避免动态扩展
        normalized_qualities = [None] * n_items
        for i, q in enumerate(qualities):
            normalized_qualities[i] = _normalize_quality(q)

    # 预分配行数据，避免动态列表扩展
    rows = [(write_time, tag_ids[i], values[i], normalized_qualities[i]) 
            for i in range(n_items)]

    total_written = 0
    
    try:
        sql = """
            INSERT INTO public.tsdata (time_stamp, tag_id, value, value_quality)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tag_id, time_stamp)
            DO UPDATE SET
                value = EXCLUDED.value,
                value_quality = EXCLUDED.value_quality
        """
        
        # 批处理写入，避免大数据集时的内存问题
        with conn.cursor() as cur:
            if n_items <= batch_size:
                # 小数据集直接写入
                cur.executemany(sql, rows)
                total_written = n_items
            else:
                # 大数据集分批写入
                for i in range(0, n_items, batch_size):
                    batch_rows = rows[i:i + batch_size]
                    cur.executemany(sql, batch_rows)
                    total_written += len(batch_rows)
                
        # 提交（在非 autocommit 模式下）
        if not conn.autocommit:
            conn.commit()
            
        logger.debug(f"成功写入 {total_written} 条 tsdata 数据")
            
        return True, total_written

    except Exception as e:
        if not conn.autocommit:
            rollback_silent(conn)
        logger.error(f"写入 tsdata 失败:\n{traceback.format_exc()}")
        return False, total_written  # 返回已写入的数量


def write_tsdata_direct(
        conn: psycopg.Connection, 
        tag_ids: List[int], 
        values: List[float], 
        qualities: Optional[List[Union[str, int, None]]] = None,
        write_time: Optional[datetime] = None
    ) -> tuple[bool, int]:
    
    n_items = len(tag_ids)
    if n_items == 0:
        return True, 0

    # 1. 简单的数据归一化
    write_time = normalize_write_time(write_time)
    
    # 2. 生成器：极低内存占用
    # 相比列表推导式，生成器几乎不占内存，对高频写入至关重要
    def row_generator():
        if qualities:
            for i in range(n_items):
                # 这里假设 _normalize_quality 开销很小
                yield (write_time, tag_ids[i], values[i], _normalize_quality(qualities[i]))
        else:
            # 如果没有 quality，循环更简单快
            for i in range(n_items):
                yield (write_time, tag_ids[i], values[i], None)

    try:
        with conn.cursor() as cur:
            # 3. 开启 COPY 通道
            # STDIN 表示数据来自客户端的标准输入流（这里即 Python 代码）
            with cur.copy("COPY public.tsdata (time_stamp, tag_id, value, value_quality) FROM STDIN") as copy:
                # 4. 写入数据
                # write_row 会自动处理 Python 类型到 PostgreSQL 文本/二进制格式的转换
                for row in row_generator():
                    copy.write_row(row)
        
        # 5. 提交事务
        # 只有提交后，数据才对其他查询可见
        if not conn.autocommit:
            conn.commit()
            
        return True, n_items

    except Exception as e:
        if not conn.autocommit:
            conn.rollback()
        # 注意：COPY 模式下，只要有 1 条数据报错（例如主键冲突），整个批次都会失败回滚
        logger.error(f"COPY 写入失败: {e}")
        return False, 0


