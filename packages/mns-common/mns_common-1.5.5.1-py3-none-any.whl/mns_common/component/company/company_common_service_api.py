import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')


@lru_cache(maxsize=None)
def get_company_info_name():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"_id": 1, 'name': 1,
                                                      "industry": 1, "company_type": 1,
                                                      "ths_concept_name": 1, "ths_concept_code": 1,
                                                      "ths_concept_sync_day": 1, 'sub_stock': 1,
                                                      "first_sw_industry": 1, "second_sw_industry": 1,
                                                      "third_sw_industry": 1, "mv_circulation_ratio": 1,
                                                      "diff_days": 1,
                                                      'em_industry': 1,
                                                      'ths_concept_list_info': 1,
                                                      'ths_concept_name_list_str': 1,
                                                      "kpl_plate_name": 1,
                                                      "kpl_plate_list_info": 1,
                                                      'operate_profit': 1,
                                                      'total_operate_income': 1
                                                      })


@lru_cache(maxsize=None)
def get_company_info_industry():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"_id": 1, "industry": 1, "company_type": 1,
                                                      "ths_concept_name": 1, "ths_concept_code": 1,
                                                      "ths_concept_sync_day": 1, 'sub_stock': 1,
                                                      "first_sw_industry": 1, "second_sw_industry": 1,
                                                      "third_sw_industry": 1, "mv_circulation_ratio": 1,
                                                      "diff_days": 1,
                                                      'em_industry': 1,
                                                      'ths_concept_list_info': 1,
                                                      'ths_concept_name_list_str': 1,
                                                      "kpl_plate_name": 1,
                                                      "kpl_plate_list_info": 1,
                                                      'operate_profit': 1,
                                                      'total_operate_income': 1
                                                      })


def get_company_info_by_field_no_cache(fields):
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     fields)


@lru_cache(maxsize=None)
def get_company_info_industry_list_date():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"_id": 1, "industry": 1, "company_type": 1,
                                                      "ths_concept_name": 1, "ths_concept_code": 1,
                                                      "ths_concept_sync_day": 1, 'sub_stock': 1,
                                                      "first_sw_industry": 1, "second_sw_industry": 1,
                                                      "third_sw_industry": 1, "mv_circulation_ratio": 1,
                                                      "list_date": 1, 'ths_concept_list_info': 1,
                                                      'ths_concept_name_list_str': 1,
                                                      "diff_days": 1, 'em_industry': 1,
                                                      "kpl_plate_name": 1, "kpl_plate_list_info": 1,
                                                      'operate_profit': 1,
                                                      'total_operate_income': 1
                                                      })


@lru_cache(maxsize=None)
def get_company_info_industry_mv():
    return mongodb_util.find_query_data_choose_field('company_info', {},
                                                     {"_id": 1, "industry": 1,
                                                      "ths_concept_name": 1, "ths_concept_code": 1,
                                                      "ths_concept_sync_day": 1, 'sub_stock': 1,
                                                      "first_sw_industry": 1, "second_sw_industry": 1,
                                                      "third_sw_industry": 1, "mv_circulation_ratio": 1,
                                                      "diff_days": 1, 'em_industry': 1, 'ths_concept_list_info': 1,
                                                      'ths_concept_name_list_str': 1,
                                                      "flow_mv_sp": 1, "total_mv_sp": 1,
                                                      "kpl_plate_name": 1, "kpl_plate_list_info": 1,
                                                      'operate_profit': 1,
                                                      'total_operate_income': 1
                                                      })


def fix_symbol_industry(realtime_quotes_now_list):
    company_info_industry = get_company_info_industry()
    realtime_quotes_now_list.drop(columns=['industry'], inplace=True)
    realtime_quotes_now_list = realtime_quotes_now_list.set_index(['symbol'], drop=False)

    company_info_industry = company_info_industry.set_index(['_id'], drop=True)

    realtime_quotes_now_list = pd.merge(realtime_quotes_now_list, company_info_industry, how='outer',
                                        left_index=True, right_index=True)

    realtime_quotes_now_list = realtime_quotes_now_list.dropna(inplace=False)
    return realtime_quotes_now_list


# 清除缓存
def company_info_industry_cache_clear():
    get_company_info_industry.cache_clear()
    get_company_info_industry_list_date.cache_clear()


def merge_company_info(df, str_day):
    if data_frame_util.is_empty(df):
        return df
    industry_group_df = get_company_info_industry_list_date()
    industry_group_df = industry_group_df.set_index(['_id'], drop=True)

    df.drop(columns=['industry'], inplace=True)
    df = df.set_index(['symbol'], drop=False)
    df = pd.merge(df, industry_group_df, how='outer',
                  left_index=True, right_index=True)
    df['symbol'] = df.index
    df = df.loc[df['amount'] > 0]
    df = common_service_fun_api.classify_symbol(df)
    df['_id'] = df['symbol'] + "_" + str_day
    df['str_day'] = str_day
    df = common_service_fun_api.total_mv_classification(df)
    return df


# 修改行业信息
def amendment_industry(real_time_quotes_now_init):
    real_time_quotes_now = real_time_quotes_now_init.copy()
    if 'list_date' in real_time_quotes_now.columns:
        industry_group_df = get_company_info_industry()
    else:
        industry_group_df = get_company_info_industry_list_date()
    industry_group_df = industry_group_df.set_index(['_id'], drop=True)
    real_time_quotes_now['em_industry_temp'] = real_time_quotes_now['industry']
    real_time_quotes_now = real_time_quotes_now.loc[~(real_time_quotes_now['em_industry_temp'] == '-')]
    real_time_quotes_now.drop(columns=['industry'], inplace=True)
    real_time_quotes_now = real_time_quotes_now.set_index(['symbol'], drop=False)
    real_time_quotes_now = pd.merge(real_time_quotes_now, industry_group_df, how='outer',
                                    left_index=True, right_index=True)

    real_time_quotes_now.loc[
        real_time_quotes_now["mv_circulation_ratio"].isnull(), ['mv_circulation_ratio']] \
        = 1
    real_time_quotes_now.loc[
        real_time_quotes_now["industry"].isnull(), ['industry']] \
        = real_time_quotes_now["em_industry_temp"]
    real_time_quotes_now.dropna(subset=['symbol'], inplace=True)
    real_time_quotes_now.drop(columns=['em_industry_temp'], inplace=True)

    return real_time_quotes_now


# 允许存在空值的合并
def amendment_industry_exist_na(real_time_quotes_now, symbol_list):
    industry_group_df = get_company_info_industry()
    industry_group_df = industry_group_df.loc[industry_group_df['_id'].isin(symbol_list)]
    industry_group_df = industry_group_df.set_index(['_id'], drop=True)
    real_time_quotes_now.drop(columns=['industry'], inplace=True)
    real_time_quotes_now = real_time_quotes_now.set_index(['symbol'], drop=False)
    real_time_quotes_now = pd.merge(real_time_quotes_now, industry_group_df, how='outer',
                                    left_index=True, right_index=True)
    return real_time_quotes_now


# 获取退市股票代码
@lru_cache(maxsize=None)
def get_de_list_company():
    return list(mongodb_util.find_all_data(db_name_constant.DE_LIST_STOCK)['symbol'])
