from tsdbpy.conn import get_conn, get_conn_from_ini, list_tsdb_database, load_db_config_from_ini

def test_get_conn_from_ini():
    """测试数据库连接"""
    conn = get_conn_from_ini(
        dbname="tsdb_default", 
        ini_profile="TSDBConnection", 
        ini_path=None, 
        connect_timeout=2.0, 
        autocommit=False)
    
    if conn:
        print("数据库连接成功")
        conn.close()
    else:
        print("数据库连接失败")
        
def test_get_conn():
    conn = get_conn(
            host = "localhost",
            port = 5432,
            user = "postgres",
            password = "",
            dbname = "tsdb_default",
            connect_timeout = 2.0,
            autocommit = False)
    if conn:
        print("数据库连接成功")
        conn.close()
    else:
        print("数据库连接失败")

def test_list_tsdb_databases():
    cfg = load_db_config_from_ini()
    cfg['dbname'] = 'postgres'
    print(cfg)
    conn = get_conn(**cfg)
    
    dbs = list_tsdb_database(conn)
    print("数据库列表:", dbs)
        
if __name__ == "__main__":
    
    # 测试数据库连接
    # test_get_conn_from_ini()
    # test_get_conn()
    test_list_tsdb_databases()
    
    
    