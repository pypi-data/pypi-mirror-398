import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests

import mns_common.utils.data_frame_util as data_frame_util
import json
import datetime
from concurrent.futures import ThreadPoolExecutor
import mns_common.component.proxies.proxy_common_api as proxy_common_api
from loguru import logger
import concurrent.futures
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import mns_common.api.em.real_time.real_time_quotes_repeat_api as real_time_quotes_repeat_api
import mns_common.api.em.real_time.east_money_stock_common_api as east_money_stock_common_api

#
# fields_02 = "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f22,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100,f101,f102,f103,f104,f105,f106,f107,f108" \
#             ",f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200" \
#             ",f209,f210,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f250,f251,f252,f253,f254,f255,f256,f257,f258,f259,f260,f261,f262,f263,f264,f265,f266,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f277,f278,f279,f280,f281,f282,f283,f284,f285,f286,f287,f288,f289,f290,f291,f292,f293,f294,f295,f296,f297,f298,f299,f300" \
#             ",f309,f310,f312,f313,f314,f315,f316,f317,f318,f319,f320,f321,f322,f323,f324,f325,f326,f327,f328,f329,f330,f331,f332,f333,f334,f335,f336,f337,f338,f339,f340,f341,f342,f343,f344,f345,f346,f347,f348,f349,f350,f351,f352,f353,f354,f355,f356,f357,f358,f359,f360,f361,f362,f363,f364,f365,f366,f367,f368,f369,f370,f371,f372,f373,f374,f375,f376,f377,f378,f379,f380,f381,f382,f383,f384,f385,f386,f387,f388,f389,f390,f391,f392,f393,f394,f395,f396,f397,f398,f399,f401"


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

# 分页条数
PAGE_SIZE = 100


def get_stock_page_data(pn, proxies, page_number, time_out):
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
        begin_index = data_text.index('[')
        end_index = data_text.index(']')
        data_json = data_text[begin_index:end_index + 1]
        data_json = json.loads(data_json)
        if data_json is None:
            return pd.DataFrame()
        else:
            return pd.DataFrame(data_json)
    except Exception as e:
        return pd.DataFrame()


def all_stock_ticker_data_new(initial_proxies, time_out, max_number) -> pd.DataFrame:
    """
            使用多线程获取所有股票数据，失败页面会使用新IP重试，最多使用10个IP
            """

    total_pages = (max_number + PAGE_SIZE - 1) // PAGE_SIZE  # 向上取整
    all_pages = set(range(1, total_pages + 1))  # 所有需要获取的页码
    success_pages = set()  # 成功获取的页码
    results = []  # 存储成功获取的数据
    used_ip_count = 1  # 已使用IP计数器（初始IP算第一个）
    MAX_IP_LIMIT = 10  # IP使用上限

    # 循环处理直到所有页面成功或达到IP上限
    while (all_pages - success_pages) and (used_ip_count < MAX_IP_LIMIT):
        # 获取当前需要处理的失败页码
        current_failed_pages = all_pages - success_pages
        if used_ip_count > 1:
            logger.info("当前需要处理的失败页码: {}, 已使用IP数量: {}/{}", current_failed_pages, used_ip_count,
                        MAX_IP_LIMIT)

        # 首次使用初始代理，后续获取新代理
        if len(success_pages) == 0:
            proxies = initial_proxies
        else:
            # 每次重试前获取新代理并计数
            # logger.info("获取新代理IP处理失败页面")
            new_proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
            proxies = {"https": new_proxy_ip}
            # logger.info("新代理IP: {}, 已使用IP数量: {}/{}", new_proxy_ip, used_ip_count + 1, MAX_IP_LIMIT)
            used_ip_count += 1  # 增加IP计数器

        # 创建线程池处理当前失败的页码
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(get_stock_page_data, pn, proxies, PAGE_SIZE, time_out): pn
                for pn in current_failed_pages
            }

            # 收集结果并记录成功页码
            for future, pn in futures.items():
                try:
                    result = future.result()
                    if not result.empty:
                        results.append(result)
                        success_pages.add(pn)
                    # else:
                    #     logger.warning("页码 {} 未返回有效数据", pn)
                except Exception as e:
                    continue
                    # logger.error("页码 {} 处理异常: {}", pn, str(e))

    # 检查是否达到IP上限
    if used_ip_count >= MAX_IP_LIMIT and (all_pages - success_pages):
        remaining_pages = all_pages - success_pages
        logger.warning("已达到最大IP使用限制({}个)，剩余未获取页码: {}, 返回现有数据", MAX_IP_LIMIT, remaining_pages)

    # 合并所有成功获取的数据
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame()


# 获取所有股票实时行情数据    f33,委比
def rename_real_time_quotes_df(temp_df):
    temp_df = temp_df.rename(columns={
        "f2": "now_price",
        "f3": "chg",
        "f5": "volume",
        "f6": "amount",
        "f8": "exchange",
        "f9": "pe_ttm",
        "f10": "quantity_ratio",
        "f22": "up_speed",
        "f12": "symbol",
        "f13": "sz_sh",
        "f14": "name",
        "f15": "high",
        "f16": "low",
        "f17": "open",
        "f18": "yesterday_price",
        "f20": "total_mv",
        "f21": "flow_mv",
        "f23": "pb",
        "f26": "list_date",
        "f33": "wei_bi",
        "f34": "outer_disk",
        "f35": "inner_disk",
        "f37": "ROE",
        "f38": "total_share",
        "f39": "flow_share",
        "f62": "today_main_net_inflow",
        "f64": "super_large_order_inflow",
        "f65": "super_large_order_outflow",
        "f67": "super_large_order_inflow_ratio",
        "f68": "super_large_order_outflow_ratio",

        "f66": "super_large_order_net_inflow",
        "f69": "super_large_order_net_inflow_ratio",
        "f70": "large_order_inflow",
        "f71": "large_order_outflow",
        "f72": "large_order_net_inflow",

        "f76": "medium_order_inflow",
        "f77": "medium_order_outflow",
        "f78": "medium_order_net_inflow",
        "f82": "small_order_inflow",
        "f83": "small_order_outflow",

        "f84": "small_order_net_inflow",
        "f102": "area",
        "f184": "today_main_net_inflow_ratio",
        "f100": "industry",
        "f103": "concept",

        "f352": "average_price",
        "f191": "hk_stock_code",
        "f193": "hk_stock_name",
        "f24": "sixty_day_chg",
        "f25": "now_year_chg",
    })
    temp_df.loc[temp_df['sixty_day_chg'] == '-', 'total_share'] = 0

    temp_df.loc[temp_df['now_year_chg'] == '-', 'now_year_chg'] = 0
    temp_df.loc[temp_df['total_share'] == '-', 'total_share'] = 0
    temp_df.loc[temp_df['flow_share'] == '-', 'flow_share'] = 0
    temp_df.loc[temp_df['pe_ttm'] == '-', 'pe_ttm'] = 0
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
    temp_df.loc[temp_df['super_large_order_inflow'] == '-', 'super_large_order_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_outflow'] == '-', 'super_large_order_outflow'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow'] == '-', 'super_large_order_net_inflow'] = 0
    temp_df.loc[temp_df['super_large_order_inflow_ratio'] == '-', 'super_large_order_inflow_ratio'] = 0
    temp_df.loc[temp_df['super_large_order_outflow_ratio'] == '-', 'super_large_order_outflow_ratio'] = 0
    temp_df.loc[temp_df['super_large_order_net_inflow_ratio'] == '-', 'super_large_order_net_inflow_ratio'] = 0

    temp_df.loc[temp_df['large_order_net_inflow'] == '-', 'large_order_net_inflow'] = 0
    temp_df.loc[temp_df['large_order_inflow'] == '-', 'large_order_inflow'] = 0
    temp_df.loc[temp_df['large_order_outflow'] == '-', 'large_order_outflow'] = 0

    temp_df.loc[temp_df['medium_order_net_inflow'] == '-', 'medium_order_net_inflow'] = 0
    temp_df.loc[temp_df['medium_order_outflow'] == '-', 'medium_order_outflow'] = 0
    temp_df.loc[temp_df['medium_order_inflow'] == '-', 'medium_order_inflow'] = 0

    temp_df.loc[temp_df['small_order_inflow'] == '-', 'small_order_inflow'] = 0
    temp_df.loc[temp_df['small_order_outflow'] == '-', 'small_order_outflow'] = 0
    temp_df.loc[temp_df['small_order_net_inflow'] == '-', 'small_order_net_inflow'] = 0

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
    temp_df["medium_order_net_inflow"] = pd.to_numeric(temp_df["medium_order_net_inflow"],
                                                       errors="coerce")

    temp_df["small_order_net_inflow"] = pd.to_numeric(temp_df["small_order_net_inflow"], errors="coerce")

    temp_df["pe_ttm"] = pd.to_numeric(temp_df["pe_ttm"], errors="coerce")
    temp_df["total_share"] = pd.to_numeric(temp_df["total_share"], errors="coerce")
    temp_df["flow_share"] = pd.to_numeric(temp_df["flow_share"], errors="coerce")

    temp_df["super_large_order_inflow"] = pd.to_numeric(temp_df["super_large_order_inflow"], errors="coerce")
    temp_df["super_large_order_outflow"] = pd.to_numeric(temp_df["super_large_order_outflow"], errors="coerce")

    temp_df["super_large_order_inflow_ratio"] = pd.to_numeric(temp_df["super_large_order_inflow_ratio"],
                                                              errors="coerce")
    temp_df["super_large_order_outflow_ratio"] = pd.to_numeric(temp_df["super_large_order_outflow_ratio"],
                                                               errors="coerce")

    temp_df["super_large_order_net_inflow"] = pd.to_numeric(temp_df["super_large_order_net_inflow"], errors="coerce")
    temp_df["super_large_order_net_inflow_ratio"] = pd.to_numeric(temp_df["super_large_order_net_inflow_ratio"],
                                                                  errors="coerce")

    temp_df["medium_order_inflow"] = pd.to_numeric(temp_df["medium_order_inflow"], errors="coerce")
    temp_df["medium_order_outflow"] = pd.to_numeric(temp_df["medium_order_outflow"], errors="coerce")

    temp_df["small_order_inflow"] = pd.to_numeric(temp_df["small_order_inflow"], errors="coerce")
    temp_df["small_order_outflow"] = pd.to_numeric(temp_df["small_order_outflow"], errors="coerce")

    outer_disk = temp_df['outer_disk']
    inner_disk = temp_df['inner_disk']
    disk_ratio = (outer_disk - inner_disk) / inner_disk
    temp_df['disk_ratio'] = round(disk_ratio, 2)
    return temp_df


def get_stock_real_time_quotes(time_out):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        initial_proxies = {"https": proxy_ip,
                           "http": proxy_ip}

        total_number = east_money_stock_common_api.get_stocks_num(1, initial_proxies, 20, time_out)
        if total_number > 0:
            break
        try_numer = try_numer - 1
    if total_number == 0:
        return pd.DataFrame()

    page_df = all_stock_ticker_data_new(initial_proxies, time_out, total_number)
    page_df = rename_real_time_quotes_df(page_df)
    page_df.drop_duplicates('symbol', keep='last', inplace=True)
    return page_df


# 示例调用
if __name__ == "__main__":
    df = get_stock_real_time_quotes(5)
    zt_df = df.loc[df['wei_bi'] == 100]
    logger.info("同步次数", zt_df.shape[0])
