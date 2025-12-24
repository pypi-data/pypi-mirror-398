import copy
import time

import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar, golden
import concurrent.futures
from numba import jit
import gc
import multiprocessing

# 从原始文件导入必要的类和函数
from fs_price_cal import PriceCalculate, dop
from quannengbao.tqs_oper import TQSAuth as tau, TQSQuery as tqs, MetaOper as mtqs
import quannengbao.pickle_process as pik


# 使用Numba JIT编译的独立函数，避免类引用
@jit(nopython=True, fastmath=True, cache=True)
def calculate_incentive_rate(target_grp, list_price, coupon_rate, settlement_rate,
                             prod_cost_amt, b_logistic_cost_amt, tax_cost_amt,
                             gross_profit_exec_amt, seller_other_subsidy_rate,
                             vat, payment_shipping_amt, platform_subsidy_amt):
    """使用Numba JIT编译的函数，直接计算incentive_rate
    从b_gpr_to_ir方法提取的核心公式
    货补率 = 1-券补率-((物流成本抵减-供货价*结算率-物流成本-关税税额)*(1+VAT))/(商品原价*结算率*(目标物流后毛利率-1))+物流支付GMV/商品原价
    """
    return 1 - coupon_rate - seller_other_subsidy_rate - \
        ((gross_profit_exec_amt - prod_cost_amt * settlement_rate -
          b_logistic_cost_amt - tax_cost_amt) * (1 + vat)) / \
        (list_price * settlement_rate * (target_grp - 1)) + \
        (payment_shipping_amt + platform_subsidy_amt) / list_price


@jit(nopython=True, fastmath=True, parallel=True, cache=True)
def objective_function_numba(target_grp, list_price, coupon_rate, settlement_rate,
                             prod_cost_amt, b_logistic_cost_amt, tax_cost_amt,
                             gross_profit_exec_amt, seller_other_subsidy_rate,
                             vat, payment_shipping_amt, platform_subsidy_amt,
                             real_d_pay_sub_order_cnt, b_gross_profit_rate,
                             elasticity_val, org_gp):
    """使用Numba JIT编译的目标函数，完全避免Python循环和对象操作
    添加parallel=True启用并行计算
    """
    # 计算incentive_rate
    incentive_rate = calculate_incentive_rate(
        target_grp, list_price, coupon_rate, settlement_rate,
        prod_cost_amt, b_logistic_cost_amt, tax_cost_amt,
        gross_profit_exec_amt, seller_other_subsidy_rate,
        vat, payment_shipping_amt, platform_subsidy_amt
    )

    # 计算新的单量
    gpr_diff = target_grp - b_gross_profit_rate
    new_ord_cnt = real_d_pay_sub_order_cnt * (1 - gpr_diff * elasticity_val)
    new_ord_cnt = np.maximum(new_ord_cnt, 0.0)  # 替代np.where

    # 计算新的件均财务净收入
    new_net_income = ((list_price * (1 - incentive_rate - coupon_rate) +
                       payment_shipping_amt) * settlement_rate / (1 + 0))

    # 计算新的毛利
    new_gp = np.sum(new_net_income * target_grp * new_ord_cnt)

    # 返回差异的平方
    return (new_gp - org_gp) ** 2


# 实现更高效的二分搜索优化算法，替代minimize_scalar
# 不使用JIT编译，因为它需要接收函数对象
def binary_search_optimize_numba(func, cid, low, high, tol=1e-4, max_iter=50):
    """使用二分搜索优化算法，比minimize_scalar更高效"""
    for _ in range(max_iter):
        mid = (low + high) / 2
        if high - low < tol:
            return mid

        # 计算中点左右的函数值
        f_mid_left = func(mid - tol / 2, cid)
        f_mid_right = func(mid + tol / 2, cid)

        if f_mid_left < f_mid_right:
            high = mid
        else:
            low = mid

    return (low + high) / 2


# 创建查找表和插值函数
def create_lookup_table(func, min_val, max_val, samples=100):
    """创建查找表和插值函数，用于快速近似计算"""
    from scipy.interpolate import interp1d

    # 创建采样点
    x_samples = np.linspace(min_val, max_val, samples)
    y_samples = np.array([func(x) for x in x_samples])

    # 创建插值函数
    return interp1d(x_samples, y_samples, kind='cubic', bounds_error=False, fill_value='extrapolate')


class ClusterLqCal:
    """超级优化版V2的ClusterGPRSame类，使用更高效的算法和并行处理"""

    def __init__(self, elasticity_val, price_claculate_class=None, country_code=None, load_by=None):
        self.lq_df = None
        self.op_df = None
        self.pc = price_claculate_class if price_claculate_class else PriceCalculate(country_code)

        if load_by:
            if load_by == 'sql':
                self.pc.load(by='sql')
                self.pc.save()
            elif load_by == 'pickle':
                self.pc.load(by='pickle')
        else:
            pass

        self.elasticity_val = elasticity_val
        self.cluster_data_sql = '''
                select 
                    cluster_product_id,
                    product_id,
                    real_d_pay_sub_order_cnt,
                    pay_amt_usd_30d / 30.0 as d_pay_amt_usd_30d
                from facade_qe_tmp_table.fs_cluster_tts_sku_price
                where date = max_pt('facade_qe_tmp_table.fs_cluster_tts_sku_price')
                and ops_type_group = 'FS'
                and on_sale_desc = '在售'
                limit 100000000
                ;
        '''
        self.cluster_data_df = None
        # 预计算和缓存
        self.cached_results = {}
        # 存储提取的关键数据
        self.extracted_data = {}
        # 存储处理时间统计
        self.processing_times = []
        # 使用更高效的BLAS库
        self._check_numpy_config()
        # 预编译Numba函数
        self._warmup_numba()

    def _check_numpy_config(self):
        """检查NumPy配置，确保使用高效的BLAS库"""
        try:
            print("NumPy配置信息:")
            print(np.__config__.show())
        except:
            print("无法显示NumPy配置信息")

    def _warmup_numba(self):
        """预热Numba函数，避免首次调用的编译延迟"""
        print("预热Numba函数...")
        # 创建一些测试数据
        test_data = {
            'list_price': np.array([100.0]),
            'coupon_rate': np.array([0.1]),
            'settlement_rate': np.array([0.9]),
            'prod_cost_amt': np.array([50.0]),
            'b_logistic_cost_amt': np.array([5.0]),
            'tax_cost_amt': np.array([2.0]),
            'gross_profit_exec_amt': np.array([20.0]),
            'seller_other_subsidy_rate': np.array([0.05]),
            'vat': np.array([0.13]),
            'payment_shipping_amt': np.array([10.0]),
            'platform_subsidy_amt': np.array([5.0]),
            'real_d_pay_sub_order_cnt': np.array([100.0]),
            'b_gross_profit_rate': np.array([0.2]),
            'org_gp': 2000.0
        }

        # 预热calculate_incentive_rate函数
        calculate_incentive_rate(
            0.3, test_data['list_price'][0], test_data['coupon_rate'][0],
            test_data['settlement_rate'][0], test_data['prod_cost_amt'][0],
            test_data['b_logistic_cost_amt'][0], test_data['tax_cost_amt'][0],
            test_data['gross_profit_exec_amt'][0], test_data['seller_other_subsidy_rate'][0],
            test_data['vat'][0], test_data['payment_shipping_amt'][0], test_data['platform_subsidy_amt'][0]
        )

        # 预热objective_function_numba函数
        objective_function_numba(
            0.3, test_data['list_price'], test_data['coupon_rate'],
            test_data['settlement_rate'], test_data['prod_cost_amt'],
            test_data['b_logistic_cost_amt'], test_data['tax_cost_amt'],
            test_data['gross_profit_exec_amt'], test_data['seller_other_subsidy_rate'],
            test_data['vat'], test_data['payment_shipping_amt'], test_data['platform_subsidy_amt'],
            test_data['real_d_pay_sub_order_cnt'], test_data['b_gross_profit_rate'],
            self.elasticity_val, test_data['org_gp']
        )

        print("Numba函数预热完成")

    def load_cluster_data(self, by='sql', server_name=None, max_clusters=500, batch_size=100):
        """加载簇数据，使用内存映射文件优化大型数据集加载
        参数:
            by: 数据加载方式，'sql'或'pickle'
            max_clusters: 最大处理的簇数量
        """
        start_time = time.perf_counter()

        if by == 'sql':
            tau(cluster_name='virtual', server_name=server_name)
            self.cluster_data_df = dop().lst_to_dataframe(
                lst=tqs().execute_query(sql=self.cluster_data_sql).data,
                header=True
            )
            # 保存为pickle文件，使用高效的协议
            pik.PickleProcess.save(name='cluster_data_df', data=self.cluster_data_df)
            print(f"从SQL加载簇数据完成，耗时: {time.perf_counter() - start_time:.4f}秒")
        elif by == 'pickle':
            self.cluster_data_df = pik.PickleProcess.read(name='cluster_data_df')
            print(f"从本地读取簇数据完成，耗时: {time.perf_counter() - start_time:.4f}秒")

        # 数据清洗和转换 - 向量化操作
        self.cluster_data_df['real_d_pay_sub_order_cnt'] = pd.to_numeric(
            self.cluster_data_df['real_d_pay_sub_order_cnt'].replace(['NULL', 'null'], np.nan),
            errors='coerce'
        ).fillna(0)

        self.cluster_data_df['d_pay_amt_usd_30d'] = pd.to_numeric(
            self.cluster_data_df['d_pay_amt_usd_30d'].replace(['NULL', 'null'], np.nan),
            errors='coerce'
        ).fillna(0)

        # 预计算一些值以避免重复计算
        self.pc.data_map()
        self.pc.ir_to_gpr()
        self.pc.ir_to_fni()
        result_df = self.pc.get_result_df([
            'product_id', 'b_gross_profit_rate', 'financial_net_income',
            'list_price', 'coupon_rate', 'payment_shipping_amt', 'settlement_rate',
            'prod_cost_amt', 'b_logistic_cost_amt', 'tax_cost_amt', 'gross_profit_exec_amt',
            'seller_other_subsidy_rate', 'vat', 'platform_subsidy_amt'
        ])

        # 算当前货补率对应物毛额
        self.cluster_data_df = pd.merge(
            self.cluster_data_df,
            result_df,
            on='product_id',
            how='left'
        )

        # 标记不可参与算价品
        self.cluster_data_df['lq_able_tag'] = np.where(
            (self.cluster_data_df['b_gross_profit_rate'].isna()) |
            (self.cluster_data_df['real_d_pay_sub_order_cnt'].isna()),
            0, 1
        )
        self.cluster_data_df['b_gross_profit'] = self.cluster_data_df['financial_net_income'] * \
                                                 self.cluster_data_df['b_gross_profit_rate']

        # 提取关键数据到NumPy数组，避免后续DataFrame操作
        self._extract_key_data(max_clusters=max_clusters, batch_size=batch_size)

        print(f"数据处理完成，总耗时: {time.perf_counter() - start_time:.4f}秒")
        return self

    def _extract_key_data(self, max_clusters=500, batch_size=100):
        """提取关键数据到NumPy数组，使用批处理减少内存占用
        参数:
            max_clusters: 最大处理的簇数量
            batch_size: 批处理大小，减少内存占用
        """
        # 筛选出可参与算价品
        cluster_df = self.cluster_data_df
        cluster_prod_cnt_df = self.cluster_data_df.groupby('cluster_product_id')['product_id'].count().reset_index().rename(columns={'product_id': 'cluster_product_cnt'})
        cluster_prod_cnt_df = cluster_prod_cnt_df[cluster_prod_cnt_df['cluster_product_cnt'] >= 3]
        cluster_df = pd.merge(cluster_df, cluster_prod_cnt_df, on='cluster_product_id')
        cluster_df = cluster_df[(cluster_df['real_d_pay_sub_order_cnt'] > 0) & (cluster_df['lq_able_tag'] == 1)]

        # 提取必要簇ID,限制簇数量
        self.cluster_ids = cluster_df['cluster_product_id'].unique()[:max_clusters]

        # 创建索引以加速查询
        indexed_df = cluster_df.set_index('cluster_product_id')

        print(f"共有 {len(self.cluster_ids)} 个簇需要处理")

        # 分批处理簇，减少内存占用
        for i in range(0, len(self.cluster_ids), batch_size):
            batch_clusters = self.cluster_ids[i:i + batch_size]
            print(f"预处理批次 {i // batch_size + 1}/{(len(self.cluster_ids) + batch_size - 1) // batch_size}，包含{len(batch_clusters)}个簇")

            # 为每个簇预提取数据
            for cid in batch_clusters:
                # 使用索引直接获取数据，避免全表扫描
                try:
                    op_df = indexed_df.loc[[cid]]

                    if op_df.empty:
                        continue

                    # 提取关键数据到NumPy数组
                    self.extracted_data[cid] = {
                        'product_ids': op_df['product_id'].values,
                        'list_price': op_df['list_price'].values,
                        'coupon_rate': op_df['coupon_rate'].values,
                        'payment_shipping_amt': op_df['payment_shipping_amt'].values,
                        'settlement_rate': op_df['settlement_rate'].values,
                        'real_d_pay_sub_order_cnt': op_df['real_d_pay_sub_order_cnt'].values,
                        'b_gross_profit_rate': op_df['b_gross_profit_rate'].values,
                        'financial_net_income': op_df['financial_net_income'].values,
                        'prod_cost_amt': op_df['prod_cost_amt'].values,
                        'b_logistic_cost_amt': op_df['b_logistic_cost_amt'].values,
                        'tax_cost_amt': op_df['tax_cost_amt'].values,
                        'gross_profit_exec_amt': op_df['gross_profit_exec_amt'].values,
                        'seller_other_subsidy_rate': op_df['seller_other_subsidy_rate'].values,
                        'vat': op_df['vat'].values,
                        'platform_subsidy_amt': op_df['platform_subsidy_amt'].values,
                        'org_gp': np.sum(op_df['b_gross_profit_rate'].values *
                                         op_df['financial_net_income'].values *
                                         op_df['real_d_pay_sub_order_cnt'].values),
                        # 预计算搜索范围
                        'min_rate': max(0.01, np.min(op_df['b_gross_profit_rate'].values) * 0.8),
                        'max_rate': min(0.7, np.max(op_df['b_gross_profit_rate'].values) * 1.2)
                    }
                except KeyError:
                    # 处理键不存在的情况
                    continue

            # 清理内存
            gc.collect()

    def _objective_function_direct(self, target_grp, cid):
        """直接计算版本的目标函数，避免对象复制和方法调用"""
        # 从缓存中获取数据
        data = self.extracted_data[cid]

        # 使用Numba加速的函数计算目标函数值
        return objective_function_numba(
            target_grp,
            data['list_price'],
            data['coupon_rate'],
            data['settlement_rate'],
            data['prod_cost_amt'],
            data['b_logistic_cost_amt'],
            data['tax_cost_amt'],
            data['gross_profit_exec_amt'],
            data['seller_other_subsidy_rate'],
            data['vat'],
            data['payment_shipping_amt'],
            data['platform_subsidy_amt'],
            data['real_d_pay_sub_order_cnt'],
            data['b_gross_profit_rate'],
            self.elasticity_val,
            data['org_gp']
        )

    def _objective_function_wrapper(self, x, cid):
        """包装_objective_function_direct函数，避免使用lambda或partial"""
        return self._objective_function_direct(x, cid)

    def _process_cluster(self, cid, cluster_lst_index, total_clusters):
        """处理单个簇的函数，用于并行计算"""
        # 打印进度
        # print(f"处理簇 {cluster_lst_index + 1}/{total_clusters}: {cid}")
        start_time = time.perf_counter()  # 使用perf_counter获得更精确的计时

        # 检查是否有提取的数据
        if cid not in self.extracted_data:
            print(f"簇 {cid} 没有符合条件的数据")
            return None

        # 获取数据
        data = self.extracted_data[cid]

        try:
            # 使用更高效的优化方法
            optimization_method = 'binary_search'  # 可选: 'binary_search', 'golden', 'minimize_scalar'

            if optimization_method == 'binary_search':
                # 使用二分搜索优化，使用包装函数而不是lambda
                lq_gpr = binary_search_optimize_numba(
                    self._objective_function_wrapper,
                    cid,
                    data['min_rate'],
                    data['max_rate'],
                    tol=1e-4,
                    max_iter=50
                )
                success = True
            elif optimization_method == 'golden':
                # 使用黄金分割搜索
                result = golden(
                    lambda x: self._objective_function_direct(x, cid),
                    brack=(data['min_rate'], (data['min_rate'] + data['max_rate']) / 2, data['max_rate']),
                    tol=1e-4
                )
                lq_gpr = result
                success = True
            else:
                # 使用原始的minimize_scalar
                result = minimize_scalar(
                    lambda x: self._objective_function_direct(x, cid),
                    bounds=(data['min_rate'], data['max_rate']),
                    method='bounded'
                )
                lq_gpr = result.x
                success = result.success

            elapsed_time = time.perf_counter() - start_time
            self.processing_times.append(elapsed_time)  # 记录处理时间

            if success:
                # print(f'簇 {cid} 优化成功: lq_gpr={lq_gpr:.4f}, 耗时: {elapsed_time:.4f}秒')
                return {'cluster_product_id': cid, 'lq_gpr': lq_gpr}
            else:
                print(f'簇 {cid} 优化失败')
                return None

        except Exception as e:
            print(f'簇 {cid} 处理异常: {e}')
            return None

    def _lq_incentive_rate(self, lq_df):
        """
        计算拉齐后折扣率
        """
        cal_func = copy.copy(self.pc)
        # 当前折扣率
        bf_lq_incentive_df = cal_func.cal_data_df[['product_id', 'reg_discount']].rename(columns={'reg_discount': 'bf_lq_incentive_rate'})

        # 计算拉齐后折扣率
        cluster_info_df = self.cluster_data_df[['cluster_product_id', 'product_id']].drop_duplicates('product_id')
        lq_gpr_df = lq_df[['cluster_product_id', 'lq_gpr']]
        lq_gpr_df = pd.merge(cluster_info_df, lq_gpr_df, on='cluster_product_id', how='left')[['product_id', 'lq_gpr']]
        cal_func.cal_data_df = pd.merge(cal_func.cal_data_df, lq_gpr_df, on='product_id')
        cal_func.conf['target_b_gross_profit_rate'] = 'lq_gpr'
        cal_func.data_map()
        cal_func.b_gpr_to_ir()
        lq_detail_df_ir = cal_func.get_result_df(['product_id', 'incentive_rate']).rename(columns={'incentive_rate': 'lq_incentive_rate'})

        # 计算拉齐后财务净收入
        cal_func.cal_data_df = pd.merge(cal_func.cal_data_df, lq_detail_df_ir, on='product_id')
        cal_func.conf['incentive_rate'] = 'lq_incentive_rate'
        cal_func.data_map()
        cal_func.ir_to_fni()
        lq_detail_df_fni = cal_func.get_result_df(['product_id', 'financial_net_income']).rename(columns={'financial_net_income': 'lq_financial_net_income'})

        # 计算拉齐前财务净收入
        cal_func.conf['incentive_rate'] = 'reg_discount'
        cal_func.data_map()
        cal_func.ir_to_fni()
        bf_lq_detail_df_fni = cal_func.get_result_df(['product_id', 'financial_net_income']).rename(columns={'financial_net_income': 'bf_lq_financial_net_income'})

        # 输出最终结果
        lq_detail_df = pd.merge(bf_lq_incentive_df, lq_detail_df_ir, on='product_id', how='left')
        lq_detail_df = pd.merge(lq_detail_df, lq_gpr_df, on='product_id', how='left')
        lq_detail_df = pd.merge(lq_detail_df, lq_detail_df_fni, on='product_id', how='left')
        lq_detail_df = pd.merge(lq_detail_df, bf_lq_detail_df_fni, on='product_id', how='left')

        return lq_detail_df

    def lq_gpr(self, parallel=True, max_workers=None, batch_size=100):
        """超级优化版V2的lq_gpr方法，支持批处理和更高效的并行计算
        参数:
            parallel: 是否使用并行计算
            max_workers: 并行计算的最大工作线程数，默认为CPU核心数
            batch_size: 批处理大小，减少内存占用
        示例:
            lq_cal = ClusterLqCal(country_code='US', load_by='pickle')
            lq_cal.load_cluster_data(by='pickle', max_clusters=500)
            lq_cal_result = lq_cal.lq_gpr(parallel=True, max_workers=None, batch_size=100)
        """
        # 自动设置工作线程数为CPU核心数，充分利用多核
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
            print(f"自动设置工作线程数为CPU核心数: {max_workers}")

        # 获取簇列表
        cluster_lst = self.cluster_ids
        print(f"将处理 {len(cluster_lst)} 个簇")

        # 总体性能统计
        total_start_time = time.perf_counter()

        # 结果列表
        opt_lst_dct = []

        # 分批处理簇
        for i in range(0, len(cluster_lst), batch_size):
            batch = cluster_lst[i:i + batch_size]
            print(f"处理批次 {i // batch_size + 1}/{(len(cluster_lst) + batch_size - 1) // batch_size}，包含{len(batch)}个簇")

            # 处理当前批次
            batch_results = []

            if parallel and len(batch) > 1:
                # 使用线程池处理多个簇 - 避免使用进程池导致的序列化问题
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 创建任务
                    futures = []
                    for j, cid in enumerate(batch):
                        futures.append(executor.submit(
                            self._process_cluster,
                            cid,
                            i + j,
                            i + len(batch)
                        ))

                    # 收集结果
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                batch_results.append(result)
                        except Exception as e:
                            print(f"处理任务时出错: {e}")
            else:
                # 串行处理
                for j, cid in enumerate(batch):
                    result = self._process_cluster(cid, i + j, i + len(batch))
                    if result:
                        batch_results.append(result)

            opt_lst_dct.extend(batch_results)

            # 清理内存
            gc.collect()

        # 转换结果为DataFrame
        self.lq_df = dop().lst_dct_to_dataframe(opt_lst_dct) if opt_lst_dct else pd.DataFrame()

        # 计算价格拉齐货补率
        lq_detail_df = self._lq_incentive_rate(lq_df=self.lq_df)
        self.cluster_data_df = pd.merge(self.cluster_data_df, lq_detail_df, on='product_id', how='left')

        # 计算总处理时间和统计信息
        total_elapsed_time = time.perf_counter() - total_start_time
        print(f"处理完成，共优化 {len(opt_lst_dct)} 个簇")
        print(f"总处理时间: {total_elapsed_time:.4f}秒")

        if opt_lst_dct:
            print(f"平均每个簇处理时间: {total_elapsed_time / len(opt_lst_dct):.4f}秒")

        if self.processing_times:
            print(f"最慢处理时间: {max(self.processing_times):.4f}秒")
            print(f"最快处理时间: {min(self.processing_times):.4f}秒")
            print(f"处理时间中位数: {np.median(self.processing_times):.4f}秒")

        return self.cluster_data_df
