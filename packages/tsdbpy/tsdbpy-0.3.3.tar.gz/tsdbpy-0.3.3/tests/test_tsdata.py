import psycopg
import datetime
from tsdbpy.conn import get_conn_from_ini
from tsdbpy.tsdata import (
    fetch_tsdata_aligned_list,
    fetch_aggregated_tsdata_aligned_list,
    write_tsdata
)

def _get_conn():
    return get_conn_from_ini(
        dbname="tsdb_default",
        ini_profile="TSDBConnection",
        ini_path=None,
        connect_timeout=2.0,
        autocommit=False,
    )


def test2_fetch_tsdata_aligned_list():
    conn = _get_conn()
    
    tag_ids = [100004, 100005, 100006]
    start = datetime.datetime(2025, 8, 8, 10, 18, 00)
    end = datetime.datetime(2025, 8, 8, 10, 19, 00)
    
    times, values = fetch_tsdata_aligned_list(conn, tag_ids, start, end)
    print(times)
    print(values)
    
    conn.close()
    

def test4_fetch_aggregated_tsdata_aligned_list():
    conn = _get_conn()
    
    tag_ids = [100004, 100005, 100006]
    start = datetime.datetime(2025, 8, 8, 10, 20, 0)
    end = datetime.datetime(2025, 8, 8, 10, 30, 0)
    
    times, values = fetch_aggregated_tsdata_aligned_list(
        conn,
        table="tsdata_minutely",
        value_column="avg_value",
        tag_ids=tag_ids,
        start=start,
        end=end
    )
    print(times)
    print(values)
    
    conn.close()

def test5_write_tsdata():
    conn = _get_conn()
    
    tag_ids = [100004, 100005, 100006]
    values =  [3.2, -2.2, -float('inf')]
    
    now = datetime.datetime.now().replace(microsecond=0)
    success, count = write_tsdata(conn, tag_ids, values)
    print(f"写入结果: {success}, count = {count}")
    
    
    times, values = fetch_tsdata_aligned_list(conn, tag_ids, now, now+datetime.timedelta(seconds=1))
    print(times)
    print(values)
    
    conn.close()
    
    

if __name__ == "__main__":
    # 仅用于测试
    # test2_fetch_tsdata_aligned_list()
    # test4_fetch_aggregated_tsdata_aligned_list()
    test5_write_tsdata()
