import threading
from dbutils.pooled_db import PooledDB
import pymysql
from pymysql import cursors
import pandas as pd
from tmutils.base.db.Mysql8Config import Mysql8Config

class Mysql8Pool(object):
    """
    mysql地址池
    SHOW FULL PROCESSLIST;
    """
    def __init__(self,config: Mysql8Config, *args, **kwargs) -> None:
        self.config = config
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=6,
            mincached=2,
            blocking=True,
            ping=0,
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            # 返回字典
            charset=self.config.charset,
            cursorclass=cursors.DictCursor,
            connect_timeout=5,  # ✅ 设置连接超时时间（单位：秒）
            read_timeout=10,       # 查询超时（重点）
            write_timeout=10,
        )
        self.local = threading.local()
        self.database=self.config.database

    def open(self, *args, **kwargs):
        conn = self.pool.connection()
        cursor = conn.cursor()
        return conn,cursor

    def close(self,cursor,conn, *args, **kwargs):
        cursor.close()
        conn.close()

    def fetchall(self,sql, *args, **kwargs):
        """ 获取所有数据 """
        try:
            print("获取数据中请等候...")
            conn,cursor = self.open()
            cursor.execute(sql, args)
            result = cursor.fetchall()
            self.close(conn,cursor)
            return result
        except KeyboardInterrupt:
            print("手动中断了请求！程序继续运行...")

    def getTableInfo(self,table_name, *args, **kwargs):
        """ 查询列信息 """
        try:
            sql = "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA,COLUMN_COMMENT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
            conn,cursor = self.open()
            cursor.execute(sql, (self.database, table_name))
            result = cursor.fetchall()
            self.close(conn,cursor)
            data={
                "columnList":[],
                "KeyCommentJson":{}
            }
            for Item in result:
                data["columnList"].append(Item["COLUMN_NAME"])
            for Item in result:
                data["KeyCommentJson"][Item["COLUMN_NAME"]]=Item["COLUMN_COMMENT"]
            return data

        except KeyboardInterrupt:
            print("手动中断了请求！程序继续运行...")

    def fetchone(self,sql, *args, **kwargs):
        """ 获取单条数据 """
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            result = cursor.fetchone()
            self.close(conn, cursor)
            return result
        except KeyboardInterrupt:
            print("手动中断了请求！程序继续运行...")

    def allCommit(self,sql, *args, **kwargs):
        """ 提交的执行脚本 """
        try:
            print("写入数据中请等候...")
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            print("写入数据成功")
            self.close(conn, cursor)
        except KeyboardInterrupt:
            print("手动中断了请求！程序继续运行...")

    def create_table_if_not_exists(self, table_name,comment="", *args, **kwargs):
        """
        判断数据库是否存在，若存在则在其中创建指定表（若该表尚不存在）
        :param db_name: 数据库名
        :param table_name: 表名
        """
        conn, cursor = self.open()
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        table_exists = cursor.fetchone()
        if not table_exists:
            # 创建表
            cursor.execute(f"""
                CREATE TABLE `{table_name}` (
                `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键id',
                `system_id` CHAR(36) NOT NULL DEFAULT (UUID()) COMMENT '系统id',
                `system_create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '系统创建时间',
                `system_update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '系统更新时间',
                `system_create_timestamp` BIGINT NOT NULL DEFAULT (UNIX_TIMESTAMP()) COMMENT '系统创建秒级时间戳',
                PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='{comment}';
            """)
            print(f"表 `{table_name}` 创建成功。")


    def add_column_if_not_exists(self, table_name, column_name, comment):
        """
        判断字段是否存在，不存在则通过 ALTER TABLE 添加字段。
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param column_name: 字段名
        """
        conn, cursor = self.open()
        # 查询字段是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
        """, ( table_name, column_name))
        row = cursor.fetchone()
        exists = row.get('COUNT(*)', 0) if row else 0
        if not exists:
            alter_sql = f"""ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '{comment}';"""
            cursor.execute(alter_sql)
            print(f"字段 `{column_name}` 已添加到表 `{table_name}`。")




    def __enter__(self, *args, **kwargs):
        conn, cursor = self.open()
        rv = getattr(self.local, 'stack', None)
        if not rv:
            self.local.stack = [(conn, cursor)]
        else:
            rv.append((conn, cursor))
            self.local.stack = rv
        return cursor

    def __exit__(self, *args, **kwargs): # 根据不同的线程关闭对应的conn和cursor
        rv = getattr(self.local, 'stack', None)
        if not rv:
            # del self.local.stack
            return
        conn, cursor = self.local.stack.pop()
        cursor.close()
        conn.close()


def get_all_data_pd(config: Mysql8Config,table_name,*args, **kwargs):
    conn = pymysql.connect(
        host=config.host,    # 服务器地址
        user=config.user,    # 用户名
        password=config.password,  # 密码
        database=config.database,  # 数据库名
        charset=config.charset,
        port=config.port
    )
    # 执行 SQL 查询
    query = "SELECT * FROM "+table_name
    df = pd.read_sql(query, conn)
    # 关闭数据库连接
    conn.close()
    return df

def get_where_data_pd(config: Mysql8Config,table_name,whereStr,*args, **kwargs):
    conn = pymysql.connect(
        host=config.host,    # 服务器地址
        user=config.user,    # 用户名
        password=config.password,  # 密码
        database=config.database,  # 数据库名
        charset=config.charset,
        port=config.port
    )
    # 执行 SQL 查询
    query = "SELECT * FROM "+table_name+" where "+whereStr
    df = pd.read_sql(query, conn)
    # 关闭数据库连接
    conn.close()
    return df


