import sqlite3

import pandas as pd
import pypika
from pypika import functions as fn
from quannengbao.data_oper import DataOperator
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


class SQLiteOper:
    def __init__(self, db_name, foreign_keys=True, busy_timeout=60000, synchronous='OFF'):

        self.create_tbl_status = 0
        self.exec_status = 0
        self.result = None
        self.pika = None
        self.foreign_keys_str = 'ON' if foreign_keys else 'OFF'
        self.busy_timeout = busy_timeout
        self.synchronous = synchronous
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.conn.cursor()
        self.cur.execute(f'PRAGMA foreign_keys = {self.foreign_keys_str};')
        self.cur.execute(f'PRAGMA foreign_keys = {self.foreign_keys_str};')  # 启用外键约束
        self.cur.execute(f'PRAGMA busy_timeout = {self.busy_timeout};')
        self.cur.execute(f'PRAGMA synchronous={self.synchronous};')
        self.tuple = None
        self.tuple_str = None
        self.columns = None
        self.rows = None
        self.sql_str = None

    def __del__(self):
        self.conn.close()

    def reonnect(self):
        self.conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cur = self.conn.cursor()
        self.cur.execute(f'PRAGMA foreign_keys = {self.foreign_keys_str};')
        self.cur.execute(f'PRAGMA foreign_keys = {self.foreign_keys_str};')  # 启用外键约束
        self.cur.execute(f'PRAGMA busy_timeout = {self.busy_timeout};')
        self.cur.execute(f'PRAGMA synchronous={self.synchronous};')
        return self

    def close(self):
        self.cur.close()
        self.conn.close()

    def fetch(self, ignore_error=True):
        try:
            columns = [col[0] for col in self.cur.description]
            rows = self.cur.fetchall()
            self.columns = columns
            self.rows = rows
        except Exception:
            if ignore_error:
                logger.warning('No data to fetch')
            else:
                logger.critical('No data to fetch')
                raise IndexError('No data to fetch')
        return self

    def execute_sql(self, sql_str=None, sql_path=None, to_fetch=True, ignore_error=True, to_print=False, **kwargs):
        if sql_path:
            self.sql_str = self.read_sql_file(sql_path=sql_path)
        else:
            self.sql_str = sql_str
        sql_str_to_print = self.sql_str
        if kwargs:
            for k, v in kwargs.items():
                sql_str_to_print = sql_str_to_print.replace(':' + k, str(v))
            logger.debug(sql_str_to_print)
            if to_print:
                print(sql_str_to_print)
        else:
            if to_print:
                print(sql_str_to_print)
        self.reonnect()
        self.cur = self.cur.execute(self.sql_str, kwargs)
        self.conn.commit()
        if to_fetch:
            self.fetch(ignore_error=ignore_error)
        self.close()
        return self

    def insert(self, table_name, column_name=None, row_data=None):

        if row_data is None:
            row_data = []
        if column_name is None:
            column_name = []

        column_name = str(tuple(column_name)).replace("'", "")
        column_name = column_name.replace("(", "").replace(")", "")
        column_name = '(' + column_name.strip(',') + ')'

        row_data = tuple(row_data)
        placeholder = ('?,' * len(row_data)).strip(',')

        sql = f"insert or replace into {table_name} {column_name} values ({placeholder})"
        # 插入一条数据
        self.cur.execute(sql, row_data)
        # 提交更改
        self.conn.commit()
        return self

    def insert_lst_dct(self, table_name, lst_dct: "list[dict]", check_column_alignment=True, ignore_error=True):
        self.exec_status = 0
        self.create_tbl_status = 0
        self.reonnect()
        # 补全字段,以防某行某字段为空,该行无此字段键值对
        if check_column_alignment:
            # 获取全部字段名称
            col_lst = []
            for dct in lst_dct:
                for item in dct.keys():
                    col_lst.append(item)
            col_lst = list(set(col_lst))
            lst_dct_new = []

            # 填补空白字段key:None
            for dct in lst_dct:
                for col in col_lst:
                    if col not in list(dct.keys()):
                        dct[col] = None
                lst_dct_new.append(dct)
        # 创建表
        try:
            col_lst = list(lst_dct[0].keys())
            col_lst_str = ','.join(col_lst)
            self.cur.execute(
                f'''
                            CREATE TABLE if not exists {table_name} (
                                {col_lst_str} 
                            );
                            '''
            )
            self.create_tbl_status = 1
            logger.debug(f'表创建成功: {table_name}')
        except Exception as e:
            if ignore_error:
                logger.warning(f'表创建失败: {e}')
            else:
                logger.critical(f'表创建失败: {e}')
                raise EOFError('报错')
        # 插入数据
        if self.create_tbl_status == 1:
            insert_data: list[tuple] = []
            lst_dct[0].values()
            # 创建一个插入语句，其中的列名和占位符是基于字典的键生成的
            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(lst_dct[0].keys())}) VALUES ({', '.join(['?' for _ in lst_dct[0]])})"
            logger.debug(f'lst_dct 插入表 {table_name} : {sql}')
            for dct in lst_dct:
                insert_data.append(tuple(dct.values()))

            # self.conn.isolation_level = None
            self.cur.executemany(sql, insert_data)
            self.conn.commit()
            logger.debug(f'数据插入成功,表 {table_name}')
            self.close()
            self.exec_status = 1
        return self

    def update(self, table_name, column_name, row_data, condition_column, condition: "[list, str]", how='equal'):

        # 构建 SET 子句，指定要更新的列和新值
        set_clause = f'{column_name} = ?'

        # 构建 WHERE 子句，指定更新的条件
        if how == 'equal':
            condition = condition[0] if isinstance(condition, list) else condition
            condition = '"' + condition + '"' if isinstance(condition, str) else condition
            where_clause = f' WHERE {condition_column} = {condition}'
        elif how == 'in':
            condition = str(tuple(condition)).strip(',')
            where_clause = f' WHERE {condition_column} in {condition}'
        else:
            logger.critical('how 参数只能是 equal 或 in')
            raise ValueError('how 参数只能是 equal 或 in')

        # 构建 SQL UPDATE 语句
        sql = f"UPDATE {table_name} SET {set_clause} {where_clause};"
        logger.debug(f"update SQL: {sql}")
        # 执行更新操作
        self.cur.execute(sql, (row_data,))
        # 提交更改
        self.conn.commit()
        return self

    def list_to_tuple(self, lst, return_type='str'):
        tpl = tuple(lst)
        tpl_wo_quote = str(tpl).replace("'", "")
        tpl_str_inside = tpl_wo_quote.replace("(", "").replace(")", "")
        tpl_str = '(' + tpl_str_inside.strip(',') + ')'
        self.tuple_str = tpl_str
        self.tuple = tpl
        if return_type == 'str':
            return_obj = tpl_str
        elif return_type == 'tuple':
            return_obj = tpl
        else:
            return_obj = self
        return return_obj

    def to_lst_dct(self, columns: "list" = None, rows: "list" = None):
        columns = self.columns if not columns else columns
        rows = self.rows if not rows else rows
        self.result: list[dict] = DataOperator().cr_to_lst_dct(columns=columns, rows=rows)
        return self

    def to_dataframe(self, columns=None, rows=None):
        columns = self.columns if not columns else columns
        rows = self.rows if not rows else rows
        self.result: pd.DataFrame = DataOperator().cr_to_dataframe(columns, rows)
        return self

    def opt(self):
        return self.result

    def read_sql_file(self, sql_path):
        sql_f = open(sql_path, encoding='utf-8')
        sql = sql_f.read()
        sql_f.close()
        return sql


class Pika(SQLiteOper):
    def __init__(self, db_name=None, foreign_keys=True, busy_timeout=10000):
        super(Pika, self).__init__(db_name=db_name, foreign_keys=foreign_keys, busy_timeout=busy_timeout)
        self.sql = None
        self.pika = pypika
        self.query = self.pika.Query
        self.field = self.pika.Field
        self.table = self.pika.Table
        self.database = self.pika.Database
        self.order = self.pika.Order
        self.functions = fn
        self.tuple = self.pika.Tuple

    def query(self):
        return self.query

    def field(self):
        return self.field

    def table(self):
        return self.table

    def database(self):
        return self.database

    # def functions(self):
    #     return self.functions

    def use_db(self, db_name):
        self.db_name = db_name
        self.__init__(db_name)
        return self

    def insert_ws_constrain(self, table_name: "str", dataframe=None, lst_dct=None, constrain_col: "list" = None):

        if lst_dct is None and dataframe is None:
            logger.critical('dataframe 和 lst_dct 不能同时为空')
            raise ValueError('dataframe 和 lst_dct 不能同时为空')
        if lst_dct and dataframe:
            logger.critical('dataframe 和 lst_dct 不能同时使用')
            raise ValueError('dataframe 和 lst_dct 不能同时使用')
        if constrain_col:
            constrain_col_lst = [self.field(col) for col in constrain_col]
            builder = self.query.from_(table_name)
            for col in constrain_col_lst:
                builder = builder.select(col).groupby(col)
            constrain_data = self.execute_sql(builder.get_sql()).to_lst_dct().opt()
            if not constrain_data:
                if dataframe is not None and not dataframe.empty:
                    data = dataframe.to_dict(orient='records')
                elif lst_dct:
                    data = lst_dct
                else:
                    logger.critical("No data to insert")
                    raise Exception("No data to insert")
                self.insert_lst_dct(table_name, lst_dct=data)
            else:
                k_lst = list(constrain_data[0].keys())
                v_lst = []
                for item in constrain_data:
                    v_tpl = tuple(item.values())
                    v_lst.append(v_tpl)
                if dataframe is not None and not dataframe.empty:
                    dataframe = dataframe.set_index(k_lst)
                    dataframe = dataframe[
                        dataframe.apply(lambda row: (row.name,) if isinstance(row.name, str) else row.index,
                                        axis=1).isin(v_lst) == False].reset_index()
                    data = dataframe.to_dict(orient='records')
                elif lst_dct:
                    data = []
                    for item in lst_dct:
                        check_lst = []
                        for col in k_lst:
                            check_lst.append(item[col])
                        if check_lst not in v_lst:
                            data.append(item)
                else:
                    logger.critical("No data to insert")
                    raise Exception("No data to insert")
                self.insert_lst_dct(table_name, lst_dct=data)

    def table_exists(self, table_name):
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
        result = self.execute_sql(query, to_fetch=True).to_lst_dct().opt()
        return result != []

    def delete_table(self, table_name, where_column=None, where_value=None):
        table_name = table_name
        query_sql = f'''delete from {table_name}'''
        if where_column:
            where_clause = f'''where {where_column} = :where_value '''
            where_param = {"where_value": where_value}
            sql = query_sql + ' ' + where_clause
        else:
            sql = query_sql
            where_param = {}
        logger.debug(sql)
        self.reonnect()
        self.conn.execute(sql, where_param)
        self.conn.commit()
        self.close()
        return self

    def delete_table2(self, table_name, **kwarg_where):
        table_name = table_name
        query_sql = f'''delete from {table_name}'''

        if kwarg_where:
            where_content_lst = []
            for k, v in kwarg_where.items():
                v = "'" + v + "'" if isinstance(v, str) else k
                where_content = k + ' = ' + v
                where_content_lst.append(where_content)
            where_content = ' and '.join(where_content_lst)
            where_clause = ''' where ''' + where_content
            sql = query_sql + where_clause

        else:
            sql = query_sql
            where_param = {}
        logger.debug(sql)
        self.reonnect()
        self.conn.execute(sql)
        self.conn.commit()
        self.close()
        return self

    def drop_table(self, table_name):
        table_name = table_name
        sql = f'''drop table if exists {table_name} '''
        logger.debug(sql)
        self.reonnect()
        self.conn.execute(sql)
        self.conn.commit()
        self.close()
