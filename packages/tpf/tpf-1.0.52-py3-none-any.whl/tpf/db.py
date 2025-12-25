import os
import pandas as pd
import sqlite3
from typing import Optional, Dict, Any
from tpf import read

# 兼容性处理：Oracle数据库依赖包导入
try:
    import cx_Oracle as ora
    ORACLE_AVAILABLE = True
except ImportError:
    cx_Oracle = None
    ORACLE_AVAILABLE = False
    print("警告: Oracle数据库依赖包 cx_Oracle 未安装，Oracle相关功能将不可用")

# 兼容性处理：MySQL数据库依赖包导入
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("警告: MySQL数据库依赖包 pymysql 未安装，MySQL相关功能将不可用")

# 兼容性处理：高斯数据库依赖包导入
try:
    import psycopg2
    import psycopg2.extras
    GAUSSDB_AVAILABLE = True
except ImportError:
    GAUSSDB_AVAILABLE = False
    print("警告: 高斯数据库依赖包 psycopg2 未安装，GaussDb 类将不可用")

def check_oracle_available():
    """检查Oracle数据库是否可用"""
    return ORACLE_AVAILABLE

def check_mysql_available():
    """检查MySQL数据库是否可用"""
    return MYSQL_AVAILABLE

def check_gaussdb_available():
    """检查高斯数据库是否可用"""
    return GAUSSDB_AVAILABLE

class DbConnect():
    def __init__(self) -> None:
        """数据库连接初始化,
        每次生产一个新的游标,游标是复用还是关闭由使用者决定
        """
        # 读取配置并加载完成连接初始化，外定方法返回句柄 
        # self.oradb = self.oracle()

        local_file_path=os.path.abspath(__file__)
        father_path=os.path.abspath(os.path.dirname(local_file_path)+os.path.sep+".")
        file_path = os.path.join(father_path,"db.db")
        self.db_file = file_path
        # self.db_file = "db.db"
        self._db_dict = {}
        if os.path.exists(self.db_file):
            with open(self.db_file,'r',encoding="utf-8") as f:
                db_dict = eval(f.read())
                self._db_dict = db_dict
        if len(self._db_dict)==0:
            print("没有配置数据库连接信息")
            
    def __enter__(self):
        # self.openedFile = open(self.filename, self.mode)
        # return self.openedFile
        pass 

    def __exit__(self, *unused):
        # self.openedFile.close()
        pass 
    
    def is_ora_open(self,conn):
        """检查Oracle连接是否打开"""
        if not ORACLE_AVAILABLE:
            return False
        try:
            # 尝试执行一个轻量级操作
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                return True
        except:
            return False

    def oradb(self, name="ora3"):
        """每次创建一个新游标,但若有已打开的连接会优先使用已有连接
        """
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle数据库依赖包 cx_Oracle 未安装，请先安装: pip install cx_Oracle")

        db_dict = self._db_dict
        conn_name = "{}.username.connect".format(name)

        _dbconnect = db_dict.get(conn_name,None)
        is_conn_open = True
        if _dbconnect is None:
            is_conn_open = False

        _dbconnect = None
        if len(db_dict) > 0 :
            uname = db_dict["{}.username".format(name)]
            if uname:
                try:
                    _dbconnect = ora.connect(uname,db_dict["{}.password".format(name)],db_dict["{}.url".format(name)])
                except Exception as e :
                    error_msg = "{} db connect error".format(db_dict["{}.url".format(name)])
                    print(error_msg,e)

            else:
                print("{} 连接信息不存在".format(name))

        self._db_dict[conn_name] = _dbconnect
        return _dbconnect 

    def casedb(self):
        """每次创建一个新游标,是复用还是关闭请自行判断
        """
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle数据库依赖包 cx_Oracle 未安装，请先安装: pip install cx_Oracle")

        db_dict = self._db_dict
        _casedb = None
        if len(db_dict) > 0 :
            if db_dict["case.username"]:
                try:
                    _casedb = ora.connect(db_dict["case.username"],db_dict["case.password"],db_dict["case.url"])
                except Exception as e:
                    error_msg = "{} case db connect error".format(db_dict["case.url"])
                    print(error_msg)
            else:
                print("case 连接信息不存在")

        return _casedb 

    def reportdb(self):
        """每次创建一个新游标,是复用还是关闭请自行判断
        """
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle数据库依赖包 cx_Oracle 未安装，请先安装: pip install cx_Oracle")

        db_dict = self._db_dict
        _reportdb = None
        if len(db_dict) > 0 :
            if db_dict["report.username"]:
                try:
                    _reportdb = ora.connect(db_dict["report.username"],db_dict["report.password"],db_dict["report.url"])
                except Exception as e:
                    error_msg = "{} report db connect error".format(db_dict["report.url"])
                    print(error_msg)
            else:
                print("report 连接信息不存在")

        return _reportdb 

    def mysql(self,name=None):
        """每次创建一个新游标,是复用还是关闭请自行判断
        """
        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL数据库依赖包 pymysql 未安装，请先安装: pip install pymysql")

        db_dict = self._db_dict
        _mysql = None
        if len(db_dict) > 0 :
            if name:
                if db_dict["{}.host".format(name)]:
                    try:
                        _mysql = pymysql.connect(host=db_dict["{}.host".format(name)],
                                    port=db_dict["{}.port".format(name)],
                                    user=db_dict["{}.username".format(name)],
                                    password=db_dict["{}.password".format(name)],
                                    database=db_dict["{}.database".format(name)],
                                    charset=db_dict["{}.charset".format(name)])

                    except Exception as e:
                        error_msg = "{} {} mysql db connect error".format(db_dict["{}.host".format(name)],db_dict["{}.port".format(name)])
                        print(error_msg)
                        print(e)
                else:
                    print("mysql {} 连接信息不存在".format(name))
            else:
                if db_dict["db1.host"]:
                    try:
                        _mysql = pymysql.connect(host=db_dict["db1.host"],
                                    port=db_dict["db1.port"],
                                    user=db_dict["db1.username"],
                                    password=db_dict["db1.password"],
                                    database=db_dict["db1.database"],
                                    charset=db_dict["db1.charset"])

                    except:
                        error_msg = "{} mysql db connect error".format(db_dict["db1.host"])
                        print(error_msg)
                        
                else:
                    print("mysql 连接信息不存在")
                
        return _mysql
        
    def write(self,obj):
        ss = str(obj)
        with open(self.db_file,"w",encoding="utf-8") as f:
            f.write(ss)

class DbTools(DbConnect):
    def __init__(self,db_dict=None) -> None:
        super().__init__()
        # if db_dict:
        #     self.resetPwd(db_dict=db_dict)
        #     super().__init__() # 重置密码后再初始化一次 

    def get_dbfile(self):
        return self.db_file

    def getPwd(self):
        """读取文件中的内容"""
        with open(self.db_file, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def resetPwd(self, db_dict=None):
        """每次写入都会覆盖之前的字典
        """
        if db_dict :
            self.write(db_dict)
        else:
            db_dict = {
                "report.username":"case",
                "report.password":"rootroot",
                "report.url":"192.168.111.220:1521/case",
                "case.username":"case",
                "case.password":"rootroot",
                "case.url":"192.168.111.220:1521/case",
                "ora3.username":"case",
                "ora3.password":"rootroot",
                "ora3.url":"192.168.111.220:1521/case",
                "db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"127.0.0.1",
                "db1.port":13301,
                "db1.database":"db1",
                "db1.charset":"utf8",
            }
            self.write(db_dict)
    
    def ora_table_stuct(self,table_name):
        sql = """
        select column_name,data_type,DATA_LENGTH From all_tab_columns  
        where table_name=upper('{}')
        """.format(table_name)
        print(sql)
        res = ""
        col = []
        with self.reportdb() as connection:
            cursor = connection.cursor()
            query = cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            res = query.fetchall()
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data

    def ora_select(self,sql,name='report',show_sql=False,lob=False):
        if show_sql:
            print(sql)
        res = ""
        col = []
        with self.oradb(name=name) as connection:
            cursor = connection.cursor()
            query = cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            if lob:
                # 一次性读取所有结果中的 LOB 数据
                res = [(lob.read() if lob is not None else None,) for lob, in query.fetchall()]
            else:
                res = query.fetchall()
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data
    
    def ora_exec(self,sql, name='report'):
        """批量插入请参考
        https://www.cnblogs.com/cszcoder/p/16248561.html
        """
        print(sql)
        res = ""
        col = []
        with self.oradb(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()
            cursor.close()

    def exec_script_ora(self, sql_text: str, name='report'):
        """
        执行SQL文本（支持多个语句），使用与ora_exec相同的连接方式

        Args:
            sql_text: 完整的SQL文本（可能包含多个语句）
            name: 数据库连接名称
        """
        if not sql_text or not sql_text.strip():
            print("没有SQL内容需要执行")
            return

        print(f"开始执行SQL文本，内容长度: {len(sql_text)} 字符")

        cursor = None
        connection = None
        try:
            # 使用与ora_exec相同的连接方式
            connection = self.oradb(name=name)
            cursor = connection.cursor()

            # 一次性执行完整的SQL文本
            print("正在执行完整的SQL文本...")
            cursor.execute(sql_text)

            # 如果SQL包含SELECT语句且有结果，获取结果
            if sql_text.upper().strip().startswith('SELECT') and 'INTO' not in sql_text.upper():
                try:
                    results = cursor.fetchall()
                    if results:
                        print(f"查询返回 {len(results)} 条结果")
                except:
                    pass  # 没有结果也不报错

            connection.commit()
            print("SQL文本执行完成")

        except Exception as e:
            print(f"执行SQL文本失败: {str(e)}")
            # 显示SQL文本的前500个字符用于调试
            if sql_text:
                print(f"SQL文本预览: {sql_text[:500]}...")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            # 关闭连接
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def exec_script_ora_legacy(self, sql_statements: list, name='report'):
        """
        执行多个SQL语句（逐条执行），保留此方法作为备用

        Args:
            sql_statements: SQL语句列表
            name: 数据库连接名称
        """
        if not sql_statements:
            print("没有SQL语句需要执行")
            return

        print(f"开始逐条执行 {len(sql_statements)} 条SQL语句...")

        cursor = None
        connection = None
        try:
            connection = self.oradb(name=name)
            cursor = connection.cursor()

            for i, sql_stmt in enumerate(sql_statements):
                sql_stmt = sql_stmt.strip()
                if not sql_stmt or sql_stmt.startswith('--') or sql_stmt.startswith('REM'):
                    continue

                try:
                    print(f"执行第 {i+1}/{len(sql_statements)} 条SQL语句...")
                    cursor.execute(sql_stmt)

                    if sql_stmt.upper().startswith('SELECT') and 'INTO' not in sql_stmt.upper():
                        cursor.fetchall()

                    connection.commit()
                    print(f"第 {i+1} 条SQL语句执行成功")

                except Exception as e:
                    error_msg = f"执行第 {i+1} 条SQL语句失败: {str(e)}\nSQL语句: {sql_stmt[:200]}..."
                    print(error_msg)
                    connection.rollback()
                    raise Exception(error_msg)

            print("所有SQL语句执行完成")

        except Exception as e:
            print(f"执行SQL脚本失败: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def select(self, sql,name='db1',show_sql=False):
        """mysql select 
        """
        if show_sql:
            print(sql)
        res = ""
        col = []
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            
            # res type list
            # res[0] type tuple 
            res = cursor.fetchall()   
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data 

    def show_mysql_version(self,name='db1'):
        sql = """
        SELECT VERSION()
        """
        print(sql)
        res = ""
        col = []
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
             # 使用 fetchone() 方法获取单条数据.
            data = cursor.fetchone()
            print ("数据库连接成功,version =",data[0])
            cursor.close()
            # connection.commit()
        return data 


    def exec(self,sql,name='db1'):
        """创建记录表
        """
        res=-1
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            res=cursor.execute(sql)
            connection.commit()
            cursor.close()
        return res


    def insert_many(self,col_list,value_list,table_name, name='db1', insert_type="ignore"):
        """
        参数列表
        --------------------------
        - col_list:[]
        - value_list:[(),()]
        - insert_type:replace/ignore


        return
        ---------------------------------
        - res:影响数据库行数


        举例
        -------------------------------------

        mock_data = [
            (1, 1001, 'aaa', 70.00, 0, '2024-03-12 10:00:00', None),
            (2, 1001, 'bbb', 65.50, 1, '2025-05-16 12:00:00', '2025-05-16 12:00:00')
        ]

        col_list=['id', 'customer_id', 'product_id', 'price', 'status', 'create_time', 'pay_time']
        
        ms.insert_many(col_list,mock_data,table_name='orders')

        
        """
        if insert_type=="replace":
            sql_insert = "replace into {}({}) values({})"
        else:
            sql_insert = "insert ignore into {}({}) values({})"
            
        cols = ','. join(col_list)
        col_num = len(col_list)-1
        place_flag = '%s'
        for i in range(col_num):
            place_flag = place_flag+','+'%s'

        #要以可插入mysql的类型查询出来
        sql_to_mysql= sql_insert.format(table_name, cols, place_flag)
        print(sql_to_mysql)
        print(value_list[0])
        res = 0
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            res=cursor.executemany(sql_to_mysql, value_list)
            connection.commit()
            print(f"{table_name} insert 插入行数: {res}\n")
            cursor.close()
        return res
    
    def pd2mysql(self,data_pd,table_name,dbname):
        """
        - insert_type:ignore/replace
        
        -- 用法
        ms.pd2mysql(data_pd,table_name="students",dbname="db1",insert_type="ignore")
        
        """
        res = 0
        col_list = data_pd.columns.tolist()
        values=[]
        for i in range(data_pd.shape[0]):
            row = data_pd.iloc[i]
            values.append(tuple(row.tolist()))

        if len(values)>0:
            res = self.insert_many(col_list=col_list,value_list=values,table_name=table_name,name=dbname,insert_type="ignore")
        return res 


     


def getPwd():
    """读取文件中的内容"""
    dt = DbTools()
    # content = dt.getPwd()
    db_file = dt.get_dbfile() 
    content = read(db_file)
    return content

def reset_passwd(db_dict):
    """重置密码，会抹去原来所有密码并写入新密码
    example
    -------------------------------------------
    from tpf.db import reset_passwd
    reset_passwd({"db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"11.11.11.11",
                "db1.port":3306,
                "db1.database":"db1",
                "db1.charset":"utf8",
                "report.username":"aaa",
                "report.password":"aaabbbcccddd",
                "report.url":"10.11.111.11:1521/orcl"})
    
    - report:oracle连接方式
    - db1:mysql连接方式
    """

    dt = DbTools()
    dt.resetPwd(db_dict=db_dict)
    
def update_passwd(db_dict):
    """更新密码，字典同key则更新，否则写入
    example
    -------------------------------------------
    from tpf.db import reset_passwd
    reset_passwd({"db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"11.11.11.11",
                "db1.port":3306,
                "db1.database":"db1",
                "db1.charset":"utf8",
                "report.username":"aaa",
                "report.password":"aaabbbcccddd",
                "report.url":"10.11.111.11:1521/orcl"})
    
    - report:oracle连接方式
    - db1:mysql连接方式
    """
    old_pwd = getPwd()
    old_pwd.update(db_dict)

    dt = DbTools()
    dt.resetPwd(db_dict=old_pwd)




class OracleDb():
    def __init__(self,name):
        import importlib
        import sys

        # 强制重新加载 db_ora 模块以确保使用最新版本
        if 'tpf.db_ora' in sys.modules:
            importlib.reload(sys.modules['tpf.db_ora'])

        from tpf.db_ora import OraclePLSQLExecutor
        self.name = name
        self.ms = DbTools()
        self.plsql = OraclePLSQLExecutor(name=name)
        self.plsql.connect()
        
    def select(self, sql, name=None,show_sql=False,lob=False):
        """
        - name:为None时使用初始化的name
        - lob:True表示查询lob字段，但仅限单列查询
        """
        if show_sql:
            print(sql)
        if name is None:
            name = self.name
        cleaned_sql = sql.rstrip().rstrip(';')
        res = self.ms.ora_select(sql=cleaned_sql,name=name,lob=lob)
        return res
    
    def drop_proc(self,proc_name,first_exec=False):
        if first_exec:
        # 执行带表名参数的 PL/SQL（方案1：使用动态SQL）
            sql = """
            CREATE OR REPLACE PROCEDURE drop_procedure_safely(
                p_procedure_name IN VARCHAR2
            )
            IS
                v_procedure_exists NUMBER;
                v_upper_procedure_name VARCHAR2(100);
                v_drop_sql VARCHAR2(500);
            BEGIN
                -- 统一转换为大写处理
                v_upper_procedure_name := UPPER(TRIM(p_procedure_name));
                
                -- 验证参数是否为空
                IF v_upper_procedure_name IS NULL THEN
                    DBMS_OUTPUT.PUT_LINE('错误: 存储过程名称不能为空');
                    RETURN;
                END IF;
                
                -- 检查存储过程是否存在
                SELECT COUNT(*)
                INTO v_procedure_exists
                FROM user_objects
                WHERE object_type = 'PROCEDURE'
                AND object_name = v_upper_procedure_name;
                
                -- 如果存在则删除
                IF v_procedure_exists > 0 THEN
                    -- 记录删除前的信息
                    DBMS_OUTPUT.PUT_LINE('正在删除存储过程: ' || v_upper_procedure_name);
                    DBMS_OUTPUT.PUT_LINE('删除时间: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS'));
                    
                    -- 构建并执行删除语句
                    v_drop_sql := 'DROP PROCEDURE ' || v_upper_procedure_name;
                    DBMS_OUTPUT.PUT_LINE('执行SQL: ' || v_drop_sql);
                    
                    EXECUTE IMMEDIATE v_drop_sql;
                    
                    DBMS_OUTPUT.PUT_LINE('存储过程删除成功');
                ELSE
                    DBMS_OUTPUT.PUT_LINE('存储过程 ' || v_upper_procedure_name || ' 不存在');
                END IF;
                
            EXCEPTION
                WHEN OTHERS THEN
                    DBMS_OUTPUT.PUT_LINE('删除失败: ' || SQLERRM);
                    DBMS_OUTPUT.PUT_LINE('错误代码: ' || SQLCODE);
            END drop_procedure_safely;
            """
            self.exec_plsql(sql)

        sql=f"""
        
        BEGIN
            drop_procedure_safely('{proc_name}');      -- 小写
        END;
        """
        self.exec_plsql(sql)
        
    def exec(self, sql, name=None):
        """- name:为None时使用初始化的name"""
        if name is None:
            name = self.name
        cleaned_sql = sql.rstrip().rstrip(';')
        self.ms.ora_exec(sql=cleaned_sql,name=name)
        
    def exec_batch(self, sql_text,sql_split=';'):
        """
        批量执行SQL语句，按分号分隔SQL文本
        
        Args:
            sql_text: 包含多个SQL语句的文本，以分号分隔
        """
        # 按分号分割SQL语句
        sql_statements = sql_text.split(sql_split)
        
        # 遍历每个SQL语句并执行
        for sql in sql_statements:
            # 去除首尾空白字符
            sql = sql.strip()
            
            # 跳过空语句
            if not sql:
                continue
                
            # 确保SQL语句以分号结尾（可选，根据数据库要求）
            # if not sql.endswith(sql_split):
            #     sql += ';'
                
            try:
                # 调用单个SQL执行方法
                self.exec(sql)
                print(f"成功执行SQL: {sql[:50]}...")  # 打印前50个字符用于日志
            except Exception as e:
                print(f"执行SQL失败: {sql[:50]}...")
                print(f"错误信息: {str(e)}")
                # 可以根据需要决定是否继续执行后续SQL
                raise e  # 如果希望遇到错误就停止，可以取消注释
           
    def exec_sql_file(self, sql_file: str,
                     in_params: Optional[Dict] = None,
                     out_params: Dict[str, Any] = None,
                     enable_output: bool = True,
                     auto_commit: bool = False) -> Dict[str, Any]:
        """
        执行SQL脚本文件，整合exec_plsql方法与exec_with_output_params方法

        Args:
            sql_file: SQL脚本文件路径
            in_params: 输入参数字典 {参数名: 参数值}
            out_params: 输出参数定义 {参数名: 参数类型}
            enable_output: 是否启用 DBMS_OUTPUT
            auto_commit: 是否自动提交

        Returns:
            Dict: 执行结果和输出参数值（如果有）

        Note:
            - 若out_params不为None或有值，则调用exec_with_output_params方法
            - 反之，调用exec_plsql方法
        """
        try:
            # 读取SQL文件内容
            with open(sql_file, 'r', encoding='utf-8') as f:
                plsql_block = f.read()

            # 根据是否有输出参数选择调用方法
            if out_params is not None and len(out_params) > 0:
                # 调用exec_with_output_params方法
                return self.exec_with_output_params(
                    plsql_block=plsql_block,
                    in_params=in_params,
                    out_params=out_params,
                    enable_output=enable_output,
                    auto_commit=auto_commit
                )
            else:
                # 调用exec_plsql方法
                return self.exec_plsql(
                    plsql_block=plsql_block,
                    in_params=in_params,
                    enable_output=enable_output,
                    auto_commit=auto_commit
                )

        except FileNotFoundError:
            return {
                'success': False,
                'error': f'SQL文件未找到: {sql_file}',
                'output_params': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'读取SQL文件失败: {str(e)}',
                'output_params': {}
            }   
    def exec_plsql(self, plsql_block: str,
                     in_params: Optional[Dict] = None,
                     enable_output: bool = True,
                     auto_commit: bool = False) -> Dict[str, Any]:
        """
        执行 PL/SQL 匿名块

        Args:
            plsql_block: PL/SQL 块代码
            in_params: 输入参数字典
            enable_output: 是否启用 DBMS_OUTPUT
            auto_commit: 是否自动提交

        Returns:
            Dict: 执行结果信息
        """
        return self.plsql.execute_plsql_block(
            plsql_block=plsql_block,
            bind_params=in_params,
            enable_output=enable_output,
            auto_commit=auto_commit
        ) 


    def exec_with_output_params(self, plsql_block: str,
                               in_params: Optional[Dict] = None,
                               out_params: Dict[str, Any] = None,
                               enable_output: bool = True,
                               auto_commit: bool = False) -> Dict[str, Any]:
        """
        执行带有输出参数的 PL/SQL 块

        Args:
            plsql_block: PL/SQL 块代码
            in_params: 输入参数字典 {参数名: 参数值}
            out_params: 输出参数定义 {参数名: 参数类型}
            enable_output: 是否启用 DBMS_OUTPUT
            auto_commit: 是否自动提交

        Returns:
            Dict: 执行结果和输出参数值
        """
        return self.plsql.execute_with_output_params(
            plsql_block=plsql_block,
            bind_params=in_params,
            out_params=out_params,
            enable_output=enable_output,
            auto_commit=auto_commit
        )
         
         
         
    def exec_proc(self, procedure_name: str,
                in_params: Optional[Dict] = None,
                out_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        调用存储过程

        Args:
            procedure_name: 存储过程名称
            in_params: 输入参数 {参数名: 参数值}
            out_params: 输出参数 {参数名: 参数类型}

        Returns:
            Dict: 执行结果
        """
        return self.plsql.call_stored_procedure(procedure_name, in_params, out_params) 
    
    
    def insert_many(self, col_list, value_list, table_name, insert_type = None, name=None, place_flag='%s'):
        """
        - name:为None时使用初始化的name
        - place_flag:  python为%s,java为?,如果使用python cx_Oracle则占位符为%s,如果是java程序则占位符为?
        
        批量插入数据
        参数列表
        --------------------------
        - col_list:[] 列英文名称
        - value_list:[(),()] 批量数据与列英文名称一致
        举例
        -------------------------------------
        col_list=['id', 'customer_id', 'product_id', 'price', 'status', 'create_time', 'pay_time']
        value_list = [
            (1, 1001, 'aaa', 70.00, 0, '2024-03-12 10:00:00', None),
            (2, 1001, 'bbb', 65.50, 1, '2025-05-16 12:00:00', '2025-05-16 12:00:00')
        ]
        ms.insert_many(col_list,value_list,table_name='orders')


        """
        if name is None:
            name = self.name
            
        if insert_type:
            if insert_type == "replace":
                #存在则替换，不存在则插入
                sql_insert = "replace into {}({}) values({})"
            else:
                #如果表中数据已存在则不再插入
                sql_insert = "insert ignore into {}({}) values({})"
        else:
            sql_insert = "insert into {}({}) values({})"

        # cols = ','.join(col_list)
        cols = ','.join(f'"{col}"' for col in col_list)
        col_num = len(col_list) - 1
        if place_flag == '%s':
            flag_num =1
            _place_flag = f":{flag_num}"  # python为%s,java为?
            
            for i in range(col_num):
                _place_flag = _place_flag + ',' + f":{flag_num+1}"
                flag_num +=1
        else: 
            for i in range(col_num):
                _place_flag = _place_flag + ',' + place_flag

        # 要以可插入mysql的类型查询出来
        sql_to_mysql = sql_insert.format(table_name, cols, _place_flag)

        with self.ms.oradb(name=name) as connection:
            cursor = None
            try:
                cursor = connection.cursor()
                cursor.executemany(sql_to_mysql, value_list)
                connection.commit()
            finally:
                if cursor is not None:
                    cursor.close()

    def insert_many_pd(self, data_pd, table_name, show_msg=False, name=None, place_flag='%s'):
        """批量插入数据,data_pd除了数字外，剩下的最好全部设置为string类型.astype('string')
        - name:为None时使用初始化的name
        - insert_type:ignore/replace
        - place_flag:  python为%s,java为?,如果使用python cx_Oracle则占位符为%s,如果是java程序则占位符为?

        -- 用法
        ms.pd2mysql(data_pd,table_name="students",insert_type="ignore")
        
        -- 除数字外，转字符串类型
        num_type = ["AMT_VAL","CRAT","CNY_AMT","USD_AMT"]
        cls_type = list(set(df.columns.tolist()) - set(num_type))
        df[cls_type] = df[cls_type].astype("string")
        df.info()

        """
        col_list = data_pd.columns.tolist()
        values = []
        for i in range(data_pd.shape[0]):
            row = data_pd.iloc[i]
            values.append(tuple(row.tolist()))
        if show_msg:
            print("col_list:\n",col_list)
            print("values:\n",values)
        if len(values) > 0:
            self.insert_many(col_list=col_list, value_list=values, table_name=table_name,name=name,place_flag=place_flag)

    def pd2db(self, data_pd, table_name, show_msg=False, place_flag='%s'):
        """pandas数表入库 
        
        params
        -------------------
        - show_msg:是否展示更详细的日志输出
        - place_flag:  python为%s,java为?,如果使用python cx_Oracle则占位符为%s,如果是java程序则占位符为?
        
        """
        tmp_pd = data_pd.copy()
        tmp_pd.columns = tmp_pd.columns.str.upper()
        self.insert_many_pd(data_pd=tmp_pd, table_name=table_name, show_msg=show_msg, place_flag=place_flag)
        del tmp_pd
   
    def pd2db_batch(self, df, table_name, batch_size = 10_000, show_msg=False, place_flag='%s'):
        total_rows = len(df)
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            print(start_idx,end_idx)
            batch = df.iloc[start_idx:end_idx]  # 按批次取数据
            self.pd2db(batch, table_name, show_msg=show_msg,place_flag=place_flag)
   
   
    def exec_script(self, script_path: str, start_date: str = None, end_date: str = None):
        """
        执行SQL脚本文件

        Args:
            script_path: SQL脚本文件路径
            start_date: 开始日期参数（可选）
            end_date: 结束日期参数（可选）
            
        example:
        ----------------------------------------------
        from tpf.db import OracleDb

        # 创建实例
        oracle = OracleDb(name='report')

        # 执行脚本
        oracle.exec_script(
            script_path='/ai/wks/sql/v1_ora/a01_create_dwd_bb11_trans.sql',
            start_date='2025-07-31',
            end_date='2025-08-02'
        )

        # 或者只进行预处理验证
        statements = oracle.test_script_execution(
            script_path='/ai/wks/sql/v1_ora/a01_create_dwd_bb11_trans.sql',
            start_date='2025-07-31',
            end_date='2025-08-02'
        )

        """
        import os
        import re

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"SQL脚本文件不存在: {script_path}")

        print(f"读取SQL脚本文件: {script_path}")

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(script_path, 'r', encoding='gbk') as f:
                sql_content = f.read()

        # 替换脚本中的参数占位符
        if start_date is not None and end_date is not None:
            print(f"替换参数: &1 -> {start_date}, &2 -> {end_date}")
            sql_content = sql_content.replace('&1', start_date)
            sql_content = sql_content.replace('&2', end_date)
        elif start_date is not None:
            print(f"替换参数: &1 -> {start_date}")
            sql_content = sql_content.replace('&1', start_date)

        # 优化：直接使用完整的SQL文本执行，而不是分割成多个语句
        # 这样可以保持SQL脚本的完整性，特别是对于复杂的存储过程

        print(f"脚本处理完成，SQL文本长度: {len(sql_content)} 字符")

        # 过滤SQL文本：移除SQL*Plus命令，但保留所有数据库语句
        filtered_sql_lines = []
        for line in sql_content.split('\n'):
            stripped_line = line.strip()
            # 跳过SQL*Plus特定命令，但保留所有数据库可执行的语句
            if (stripped_line and
                not stripped_line.upper().startswith(('SET ', 'WHENEVER ', 'PROMPT', 'DEFINE ', 'EXIT')) and
                not stripped_line.startswith('--') and
                not stripped_line.startswith('REM')):
                filtered_sql_lines.append(line)

        # 重新组合过滤后的SQL文本
        filtered_sql_text = '\n'.join(filtered_sql_lines)
        print(filtered_sql_text)

        if filtered_sql_text.strip():
            print(f"过滤后的SQL文本长度: {len(filtered_sql_text)} 字符")

            # 调用DbTools的exec_script_ora方法执行完整SQL文本
            try:
                print(f"开始执行脚本: {script_path} (一次性执行完整SQL文本)")
                self.ms.exec_script_ora(filtered_sql_text, name=self.name)
                print(f"脚本 {script_path} 执行完成")
            except Exception as e:
                print(f"脚本执行失败: {str(e)}")
                raise
        else:
            print("没有有效的SQL内容需要执行")


    def show_proc_status(self,proc_name):
        sql=f"""
        SELECT object_name, object_type, status, created, last_ddl_time
        FROM user_objects 
        WHERE object_name = upper('{proc_name}');
        """
        df = self.select(sql)
        status = df["STATUS"][0]
        if status =='INVALID':
            print(df)
            sql = f"""
            SELECT line, position, text
            FROM user_errors
            WHERE name = '{proc_name}'
            ORDER BY line
            """
            df = self.select(sql)
        return df 


    def _split_sql_statements(self, sql_content: str):
        """
        分割SQL内容为独立的语句，正确处理PL/SQL块

        Args:
            sql_content: SQL内容

        Returns:
            List[str]: SQL语句列表
        """
        statements = []
        current_stmt = ""
        in_plsql_block = False
        plsql_delimiters = ['BEGIN', 'DECLARE', 'CREATE OR REPLACE', 'CREATE PROCEDURE',
                           'CREATE FUNCTION', 'CREATE TRIGGER', 'CREATE PACKAGE']

        lines = sql_content.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('--') or line.startswith('REM'):
                continue

            current_stmt += line + "\n"

            # 检查是否进入PL/SQL块
            upper_line = line.upper()
            for delimiter in plsql_delimiters:
                if upper_line.startswith(delimiter):
                    in_plsql_block = True
                    break

            # 检查是否结束PL/SQL块
            if in_plsql_block and upper_line.endswith(';'):
                if upper_line.endswith('END;') or upper_line.endswith('END;/'):
                    in_plsql_block = False
                    statements.append(current_stmt.strip())
                    current_stmt = ""
                continue

            # 如果不在PL/SQL块中且以分号结尾，则结束当前语句
            if not in_plsql_block and upper_line.endswith(';'):
                # 处理SQL*Plus的特殊命令
                if line.upper().startswith(('SET ', 'WHENEVER ', 'PROMPT', 'DEFINE ', 'EXIT')):
                    current_stmt = ""  # 忽略SQL*Plus命令
                else:
                    statements.append(current_stmt.strip())
                    current_stmt = ""

        # 添加最后一个语句（如果存在）
        if current_stmt.strip():
            statements.append(current_stmt.strip())

        return statements

    def test_script_execution(self, script_path: str, start_date: str = None, end_date: str = None):
        """
        测试脚本执行（不实际执行SQL，只验证预处理）

        Args:
            script_path: SQL脚本文件路径
            start_date: 开始日期参数（可选）
            end_date: 结束日期参数（可选）
        """
        import os

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"SQL脚本文件不存在: {script_path}")

        # 读取脚本内容
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 替换参数
        if start_date is not None and end_date is not None:
            sql_content = sql_content.replace('&1', start_date).replace('&2', end_date)
        elif start_date is not None:
            sql_content = sql_content.replace('&1', start_date)

        # 分割SQL语句
        statements = self._split_sql_statements(sql_content)

        print(f"脚本预处理成功:")
        print(f"  文件路径: {script_path}")
        print(f"  SQL语句数量: {len(statements)}")
        if start_date and end_date:
            print(f"  开始日期: {start_date}")
            print(f"  结束日期: {end_date}")

        return statements


class PgDb():
    def __init__(self):
        pass


class MyDb():
    def __init__(self,name="link_mysql") -> None:
        self.dbtool = DbTools()
        self.name = name
        
    def select(self,sql,show_sql=False):
        if show_sql:
            print(sql)
        return self.dbtool.select(sql,name=self.name)
    
    def exec(self,sql):
        self.dbtool.exec(sql=sql,name=self.name)
        
    def insert_many(self,col_list,value_list,table_name):
        res = self.dbtool.insert_many(col_list=col_list,value_list=value_list,table_name=table_name, name=self.name, insert_type="ignore")
        return res
    
    def pd2mysql(self,data_pd,table_name):
        res = self.dbtool.pd2mysql(data_pd=data_pd,table_name=table_name,dbname=self.name)
        return res     
 
class GaussDb():
    def __init__(self, name="gaussdb"):
        """高斯数据库操作类

        Args:
            name: 数据库连接名称，用于从配置文件中获取连接信息
        """
        if not GAUSSDB_AVAILABLE:
            raise ImportError("高斯数据库依赖包 psycopg2 未安装，请先安装: pip install psycopg2-binary")

        self.name = name
        self.dbtool = DbTools()
        self._connection = None

    def get_connection(self):
        """获取数据库连接"""
        if self._connection is None:
            db_dict = self.dbtool._db_dict

            # 检查连接配置是否存在
            host_key = f"{self.name}.host"
            port_key = f"{self.name}.port"
            user_key = f"{self.name}.username"
            pwd_key = f"{self.name}.password"
            db_key = f"{self.name}.database"

            if not all(key in db_dict for key in [host_key, port_key, user_key, pwd_key, db_key]):
                raise ValueError(f"高斯数据库 {self.name} 连接配置不完整，请检查配置文件")

            try:
                conn_str = f"host={db_dict[host_key]} port={db_dict[port_key]} dbname={db_dict[db_key]} user={db_dict[user_key]} password={db_dict[pwd_key]}"
                self._connection = psycopg2.connect(conn_str)
            except Exception as e:
                error_msg = f"高斯数据库连接失败: {db_dict[host_key]}:{db_dict[port_key]}"
                print(error_msg, e)
                raise e

        return self._connection

    def close_connection(self):
        """关闭数据库连接"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None


    def select_byday(self, sql, time_col='dt_time', start_date='2025-01-01', end_date='2025-01-01',
                      deal_func=None, show_progress=True, **func_params):
        """高斯数据库按天查询数据并进行处理

        从start_date到end_date，逐天查询数据，每天查询完成后执行deal_func处理

        Args:
            sql: SQL查询语句，应包含时间列占位符 {time_col_condition}
            time_col: 时间列名，默认为 'dt_time'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            deal_func: 数据处理函数，接收DataFrame参数
            show_progress: 是否显示处理进度
            **func_params: 传递给deal_func的额外参数

        Returns:
            如果deal_func为None，返回所有查询结果的合并DataFrame
            如果deal_func不为None，返回每天处理结果的列表

        Example:
            # 基本用法 - 逐天查询并合并结果
            result = gdb.select_byday(
                "SELECT * FROM sales WHERE {time_col_condition}",
                time_col='create_time',
                start_date='2025-01-01',
                end_date='2025-01-07'
            )

            # 带数据处理的用法 - 逐天处理
            def process_daily_data(df, **params):
                # 每日数据处理逻辑
                return {
                    'date': df['create_time'].dt.date.iloc[0],
                    'total_amount': df['amount'].sum(),
                    'order_count': len(df)
                }

            results = gdb.select_byday(
                "SELECT * FROM sales WHERE {time_col_condition}",
                start_date='2025-01-01',
                end_date='2025-01-31',
                deal_func=process_daily_data
            )
        """
        import datetime

        # 生成从start_date到end_date的日期列表
        start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        if start_dt > end_dt:
            raise ValueError(f"开始日期 {start_date} 不能晚于结束日期 {end_date}")

        # 计算总天数
        total_days = (end_dt - start_dt).days + 1
        print(f"开始按天查询数据，从 {start_date} 到 {end_date}，共 {total_days} 天")

        all_results = []
        current_dt = start_dt
        day_count = 0

        # 逐天循环查询
        while current_dt <= end_dt:
            day_count += 1
            current_date_str = current_dt.strftime('%Y-%m-%d')

            if show_progress:
                print(f"\n处理第 {day_count}/{total_days} 天: {current_date_str}")

            try:
                # 构建单天的查询条件
                time_condition = f"DATE({time_col}) = '{current_date_str}'"

                # 替换SQL中的时间条件占位符
                final_sql = sql.format(time_col_condition=time_condition)

                if show_progress:
                    print(f"查询SQL: {final_sql}")

                # 查询当天的数据
                daily_df = self.select(final_sql, show_sql=False)

                if daily_df.empty:
                    if show_progress:
                        print(f"  - {current_date_str} 无数据")
                    daily_result = None
                else:
                    if show_progress:
                        print(f"  - 查询到 {len(daily_df)} 条记录")

                    # 如果提供了数据处理函数，则调用处理函数
                    if deal_func is not None and callable(deal_func):
                        try:
                            daily_result = deal_func(daily_df, **func_params)
                            if show_progress:
                                print(f"  - 数据处理完成: {type(daily_result)}")
                        except Exception as e:
                            print(f"  - 数据处理失败: {e}")
                            daily_result = None
                    else:
                        # 没有处理函数，直接返回查询结果
                        daily_result = daily_df

                all_results.append({
                    'date': current_date_str,
                    'data': daily_result,
                    'count': len(daily_df) if not daily_df.empty else 0
                })

            except Exception as e:
                print(f"  - 处理日期 {current_date_str} 时出错: {e}")
                all_results.append({
                    'date': current_date_str,
                    'data': None,
                    'count': 0,
                    'error': str(e)
                })

            # 移动到下一天
            current_dt += datetime.timedelta(days=1)

        # 汇总结果
        successful_days = [r for r in all_results if r.get('error') is None]
        failed_days = [r for r in all_results if r.get('error') is not None]
        total_records = sum(r['count'] for r in all_results)

        print(f"\n查询完成:")
        print(f"  - 总天数: {total_days}")
        print(f"  - 成功处理: {len(successful_days)} 天")
        print(f"  - 处理失败: {len(failed_days)} 天")
        print(f"  - 总记录数: {total_records}")

        # 返回结果
        if deal_func is not None and callable(deal_func):
            # 如果有处理函数，返回处理结果列表
            results = [r['data'] for r in successful_days if r['data'] is not None]
            return results
        else:
            # 如果没有处理函数，合并所有DataFrame
            valid_dfs = [r['data'] for r in successful_days if r['data'] is not None and not r['data'].empty]
            if valid_dfs:
                combined_df = pd.concat(valid_dfs, ignore_index=True)
                print(f"  - 合并后数据: {len(combined_df)} 条记录")
                return combined_df
            else:
                print("  - 无有效数据")
                return pd.DataFrame()

     

    def select(self, sql, show_sql=False):
        """查询数据

        Args:
            sql: SQL查询语句
            show_sql: 是否显示SQL语句

        Returns:
            pd.DataFrame: 查询结果DataFrame
        """
        if show_sql:
            print(sql)

        conn = self.get_connection()
        cleaned_sql = sql.rstrip().rstrip(';')

        try:
            with conn.cursor() as cursor:
                cursor.execute(cleaned_sql)
                col = [desc[0] for desc in cursor.description]
                res = cursor.fetchall()
                data = pd.DataFrame(res, columns=col)
                return data
        except Exception as e:
            print(f"查询执行失败: {e}")
            raise e

    def select_single(self, sql, show_sql=False):
        """查询单个值

        Args:
            sql: SQL查询语句
            show_sql: 是否显示SQL语句

        Returns:
            查询到的单个值，如果没有结果返回None
        """
        df = self.select(sql, show_sql=show_sql)
        if df.shape[0] > 0:
            return df.iloc[0, 0]
        return None

    def exec(self, sql, show_sql=False):
        """执行SQL语句（INSERT, UPDATE, DELETE等）

        Args:
            sql: SQL执行语句
            show_sql: 是否显示SQL语句

        Returns:
            int: 影响的行数
        """
        if show_sql:
            print(sql)

        conn = self.get_connection()
        cleaned_sql = sql.rstrip().rstrip(';')

        try:
            with conn.cursor() as cursor:
                res = cursor.execute(cleaned_sql)
                conn.commit()
                return res.rowcount if hasattr(res, 'rowcount') else cursor.rowcount
        except Exception as e:
            conn.rollback()
            print(f"SQL执行失败: {e}")
            raise e

    def exec_batch(self, sql_text, sql_split=';', show_sql=False):
        """批量执行SQL语句，按分号分隔SQL文本

        Args:
            sql_text: 包含多个SQL语句的文本，以分号分隔
            sql_split: SQL分隔符，默认为分号
            show_sql: 是否显示SQL语句
        """
        sql_statements = sql_text.split(sql_split)

        for sql in sql_statements:
            sql = sql.strip()
            if not sql:
                continue

            try:
                self.exec(sql, show_sql=show_sql)
                print(f"成功执行SQL: {sql[:50]}...")
            except Exception as e:
                print(f"执行SQL失败: {sql[:50]}...")
                print(f"错误信息: {str(e)}")
                raise e

    def insert_many(self, col_list, value_list, table_name, insert_type="ignore", show_sql=False):
        """批量插入数据

        Args:
            col_list: 列名列表
            value_list: 数据值列表，格式为 [(row1), (row2), ...]
            table_name: 表名
            insert_type: 插入类型 "ignore"(忽略重复) 或 "replace"(替换重复)
            show_sql: 是否显示SQL语句

        Returns:
            int: 影响的行数
        """
        if not col_list or not value_list:
            return 0

        if insert_type == "replace":
            sql_insert = "INSERT INTO {}({}) VALUES({}) ON CONFLICT DO UPDATE SET "
        else:
            sql_insert = "INSERT INTO {}({}) VALUES({}) ON CONFLICT DO NOTHING"

        cols = ','.join(f'"{col}"' for col in col_list)
        place_holders = ','.join(['%s'] * len(col_list))

        sql_to_execute = sql_insert.format(table_name, cols, place_holders)

        if insert_type == "replace":
            # 构建UPDATE子句
            update_clauses = [f'"{col}"=EXCLUDED."{col}"' for col in col_list]
            sql_to_execute += ','.join(update_clauses)

        if show_sql:
            print(sql_to_execute)
            print(value_list[0] if value_list else "No data")

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                res = cursor.executemany(sql_to_execute, value_list)
                conn.commit()
                affected_rows = cursor.rowcount
                print(f"{table_name} 批量插入影响行数: {affected_rows}")
                return affected_rows
        except Exception as e:
            conn.rollback()
            print(f"批量插入失败: {e}")
            raise e

    def insert_many_pd(self, data_pd, table_name, show_msg=False, insert_type="ignore"):
        """批量插入pandas DataFrame数据

        Args:
            data_pd: pandas DataFrame数据
            table_name: 表名
            show_msg: 是否显示详细信息
            insert_type: 插入类型 "ignore" 或 "replace"
        """
        if data_pd.empty:
            return 0

        col_list = data_pd.columns.tolist()
        values = []

        for i in range(data_pd.shape[0]):
            row = data_pd.iloc[i]
            values.append(tuple(row.tolist()))

        if show_msg:
            print(f"列名: {col_list}")
            print(f"数据行数: {len(values)}")

        return self.insert_many(
            col_list=col_list,
            value_list=values,
            table_name=table_name,
            insert_type=insert_type
        )

    def pd2db(self, data_pd, table_name, show_msg=False, insert_type="ignore"):
        """pandas DataFrame导入数据库

        Args:
            data_pd: pandas DataFrame数据
            table_name: 表名
            show_msg: 是否显示详细信息
            insert_type: 插入类型 "ignore" 或 "replace"
        """
        if data_pd.empty:
            print("DataFrame为空，无需导入")
            return 0

        # 将列名转换为大写以符合数据库规范
        tmp_pd = data_pd.copy()
        tmp_pd.columns = tmp_pd.columns.str.upper()

        if show_msg:
            print(f"导入表名: {table_name}")
            print(f"列名: {tmp_pd.columns.tolist()}")
            print(f"数据行数: {tmp_pd.shape[0]}")

        return self.insert_many_pd(data_pd=tmp_pd, table_name=table_name, show_msg=show_msg, insert_type=insert_type)

    def pd2db_batch(self, df, table_name, batch_size=10000, show_msg=False, insert_type="ignore"):
        """批量导入pandas DataFrame数据（分批处理）

        Args:
            df: pandas DataFrame数据
            table_name: 表名
            batch_size: 批次大小，默认10000行
            show_msg: 是否显示详细信息
            insert_type: 插入类型 "ignore" 或 "replace"
        """
        if df.empty:
            print("DataFrame为空，无需导入")
            return 0

        total_rows = len(df)
        total_affected = 0

        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)

            if show_msg:
                print(f"处理批次: {start_idx} - {end_idx} / {total_rows}")

            batch = df.iloc[start_idx:end_idx]
            affected_rows = self.pd2db(batch, table_name, show_msg=show_msg, insert_type=insert_type)
            total_affected += affected_rows

        print(f"批量导入完成，总计影响行数: {total_affected}")
        return total_affected

    def get_table_info(self, table_name, show_sql=False):
        """获取表结构信息

        Args:
            table_name: 表名
            show_sql: 是否显示SQL语句

        Returns:
            pd.DataFrame: 表结构信息
        """
        sql = f"""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        return self.select(sql, show_sql=show_sql)

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，自动关闭连接"""
        self.close_connection()


class SqLite():
    def __init__(self,db="vo.db"):
        # 连接到数据库（如果数据库文件不存在，会自动创建）
        self.conn = sqlite3.connect('vo.db')

    def exec(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def select(self, sql, columns=None):
        cursor = self.conn.cursor()
        # 查询数据
        cursor.execute(sql)
        rows = cursor.fetchall()
        if columns:
            df = pd.DataFrame(rows, columns=columns)
        else:
            df = pd.DataFrame(rows)
        cursor.close()
        return df 
        
    def close(self):
        self.conn.close()

    def init_table(self):
        database_schema_string = """
        CREATE TABLE orders (
            id INT PRIMARY KEY NOT NULL, 
            customer_id INT NOT NULL, 
            product_id STR NOT NULL, 
            price DECIMAL(10,2) NOT NULL, 
            status INT NOT NULL, -- 订单状态，整数类型，0-代表待支付，1-代表已支付，2-代表已退款
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pay_time TIMESTAMP 
        );
        """
                
        cursor = self.conn.cursor()
        try:
            cursor.execute(database_schema_string)
        except Exception as e:
            return  

        mock_data = [
            (1, 1001, 'aa1', 10.0, 1, '2025-06-12 10:00:00', ''),
            (2, 1001, 'aa2', 10.0, 1, '2025-06-16 11:00:00', '2025-08-16 12:00:00'),
            (3, 1002, 'bb1', 10.0, 0, '2025-10-17 12:30:00', '2025-08-17 13:00:00'),
            (4, 1003, 'bb2', 10.0, 0, '2025-10-17 12:30:00', '2025-08-17 13:00:00'),
            (5, 1003, 'cc', 10.0, 0, '2025-10-20 14:00:00', '2025-08-20 15:00:00'),
            (6, 1002, 'dd', 10.0, 2, '2025-10-28 16:00:00', '')
        ]

        for record in mock_data:
            cursor.execute('''
            INSERT INTO orders (id, customer_id, product_id, price, status, create_time, pay_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', record)

        self.conn.commit()
        
    def select_order(self):
        sql = "select id, customer_id, product_id, price, status, create_time, pay_time from orders" 
        df = self.select(sql,columns=["id", "customer_id", "product_id", "price", "status", "create_time", "pay_time"])
        return df 

    def select_single(self, sql, columns=None):
        """单值查询"""
        res = self.select(sql)
        if res.shape[0]>0:
            value = res.iloc[0][0]
            return value 
        return None 
     
def test():
    # 直接使用本地模块，避免包名冲突
    reset_passwd({"db1.username":"automng",
                    "db1.password":"Automng_123",
                    "db1.host":"11.11.11.11",
                    "db1.port":13301,
                    "db1.database":"db1",
                    "db1.charset":"utf8",
                    "report.username":"aaa",
                    "report.password":"aaabbbcccddd",
                    "report.url":"10.11.111.11:1521/orcl"})

    db = MyDb(name='db1')
    try:
        db.select("select version()")
    except Exception as e:
        print(f"MySQL连接测试失败（预期）: {e}")


    sdb = SqLite()
    sql= '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
    '''
    sdb.exec(sql)
    #插入数据
    sdb.exec("INSERT INTO users (name, age) VALUES ('Alice', 25)")
    sdb.exec("INSERT INTO users (name, age) VALUES ('Bob', 30)")
    sql = "SELECT * FROM users"
    sdb.select(sql, columns=["id","name","age"])


    sdb.init_table()
    sdb.select_order()

    # 高斯数据库使用示例
    print("\n=== 高斯数据库使用示例 ===")
    if GAUSSDB_AVAILABLE:
        print("高斯数据库依赖包已安装，可以使用 GaussDb 类")
        print("使用示例:")
        print("from tpf.db import GaussDb, update_passwd")
        print("")
        print("# 配置高斯数据库连接信息")
        print("update_passwd({")
        print("    'gaussdb.host': 'localhost',")
        print("    'gaussdb.port': 5432,")
        print("    'gaussdb.username': 'gaussdb',")
        print("    'gaussdb.password': 'password',")
        print("    'gaussdb.database': 'testdb'")
        print("})")
        print("")
        print("# 使用高斯数据库")
        print("with GaussDb('gaussdb') as gdb:")
        print("    # 查询数据")
        print("    result = gdb.select('SELECT * FROM test_table')")
        print("    # 执行SQL")
        print("    gdb.exec('INSERT INTO test_table (name) VALUES (%s)', ['test'])")
        print("    # 批量插入")
        print("    gdb.insert_many(['name'], [('name1'), ('name2')], 'test_table')")
        print("    # DataFrame导入")
        print("    gdb.pd2db(df, 'test_table')")
    else:
        print("高斯数据库依赖包未安装，请运行: pip install psycopg2-binary")



def test_ora_plsql():
    from tpf.db import OracleDb
    db = OracleDb(name="aml")
    # 执行带表名参数的 PL/SQL（方案1：使用动态SQL）
    sql = """
    declare
        v_count number;
        v_sql varchar2(1000);
    begin
        v_sql := 'select count(*) from ' || :table_name||' where rownum<3 ';
        execute immediate v_sql into v_count;
        dbms_output.put_line('Count: ' || v_count);
    end;
    """
    db.exec_plsql(sql,bind_params={'table_name': 'bb11_trans'})

    
def test_ora_psql_with_output_params():
    from tpf.db import OracleDb
    import cx_Oracle  # 导入必要的类型定义
    db = OracleDb(name="aml")
    sql = """
    declare
        v_count number;
        v_sql varchar2(1000);
    begin
        v_sql := 'select count(*) from ' || :table_name ;
        if :where_clause is not null then
            v_sql := v_sql || ' where ' || :where_clause;
        end if;
        execute immediate v_sql into v_count;
        dbms_output.put_line('Total count: ' || v_count);
        :out_count := v_count;
    end;
    """
    result = db.exec_with_output_params(sql, bind_params={
            'table_name': 'bb11_trans',
            'where_clause': 'rownum<3 '
        }, out_params={'out_count': cx_Oracle.NUMBER})
    print(result)

def test_procedure_call():
    from tpf.db import OracleDb
    db = OracleDb(name="aml")
    db.exec_proc("proc_create_trans",
        in_params={'p_start_date': '2025-07-01', 'p_end_date': '2025-07-31'},
        out_params={})
     
        
if __name__=="__main__":
    test_procedure_call()
    print("----------over -------")
