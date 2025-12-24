import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import requests

# symbol 代码
# 北交所:0  深圳：0 上海：1
"""
获取分钟数据
"""


def get_minute_data(symbol, start_date, end_date, period,
                    adjust) -> pd.DataFrame:
    """
    东方财富网-行情首页-沪深京 A 股-每日分时行情
    https://quote.eastmoney.com/concept/sh603777.html?from=classic
    :param symbol: 股票代码
    :type symbol: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :param period: choice of {'1', '5', '15', '30', '60'}
    :type period: str
    :param adjust: choice of {'', 'qfq', 'hfq'}
    :type adjust: str
    :return: 每日分时行情
    :rtype: pandas.DataFrame
    """
    adjust_map = {
        "": "0",
        "qfq": "1",
        "hfq": "2",
    }
    if period == "1":
        url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "ndays": "5",
            "iscr": "0",
            "secid": symbol,
            "_": "1623766962675",
        }
        r = requests.get(url, timeout=15, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["trends"]]
        )
        temp_df.columns = [
            "time",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "ava_price",
        ]
        temp_df.index = pd.to_datetime(temp_df["time"])
        temp_df = temp_df[start_date:end_date]
        temp_df.reset_index(drop=True, inplace=True)
        temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
        temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
        temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
        temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
        temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
        temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
        temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
        temp_df["ava_price"] = pd.to_numeric(temp_df["ava_price"], errors="coerce")
        temp_df["time"] = pd.to_datetime(temp_df["time"]).astype(str)
        return temp_df
    else:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": period,
            "fqt": adjust_map[adjust],
            "secid": symbol,
            "beg": "0",
            "end": "20500000",
            "_": "1630930917857",
        }
        r = requests.get(url, timeout=15, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(
            [item.split(",") for item in data_json["data"]["klines"]]
        )
        temp_df.columns = [
            "time",
            "open",
            "close",
            "high",
            "low",
            "amount",
            "volume",
            "pct_chg",
            "chg",
            "change",
            "exchange",
        ]
        temp_df.index = pd.to_datetime(temp_df["time"])
        temp_df = temp_df[start_date:end_date]
        temp_df.reset_index(drop=True, inplace=True)
        temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
        temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
        temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
        temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
        temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
        temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
        temp_df["pct_chg"] = pd.to_numeric(temp_df["pct_chg"], errors="coerce")
        temp_df["chg"] = pd.to_numeric(temp_df["chg"], errors="coerce")
        temp_df["change"] = pd.to_numeric(temp_df["change"], errors="coerce")
        temp_df["exchange"] = pd.to_numeric(temp_df["exchange"], errors="coerce")
        temp_df["time"] = pd.to_datetime(temp_df["time"]).astype(str)
        temp_df = temp_df[
            [
                "time",
                "volume",
                "close",
                "high",
                "low",
                "chg",
                "change",
                "amount",
                "volume",
                "pct_chg",
                "exchange",
            ]
        ]
        return temp_df


if __name__ == '__main__':
    test_df = get_minute_data('0.899050', start_date="2025-03-03 09:30:00",
                              end_date="2025-03-07 15:00:00", period="1", adjust="")
    print(test_df)
