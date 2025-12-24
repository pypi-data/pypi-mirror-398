import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')
import mns_common.utils.date_handle_util as date_handle_util


# 查询日期str_day 大于chg的数据
@lru_cache(maxsize=None)
def get_last_trade_k_line_high_chg(str_day, chg):
    query = {'date': date_handle_util.no_slash_date(str_day), "chg": {"$gte": chg}}
    return mongodb_util.find_query_data_choose_field('stock_qfq_daily', query,
                                                     query_field={'symbol': 1, 'name': 1, "chg": 1})


# 计算k线相关参数 当前最大涨幅  回落的幅度 超平均价幅度
def calculate_real_time_k_line_param(real_time_quotes_now):
    # 最大涨幅
    real_time_quotes_now['max_chg'] = round(
        (((real_time_quotes_now['high'] - real_time_quotes_now['yesterday_price']) / real_time_quotes_now[
            'yesterday_price']) * 100), 2)
    # 最大涨幅与当前涨幅的差值 越大表明是拉高出货
    real_time_quotes_now['chg_fall_back'] = round(real_time_quotes_now['max_chg'] - real_time_quotes_now['chg'], 2)
    # 当前价格与今天开盘价格的差值 为负表明为下跌趋势
    real_time_quotes_now['chg_from_open'] = round(
        (((real_time_quotes_now['now_price'] - real_time_quotes_now['open']) / real_time_quotes_now[
            'open']) * 100), 2)
    # 最低和最高之间的差值
    real_time_quotes_now['high_from_low_chg'] = round(
        (((real_time_quotes_now['high'] - real_time_quotes_now['low']) / real_time_quotes_now[
            'low']) * 100), 2)

    if 'average_price' in real_time_quotes_now.columns:
        # 高于平均线的差值 越大表明极速拉伸
        real_time_quotes_now['diff_avg_chg'] = round(
            (((real_time_quotes_now['now_price'] - real_time_quotes_now['average_price']) / real_time_quotes_now[
                'average_price']) * 100), 2)
    else:
        real_time_quotes_now['diff_avg_chg'] = 0
    return real_time_quotes_now


# 计算当前 成交量变化和均线数据
def calculate_exchange_and_avg_chg(real_time_quotes_now_kc):
    real_time_quotes_now_kc['exchange_chg_percent_yesterday'] = round(
        (real_time_quotes_now_kc['exchange'] / real_time_quotes_now_kc['exchange_mean_last']), 2)

    real_time_quotes_now_kc['exchange_chg_percent_ten'] = round(
        (real_time_quotes_now_kc['amount_level'] / real_time_quotes_now_kc['mean_amount_ten']), 2)

    real_time_quotes_now_kc['now_chg_diff_five'] = real_time_quotes_now_kc['close_difference_five_last'] + \
                                                   real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_diff_ten'] = real_time_quotes_now_kc['close_difference_ten_last'] + \
                                                  real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_diff_twenty'] = real_time_quotes_now_kc['close_difference_twenty_last'] + \
                                                     real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_diff_thirty'] = real_time_quotes_now_kc['close_difference_thirty_last'] + \
                                                     real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_diff_sixty'] = real_time_quotes_now_kc['close_difference_sixty_last'] + \
                                                    real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_plus_last_chg'] = real_time_quotes_now_kc['chg_last'] + \
                                                       real_time_quotes_now_kc['chg']
    real_time_quotes_now_kc['now_chg_plus_two_days'] = (real_time_quotes_now_kc['daily01'] + \
                                                        real_time_quotes_now_kc['chg'] +
                                                        real_time_quotes_now_kc['daily02'])

    real_time_quotes_now_kc['now_chg_plus_three_days'] = real_time_quotes_now_kc['daily01'] + real_time_quotes_now_kc[
        'daily02'] + real_time_quotes_now_kc['daily03'] + real_time_quotes_now_kc['chg']

    real_time_quotes_now_kc['now_chg_plus_four_days'] = real_time_quotes_now_kc['daily01'] + real_time_quotes_now_kc[
        'daily02'] + real_time_quotes_now_kc['daily03'] + real_time_quotes_now_kc['daily04'] + real_time_quotes_now_kc[
                                                            'chg']

    return real_time_quotes_now_kc


# 获取交易日期
def get_deal_days(str_day, symbol):
    # 当天没有k线数据时 进行同步
    query = {"symbol": symbol, 'date': {"$lt": date_handle_util.no_slash_date(str_day)}}
    return mongodb_util.count(query, 'stock_qfq_daily')
