import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')
from functools import lru_cache
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.utils.data_frame_util as data_frame_util


# 开盘啦概念操作类

# 获取单个股票所有概念数据
@lru_cache(maxsize=None)
def get_symbol_all_kpl_concept(symbol):
    query = {'symbol': symbol}
    return mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL, query)


# 获取单个kpl板块所有股票组成
@lru_cache(maxsize=None)
def get_one_plate_code_all_symbol(plate_code):
    query = {"plate_code": plate_code}
    return mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL, query)


# 获取所有开盘啦概念列表
@lru_cache(maxsize=None)
def get_kpl_all_concept():
    query = {}
    kpl_best_choose_index = mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX, query)
    return kpl_best_choose_index


# 获取开盘啦有效概念列表
@lru_cache(maxsize=None)
def get_valid_kpl_all_concept():
    all_kpl_concept_df = get_kpl_all_concept()

    return all_kpl_concept_df.loc[all_kpl_concept_df['valid']]


# 最近股票新添加ths概念 刚好这个模板在热炒中
def kpl_recent_add_new_concept(str_day, before_num, str_now_date):
    last_trade_day = trade_date_common_service_api.get_before_trade_date(str_day, before_num)
    if str_now_date is not None:
        # 上一个交易结束时间
        last_trade_end_time = last_trade_day + ' 15:00:00'

        query = {'$and': [{"create_time": {"$gte": last_trade_end_time}},
                          {"create_time": {"$lte": str_now_date}}],
                 'concept_type': 'kpl'}
    else:

        # 上一个交易结束时间
        last_trade_end_time = last_trade_day + ' 15:00:00'
        today_trade_begin_time = str_day + ' 15:00:00'
        query = {'$and': [{"create_time": {"$gte": last_trade_end_time}},
                          {"create_time": {"$lte": today_trade_begin_time}}],
                 'concept_type': 'kpl'}

    recent_add_new_concept_df = mongodb_util.find_query_data('today_new_concept_list', query)
    if data_frame_util.is_empty(recent_add_new_concept_df):
        return None
    return recent_add_new_concept_df[[
        'symbol',
        'name',
        'plate_code',
        'plate_name',
        'first_plate_code',
        'first_plate_name',
        'plate_name_list',
        'most_relative_name',
        'index_class',
        'sync_str_day',
        'sync_str_time'
    ]]


# 清除开盘啦概念缓存
def clear_kpl_concept_cache():
    get_kpl_all_concept.cache_clear()
    get_symbol_all_kpl_concept.cache_clear()
    get_valid_kpl_all_concept.cache_clear()


if __name__ == '__main__':
    df = get_valid_kpl_all_concept()
    df = get_valid_kpl_all_concept()
    clear_kpl_concept_cache()
    df = get_kpl_all_concept()
