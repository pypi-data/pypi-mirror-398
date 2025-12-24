import sys
import os

import requests
import pandas as pd
from loguru import logger
import json


def all_stock_ticker_data_new(fields, fs) -> pd.DataFrame:
    url = "https://13.push2.eastmoney.com/api/qt/clist/get"
    # url = "https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery112303212778189608789_1645434416300&fid=f62&po=1&pz=6000&pn=1&np=1&fltt=2&invt=2&ut=b2884a393a59ad64002292a3e90d46a5&fs=m%3A0%2Bt%3A6%2Bf%3A!2%2Cm%3A0%2Bt%3A13%2Bf%3A!2%2Cm%3A0%2Bt%3A80%2Bf%3A!2%2Cm%3A1%2Bt%3A2%2Bf%3A!2%2Cm%3A1%2Bt%3A23%2Bf%3A!2%2Cm%3A0%2Bt%3A7%2Bf%3A!2%2Cm%3A1%2Bt%3A3%2Bf%3A!2&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124%2Cf1%2Cf13"
    params = {
        "cb": "jQuery1124046660442520420653_1660036672477",
        "pn": "1",
        "pz": "10000",
        "po": "1",
        "np": "3",
        "ut": " bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f3",
        "fs": fs,
        "fields": fields,
        "_": 1660036672518
    }
    try:
        r = requests.get(url, params)
        data_text = r.text
        begin_index = data_text.index('[')
        end_index = data_text.index(']')
        data_json = data_text[begin_index:end_index + 1]
        data_json = json.loads(data_json)
        if data_json is None:
            return pd.DataFrame()
        return pd.DataFrame(data_json)
    except Exception as e:
        logger.error("获取股票列表,实时行情异常:{}", e)
        return None


# f212 卖1
# f211 买1
# f31 买1价格
# "f32" : 卖1价格


# 获取所有股票实时行情数据    f33,委比
def get_real_time_quotes_all_stocks():
    stock_ticker_data = all_stock_ticker_data_new(
        "f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,f18,f20,f21,f26,"
        "f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212",
        "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048")

    temp_df = stock_ticker_data.rename(columns={
        "f2": "now_price",
        "f3": "chg",
        "f5": "volume",
        "f6": "amount",
        "f8": "exchange",
        "f10": "quantity_ratio",
        "f22": "up_speed",
        "f11": "up_speed_05",
        "f12": "symbol",
        "f14": "name",
        "f15": "high",
        "f16": "low",
        "f17": "open",
        "f18": "yesterday_price",
        "f20": "total_mv",
        "f21": "flow_mv",
        "f26": "list_date",
        "f33": "wei_bi",
        "f34": "outer_disk",
        "f35": "inner_disk",
        "f62": "today_main_net_inflow",
        "f66": "super_large_order_net_inflow",
        "f69": "super_large_order_net_inflow_ratio",
        "f72": "large_order_net_inflow",
        # "f78": "medium_order_net_inflow",
        # "f84": "small_order_net_inflow",
        "f100": "industry",
        # "f103": "concept",
        "f184": "today_main_net_inflow_ratio",
        "f352": "average_price",
        "f211": "buy_1_num",
        "f212": "sell_1_num"
    })
    temp_df.loc[temp_df['buy_1_num'] == '-', 'buy_1_num'] = 0
    temp_df.loc[temp_df['sell_1_num'] == '-', 'sell_1_num'] = 0
    temp_df.loc[temp_df['up_speed_05'] == '-', 'up_speed_05'] = 0
    temp_df.loc[temp_df['up_speed'] == '-', 'up_speed'] = 0
    temp_df.loc[temp_df['average_price'] == '-', 'average_price'] = 0
    temp_df.loc[temp_df['wei_bi'] == '-', 'wei_bi'] = 0
    temp_df.loc[temp_df['yesterday_price'] == '-', 'yesterday_price'] = 0
    temp_df.loc[temp_df['now_price'] == '-', 'now_price'] = 0
    temp_df.loc[temp_df['chg'] == '-', 'chg'] = 0
    temp_df.loc[temp_df['volume'] == '-', 'volume'] = 0
    temp_df.loc[temp_df['amount'] == '-', 'amount'] = 0
    temp_df.loc[temp_df['exchange'] == '-', 'exchange'] = 0
    temp_df.loc[temp_df['quantity_ratio'] == '-', 'quantity_ratio'] = 0
    temp_df.loc[temp_df['high'] == '-', 'high'] = 0
    temp_df.loc[temp_df['low'] == '-', 'low'] = 0
    temp_df.loc[temp_df['open'] == '-', 'open'] = 0
    temp_df.loc[temp_df['total_mv'] == '-', 'total_mv'] = 0
    temp_df.loc[temp_df['flow_mv'] == '-', 'flow_mv'] = 0
    temp_df.loc[temp_df['inner_disk'] == '-', 'inner_disk'] = 0
    temp_df.loc[temp_df['outer_disk'] == '-', 'outer_disk'] = 0
    temp_df.loc[temp_df['today_main_net_inflow_ratio'] == '-', 'today_main_net_inflow_ratio'] = 0
    temp_df.loc[temp_df['today_main_net_inflow'] == '-', 'today_main_net_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow'] == '-', 'super_large_order_net_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow_ratio'] == '-', 'super_large_order_net_inflow_ratio'] = 0
    temp_df.loc[temp_df['large_order_net_inflow'] == '-', 'large_order_net_inflow'] = 0
    # temp_df.loc[temp_df['medium_order_net_inflow'] == '-', 'medium_order_net_inflow'] = 0
    # temp_df.loc[temp_df['small_order_net_inflow'] == '-', 'small_order_net_inflow'] = 0

    temp_df["list_date"] = pd.to_numeric(temp_df["list_date"], errors="coerce")
    temp_df["wei_bi"] = pd.to_numeric(temp_df["wei_bi"], errors="coerce")
    temp_df["average_price"] = pd.to_numeric(temp_df["average_price"], errors="coerce")
    temp_df["yesterday_price"] = pd.to_numeric(temp_df["yesterday_price"], errors="coerce")
    temp_df["now_price"] = pd.to_numeric(temp_df["now_price"], errors="coerce")
    temp_df["chg"] = pd.to_numeric(temp_df["chg"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    temp_df["exchange"] = pd.to_numeric(temp_df["exchange"], errors="coerce")
    temp_df["quantity_ratio"] = pd.to_numeric(temp_df["quantity_ratio"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["total_mv"] = pd.to_numeric(temp_df["total_mv"], errors="coerce")
    temp_df["flow_mv"] = pd.to_numeric(temp_df["flow_mv"], errors="coerce")
    temp_df["outer_disk"] = pd.to_numeric(temp_df["outer_disk"], errors="coerce")
    temp_df["inner_disk"] = pd.to_numeric(temp_df["inner_disk"], errors="coerce")
    temp_df["today_main_net_inflow"] = pd.to_numeric(temp_df["today_main_net_inflow"], errors="coerce")
    temp_df["super_large_order_net_inflow"] = pd.to_numeric(temp_df["super_large_order_net_inflow"],
                                                            errors="coerce")
    temp_df["super_large_order_net_inflow_ratio"] = pd.to_numeric(temp_df["super_large_order_net_inflow_ratio"],
                                                                  errors="coerce")
    temp_df["large_order_net_inflow"] = pd.to_numeric(temp_df["large_order_net_inflow"],
                                                      errors="coerce")
    # temp_df["medium_order_net_inflow"] = pd.to_numeric(temp_df["medium_order_net_inflow"],
    #                                                    errors="coerce")
    # temp_df["small_order_net_inflow"] = pd.to_numeric(temp_df["small_order_net_inflow"], errors="coerce")

    # 大单比例
    temp_df['large_order_net_inflow_ratio'] = round((temp_df['large_order_net_inflow'] / temp_df['amount']) * 100, 2)


    return temp_df


if __name__ == '__main__':
    df = get_real_time_quotes_all_stocks()
    df = df.loc[df['wei_bi'] == 100]
    print(df)
