import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)


mongodb_util = MongodbUtil('27017')


@lru_cache(maxsize=None)
def get_company_info_by_field(query_key, query_field_key):
    query = eval(query_key)
    query_field = eval(query_field_key)
    return mongodb_util.find_query_data_choose_field('company_info', query, query_field)


# 获取退市股票代码
@lru_cache(maxsize=None)
def get_de_list_company():
    return list(mongodb_util.find_all_data(db_name_constant.DE_LIST_STOCK)['symbol'])


# 获取公司详情
@lru_cache(maxsize=None)
def get_company_info_info():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"_id": 1,
                                                      "industry": 1,
                                                      "company_type": 1,
                                                      "ths_concept_name": 1,
                                                      "ths_concept_code": 1,
                                                      "ths_concept_sync_day": 1,
                                                      'sub_stock': 1,
                                                      "first_sw_industry": 1,
                                                      "second_sw_industry": 1,
                                                      "third_sw_industry": 1,
                                                      "mv_circulation_ratio": 1,
                                                      "diff_days": 1,
                                                      "list_date": 1,
                                                      'em_industry': 1,
                                                      'ths_concept_list_info': 1,
                                                      'ths_concept_name_list_str': 1,
                                                      "kpl_plate_name": 1,
                                                      "kpl_plate_list_info": 1,
                                                      'operate_profit': 1,
                                                      'total_operate_income': 1,
                                                      "flow_mv_sp": 1,
                                                      "total_mv_sp": 1
                                                      })


def clear_company_info_cache():
    get_company_info_info.cache_clear()


# 使用同花顺行业分类
def amend_ths_industry(real_time_quotes_now_init):
    real_time_quotes_now = real_time_quotes_now_init.copy()
    query_field = {"_id": 1, "industry": 1, "company_type": 1,
                   "ths_concept_name": 1, "ths_concept_code": 1,
                   "ths_concept_sync_day": 1, 'sub_stock': 1,
                   "first_sw_industry": 1, "second_sw_industry": 1,
                   "third_sw_industry": 1, "mv_circulation_ratio": 1,
                   "list_date": 1, 'ths_concept_list_info': 1, 'ths_concept_name_list_str': 1,
                   "ths_concept_list": 1,
                   "diff_days": 1, 'em_industry': 1,
                   "kpl_plate_name": 1, "kpl_plate_list_info": 1,
                   'operate_profit': 1,
                   'total_operate_income': 1,
                   "name": 1,
                   'pb': 1, 'pe_ttm': 1, 'ROE': 1
                   }
    query_field_key = str(query_field)
    query = {}
    query_key = str(query)

    industry_group_df = get_company_info_by_field(query_key, query_field_key)
    if 'list_date' in real_time_quotes_now.columns:
        del real_time_quotes_now['list_date']
    if 'name' in real_time_quotes_now.columns:
        del real_time_quotes_now['name']
    if 'industry' in real_time_quotes_now.columns:
        del real_time_quotes_now['industry']

    industry_group_df = industry_group_df.set_index(['_id'], drop=True)
    real_time_quotes_now = real_time_quotes_now.set_index(['symbol'], drop=False)
    real_time_quotes_now = pd.merge(real_time_quotes_now, industry_group_df, how='outer',
                                    left_index=True, right_index=True)
    real_time_quotes_now.dropna(subset=['symbol'], axis=0, inplace=True)

    symbol_list = list(real_time_quotes_now['symbol'])

    na_industry_data = real_time_quotes_now_init.loc[
        ~(real_time_quotes_now_init['symbol'].isin(symbol_list))]
    # 修复空值
    na_industry_data = na_industry_data.loc[na_industry_data['amount'] != 0]

    real_time_quotes_now_result = pd.concat([real_time_quotes_now, na_industry_data], axis=0)
    real_time_quotes_now.fillna({'connected_boards_numbers': 1}, inplace=True)

    # 处理na值
    real_time_quotes_now_result.fillna(0, inplace=True)
    return real_time_quotes_now_result


# 获取公司详情
@lru_cache(maxsize=None)
def get_company_all_info_info():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"ths_concept_list_info": 0,
                                                      "kpl_plate_list_info": 0,
                                                      })


def clear_company_all_info_cache():
    get_company_all_info_info.cache_clear()
