import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api

mongodb_util = MongodbUtil('27017')
import pandas as pd
from io import StringIO
from functools import lru_cache


# 同花顺概念操作类


# 获取所有同花顺概念代码
@lru_cache(maxsize=None)
def get_all_ths_concept():
    query = {}
    ths_concept_list = mongodb_util.find_query_data('ths_concept_list', query)
    return ths_concept_list


# 获取有效同花顺概念代码
@lru_cache(maxsize=None)
def get_all_ths_effective_concept():
    query = {}
    ths_concept_list = mongodb_util.find_query_data('ths_concept_list', query)
    # 选择有效的概念
    ths_concept_list_effective = ths_concept_list.loc[ths_concept_list['valid']]
    return ths_concept_list_effective


# 获取单个股票所有有效概念数据
@lru_cache(maxsize=None)
def get_one_symbol_effective_ths_concept(symbol):
    ths_concept_list = get_all_ths_concept()
    # 选择有效的概念
    ths_concept_list_effective = ths_concept_list.loc[ths_concept_list['valid']]
    effective_ths_concept_ids = list(ths_concept_list_effective['symbol'])
    query = {'symbol': symbol, '$and': [{'concept_code': {'$in': effective_ths_concept_ids}},
                                        {'concept_name': {"$ne": None}}]}
    return mongodb_util.find_query_data('ths_stock_concept_detail', query)


# 获取单个股票所有有效概念数据
@lru_cache(maxsize=None)
def get_one_symbol_all_ths_concept(symbol):
    query = {'symbol': symbol}
    return mongodb_util.find_query_data('ths_stock_concept_detail', query)


# 设置同花顺最新概念
def set_ths_concept(symbol, df):
    ths_stock_concept_detail = get_one_symbol_all_ths_concept(symbol)
    df['ths_concept_name'] = "未有"
    df['ths_concept_code'] = 0
    df['ths_concept_sync_day'] = "1989-07-29"
    # 有效数量
    df['ths_concept_count'] = 0

    df['ths_concept_list_info'] = "-"

    df['ths_concept_name_list_str'] = "-"

    df['ths_concept_most_relative_name'] = "未有"

    df['ths_concept_most_relative_code'] = 0

    df['ths_concept_list'] = [[] for _ in range(len(df))]

    if ths_stock_concept_detail.shape[0] == 0:
        return df

    ths_stock_concept_detail = ths_stock_concept_detail.sort_values(by=['concept_code'], ascending=False)
    ths_stock_concept_detail.dropna(subset=['concept_name'], axis=0, inplace=True)
    ths_stock_concept_detail.dropna(subset=['concept_code'], axis=0, inplace=True)

    if data_frame_util.is_not_empty(ths_stock_concept_detail):
        ths_stock_concept_detail['concept_name_str'] = ths_stock_concept_detail['concept_name']
        df_unique = ths_stock_concept_detail['concept_name_str'].drop_duplicates()
        concept_name_str = ','.join(df_unique)

        ths_stock_concept_detail = ths_stock_concept_detail[[
            'concept_code',
            'concept_name',
            'grade',
            'remark',
            'str_day',
            'str_now_time',
            'concept_create_day']]
        # 去除空格
        ths_stock_concept_detail['concept_name'] = ths_stock_concept_detail['concept_name'].str.replace(' ', '')

        df.loc[:, 'ths_concept_list_info'] = ths_stock_concept_detail.to_string(index=False)
        df.loc[:, 'ths_concept_name_list_str'] = concept_name_str
        ths_concept_list_record = ths_stock_concept_detail.to_dict(orient='records')
        df.at[df.index[0], 'ths_concept_list'] = ths_concept_list_record

    ths_effective_concept_list = get_all_ths_effective_concept()
    ths_effective_concept_code_list = list(ths_effective_concept_list['symbol'])

    ths_stock_concept_detail_effective = ths_stock_concept_detail.loc[
        ths_stock_concept_detail['concept_code'].isin(ths_effective_concept_code_list)]

    ths_stock_concept_detail_effective = ths_stock_concept_detail_effective.sort_values(by=['concept_code'],
                                                                                        ascending=False)
    ths_concept_count = ths_stock_concept_detail_effective.shape[0]

    df.loc[:, 'ths_concept_count'] = ths_concept_count

    if data_frame_util.is_empty(ths_stock_concept_detail_effective):
        return df
    # 最新概念设置
    ths_stock_concept_detail_last_one = ths_stock_concept_detail_effective.iloc[0:1]
    if ths_stock_concept_detail_last_one['concept_name'] is None:
        df['ths_concept_name'] = "未有"
    else:
        df['ths_concept_name'] = list(ths_stock_concept_detail_last_one['concept_name'])[0]
    if ths_stock_concept_detail_last_one['concept_code'] is None:
        df['concept_code'] = 0
    else:
        df['ths_concept_code'] = list(ths_stock_concept_detail_last_one['concept_code'])[0]

    df['ths_concept_sync_day'] = list(ths_stock_concept_detail_last_one['str_day'])[0]

    ths_stock_concept_detail_effective = ths_stock_concept_detail_effective.sort_values(by=['grade'],
                                                                                        ascending=False)

    # 最相关的概念
    ths_stock_concept_detail_most_relative_one = ths_stock_concept_detail_effective.iloc[0:1]

    if ths_stock_concept_detail_most_relative_one['concept_name'] is None:
        df['ths_concept_most_relative_name'] = "未有"
    else:
        df['ths_concept_most_relative_name'] = list(ths_stock_concept_detail_last_one['concept_name'])[0]
    if ths_stock_concept_detail_most_relative_one['concept_code'] is None:
        df['ths_concept_most_relative_code'] = 0
    else:
        df['ths_concept_most_relative_code'] = list(ths_stock_concept_detail_most_relative_one['concept_code'])[0]

    return df


# 设置最新ths概念
def set_last_ths_concept(symbol, stock_em_zt_pool_df_data, str_day):
    query = {'concept_name': {'$ne': ""}, 'symbol': symbol, "str_day": {"$lte": str_day}}
    ths_stock_concept_detail = mongodb_util.descend_query(query, 'ths_stock_concept_detail', 'concept_code', 1)
    stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_name']] = "未有"
    stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_code']] = 0
    stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_sync_day']] = "1989-07-29"

    if ths_stock_concept_detail.shape[0] == 0:
        return stock_em_zt_pool_df_data
    # 设置最新ths概念
    ths_effective_concept_list = get_all_ths_effective_concept()
    ths_effective_concept_code_list = list(ths_effective_concept_list['symbol'])

    ths_stock_concept_detail = ths_stock_concept_detail.loc[
        ths_stock_concept_detail['concept_code'].isin(ths_effective_concept_code_list)]

    if data_frame_util.is_empty(ths_stock_concept_detail):
        return stock_em_zt_pool_df_data
    if ths_stock_concept_detail['concept_name'] is None:
        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_name']] = "未有"
    else:
        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_name']] = \
            list(ths_stock_concept_detail['concept_name'])[0]

    if ths_stock_concept_detail['concept_code'] is None:
        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_code']] = 0
    else:
        stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_code']] = \
            list(ths_stock_concept_detail['concept_code'])[0]
    stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['symbol'] == symbol, ['ths_concept_sync_day']] = \
        list(ths_stock_concept_detail['str_day'])[0]
    return stock_em_zt_pool_df_data


# 将同花顺概念str 转换成df
def trans_ths_concept_list_info(ths_concept_list_info):
    ths_concept_list_info_df = pd.read_csv(StringIO(ths_concept_list_info), delim_whitespace=True)
    ths_concept_list_info_df.loc[:, 'str_now_time'] = ths_concept_list_info_df['concept_name'] + " " + \
                                                      ths_concept_list_info_df['str_now_time']
    ths_concept_list_info_df.loc[:, 'concept_name'] = ths_concept_list_info_df['concept_code']
    ths_concept_list_info_df.loc[:, 'concept_code'] = ths_concept_list_info_df.index
    return ths_concept_list_info_df


# 获取一个概念下所有股票组成
@lru_cache(maxsize=None)
def get_concept_by_code(concept_code):
    query = {'concept_code': concept_code}
    ths_concept_list = mongodb_util.find_query_data('ths_stock_concept_detail', query)
    if data_frame_util.is_not_empty(ths_concept_list):
        return list(ths_concept_list['symbol'])
    else:
        return []


# 更概念编码获取 该概念所有组成数据
@lru_cache(maxsize=None)
def get_concept_list_by_code(concept_code):
    query = {'concept_code': concept_code}
    return mongodb_util.find_query_data('ths_stock_concept_detail', query)


# 最近股票新添加ths概念 刚好这个模板在热炒中
def ths_recent_add_new_concept(str_day, before_num, str_now_date):
    last_trade_day = trade_date_common_service_api.get_before_trade_date(str_day, before_num)
    if str_now_date is not None:
        # 上一个交易结束时间
        last_trade_end_time = last_trade_day + ' 00:00:00'
        query = {'$and': [{"str_now_time": {"$gte": last_trade_end_time}},
                          {"str_now_time": {"$lte": str_now_date}}],
                 '$or': [{'concept_type': {"$exists": False}}, {'concept_type': 'ths'}]}
    else:
        # 上一个交易结束时间
        last_trade_end_time = last_trade_day + ' 00:00:00'
        today_trade_end_time = str_day + ' 15:00:00'
        query = {'$and': [{"str_now_time": {"$gte": last_trade_end_time}},
                          {"str_now_time": {"$lte": today_trade_end_time}}],
                 '$or': [{'concept_type': {"$exists": False}}, {'concept_type': 'ths'}]}
    recent_add_new_concept_df = mongodb_util.find_query_data('today_new_concept_list', query)
    if data_frame_util.is_empty(recent_add_new_concept_df):
        return None
    return recent_add_new_concept_df[[
        'symbol',
        'name',
        'concept_code',
        'concept_name',
        'flow_mv_sp',
        'total_mv_sp',
        'str_day',
        'str_now_time'
    ]]


def clear_ths_concept_cache():
    get_all_ths_concept.cache_clear()
    get_all_ths_effective_concept.cache_clear()
    get_one_symbol_effective_ths_concept.cache_clear()


def clear_one_concept_cache(concept_code):
    get_one_symbol_all_ths_concept.cache_clear()


def clear_effective_ths_concept_cache():
    get_all_ths_effective_concept.cache_clear()
    get_one_symbol_effective_ths_concept.cache_clear()


def get_choose_effective_ths_concept_no_cache():
    query = {'valid': True}
    ths_concept_list_effective = mongodb_util.find_query_data('ths_concept_list', query)
    return ths_concept_list_effective


if __name__ == '__main__':
    symbol_test = '300085'
    company_info_df = mongodb_util.find_query_data('company_info', {"symbol": symbol_test})
    set_ths_concept(symbol_test, company_info_df)
