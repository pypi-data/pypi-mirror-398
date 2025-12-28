#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/05/19 14:38 
# @Author : JY
"""
MySQL操作
"""
import pymysql
from pymysql.cursors import DictCursor
import datetime
import time
import sqlparse
from typing import Union,List,Tuple


class mysql:
    def __init__(self, config: dict = None, host: str = None, user: str = None, password: str = None,
                 database: str = None, port: int = 3306, charset: str = 'utf8mb4'):
        """
        初始化数据库连接参数
        默认的超时时间
            - 连接超时（connect_timeout）: 10 秒（单位：秒）
            - 读取超时（read_timeout）: None（无超时限制）
            - 写入超时（write_timeout）: None（无超时限制）
        """
        if config is None:
            config = {}
        self.config = {
            'host': config['host'] if config.get('host', False) else host,
            'user': config['user'] if config.get('user', False) else user,
            'password': config['password'] if config.get('password', False) else password,
            'database': config['db'] if config.get('db', False) else database,
            'port': config['port'] if config.get('port', False) else port,
            'charset': config['charset'] if config.get('charset', False) else charset,
            'cursorclass': config['cursor'] if config.get('cursor', False) else DictCursor,
            'autocommit': False  # 手动控制事务
        }

    def _get_connection(self, printInfo: bool = False):
        """获取数据库连接"""
        # return pymysql.connect(**self.config) # python=3.8.0会出问题，改成下面的
        conn = pymysql.connect(**self.config)

        # 包装连接对象，确保实现上下文管理器
        class ConnectionWrapper:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                if printInfo:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '连接',
                          f"{self.conn.host}:{self.conn.port}/{self.conn.db.decode('utf8')}")
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    self.conn.close()
                    if printInfo:
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '关闭',
                              f"{self.conn.host}:{self.conn.port}/{self.conn.db.decode('utf8')}")
                except Exception as e:
                    print(f"Warning: Failed to close connection: {e}")
                return False  # 不抑制异常，继续向上传播

        return ConnectionWrapper(conn)

    def select(self, sql: Union[str, List[str]], params=None, printInfo: bool = False) -> Union[List, Tuple[List]]:
        """
        执行查询语句（SELECT），返回结果\n
        :param sql: str的话就返回一个该sql的结果list   list传入多个SQL的话,就返回多个返回值,分别对应SQL的结果
        :param params:
        :param printInfo:
        :return:
        """
        with self._get_connection(printInfo=printInfo) as conn:
            with conn.cursor() as cursor:
                if printInfo:
                    start = time.time()
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始', sql)
                if isinstance(sql, str):
                    sql = [sql]
                sql = [one_sql for one_sql in sql if one_sql.strip() != '']
                result = []
                for one_sql in sql:
                    cursor.execute(one_sql, params)
                    one_result = cursor.fetchall()
                    one_result = one_result if one_result else []
                    result.append(one_result)
                if printInfo:
                    result_num = len(result[0]) if len(sql) == 1 else [len(i) for i in result]
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束',
                          '耗时: %s秒' % round((time.time() - start), 2), '结果: %s条' % result_num, sql)
                return result[0] if len(sql) == 1 else tuple(result)

    def select_one(self, sql: str, params=None, printInfo=False) -> dict:
        """执行查询语句，返回单行结果"""
        with self._get_connection(printInfo=printInfo) as conn:
            with conn.cursor() as cursor:
                if printInfo:
                    start = time.time()
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始', sql)
                cursor.execute(sql, params)
                result = cursor.fetchone()
                if printInfo:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束',
                          '耗时: %s秒' % round((time.time() - start), 2), '结果: 1条', sql)
                return result if result else {}

    def execute_sql(self, sql: str, params=None, printInfo=False) -> int:
        """执行更新操作（INSERT/UPDATE/DELETE）"""
        conn = None
        try:
            with self._get_connection(printInfo=printInfo) as conn:
                with conn.cursor() as cursor:
                    if printInfo:
                        start = time.time()
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始', sql)
                    cursor.execute(sql, params)
                    conn.commit()
                    if printInfo:
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束',
                              '耗时: %s秒' % round((time.time() - start), 2), '影响: %s条' % cursor.rowcount, sql)
                    return cursor.rowcount
        except pymysql.Error as e:
            try:
                # 关键：检查连接是否有效（conn.open判断连接状态）否则执行conn.rollback()也可能会报错导致程序二次崩溃
                if conn and conn.open:
                    conn.rollback()
            except Exception as rollback_err:
                pass
            raise Exception(str(e) + '\nRUN SQL: ' + sql) from None

    def update(self, table: str, setDict: dict, whereStr: str, returnSQL: bool = False, printInfo: bool = False) -> \
            Union[int, str]:
        sql = f"""UPDATE {table} SET """
        for key, value in setDict.items():
            if isinstance(value, str):
                if '"' in value:
                    value = value.replace('"', '\\"')
                value = '"' + value + '"'
            if value is None:
                value = 'NULL'
            sql += f"""{key}={value},"""
        sql = sql[:-1]
        sql += f""" WHERE {whereStr}"""
        if returnSQL:
            return sql
        return self.execute_sql(sql, None, printInfo)

    def delete(self, table: str, whereStr: str, limit=None, returnSQL=False, printInfo=False) -> Union[int, str]:
        sql = f"DELETE FROM {table} WHERE {whereStr}"
        if limit is not None:
            if isinstance(limit, int):
                sql += f" LIMIT {limit}"
            else:
                raise "limit参数需要为整数"
        if returnSQL:
            return sql
        return self.execute_sql(sql, None, printInfo)

    # INSERT IGNORE 的核心作用是静默处理违反约束的行，但它的影响范围不仅限于唯一索引冲突，还包括数据类型、空值、外键等约束
    def insert(self, table: str, data: Union[list, dict], returnSQL: bool = False, printInfo: bool = False,
               ignoreMode: bool = False) -> Union[int, str]:
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return 0
        if data.__len__() == 0:
            return 0
        # 判断有几个字段
        field_len = data[0].__len__()
        if field_len == 0:
            return 0
        filed_str = ''
        field_list = []
        for filed in data[0]:
            filed_str += '`' + filed + '`,'
            field_list.append(filed)
        filed_str = filed_str[:-1]
        ignoreMode = " IGNORE " if ignoreMode else " "
        sql = """INSERT%sINTO %s(%s) VALUES""" % (ignoreMode, table, filed_str)
        for item in data:
            if item.__len__() != field_len:
                raise RuntimeError('insert方法批量插入数据错误，插入数据长度不统一' + str(item))
            sql += """("""
            for filed in field_list:
                value = item[filed]
                if isinstance(value, str):
                    if '"' in value:
                        value = value.replace('"', '\\"')
                    value = '"' + value + '"'
                if value is None:
                    value = 'NULL'
                sql += f"""{value},"""
            sql = sql[:-1]
            sql += """),"""
        sql = sql[:-1]
        if returnSQL:
            return sql
        return self.execute_sql(sql, None, printInfo)

    def execute_manySQLs(self, sqls: Union[str, list] = None, sqls_from_file: str = None, printInfo=False,
                         printSql=False, batch_size: int = None, sleep: int = 0) -> list:
        """执行事务（多个SQL操作）"""
        if sleep > 0 and batch_size != 1:
            raise Exception('设置sleep参数的时候,batch_size只能是1')
        if sqls_from_file is not None:
            # 读取文件中的SQL
            sqls = mysql.read_sql_from_file(sqls_from_file)
        else:
            if not isinstance(sqls, list):
                sqls = [sqls]
        conn = None
        current_sql = ''
        try:
            with self._get_connection(printInfo=printInfo) as conn:
                with conn.cursor() as cursor:
                    res_rowcount = []
                    sql_nums = len(sqls)
                    for i, sql in enumerate(sqls):
                        current_sql = sql
                        if printInfo:
                            start = time.time()
                            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始', f"{i + 1}/{sql_nums}",
                                  sql if printSql else '')
                        cursor.execute(sql, None)
                        res_rowcount.append(cursor.rowcount)
                        if printInfo:
                            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束', f"{i + 1}/{sql_nums}",
                                  '耗时: %s秒' % round((time.time() - start), 2), '影响: %s条' % cursor.rowcount,
                                  sql if printSql else '')
                        # 每 batch_size 条提交一次，最后一组不足也提交
                        if batch_size is not None:
                            if (i + 1) % batch_size == 0:
                                conn.commit()
                                if printInfo:
                                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '提交',
                                          f"第{int((i + 1) / batch_size)}组SQL", f"每组{batch_size}条")
                                if sleep > 0:
                                    time.sleep(sleep)
                    conn.commit()
                    return res_rowcount
        except pymysql.Error as e:
            try:
                # 关键：检查连接是否有效（conn.open判断连接状态）否则执行conn.rollback()也可能会报错导致程序二次崩溃
                if conn and conn.open:
                    conn.rollback()
            except Exception as rollback_err:
                pass
            raise Exception(str(e) + '\nRUN SQL: ' + current_sql + '\n如未设置 batch_size 参数,全部SQL已回滚') from None

    @staticmethod
    def read_sql_from_file(file_path: str, encoding='utf-8') -> list:
        """
        用sqlparse读取SQL文件
        :param file_path: SQL文件路径
        :param encoding: 文件编码（如 utf-8、gbk）
        :return: [str, str, ...] 分割后的合法SQL语句列表
        """
        sqls = []
        try:
            # 1. 读取文件内容
            with open(file_path, 'r', encoding=encoding) as f:
                sql_content = f.read()
            for row in sqlparse.parse(sql_content):
                sql = str(row)
                sql = sqlparse.format(sql, strip_comments=True)
                sql = sql.strip()
                if not sql:
                    continue
                sqls.append(sql)
            return sqls
        except FileNotFoundError:
            raise FileNotFoundError(f"SQL文件不存在：{file_path}")
        except UnicodeDecodeError:
            raise ValueError(f"文件编码错误：当前指定 {encoding}，请尝试 encoding='gbk'")
        except Exception as e:
            raise Exception(f"读取SQL文件失败：{str(e)}")


if __name__ == '__main__':
    db_config = {
        'host': '',
        'port': 3306,
        'user': 'root',
        'password': '',
        'db': 'test'
    }
    dbIns = mysql(db_config)
    # res1 = dbIns.select('set @lv := 9;select iLevel from payflow where iLevel = @lv;'.split(';'),printInfo=True)
    res1, res2 = dbIns.select(
        'select iLevel from payflow where iLevel=1;select iLevel from payflow where iLevel=9;'.split(';'),
        printInfo=True)
    print(res1)
    print(res2)
    print('-------')
    # res = dbIns.execute_sql('update payflow set iLevel=9 where iEventTime=1717776886',printInfo=True)
    # res = dbIns.update(table='payflow',setDict={'iLevel':None,'iVipLevel':88,'vName':'xxx','vLang':'1"2\'1"2',},whereStr="iEventTime=1720602342")
    # res = dbIns.delete('payflow','iEventTime=1720601151',10,printInfo=True)
    # res = dbIns.insert('payflow',[{'iRoleID':1234,'vName':'1"2中文'},{'iRoleID':1236,'vName':None}],printInfo=True)
    # res = dbIns.execute_manySQLs([
    #     "SET @time := 1720602342;",
    #     "update payflow set vName='a1' WHERE iEventTime = @time;",
    #     "update payflow set vName='a2' WHERE iEventTime = @time;",
    #     "update payflow set vName='asd' WHERE iEventTime = 1720597390;",
    #     "update payflow set vName='a3' WHERE iEventTime = @time;",
    #     "update payflow set vName='aaas1' WHERE vUID='990791'",
    #     "DELETE FROM payflow WHERE vUID='990791' LIMIT 1",
    #     "update payflow set vName='a4' WHERE iEventTime = @time;",
    # ],printInfo=True)
    # print(res)

    db_config = {
        'host': '',
        'port': 3306,
        'user': 'root',
        'password': '',
        'db': 'test'
    }
    # dbIns = mysql(db_config)
    # sqls = [
    #     "SET @name := 'aaq'",
    #     "INSERT INTO role(`roleid`,`name`,`type`,`readonly`) VALUES(120800,1000000,1,1)",
    #     "INSERT INTO role(`roleid`,`name`,`type`,`readonly`) VALUES(100270,1000010,1,1)",
    # ]
    # res = dbIns.execute_manySQLs(sqls_from_file=r"D:\downloads\upload\test.sql",printInfo=True,printSql=True)
    # res = dbIns.execute_manySQLs(sqls_from_file=r"D:\downloads\test1.sql",printInfo=True,printSql=True)
    # exit()
    # res = dbIns.insert(table='role',data={'role_id':123,'name':'xxx','type':1,'readonly':1},returnSQL=True,ignoreMode=True)
    # print(res)

    # r"D:\downloads\upload\test.sql"
    # res = mysql.read_sql_from_file(r"D:\downloads\upload\test.sql")
    # res = mysql.read_sql_from_file(r"D:\downloads\upload\test.sql")
    # res = mysql.read_sql_from_file(r"D:\downloads\test1.sql")
    # for i in res:
    #     print(i)
    #     print('----------------')
