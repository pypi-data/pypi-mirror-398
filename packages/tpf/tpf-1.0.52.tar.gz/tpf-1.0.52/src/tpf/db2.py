# db2_helper.py
import ibm_db
import ibm_db_dbi
import pandas as pd
from contextlib import contextmanager
from typing import Optional


class DB2Helper:
    """
    轻量级 DB2 工具类
    pip install ibm_db pandas
    """

    def __init__(
        self,
        database: str,
        host: str,
        port: int = 50000,
        user: str = "",
        password: str = "",
    ):
        """
        :param database: 数据库名称
        :param host: 主机地址
        :param port: 端口
        :param user: 用户名
        :param password: 密码
        
        
        example
        --------------------------------------------
from db2_helper import DB2Helper

with DB2Helper("sample", "192.168.x.x", user="db2inst1", password="***") as db:
    df = db.select("SELECT * FROM employee")
        
        """
        
        self.conn_str = (
            f"DATABASE={database};"
            f"HOSTNAME={host};"
            f"PORT={port};"
            f"PROTOCOL=TCPIP;"
            f"UID={user};"
            f"PWD={password}"
        )
        self._db_conn = None          # ibm_db 原生连接
        self._db_api_conn = None      # ibm_db_dbi 连接，给 pandas 用

    # ---------- 连接 / 关闭 ----------
    def open(self):
        """建立连接（可重复调用，不会重复创建）"""
        if self._db_conn is None:
            self._db_conn = ibm_db.connect(self.conn_str, "", "")
            self._db_api_conn = ibm_db_dbi.Connection(self._db_conn)
        return self

    def close(self):
        """关闭连接"""
        if self._db_conn:
            ibm_db.close(self._db_conn)
            self._db_conn = None
            self._db_api_conn = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ---------- 核心 API ----------
    def select(self, sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """SQL → DataFrame"""
        return pd.select_query(sql, self._db_api_conn, params=params)

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """
        执行 INSERT / UPDATE / DELETE  
        返回受影响行数
        """
        stmt = ibm_db.prepare(self._db_conn, sql)
        if params:
            ibm_db.execute(stmt, params)
        else:
            ibm_db.execute(stmt)
        return ibm_db.num_rows(stmt)

    @contextmanager
    def transaction(self):
        """手动事务上下文"""
        ibm_db.autocommit(self._db_conn, ibm_db.SQL_AUTOCOMMIT_OFF)
        try:
            yield self
            ibm_db.commit(self._db_conn)
        except Exception:
            ibm_db.rollback(self._db_conn)
            raise
        finally:
            ibm_db.autocommit(self._db_conn, ibm_db.SQL_AUTOCOMMIT_ON)


# ---------- 使用示例 ----------
if __name__ == "__main__":
    # 1. 连接
    db = (
        DB2Helper(
            database="sample",
            host="192.168.1.10",
            user="db2inst1",
            password="secret",
        )
        .open()
    )

    # 2. 读
    df = db.select(
        "SELECT deptno, deptname, mgrno FROM department FETCH FIRST 5 ROWS ONLY"
    )
    print(df)

    # 3. 写
    db.execute(
        "INSERT INTO department(deptno, deptname) VALUES (?, ?)",
        ("Z99", "AI DEPARTMENT"),
    )

    # 4. 事务批量写
    with db.transaction():
        db.execute("UPDATE department SET deptname=? WHERE deptno=?", ("AI LAB", "Z99"))
        db.execute("DELETE FROM department WHERE deptno=?", ("Z99",))

    # 5. 关闭
    db.close()

