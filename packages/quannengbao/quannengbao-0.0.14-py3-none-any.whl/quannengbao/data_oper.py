import numpy as np
import pandas as pd
from dateutil import parser
from datetime import datetime
import re
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


def has_double_separator(text):
    pattern = r'.*[-/]{2}.*'
    return bool(re.match(pattern, text))


class DataOperator:
    def __init__(self):
        self.data = None
        self.value = None
        self.result = None
        self.lst = None
        self.lst_dct = None
        self.dataframe = None
        self.indexer_dct = None
        self.index_num = None

    def convert_text_to_number(self, value, convert_nan=False, nan_to=0):
        self.value = value
        if convert_nan and not self.value:
            self.value = nan_to
            return self.value

        if isinstance(self.value, str):
            # 匹配整数和小数
            integer_match = re.match(r'^[-+]?\d+$', self.value)
            decimal_match = re.match(r'^[-+]?\d+\.\d+$', self.value)

            if integer_match:
                self.value = int(integer_match.group())
                return self.value
            elif decimal_match:
                self.value = float(decimal_match.group())
                return self.value

            # 匹配百分比
            percentage_match = re.match(r'^([-+]?\d+\.?\d*)%$', self.value)
            if percentage_match:
                self.value = float(percentage_match.group(1)) / 100
                return self.value
            else:
                try:
                    # 尝试将其他文本形式转换为数字
                    self.value = float(self.value)
                    return self.value
                except ValueError:
                    return self.value
        elif isinstance(self.value, datetime):
            self.value = str(self.value)
            return self.value

        else:
            return self.value

    def convert_datetime_to_str(self, value, convert_nan=False, nan_to=''):
        self.value = value
        if convert_nan and not self.value:
            self.value = nan_to
            return self.value

        if isinstance(self.value, datetime):
            self.value = str(self.value)
            return self.value
        else:
            return self.value

    def create_indexer(self, lst_dct, index_name_lst: list):
        self.data = lst_dct
        self.indexer_dct = {}
        for i in range(len(self.data)):
            dct = self.data[i]
            index_dct = {}
            for index_name in index_name_lst:
                index_dct[index_name] = dct.get(index_name)
            self.indexer_dct[index_dct.__str__()] = i
        return self

    def get_index_data(self, data_name, lst_dct=None, indexer_dct=None, **kwargs):
        '''
        输入lst_dct数据，data_name 字段名称，index值，得到查找数据
        :param lst_dct:
        :param data_name: 字段名称
        :param indexer_dct: 索引
        :param kwargs:
        :return:
        '''

        def get_index_num(indexer_dct=None, **kwargs):
            '''
            输入index,**kwargs 得到对应行数值 index_num
            :param indexer_dct:
            :param kwargs:
            :return:
            '''
            indexer_dct = self.indexer_dct if not indexer_dct else indexer_dct
            index_num = indexer_dct.get(kwargs.__str__())
            if not index_num:
                logger.warning(f'lst_dct 查询未搜索到 {kwargs}')
            return index_num

        lst_dct = self.data if not lst_dct or not lst_dct == [] else lst_dct
        self.index_num = get_index_num(indexer_dct=indexer_dct, **kwargs)
        self.value = lst_dct[self.index_num].get(data_name)
        return self.value

    def add_df_column(self, add_dct: dict, dataframe=None):
        dataframe = self.dataframe if not dataframe else dataframe
        for k, v in add_dct.items():
            dataframe[k] = v
        self.dataframe = dataframe
        return self

    def standardize_date_str(self, obj):
        datetime_type = (type(datetime.now().date()),
                         type(datetime.now().time()),
                         pd.Timestamp,
                         )
        if isinstance(obj, datetime_type):
            result = datetime.strftime(obj, '%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, int) and len(str(obj)) == 8:
            try:
                result = parser.parse(str(obj)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                result = obj
        elif isinstance(obj, str) and (has_double_separator(obj) or len(obj) == 8):
            try:
                result = parser.parse(obj).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                result = obj
        else:
            result = obj
        self.result = result
        return self.result

    def muti_data_lst_calc(self, df, row_limit=None, header=False):
        data_lst = self.dataframe_to_lst(df, header=header)
        if not row_limit:
            return [data_lst]
        else:
            left_rows = len(data_lst)
            data_lst_muti = []
            while left_rows != 0:
                add_rows = min(left_rows, row_limit)
                data_lst_muti.append(data_lst[:add_rows])
                data_lst = data_lst[add_rows - 1:]
                left_rows = left_rows - add_rows
            return data_lst_muti

    def dataframe_to_lst(self, dataframe, header=False):
        dataframe: pd.DataFrame = self.dataframe if dataframe.empty else dataframe
        if dataframe is None or dataframe.empty:
            self.lst = [[]]
        else:
            if header:
                lst = dataframe.values.tolist()
                lst.insert(0, dataframe.columns.tolist())
                self.lst = lst
            else:
                self.lst = dataframe.values.tolist()
        return self.lst

    def lst_to_dataframe(self, lst, header=True):
        '''
        将[[columns],[row],[row]]列表转换为DataFrame
        :param lst:
        :param header:
        :return:
        '''
        if header:
            self.dataframe = pd.DataFrame(lst[1:], columns=lst[0])
        else:
            self.dataframe = pd.DataFrame(lst)
        return self.dataframe

    def lst_to_dataframe_batch(self, lst, header=True, batch_size=10000, optimize_dtypes=True):
        '''
        分批处理将列表转换为DataFrame，优化内存使用
        :param lst: 输入列表
        :param header: 是否包含表头
        :param batch_size: 每批处理的行数，默认10000行
        :param optimize_dtypes: 是否优化数据类型，默认True
        :return: DataFrame
        '''
        if not lst:
            self.dataframe = pd.DataFrame()
            return self.dataframe
            
        # 获取列名和数据行
        if header:
            columns = lst[0]
            data_rows = lst[1:]
        else:
            columns = None
            data_rows = lst
            
        total_rows = len(data_rows)
        
        # 如果数据量小于批处理大小，直接处理
        if total_rows <= batch_size:
            if header:
                self.dataframe = pd.DataFrame(data_rows, columns=columns)
            else:
                self.dataframe = pd.DataFrame(data_rows)
            return self.dataframe
        
        # 分批处理
        dataframes = []
        for i in range(0, total_rows, batch_size):
            batch_end = min(i + batch_size, total_rows)
            batch_data = data_rows[i:batch_end]
            
            # 创建当前批次的DataFrame
            if header:
                batch_df = pd.DataFrame(batch_data, columns=columns)
            else:
                batch_df = pd.DataFrame(batch_data)
            
            dataframes.append(batch_df)
            
            # 释放当前批次数据的内存
            del batch_data
            
        # 合并所有批次
        if dataframes:
            self.dataframe = pd.concat(dataframes, ignore_index=True)
            if optimize_dtypes:
                self.dataframe = self._optimize_dataframe_dtypes(self.dataframe)
        else:
            self.dataframe = pd.DataFrame()
            
        # 释放中间变量内存
        del dataframes
        
        return self.dataframe

    def _optimize_dataframe_dtypes(self, df):
        '''
        优化DataFrame的数据类型以减少内存使用
        :param df: 输入的DataFrame
        :return: 优化后的DataFrame
        '''
        # 复制DataFrame以避免修改原始数据
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            # 尝试将数值列转换为float32
            if optimized_df[col].dtype in [np.float64, np.int64]:
                try:
                    optimized_df[col] = optimized_df[col].astype(np.float32)
                except (ValueError, TypeError):
                    pass
            
            # 对于字符串列，如果基数较低，转换为category类型
            elif optimized_df[col].dtype == 'object':
                # 检查前1000行样本的基数
                sample_size = min(1000, len(optimized_df))
                unique_count = optimized_df[col].iloc[:sample_size].nunique()
                
                # 如果基数小于总行数的50%，转换为category
                if unique_count < len(optimized_df) * 0.5:
                    try:
                        optimized_df[col] = optimized_df[col].astype('category')
                    except (ValueError, TypeError):
                        pass
        
        return optimized_df

    def lst_to_lst_dct(self, lst):
        '''
        将[[row],[row]]转换为列表字典
        :param lst:
        :return:
        '''
        columns = lst[0]
        rows = lst[1:]
        result = []
        for row in rows:
            dct = {}
            for i in range(len(columns)):
                dct[columns[i]] = row[i]
            result.append(dct)
        self.result = result
        return self.result

    def lst_dct_to_lst(self, lst_dct):
        '''
        将列表字典转换为[[row],[row]]
        :param lst_dct:
        :return:
        '''
        columns = list(lst_dct[0].keys())
        rows = []
        for dct in lst_dct:
            row = [dct.get(col, None) for col in columns]
            rows.append(row)
        self.result = [columns] + rows
        return self.result

    def lst_dct_to_dataframe(self, lst_dct):
        self.lst = self.lst_dct_to_lst(lst_dct=lst_dct)
        self.dataframe = self.lst_to_dataframe(self.lst)
        return self.dataframe

    def cr_to_lst_dct(self, columns, rows):
        '''
        将[columns] [[row],[row]]转换为列表字典
        :param columns:
        :param rows:
        :return:
        '''
        result = []
        for row in rows:
            row_dct = {}
            for i in range(len(columns)):
                row_dct[columns[i]] = row[i]
            result.append(row_dct)
        self.result = result
        return self.result

    def cr_to_dataframe(self, columns: list = None, rows: list = None):
        '''
        将[columns] [[row],[row]]转换为DataFrame
        :param columns:
        :param rows:
        :return:
        '''
        lst_dct = self.cr_to_lst_dct(columns, rows)
        self.result: pd.DataFrame = pd.DataFrame.from_dict(lst_dct)
        return self.result

    def lst_dct_rename_col(self, lst_dct, rename_dict):
        '''
        重命名列表字典的列名
        :param lst_dct:
        :param rename_dict:
        :return:
        '''
        err_collect_lst = []
        for dct in lst_dct:
            for old_name, new_name in rename_dict.items():
                try:
                    dct[new_name] = dct.pop(old_name)
                except KeyError:
                    err_collect_lst.append(old_name)
        if err_collect_lst:
            logger.critical(f'Error: {err_collect_lst} not in the list')
            raise ValueError(f'Error: {err_collect_lst} not in the list')
        self.result = lst_dct
        return self.result

    def clean_dataframe(self, df=None):
        '''
        处理dataframe格式
        :param df:
        :return:
        '''
        df = self.dataframe if df.empty else df
        replace_info = {np.inf: None, -np.inf: None, pd.NaT: None, np.nan: None, '': None, 'NULL': None,
                        'null': None}
        df = (
            df.replace(replace_info).applymap(lambda x: self.standardize_date_str(x))
        )
        self.dataframe: pd.DataFrame = df
        logger.debug(f'clean_dataframe replace_info：{replace_info}')
        return self.dataframe

    def change_col_type(self, dataframe):
        for col in dataframe.columns:
            non_null_values = dataframe[col].dropna()[:200]
            if all(isinstance(val, int) for val in non_null_values):
                dataframe[col] = dataframe[col].astype(int)
            elif all(isinstance(val, float) for val in non_null_values):
                dataframe[col] = dataframe[col].astype(float)
            elif all(isinstance(val, str) for val in non_null_values):
                dataframe[col] = dataframe[col].astype(str)
        return dataframe

    def lst_dct_select_columns(self, lst_dct, columns):
        lst_dct_new = []
        for dct in lst_dct:
            new_dct = {}
            for k, v in dct.items():
                if k in columns:
                    new_dct[k] = v
            lst_dct_new.append(new_dct)
        return lst_dct_new

    def lst_dct_join(self, left_lst_dct, right_lst_dct, columns: list):
        '''
        合并字典
        :param left_dct:
        :param right_dct:
        :param columns:
        :return:
        '''

        for left_dct in left_lst_dct:
            for right_dct in right_lst_dct:
                if all(left_dct.get(col) == right_dct.get(col) for col in columns):
                    for col in columns:
                        if left_dct.get(col) == right_dct.get(col):
                            right_dct.pop(col)
                    left_dct.update(right_dct)
        return left_lst_dct


class DfOperator(pd.DataFrame):
    def __init__(self):
        super().__init__()

    def cols_to_number(self, col_lst):
        self[col_lst] = self[col_lst].replace('NULL', '').replace('null', '')
        self[col_lst] = self[col_lst].replace('NULL', '').replace('null', '').replace('', 0.0)
