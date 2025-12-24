from quannengbao.data_oper import DataOperator as dop
from quannengbao.tqs_oper import TQSAuth as tau, TQSQuery as tqs, MetaOper as mtqs
import pandas as pd
import re
import numpy as np
import statsmodels.api as sm
import quannengbao.pickle_process as pik
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


class LoadCalData:
    # 导出数据
    # 分国家存储数据，或是适应多国计算

    def __init__(self, country_code, cluster_name='virtual', server_name=None):
        self.tau = tau(cluster_name=cluster_name, server_name=server_name)
        self.mtqs = mtqs()
        self.tqs = tqs()
        self.dop = dop()
        self.pik = pik.PickleProcess
        self.base_data_source = 'facade_qe_tmp_table.fs_pricing_product_sum_df'
        self.base_data_p_date_str = None
        self.base_data_p_hour_str = None
        self.country_code = country_code

        self.base_data_df: pd.DataFrame = None
        self.c1_cap_cate_lst = None
        self.cap_sum_1c_df = None
        self.cal_data_df: pd.DataFrame = None
        self.base_data_sql = '''
            select concat(date, '-', hour)                                                                  as update_info,
                   sale_desc,
                   spu_code,
                   country_code,
                   product_id,
                   first_industry_name,
                   second_industry_name,
                   s_first_category_name,
                   s_second_category_name,
                   s_third_category_name,
                   concat('日常货补规则:', nvl(reg_promotion_name, '无'), '|', '营销货补规则:',
                          nvl(pro_promotion_name, '无'))                                                    as promotion_info,

                   payment_amt_usd * 1.000000 / max_prod_day_cnt * 1.000000                                 as d_payment_amt_usd,
                   pay_sub_order_exl_sample_cnt * 1.000000 / max_prod_day_cnt * 1.000000                    as d_pay_sub_order_exl_sample_cnt,

                   prod_list_price_payment_amt_usd * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as list_price_usd,
                   payment_shipping_amt_usd * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as payment_shipping_amt_usd,
                   reg_discount_times_sale_amt * 1.000000 / prod_list_price_payment_amt_usd *
                   1.000000                                                                                 as reg_discount,
                   pro_discount_times_sale_amt * 1.000000 / prod_list_price_payment_amt_usd *
                   1.000000                                                                                 as pro_discount,

                   ext_tax_expt_payment_amt_usd * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as ext_tax_expt_payment_amt_usd,
                   overall_gross_profit * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                as overall_gross_profit,
                   origin_prod_cost_amt_usd * 1.000000 / pay_sub_order_cnt *
                   1.000000                                                                                 as origin_prod_cost_amt,
                   logistic_cost_amt * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                   as logistic_cost_amt,
                   tax_cost_usd * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                        as tax_cost_usd,

                   a_logistic_cost_amt * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                 as a_logistic_cost_amt,
                   expt_prod_loss_amt_usd * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000              as expt_prod_loss_amt_usd,
                   author_commission_amt * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000               as author_commission_amt,
                   sample_amt * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                          as sample_amt,
                   ug_cost_amt * 1.000000 / pay_sub_order_exl_sample_cnt * 1.000000                         as ug_cost_amt,
                   platform_commission_cost_usd * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as platform_commission_cost_usd,

                   product_publicity_cost * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as product_publicity_cost,
                   seller_incentives_cost * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as seller_incentives_cost,


                   settlement_rate * 1.000000                                                               as settlement_rate,
                   coupon_amt * 1.000000 / prod_list_price_payment_amt_usd * 1.000000                       as coupon_rate,

                   author_commission_amt * 1.000000 / ext_tax_expt_payment_amt_usd * 1.000000               as author_commission_rate,
                   sample_amt * 1.000000 / ext_tax_expt_payment_amt_usd * 1.000000                          as sample_rate,
                   ug_cost_amt * 1.000000 / ext_tax_expt_payment_amt_usd * 1.000000                         as ug_cost_rate,
                   a_logistic_cost_amt * 1.000000 / ext_tax_expt_payment_amt_usd * 1.000000                 as a_logistic_cost_rate,
                   expt_prod_loss_amt_usd * 1.000000 / ext_tax_expt_payment_amt_usd * 1.000000              as expt_prod_loss_rate,
                   platform_commission_cost_usd * 1.000000 / ext_tax_expt_payment_amt_usd *
                   1.000000                                                                                 as platform_commission_cost_rate,
                   product_publicity_cost * 1.000000 / ext_tax_expt_payment_amt_usd *
                   1.000000                                                                                 as product_publicity_cost_rate,
                   seller_incentives_cost * 1.000000 / ext_tax_expt_payment_amt_usd *
                   1.000000                                                                                 as seller_incentives_cost_rate,


                   coalesce(content_payment_amt_usd, 0) * 1.000000 / payment_amt_usd *
                   1.000000                                                                                 as content_payment_amt_rate,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd) * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as b_gross_profit,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd
                       - a_logistic_cost_amt - expt_prod_loss_amt_usd) * 1.000000 / pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as ab_gross_profit,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd
                       - a_logistic_cost_amt - expt_prod_loss_amt_usd
                       - author_commission_amt - sample_amt - ug_cost_amt - platform_commission_cost_usd) * 1.000000 /
                   pay_sub_order_exl_sample_cnt *
                   1.000000                                                                                 as margin1,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd) / ext_tax_expt_payment_amt_usd as b_gross_profit_rate,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd
                       - a_logistic_cost_amt - expt_prod_loss_amt_usd) / ext_tax_expt_payment_amt_usd       as ab_gross_profit_rate,

                   (overall_gross_profit - logistic_cost_amt - tax_cost_usd
                       - a_logistic_cost_amt - expt_prod_loss_amt_usd
                       - author_commission_amt - sample_amt - ug_cost_amt - platform_commission_cost_usd - product_publicity_cost -
                    seller_incentives_cost) /
                   ext_tax_expt_payment_amt_usd                                                             as margin1_rate,
                   tax_rate_times_sale_amt * 1.000000 / prod_list_price_payment_amt_usd * 1.000000          as tax_rate


            from facade_qe_tmp_table.fs_pricing_product_sum_df
            where date = '${date}'
              and hour = '${hour}'
              and country_code = '${country_code}'
              ${pid_in_expression}
              and calable_tag = '1'
              and prod_list_price_payment_amt_usd is not null
              and prod_list_price_payment_amt_usd <> 0
            limit 100000000
            ;
        '''

    def load_from_sql(self, pid_lst, print_sql):
        self.load_base_data_partition()
        self.load_base_data(pid_lst, print_sql)
        print('底表读取完成')
        self.cal_cap_table()
        print('卡控表计算完成')
        self.cal_final_tbl()
        print('算价基础表读取完成')
        self.del_base_df_cache()
        print('算价原始数据缓存清除完成')
        return self

    def load_from_pickle(self, name, path):
        self.cal_data_df = pik.PickleProcess.read(name=name, path=path)
        print('算价基础表从本地读取完成')
        return self

    def load_base_data_partition(self):
        '''
        读取算价基础数据表的最新分区
        :return:
        '''
        logger.info(f"开始读取算价基础数据表的最新分区")
        mtqs = self.mtqs
        mtqs.query_max_partition(schema_table_name=self.base_data_source)
        p_str = mtqs.partition_str
        self.base_data_p_date_str = re.match(pattern='(.*)(\\d{8})(.*)', string=p_str).group(2)
        self.base_data_p_hour_str = re.search(r'hour=(\d+)', string=p_str).group(1)
        logger.info(
            f"算价基础数据表的最新分区读取完成 p_date_str:{self.base_data_p_date_str},p_hour_str:{self.base_data_p_hour_str}")

    def load_base_data(self, pid_lst=None, print_sql=False):
        '''
        读取算价基础数据表
        :return:
        '''
        self.pid_lst = pid_lst
        df_lst = []
        if pid_lst:
            tms = len(pid_lst) // 40000 + 1
            print(f'需要取数{tms}次')
            for i in range(tms):
                in_pid_lst = pid_lst[i * 40000:(i + 1) * 40000]
                print(f"分批读取数据，第{i + 1}批，pid数量：{len(in_pid_lst)}")
                pid_str = "','".join([pid for pid in in_pid_lst])
                pid_in_expression = f"and product_id in ('{pid_str}')"
                self.tqs.execute_query(sql=self.base_data_sql, print_sql=print_sql,
                                       param={'date': self.base_data_p_date_str, 'hour': self.base_data_p_hour_str,
                                              'country_code': self.country_code, 'pid_in_expression': pid_in_expression})
                df = self.dop.lst_to_dataframe_batch(lst=self.tqs.data, header=True)
                df_lst.append(df)
            df = pd.concat(df_lst, axis=0)
        else:
            pid_in_expression = ""
            self.tqs.execute_query(sql=self.base_data_sql, print_sql=print_sql,
                                   param={'date': self.base_data_p_date_str, 'hour': self.base_data_p_hour_str,
                                          'country_code': self.country_code, 'pid_in_expression': pid_in_expression})
            df = self.dop.lst_to_dataframe_batch(lst=self.tqs.data, header=True)
        del self.tqs
        del self.dop

        df['error_tag'] = np.where((df['list_price_usd'] == 0) | (df['list_price_usd'].isnull()), 1, 0)
        df = df[df['country_code'] == self.country_code]

        str_cols = ['update_info', 'sale_desc', 'spu_code', 'country_code', 'product_id',
                    'first_industry_name', 'second_industry_name', 's_first_category_name',
                    's_second_category_name', 's_third_category_name', 'promotion_info']
        num_cols = ['d_payment_amt_usd', 'd_pay_sub_order_exl_sample_cnt', 'list_price_usd', 'payment_shipping_amt_usd',
                    'reg_discount', 'pro_discount',
                    'ext_tax_expt_payment_amt_usd', 'overall_gross_profit',
                    'origin_prod_cost_amt', 'logistic_cost_amt', 'tax_cost_usd',
                    'a_logistic_cost_amt', 'expt_prod_loss_amt_usd',
                    'author_commission_amt', 'sample_amt', 'ug_cost_amt',
                    'platform_commission_cost_usd', 'settlement_rate', 'coupon_rate',
                    'author_commission_rate', 'sample_rate', 'ug_cost_rate',
                    'a_logistic_cost_rate', 'expt_prod_loss_rate',
                    'platform_commission_cost_rate', 'content_payment_amt_rate',
                    'b_gross_profit', 'ab_gross_profit', 'margin1', 'b_gross_profit_rate',
                    'ab_gross_profit_rate', 'margin1_rate', 'product_publicity_cost', 'seller_incentives_cost',
                    'product_publicity_cost_rate', 'seller_incentives_cost_rate', 'tax_rate']

        df[str_cols] = df[str_cols].astype(str)
        df[str_cols] = df[str_cols].replace('NULL', '').replace('null', '')
        df[num_cols] = df[num_cols].replace('NULL', '').replace('null', '').replace('', 0.0)
        df[num_cols] = df[num_cols].astype(float)
        self.base_data_df = df
        del df
        logger.info(f"算价基础数据表，从脚本读取完成")

    def cal_cap_table(self):
        '''
        :return:
        '''

        logger.info(f"计算费用卡控表")
        # 优化：避免深拷贝，使用视图或浅拷贝
        # 筛选动销品，剔除异常品
        cap_sum_df = self.base_data_df[(self.base_data_df['sale_desc'] == 'sale') & (self.base_data_df['error_tag'] == 0)].copy()
        cap_sum_df = cap_sum_df[
            ['spu_code', 'country_code', 'product_id', 'first_industry_name', 'second_industry_name',
             's_first_category_name', 's_third_category_name',
             'author_commission_rate', 'sample_rate', 'ug_cost_rate',
             'a_logistic_cost_rate', 'expt_prod_loss_rate', 'platform_commission_cost_rate',
             'content_payment_amt_rate']]

        # 样品费率、UG费率、货损率、平台佣金率、a段物流成本含货损率，按分位卡控
        # 剔除费率0
        sample_rate_df = cap_sum_df[cap_sum_df['sample_rate'] > 0]
        ug_cost_rate_df = cap_sum_df[cap_sum_df['ug_cost_rate'] > 0]
        expt_prod_loss_rate_df = cap_sum_df[cap_sum_df['expt_prod_loss_rate'] > 0]
        platform_commission_cost_rate_df = cap_sum_df[cap_sum_df['platform_commission_cost_rate'] > 0]
        a_logistic_cost_rate_df = cap_sum_df[cap_sum_df['a_logistic_cost_rate'] > 0]
        # 按一级类目卡控费率
        cat_sample_rate_df = sample_rate_df.groupby('s_first_category_name')[
            'sample_rate'].quantile(0.40)  # 样品费率分布多数分布在0附近，在零之外分布也较为离散，后续应讨论新的解决方案
        cat_ug_cost_rate_df = ug_cost_rate_df.groupby('s_first_category_name')[
            'ug_cost_rate'].quantile(0.90)
        cat_expt_prod_loss_rate_df = expt_prod_loss_rate_df.groupby('s_first_category_name')[
            'expt_prod_loss_rate'].quantile(0.90)
        cat_platform_commission_cost_rate_df = platform_commission_cost_rate_df.groupby('s_first_category_name')[
            'platform_commission_cost_rate'].quantile(0.90)
        cat_a_logistic_cost_rate_df = a_logistic_cost_rate_df.groupby('s_first_category_name')[
            'a_logistic_cost_rate'].quantile(0.75)

        # 按全量品计算的卡控费率值
        all_sample_rate = sample_rate_df['sample_rate'].quantile(0.90)
        all_ug_cost_rate = ug_cost_rate_df['ug_cost_rate'].quantile(0.90)
        all_expt_prod_loss_rate = expt_prod_loss_rate_df['expt_prod_loss_rate'].quantile(0.90)
        all_platform_commission_cost_rate = platform_commission_cost_rate_df['platform_commission_cost_rate'].quantile(
            0.90)
        all_a_logistic_cost_rate = a_logistic_cost_rate_df['a_logistic_cost_rate'].quantile(0.75)
        # 样品费率、UG费率、货损率、平台佣金率、a段物流成本含货损率，卡控值计算完成
        self.c1_cap_cate_lst = cap_sum_df['s_first_category_name'].drop_duplicates().values.tolist()

        # 达人佣金率线性拟合计算，输出斜率、截距
        # 按一级类目
        data_dct_lst = []
        for cate in self.c1_cap_cate_lst:
            fitting_df = cap_sum_df[cap_sum_df['s_first_category_name'] == cate]
            # 剔除极小极大值，优化拟合结果
            fitting_df = fitting_df[(fitting_df['content_payment_amt_rate'] >= 0.05) & (fitting_df['content_payment_amt_rate'] < 1.0)]
            # 内容占比与达人佣金率线性拟合
            y = fitting_df['author_commission_rate']
            X = fitting_df['content_payment_amt_rate']

            # 添加常数项
            X = sm.add_constant(X)
            # 进行多元线性回归
            try:
                model = sm.OLS(y, X).fit()
            except Exception as e:
                print(f'cate {cate} {e}')

            try:
                intercept = model.params['const']
                intercept = 0 if intercept < 0 else intercept
                slope = model.params['content_payment_amt_rate']
                slope = slope * 1.3
            except:
                intercept = 0.0
                slope = 0.0

            dct = {'s_first_category_name': cate, 'author_commission_rate_intercept': intercept,
                   'author_commission_rate_slope': slope}
            data_dct_lst.append(dct)
        cap_author_commission_rate_df = pd.DataFrame(data_dct_lst).set_index('s_first_category_name')
        del data_dct_lst
        del dct

        # 按全量
        all_fitting_df = cap_sum_df[(cap_sum_df['content_payment_amt_rate'] >= 0.05) & (cap_sum_df['content_payment_amt_rate'] < 1.0)]
        # 内容占比与达人佣金率线性拟合
        y = all_fitting_df['author_commission_rate']
        X = all_fitting_df['content_payment_amt_rate']
        # 添加常数项
        X = sm.add_constant(X)
        # 进行多元线性回归
        model = sm.OLS(y, X).fit()
        try:
            all_intercept = model.params['const']
            all_intercept = 0 if intercept < 0 else intercept
            all_slope = model.params['content_payment_amt_rate']
            all_slope = all_slope * 1.3
        except:
            all_intercept = 0.0
            all_slope = 0.0

        # 标记商品数足够的格子
        sufficient_df = cap_sum_df[['s_first_category_name', 'product_id']].groupby('s_first_category_name').count()
        sufficient_df['sufficient_tag'] = np.where(sufficient_df['product_id'] >= 100, 1, 0)
        # 足够的按格子,足够的按格子,不足的按全量卡控值赋值
        ntile_df_lst = [sufficient_df['sufficient_tag'], cat_sample_rate_df, cat_ug_cost_rate_df,
                        cat_expt_prod_loss_rate_df, cat_platform_commission_cost_rate_df, cat_a_logistic_cost_rate_df, ]
        cap_sum_1c_df = pd.concat(ntile_df_lst, axis=1)
        cap_sum_1c_df['sample_rate'] = np.where(cap_sum_1c_df['sufficient_tag'] == 1, cap_sum_1c_df['sample_rate'], all_sample_rate)
        cap_sum_1c_df['ug_cost_rate'] = np.where(cap_sum_1c_df['sufficient_tag'] == 1, cap_sum_1c_df['ug_cost_rate'], all_ug_cost_rate)
        cap_sum_1c_df['expt_prod_loss_rate'] = np.where(cap_sum_1c_df['sufficient_tag'] == 1, cap_sum_1c_df['expt_prod_loss_rate'], all_expt_prod_loss_rate)
        cap_sum_1c_df['platform_commission_cost_rate'] = (
            np.where(cap_sum_1c_df['sufficient_tag'] == 1, cap_sum_1c_df['platform_commission_cost_rate'], all_platform_commission_cost_rate))
        cap_sum_1c_df['a_logistic_cost_rate'] = np.where(cap_sum_1c_df['sufficient_tag'] == 1, cap_sum_1c_df['a_logistic_cost_rate'], all_a_logistic_cost_rate)
        # 达人费率斜率截距写入,足够的按格子,不足的按全量卡控值赋值
        cap_sum_1c_df = pd.concat([cap_sum_1c_df, cap_author_commission_rate_df], axis=1).reset_index()
        cap_sum_1c_df['author_commission_rate_intercept'] = np.where((cap_sum_1c_df['sufficient_tag'] == 0) | (cap_sum_1c_df['author_commission_rate_slope'] == 0), 0,
                                                                     cap_sum_1c_df['author_commission_rate_intercept'])
        cap_sum_1c_df['author_commission_rate_slope'] = np.where((cap_sum_1c_df['sufficient_tag'] == 0) | (cap_sum_1c_df['author_commission_rate_slope'] == 0),
                                                                 all_slope, cap_sum_1c_df['author_commission_rate_slope'])
        cap_sum_1c_df = cap_sum_1c_df.drop('sufficient_tag', axis=1)

        # 重命名字段名称，费率名称 to 卡控费率名称
        col_lst = ['sample_rate',
                   'ug_cost_rate', 'expt_prod_loss_rate', 'platform_commission_cost_rate',
                   'a_logistic_cost_rate', 'author_commission_rate_intercept',
                   'author_commission_rate_slope']
        rename_col_lst = []
        for col in col_lst:
            n_col = 'cap_' + col
            rename_col_lst.append(n_col)
        rename_dct = dict(zip(col_lst, rename_col_lst))
        cap_sum_1c_df.rename(columns=rename_dct, inplace=True)
        self.cap_sum_1c_df = cap_sum_1c_df
        del cap_sum_1c_df
        logger.info((f"费用卡控表计算完成，类目:{self.c1_cap_cate_lst}"))
        return self

    def cal_final_tbl(self):
        """
        # 输出卡控后费用后结果、各项费用结果
        # 理论物毛率(b)的费用cap
        # cap b费用 - 0
        # cap m1达人费用 - 样品、佣金
        # cap m1其他费用 - a段物流、货损、UG、平台佣金

        # 理论物毛率(ab)的费用cap
        # cap ab费用 - a段物流、货损
        # cap m1达人费用 - 样品、佣金
        # cap m1其他费用 - UG、平台佣金
        :return:
        """

        # 优化：避免深拷贝，直接使用过滤后的数据
        cal_df_pre = self.base_data_df[self.base_data_df['error_tag'] == 0].copy()
        cal_df_pre = pd.DataFrame.merge(cal_df_pre, self.cap_sum_1c_df, how='left',
                                        on='s_first_category_name')
        cal_df_pre['cap_author_commission_rate'] = cal_df_pre['cap_author_commission_rate_intercept'] + cal_df_pre[
            'cap_author_commission_rate_slope'] * cal_df_pre['content_payment_amt_rate']

        cal_df_pre['exc_sample_rate'] = np.where(cal_df_pre['sample_rate'] > cal_df_pre['cap_sample_rate'],
                                                 cal_df_pre['sample_rate'] - cal_df_pre['cap_sample_rate'], 0.0)
        cal_df_pre['exc_author_commission_rate'] = np.where(
            cal_df_pre['author_commission_rate'] > cal_df_pre['cap_author_commission_rate'],
            cal_df_pre['author_commission_rate'] - cal_df_pre['cap_author_commission_rate'], 0.0)
        cal_df_pre['exc_a_logistic_cost_rate'] = np.where(
            cal_df_pre['a_logistic_cost_rate'] > cal_df_pre['cap_a_logistic_cost_rate'],
            cal_df_pre['a_logistic_cost_rate'] - cal_df_pre['cap_a_logistic_cost_rate'], 0.0)
        cal_df_pre['exc_expt_prod_loss_rate'] = np.where(
            cal_df_pre['expt_prod_loss_rate'] > cal_df_pre['cap_expt_prod_loss_rate'],
            cal_df_pre['expt_prod_loss_rate'] - cal_df_pre['cap_expt_prod_loss_rate'], 0.0)
        cal_df_pre['exc_ug_cost_rate'] = np.where(cal_df_pre['ug_cost_rate'] > cal_df_pre['cap_ug_cost_rate'],
                                                  cal_df_pre['ug_cost_rate'] - cal_df_pre['cap_ug_cost_rate'], 0.0)
        cal_df_pre['exc_platform_commission_cost_rate'] = np.where(
            cal_df_pre['platform_commission_cost_rate'] > cal_df_pre['cap_platform_commission_cost_rate'],
            cal_df_pre['platform_commission_cost_rate'] - cal_df_pre['cap_platform_commission_cost_rate'], 0.0)

        cal_df_pre['exc_sample_amt'] = cal_df_pre['exc_sample_rate'] * cal_df_pre['ext_tax_expt_payment_amt_usd']
        cal_df_pre['exc_author_commission_amt'] = cal_df_pre['exc_author_commission_rate'] * cal_df_pre[
            'ext_tax_expt_payment_amt_usd']
        cal_df_pre['exc_a_logistic_cost_amt'] = cal_df_pre['exc_a_logistic_cost_rate'] * cal_df_pre[
            'ext_tax_expt_payment_amt_usd']
        cal_df_pre['exc_expt_prod_loss_amt'] = cal_df_pre['exc_expt_prod_loss_rate'] * cal_df_pre[
            'ext_tax_expt_payment_amt_usd']
        cal_df_pre['exc_ug_cost_amt'] = cal_df_pre['exc_ug_cost_rate'] * cal_df_pre['ext_tax_expt_payment_amt_usd']
        cal_df_pre['exc_platform_commission_cost_amt'] = cal_df_pre['exc_platform_commission_cost_rate'] * cal_df_pre[
            'ext_tax_expt_payment_amt_usd']

        # 物毛费用	UE费用
        if self.country_code == 'US':  # US a段物流成本、货损 在M1层
            # 实际费用(除了b段物流成本、供货价之外的成本费用) 8项
            cal_df_pre['gross_profit_actual_cost_amt'] = 0
            cal_df_pre['m1_actual_cost_amt'] = cal_df_pre['a_logistic_cost_amt'] + cal_df_pre['expt_prod_loss_amt_usd'] \
                                               + cal_df_pre['ug_cost_amt'] + cal_df_pre['platform_commission_cost_usd'] \
                                               + cal_df_pre['product_publicity_cost'] + cal_df_pre[
                                                   'seller_incentives_cost']
            # 超出费用(除了b段物流成本、供货价之外的成本费用) 4项需要cap
            cal_df_pre['gross_profit_exec_cost_amt'] = 0
            cal_df_pre['m1_exec_cost_amt'] = cal_df_pre['exc_a_logistic_cost_amt'] + cal_df_pre[
                'exc_expt_prod_loss_amt'] \
                                             + cal_df_pre['exc_ug_cost_amt'] + cal_df_pre[
                                                 'exc_platform_commission_cost_amt']

        elif self.country_code == 'GB':  # UK a段物流成本、货损 在物毛层
            # 实际费用(除了b段物流成本、供货价之外的成本费用) 8项
            cal_df_pre['gross_profit_actual_cost_amt'] = cal_df_pre['a_logistic_cost_amt'] + cal_df_pre[
                'expt_prod_loss_amt_usd']
            cal_df_pre['m1_actual_cost_amt'] = cal_df_pre['ug_cost_amt'] + cal_df_pre['platform_commission_cost_usd'] \
                                               + cal_df_pre['product_publicity_cost'] + cal_df_pre[
                                                   'seller_incentives_cost']
            # 超出费用(除了b段物流成本、供货价之外的成本费用) 6项需要cap
            cal_df_pre['gross_profit_exec_cost_amt'] = cal_df_pre['exc_a_logistic_cost_amt'] + cal_df_pre[
                'exc_expt_prod_loss_amt']
            cal_df_pre['m1_exec_cost_amt'] = cal_df_pre['exc_ug_cost_amt'] + cal_df_pre[
                'exc_platform_commission_cost_amt']

        cal_df_pre['m1_actual_author_cost_amt'] = cal_df_pre['sample_amt'] + cal_df_pre['author_commission_amt']
        cal_df_pre['m1_exec_author_cost_amt'] = cal_df_pre['exc_sample_amt'] + cal_df_pre['exc_author_commission_amt']

        cal_df_pre['other_cost_amt'] = cal_df_pre['product_publicity_cost'] + cal_df_pre['seller_incentives_cost']

        # 优化内存消耗和性能 - 向量化构建exec_cost_rate_json
        exec_columns_map = {
            'exc_sample_rate': '样品费率',
            'exc_author_commission_rate': '达人佣金率',
            'exc_a_logistic_cost_rate': 'a段物流费率',
            'exc_expt_prod_loss_rate': '货损率',
            'exc_ug_cost_rate': 'ug投流费率',
            'exc_platform_commission_cost_rate': '平台佣金率'
        }

        # 使用pandas向量化操作，避免循环
        # 为每个字段创建格式化字符串列
        formatted_cols = []
        for col, label in exec_columns_map.items():
            # 向量化计算百分比并格式化
            formatted_col = f'"{label}":"' + (cal_df_pre[col].round(4) * 100).astype(str) + '%"'
            formatted_cols.append(formatted_col)

        # 使用字符串连接函数一次性合并所有列
        cal_df_pre['exec_cost_rate_json'] = "{" + formatted_cols[0]
        for i in range(1, len(formatted_cols)):
            cal_df_pre['exec_cost_rate_json'] = cal_df_pre['exec_cost_rate_json'] + "," + formatted_cols[i]
        cal_df_pre['exec_cost_rate_json'] = cal_df_pre['exec_cost_rate_json'] + "}"

        # 优化内存消耗和性能 - 向量化构建actual_cost_rate_json
        actual_columns_map = {
            'sample_rate': '样品费率',
            'author_commission_rate': '达人佣金率',
            'a_logistic_cost_rate': 'a段物流费率',
            'expt_prod_loss_rate': '货损率',
            'ug_cost_rate': 'ug投流费率',
            'platform_commission_cost_rate': '平台佣金率',
            'seller_incentives_cost_rate': '商家激励费率',
            'product_publicity_cost_rate': '品宣费率'
        }

        # 使用pandas向量化操作，避免循环
        # 为每个字段创建格式化字符串列
        formatted_cols = []
        for col, label in actual_columns_map.items():
            # 向量化计算百分比并格式化
            formatted_col = f'"{label}":"' + (cal_df_pre[col].round(4) * 100).astype(str) + '%"'
            formatted_cols.append(formatted_col)

        # 使用字符串连接函数一次性合并所有列
        cal_df_pre['actual_cost_rate_json'] = "{" + formatted_cols[0]
        for i in range(1, len(formatted_cols)):
            cal_df_pre['actual_cost_rate_json'] = cal_df_pre['actual_cost_rate_json'] + "," + formatted_cols[i]
        cal_df_pre['actual_cost_rate_json'] = cal_df_pre['actual_cost_rate_json'] + "}"

        self.cal_data_df = cal_df_pre
        del cal_df_pre
        return self

    def del_base_df_cache(self):
        del self.base_data_df


class PriceCalculate(LoadCalData):
    def __init__(self, country_code, server_name=None):
        super().__init__(country_code=country_code, server_name=server_name)
        self.result_df: pd.DataFrame = None
        self.conf: dict = {
            'spu_code': 'spu_code',
            'product_id': 'product_id',
            'country_code': 'country_code',
            'list_price': 'list_price_usd',
            'incentive_rate': 'reg_discount',
            'coupon_rate': 'coupon_rate',
            # 'seller_bonus_subsidy_rate': '',
            # 'seller_logistic_subsidy_rate': '',
            # 'seller_other_subsidy_rate': '',
            # 'platform_subsidy_amt': '',
            'payment_shipping_amt': 'payment_shipping_amt_usd',
            'settlement_rate': 'settlement_rate',
            # 'vat': 'vat',
            'prod_cost_amt': 'origin_prod_cost_amt',
            'b_logistic_cost_amt': 'logistic_cost_amt',
            'a_logistic_cost_amt': 'a_logistic_cost_amt',
            'expt_prod_loss_amt': 'expt_prod_loss_amt_usd',
            'tax_cost_amt': 'tax_cost_amt',
            # 'tax_cost_amt_f_weight': '',
            # 'tax_cost_amt_f_quant': '',
            'tax_rate': 'tax_rate',
            'author_commission_cost_amt': 'author_commission_amt',
            'sample_amt': 'sample_amt',
            'ug_cost_amt': 'ug_cost_amt',
            'platform_commission_cost_rate': 'platform_commission_cost_rate',
            'gross_profit_exec_amt': 'gross_profit_exec_cost_amt',
            'm1_cost_exec_amt': 'm1_exec_cost_amt',
            'm1_author_cost_exec_amt': 'm1_exec_author_cost_amt',

            'target_b_gross_profit_rate': 'target_b_gross_profit_rate',
            'target_ab_gross_profit_rate': 'target_ab_gross_profit_rate',
            'target_margin1_rate': 'target_margin1_rate',
        }
        self.data_dct = None
        self.data_type = None
        self.pid_lst = None

    def load(self, by, name=None, path=None, pid_lst=None, print_sql=False):
        if not by:
            pass
        elif by == 'sql':
            self.load_from_sql(pid_lst=pid_lst, print_sql=print_sql)

        elif by == 'pickle':
            if path and name:
                self.load_from_pickle(name=name, path=path)
                country_lst = self.cal_data_df['country_code'].drop_duplicates().values.tolist()
                if self.country_code not in country_lst:
                    raise ValueError('算价基础数据不含指定国家请重新读取')
            else:
                try:
                    self.load_from_pickle(name='cal_data_df', path=path)
                except BaseException as e:
                    print(f'pickle 读取失败,请补充pickle读取信息 {e} ')
        else:
            raise ValueError('请输入正确的读取算价底表方式')
        return self

    def save(self, path=None):
        if not self.cal_data_df.empty:
            self.pik.save(data=self.cal_data_df, name='cal_data_df', path=path)
            print('算价基础数据,存储完成')
        else:
            print('算价基础数据,无数据可存储')
        return self

    def safe_value(self, value):
        """
        将可能为None的值转换为安全的默认值(区分数值和DataFrame)
        参数:
            value: 待处理的值(可能为None、数值、DataFrame)
            default_num: 数值类型的默认值(默认0)
            default_df: DataFrame类型的默认值(默认空DataFrame)
        返回:
            安全值(非None)
        """
        if value is None:
            if self.data_type == 'df':
                value = pd.Series(data=0, index=self.data.index)
            else:
                value = 0
            self.value_safe = False
        else:
            self.value_safe = True
        return value

    def data_dct_get(self, name):
        value = self.data_dct.get(name)
        return self.safe_value(value)

    def data_map(self, data=None, conf=None):
        self.data = data if data else self.cal_data_df
        self.conf = conf if conf else self.conf
        if data and not conf:
            raise ValueError('请补充config信息')
        if isinstance(self.data, pd.DataFrame):
            self.data_type = 'df'
        elif isinstance(self.data, dict):
            self.data_type = 'dict'
        else:
            raise ValueError('数据仅支持[df,dict]')

        # 根据conf字典，将不同外部输入字段映射为方法内对应字段名称
        self.data_dct = {}
        for k, v in self.conf.items():
            if self.data_type == 'df':
                try:
                    self.data_dct[k] = self.data[v]
                except:
                    self.data_dct[k] = None
            elif self.data_type == 'dict':
                self.data_dct[k] = self.data.get(v)
            else:
                raise ValueError('数据输入类型错误')

        self.spu_code = self.data_dct_get('spu_code')
        spu_safe = self.value_safe
        self.product_id = self.data_dct_get('product_id')
        pid_safe = self.value_safe
        if self.data_type == 'df':
            if not (spu_safe or pid_safe):
                raise ValueError('请输入 spu_code/product_id')

        self.country_code = self.data_dct_get('country_code')
        if not self.value_safe:
            raise ValueError('请输入 country_code')

        self.list_price = self.data_dct_get('list_price')
        self.incentive_rate = self.data_dct_get('incentive_rate')
        self.coupon_rate = self.data_dct_get('coupon_rate')
        self.seller_bonus_subsidy_rate = self.data_dct_get('seller_bonus_subsidy_rate')
        self.seller_logistic_subsidy_rate = self.data_dct_get('seller_logistic_subsidy_rate')
        self.seller_other_subsidy_rate = self.seller_bonus_subsidy_rate + self.seller_logistic_subsidy_rate

        self.platform_subsidy_amt = self.data_dct_get('platform_subsidy_amt')  # 行业补贴=行业货补+行业券补+行业物流补贴*行业承担比例(需要维护承担比例)+TT主端裂变券补贴
        self.payment_shipping_amt = self.data_dct_get('payment_shipping_amt')

        self.settlement_rate = self.data_dct_get('settlement_rate')

        self.data_dct_get('vat')
        if not self.value_safe:
            if self.data_type == 'df':
                self.vat = pd.Series(np.select([self.country_code == 'US', self.country_code == 'GB', ], [0, 0.2]))
            elif self.data_type == 'dict':
                if self.country_code == 'US':
                    self.vat = 0
                elif self.country_code == 'GB':
                    self.vat = 0.2
        else:
            self.vat = self.data_dct_get('vat')

        self.prod_cost_amt = self.data_dct_get('prod_cost_amt')
        self.b_logistic_cost_amt = self.data_dct_get('b_logistic_cost_amt')
        self.a_logistic_cost_amt = self.data_dct_get('a_logistic_cost_amt')
        self.expt_prod_loss_amt = self.data_dct_get('expt_prod_loss_amt')

        self.tax_cost_amt = self.data_dct_get('tax_cost_amt')
        self.tax_cost_amt_f_weight = self.data_dct_get('tax_cost_amt_f_weight')  # --从重税金
        self.tax_cost_amt_f_quant = self.data_dct_get('tax_cost_amt_f_quant')  # --从量税金
        self.tax_rate = self.data_dct_get('tax_rate')

        self.author_commission_cost_amt = self.data_dct_get('author_commission_cost_amt')
        self.sample_amt = self.data_dct_get('sample_amt')
        self.ug_cost_amt = self.data_dct_get('ug_cost_amt')
        self.platform_commission_cost_rate = self.data_dct_get('platform_commission_cost_rate')

        self.gross_profit_exec_amt = self.data_dct_get('gross_profit_exec_amt')
        self.m1_cost_exec_amt = self.data_dct_get('m1_cost_exec_amt')
        self.m1_author_cost_exec_amt = self.data_dct_get('m1_author_cost_exec_amt')

        self.target_b_gross_profit_rate = self.data_dct_get('target_b_gross_profit_rate')
        self.target_ab_gross_profit_rate = self.data_dct_get('target_ab_gross_profit_rate')
        self.target_margin1_rate = self.data_dct_get('target_margin1_rate')

        return self

    # 国家/货补率 推 物毛率/M1%
    def ir_to_fni(self):
        self.financial_net_income = (
                                            self.list_price * (1 - self.incentive_rate - self.coupon_rate - self.seller_other_subsidy_rate)
                                            + self.payment_shipping_amt + self.platform_subsidy_amt
                                    ) * self.settlement_rate / (1 + self.vat)

    def cal_tax_amt(self):
        if self.data_type == 'df':
            self.tax_base = pd.Series(np.select([self.country_code == 'US', ], [self.prod_cost_amt + 0.40298, ], 0))

        elif self.data_type == 'dict':
            if self.country_code == 'US':
                self.tax_base = self.prod_cost_amt + 0.40298
            else:
                self.tax_cost_amt = 0
        self.tax_cost_amt = self.tax_base * self.tax_rate + self.tax_cost_amt_f_weight + self.tax_cost_amt_f_quant
        return self

    def ir_to_gp(self):
        self.ir_to_fni()
        self.cal_tax_amt()
        self.b_gross_profit = (self.financial_net_income - self.prod_cost_amt * self.settlement_rate
                               - self.b_logistic_cost_amt - self.tax_cost_amt + self.gross_profit_exec_amt)
        self.ab_gross_profit = (self.financial_net_income - self.prod_cost_amt * self.settlement_rate
                                - self.b_logistic_cost_amt - self.a_logistic_cost_amt - self.tax_cost_amt + self.gross_profit_exec_amt)
        self.margin1 = (
                self.financial_net_income - self.prod_cost_amt * self.settlement_rate
                - self.b_logistic_cost_amt - self.tax_cost_amt - self.a_logistic_cost_amt
                - self.expt_prod_loss_amt - self.author_commission_cost_amt - self.sample_amt - self.ug_cost_amt
                - self.financial_net_income * self.platform_commission_cost_rate
                + self.gross_profit_exec_amt + self.m1_cost_exec_amt + self.m1_author_cost_exec_amt)
        return self

    def ir_to_gpr(self):
        self.ir_to_gp()
        self.b_gross_profit_rate = self.b_gross_profit / self.financial_net_income
        self.ab_gross_profit_rate = self.ab_gross_profit / self.financial_net_income
        self.margin1_rate = self.margin1 / self.financial_net_income
        return self

    def b_gpr_to_ir(self):
        self.cal_tax_amt()

        # 1 - 券补率 - 其他补贴率 - ((物毛内成本费用抵减 - 供货价 * 结算率 - b段物流成本 - ((供货价 + a段物流成本(关务)) * 税率 + 从重税金 + 从量税金)) * (1 + VAT)) / (
        #             商品原价 * 结算率 * (目标物流后毛利率 - 1)) + (物流支付GMV + 行业补贴) / 商品原价

        self.incentive_rate = 1 - self.coupon_rate - self.seller_other_subsidy_rate - (
                (self.gross_profit_exec_amt - self.prod_cost_amt * self.settlement_rate - self.b_logistic_cost_amt - self.tax_cost_amt) * (1 + self.vat)) / (
                                      self.list_price * self.settlement_rate * (self.target_b_gross_profit_rate - 1)) + (
                                      self.payment_shipping_amt + self.platform_subsidy_amt) / self.list_price
        return self

    # def ab_gpr_to_ir(self):
    #     self.cal_tax_amt()
    #
    #     # 1 - 券补率 - 其他补贴率 - ((物毛内成本费用抵减 - 供货价 * 结算率 - b段物流成本 - ((供货价 + a段物流成本(关务)) * 税率 + 从重税金 + 从量税金)) * (1 + VAT)) / (
    #     #             商品原价 * 结算率 * (目标物流后毛利率 - 1)) + (物流支付GMV + 行业补贴) / 商品原价
    #
    #     self.incentive_rate = 1 - self.coupon_rate - self.seller_other_subsidy_rate - (
    #                 (self.gross_profit_exec_amt - self.prod_cost_amt * self.settlement_rate - self.b_logistic_cost_amt - self.a_logistic_cost_amt - self.tax_cost_amt) * (1 + self.vat)) / (
    #                 self.list_price * self.settlement_rate * (self.b_gross_profit_rate - 1)) + (self.payment_shipping_amt + self.platform_subsidy_amt) / self.list_price
    #     return self

    def print_attr_lst(self):
        print(list(self.__dict__.keys()))

    def get_result_data_lst(self, col_lst):
        self.attr_lst = []
        for attr in col_lst:
            self.attr_lst.append(getattr(self, attr, None))
        return self.attr_lst

    def get_result_data_dct(self, col_lst):
        self.attr_dct = {}
        for attr in col_lst:
            self.attr_dct[attr] = getattr(self, attr, None)
        return self.attr_dct

    def get_result_df(self, col_lst):
        attr_dct = self.get_result_data_dct(col_lst)
        self.result_df = pd.concat(attr_dct, axis=1)
        return self.result_df
