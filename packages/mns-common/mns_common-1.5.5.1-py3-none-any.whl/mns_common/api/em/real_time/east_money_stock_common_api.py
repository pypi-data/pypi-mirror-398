import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import requests
from loguru import logger
import datetime

fs = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"
fields = ("f2,f3,f5,f6,f8,"
          "f9,f10,f22,f12,f13,"
          "f14,f15,f16,f17,f18,"
          "f20,f21,f23,f26,f33,"
          "f34,f35,f37,f38,f39,"
          "f62,f64,f65,f67,f68,"
          "f66,f69,f70,f71,f72,"
          "f76,f77,f78,f82,f83,"
          "f84,f102,f184,f100,f103,"
          "f352,f191,f193,f24,f25")


# 获取所有股票实时行情数据    f33,委比
def rename_real_time_quotes_df(temp_df):
    temp_df = temp_df.rename(columns={
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
    if data_frame_util.is_empty(temp_df):
        return pd.DataFrame()
    else:
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
        temp_df['large_order_net_inflow_ratio'] = round((temp_df['large_order_net_inflow'] / temp_df['amount']) * 100,
                                                        2)

        # 外盘是内盘倍数
        temp_df['disk_ratio'] = round((temp_df['outer_disk'] - temp_df['inner_disk']) / temp_df['inner_disk'], 2)
        # 只有外盘没有内盘
        temp_df.loc[temp_df["inner_disk"] == 0, ['disk_ratio']] = 1688
        temp_df = temp_df.sort_values(by=['chg'], ascending=False)
        return temp_df


def get_stocks_num(pn, proxies, page_number, time_out):
    """
    获取单页股票数据
    """
    # 获取当前日期和时间
    current_time = datetime.datetime.now()

    # 将当前时间转换为时间戳（以毫秒为单位）
    current_timestamp_ms = int(current_time.timestamp() * 1000)

    url = "https://13.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "cb": "jQuery1124046660442520420653_" + str(current_timestamp_ms),
        "pn": str(pn),
        "pz": str(page_number),  # 每页最大200条
        "po": "1",
        "np": "3",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f3",
        "fs": fs,
        "fields": fields,
        "_": current_timestamp_ms
    }
    try:
        if proxies is None:
            r = requests.get(url, params, timeout=time_out)
        else:
            r = requests.get(url, params, proxies=proxies, timeout=time_out)
        data_text = r.text

        begin_index_total = data_text.index('"total":')
        end_index_total = data_text.index('"diff"')
        return int(data_text[begin_index_total + 8:end_index_total - 1])

    except Exception as e:
        logger.error("获取股票数量异常:{}", str(e))
        return 0


import mns_common.component.proxies.proxy_common_api as proxy_common_api

if __name__ == '__main__':
    proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
    proxies = {"https": proxy_ip}
    get_stocks_num(1, proxies, 100, 30)
