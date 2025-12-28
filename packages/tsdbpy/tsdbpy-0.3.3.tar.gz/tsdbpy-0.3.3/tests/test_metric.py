import psycopg
from tsdbpy.conn import get_conn_from_ini
from tsdbpy.metrics import (
    MetricsInfo,
    OperationResult,
    MetricsFilter,
    get_metrics,
    get_metric,
    resolve_metric_ids,
    insert_new_metric,
    update_metric_fields,
    get_all_metrics,
    delete_metric,
)

# 说明: 请根据数据库现有实际数据调整示例中的 metric 名称 / ID。
def _get_conn():
    return get_conn_from_ini(
        dbname="tsdb_default",
        ini_profile="TSDBConnection",
        ini_path=None,
        connect_timeout=2.0,
        autocommit=False,
    )


def test1_get_metric():
    conn = _get_conn()
    metric_name1 = 'temperature'
    m1 = get_metric(conn, metric_name=metric_name1)
    print(m1)
    metric_id2 = 2
    m2 = get_metric(conn, metric_id=metric_id2)
    print(m2)
    conn.close()


def test2_get_metrics():
    conn = _get_conn()
    dbids = [1, 2]
    flt = MetricsFilter(ids=dbids)
    metrics = get_metrics(conn, flt)
    print(f"get_metrics(ids={dbids}) 返回 {len(metrics)} 条:")
    for m in metrics:
        print(m)
    conn.close()


def test3_resolve_metric_ids():
    conn = _get_conn()
    names = ['temperature', 'room_temperature', 'not_exist_metric']
    ids = resolve_metric_ids(conn, names)
    print(f"{names = }")
    print(f"{ids = }")
    conn.close()


def test4_insert_new_metric():
    conn = _get_conn()
    new_name = 'Demo.Metric9996'
    existing = get_metric(conn, metric_name=new_name)
    if existing:
        print(f"指标({new_name}) 已存在")
        return
    metric = MetricsInfo(
        metric_name=new_name,
        metric_name_zh='测试指标9996',
        unit_id=None,  # 若需要可先插入或查询一个单位 ID
        description={'desc': '测试指标'}
    )
    result: OperationResult = insert_new_metric(conn, metric)
    print(f"尝试新建指标({new_name})")
    print(f"返回: {result}")
    if result.ok:
        print("插入成功")
        print(result.data)
    conn.close()


def test5_update_metric():
    conn = _get_conn()
    # 确保 Demo.Metric9996 已存在
    metric = get_metric(conn, metric_name='Demo.Metric9996')
    if not metric:
        print('Demo.Metric9996 不存在')
        return
    update_dict = {
        'metric_name_zh': '已更新中文名',
        'description': {'desc': '已更新'},
        'unit_id': metric.unit_id,  # 如果需要更改可以替换
    }
    result: OperationResult = update_metric_fields(conn, metric.metric_id, update_dict)
    print(f"尝试更新指标({metric.metric_id})")
    print(f"返回: {result}")
    if result.ok:
        print('更新成功')
        print(result.data)
    conn.close()


def test6_get_all_metrics():
    conn = _get_conn()
    metrics = get_all_metrics(conn)
    print(f"get_all_metrics 返回 {len(metrics)} 条:")
    for m in metrics:
        print(m)
    conn.close()


def test7_delete_metric():
    conn = _get_conn()
    metric = get_metric(conn, metric_name='Demo.Metric9996')
    if not metric:
        print('Demo.Metric9996 不存在')
        return
    result = delete_metric(conn, metric.metric_id)
    print(f"尝试删除指标({metric.metric_id})")
    print(f"返回: {result}")
    conn.close()

if __name__ == '__main__':
    # test1_get_metric()
    # test2_get_metrics()
    # test3_resolve_metric_ids()
    # test4_insert_new_metric()
    # test5_update_metric()
    test6_get_all_metrics()
    # test7_delete_metric()
    pass
