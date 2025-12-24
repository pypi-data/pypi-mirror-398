import requests
import mns_common.utils.data_frame_util as data_frame_util
import json
import datetime
import mns_common.component.proxies.proxy_common_api as proxy_common_api
from loguru import logger
import mns_common.api.em.real_time.east_money_stock_common_api as east_money_stock_common_api
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,"
          "f18,f20,f21,f26,f33,f34,f35,f62,f66,f69,f72,f100,f184,f211,f212"),
fs = "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"

# 分页条数
PAGE_SIZE = 100


def get_stock_page_data_time_out(pn, proxies, page_size, time_out):
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
        if pn == 1:
            try:
                begin_index_total = data_text.index('"total":')

                end_index_total = data_text.index('"diff"')
                global max_number
                max_number = int(data_text[begin_index_total + 8:end_index_total - 1])
            except Exception as e:
                logger.error("获取第{}页股票列表异常:{}", pn, str(e))
                return pd.DataFrame()

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
        return pd.DataFrame()




def repeated_acquisition_ask_sync(time_out):
    per_page = PAGE_SIZE
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整
    result_df = pd.DataFrame()
    now_page = 1
    proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
    while now_page <= total_pages:
        proxies = {"https": proxy_ip,
                   "http": proxy_ip}
        try:
            page_df = get_stock_page_data_time_out(now_page, proxies, PAGE_SIZE, time_out)
            if data_frame_util.is_not_empty(page_df):
                result_df = pd.concat([page_df, result_df])
                logger.info("获取页面数据成功:{}", now_page)
                now_page = now_page + 1
            else:
                time.sleep(0.2)
                proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                logger.info("获取页面数据失败:{}", now_page)
        except BaseException as e:
            time.sleep(1)
            proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        # 示例调用
    return result_df


def repeated_acquisition_ask_async(initial_proxies, time_out, max_number):
    """
       使用多线程获取所有股票数据，失败页面会使用新IP重试，最多使用10个IP
       """
    per_page = PAGE_SIZE
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
                executor.submit(get_stock_page_data_time_out, pn, proxies, PAGE_SIZE, time_out): pn
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

    result_df = repeated_acquisition_ask_async(initial_proxies, time_out, total_number)
    return east_money_stock_common_api.rename_real_time_quotes_df(result_df)


if __name__ == '__main__':

    while True:
        # proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        # proxies = {"https": proxy_ip,
        #            "http": proxy_ip}
        time_out_test = 10  # Set the timeout value
        result = get_stock_real_time_quotes(time_out_test)
        print(result)
