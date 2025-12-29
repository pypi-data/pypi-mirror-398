import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 21
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger
import csv
import requests
import pandas as pd
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from functools import lru_cache
import mns_common.utils.data_frame_util as data_frame_util


@lru_cache()
def get_us_stock_info():
    # 东财美股列表
    em_us_stock_info_df = em_stock_info_api.get_us_stock_info()
    em_us_stock_info_df['symbol'] = em_us_stock_info_df['symbol'].str.replace('_', '-')
    em_us_stock_info_df = em_us_stock_info_df.loc[em_us_stock_info_df['total_mv'] != 0]

    if data_frame_util.is_not_empty(em_us_stock_info_df):
        em_us_stock_info_df.fillna({'list_date': 10000101}, inplace=True)
        em_us_stock_info_df = em_us_stock_info_df[['symbol', 'name', 'list_date']]

    # alpha 股票名单
    alpha_us_stock_info = get_us_alpha_stock_list()
    alpha_us_stock_info = alpha_us_stock_info.loc[alpha_us_stock_info['assetType'] == 'Stock']
    if data_frame_util.is_not_empty(alpha_us_stock_info):
        alpha_us_stock_info.fillna({'list_date': '1000-01-01'}, inplace=True)
        alpha_us_stock_info = alpha_us_stock_info[['symbol', 'name', 'list_date']]

        alpha_us_stock_info['list_date'] = alpha_us_stock_info['list_date'].astype(str).str.replace('-', '').astype(int)

    us_stock_result_df = pd.concat([alpha_us_stock_info, em_us_stock_info_df])
    us_stock_result_df.drop_duplicates(subset=['symbol'], inplace=True)

    return us_stock_result_df


@lru_cache()
def get_us_etf_info():
    us_etf_info_df = em_stock_info_api.get_us_etf_info()
    if data_frame_util.is_not_empty(us_etf_info_df):
        us_etf_info_df.fillna({'list_date': 10000101}, inplace=True)
        us_etf_info_df = us_etf_info_df[['symbol', 'name', 'list_date']]

    # alpha ETF名单
    alpha_us_etf_info = get_us_alpha_stock_list()
    alpha_us_etf_info = alpha_us_etf_info.loc[alpha_us_etf_info['assetType'] == 'ETF']
    if data_frame_util.is_not_empty(alpha_us_etf_info):
        alpha_us_etf_info.fillna({'list_date': '1000-01-01'}, inplace=True)
        alpha_us_etf_info = alpha_us_etf_info[['symbol', 'name', 'list_date']]

        alpha_us_etf_info['list_date'] = alpha_us_etf_info['list_date'].astype(str).str.replace('-', '').astype(int)
    us_etf_result_df = pd.concat([us_etf_info_df, alpha_us_etf_info])
    us_etf_result_df.drop_duplicates(subset=['symbol'], inplace=True)

    return us_etf_result_df


# 退市 https://www.alphavantage.co/query?function=LISTING_STATUS&date=2012-07-10&state=delisted&apikey=QODR3TBYB2U4M9YR
@lru_cache()
def get_us_alpha_stock_list():
    try:
        # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
        CSV_URL = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo'
        with requests.Session() as s:
            download = s.get(CSV_URL)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)
            # 提取列名（第1行）
            columns = my_list[0]
            # 提取数据（第2行及以后）
            values = my_list[1:]

            # 转换为 DataFrame
            df = pd.DataFrame(values, columns=columns)
            df = df.rename(columns={'ipoDate': 'list_date'})
            if data_frame_util.is_not_empty(df):
                df.to_csv(r'D:\mns\mns-common\mns_common\component\us\listing_status.csv', index=False, encoding='gbk')
            return df
    except BaseException as e:
        logger.error("下载出现异常:{},", e)
        df = pd.read_csv(r'D:\mns\mns-common\mns_common\component\us\listing_status.csv', encoding='utf-8')
        df = df.rename(columns={'ipoDate': 'list_date'})
        return df


def get_us_alpha_stock_de_list():
    try:
        # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
        CSV_URL = 'https://www.alphavantage.co/query?function=LISTING_STATUS&date=2025-08-02&state=delisted&apikey=QODR3TBYB2U4M9YR'
        with requests.Session() as s:
            download = s.get(CSV_URL)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)
            # 提取列名（第1行）
            columns = my_list[0]
            # 提取数据（第2行及以后）
            values = my_list[1:]

            # 转换为 DataFrame
            df = pd.DataFrame(values, columns=columns)
            df = df.rename(columns={'ipoDate': 'list_date'})
            if data_frame_util.is_not_empty(df):
                df.to_csv(r'D:\mns\mns-common\mns_common\component\us\de_list_status.csv', index=False, encoding='gbk')
            return df
    except BaseException as e:
        logger.error("下载出现异常:{},", e)
        df = pd.read_csv(r'D:\mns\mns-common\mns_common\component\us\de_list_status.csv', encoding='utf-8')
        df = df.rename(columns={'ipoDate': 'list_date'})
        return df


if __name__ == '__main__':
    # get_us_alpha_stock_de_list()
    df_test = get_us_stock_info()
    df_test.drop_duplicates(subset=['symbol'], inplace=True)
    print(df_test)
    get_us_alpha_stock_de_list()
