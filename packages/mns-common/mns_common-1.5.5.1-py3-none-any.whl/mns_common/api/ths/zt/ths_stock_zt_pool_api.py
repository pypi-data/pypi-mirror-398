import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import re
from loguru import logger
import mns_common.component.company.company_common_service_api as company_common_service_api
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
from datetime import datetime
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api

mongodb_util = MongodbUtil('27017')


def get_zt_reason(str_day):
    if data_frame_util.is_string_not_empty(str_day):
        key_word = str_day + '涨停'
    else:
        now_date = datetime.now()
        hour = now_date.hour
        minute = now_date.minute
        str_day = now_date.strftime('%Y-%m-%d')
        if (hour < 9) or (hour == 9 and minute < 25):
            str_day = trade_date_common_service_api.get_last_trade_day(str_day)
            key_word = str_day + '涨停'
        else:
            key_word = '涨停'
    zt_df = ths_wen_cai_api.wen_cai_api(key_word, 'stock')
    if data_frame_util.is_empty(zt_df):
        return None
    zt_df.fillna('', inplace=True)
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
        "code": "symbol",
        "最新价": "now_price",
        "最新涨跌幅": "chg",

    })
    zt_df['symbol'] = zt_df['symbol'].astype(str)
    if 'statistics_detail' in zt_df.columns:
        zt_df['statistics'] = zt_df['statistics_detail'].apply(convert_statistics)
    if 'code' in zt_df.columns:
        del zt_df['code']
    if 'flow_mv' in zt_df.columns:
        del zt_df['flow_mv']
    zt_df['zt_flag'] = True
    zt_df['str_day'] = str_day
    zt_df = zt_df.fillna('')
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


def get_real_time_zt_info():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    zt_df = get_zt_reason(str_day)
    if data_frame_util.is_empty(zt_df):
        return None
    real_time_df = em_real_time_quotes_api.get_real_time_quotes_now(None, None)

    zt_df = merge_high_chg(real_time_df, zt_df)

    symbol_list = list(zt_df['symbol'])
    zt_ream_time_data = real_time_df.loc[real_time_df['symbol'].isin(symbol_list)]
    zt_ream_time_data = zt_ream_time_data[[
        'symbol',
        'amount',
        'quantity_ratio',
        'high',
        'low',
        'open',
        'list_date',
        'exchange',
        'wei_bi',
        'flow_mv',
        'total_mv',
        'buy_1_num'
    ]]

    company_df = company_common_service_api.get_company_info_industry()
    company_df = company_df[[
        '_id',
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
        "ths_concept_list_info",
        "kpl_plate_name",
        "kpl_plate_list_info",
        "diff_days"
    ]]
    company_df = company_df.loc[company_df['_id'].isin(symbol_list)]

    company_df = company_df.set_index(['_id'], drop=True)
    zt_df = zt_df.set_index(['symbol'], drop=True)
    zt_ream_time_data = zt_ream_time_data.set_index(['symbol'], drop=False)

    zt_df = pd.merge(zt_df, company_df, how='outer',
                     left_index=True, right_index=True)
    zt_df = pd.merge(zt_df, zt_ream_time_data, how='outer',
                     left_index=True, right_index=True)

    zt_df = common_service_fun_api.classify_symbol(zt_df)
    zt_df = common_service_fun_api.total_mv_classification(zt_df)

    zt_df = common_service_fun_api.symbol_amount_simple(zt_df)
    zt_df = common_service_fun_api.exclude_new_stock(zt_df)
    zt_df.fillna(0, inplace=True)
    zt_df['chg'] = zt_df['chg'].astype(float)
    zt_df['chg'] = round(
        zt_df['chg'], 2)
    return zt_df


def merge_high_chg(real_time_df, zt_df):
    real_time_df_high_chg = real_time_df.loc[real_time_df['chg'] >= 9.5]
    if data_frame_util.is_empty(real_time_df_high_chg) and data_frame_util.is_empty(zt_df):
        return None

    if data_frame_util.is_not_empty(zt_df) and data_frame_util.is_empty(real_time_df_high_chg):
        return zt_df

    if data_frame_util.is_empty(zt_df) and data_frame_util.is_not_empty(real_time_df_high_chg):
        real_time_df_high_chg = real_time_df_high_chg[['symbol',
                                                       'name',
                                                       'now_price',
                                                       "flow_mv"]]
        return real_time_df_high_chg

    real_time_df_high_chg = real_time_df_high_chg.loc[~(real_time_df_high_chg['symbol'].isin(list(zt_df['symbol'])))]
    if data_frame_util.is_empty(real_time_df_high_chg):
        return zt_df

    real_time_df_high_chg = real_time_df_high_chg[['symbol',
                                                   'name',
                                                   'chg',
                                                   'now_price']]

    real_time_df_high_chg['connected_boards_numbers'] = 1

    real_time_df_high_chg['statistics_detail'] = '1/1'

    real_time_df_high_chg['zt_flag'] = False

    zt_df = pd.concat([zt_df, real_time_df_high_chg], ignore_index=True)
    zt_df = zt_df.fillna('0')
    return zt_df


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
            zt_stock_one_df = zt_pool_df.loc[zt_pool_df['symbol'] == zt_stock_one.symbol]
            zt_stock_one_df = zt_stock_one_df[
                ['symbol',
                 'name',
                 'now_price',
                 'first_closure_time',
                 'last_closure_time',
                 'connected_boards_numbers',
                 'zt_reason',
                 "closure_volume",
                 "closure_funds",
                 "closure_funds_per_amount",
                 "closure_funds_per_flow_mv",
                 "frying_plates_numbers"
                 ]]
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


def zt_analyse_reason(symbol):
    try:
        key = symbol + '涨停分析'
        zt_dict = ths_wen_cai_api.wen_cai_api(key, 'stock')
        zt_analyse_detail = zt_dict['涨停揭秘'][0]['content']['value']
        zt_reason = zt_dict['涨停揭秘'][0]['title']['value']

        result_dict = {
            'zt_analyse_detail': zt_analyse_detail,
            'zt_reason': zt_reason
        }

        return result_dict
    except BaseException as e:
        logger.error("获取涨停分享异常b:{},{}", symbol, str(e))
        return ''


if __name__ == '__main__':
    zt_analyse_reason('003027')
    # get_real_time_zt_info()
