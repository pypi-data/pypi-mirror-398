import sys
import os
import time

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import datetime
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')
fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,"
          "f18,f20,f21,f26,f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212"),
fs = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"

# 最大返回条数
max_number = 5800
# 最小返回条数
min_number = 5600
# 分页条数
PAGE_SIZE = 100


def get_stock_page_data(pn, proxies, page_size, time_out):
    """
    获取单页股票数据
    """
    # 获取当前日期和时间
    current_time = datetime.datetime.now()

    # 将当前时间转换为时间戳（以毫秒为单位）
    current_timestamp_ms = int(current_time.timestamp() * 1000)

    url = "https://33.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "cb": "jQuery1124046660442520420653_" + str(current_timestamp_ms),
        "pn": str(pn),
        "pz": str(page_size),  # 每页最大200条
        "po": "0",
        "np": "3",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f12",
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


        begin_index = data_text.index('[')
        end_index = data_text.index(']')
        data_json = data_text[begin_index:end_index + 1]
        data_json = json.loads(data_json)
        if data_json is None:
            return pd.DataFrame()
        else:
            result_df = pd.DataFrame(data_json)
            result_df['page_number'] = pn
            return result_df
    except Exception as e:
        # logger.error("获取第{}页股票列表异常:{}", pn, str(e))
        return pd.DataFrame()


def all_stock_ticker_data_new(proxies, time_out) -> pd.DataFrame:
    """
    使用多线程获取所有股票数据
    """

    per_page = PAGE_SIZE
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整

    # 创建线程池
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交任务，获取每页数据
        futures = [executor.submit(get_stock_page_data, pn, proxies, PAGE_SIZE, time_out)
                   for pn in range(1, total_pages + 1)]

        # 收集结果
        results = []
        for future in futures:
            result = future.result()
            if not result.empty:
                results.append(result)

    # 合并所有页面的数据
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()


def get_real_time_quotes_all_stocks(proxies, time_out):
    page_df = all_stock_ticker_data_new(proxies, time_out)
    page_df = rename_real_time_quotes_df(page_df)
    page_df.drop_duplicates('symbol', keep='last', inplace=True)
    return page_df


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


# 北向/南向资金状况 北向已经停止
def get_sum_north_south_net_buy_amt():
    # 设置请求头部信息
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # 设置请求URL
    url = 'http://push2.eastmoney.com/api/qt/kamt/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70&ut=b2884a393a59ad640022ce1e1e78431c&deviceid=0&cb=jsonp_1622790712837&_=1622790712926'

    # 发送HTTP请求
    response = requests.get(url, headers=headers, params={"type": "json"})

    # 解析JSON数据
    data = json.loads(response.text.lstrip('jsonp_1622790712837(').rstrip(');'))

    # 处理数据

    # 单位(万元)
    # dayNetAmtIn  资金净流入
    # dayAmtRemain  当日资金余额
    # dayAmtThreshold  当日资金限额
    # monthNetAmtIn   当月净流入
    # yearNetAmtIn    年度净流入
    # allNetAmtIn     总净流入
    # buyAmt          当日买入金额
    # sellAmt         当日卖出金额
    # buySellAmt      当日买入卖出总金额
    # netBuyAmt        成交净买额

    # Hongkong to Shanghai
    hk2sh = data['data']['hk2sh']
    hk2sh_df = pd.DataFrame(hk2sh, index=[0])
    # Hongkong to ShenZhen
    hk2sz = data['data']['hk2sz']
    hk2sz_df = pd.DataFrame(hk2sz, index=[0])

    # Shanghai to Hongkong
    sh2hk = data['data']['sh2hk']
    sh2hk_df = pd.DataFrame(sh2hk, index=[0])

    # ShenZhen  to Hongkong
    sz2hk = data['data']['sz2hk']
    sz2hk_df = pd.DataFrame(sz2hk, index=[0])
    # 北向总额
    sum_north_netBuyAmt = hk2sh_df['netBuyAmt'] + hk2sz_df['netBuyAmt']

    sum_south_netBuyAmt = sh2hk_df['netBuyAmt'] + sz2hk_df['netBuyAmt']

    df = pd.DataFrame([[
        list(hk2sh_df['netBuyAmt'])[0],
        list(hk2sz_df['netBuyAmt'])[0],
        list(sum_north_netBuyAmt)[0],
        list(sh2hk_df['netBuyAmt'])[0],
        list(sz2hk_df['netBuyAmt'])[0],
        list(sum_south_netBuyAmt)[0]]],
        columns=['sh_netBuyAmt', 'sz_netBuyAmt', 'sum_north_netBuyAmt',
                 'sh_hk_netBuyAmt', 'sz_hk_netBuyAmt', 'sum_south_netBuyAmt'])

    # 打印结果
    return df


import mns_common.component.proxies.proxy_common_api as proxy_common_api

# 示例调用
if __name__ == "__main__":

    while True:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        proxy = {"https": proxy_ip}
        logger.info(proxy_ip)
        df = all_stock_ticker_data_new(proxy, 3)
        logger.info("数据条数,{}", df.shape[0])
        time.sleep(1)

    else:
        time.sleep(1)
        logger.error("ip为空")
