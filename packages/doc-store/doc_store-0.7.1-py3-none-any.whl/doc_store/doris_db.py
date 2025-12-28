import pymysql
import pymysql.cursors
from dbutils.pooled_db import PooledDB

from .config import config

# 1. 配置Doris连接池（关键参数适配Doris特性）
pool = PooledDB(
    creator=pymysql,  # 指定使用PyMySQL作为数据库驱动
    maxconnections=10,  # 连接池最大连接数（Doris FE建议≤20）
    mincached=2,  # 初始化时，连接池至少创建的空闲连接数
    maxcached=5,  # 连接池最大空闲连接数
    maxshared=3,  # 最大共享连接数（Doris建议设小，避免连接抢占）
    blocking=True,  # 连接池无空闲连接时，是否阻塞等待（True=等待，False=报错）
    maxusage=None,  # 单个连接最大复用次数（None=无限）
    setsession=[],  # 连接建立时执行的SQL（如SET session query_timeout=300）
    ping=0,  # 检测连接有效性：0=不检测，1=每次请求检测，2=空闲时检测

    # Doris连接参数（FE地址+9030端口）
    host=config.doris.host,
    port=config.doris.port,
    user=config.doris.username,
    password=config.doris.password,
    database=config.doris.database,
    charset=config.doris.charset,
    cursorclass=pymysql.cursors.SSCursor,
)

# 2. 从连接池获取连接（复用连接，无需手动创建/关闭）
def query_doris(sql):
    # conn = None
    cursor = None
    conn = pool.connection()  # 从池获取连接
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        # 流式读取Doris大结果集（避免内存溢出）
        for row in cursor:
            yield row
    except Exception as e:
        print(f"查询错误: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()  # 并非真关闭，而是归还到连接池

# 3. 使用示例（查询Doris大表）
for row in query_doris("SHOW TABLES"):
    print(row)

# 4. 关闭连接池（程序退出时执行）
pool.close()


# 'pool_name': 'doris_pool',
# 'pool_size': pool_size,
# 'pool_reset_session': True,
# 'autocommit': True,
# 'connect_timeout': 30,
# 'use_pure': True,
