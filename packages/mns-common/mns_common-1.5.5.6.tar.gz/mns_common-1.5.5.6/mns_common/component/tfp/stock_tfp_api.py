import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.utils.date_handle_util as date_handle_util
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')

"""
Date: 2024/4/29 15:00
Desc: 东方财富网-数据中心-特色数据-停复牌信息
https://data.eastmoney.com/tfpxx/
"""

import pandas as pd
import requests


def stock_tfp_em(date: str = "20240426") -> pd.DataFrame:
    """
    东方财富网-数据中心-特色数据-停复牌信息
    https://data.eastmoney.com/tfpxx/
    :param date: specific date as "2020-03-19"
    :type date: str
    :return: 停复牌信息表
    :rtype: pandas.DataFrame
    """
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "sortColumns": "SUSPEND_START_DATE",
        "sortTypes": "-1",
        "pageSize": "500",
        "pageNumber": "1",
        "reportName": "RPT_CUSTOM_SUSPEND_DATA_INTERFACE",
        "columns": "ALL",
        "source": "WEB",
        "client": "WEB",
        "filter": f"""(MARKET="全部")(DATETIME='{"-".join([date[:4], date[4:6], date[6:]])}')""",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    total_page = data_json["result"]["pages"]
    big_df = pd.DataFrame()
    for page in range(1, total_page + 1):
        params.update({"pageNumber": page})
        r = requests.get(url, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(data_json["result"]["data"])
        big_df = pd.concat(objs=[big_df, temp_df], ignore_index=True)

    big_df.reset_index(inplace=True)

    big_df["SUSPEND_START_TIME"] = pd.to_datetime(big_df["SUSPEND_START_TIME"], errors="coerce").dt.date
    big_df["SUSPEND_END_TIME"] = pd.to_datetime(
        big_df["SUSPEND_END_TIME"], errors="coerce"
    ).dt.date

    big_df["SUSPEND_START_DATE"] = pd.to_datetime(
        big_df["SUSPEND_START_DATE"], errors="coerce"
    ).dt.date
    big_df["PREDICT_RESUME_DATE"] = pd.to_datetime(
        big_df["PREDICT_RESUME_DATE"], errors="coerce"
    ).dt.date

    big_df = big_df[['index', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'SUSPEND_START_TIME',
                     'SUSPEND_END_TIME', 'SUSPEND_EXPIRE', 'SUSPEND_REASON', 'TRADE_MARKET',
                     'SUSPEND_START_DATE',
                     'PREDICT_RESUME_DATE'
                     ]]

    return big_df


def get_stock_tfp_by_day(str_day):
    stock_tfp_em_df = stock_tfp_em(date_handle_util.no_slash_date(str_day))
    stock_tfp_em_df = stock_tfp_em_df.rename(
        columns={'index': 'index',
                 'SECURITY_CODE': 'symbol',
                 'SECURITY_NAME_ABBR': 'name',
                 'SUSPEND_START_TIME': 'sus_begin_time',
                 'SUSPEND_END_TIME': 'sus_end_time',

                 'SUSPEND_START_DATE': 'sus_begin_date',
                 'PREDICT_RESUME_DATE': 'resume_time',

                 'SUSPEND_EXPIRE': 'sus_period',
                 'SUSPEND_REASON': 'sus_reason',
                 'TRADE_MARKET': 'market',

                 })
    return stock_tfp_em_df


# 获取停牌股票列表
@lru_cache(maxsize=None)
def get_stock_tfp_symbol_list_by_day(str_day):
    try:
        stock_tfp_em_df = get_stock_tfp_by_day(str_day)
        if data_frame_util.is_not_empty(stock_tfp_em_df):
            return list(stock_tfp_em_df['symbol'])
        else:
            return ['666666']

    except BaseException as e:
        logger.error("获取停牌信息异常:{}", e)
        return ['666666']


@lru_cache(maxsize=None)
def get_stock_tfp_symbol_from_db(str_day):
    try:
        query = {'str_day': str_day}
        stock_tfp_df = mongodb_util.find_query_data(db_name_constant.STOCK_TFP_INFO, query)
        if data_frame_util.is_not_empty(stock_tfp_df):
            return list(stock_tfp_df['symbol'])
        else:
            return ['666666']
    except BaseException as e:
        logger.error("获取停牌信息异常:{}", e)
        return ['666666']


if __name__ == '__main__':
    get_stock_tfp_symbol_list_by_day('2025-06-21')
