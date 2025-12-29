import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
from loguru import logger
import requests
import time
import mns_common.component.proxies.proxy_common_api as proxy_common_api
from concurrent.futures import ThreadPoolExecutor
import json
import mns_common.component.cookie.cookie_info_service as cookie_info_service

# 分页条数
page_number = 100

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,f18,f20,f21,f26,"
          "f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212")


def get_hk_stock_count(pn, proxies, page_size, cookie, time_out):
    try:
        headers = {
            'Cookie': cookie
        }
        current_timestamp = str(int(round(time.time() * 1000, 0)))

        url_new = ('https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery371026074131356896413_' + str(
            current_timestamp) +
                   '&np=1'
                   '&fltt=1'
                   '&invt=2'
                   '&fs=m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2'
                   '&fields=' + fields +
                   '&fid=f12'
                   '&pn=' + str(pn) +
                   '&pz=' + str(page_size) +
                   '&po=1'
                    '&dect=1'
                   '&ut=fa5fd1943c7b386f172d6893dbfba10b'
                   '&wbp2u=4253366368931142|0|1|0|web'
                   '&_' + str(current_timestamp))

        if proxies is None:
            r = requests.get(url_new, headers=headers, timeout=time_out)
        else:
            r = requests.get(url_new, headers=headers, proxies=proxies, timeout=time_out)
        result = r.content.decode("utf-8")
        begin_index_total = result.index('"total":')
        end_index_total = result.index('"diff"')
        return int(result[begin_index_total + 8:end_index_total - 1])
    except Exception as e:
        logger.error("获取港股股票列表,实时行情异常:{}", e)
        return 0


def get_hk_real_time_quotes_page_df(pn, proxies, page_size, cookie, time_out):
    try:
        headers = {
            'Cookie': cookie
        }
        current_timestamp = str(int(round(time.time() * 1000, 0)))
        url_new = ('https://61.push2.eastmoney.com/api/qt/clist/get?cb=jQuery112409497467688484127_' + str(
            current_timestamp) +
                   '&pn=' + str(pn) +
                   '&pz=' + str(page_size) +
                   '&po=1'
                   '&np=3'
                   '&ut=bd1d9ddb04089700cf9c27f6f7426281'
                   '&fltt=2'
                   '&invt=2'
                   '&wbp2u=4253366368931142|0|1|0|web'
                   '&fid=f12'
                   '&fs=m:116+t:3,m:116+t:4,m:116+t:1,m:116+t:2'
                   '&fields=' + fields +
                   '&_=' + str(current_timestamp))

        if proxies is None:
            r = requests.get(url_new, headers=headers, timeout=time_out)
        else:
            r = requests.get(url_new, headers=headers, proxies=proxies, timeout=time_out)
        result = r.content.decode("utf-8")
        startIndex = result.index('"diff"')
        endIndex = result.index('}]}')
        result = result[startIndex + 7:endIndex + 2]
        data_json = json.loads(result)
        temp_df = pd.DataFrame(data_json)
        return temp_df
    except Exception as e:
        logger.error("获取港股列表,实时行情异常:{}", e)
        return pd.DataFrame()


# 改名
def rename_hk_field(temp_df):
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


def all_hk_stock_ticker_data_new(initial_proxies, time_out, em_cookie, max_number) -> pd.DataFrame:
    """
    使用多线程获取所有股票数据，失败页面会使用新IP重试，最多使用10个IP
    """
    per_page = page_number
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整
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
                executor.submit(get_hk_real_time_quotes_page_df, pn, proxies,
                                per_page, em_cookie, time_out): pn
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


def get_hk_real_time_quotes(time_out, em_cookie):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        initial_proxies = {"https": proxy_ip,
                           "http": proxy_ip}

        max_number = get_hk_stock_count(1, initial_proxies, 20, em_cookie, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        return pd.DataFrame()
    all_hk_stock_ticker_data_new_df = all_hk_stock_ticker_data_new(initial_proxies, time_out, em_cookie, max_number)
    return rename_hk_field(all_hk_stock_ticker_data_new_df)


if __name__ == '__main__':
    em_cookie_test = cookie_info_service.get_em_cookie()
    get_hk_real_time_quotes(30, em_cookie_test)
