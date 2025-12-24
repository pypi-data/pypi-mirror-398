import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import pandas as pd
from loguru import logger
import requests
import time
import mns_common.component.proxies.proxy_common_api as proxy_common_api
import concurrent.futures

from threading import Lock
import mns_common.utils.data_frame_util as data_frame_util

# 分页条数
page_number = 100


def rename_hg_ggt(temp_df):
    temp_df.columns = [
        "序号",
        "-",
        "最新价",
        "涨跌幅",
        "涨跌额",
        "成交量",
        "成交额",
        "-",
        "-",
        "-",
        "-",
        "-",
        "代码",
        "-",
        "名称",
        "最高",
        "最低",
        "今开",
        "昨收",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]
    temp_df = temp_df[
        [
            "序号",
            "代码",
            "名称",
            "最新价",
            "涨跌额",
            "涨跌幅",
            "今开",
            "最高",
            "最低",
            "昨收",
            "成交量",
            "成交额",
        ]
    ]

    temp_df = temp_df.rename(columns={
        "序号": "index",
        "代码": "symbol",
        "名称": "name",
        "最新价": "now_price",
        "涨跌额": "range",
        "涨跌幅": "chg",
        "今开": "open",
        "最高": "high",
        "最低": "low",
        "昨收": "yesterday_price",
        "成交额": "amount",
        "成交量": "volume",
    })

    return temp_df


# 获取港股通个数
def get_stock_hk_ggt_components_em_count(cookie, pn, proxies, page_size, time_out):
    headers = {
        'Cookie': cookie
    }
    url = "https://33.push2.eastmoney.com/api/qt/clist/get"
    current_timestamp = str(int(round(time.time() * 1000, 0)))
    params = {
        "pn": str(pn),
        "pz": str(page_size),
        "po": "1",
        "np": "2",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "fid": "f3",
        "fs": "b:DLMK0146,b:DLMK0144",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f23,f24,"
                  "f25,f26,f22,f33,f11,f62,f128,f136,f115,f152",
        "_": str(current_timestamp),
    }
    try:
        if proxies is None:
            r = requests.get(url, params, timeout=time_out, headers=headers)
        else:
            r = requests.get(url, params, proxies=proxies, timeout=time_out, headers=headers)
        data_json = r.json()
        total_number = int(data_json['data']['total'])
        return total_number
    except Exception as e:
        logger.error("获取港股通列表,实时行情异常:{}", e)
        return 0


# 获取港股通名单 todo 被封以后替换
def stock_hk_ggt_components_em(cookie, pn, proxies, page_size, time_out) -> pd.DataFrame:
    """
    东方财富网-行情中心-港股市场-港股通成份股
    https://quote.eastmoney.com/center/gridlist.html#hk_components
    :return: 港股通成份股
    :rtype: pandas.DataFrame
    """
    headers = {
        'Cookie': cookie
    }
    url = "https://33.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": str(pn),
        "pz": str(page_size),
        "po": "1",
        "np": "2",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "fid": "f3",
        "fs": "b:DLMK0146,b:DLMK0144",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f23,f24,"
                  "f25,f26,f22,f33,f11,f62,f128,f136,f115,f152",
        "_": "1639974456250",
    }
    try:
        if proxies is None:
            r = requests.get(url, params=params, timeout=time_out, headers=headers)
        else:
            r = requests.get(url, params=params, proxies=proxies, timeout=time_out, headers=headers)

        data_json = r.json()
        temp_df = pd.DataFrame(data_json["data"]["diff"]).T
        temp_df.reset_index(inplace=True)
        temp_df["index"] = temp_df.index + 1
        return temp_df
    except Exception as e:
        logger.error("获取港股通列表:{}", e)


def repeated_acquisition_ask_hk_gtt_async(em_cookie, time_out, max_number, num_threads, pages_per_thread):
    per_page = page_number
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整
    result_df = pd.DataFrame()

    # 创建线程锁以确保线程安全
    df_lock = Lock()

    # 计算每个线程处理的页数范围
    def process_page_range(start_page, end_page, thread_id):
        nonlocal result_df
        local_df = pd.DataFrame()
        current_page = start_page
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)

        while current_page <= end_page and current_page <= total_pages:
            proxies = {"https": proxy_ip, "http": proxy_ip}
            try:
                page_df = stock_hk_ggt_components_em(em_cookie, current_page, proxies, page_number, time_out)
                if data_frame_util.is_not_empty(page_df):
                    local_df = pd.concat([local_df, page_df])
                    logger.info("线程{}获取页面数据成功: {}", thread_id, current_page)
                    current_page += 1
                else:
                    time.sleep(0.2)
                    proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                    logger.info("线程{}获取页面数据失败: {}", thread_id, current_page)
            except BaseException as e:
                time.sleep(1)
                proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
                logger.error("线程{}处理页面{}时发生错误: {}", thread_id, current_page, e)

        with df_lock:
            result_df = pd.concat([result_df, local_df])
        return len(local_df)

    # 计算每个线程的页面范围
    page_ranges = []
    for i in range(num_threads):
        start_page = i * pages_per_thread + 1
        end_page = (i + 1) * pages_per_thread
        if start_page > total_pages:
            break
        page_ranges.append((start_page, end_page, i + 1))

    # 使用线程池执行任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交所有任务
        futures = [
            executor.submit(process_page_range, start, end, tid)
            for start, end, tid in page_ranges
        ]

        # 等待所有任务完成并获取结果
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error("线程执行出错: {}", e)

    return rename_hg_ggt(result_df)


# 港股通实时行情
def get_ggt_real_time_quotes(em_cookie, time_out, pages_per_thread):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        proxies = {"https": proxy_ip,
                   "http": proxy_ip}

        max_number = get_stock_hk_ggt_components_em_count(em_cookie, 1, proxies, 20, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        return pd.DataFrame()

    total_pages = (max_number + page_number - 1) // page_number  # 向上取整

    num_threads = int((total_pages / pages_per_thread) + 1)
    return repeated_acquisition_ask_hk_gtt_async(em_cookie, time_out, max_number, num_threads, pages_per_thread)


import mns_common.component.cookie.cookie_info_service as cookie_info_service

if __name__ == '__main__':
    em_cookie_test = cookie_info_service.get_em_cookie()
    test_df = get_ggt_real_time_quotes(em_cookie_test, 30, 6)
    print(test_df)
