from typing import List, Optional, Union, Dict, Any
from tsdbpy import logger
import psycopg
import os
from pathlib import Path
import configparser

def ping(
    conn: psycopg.Connection
    ) -> bool:
    """检查数据库连接是否正常"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            return cur.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Ping failed: {e}")
        return False

def search_ini_path(explicit_path: Optional[Union[str, os.PathLike[str], Path]] = None) -> Optional[Path]:
    """按常见路径查找 tsdbpy.ini（可通过 explicit_path 指定）。"""
    candidates: List[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    # 包目录同级
    candidates.append(Path(__file__).resolve().parent / "tsdbpy.ini")
    # 包目录上层
    candidates.append(Path(__file__).resolve().parent.parent / "tsdbpy.ini")
    # 工作目录
    cwd = Path.cwd()
    candidates.append(cwd / "tsdbpy.ini")
    # 常见的 tests 目录（便于本仓库示例）
    candidates.append(cwd / "tests" / "tsdbpy.ini")
    # Windows: %APPDATA%\tsdbpy\tsdbpy.ini
    appdata = os.getenv("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "tsdbpy" / "tsdbpy.ini")
    for p in candidates:
        if p.is_file():
            return p
    return None

def load_db_config_from_ini(profile: str = "TSDBConnection", path: Optional[Union[str, os.PathLike[str], Path]] = None) -> Dict[str, Any]:
    """从 INI 读取数据库配置"""
    if path is not None:
        ini_path = Path(path)
        if not ini_path.is_file():
            raise FileNotFoundError(f"指定的路径 {ini_path} 不是一个有效的文件。请检查路径是否正确。")
    else:
        ini_path = search_ini_path(path)
        if not ini_path:
            raise FileNotFoundError("未找到 tsdbpy.ini。可传入 path，或将文件放在项目根/包目录/tests，或 %APPDATA%\\tsdbpy\\tsdbpy.ini")
    
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    if profile not in cp:
        raise KeyError(f"配置节 [{profile}] 不存在: {ini_path}")
    sec = cp[profile]
    cfg: Dict[str, Any] = {
        "host": sec.get("host", "localhost"),
        "port": sec.getint("port", fallback=5432),
        "user": sec.get("user", "postgres"),
        "password": sec.get("password", "")
    }
    logger.info(f"从 INI {ini_path} 读取配置节 [{profile}] 成功: {cfg}")
    return cfg

def get_conn(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "",
    dbname: str = "tsdb_default",
    connect_timeout: float = 2.0,
    autocommit: bool = False
) -> Optional[psycopg.Connection]:
    """
    建立数据库连接；成功则返回连接，失败返回 None。
    连接建立后会执行一次 ping 校验，失败则关闭连接。
    """
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=connect_timeout,
            autocommit=autocommit
        )
        if ping(conn):
            logger.info(f"Connected to database {dbname} at {host}:{port} as {user}")
            return conn
        try:
            conn.close()
        finally:
            pass
        logger.error("Database connection failed: ping check failed.")
        return None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_conn_from_ini(
    dbname: str = "tsdb_default",
    ini_profile: str = "TSDBConnection",
    ini_path: Optional[str] = None,
    connect_timeout: float = 2.0,
    autocommit: bool = False,
) -> Optional[psycopg.Connection]:
    """
    从 INI 读取指定 profile 的连接参数并建立连接。
    """
    try:
        cfg = load_db_config_from_ini(profile=ini_profile, path=ini_path)
        return get_conn(
            host=cfg["host"],
            port=int(cfg["port"]),
            user=cfg["user"],
            password=cfg["password"],
            dbname=dbname,
            connect_timeout=connect_timeout,
            autocommit=autocommit
        )
    except Exception as e:
        logger.error(f"Failed to connect from INI: {e}")
        return None    
           
def list_tsdb_database(admin_conn: psycopg.Connection) -> list:
    """
    使用已建立的管理员连接（应连接至 postgres 库）列出以 tsdb 开头的数据库。
    注意：不会关闭传入的连接。
    """
    try:
        if admin_conn is None:
            logger.error("admin_conn is None")
            return []
        # 连接状态与可用性检查
        if getattr(admin_conn, "closed", False):
            logger.error("admin_conn is closed")
            return []
        if not ping(admin_conn):
            logger.error("admin_conn ping failed")
            return []

        # 校验当前数据库是否为 postgres
        dbname = None
        try:
            info = getattr(admin_conn, "info", None)
            if info is not None and hasattr(info, "dbname"):
                dbname = info.dbname
            else:
                with admin_conn.cursor() as cur:
                    cur.execute("select current_database();")
                    dbname = cur.fetchone()[0]
        except Exception:
            dbname = None

        if dbname != "postgres":
            logger.error(f"admin_conn not connected to 'postgres' (current: {dbname})")
            return []

        # 查询 tsdb* 库
        with admin_conn.cursor() as cur:
            cur.execute("""
                SELECT datname FROM pg_database
                WHERE datistemplate = false AND datname LIKE 'tsdb%';
            """)
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Database Error in list_tsdb_database: {e}")
        return []
    
def fetch_available_tsdbs(tsdb_cfg: dict) -> list:
    """读取配置并列出可用的 TSDB 数据库列表。"""
    admin_db_conn = None
    try:
        tsdb_admin_cfg = {k:v for k, v in tsdb_cfg.items() if k in ['host', 'port', 'user', 'password']}
        tsdb_admin_cfg['dbname'] = 'postgres'

        admin_db_conn = get_conn(**tsdb_admin_cfg)
        dbs = list_tsdb_database(admin_db_conn)
        # 去重并排序，便于展示
        dbs = sorted(set(dbs)) if dbs else []
        if not dbs:
            logger.warning("No TSDB databases found on server.")
        return dbs
    finally:
        try:
            if admin_db_conn:
                admin_db_conn.close()
        except Exception:
            logger.warning("Failed to close admin DB connection", exc_info=True)    