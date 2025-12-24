# coding: utf-8
import os
import re
import time
from datetime import datetime
import bytedtqs
import requests

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
bytedtqs.client.logger.removeHandler(hdlr=bytedtqs.client.log_handler)


class DuplicateRateLimitFilter(logging.Filter):
    def __init__(self, min_interval=5):
        super().__init__()
        self.min_interval = min_interval  # 最小间隔时间（秒）
        self.last_log_time = {}  # 记录{日志内容: 最后打印时间}

    def filter(self, record):
        log_msg = record.getMessage()  # 获取日志内容
        current_time = time.time()
        # 若该日志从未打印过，或已超过间隔时间，则允许输出
        if log_msg not in self.last_log_time or current_time - self.last_log_time[log_msg] > self.min_interval:
            self.last_log_time[log_msg] = current_time
            return True
        return False


logger.addFilter(DuplicateRateLimitFilter(min_interval=20))


class TQSAuth():
    def __init__(self, app_id=None, app_key=None, user_name=None, cluster_name=None, server_name='VA_OG'):
        if not app_id:
            self.app_id = os.getenv('TQS_APP_ID')
            if not self.app_id:
                raise ValueError("app_id 环境变量获取失败")
        else:
            self.app_id = app_id
        if not app_key:
            self.app_key = os.getenv('TQS_APP_KEY')
            if not self.app_key:
                raise ValueError("app_key 环境变量获取失败")
        else:
            self.app_key = app_key
        if not user_name:
            self.user_name = os.getenv('TQS_USER_NAME')
            if not self.user_name:
                raise ValueError("app_key 环境变量获取失败")
        else:
            self.user_name = user_name

        if server_name == 'VA_OG':
            try:
                self.cluster = bytedtqs.Cluster.VA_OG
            except Exception as e:
                self.cluster = bytedtqs.Cluster.VA
                print(f'{e} 重新指定cluster到VA')
        else:
            self.cluster = bytedtqs.Cluster.VA

        if cluster_name == 'macaw':
            self.cluster_name = 'macaw'
            self.queue_name = 'root.macaw_adhoc'
        elif cluster_name == 'virtual':
            self.cluster_name = 'virtual'
            self.queue_name = 'root.virtual_oec_dw_all_va'
        elif cluster_name == 'monkey':
            self.cluster_name = 'monkey'
            self.queue_name = 'root.monkey_ecom_ds_public'
        else:
            self.cluster_name = 'monkey'
            self.queue_name = 'root.monkey_ecom_ds_public'

        self.client = None

    def authenticate(self):
        """显式认证方法"""
        if not self.app_id or not self.app_key:
            raise ValueError("app_id和app_key不能为空")

        self.client = bytedtqs.TQSClient(
            self.app_id,
            self.app_key,
            cluster=self.cluster,
            enable_domain=True
        )
        return self


class MetaOper(TQSAuth):
    def __init__(self, ):
        # 调用父类初始化，参数可为None，使用父类默认值
        super().__init__()
        if not self.client:
            self.authenticate()

        self.data = None
        self.result_url = None
        self.partition_str = None

    def query_max_partition(self, schema_table_name):
        sql = f"show partitions {schema_table_name};"
        logger.debug(f'TQS query_max_partition SQL:{sql}')
        # self.client = bytedtqs.TQSClient(self.app_id, self.app_key, cluster=self.cluster, enable_domain=True)
        job = self.client.execute_query(
            user_name=self.user_name,
            query=sql,
            conf={'yarn.cluster.name': self.cluster_name, 'mapreduce.job.queuename': self.queue_name}
        )
        if job.is_success():
            # 任务运行成功
            result = job.get_result()
            self.result_url = result.result_url
            self.data = result.fetch_all_data()

            partition_lst_lst = self.data
            partition_lst = []
            for par_str in partition_lst_lst[1:]:
                # par_str != 'parititon' 这一段不确定par_str 是否为文本，可能要修改
                if par_str != 'parititon' and not ('test' in par_str[0]):
                    partition_lst.append(par_str[0])
            partition_lst.sort(reverse=True)
            partition_str = partition_lst[0]
            self.partition_str = partition_str
            try:
                max_partition_str = re.match(pattern='(.*)(\\d{8})(.*)', string=partition_str).group(2)
                logger.debug(f'{schema_table_name} max_partition {max_partition_str}')
                return max_partition_str
            except ValueError as error_1:
                try:
                    max_partition_str = re.match(pattern='(.*)([0-9-]{10})(.*)', string=partition_str).group(2)
                    logger.debug(f'max_partition_str {max_partition_str}')
                    return max_partition_str
                except ValueError as error_2:
                    logger.critical(f'{schema_table_name} 获取表分区失败：{error_1} {error_2}')
                    raise ValueError(f'{schema_table_name} 获取表分区失败：{error_1} {error_2}')
        else:
            # 任务运行异常，输出相关日志
            logger.debug(job.analysis_error_message)
            logger.debug(job.query_error_url)
            logger.debug(job.query_log_url)
            logger.debug(job.tracking_urls)
            return None

    def query_max_transient_time(self, schema_table_name, timeout=120):
        sql = f"show create table {schema_table_name};"
        logger.debug(f'TQS query_max_transient_time SQL:{sql}')
        # self.client = bytedtqs.TQSClient(self.app_id, self.app_key, cluster=self.cluster, enable_domain=True, timeout=timeout)
        job = self.client.execute_query(
            user_name=self.user_name,
            query=sql,
            conf={'yarn.cluster.name': self.cluster_name, 'mapreduce.job.queuename': self.queue_name}
        )
        if job.is_success():
            # 任务运行成功
            print('job.is_success()')
            result = job.get_result()
            self.result_url = result.result_url
            print('self.result_url = result.result_url')
            self.data = result.fetch_all_data()
            print('self.data = result.fetch_all_data()')
            create_table_str = self.data[1][0]
            try:
                update_timestamp_str = re.search(r"'transient_lastDdlTime' = '(\d{10})'", create_table_str).group(1)
                update_timestamp = int(update_timestamp_str)
                update_dt_str = datetime.fromtimestamp(update_timestamp).strftime('%Y-%m-%d')
                logger.debug(f'{schema_table_name} update_dt:{update_dt_str}')
                return update_dt_str
            except ValueError:
                logger.critical(f'{schema_table_name} 获取表更新时间失败')
                return None

        else:
            # 任务运行异常，输出相关日志
            logger.debug(job.analysis_error_message)
            logger.debug(job.query_error_url)
            logger.debug(job.query_log_url)
            logger.debug(job.tracking_urls)
            return None


class TQSQuery(TQSAuth):
    def __init__(self):
        # 调用父类初始化，参数可为None，使用父类默认值
        super().__init__()
        if not self.client:
            self.authenticate()

        self.sql = None
        self.result = None
        self.data = None
        self.result_url = None
        self.query_status = 0

    def execute_query(self, sql=None, sql_path=None, param: dict = None, print_sql=False, to_fetch=True, timeout=1200):
        self.query_status = 0
        if sql:
            pass
        elif not sql_path:
            logger.critical(f'请输入SQL文本或SQL文件路径')
            raise ValueError('请输入SQL文本或SQL文件路径')
        else:
            sql_f = open(sql_path, encoding='utf-8')
            sql = sql_f.read()
            sql_f.close()

        if param:
            param_keys = param.keys()
            for key in param_keys:
                value = param.get(key)
                sql = re.sub(r"\${" + key + "}", repl=value, string=sql)
                logger.debug(f'TQS SQL:{sql}')

        self.sql = sql
        if print_sql:
            print(self.sql)
        # self.client = bytedtqs.TQSClient(self.app_id, self.app_key, cluster=self.cluster, enable_domain=True, timeout=timeout)
        job = self.client.execute_query(
            user_name=self.user_name,
            query=self.sql,
            conf={'yarn.cluster.name': self.cluster_name, 'mapreduce.job.queuename': self.queue_name}
        )
        if job.is_success():
            # 任务运行成功
            result = job.get_result()
            self.result_url = result.result_url
            self.data = result.fetch_all_data() if to_fetch else None
            self.query_status = 1
            logger.info(f'TQS result csv url:{result.result_url}')  # 查询结果的 csv 下载链接

        else:
            # 任务运行异常，输出相关日志
            self.query_status = -1
            logger.debug(job.analysis_error_message)
            logger.debug(job.query_error_url)
            logger.debug(job.query_log_url)
            logger.debug(job.tracking_urls)
        return self

    def save_csv(self, save_path):
        # 发送 GET 请求（stream=True 表示流式下载，适合大文件）
        response = requests.get(self.result_url, stream=True)
        # 检查请求是否成功（状态码 200）
        if response.status_code == 200:
            # 打开文件并写入内容
            with open(save_path, 'wb') as f:
                # 分块写入（每次 1024 字节），避免占用过多内存
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # 过滤空块
                        f.write(chunk)
            print(f"文件下载成功，保存至：{save_path}")
        else:
            print(f"下载失败，状态码：{response.status_code}")
