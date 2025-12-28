import psycopg
from tsdbpy.tag import (
    TagInfo,
    OperationResult,
    TagFilter,
    get_tags,
    get_tag,
    resolve_tag_ids,
    insert_new_tag,
    update_tag_fields,
    get_all_tags
)
from tsdbpy.conn import get_conn_from_ini

def _get_conn():
    return get_conn_from_ini(
        dbname="tsdb_default", 
        ini_profile="TSDBConnection", 
        ini_path=None, 
        connect_timeout=2.0, 
        autocommit=False)

def test1_get_tag():
    conn = _get_conn()
    tag_name1 = 'Demo.Count1'
    tag_info1 = get_tag(conn, tag_name = tag_name1)
    print(tag_info1)
    tag_id2 = 100010
    tag_info2 = get_tag(conn, tag_id = tag_id2)
    print(tag_info2)
    conn.close()
    
def test2_get_tags():
    conn = _get_conn()
    dbids = [100000, 100001]
    flt = TagFilter(ids=dbids)
    tags = get_tags(conn, flt)
    print(f"get_tags(ids={dbids}) 返回 {len(tags)} 条:")
    for tag in tags:
        print(tag)
    conn.close()
    
def test3_resolve_tag_ids():
    conn = _get_conn()
    names = ['Demo.Count1', 'Demo.Count2', 'hihihiih']
    ids = resolve_tag_ids(conn, names)
    print(f"{names = }")
    print(f"{ids = }")
    conn.close()

def test4_insert_new_tag():
    conn = _get_conn()

    new_tag_name = 'Demo.Count9996'
    # 插入前要先查询，确保位号不存在
    existing_tag = get_tag(conn, tag_name=new_tag_name)
    if existing_tag:
        print(f"位号({new_tag_name}) 已存在")
        return
    new_tag = TagInfo(
        tag_name=new_tag_name,
        description='测试位号2'
    )
    result: OperationResult = insert_new_tag(conn, new_tag)
    print(f"尝试新建位号({new_tag_name})")
    print(f"返回: {result}")
    if result.ok:
        print("插入成功")
        print(f"{result.data}")
    conn.close()


def test5_update_tag():
    conn = _get_conn()

    tag_name = 'Demo.Count9997'
    tag_info: TagInfo = get_tag(conn, tag_name=tag_name)
    if not tag_info:
        print(f"位号({tag_name}) 不存在")
        return

    # 更新描述信息
    update_dict = {
        "positive_error": 0.1,
        "negative_error": -0.2,
        # "source_id": 1002,
        # "source_tagname": "Demo.Source2",
        "description": {"desc": "12321"},
        "is_deleted": True
    }
    result: OperationResult = update_tag_fields(conn, tag_name, update_dict)
    print(f"尝试更新位号({tag_name})")
    print(f"返回: {result}")
    if result.ok:
        print("更新成功")
        print(f"{result.data}")
    conn.close()
    
def test6_get_all_tags():
    conn = _get_conn()
    tags = get_all_tags(conn)
    print(f"get_all_tags 返回 {len(tags)} 条:")
    for tag in tags:
        print(tag)
    conn.close()

if __name__ == "__main__":
    # test1_get_tag()
    # test2_get_tags()
    # test3_resolve_tag_ids()
    # test4_insert_new_tag()
    # test5_update_tag()
    test6_get_all_tags()
