import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.api.akshare.stock_zt_pool_api as stock_zt_pool_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import pandas as pd
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
mongodb_util = MongodbUtil('27017')
from loguru import logger


@lru_cache(maxsize=None)
def get_last_trade_day_zt(str_day):
    last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)
    query = {'str_day': last_trade_day}
    last_trade_day_zt = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL, query)
    if last_trade_day_zt is None or last_trade_day_zt.shape[0] == 0:
        last_trade_day_zt = stock_zt_pool_api.stock_em_zt_pool_df(date_handle_util.no_slash_date(last_trade_day))
    return last_trade_day_zt


# 按照字段分组
def group_by_industry(real_time_quotes_now, field):
    grouped = real_time_quotes_now.groupby(field)
    result_list = grouped.size()
    group_industry = pd.DataFrame(result_list, columns=['number'])
    # 降序排列
    group_industry[field] = group_industry.index
    group_industry = group_industry.sort_values(by=['number'],
                                                ascending=False)
    return group_industry


# 涨停分组
def group_industry_zt_by_field(industry_realtime_quotes_now, field):
    try:
        industry_realtime_quotes_now_zt = industry_realtime_quotes_now.loc[
            (industry_realtime_quotes_now['wei_bi'] == 100) & (industry_realtime_quotes_now['classification'].isin(
                ['S', 'H']))]
    except Exception as e:
        industry_realtime_quotes_now_zt = industry_realtime_quotes_now.loc[
            (((industry_realtime_quotes_now['classification'].isin(['S', 'H'])) & (
                    industry_realtime_quotes_now['chg'] >= 9.90)) |
             ((industry_realtime_quotes_now['classification'].isin(['K', 'C', 'X'])) & (
                     industry_realtime_quotes_now['chg'] >= 19.90)))]

    zt_group_industry = group_by_industry(industry_realtime_quotes_now_zt, field)
    zt_group_industry = zt_group_industry.rename(columns={'number': field + '_' + 'sh_zt_number'})

    # 科创 创业 北交所涨停股票
    industry_realtime_a = industry_realtime_quotes_now.loc[(industry_realtime_quotes_now['wei_bi'] == 100) & (
        industry_realtime_quotes_now['classification'].isin(['K', 'C', 'X']))]

    if industry_realtime_a.shape[0] == 0:
        zt_group_industry[field + '_' + 'kc_zt_number'] = 0
    else:
        kc_zt_group_industry = group_by_industry(industry_realtime_a, field)
        kc_zt_group_industry = kc_zt_group_industry.rename(columns={'number': field + '_' + 'kc_zt_number'})
        zt_group_industry = zt_group_industry.set_index([field], drop=False)
        kc_zt_group_industry = kc_zt_group_industry.set_index([field], drop=True)
        zt_group_industry = pd.merge(zt_group_industry, kc_zt_group_industry, how='outer',
                                     left_index=True, right_index=True)

    # 高涨幅 10 -19 之间的
    industry_realtime_quotes_now_high_chg = industry_realtime_quotes_now.loc[
        (industry_realtime_quotes_now['wei_bi'] != 100) & (industry_realtime_quotes_now['chg'] >= 10)]
    if industry_realtime_quotes_now_high_chg.shape[0] == 0:
        zt_group_industry[field + '_' + 'kc_high_chg_number'] = 0
    else:
        kc_high_chg_group_industry = group_by_industry(industry_realtime_quotes_now_high_chg, field)
        kc_high_chg_group_industry = kc_high_chg_group_industry.rename(
            columns={'number': field + '_' + 'kc_high_chg_number'})
        kc_high_chg_group_industry = kc_high_chg_group_industry.set_index([field], drop=True)

        zt_group_industry = pd.merge(zt_group_industry, kc_high_chg_group_industry, how='outer',
                                     left_index=True, right_index=True)

        # 中涨幅 5 -10 之间的
    industry_realtime_quotes_now_middle_chg = industry_realtime_quotes_now.loc[
        (industry_realtime_quotes_now['wei_bi'] != 100) & (industry_realtime_quotes_now['chg'] < 10) & (
                industry_realtime_quotes_now['chg'] >= 5)]
    if industry_realtime_quotes_now_middle_chg.shape[0] == 0:
        zt_group_industry[field + '_' + 'middle_chg_number'] = 0
    else:
        middle_chg_group_industry = group_by_industry(industry_realtime_quotes_now_middle_chg, field)
        middle_chg_group_industry = middle_chg_group_industry.rename(
            columns={'number': field + '_' + 'middle_chg_number'})
        middle_chg_group_industry = middle_chg_group_industry.set_index([field], drop=True)

        zt_group_industry = pd.merge(zt_group_industry, middle_chg_group_industry, how='outer',
                                     left_index=True, right_index=True)
    # 0-5 之间涨幅的
    industry_realtime_quotes_now_low_chg = industry_realtime_quotes_now.loc[
        (industry_realtime_quotes_now['chg'] < 5) & (
                industry_realtime_quotes_now['chg'] >= 0)]

    if industry_realtime_quotes_now_low_chg.shape[0] == 0:
        zt_group_industry[field + '_' + 'low_chg_number'] = 0
    else:
        low_chg_group_industry = group_by_industry(industry_realtime_quotes_now_low_chg, field)
        low_chg_group_industry = low_chg_group_industry.rename(
            columns={'number': field + '_' + 'low_chg_number'})
        low_chg_group_industry = low_chg_group_industry.set_index([field], drop=True)

        zt_group_industry = pd.merge(zt_group_industry, low_chg_group_industry, how='outer',
                                     left_index=True, right_index=True)

    # 跌幅在0到-9之间的

    industry_realtime_quotes_now_negative_chg = industry_realtime_quotes_now.loc[
        (industry_realtime_quotes_now['chg'] < 0) & (
                industry_realtime_quotes_now['chg'] >= -9)]

    if industry_realtime_quotes_now_negative_chg.shape[0] == 0:
        zt_group_industry[field + '_' + 'negative_chg_number'] = 0
    else:
        negative_chg_group_industry = group_by_industry(industry_realtime_quotes_now_negative_chg, field)
        negative_chg_group_industry = negative_chg_group_industry.rename(
            columns={'number': field + '_' + 'negative_chg_number'})
        negative_chg_group_industry = negative_chg_group_industry.set_index([field], drop=True)

        zt_group_industry = pd.merge(zt_group_industry, negative_chg_group_industry, how='outer',
                                     left_index=True, right_index=True)

    # 跌幅大于9%的
    industry_realtime_quotes_now_dt = industry_realtime_quotes_now.loc[
        (industry_realtime_quotes_now['chg'] < -9)]

    if industry_realtime_quotes_now_dt.shape[0] == 0:
        zt_group_industry[field + '_' + 'dt_chg_number'] = 0
    else:
        dt_chg_group_industry = group_by_industry(industry_realtime_quotes_now_dt, field)
        dt_chg_group_industry = dt_chg_group_industry.rename(
            columns={'number': field + '_' + 'dt_chg_number'})
        dt_chg_group_industry = dt_chg_group_industry.set_index([field], drop=True)

        zt_group_industry = pd.merge(zt_group_industry, dt_chg_group_industry, how='outer',
                                     left_index=True, right_index=True)

    zt_group_industry[field] = zt_group_industry.index
    zt_group_industry = zt_group_industry.fillna(0)

    return zt_group_industry


# 获取当天炸板股票代码 zb
def set_zb_symbol(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[(real_time_quotes_now['wei_bi'] != 100)]
    real_time_quotes_zb = real_time_quotes_now.loc[
        ((real_time_quotes_now['classification'].isin(['S', 'H'])) & (real_time_quotes_now['max_chg'] >= 9.90))
        | (real_time_quotes_now['classification'].isin(['K', 'C'])) & (real_time_quotes_now['max_chg'] >= 19.90)
        | (real_time_quotes_now['classification'].isin(['X'])) & (real_time_quotes_now['max_chg'] >= 29.90)]

    if real_time_quotes_zb.shape[0] == 0:
        zb_symbol_list = ['000001']
    else:
        zb_symbol_list = list(real_time_quotes_zb['symbol'])

    real_time_quotes_now.loc[real_time_quotes_now['symbol'].isin(zb_symbol_list), 'is_zb'] = True
    return real_time_quotes_now


# 获取一段时间连板股票信息
@lru_cache(maxsize=None)
def get_period_connected_boards_zt_pool(begin_day, end_day, connected_boards_numbers):
    query = {"connected_boards_numbers": connected_boards_numbers,
             "$and": [{"before_five_day": {"$gte": begin_day}}, {"before_five_day": {"$gte": end_day}}]}

    stock_zt_pool_df = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL, query)
    if data_frame_util.is_empty(stock_zt_pool_df):
        zt_symbol_list = ['000001']
    else:
        zt_symbol_list = list(stock_zt_pool_df['symbol'])
    return zt_symbol_list


# 获取一段时间五板股票
@lru_cache(maxsize=None)
def get_period_five_boards_zt_pool(begin_day, end_day):
    query = {"$and": [{"before_five_day": {"$gte": begin_day}}, {"before_five_day": {"$gte": end_day}}]}
    stock_zt_pool_five_df = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL_FIVE, query)
    if data_frame_util.is_empty(stock_zt_pool_five_df):
        zt_symbol_list = ['000001']
    else:
        zt_symbol_list = list(stock_zt_pool_five_df['symbol'])
    return zt_symbol_list


'''
涨停原因分组统计
'''


def zt_reason_group(zt_pool_df):
    if data_frame_util.is_empty(zt_pool_df):
        return pd.DataFrame()

    zt_pool_df = common_service_fun_api.exclude_st_symbol(zt_pool_df)
    if data_frame_util.is_empty(zt_pool_df):
        return pd.DataFrame()

    zt_pool_df['symbol'] = zt_pool_df['symbol'].astype(str)
    result_group_df = None
    for zt_stock_one in zt_pool_df.itertuples():
        try:
            zt_reason = zt_stock_one.zt_reason
            if data_frame_util.is_string_empty(zt_reason):
                continue
            zt_reason_list = zt_reason.split("+")
            if len(zt_reason_list) > 0:
                for zt_reason_one in zt_reason_list:
                    zt_reason_dict = {'zt_reason_name': zt_reason_one,
                                      'number': 1
                                      }
                    zt_reason_df_new = pd.DataFrame(zt_reason_dict, index=[0])
                    if result_group_df is None:
                        result_group_df = zt_reason_df_new
                    else:
                        exist_zt_reason = result_group_df.loc[result_group_df['zt_reason_name'] == zt_reason_one]
                        if data_frame_util.is_not_empty(exist_zt_reason):
                            result_group_df.loc[result_group_df['zt_reason_name'] == zt_reason_one, "number"] = \
                                exist_zt_reason['number'] + 1
                        else:
                            result_group_df = pd.concat([result_group_df, zt_reason_df_new])

        except BaseException as e:
            logger.error("涨停原因分组出现异常:{},{}", zt_stock_one.symbol, e)
    if data_frame_util.is_not_empty(result_group_df):
        result_group_df = result_group_df.sort_values(by=['number'], ascending=False)

    return result_group_df


if __name__ == '__main__':
    get_last_trade_day_zt('20231215')
