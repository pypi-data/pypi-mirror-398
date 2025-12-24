import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import requests


def stock_k_line_hist(
        symbol: str = "000001",
        period: str = "daily",
        start_date: str = "19700101",
        end_date: str = "20500101",
        adjust: str = "",
        timeout: float = None,
        proxies: str = None
) -> pd.DataFrame:
    """
    东方财富网-行情首页-沪深京 A 股-每日行情
    https://quote.eastmoney.com/concept/sh603777.html?from=classic
    :param symbol: 股票代码
    :type symbol: str
    :param period: choice of {'daily', 'weekly', 'monthly'}
    :type period: str
    :param start_date: 开始date
    :type start_date: str
    :param end_date: 结束date
    :type end_date: str
    :param adjust: choice of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
    :type adjust: str
    :param timeout: choice of None or a positive float number
    :type timeout: float
    :param proxies: 代理ip
    :type proxies: str

    :return: 每日行情
    :rtype: pandas.DataFrame
    """
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "secid": symbol,
        "beg": start_date,
        "end": end_date,
        "_": "1623766962675",
    }

    if proxies is None:
        r = requests.get(url, params=params, timeout=timeout)
    else:
        r = requests.get(url, params=params, proxies=proxies, timeout=timeout)

    data_json = r.json()
    if not (data_json["data"] and data_json["data"]["klines"]):
        return pd.DataFrame()
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
        "change_price",
        "exchange",
    ]
    temp_df["date"] = pd.to_datetime(temp_df["date"], errors="coerce").dt.date
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    temp_df["pct_chg"] = pd.to_numeric(temp_df["pct_chg"], errors="coerce")
    temp_df["chg"] = pd.to_numeric(temp_df["chg"], errors="coerce")
    temp_df["change_price"] = pd.to_numeric(temp_df["change_price"], errors="coerce")
    temp_df["exchange"] = pd.to_numeric(temp_df["exchange"], errors="coerce")
    temp_df = temp_df[
        [
            "date",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "pct_chg",
            "chg",
            "change_price",
            "exchange",
        ]
    ]
    return temp_df


if __name__ == '__main__':
    stock_k_line_hist(
        "1.513180",
        "daily",
        "19700101",
        "20500101",
        "",
        None,
        None)
