# oracle_plsql_executor.py
import cx_Oracle
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from contextlib import contextmanager
import os
import time

class OraclePLSQLExecutor:
    """
    Oracle PL/SQL 执行器 - 封装所有 cx_Oracle 相关的 PL/SQL 块操作
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 dsn: Optional[str] = None, name: Optional[str] = None, **kwargs):
        """
        初始化 Oracle PL/SQL 执行器

        Args:
            username: 数据库用户名 (可选，如果提供name则会从配置中获取)
            password: 数据库密码 (可选，如果提供name则会从配置中获取)
            dsn: 数据库连接字符串 (可选，如果提供name则会从配置中获取)
            name: 配置名称，用于从配置字典中获取连接信息
            **kwargs: 其他连接参数
                - min: 连接池最小连接数
                - max: 连接池最大连接数
                - increment: 连接池增量
                - encoding: 编码格式
        """
        self.name = name
        self.connection_pool = None
        self.connection = None
        self.pool_params = kwargs

        # 设置日志（在配置获取之前设置）
        self.logger = self._setup_logger()

        # 如果提供了name，则从配置中获取连接信息
        if name and (not username or not password or not dsn):
            # self.logger.info(f"正在从配置中获取连接信息，配置名称: {name}")
            config = self._get_db_config(name)
            username = username or config.get('username')
            password = password or config.get('password')
            dsn = dsn or config.get('url')

        # 验证必要的参数
        if not username or not password or not dsn:
            raise ValueError("必须提供 username、password、dsn 参数，或者通过 name 参数指定配置名称")

        self.username = username
        self.password = password
        self.dsn = dsn

        # self.logger.info(f"OraclePLSQLExecutor 初始化完成，用户: {username}")

    def _get_db_config(self, name: str) -> Dict[str, str]:
        """
        根据配置名称获取数据库连接配置信息

        Args:
            name: 配置名称

        Returns:
            Dict[str, str]: 包含 username, password, url 的配置字典
        """
        try:
            # 参考db.py中的配置获取方式
            db_dict = self._load_db_config()

            if not db_dict:
                raise ValueError(f"数据库配置文件为空或不存在")

            # 获取配置信息
            username = db_dict.get(f"{name}.username")
            password = db_dict.get(f"{name}.password")
            url = db_dict.get(f"{name}.url")

            if not username or not password or not url:
                available_configs = []
                for key in db_dict.keys():
                    if key.endswith('.username'):
                        config_name = key.replace('.username', '')
                        available_configs.append(config_name)

                raise ValueError(
                    f"配置名称 '{name}' 的连接信息不完整。\n"
                    f"缺失信息: username={bool(username)}, password={bool(password)}, url={bool(url)}\n"
                    f"可用的配置名称: {available_configs}"
                )

            config = {
                'username': username,
                'password': password,
                'url': url
            }

            # self.logger.info(f"成功获取配置 '{name}' 的数据库连接信息")
            return config

        except Exception as e:
            self.logger.error(f"获取配置 '{name}' 失败: {e}")
            raise

    def _load_db_config(self) -> Dict[str, str]:
        """
        加载数据库配置文件

        Returns:
            Dict[str, str]: 数据库配置字典
        """
        try:
            # 参考db.py中的配置文件加载方式
            local_file_path = os.path.abspath(__file__)
            father_path = os.path.abspath(os.path.dirname(local_file_path) + os.path.sep + ".")
            file_path = os.path.join(father_path, "db.db")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"数据库配置文件不存在: {file_path}")

            with open(file_path, 'r', encoding="utf-8") as f:
                config_content = f.read()
                db_dict = eval(config_content)  # 注意：生产环境中应使用更安全的配置解析方式

            return db_dict

        except Exception as e:
            self.logger.error(f"加载数据库配置文件失败: {e}")
            raise

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f'OraclePLSQLExecutor_{id(self)}')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def connect(self, use_pool: bool = False) -> bool:
        """
        连接到 Oracle 数据库
        
        Args:
            use_pool: 是否使用连接池
            
        Returns:
            bool: 连接是否成功
        """
        try:
            if use_pool:
                self.connection_pool = cx_Oracle.SessionPool(
                    user=self.username,
                    password=self.password,
                    dsn=self.dsn,
                    min=self.pool_params.get('min', 1),
                    max=self.pool_params.get('max', 5),
                    increment=self.pool_params.get('increment', 1),
                    encoding=self.pool_params.get('encoding', 'UTF-8')
                )
                self.connection = self.connection_pool.acquire()
            else:
                self.connection = cx_Oracle.connect(
                    user=self.username,
                    password=self.password,
                    dsn=self.dsn,
                    encoding=self.pool_params.get('encoding', 'UTF-8')
                )
            
            self.logger.info("数据库连接成功!")
            return True
            
        except cx_Oracle.Error as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        try:
            if self.connection:
                if self.connection_pool:
                    self.connection_pool.release(self.connection)
                    self.connection_pool.close()
                else:
                    self.connection.close()
                self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭连接时出错: {e}")

    def is_connection_valid(self) -> bool:
        """
        检查数据库连接是否有效

        Returns:
            bool: 连接是否有效
        """
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchall()
            cursor.close()
            return True
        except Exception:
            return False

    def ensure_connection(self) -> bool:
        """
        确保数据库连接有效，如果无效则尝试重新连接

        Returns:
            bool: 连接是否有效
        """
        if not self.is_connection_valid():
            self.logger.warning("数据库连接无效，尝试重新连接...")
            return self.connect()
        return True

    @contextmanager
    def get_cursor(self):
        """获取游标的上下文管理器"""
        cursor = None
        try:
            # 检查连接是否有效
            if not self.connection:
                raise Exception("数据库连接未建立或已关闭")

            cursor = self.connection.cursor()
            yield cursor

        except Exception as e:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            raise e
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

    def enable_dbms_output(self, buffer_size: int = 1000000) -> bool:
        """
        启用 DBMS_OUTPUT
        
        Args:
            buffer_size: 缓冲区大小
            
        Returns:
            bool: 是否启用成功
        """
        try:
            with self.get_cursor() as cursor:
                cursor.callproc("dbms_output.enable", [buffer_size])
            return True
        except cx_Oracle.Error as e:
            self.logger.error(f"启用 DBMS_OUTPUT 失败: {e}")
            return False

    def get_dbms_output(self) -> List[str]:
        """
        获取 DBMS_OUTPUT 内容

        Returns:
            List[str]: 输出行列表
        """
        lines = []
        try:
            with self.get_cursor() as cursor:
                # 使用 get_line 逐行获取，更稳定
                while True:
                    line_var = cursor.var(cx_Oracle.STRING)
                    status_var = cursor.var(cx_Oracle.NUMBER)

                    # 调用 dbms_output.get_line，返回单行
                    cursor.callproc("dbms_output.get_line", (line_var, status_var))

                    # status_var = 0 表示成功获取一行，1 表示没有更多行
                    if status_var.getvalue() == 0:
                        line = line_var.getvalue()
                        if line:
                            lines.append(line)
                    else:
                        break

        except cx_Oracle.Error as e:
            self.logger.error(f"获取 DBMS_OUTPUT 失败: {e}")

        return lines

    def execute_plsql_block(self, plsql_block: str, 
                           bind_params: Optional[Dict] = None,
                           enable_output: bool = True,
                           auto_commit: bool = False) -> Dict[str, Any]:
        """
        执行 PL/SQL 匿名块
        
        Args:
            plsql_block: PL/SQL 块代码
            bind_params: 绑定参数字典
            enable_output: 是否启用 DBMS_OUTPUT
            auto_commit: 是否自动提交
            
        Returns:
            Dict: 执行结果信息
        """
        start_time = time.time()
        result = {
            'success': False,
            'execution_time': 0,
            'output': [],
            'error': None
        }
        
        try:
            # 确保连接有效
            if not self.ensure_connection():
                raise Exception("无法建立有效的数据库连接")

            if enable_output:
                self.enable_dbms_output()

            with self.get_cursor() as cursor:
                # 执行 PL/SQL 块
                if bind_params:
                    cursor.execute(plsql_block, bind_params)
                else:
                    cursor.execute(plsql_block)
                
                # 获取输出
                if enable_output:
                    result['output'] = self.get_dbms_output()
                
                # 提交事务
                if auto_commit:
                    self.connection.commit()
                
                result['success'] = True
                # self.logger.info("PL/SQL 块执行成功")
                
        except cx_Oracle.Error as e:
            error_obj = e.args[0] if e.args else e
            result['error'] = {
                'code': getattr(error_obj, 'code', 'UNKNOWN'),
                'message': str(error_obj)
            }
            self.logger.error(f"PL/SQL 执行失败: {error_obj}")
            
            # 发生错误时回滚
            try:
                self.connection.rollback()
            except:
                pass
                
        finally:
            result['execution_time'] = round(time.time() - start_time, 3)
            
        return result

    def execute_dynamic_partition_script(self, start_date: str, end_date: str, 
                                       table_name: str = "bb11_trans1") -> Dict[str, Any]:
        """
        执行动态分区创建脚本
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            table_name: 表名
            
        Returns:
            Dict: 执行结果
        """
        plsql_block = f"""
        declare
            v_start_date date := to_date(:start_date, 'yyyy-mm-dd');
            v_end_date date := to_date(:end_date, 'yyyy-mm-dd');
            v_current_date date;
            v_partition_clauses varchar2(32767) := '';
            v_sql_create_table clob;
            v_table_exists number;
        begin
            -- 检查表是否存在
            select count(*) into v_table_exists 
            from user_tables 
            where table_name = upper('{table_name}');
            
            -- 清理旧表（如果存在）
            if v_table_exists > 0 then
                execute immediate 'drop table {table_name} cascade constraints';
                dbms_output.put_line('旧表删除成功: {table_name}');
            else
                dbms_output.put_line('表不存在，无需删除: {table_name}');
            end if;
            
            -- 生成分区子句
            v_current_date := v_start_date;
            while v_current_date <= v_end_date loop
                v_partition_clauses := v_partition_clauses || 
                    'partition p_' || to_char(v_current_date, 'YYYYMMDD') ||
                    ' values less than (to_date(''' || 
                    to_char(v_current_date + 1, 'YYYY-MM-DD') || 
                    ''', ''YYYY-MM-DD'')), ';
                v_current_date := v_current_date + 1;
            end loop;
            
            -- 移除最后的逗号和空格
            v_partition_clauses := rtrim(v_partition_clauses, ', ');
            
            -- 创建新表
            v_sql_create_table := '
                create table {table_name} (
                    trans_id number,
                    trans_date date,
                    amount number(15,2),
                    description varchar2(200)
                )
                partition by range (trans_date) (' || 
                v_partition_clauses || 
                ')';
                
            -- 执行创建表语句
            execute immediate v_sql_create_table;
            dbms_output.put_line('新表创建成功: {table_name}');
            dbms_output.put_line('分区范围: ' || :start_date || ' 到 ' || :end_date);
            
        exception
            when others then
                dbms_output.put_line('错误代码: ' || sqlcode);
                dbms_output.put_line('错误信息: ' || sqlerrm);
                raise;
        end;
        """
        
        bind_params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self.execute_plsql_block(plsql_block, bind_params, auto_commit=True)

    def execute_with_output_params(self, plsql_block: str,
                                 bind_params: Optional[Dict] = None,
                                 out_params: Dict[str, Any] = None,
                                 enable_output: bool = True,
                                 auto_commit: bool = False) -> Dict[str, Any]:
        """
        执行带有输出参数的 PL/SQL 块

        Args:
            plsql_block: PL/SQL 块代码
            bind_params: 输入参数字典 {参数名: 参数值}
            out_params: 输出参数定义 {参数名: 参数类型}
            enable_output: 是否启用 DBMS_OUTPUT
            auto_commit: 是否自动提交

        Returns:
            Dict: 执行结果和输出参数值
        """
        result = {
            'success': False,
            'output_params': {},
            'execution_time': 0,
            'error': None
        }
        
        start_time = time.time()

        # 参数验证
        if not out_params:
            raise ValueError("out_params 参数不能为空")

        try:
            # 确保连接有效
            if not self.ensure_connection():
                raise Exception("无法建立有效的数据库连接")

            # 启用DBMS_OUTPUT（如果需要）
            if enable_output:
                self.enable_dbms_output()

            with self.get_cursor() as cursor:
                # 准备所有参数字典（输入参数 + 输出参数）
                all_params = {}

                # 添加输入参数
                if bind_params:
                    all_params.update(bind_params)

                # 准备输出变量
                out_vars = {}
                for param_name, param_type in out_params.items():
                    if param_type == cx_Oracle.NUMBER:
                        out_vars[param_name] = cursor.var(cx_Oracle.NUMBER)
                    elif param_type == cx_Oracle.STRING:
                        out_vars[param_name] = cursor.var(cx_Oracle.STRING)
                    elif param_type == cx_Oracle.DATETIME:
                        out_vars[param_name] = cursor.var(cx_Oracle.DATETIME)
                    elif param_type == cx_Oracle.CLOB:
                        out_vars[param_name] = cursor.var(cx_Oracle.CLOB)
                    else:
                        out_vars[param_name] = cursor.var(param_type)

                    # 添加到总参数字典
                    all_params[param_name] = out_vars[param_name]

                # 执行 PL/SQL 块
                cursor.execute(plsql_block, all_params)

                # 获取DBMS_OUTPUT（如果启用）- 在cursor关闭前获取
                dbms_output = []
                if enable_output:
                    # 在同一个cursor中获取DBMS_OUTPUT
                    try:
                        # 使用 get_line 逐行获取，更稳定
                        while True:
                            line_var = cursor.var(cx_Oracle.STRING)
                            status_var = cursor.var(cx_Oracle.NUMBER)

                            # 调用 dbms_output.get_line，返回单行
                            cursor.callproc("dbms_output.get_line", (line_var, status_var))

                            # status_var = 0 表示成功获取一行，1 表示没有更多行
                            if status_var.getvalue() == 0:
                                line = line_var.getvalue()
                                if line:
                                    dbms_output.append(line)
                            else:
                                break
                    except Exception as e:
                        self.logger.warning(f"获取DBMS_OUTPUT失败: {e}")

                # 获取输出参数值 - 在cursor关闭前获取
                for param_name, var_obj in out_vars.items():
                    result['output_params'][param_name] = var_obj.getvalue()

                # 提交事务（如果需要）
                if auto_commit:
                    self.connection.commit()

                result['dbms_output'] = dbms_output
                result['success'] = True
                self.logger.info("带输出参数的 PL/SQL 执行成功")
                
        except cx_Oracle.Error as e:
            error_obj = e.args[0] if e.args else e
            result['error'] = {
                'code': getattr(error_obj, 'code', 'UNKNOWN'),
                'message': str(error_obj)
            }
            self.logger.error(f"执行失败: {error_obj}")
            
        finally:
            result['execution_time'] = round(time.time() - start_time, 3)
            
        return result

    def execute_count_query(self, table_name: str, where_clause: Optional[str] = None) -> Dict[str, Any]:
        """
        执行表行数统计查询，支持动态表名和WHERE条件

        Args:
            table_name: 表名
            where_clause: 可选的WHERE条件

        Returns:
            Dict: 执行结果，包含行数统计信息
        """
        plsql_block = """
        declare
            v_count number;
            v_sql clob;
        begin
            v_sql := 'select count(*) from ' || :table_name;
            if :where_clause is not null then
                v_sql := v_sql || ' where ' || :where_clause;
            end if;

            execute immediate v_sql into v_count;
            dbms_output.put_line('表 ' || :table_name || ' 的行数: ' || v_count);
            :out_count := v_count;
        end;
        """

        bind_params = {
            'table_name': table_name,
            'where_clause': where_clause
        }

        out_params = {
            'out_count': cx_Oracle.NUMBER
        }

        return self.execute_with_output_params(plsql_block, bind_params, out_params)

    def execute_dynamic_select(self, table_name: str, select_clause: str = "*",
                              where_clause: Optional[str] = None,
                              order_clause: Optional[str] = None,
                              limit_clause: Optional[str] = None) -> Dict[str, Any]:
        """
        执行动态SELECT查询，支持动态表名和各种SQL子句

        Args:
            table_name: 表名
            select_clause: SELECT子句，默认为"*"
            where_clause: WHERE条件
            order_clause: ORDER BY子句
            limit_clause: LIMIT子句（Oracle使用ROWNUM）

        Returns:
            Dict: 执行结果
        """
        plsql_block = """
        declare
            v_sql clob;
            v_cursor sys_refcursor;
            v_row_count number := 0;
        begin
            v_sql := 'select ' || :select_clause || ' from ' || :table_name;

            if :where_clause is not null then
                v_sql := v_sql || ' where ' || :where_clause;
            end if;

            if :order_clause is not null then
                v_sql := v_sql || ' order by ' || :order_clause;
            end if;

            if :limit_clause is not null then
                v_sql := 'select * from (' || v_sql || ') where rownum <= ' || :limit_clause;
            end if;

            dbms_output.put_line('执行SQL: ' || v_sql);

            -- 注意：这里只是示例，实际使用时需要根据需求调整
            -- 因为PL/SQL块中不能直接返回查询结果集
            :out_sql := v_sql;
        end;
        """

        bind_params = {
            'select_clause': select_clause,
            'table_name': table_name,
            'where_clause': where_clause,
            'order_clause': order_clause,
            'limit_clause': limit_clause
        }

        out_params = {
            'out_sql': cx_Oracle.CLOB
        }

        return self.execute_with_output_params(plsql_block, bind_params, out_params)

    def call_stored_procedure(self, procedure_name: str, 
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
        result = {
            'success': False,
            'output_params': {},
            'execution_time': 0,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            with self.get_cursor() as cursor:
                # 准备参数
                all_params = {}
                
                # 输入参数
                if in_params:
                    all_params.update(in_params)
                
                # 输出参数
                out_vars = {}
                if out_params:
                    for param_name, param_type in out_params.items():
                        if param_type == cx_Oracle.NUMBER:
                            out_vars[param_name] = cursor.var(cx_Oracle.NUMBER)
                        elif param_type == cx_Oracle.STRING:
                            out_vars[param_name] = cursor.var(cx_Oracle.STRING)
                        else:
                            out_vars[param_name] = cursor.var(param_type)
                    all_params.update(out_vars)
                
                # 调用存储过程
                cursor.callproc(procedure_name, keywordParameters=all_params)
                
                # 获取输出参数值
                if out_params:
                    for param_name in out_params.keys():
                        result['output_params'][param_name] = out_vars[param_name].getvalue()
                
                result['success'] = True
                self.logger.info(f"存储过程 {procedure_name} 调用成功")
                
        except cx_Oracle.Error as e:
            error_obj = e.args[0] if e.args else e
            result['error'] = {
                'code': getattr(error_obj, 'code', 'UNKNOWN'),
                'message': str(error_obj)
            }
            self.logger.error(f"存储过程调用失败: {error_obj}")
            
        finally:
            result['execution_time'] = round(time.time() - start_time, 3)
            
        return result

    def execute_batch_plsql(self, plsql_blocks: List[Tuple[str, Dict]], 
                          stop_on_error: bool = False) -> List[Dict[str, Any]]:
        """
        批量执行 PL/SQL 块
        
        Args:
            plsql_blocks: PL/SQL 块列表 [(plsql_block, bind_params), ...]
            stop_on_error: 遇到错误是否停止
            
        Returns:
            List[Dict]: 每个块的执行结果
        """
        results = []
        
        for i, (plsql_block, bind_params) in enumerate(plsql_blocks):
            self.logger.info(f"执行第 {i+1}/{len(plsql_blocks)} 个 PL/SQL 块")
            
            result = self.execute_plsql_block(plsql_block, bind_params)
            results.append(result)
            
            if not result['success'] and stop_on_error:
                self.logger.error(f"第 {i+1} 个块执行失败，停止批量执行")
                break
                
        return results

    def test_connection(self) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Returns:
            Dict: 连接测试结果
        """
        result = {
            'success': False,
            'database_version': None,
            'current_user': None,
            'current_date': None,
            'error': None
        }
        
        try:
            with self.get_cursor() as cursor:
                # 获取数据库版本
                cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
                version = cursor.fetchone()
                result['database_version'] = version[0] if version else None
                
                # 获取当前用户
                cursor.execute("SELECT USER FROM DUAL")
                user = cursor.fetchone()
                result['current_user'] = user[0] if user else None
                
                # 获取当前日期
                cursor.execute("SELECT SYSDATE FROM DUAL")
                current_date = cursor.fetchone()
                result['current_date'] = current_date[0] if current_date else None
                
                result['success'] = True
                self.logger.info("数据库连接测试成功")
                
        except cx_Oracle.Error as e:
            error_obj = e.args[0] if e.args else e
            result['error'] = {
                'code': getattr(error_obj, 'code', 'UNKNOWN'),
                'message': str(error_obj)
            }
            self.logger.error(f"连接测试失败: {error_obj}")
            
        return result

    def execute_dml_with_transaction(self, dml_statements: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """
        在事务中执行 DML 语句
        
        Args:
            dml_statements: DML 语句列表 [(sql, params), ...]
            
        Returns:
            Dict: 执行结果
        """
        result = {
            'success': False,
            'rows_affected': 0,
            'execution_time': 0,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            with self.get_cursor() as cursor:
                total_rows = 0
                
                for sql, params in dml_statements:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    total_rows += cursor.rowcount
                
                self.connection.commit()
                result['rows_affected'] = total_rows
                result['success'] = True
                self.logger.info(f"DML 事务执行成功，影响 {total_rows} 行")
                
        except cx_Oracle.Error as e:
            self.connection.rollback()
            error_obj = e.args[0] if e.args else e
            result['error'] = {
                'code': getattr(error_obj, 'code', 'UNKNOWN'),
                'message': str(error_obj)
            }
            self.logger.error(f"DML 事务执行失败: {error_obj}")
            
        finally:
            result['execution_time'] = round(time.time() - start_time, 3)
            
        return result


def test():
    # 设置 Oracle 客户端路径（如果需要）
    # os.environ['LD_LIBRARY_PATH'] = '/opt/oracle/instantclient_19_10'
    
    # 创建执行器实例
    executor = OraclePLSQLExecutor(
        username="your_username",
        password="your_password",
        dsn="10.14.120.80:1521/pdb"
    )
    
    try:
        # 连接数据库
        if executor.connect():
            # 测试连接
            test_result = executor.test_connection()
            print("连接测试结果:", test_result)
            
            # 执行动态分区脚本
            partition_result = executor.execute_dynamic_partition_script(
                start_date='2024-01-01',
                end_date='2024-01-07'
            )
            print("分区脚本执行结果:", partition_result)
            
            # 执行带输出参数的 PL/SQL
            plsql_with_output = """
            declare
                v_count number;
                v_message varchar2(100);
            begin
                select count(*) into v_count from user_tables;
                v_message := '用户表数量: ' || v_count;
                :out_count := v_count;
                :out_message := v_message;
                dbms_output.put_line(v_message);
            end;
            """
            
            output_result = executor.execute_with_output_params(
                plsql_with_output,
                out_params={
                    'out_count': cx_Oracle.NUMBER,
                    'out_message': cx_Oracle.STRING
                }
            )
            print("带输出参数的执行结果:", output_result)
            
    finally:
        # 关闭连接
        executor.close()


    # --------------------------------------------------
    # 基本使用示例2 
    executor = OraclePLSQLExecutor("user", "pass", "host:1521/service")
    executor.connect()

    # 执行 PL/SQL 块
    result = executor.execute_plsql_block("""
    begin
        -- 你的 PL/SQL 代码
        dbms_output.put_line('Hello World');
    end;
    """)

    # 执行带参数的 PL/SQL
    result = executor.execute_plsql_block("""
    declare
        v_count number;
    begin
        select count(*) into v_count from my_table;
        dbms_output.put_line('Count: ' || v_count);
    end;
    """, bind_params={})

    # 执行带表名参数的 PL/SQL（方案1：使用动态SQL）
    result = executor.execute_plsql_block("""
    declare
        v_count number;
        v_sql varchar2(1000);
    begin
        v_sql := 'select count(*) from ' || :table_name;
        execute immediate v_sql into v_count;
        dbms_output.put_line('Count: ' || v_count);
    end;
    """, bind_params={'table_name': 'my_table'})

    # 执行带表名参数的 PL/SQL（方案2：使用输出参数）
    result = executor.execute_with_output_params("""
    declare
        v_count number;
        v_sql varchar2(1000);
    begin
        v_sql := 'select count(*) from ' || :table_name;
        if :where_clause is not null then
            v_sql := v_sql || ' where ' || :where_clause;
        end if;
        execute immediate v_sql into v_count;
        dbms_output.put_line('Total count: ' || v_count);
        :out_count := v_count;
    end;
    """, bind_params={
        'table_name': 'my_table',
        'where_clause': 'status = ''ACTIVE'''
    }, out_params={'out_count': cx_Oracle.NUMBER})

    # 使用专门的方法进行表计数查询（推荐方式）
    count_result = executor.execute_count_query(
        table_name='my_table',
        where_clause='status = ''ACTIVE'''
    )
    print(f"表行数统计结果: {count_result}")

    # 使用动态SELECT查询方法
    select_result = executor.execute_dynamic_select(
        table_name='my_table',
        select_clause='id, name, status',
        where_clause='status = ''ACTIVE''',
        order_clause='id desc',
        limit_clause='10'
    )
    print(f"动态查询结果: {select_result}")

    # 调用存储过程
    result = executor.call_stored_procedure(
        "my_procedure",
        in_params={'p_input': 'value'},
        out_params={'p_output': cx_Oracle.STRING}
    )
    
    # --------------------------------------------------
    # 推荐方式（通过配置名称）：
    executor = OraclePLSQLExecutor(name="report")
    
    # --------------------------------------------------
    #混合方式：
    executor = OraclePLSQLExecutor(
        name="report",           # 从配置文件获取连接信息
        encoding="UTF-8",        # 直接提供其他参数
        min=1, max=10
    )


def test2():
    import cx_Oracle
    from tpf.db_ora import OraclePLSQLExecutor
    db = OraclePLSQLExecutor(name="aml")

    try:
        if not db.connect():
            print("❌ 数据库连接失败")
            return

        print("✅ 数据库连接成功")

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

        print("🔄 开始执行PL/SQL块...")
        # 移除WHERE条件，因为status字段可能不存在
        result = db.execute_with_output_params(sql, bind_params={
                'table_name': 'bb11_trans',
                'where_clause': ' rownum < 3'  # 移除status条件
            }, out_params={'out_count': cx_Oracle.NUMBER})
        print(f"表行数统计结果: {result}")

    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保关闭连接
        print("🔄 关闭数据库连接...")
        db.close()



# 使用示例和测试
if __name__ == "__main__":
    test2() 