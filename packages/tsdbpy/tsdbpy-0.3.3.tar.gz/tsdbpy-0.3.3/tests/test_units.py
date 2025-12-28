import psycopg
from tsdbpy.conn import get_conn_from_ini
from tsdbpy.units import (
    UnitInfo,
    OperationResult,
    UnitsFilter,
    get_units,
    get_unit,
    resolve_unit_ids,
    insert_new_unit,
    update_unit_fields,
    get_all_units,
    delete_unit,
)

# 说明: 根据实际数据库数据调整示例里的 unit 名称 / ID。
# 建议执行顺序：先查看已有，再插入测试条目，更新，最后删除。


def _connect():
    return get_conn_from_ini(
        dbname="tsdb_default",
        ini_profile="TSDBConnection",
        ini_path=None,
        connect_timeout=2.0,
        autocommit=False,
    )


def test1_get_unit():
    conn = _connect()
    unit_name1 = 'celsius'
    u1 = get_unit(conn, unit_name=unit_name1)
    print('单个(按名称):', u1)
    unit_id2 = 9
    u2 = get_unit(conn, unit_id=unit_id2)
    print('单个(按ID):', u2)
    conn.close()


def test2_get_units():
    conn = _connect()
    dbids = [1, 9]
    flt = UnitsFilter(ids=dbids)
    units = get_units(conn, flt)
    print(f"get_units(ids={dbids}) 返回 {len(units)} 条:")
    for u in units:
        print(u)
    conn.close()


def test3_resolve_unit_ids():
    conn = _connect()
    names = ['celsius', 'Demo.Unit9996', 'not_exist_unit']
    ids = resolve_unit_ids(conn, names)
    print(f"{names = }")
    print(f"{ids = }")
    conn.close()


def test4_insert_new_unit():
    conn = _connect()
    new_name = 'Demo.Unit9996'
    existing = get_unit(conn, unit_name=new_name)
    if existing:
        print(f"单位({new_name}) 已存在")
        conn.close()
        return
    unit = UnitInfo(
        unit_name=new_name,
        unit_name_zh='测试单位9996',
        description={'desc': '测试单位'},
    )
    result: OperationResult = insert_new_unit(conn, unit)
    print(f"尝试新建单位({new_name})")
    print('返回:', result)
    if result.ok:
        print('插入成功 ->', result.data)
    conn.close()


def test5_update_unit():
    conn = _connect()
    # 确保 Demo.Unit9996 已存在 (可先用 test4 插入或手动插入)
    unit = get_unit(conn, unit_name='Demo.Unit9996')
    if not unit:
        print('Demo.Unit9996 不存在')
        conn.close()
        return
    update_dict = {
        'unit_name_zh': '已更新单位中文名',
        'description': {'desc': '已更新'},
    }
    result: OperationResult = update_unit_fields(conn, unit.unit_id, update_dict)
    print(f"尝试更新单位({unit.unit_id})")
    print('返回:', result)
    if result.ok:
        print('更新成功 ->', result.data)
    conn.close()


def test6_get_all_units():
    conn = _connect()
    units = get_all_units(conn)
    print(f"get_all_units 返回 {len(units)} 条:")
    for u in units:
        print(u)
    conn.close()


def test7_delete_unit():
    conn = _connect()
    unit = get_unit(conn, unit_name='Demo.Unit9996')
    if not unit:
        print('Demo.Unit9996 不存在')
        conn.close()
        return
    result = delete_unit(conn, unit.unit_id)
    print(f"尝试删除单位({unit.unit_id})")
    print('返回:', result)
    conn.close()


if __name__ == '__main__':
    # test1_get_unit()
    # test2_get_units()
    # test3_resolve_unit_ids()
    # test4_insert_new_unit()
    # test5_update_unit()
    # test6_get_all_units()
    # test7_delete_unit()
    pass
