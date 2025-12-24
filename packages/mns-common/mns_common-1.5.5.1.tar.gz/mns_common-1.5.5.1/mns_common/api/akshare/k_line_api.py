import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import pandas as pd
import mns_common.component.common_service_fun_api as common_service_fun_api
from datetime import datetime
import numpy as np


def stock_zh_a_hist(
        symbol: str = "0.000001",
        period: str = 'daily',
        start_date: str = "19700101",
        end_date: str = "22220101",
        adjust: str = "",
        proxies: str = None
) -> pd.DataFrame:
    """
    东方财富网-行情首页-沪深京 A 股-每日行情
    http://quote.eastmoney.com/concept/sh603777.html?from=classic
    :param symbol: 股票代码
    :type symbol: str
    :param period: choice of {'daily', 'weekly', 'monthly'}
    :type period: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :param adjust: choice of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
    :type adjust: str
    :param proxies: 代理ip
    :type proxies: str

    :return: 每日行情
    :rtype: pandas.DataFrame
    """
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {'daily': '101', 'weekly': '102', 'monthly': '103'}
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    now_date = datetime.now()
    now_time = int(now_date.timestamp() * 1000)
    now_time = str(now_time)

    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "secid": symbol,
        "beg": "0",
        "end": "20500000",
        "_": now_time,
    }

    if proxies is None:
        r = requests.get(url, params=params)
    else:
        r = requests.get(url, params=params, proxies=proxies)

    data_json = r.json()
    temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
    temp_df.columns = [
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "amount",
        "pct_chg",
        "chg",
        "change",
        "exchange",
    ]

    temp_df['date'] = temp_df['date'].apply(
        lambda x: x.replace("-", ""))
    temp_df.index = temp_df["date"]
    temp_df = temp_df[start_date:end_date]
    temp_df.reset_index(inplace=True, drop=True)
    temp_df['open'] = pd.to_numeric(temp_df['open'])
    temp_df['close'] = pd.to_numeric(temp_df['close'])
    temp_df['high'] = pd.to_numeric(temp_df['high'])
    temp_df['low'] = pd.to_numeric(temp_df['low'])
    temp_df['volume'] = pd.to_numeric(temp_df['volume'])
    temp_df['amount'] = pd.to_numeric(temp_df['amount'])
    temp_df['pct_chg'] = pd.to_numeric(temp_df['pct_chg'])
    temp_df['chg'] = pd.to_numeric(temp_df['chg'])
    temp_df['change'] = pd.to_numeric(temp_df['change'])
    temp_df['exchange'] = pd.to_numeric(temp_df['exchange'])

    temp_df['symbol'] = symbol
    temp_df['_id'] = temp_df['symbol'] + '-' + temp_df['date']
    temp_df['last_price'] = round(((temp_df['close']) / (1 + temp_df['chg'] / 100)), 2)
    temp_df['max_chg'] = round(
        ((temp_df['high'] - temp_df['last_price']) / temp_df['last_price']) * 100, 2)
    temp_df['amount_level'] = round((temp_df['amount'] / common_service_fun_api.HUNDRED_MILLION), 2)
    temp_df['flow_mv'] = round(temp_df['amount'] * 100 / temp_df['exchange'], 2)
    temp_df['flow_mv_sp'] = round(temp_df['flow_mv'] / common_service_fun_api.HUNDRED_MILLION, 2)

    temp_df.replace([np.inf, -np.inf], 0, inplace=True)
    temp_df.fillna(0, inplace=True)
    return temp_df


import mns_common.component.proxies.proxy_common_api as proxy_common_api

if __name__ == '__main__':
    while True:
        proxy_ip = proxy_common_api.get_proxy_ip(5)
        df = stock_zh_a_hist("0.000001",
                             'daily',
                             "19700101",
                             "22220101",
                             "",
                             proxy_ip)
        print(df)
