import psycopg
import datetime
from tsdbpy.conn import get_conn_from_ini
from tsdbpy.source import (
    SourceInfo,
    SourceStatus,
    SourceProtocol,
    OperationResult,
    SourceFilter,
    get_sources,
    get_source,
    resolve_source_ids,
    insert_new_source,
    update_source_fields,
    get_all_sources,
    set_source_status,
    delete_source
)

def _get_conn():
    return get_conn_from_ini(
        dbname="tsdb_default",
        ini_profile="TSDBConnection",
        ini_path=None,
        connect_timeout=2.0,
        autocommit=False,
    )

def test1_get_source():
    conn = _get_conn()
    # 请根据实际库中存在的 source_id/source_name 替换
    source_name1 = 'PLC_Main_OPCUA'
    info1 = get_source(conn, source_name=source_name1)
    print(info1)
    source_id2 = 24
    info2 = get_source(conn, source_id=source_id2)
    print(info2)
    conn.close()

def test2_get_sources():
    conn = _get_conn()
    dbids = [13, 14, 15]
    flt = SourceFilter(ids=dbids)
    sources = get_sources(conn, flt)
    print(f"get_sources(ids={dbids}) 返回 {len(sources)} 条:")
    for src in sources:
        print(src)
    conn.close()

def test3_resolve_source_ids():
    conn = _get_conn()
    names = ['PLC_Main_OPCUA', 'Legacy_System_OPCDA', 'not_exist_source']
    ids = resolve_source_ids(conn, names)
    print(f"{names = }")
    print(f"{ids = }")
    conn.close()

def test4_insert_new_source():
    conn = _get_conn()
    new_name = 'Demo_Source111'
    existing = get_source(conn, source_name=new_name)
    if existing:
        print(f"数据源({new_name}) 已存在")
        return
    new_source = SourceInfo(
        source_name=new_name,
        source_type='TestType',
        interval_msec=2000,
        status=SourceStatus.ACTIVE,
        protocol=SourceProtocol.OPC_UA,
        endpoint='opc.tcp://localhost:4840',
        auth_config={'user': 'test'},
        conn_policy={'retry': 3},
        description={'desc': '测试数据源'}
    )
    result: OperationResult = insert_new_source(conn, new_source)
    print(f"尝试新建数据源({new_name})")
    print(f"返回: {result}")
    if result.ok:
        print("插入成功")
        print(f"{result.data}")
    conn.close()

def test5_update_source():
    conn = _get_conn()
    # 请先确保 Demo_Source111 存在
    src = get_source(conn, source_name='Demo_Source111')
    if not src:
        print("Demo.Source9997 不存在")
        return
    update_dict = {
        "status": SourceStatus.DISABLED,
        "protocol": SourceProtocol.MODBUS,
        "source_name": "Demo_Source111_Updated",
        "description": {"desc": "已更新"}
    }
    result: OperationResult = update_source_fields(conn, src.source_id, update_dict)
    print(f"尝试更新数据源({src.source_id})")
    print(f"返回: {result}")
    if result.ok:
        print("更新成功")
        print(f"{result.data}")
    conn.close()

def test6_get_all_sources():
    conn = _get_conn()
    sources = get_all_sources(conn)
    print(f"get_all_sources 返回 {len(sources)} 条:")
    for src in sources:
        print(src)
    conn.close()

def test7_delete_source():
    conn = _get_conn()
    # 请先确保 Demo_Source111_Updated 存在
    src = get_source(conn, source_name='Demo_Source111_Updated')
    if not src:
        print("Demo_Source111_Updated 不存在")
        return
    result = delete_source(conn, src.source_id)
    print(f"尝试删除数据源({src.source_id})")
    print(f"返回: {result}")
    conn.close()

if __name__ == "__main__":
    test1_get_source()
    # test2_get_sources()
    # test3_resolve_source_ids()
    # test4_insert_new_source()
    # test5_update_source()
    # test6_get_all_sources()
    # test7_delete_source()
