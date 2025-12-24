from mns_common.db.MongodbUtil import MongodbUtil
import requests
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import datetime
from loguru import logger
import mns_common.component.proxies.proxy_common_api as proxy_common_api
import mns_common.api.em.real_time.east_money_stock_common_api as east_money_stock_common_api

mongodb_util = MongodbUtil('27017')

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,"
          "f18,f20,f21,f26,f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212"),
fs = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"

# 分页条数
PAGE_SIZE = 100


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


def get_stock_page_data(pn, proxies, page_size, time_out):
    """获取单页股票数据"""
    current_time = datetime.datetime.now()
    current_timestamp_ms = int(current_time.timestamp() * 1000)

    url = "https://33.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "cb": "jQuery1124046660442520420653_" + str(current_timestamp_ms),
        "pn": str(pn),
        "pz": str(page_size),
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

        if r.status_code != 200:
            return pd.DataFrame()

        data_text = r.text
        begin_index = data_text.index('[')
        end_index = data_text.index(']')
        data_json = data_text[begin_index:end_index + 1]
        data_json = json.loads(data_json)

        if not data_json:
            return pd.DataFrame()

        result_df = pd.DataFrame(data_json)
        result_df['page_number'] = pn
        return result_df
    except Exception as e:
        return pd.DataFrame()


def get_real_time_quotes_all_stocks(time_out):
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
    page_df = east_money_stock_common_api.rename_real_time_quotes_df(page_df)
    page_df.drop_duplicates('symbol', keep='last', inplace=True)
    return page_df


if __name__ == '__main__':
    # 调用方式
    df = get_real_time_quotes_all_stocks(5)
    logger.info("数据条数,{}", df.shape[0])
