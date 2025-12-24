import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from loguru import logger
import requests
import time

# 最大返回条数
max_number = 12000
# 最小返回条数
min_number = 11000
# 分页条数
page_number = 100

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f13,f22,f12,f14,f15,f16,f17,f18,f20,f21,f26,"
          "f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212")


def us_real_time_quotes_page_df(cookie, pn, proxies):
    try:
        headers = {
            'Cookie': cookie
        }

        current_timestamp = str(int(round(time.time() * 1000, 0)))

        url = "https://72.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": str(pn),
            "pz": "50000",
            "po": "1",
            "np": "2",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f12",
            "fs": "m:105,m:106,m:107",
            "fields": fields,
            "_": str(current_timestamp),
        }
        if proxies is None:
            r = requests.get(url, params=params, headers=headers)
        else:
            r = requests.get(url, params=params, headers=headers, proxies=proxies)
        data_json = r.json()
        if pn == 1:
            try:
                global max_number
                max_number = int(data_json['data']['total'])
            except Exception as e:
                logger.error(f"获取第{pn}页美股列表异常: {e}")
                return pd.DataFrame()

        if not data_json["data"]["diff"]:
            return pd.DataFrame()
        temp_df = pd.DataFrame(data_json["data"]["diff"]).T

        return temp_df
    except Exception as e:
        logger.error("获取美股实时行情异常:{}", e)
        return pd.DataFrame()


def thread_pool_executor(cookie, proxies):
    """
       使用多线程获取所有美股数据
       """
    # 计算总页数，假设总共有1000条数据，每页200条

    per_page = page_number
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整

    # 创建线程池
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务，获取每页数据
        futures = [executor.submit(us_real_time_quotes_page_df, cookie, pn, proxies)
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


def get_us_stock_real_time_quotes(cookie, proxies):
    # 获取第一页数据
    page_one_df = us_real_time_quotes_page_df(cookie, 1, proxies)
    # 数据接口正常返回5600以上的数量
    if page_one_df.shape[0] > min_number:
        page_one_df = rename_us_stock(page_one_df)
        page_one_df.drop_duplicates('symbol', keep='last', inplace=True)
        return page_one_df
    else:
        page_df = thread_pool_executor(cookie, proxies)
        page_df = rename_us_stock(page_df)
        page_df.drop_duplicates('symbol', keep='last', inplace=True)
        return page_df


def rename_us_stock(temp_df):
    temp_df = temp_df.rename(columns={

        "f12": "symbol",
        "f14": "name",
        "f3": "chg",
        "f2": "now_price",
        "f5": "volume",
        "f6": "amount",
        "f8": "exchange",
        "f10": "quantity_ratio",
        "f22": "up_speed",
        "f11": "up_speed_05",
        "f13": "simple_symbol",
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
    temp_df['large_order_net_inflow_ratio'] = round((temp_df['large_order_net_inflow'] / temp_df['amount']) * 100,
                                                    2)

    # 外盘是内盘倍数
    temp_df['disk_ratio'] = round((temp_df['outer_disk'] - temp_df['inner_disk']) / temp_df['inner_disk'], 2)
    # 只有外盘没有内盘
    temp_df.loc[temp_df["inner_disk"] == 0, ['disk_ratio']] = 1688
    temp_df['disk_diff_amount'] = round(
        (temp_df['outer_disk'] - temp_df['inner_disk']) * temp_df[
            "average_price"],
        2)
    return temp_df


if __name__ == '__main__':
    cookie_test = 'qgqp_b_id=1e0d79428176ed54bef8434efdc0e8c3; mtp=1; ct=QVRY_s8Tiag1WfK2tSW2n03qpsX-PD8aH_rIjKVooawX8K33UVnpIofK088lD1lguWlE_OEIpQwn3PJWFPhHvSvyvYr4Zka3l4vxtZfH1Uikjtyy9z1H4Swo0rQzMKXncVzBXiOo5TjE-Dy9fcoG3ZF7UVdQ35jp_cFwzOlpK5Y; ut=FobyicMgeV51lVMr4ZJXvn-72bp0oeSOvtzifFY_U7kBFtR6og4Usd-VtBM5XBBvHq0lvd9xXkvpIqWro9EDKmv6cbKOQGyawUSMcKVP57isZCaM7lWQ6jWXajvTfvV4mIR-W_MZNK8VY0lL9W4qNMniJ6PBn_gkJsSAJCadmsyI9cxmjx--gR4m54pdF_nie_y4iWHys83cmWR2R7Bt1KKqB25OmkfCQTJJqIf7QsqangVGMUHwMC39Z9QhrfCFHKVNrlqS503O6b9GitQnXtvUdJhCmomu; pi=4253366368931142%3Bp4253366368931142%3B%E8%82%A1%E5%8F%8B9x56I87727%3BYNigLZRW%2FzMdGgVDOJbwReDWnTPHl51dB0gQLiwaCf1XY98mlJYx6eJbsoYr5Nie%2BX1L%2BzaMsec99KkX%2BT29Ds1arfST7sIBXxjUQ3dp11IPUnXy64PaBFRTHzMRWnCFJvvhc%2FAI41rXSGXolC8YMxI%2BvyPS%2BuErwgOVjC5vvsIiKeO7TLyKkhqqQJPX%2F7RWC5Sf3QLh%3Bdwjn4Xho10%2FKjqOgTWs%2FJF4%2FkdKzeuBwM8sz9aLvJovejAkCAyGMyGYA6AE67Xk2Ki7x8zdfBifF2DG%2Fvf2%2BXAYN8ZVISSEWTIXh32Z5MxEacK4JBTkqyiD93e1vFBOFQ82BqaiVmntUq0V6FrTUHGeh1gG5Sg%3D%3D; uidal=4253366368931142%e8%82%a1%e5%8f%8b9x56I87727; sid=170711377; vtpst=|; quote_lt=1; websitepoptg_api_time=1715777390466; emshistory=%5B%22%E8%BD%AC%E5%80%BA%E6%A0%87%22%2C%22%E8%BD%AC%E5%80%BA%E6%A0%87%E7%9A%84%22%5D; st_si=00364513876913; st_asi=delete; HAList=ty-116-00700-%u817E%u8BAF%u63A7%u80A1%2Cty-1-688695-%u4E2D%u521B%u80A1%u4EFD%2Cty-1-600849-%u4E0A%u836F%u8F6C%u6362%2Cty-1-603361-%u6D59%u6C5F%u56FD%u7965%2Cty-1-603555-ST%u8D35%u4EBA%2Cty-0-000627-%u5929%u8302%u96C6%u56E2%2Cty-0-002470-%u91D1%u6B63%u5927%2Cty-0-832876-%u6167%u4E3A%u667A%u80FD%2Cty-0-300059-%u4E1C%u65B9%u8D22%u5BCC%2Cty-107-CWB-%u53EF%u8F6C%u503AETF-SPDR; st_pvi=26930719093675; st_sp=2024-04-28%2017%3A27%3A05; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=23; st_psi=20240517111108288-113200301321-2767127768'
    while True:
        us_df = get_us_stock_real_time_quotes(cookie_test, None)
        us_df = us_df.loc[us_df['flow_mv'] != 0]
        us_df = us_df.sort_values(by=['amount'], ascending=False)
        us_stock_df = us_df[[
            "symbol",
            "name",
            "chg",
            "amount"
        ]]
        logger.info('test')
