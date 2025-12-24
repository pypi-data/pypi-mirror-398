import os
import subprocess
from quannengbao.file_oper import FileOper as fo
import pandas as pd
from quannengbao.pickle_process import PickleProcess as pik


class HdfsOper:
    def __init__(self, dir_path, pik_save_path):
        self.data_df = None
        self.dir_path = dir_path
        self.pik_save_path = pik_save_path
        self.hdfs_path = 'hdfs://harunava/default/user/tiger/warehouse/'

    def _join_dir(self, dir_path: str, sub_dir: str):
        if sub_dir != '':
            final_dir = os.path.join(dir_path, sub_dir)
        else:
            final_dir = dir_path
        return final_dir

    def save_hdfs_to_local(self, database_name: str, table_name: str, date: str = None, strict_mode=True, make_dir=True, sub_dir='', **kwargs):
        if strict_mode and not date:
            raise ValueError("date 不能为空")
        if not self.dir_path:
            raise ValueError("dir_path 不能为空")

        if make_dir:
            final_dir = self._join_dir(self.dir_path, sub_dir)
            fo(final_dir).mkdir()
        else:
            final_dir = self.dir_path
        date_str = f"date={date}/" if date else ''

        def _const_kwargs():
            if kwargs:
                return '/'.join([f"{k}={v}" for k, v in kwargs.items()]) + '/'
            else:
                return ''

        # 定义 HDFS 命令
        hdfs_path = self.hdfs_path + f"{database_name}.db/{table_name}/" + date_str + _const_kwargs() + "*"
        print(f'从HDFS下载文件: {hdfs_path}')
        hdfs_cmd = [
            "hdfs",
            "dfs",
            "-get",
            hdfs_path,  # hdfs文件路径
            f"{final_dir}"  # 本地保存路径
        ]
        # 执行命令
        try:
            result = subprocess.run(hdfs_cmd, check=True, capture_output=True, text=True)
            print(f"{sub_dir}执行成功!")
        except subprocess.CalledProcessError as e:
            print(f"{sub_dir}执行失败:", e)
        return self

    def pars_local_parquet_to_df(self, sub_dir=''):
        if not self.dir_path:
            raise ValueError("dir_path 不能为空")
        df_lst = []
        final_dir = self._join_dir(self.dir_path, sub_dir)
        try:
            dir_contents = os.listdir(final_dir)
        except FileNotFoundError:
            print(f"错误：目录 {final_dir} 不存在")
        except PermissionError as e:
            print(f"错误：目录 {final_dir} 权限不足: {e}")

        print(f"目录 {final_dir} 下的内容,解析文件:")
        for file in dir_contents:
            file_path = os.path.join(final_dir, file)
            if os.path.isfile(file_path) and (file_path.endswith(".c000")):
                df = pd.read_parquet(file_path, engine="pyarrow")  # engine 可选 pyarrow 或 fastparquet
                df_lst.append(df)
                print(f"解析文件：{file_path}")
        data_df = pd.concat(df_lst, ignore_index=True)
        self.data_df = data_df
        return self

    def to_pik(self, name, suffix=None):
        if not self.dir_path:
            raise ValueError("dir_path 不能为空")
        if not self.pik_save_path:
            raise ValueError("dir_path 不能为空")
        file_name = f'{name}_{suffix}' if suffix else name
        pik.save(data=self.data_df, name=file_name, path=self.pik_save_path)
        print(f"{self.pik_save_path}保存pik文件：{file_name}")

    def batch_save_hdfs_to_pik(self, name, pik_save_path,
                               batch_info: list[tuple[str, dict]], database_name: str, table_name: str, date: str = None, strict_mode=True, make_dir=True, **common_kwargs):
        if strict_mode and not date:
            raise ValueError("date 不能为空")
        for sub_dir, item_kwargs in batch_info:
            # 合并 公共kwargs + 当前批次专属kwargs（专属kwargs 会覆盖公共kwargs 的同名键）
            final_kwargs = {**common_kwargs, **item_kwargs}
            self.save_hdfs_to_local(database_name=database_name, table_name=table_name, date=date,
                                    strict_mode=strict_mode, make_dir=make_dir, sub_dir=sub_dir, **final_kwargs)
            self.pars_local_parquet_to_df(sub_dir=sub_dir)
            self.to_pik(name=name, suffix=sub_dir)
        return self

    def batch_merge_pik(self, name, batch_info: list[tuple[str, dict]], pik_save_path: str = None):
        if not pik_save_path:
            pik_save_path = self.dir_path
        for item, _ in batch_info:
            file_name = f'{name}_{item}'
            df = pik.read(name=file_name, path=pik_save_path)
            self.data_df = pd.concat([self.data_df, df], ignore_index=True)
        pik.save(name=name, data=self.data_df, path=pik_save_path)
        print(f"{pik_save_path}合并pik文件：{file_name}")
        return self

    def batch_remove_local_parquet(self, batch_info: list[tuple[str, dict]]):
        for item, _ in batch_info:
            final_dir = self._join_dir(self.dir_path, item)
            fo(final_dir).del_dir()
            print(f"{final_dir}删除成功!")
        return self

    def clear(self):
        self.data_df = None
        return self
