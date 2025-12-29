import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 7
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import requests


def stock_bid_ask_em(symbol: str = "000001") -> pd.DataFrame:
    """
    东方财富-行情报价
    https://quote.eastmoney.com/sz000001.html
    :param symbol: 股票代码
    :type symbol: str
    :return: 行情报价
    :rtype: pandas.DataFrame
    """
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f120,f121,f122,f174,f175,f59,f163,f43,f57,f58,f169,f170,f46,f44,f51,"
                  "f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,"
                  "f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,"
                  "f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,"
                  "f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,"
                  "f268,f255,f256,f257,f258,f127,f199,f128,f198,f259,f260,f261,f171,f277,f278,"
                  "f279,f288,f152,f250,f251,f252,f253,f254,f269,f270,f271,f272,f273,f274,f275,"
                  "f276,f265,f266,f289,f290,f286,f285,f292,f293,f294,f295",

        "secid": symbol,
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    tick_dict = {
        "now_price": data_json["data"]["f43"],
        "dt_price": data_json["data"]["f52"],
        "zt_price": data_json["data"]["f51"],
        "wei_bi": data_json["data"]["f191"],
        "sell_5": data_json["data"]["f31"],
        "sell_5_vol": data_json["data"]["f32"] * 100,
        "sell_4": data_json["data"]["f33"],
        "sell_4_vol": data_json["data"]["f34"] * 100,
        "sell_3": data_json["data"]["f35"],
        "sell_3_vol": data_json["data"]["f36"] * 100,
        "sell_2": data_json["data"]["f37"],
        "sell_2_vol": data_json["data"]["f38"] * 100,
        "sell_1": data_json["data"]["f39"],
        "sell_1_vol": data_json["data"]["f40"] * 100,
        "buy_1": data_json["data"]["f19"],
        "buy_1_vol": data_json["data"]["f20"] * 100,
        "buy_2": data_json["data"]["f17"],
        "buy_2_vol": data_json["data"]["f18"] * 100,
        "buy_3": data_json["data"]["f15"],
        "buy_3_vol": data_json["data"]["f16"] * 100,
        "buy_4": data_json["data"]["f13"],
        "buy_4_vol": data_json["data"]["f14"] * 100,
        "buy_5": data_json["data"]["f11"],
        "buy_5_vol": data_json["data"]["f12"] * 100,
    }
    temp_df = pd.DataFrame(tick_dict, index=[1])
    temp_df.reset_index(inplace=True)
    temp_df.loc[temp_df['wei_bi'] == '-', 'wei_bi'] = 0
    temp_df.loc[temp_df['sell_5_vol'] == '-', 'sell_5_vol'] = 0
    temp_df.loc[temp_df['sell_5'] == '-', 'sell_5'] = 0
    temp_df.loc[temp_df['sell_4_vol'] == '-', 'sell_4_vol'] = 0
    temp_df.loc[temp_df['sell_4'] == '-', 'sell_4'] = 0
    temp_df.loc[temp_df['sell_3_vol'] == '-', 'sell_3_vol'] = 0
    temp_df.loc[temp_df['sell_3'] == '-', 'sell_3'] = 0
    temp_df.loc[temp_df['sell_2_vol'] == '-', 'sell_2_vol'] = 0
    temp_df.loc[temp_df['sell_2'] == '-', 'sell_2'] = 0
    temp_df.loc[temp_df['sell_1_vol'] == '-', 'sell_1_vol'] = 0
    temp_df.loc[temp_df['sell_1'] == '-', 'sell_1'] = 0
    temp_df.loc[temp_df['buy_1_vol'] == '-', 'buy_1_vol'] = 0
    temp_df.loc[temp_df['buy_1'] == '-', 'buy_1'] = 0
    temp_df.loc[temp_df['buy_2_vol'] == '-', 'buy_2_vol'] = 0
    temp_df.loc[temp_df['buy_2'] == '-', 'buy_2'] = 0
    temp_df.loc[temp_df['buy_3_vol'] == '-', 'buy_3_vol'] = 0
    temp_df.loc[temp_df['buy_3'] == '-', 'buy_3'] = 0
    temp_df.loc[temp_df['buy_4_vol'] == '-', 'buy_4_vol'] = 0
    temp_df.loc[temp_df['buy_4'] == '-', 'buy_4'] = 0
    temp_df.loc[temp_df['buy_5_vol'] == '-', 'buy_5_vol'] = 0
    temp_df.loc[temp_df['buy_5'] == '-', 'buy_5'] = 0
    temp_df['symbol'] = symbol
    return temp_df


if __name__ == '__main__':
    while True:
        df = stock_bid_ask_em('0.000001')
        print(df)
