import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import re
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.zt.zt_common_service_api as zt_common_service_api
from loguru import logger
# question
# 必填，查询问句
#
# sort_key
# 非必填，指定用于排序的字段，值为返回结果的列名
#
# sort_order
# 非必填，排序规则，至为asc（升序）或desc（降序）
#
# page
# 非必填，查询的页号，默认为1
#
# perpage
# 非必填，每页数据条数，默认值100，由于问财做了数据限制，最大值为100，指定大于100的数值无效。
#
# loop
# 非必填，是否循环分页，返回多页合并数据。默认值为False，可以设置为True或具体数值。
#
# 当设置为True时，程序会一直循环到最后一页，返回全部数据。
#
# 当设置具体数值n时，循环请求n页，返回n页合并数据。


import mns_common.component.em.em_real_time_quotes_api as em_real_time_quotes_api
from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.api.ths.wen_cai.ths_wen_cai_api as ths_wen_cai_api
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.api.akshare.stock_zt_pool_api as stock_zt_pool_api
import mns_common.component.cache.cache_service as cache_service

mongodb_util = MongodbUtil('27017')

# 缓存key
THS_NOW_ZT_POOL = 'ths_now_zt_pool'
# 缓存过期时间 一分钟
CACHE_TIME_OUT_TIME = 60


# 频繁调用容易被封  设置缓存
def get_ths_stock_zt_reason_with_cache(str_day):
    stock_zt_reason = cache_service.get_cache(THS_NOW_ZT_POOL)
    if data_frame_util.is_empty(stock_zt_reason):
        stock_zt_reason = get_zt_reason(str_day)
        # time_out 为秒
        cache_service.set_cache_time_out(THS_NOW_ZT_POOL, stock_zt_reason, CACHE_TIME_OUT_TIME)
        return stock_zt_reason
    else:
        return stock_zt_reason


# 数据不对 todo
def get_zt_reason(str_day):
    if data_frame_util.is_string_not_empty(str_day):
        key_word = str_day + '涨停'
    else:
        key_word = '涨停'
    zt_df = ths_wen_cai_api.wen_cai_api(key_word, 'stock')
    if data_frame_util.is_empty(zt_df):
        return None
    zt_df.fillna('0', inplace=True)
    no_slash_day = date_handle_util.no_slash_date(str_day)
    no_slash_day = "[" + no_slash_day + "]"
    zt_df = zt_df.rename(columns={
        "股票代码": "code",
        "股票简称": "name",
        "涨停" + no_slash_day: "zt_tag",
        "首次涨停时间" + no_slash_day: "first_closure_time",
        "最终涨停时间" + no_slash_day: "last_closure_time",
        "涨停明细数据" + no_slash_day: "zt_detail",
        "连续涨停天数" + no_slash_day: "connected_boards_numbers",
        "涨停原因类别" + no_slash_day: "zt_reason",
        "涨停封单量" + no_slash_day: "closure_volume",
        "涨停封单额" + no_slash_day: "closure_funds",
        "涨停封单量占成交量比" + no_slash_day: "closure_funds_per_amount",
        "涨停封单量占流通a股比" + no_slash_day: "closure_funds_per_flow_mv",
        "涨停开板次数" + no_slash_day: "frying_plates_numbers",
        "a股市值(不含限售股)" + no_slash_day: "flow_mv",
        "几天几板" + no_slash_day: "statistics_detail",
        "涨停类型" + no_slash_day: "zt_type",
        "最新价": "now_price",
        "最新涨跌幅": "chg",
        "code": "simple_code",

    })
    zt_df['code'] = zt_df['code'].astype(str)
    zt_df['symbol'] = zt_df['code'].astype(str).str.slice(0, 6)
    if 'statistics_detail' in zt_df.columns:
        zt_df['statistics'] = zt_df['statistics_detail'].apply(convert_statistics)
    if 'code' in zt_df.columns:
        del zt_df['code']
    if 'flow_mv' in zt_df.columns:
        del zt_df['flow_mv']
    zt_df['zt_flag'] = True
    zt_df['str_day'] = str_day
    # 渣渣有重复的数据
    zt_df.drop_duplicates('symbol', keep='last', inplace=True)
    return zt_df


# 定义一个函数，用于将统计数据转换成相应的格式
def convert_statistics(stat):
    try:
        if stat is None:
            return '1/1'
        match = re.match(r'(\d+)天(\d+)板', stat)
        if match:
            n, m = map(int, match.groups())
            return f'{n}/{m}'
        elif stat == '首板涨停':
            return '1/1'
        else:
            return stat
    except BaseException as e:
        logger.error("转换出现异常:{},{}", e, stat)
        return '1/1'


# 获取实时行情涨停列表
def get_real_time_zt_info():
    real_time_df = em_real_time_quotes_api.get_real_time_quotes_now(None, None)
    real_time_df_zt = real_time_df.loc[
        (real_time_df['chg'] > common_service_fun_api.ZT_CHG) | (real_time_df['wei_bi'] == 100)]
    if data_frame_util.is_empty(real_time_df_zt):
        return pd.DataFrame()
    real_time_df_zt = real_time_df_zt[[
        'symbol',
        'chg',
        'amount',
        'quantity_ratio',
        'now_price',
        'high',
        'low',
        'open',
        'exchange',
        'wei_bi',
        'flow_mv',
        'total_mv',
        'buy_1_num'
    ]]
    company_df = company_common_service_new_api.get_company_all_info_info()
    company_df = company_df[[
        '_id',
        'name',
        'list_date',
        "industry",
        "first_sw_industry",
        "second_sw_industry",
        "third_sw_industry",
        "ths_concept_name",
        "ths_concept_code",
        "ths_concept_sync_day",
        "em_industry",
        "company_type",
        "mv_circulation_ratio",
        "diff_days"
    ]]
    company_df = company_df.loc[company_df['_id'].isin(real_time_df_zt['symbol'])]
    company_df = company_df.set_index(['_id'], drop=True)
    real_time_df_zt = real_time_df_zt.set_index(['symbol'], drop=False)
    real_time_df_zt = pd.merge(real_time_df_zt, company_df, how='outer',
                               left_index=True, right_index=True)
    real_time_df_zt = common_service_fun_api.classify_symbol(real_time_df_zt)
    real_time_df_zt = common_service_fun_api.total_mv_classification(real_time_df_zt)
    real_time_df_zt = common_service_fun_api.symbol_amount_simple(real_time_df_zt)
    real_time_df_zt = common_service_fun_api.exclude_new_stock(real_time_df_zt)
    real_time_df_zt.fillna('0', inplace=True)
    real_time_df_zt['chg'] = real_time_df_zt['chg'].astype(float)
    real_time_df_zt['chg'] = round(
        real_time_df_zt['chg'], 2)
    real_time_df_zt = real_time_df_zt.sort_values(by=['chg'], ascending=False)
    return real_time_df_zt


def get_now_zt_pool_with_reason(str_day):
    # 实时行情涨停信息
    real_time_zt_df = get_real_time_zt_info()
    # 昨日涨停列表
    last_trade_zt = zt_common_service_api.get_last_trade_day_zt(str_day)

    try:
        # 东方财富涨停列表
        em_now_zt_pool = stock_zt_pool_api.stock_em_zt_pool_df(date_handle_util.no_slash_date(str_day))
    except BaseException as e:
        em_now_zt_pool = pd.DataFrame()
        logger.error("获取东方财富涨停列表异常:{}", e)

    if data_frame_util.is_not_empty(em_now_zt_pool):
        real_time_zt_df_wei_bi_100 = real_time_zt_df.loc[real_time_zt_df['symbol'].isin(em_now_zt_pool['symbol'])]
        real_time_zt_df_high_chg = real_time_zt_df.loc[~(real_time_zt_df['symbol'].isin(em_now_zt_pool['symbol']))]

        em_now_zt_pool = em_now_zt_pool[['symbol',
                                         'connected_boards_numbers',
                                         'statistics',
                                         'closure_funds',
                                         'first_closure_time',
                                         'last_closure_time',
                                         'frying_plates_numbers']]

        em_now_zt_pool = em_now_zt_pool.set_index(['symbol'], drop=True)
        real_time_zt_df_wei_bi_100 = real_time_zt_df_wei_bi_100.set_index(['symbol'], drop=False)
        real_time_zt_df_wei_bi_100 = pd.merge(real_time_zt_df_wei_bi_100, em_now_zt_pool, how='outer',
                                              left_index=True, right_index=True)

        now_continue_zt = last_trade_zt.loc[
            last_trade_zt['symbol'].isin(list(real_time_zt_df_wei_bi_100['symbol']))]

    else:
        real_time_zt_df_wei_bi_100 = real_time_zt_df.loc[real_time_zt_df['wei_bi'] == 100]

        real_time_zt_df_wei_bi_100['connected_boards_numbers'] = 1
        real_time_zt_df_wei_bi_100['statistics'] = '1/1'
        real_time_zt_df_wei_bi_100['closure_funds'] = real_time_zt_df_wei_bi_100['now_price'] * \
                                                      real_time_zt_df_wei_bi_100['buy_1_num'] * 100
        real_time_zt_df_wei_bi_100['first_closure_time'] = '153000'
        real_time_zt_df_wei_bi_100['last_closure_time'] = '153000'
        real_time_zt_df_wei_bi_100['frying_plates_numbers'] = 0
        now_continue_zt = last_trade_zt.loc[
            last_trade_zt['symbol'].isin(list(real_time_zt_df_wei_bi_100['symbol']))]

        if data_frame_util.is_not_empty(now_continue_zt):
            now_continue_zt = now_continue_zt[['symbol', 'connected_boards_numbers', 'statistics']]

            connected_boards_map = now_continue_zt.set_index('symbol')['connected_boards_numbers'].to_dict()

            # 将映射的值加到原DataFrame上
            real_time_zt_df_wei_bi_100['connected_boards_numbers'] = real_time_zt_df_wei_bi_100[
                                                                         'connected_boards_numbers'] + \
                                                                     real_time_zt_df_wei_bi_100['symbol'].map(
                                                                         connected_boards_map).fillna(0)

            real_time_zt_df_wei_bi_100 = real_time_zt_df_wei_bi_100.sort_values(by=['connected_boards_numbers'],
                                                                                ascending=False)

        real_time_zt_df_high_chg = real_time_zt_df.loc[real_time_zt_df['wei_bi'] != 100]

        # todo
    # 高涨幅处理
    now_zt_pool_df = handle_high_chg(real_time_zt_df_high_chg, last_trade_zt, real_time_zt_df_wei_bi_100)

    now_zt_pool_df = merge_zt_reason(now_zt_pool_df, str_day, last_trade_zt, now_continue_zt)

    result_first = now_zt_pool_df.loc[now_zt_pool_df['connected_boards_numbers'] == 1]
    result_connected_boards = now_zt_pool_df.loc[now_zt_pool_df['connected_boards_numbers'] > 1]
    result_connected_boards = result_connected_boards.sort_values(by=['connected_boards_numbers'], ascending=False)
    result_first = result_first.sort_values(by=['first_closure_time'], ascending=True)

    now_zt_pool_df = pd.concat([result_connected_boards,
                                result_first])
    now_zt_pool_df = now_zt_pool_df.fillna('未知数据')
    now_zt_pool_df.drop_duplicates('symbol', keep='last', inplace=True)

    return now_zt_pool_df


def handle_high_chg(real_time_zt_df_high_chg, last_trade_zt, real_time_zt_df_wei_bi_100):
    # 初始化数据
    real_time_zt_df_high_chg['closure_funds'] = 0
    real_time_zt_df_high_chg['first_closure_time'] = '153000'
    real_time_zt_df_high_chg['last_closure_time'] = '153000'
    real_time_zt_df_high_chg['frying_plates_numbers'] = 0

    real_time_zt_df_high_chg_last_trade_zt = real_time_zt_df_high_chg.loc[
        real_time_zt_df_high_chg['symbol'].isin(last_trade_zt['symbol'])]
    real_time_zt_df_high_chg_last_trade_no_zt = real_time_zt_df_high_chg.loc[
        ~(real_time_zt_df_high_chg['symbol'].isin(last_trade_zt['symbol']))]

    last_trade_zt_copy_today_high_chg = last_trade_zt.loc[
        last_trade_zt['symbol'].isin(real_time_zt_df_high_chg_last_trade_zt['symbol'])]

    last_trade_zt_copy_today_high_chg = last_trade_zt_copy_today_high_chg[
        ['symbol', 'connected_boards_numbers', 'statistics']]
    last_trade_zt_copy_today_high_chg['connected_boards_numbers'] = last_trade_zt_copy_today_high_chg[
                                                                        'connected_boards_numbers'] + 1

    last_trade_zt_copy_today_high_chg = last_trade_zt_copy_today_high_chg.set_index(['symbol'], drop=True)
    real_time_zt_df_high_chg_last_trade_zt = real_time_zt_df_high_chg_last_trade_zt.set_index(['symbol'], drop=False)
    real_time_zt_df_high_chg_last_trade_zt = pd.merge(real_time_zt_df_high_chg_last_trade_zt,
                                                      last_trade_zt_copy_today_high_chg, how='outer',
                                                      left_index=True, right_index=True)

    real_time_zt_df_high_chg_last_trade_no_zt['connected_boards_numbers'] = 1
    real_time_zt_df_high_chg_last_trade_no_zt['statistics'] = '1/1'
    real_time_zt_df_high_chg_last_trade_zt['statistics'] = real_time_zt_df_high_chg_last_trade_zt['statistics'].apply(
        add_one_to_each_side)
    now_zt_pool_df = pd.concat([real_time_zt_df_wei_bi_100,
                                real_time_zt_df_high_chg_last_trade_zt,
                                real_time_zt_df_high_chg_last_trade_no_zt])

    return now_zt_pool_df


def merge_zt_reason(now_zt_pool_df, str_day, last_trade_zt, now_continue_zt):
    try:
        zt_reason_df = get_ths_stock_zt_reason_with_cache(str_day)
    except BaseException as e:
        zt_reason_df = None
        logger.error("获取涨停原因异常:{}", e)

    last_trade_zt_copy = last_trade_zt.copy()

    if "zt_reason" not in last_trade_zt.columns:
        last_trade_zt_copy['zt_reason'] = '暂无'

    if 'main_line' not in last_trade_zt.columns:
        last_trade_zt['main_line'] = ''

    if 'sub_main_line' not in last_trade_zt.columns:
        last_trade_zt['sub_main_line'] = ''

    last_trade_zt_copy = last_trade_zt_copy[['symbol', 'zt_reason', 'sub_main_line', 'main_line']]

    if data_frame_util.is_empty(zt_reason_df):
        now_zt_pool_df['zt_reason'] = '暂无'

        last_trade_zt_copy = last_trade_zt_copy.set_index(['symbol'], drop=True)
        now_zt_pool_df = now_zt_pool_df.set_index(['symbol'], drop=False)
        now_zt_pool_df = pd.merge(now_zt_pool_df, last_trade_zt_copy, how='outer',
                                  left_index=True, right_index=True)
        now_zt_pool_df.dropna(subset=['symbol'], inplace=True)
        return now_zt_pool_df

    zt_reason_df_copy = zt_reason_df.copy()
    zt_reason_df_copy = zt_reason_df_copy[['symbol', 'zt_reason']]
    zt_reason_df_copy.symbol = zt_reason_df_copy.symbol.astype(str)
    zt_reason_df_copy = zt_reason_df_copy.set_index(['symbol'], drop=True)
    now_zt_pool_df = now_zt_pool_df.set_index(['symbol'], drop=False)

    if data_frame_util.is_not_empty(now_continue_zt):
        now_continue_zt = now_continue_zt[['symbol', 'main_line', 'sub_main_line']]

        # 创建一个 symbol 到 main_line 的映射
        main_line_mapping = now_continue_zt.set_index('symbol')['main_line'].to_dict()

        # 使用 map 更新 main_line 列
        now_zt_pool_df['main_line'] = now_zt_pool_df['symbol'].map(main_line_mapping).fillna("")

        # 创建一个 symbol 到 main_line 的映射
        sub_main_line_mapping = now_continue_zt.set_index('symbol')['sub_main_line'].to_dict()

        # 使用 map 更新 sub_main_line 列
        now_zt_pool_df['sub_main_line'] = now_zt_pool_df['symbol'].map(sub_main_line_mapping).fillna("")

    result_zt_df = pd.merge(now_zt_pool_df, zt_reason_df_copy, how='outer',
                            left_index=True, right_index=True)

    # 找出 'symbol' 列中为 NaN 值的数据
    zt_reason_na = result_zt_df[result_zt_df['zt_reason'].isna()]
    zt_reason_not_na = result_zt_df[result_zt_df['zt_reason'].notna()]

    last_trade_zt_copy = last_trade_zt_copy.set_index(['symbol'], drop=True)
    del zt_reason_na['zt_reason']
    zt_reason_na = zt_reason_na.set_index(['symbol'], drop=False)
    del last_trade_zt_copy['main_line']
    del last_trade_zt_copy['sub_main_line']

    zt_reason_na = pd.merge(zt_reason_na, last_trade_zt_copy, how='outer',
                            left_index=True, right_index=True)

    zt_reason_na['zt_reason'] = zt_reason_na['zt_reason'].fillna('0')
    # 删除昨日涨停 今日未涨停的
    zt_reason_na.dropna(subset=['symbol'], inplace=True)
    result = pd.concat([zt_reason_na,
                        zt_reason_not_na])
    result.dropna(subset=['symbol'], inplace=True)
    result.drop_duplicates('symbol', keep='last', inplace=True)
    result['zt_reason'] = result['zt_reason'].replace({0: '0',
                                                       '': '0'})

    return result


# 定义一个函数来处理字符串 涨停统计加1
def add_one_to_each_side(s):
    left, right = s.split('/')
    new_left = str(int(left) + 1)
    new_right = str(int(right) + 1)
    return f"{new_left}/{new_right}"


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
    str_day_test = '2025-10-28'
    # 同花顺涨停
    ths_zt_pool_df = get_now_zt_pool_with_reason(str_day_test)
    # 东财涨停池
    em_now_zt_pool_test = stock_zt_pool_api.stock_em_zt_pool_df(date_handle_util.no_slash_date(str_day_test))

    miss_zt_df = em_now_zt_pool_test.loc[~(em_now_zt_pool_test['symbol'].isin(ths_zt_pool_df['symbol']))]
    pass
