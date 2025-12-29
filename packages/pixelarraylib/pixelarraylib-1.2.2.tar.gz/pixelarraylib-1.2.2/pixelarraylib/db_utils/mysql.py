import traceback
import pymysql
import aiomysql
import asyncio
from pixelarraylib.monitor.feishu import Feishu
import time
from pymysql.err import OperationalError

feishu_alert = Feishu("devtoolkit服务报警")


class MysqlUtils:
    def __init__(
        self,
        host,
        database,
        user,
        password,
        port,
        max_retries=3,
    ):
        """
        description:
            初始化MySQL工具类
        parameters:
            host(str): 数据库主机地址
            database(str): 数据库名称
            user(str): 数据库用户名
            password(str): 数据库密码
            port(int): 数据库端口
            max_retries(int): 最大重试次数，默认为3
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.max_retries = max_retries
        self.mysql = None
        self._connect()

    def _connect(self):
        """
        description:
            建立数据库连接，支持重试机制
        """
        for attempt in range(self.max_retries):
            try:
                self.mysql = pymysql.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    connect_timeout=60,
                    read_timeout=60,
                    write_timeout=60,
                    autocommit=True,
                )
                break  # 连接成功，跳出重试循环
            except OperationalError as e:
                if attempt < self.max_retries - 1:
                    print(
                        f"MySQL连接失败，正在重试 ({attempt + 1}/{self.max_retries}): {str(e)}"
                    )
                    time.sleep(2**attempt)  # 指数退避
                else:
                    print(f"MySQL连接最终失败: {traceback.format_exc()}")
                    raise

    def get_conn(self):
        """
        description:
            获取MySQL连接对象
        return:
            mysql_conn(pymysql.Connection): MySQL连接对象
        """
        return self.mysql

    def _ensure_connection(self):
        """
        description:
            确保连接有效，如果断开则重新连接
        """
        try:
            self.mysql.ping(reconnect=True)
        except Exception:
            self._connect()

    def get_db_name(self):
        """
        description:
            获取当前数据库名称
        return:
            database_name(str): 数据库名称
        """
        res = self.query("SELECT DATABASE();")
        database_name = res[0][0]
        return database_name

    def create_table(self, table_name, columns):
        """
        description:
            创建数据表
        parameters:
            table_name(str): 表名
            columns(list(tuple)): 列名和类型的元组列表
        return:
            flag(bool): 是否创建成功
        """
        sql = f"""
            CREATE TABLE {table_name} (
                {','.join([f'{col_name} {type}' for col_name, type in columns])}
            );
        """
        return self.execute_sql(sql)

    def add_column(self, table_name, column_name, column_type):
        """
        description:
            添加列
        parameters:
            table_name(str): 表名
            column_name(str): 列名
            column_type(str): 列类型
        return:
            flag(bool): 是否成功
        """
        sql = f"""
            ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};
        """
        return self.execute_sql(sql)

    def delete_column(self, table_name, column_name):
        """
        description:
            删除列
        parameters:
            table_name(str): 表名
            column_name(str): 列名
        return:
            flag(bool): 是否成功
        """
        sql = f"""
            ALTER TABLE {table_name} DROP COLUMN {column_name};
        """
        return self.execute_sql(sql)

    def get_table_names(self):
        """
        description:
            获取当前数据库中的所有表名
        return:
            table_names(list): 表名列表
        """
        res = self.query("SHOW TABLES;")
        table_names = [row[0] for row in res]
        return table_names

    def insert(self, table_name, rows, batch_size=100):
        """
        description:
            插入数据
        parameters:
            table_name(str): 表名
            rows(list(dict)): 数据
            batch_size(int): 每批插入的条数
        return:
            flag(bool): 是否成功
        """
        for i in range(0, len(rows), batch_size):
            batch_rows = rows[i : i + batch_size]
            values_str_list = []
            for row in batch_rows:
                values_str = ",".join([f"'{value}'" for value in row.values()])
                values_str = f"({values_str})"
                values_str_list.append(values_str)
            sql = f"""
                INSERT INTO {table_name} ({','.join(rows[0].keys())})
                VALUES
                {','.join(values_str_list)};
            """
            self.execute_sql(sql)
            print(f"insert {i} / {len(rows)} rows to {table_name}")
        return True

    def insert_or_update(self, table_name, rows, key_columns, batch_size=100):
        """
        description:
            插入数据，如果指定的键已存在则更新
        parameters:
            table_name(str): 表名
            rows(list(dict)): 数据
            key_columns(list): 作为唯一标识的列名列表
            batch_size(int): 每批插入的条数
        return:
            flag(bool): 是否成功
        """
        try:
            for i in range(0, len(rows), batch_size):
                batch_rows = rows[i : i + batch_size]
                values_str_list = []
                for row in batch_rows:
                    values_str = ",".join([f"'{value}'" for value in row.values()])
                    values_str = f"({values_str})"
                    values_str_list.append(values_str)

                update_str = ",".join(
                    [f"{k}=VALUES({k})" for k in rows[0].keys() if k not in key_columns]
                )
                on_duplicate_key = (
                    f"ON DUPLICATE KEY UPDATE {update_str}" if update_str else ""
                )

                sql = f"""
                    INSERT INTO {table_name} ({','.join(rows[0].keys())})
                    VALUES
                    {','.join(values_str_list)}
                    {on_duplicate_key};
                """
                self.execute_sql(sql)
                print(f"插入/更新 {i} / {len(rows)} 行到 {table_name}")
            return True
        except Exception as e:
            print(f"mysql-insert_or_update error {traceback.format_exc()}")
            return False

    def query(self, sql, convert_to_dict=False):
        """
        description:
            执行sql查询语句
        parameters:
            sql(str): sql语句
            convert_to_dict(bool): 是否将查询结果转换为字典
        return:
            result(list): 查询结果
        """
        allowed_sql_prefixes = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")
        assert (
            sql.lstrip().upper().startswith(allowed_sql_prefixes)
        ), f"sql 必须以 {', '.join(allowed_sql_prefixes)} 开头"
        try:
            self._ensure_connection()  # 确保连接有效
            cursor = self.mysql.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            if convert_to_dict:
                return [dict(zip(columns, row)) for row in result]
            return list(result)
        except Exception as e:
            print(f"mysql-query error {traceback.format_exc()}")
            return []
        finally:
            cursor.close()

    def execute_sql(self, sql):
        """
        description:
            执行sql语句
        parameters:
            sql(str): sql语句
        return:
            flag(bool): 是否成功
        """
        try:
            self._ensure_connection()  # 确保连接有效
            cursor = self.mysql.cursor()
            cursor.execute(sql)
            self.mysql.commit()
            return True
        except Exception as e:
            self.mysql.rollback()
            print(f"mysql-execute error {traceback.format_exc()}")
            return False
        finally:
            cursor.close()

    def clear_table(self, table_name):
        """
        description:
            清空数据表
        parameters:
            table_name(str): 表名
        return:
            flag(bool): 是否清空成功
        """
        sql = f"""
            TRUNCATE TABLE {table_name};
        """
        return self.execute_sql(sql)

    def delete_table(self, table_name):
        """
        description:
            删除数据表
        parameters:
            table_name(str): 表名
        return:
            flag(bool): 是否删除成功
        """
        sql = f"""
            DROP TABLE {table_name};
        """
        return self.execute_sql(sql)


class MysqlUtilsAsync:
    def __init__(
        self,
        host,
        database,
        user,
        password,
        port,
        max_retries=3,
    ):
        """
        description:
            初始化异步MySQL工具类
        parameters:
            host(str): 数据库主机地址
            database(str): 数据库名称
            user(str): 数据库用户名
            password(str): 数据库密码
            port(int): 数据库端口
            max_retries(int): 最大重试次数，默认为3
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.max_retries = max_retries
        self.async_mysql = None

    async def get_async_conn(self):
        """
        description:
            获取异步MySQL连接对象
        return:
            async_mysql_conn(aiomysql.Connection): 异步MySQL连接对象
        """
        if self.async_mysql is None:
            await self._async_connect()
        return self.async_mysql

    async def _async_connect(self):
        """
        description:
            建立异步数据库连接，支持重试机制
        """
        for attempt in range(self.max_retries):
            try:
                self.async_mysql = await aiomysql.connect(
                    host=self.host,
                    db=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    connect_timeout=60,
                    autocommit=True,
                )
                break  # 连接成功，跳出重试循环
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(
                        f"异步MySQL连接失败，正在重试 ({attempt + 1}/{self.max_retries}): {str(e)}"
                    )
                    await asyncio.sleep(2**attempt)  # 指数退避
                else:
                    print(
                        f"异步MySQL连接最终失败: {traceback.format_exc()}"
                    )
                    raise

    async def _async_ensure_connection(self):
        """
        description:
            确保异步连接有效，如果断开则重新连接
        """
        try:
            if self.async_mysql is None:
                await self._async_connect()
            else:
                # aiomysql没有ping方法，直接尝试执行简单查询
                cursor = await self.async_mysql.cursor()
                await cursor.execute("SELECT 1")
                await cursor.close()
        except Exception:
            await self._async_connect()

    async def get_db_name(self):
        """
        description:
            异步获取当前数据库名称
        return:
            database_name(str): 数据库名称
        """
        res = await self.query("SELECT DATABASE();")
        database_name = res[0][0]
        return database_name

    async def create_table(self, table_name, columns):
        """
        description:
            异步创建数据表
        parameters:
            table_name(str): 表名
            columns(list(tuple)): 列名和类型的元组列表
        return:
            flag(bool): 是否创建成功
        """
        sql = f"""
            CREATE TABLE {table_name} (
                {','.join([f'{col_name} {type}' for col_name, type in columns])}
            );
        """
        return await self.execute_sql(sql)

    async def add_column(self, table_name, column_name, column_type):
        """
        description:
            异步添加列
        parameters:
            table_name(str): 表名
            column_name(str): 列名
            column_type(str): 列类型
        return:
            flag(bool): 是否成功
        """
        sql = f"""
            ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};
        """
        return await self.execute_sql(sql)

    async def delete_column(self, table_name, column_name):
        """
        description:
            异步删除列
        parameters:
            table_name(str): 表名
            column_name(str): 列名
        return:
            flag(bool): 是否成功
        """
        sql = f"""
            ALTER TABLE {table_name} DROP COLUMN {column_name};
        """
        return await self.execute_sql(sql)

    async def get_table_names(self):
        """
        description:
            异步获取当前数据库中的所有表名
        return:
            table_names(list): 表名列表
        """
        res = await self.query("SHOW TABLES;")
        table_names = [row[0] for row in res]
        return table_names

    async def insert(self, table_name, rows, batch_size=100):
        """
        description:
            异步插入数据
        parameters:
            table_name(str): 表名
            rows(list(dict)): 数据
            batch_size(int): 每批插入的条数
        return:
            flag(bool): 是否成功
        """
        for i in range(0, len(rows), batch_size):
            batch_rows = rows[i : i + batch_size]
            values_str_list = []
            for row in batch_rows:
                values_str = ",".join([f"'{value}'" for value in row.values()])
                values_str = f"({values_str})"
                values_str_list.append(values_str)
            sql = f"""
                INSERT INTO {table_name} ({','.join(rows[0].keys())})
                VALUES
                {','.join(values_str_list)};
            """
            await self.execute_sql(sql)
            print(f"insert {i} / {len(rows)} rows to {table_name}")
        return True

    async def insert_or_update(self, table_name, rows, key_columns, batch_size=100):
        """
        description:
            异步插入数据，如果指定的键已存在则更新
        parameters:
            table_name(str): 表名
            rows(list(dict)): 数据
            key_columns(list): 作为唯一标识的列名列表
            batch_size(int): 每批插入的条数
        return:
            flag(bool): 是否成功
        """
        try:
            for i in range(0, len(rows), batch_size):
                batch_rows = rows[i : i + batch_size]
                values_str_list = []
                for row in batch_rows:
                    values_str = ",".join([f"'{value}'" for value in row.values()])
                    values_str = f"({values_str})"
                    values_str_list.append(values_str)

                update_str = ",".join(
                    [f"{k}=VALUES({k})" for k in rows[0].keys() if k not in key_columns]
                )
                on_duplicate_key = (
                    f"ON DUPLICATE KEY UPDATE {update_str}" if update_str else ""
                )

                sql = f"""
                    INSERT INTO {table_name} ({','.join(rows[0].keys())})
                    VALUES
                    {','.join(values_str_list)}
                    {on_duplicate_key};
                """
                await self.execute_sql(sql)
                print(f"插入/更新 {i} / {len(rows)} 行到 {table_name}")
            return True
        except Exception as e:
            print(
                f"mysql-insert_or_update_async error {traceback.format_exc()}"
            )
            return False

    async def query(self, sql, convert_to_dict=False):
        """
        description:
            异步执行sql查询语句
        parameters:
            sql(str): sql语句
            convert_to_dict(bool): 是否将查询结果转换为字典
        return:
            result(list): 查询结果
        """
        allowed_sql_prefixes = ("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")
        assert (
            sql.lstrip().upper().startswith(allowed_sql_prefixes)
        ), f"sql 必须以 {', '.join(allowed_sql_prefixes)} 开头"
        cursor = None
        try:
            await self._async_ensure_connection()  # 确保连接有效
            async_mysql = await self.get_async_conn()
            cursor = await async_mysql.cursor()
            await cursor.execute(sql)
            result = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            if convert_to_dict:
                return [dict(zip(columns, row)) for row in result]
            return list(result)
        except Exception as e:
            print(f"mysql-query_async error {traceback.format_exc()}")
            return []
        finally:
            if cursor:
                await cursor.close()

    async def execute_sql(self, sql):
        """
        description:
            异步执行sql语句
        parameters:
            sql(str): sql语句
        return:
            flag(bool): 是否成功
        """
        cursor = None
        try:
            await self._async_ensure_connection()  # 确保连接有效
            async_mysql = await self.get_async_conn()
            cursor = await async_mysql.cursor()
            await cursor.execute(sql)
            await async_mysql.commit()
            return True
        except Exception as e:
            async_mysql = await self.get_async_conn()
            await async_mysql.rollback()
            print(f"mysql-execute_async error {traceback.format_exc()}")
            return False
        finally:
            if cursor:
                await cursor.close()

    async def clear_table(self, table_name):
        """
        description:
            异步清空数据表
        parameters:
            table_name(str): 表名
        return:
            flag(bool): 是否清空成功
        """
        sql = f"""
            TRUNCATE TABLE {table_name};
        """
        return await self.execute_sql(sql)

    async def delete_table(self, table_name):
        """
        description:
            异步删除数据表
        parameters:
            table_name(str): 表名
        return:
            flag(bool): 是否删除成功
        """
        sql = f"""
            DROP TABLE {table_name};
        """
        return await self.execute_sql(sql)

    async def close(self):
        """
        description:
            关闭异步MySQL连接
        """
        if self.async_mysql:
            self.async_mysql.close()
            await self.async_mysql.wait_closed()
