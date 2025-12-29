import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.api.ths.zt.ths_stock_zt_pool_api as ths_stock_zt_pool_api

mongodb_util = MongodbUtil('27017')
import mns_common.utils.data_frame_util as data_frame_util
import time
from loguru import logger
import pandas as pd
from datetime import datetime


# 添加主线和涨停分析临时数据
def merge_main_line_info(str_day, data_df):
    # 保证数据完整性
    if 'main_line' not in data_df.columns:
        data_df['main_line'] = ''
    else:
        data_df.fillna({'main_line': ''}, inplace=True)

    if 'sub_main_line' not in data_df.columns:
        data_df['sub_main_line'] = ''
    else:
        data_df.fillna({'sub_main_line': ''}, inplace=True)

    if 'zt_analysis' not in data_df.columns:
        data_df['zt_analysis'] = ''

    else:
        data_df.fillna({'zt_analysis': ''}, inplace=True)

    if 'zt_reason' not in data_df.columns:
        data_df['zt_reason'] = ''
    else:
        data_df.fillna({'zt_reason': ''}, inplace=True)

    if 'is_leader' not in data_df.columns:
        data_df['is_leader'] = 0
    else:
        data_df.fillna({'is_leader': 0}, inplace=True)

    if 'main_line_position' not in data_df.columns:
        data_df['main_line_position'] = ''
    else:
        data_df.fillna({'main_line_position': ''}, inplace=True)

    if 'main_line_choose_source' not in data_df.columns:
        data_df['main_line_choose_source'] = 'now_zt'
    else:
        data_df.fillna({'main_line_choose_source': 'now_zt'}, inplace=True)

    if 'main_line_grade' not in data_df.columns:
        data_df['main_line_grade'] = 1
    else:
        data_df.fillna({'main_line_grade': 1}, inplace=True)

    query_zt_now = {'symbol': {"$in": list(data_df['symbol'])}, 'str_day': str_day}
    # merge 主线 涨停详情
    main_line_detail_df = mongodb_util.find_query_data(db_name_constant.MAIN_LINE_DETAIL, query_zt_now)
    if data_frame_util.is_not_empty(main_line_detail_df):
        symbol_mapping_zt_reason_now = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['zt_reason']))

        symbol_mapping_zt_analysis_now = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['zt_analysis']))

        symbol_mapping_main_line_now = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['main_line']))

        symbol_mapping_sub_main_line_now = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['sub_main_line']))

        symbol_mapping_is_leader = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['is_leader']))

        symbol_mapping_main_line_position = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['main_line_position']))

        symbol_mapping_main_line_choose_source = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['main_line_choose_source']))

        symbol_mapping_main_line_grade = dict(
            zip(main_line_detail_df['symbol'], main_line_detail_df['main_line_grade']))

        data_df['main_line_grade'] = data_df['symbol'].map(
            symbol_mapping_main_line_grade).fillna(
            data_df['main_line_grade'])

        data_df['main_line'] = data_df['symbol'].map(
            symbol_mapping_main_line_now).fillna(
            data_df['main_line'])

        data_df['sub_main_line'] = data_df['symbol'].map(
            symbol_mapping_sub_main_line_now).fillna(
            data_df['sub_main_line'])
        data_df['zt_reason'] = data_df['symbol'].map(
            symbol_mapping_zt_reason_now).fillna(
            data_df['zt_reason'])
        data_df['zt_analysis'] = data_df['symbol'].map(
            symbol_mapping_zt_analysis_now).fillna(
            data_df['zt_analysis'])

        data_df['is_leader'] = data_df['symbol'].map(
            symbol_mapping_is_leader).fillna(
            data_df['is_leader'])

        data_df['main_line_position'] = data_df['symbol'].map(
            symbol_mapping_main_line_position).fillna(
            data_df['main_line_position'])

        data_df['main_line_choose_source'] = data_df['symbol'].map(
            symbol_mapping_main_line_choose_source).fillna(
            data_df['main_line_choose_source'])

    return data_df


# merge涨停分析 原因
def merge_zt_reason_info(str_day, data_df):
    if 'zt_analysis' not in data_df.columns:
        data_df['zt_analysis'] = ''

    else:
        data_df.fillna({'zt_analysis': ''}, inplace=True)

    if 'zt_reason' not in data_df.columns:
        data_df['zt_reason'] = ''
    else:
        data_df.fillna({'zt_reason': ''}, inplace=True)

    query_zt_now = {'symbol': {"$in": list(data_df['symbol'])}, 'str_day': str_day}
    # merge 主线 涨停详情
    zt_reason_analysis_df = mongodb_util.find_query_data(db_name_constant.ZT_REASON_ANALYSIS, query_zt_now)
    if data_frame_util.is_not_empty(zt_reason_analysis_df):
        symbol_mapping_zt_reason_now = dict(
            zip(zt_reason_analysis_df['symbol'], zt_reason_analysis_df['zt_reason']))

        symbol_mapping_zt_analysis_now = dict(
            zip(zt_reason_analysis_df['symbol'], zt_reason_analysis_df['zt_analysis']))

        data_df['zt_reason'] = data_df['symbol'].map(
            symbol_mapping_zt_reason_now).fillna(
            data_df['zt_reason'])
        data_df['zt_analysis'] = data_df['symbol'].map(
            symbol_mapping_zt_analysis_now).fillna(
            data_df['zt_analysis'])

    return data_df


def update_zt_reason_analysis(symbol, str_day, name, need_update):
    try:
        key_id = symbol + "_" + str_day
        query_zt = {"_id": key_id}

        # 已经存在的数据
        zt_reason_analysis_exists_df = mongodb_util.find_query_data(db_name_constant.ZT_REASON_ANALYSIS,
                                                                    query_zt)

        if data_frame_util.is_not_empty(zt_reason_analysis_exists_df):
            zt_analysis = list(zt_reason_analysis_exists_df['zt_analysis'])[0]
            zt_reason = list(zt_reason_analysis_exists_df['zt_reason'])[0]
            # 需要更新数据
            if data_frame_util.is_string_empty(zt_analysis) or data_frame_util.is_string_empty(
                    zt_reason) or need_update:
                try:
                    zt_result_dict = ths_stock_zt_pool_api.zt_analyse_reason(symbol)
                    zt_analysis = zt_result_dict['zt_analyse_detail']
                    zt_reason = zt_result_dict['zt_reason']
                    time.sleep(1)
                except BaseException as e:
                    time.sleep(1)
                    zt_analysis = ''
                    zt_reason = ''

                zt_reason_analysis_exists_df['zt_analysis'] = zt_analysis
                zt_reason_analysis_exists_df['zt_reason'] = zt_reason
                mongodb_util.save_mongo(zt_reason_analysis_exists_df, db_name_constant.ZT_REASON_ANALYSIS)
        else:
            # 不存在临时主线数据
            try:
                zt_result_dict = ths_stock_zt_pool_api.zt_analyse_reason(symbol)
                zt_analysis = zt_result_dict['zt_analyse_detail']
                zt_reason = zt_result_dict['zt_reason']
                time.sleep(1)
            except BaseException as e:
                time.sleep(1)
                zt_analysis = ''
                zt_reason = ''
            now_date = datetime.now()
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
            reason_dict = {'_id': key_id,
                           'symbol': symbol,
                           'name': name,
                           'zt_analysis': zt_analysis,
                           'zt_reason': zt_reason,
                           'str_day': str_day,
                           'update_time': str_now_date,
                           }
            reason_df = pd.DataFrame(reason_dict, index=[1])
            mongodb_util.save_mongo(reason_df, db_name_constant.ZT_REASON_ANALYSIS)
    except BaseException as e:
        logger.error("添加涨停原因详情异常:{},{}", e, name)


def update_symbol_list_zt_reason_analysis(data_df, need_update):
    for stock_one in data_df.itertuples():
        str_day = stock_one.str_day
        symbol = stock_one.symbol
        name = stock_one.name
        update_zt_reason_analysis(symbol, str_day, name, need_update)
        time.sleep(1)


if __name__ == '__main__':
    update_zt_reason_analysis('600362', '2025-12-26', '江西铜业', True)
