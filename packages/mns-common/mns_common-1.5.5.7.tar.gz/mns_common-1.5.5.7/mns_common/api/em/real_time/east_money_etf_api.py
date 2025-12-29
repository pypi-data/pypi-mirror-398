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
import numpy as np
import mns_common.component.proxies.proxy_common_api as proxy_common_api
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import mns_common.utils.data_frame_util as data_frame_util

# 分页条数
page_number = 100


def get_etf_count(pn, proxies, page_size, time_out):
    """
    东方财富-ETF 实时行情
    https://quote.eastmoney.com/center/gridlist.html#fund_etf
    :return: ETF 实时行情
    :rtype: pandas.DataFrame
    """
    current_timestamp = str(int(round(time.time() * 1000, 0)))
    url = "https://88.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": str(pn),
        "pz": str(page_size),
        "po": "1",
        "np": "3",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f12",
        "fs": "b:MK0021,b:MK0022,b:MK0023,b:MK0024",
        "fields": (
            "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,"
            "f12,f13,f14,f15,f16,f17,f18,f20,f21,"
            "f23,f24,f25,f26,f22,f11,f30,f31,f32,f33,"
            "f34,f35,f38,f62,f63,f64,f65,f66,f69,"
            "f72,f75,f78,f81,f84,f87,f115,f124,f128,"
            "f136,f152,f184,f297,f402,f441"
        ),
        "_": str(current_timestamp),
    }
    try:
        if proxies is None:
            r = requests.get(url, params, timeout=time_out)
        else:
            r = requests.get(url, params, proxies=proxies, timeout=time_out)
        data_json = r.json()
        total_number = int(data_json['data']['total'])
        return total_number
    except Exception as e:
        logger.error("获取ETF列表,实时行情异常:{}", e)
        return 0


def get_fund_etf_page_df(pn, proxies, page_size, time_out) -> pd.DataFrame:
    """
    东方财富-ETF 实时行情
    https://quote.eastmoney.com/center/gridlist.html#fund_etf
    :return: ETF 实时行情
    :rtype: pandas.DataFrame
    """
    current_timestamp = str(int(round(time.time() * 1000, 0)))
    url = "https://88.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": str(pn),
        "pz": str(page_size),
        "po": "1",
        "np": "3",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "wbp2u": "|0|0|0|web",
        "fid": "f12",
        "fs": "b:MK0021,b:MK0022,b:MK0023,b:MK0024",
        "fields": (
            "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,"
            "f12,f13,f14,f15,f16,f17,f18,f20,f21,"
            "f23,f24,f25,f26,f22,f11,f30,f31,f32,f33,"
            "f34,f35,f38,f62,f63,f64,f65,f66,f69,"
            "f72,f75,f78,f81,f84,f87,f115,f124,f128,"
            "f136,f152,f184,f297,f402,f441"
        ),
        "_": str(current_timestamp),
    }
    try:
        if proxies is None:
            r = requests.get(url, params, timeout=time_out)
        else:
            r = requests.get(url, params, proxies=proxies, timeout=time_out)
        data_json = r.json()
        if pn == 1:
            try:
                global max_number
                max_number = int(data_json['data']['total'])
            except Exception as e:
                logger.error("获取第{}页ETF列表异常:{}", page_size, str(e))
                return pd.DataFrame()

        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.rename(
            columns={
                "f26": "上市时间",
                "f12": "代码",
                "f14": "名称",
                "f2": "最新价",
                "f4": "涨跌额",
                "f3": "涨跌幅",
                "f5": "成交量",
                "f6": "成交额",
                "f7": "振幅",
                "f17": "开盘价",
                "f15": "最高价",
                "f16": "最低价",
                "f18": "昨收",
                "f8": "换手率",
                "f10": "量比",
                "f30": "现手",
                "f31": "买一",
                "f32": "卖一",
                "f33": "委比",
                "f34": "外盘",
                "f35": "内盘",
                "f62": "主力净流入-净额",
                "f184": "主力净流入-净占比",
                "f66": "超大单净流入-净额",
                "f69": "超大单净流入-净占比",
                "f72": "大单净流入-净额",
                "f75": "大单净流入-净占比",
                "f78": "中单净流入-净额",
                "f81": "中单净流入-净占比",
                "f84": "小单净流入-净额",
                "f87": "小单净流入-净占比",
                "f38": "最新份额",
                "f21": "流通市值",
                "f20": "总市值",
                "f402": "基金折价率",
                "f441": "IOPV实时估值",
                "f297": "数据日期",
                "f124": "更新时间",
                "f13": "market"
            },
            inplace=True,
        )
        temp_df = temp_df[
            [
                "代码",
                "名称",
                "最新价",
                "IOPV实时估值",
                "基金折价率",
                "涨跌额",
                "涨跌幅",
                "成交量",
                "成交额",
                "开盘价",
                "最高价",
                "最低价",
                "昨收",
                "振幅",
                "换手率",
                "量比",
                "委比",
                "外盘",
                "内盘",
                "主力净流入-净额",
                "主力净流入-净占比",
                "超大单净流入-净额",
                "超大单净流入-净占比",
                "大单净流入-净额",
                "大单净流入-净占比",
                "中单净流入-净额",
                "中单净流入-净占比",
                "小单净流入-净额",
                "小单净流入-净占比",
                "现手",
                "买一",
                "卖一",
                "最新份额",
                "流通市值",
                "总市值",
                "数据日期",
                "更新时间",
                "market",
                "上市时间"
            ]
        ]
        temp_df["最新价"] = pd.to_numeric(temp_df["最新价"], errors="coerce")
        temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
        temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
        temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
        temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
        temp_df["开盘价"] = pd.to_numeric(temp_df["开盘价"], errors="coerce")
        temp_df["最高价"] = pd.to_numeric(temp_df["最高价"], errors="coerce")
        temp_df["最低价"] = pd.to_numeric(temp_df["最低价"], errors="coerce")
        temp_df["昨收"] = pd.to_numeric(temp_df["昨收"], errors="coerce")
        temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")
        temp_df["量比"] = pd.to_numeric(temp_df["量比"], errors="coerce")
        temp_df["委比"] = pd.to_numeric(temp_df["委比"], errors="coerce")
        temp_df["外盘"] = pd.to_numeric(temp_df["外盘"], errors="coerce")
        temp_df["内盘"] = pd.to_numeric(temp_df["内盘"], errors="coerce")
        temp_df["流通市值"] = pd.to_numeric(temp_df["流通市值"], errors="coerce")
        temp_df["总市值"] = pd.to_numeric(temp_df["总市值"], errors="coerce")
        temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
        temp_df["现手"] = pd.to_numeric(temp_df["现手"], errors="coerce")
        temp_df["买一"] = pd.to_numeric(temp_df["买一"], errors="coerce")
        temp_df["卖一"] = pd.to_numeric(temp_df["卖一"], errors="coerce")
        temp_df["最新份额"] = pd.to_numeric(temp_df["最新份额"], errors="coerce")
        temp_df["IOPV实时估值"] = pd.to_numeric(temp_df["IOPV实时估值"], errors="coerce")
        temp_df["基金折价率"] = pd.to_numeric(temp_df["基金折价率"], errors="coerce")
        temp_df["主力净流入-净额"] = pd.to_numeric(
            temp_df["主力净流入-净额"], errors="coerce"
        )
        temp_df["主力净流入-净占比"] = pd.to_numeric(
            temp_df["主力净流入-净占比"], errors="coerce"
        )
        temp_df["超大单净流入-净额"] = pd.to_numeric(
            temp_df["超大单净流入-净额"], errors="coerce"
        )
        temp_df["超大单净流入-净占比"] = pd.to_numeric(
            temp_df["超大单净流入-净占比"], errors="coerce"
        )
        temp_df["大单净流入-净额"] = pd.to_numeric(
            temp_df["大单净流入-净额"], errors="coerce"
        )
        temp_df["大单净流入-净占比"] = pd.to_numeric(
            temp_df["大单净流入-净占比"], errors="coerce"
        )
        temp_df["中单净流入-净额"] = pd.to_numeric(
            temp_df["中单净流入-净额"], errors="coerce"
        )
        temp_df["中单净流入-净占比"] = pd.to_numeric(
            temp_df["中单净流入-净占比"], errors="coerce"
        )
        temp_df["小单净流入-净额"] = pd.to_numeric(
            temp_df["小单净流入-净额"], errors="coerce"
        )
        temp_df["小单净流入-净占比"] = pd.to_numeric(
            temp_df["小单净流入-净占比"], errors="coerce"
        )
        temp_df["数据日期"] = pd.to_datetime(
            temp_df["数据日期"], format="%Y%m%d", errors="coerce"
        )
        temp_df["更新时间"] = (
            pd.to_datetime(temp_df["更新时间"], unit="s", errors="coerce")
            .dt.tz_localize("UTC")
            .dt.tz_convert("Asia/Shanghai")
        )

        return temp_df
    except Exception as e:
        logger.error("获取ETF列表,实时行情异常:{}", e)
        return pd.DataFrame()


def thread_pool_executor(proxies):
    """
       使用多线程获取所有ETF数据
       """
    # 计算总页数，假设总共有1000条数据，每页200条

    per_page = page_number
    total_pages = (max_number + per_page - 1) // per_page  # 向上取整

    # 创建线程池
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务，获取每页数据
        futures = [executor.submit(get_fund_etf_page_df, pn, proxies)
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


def rename_etf(fund_etf_spot_em_df):
    fund_etf_spot_em_df = fund_etf_spot_em_df.rename(columns={
        "上市时间": "list_date",
        "最新价": "now_price",
        "涨跌幅": "chg",
        "基金折价率": "fund_discount_rate",
        "振幅": "pct_chg",
        "涨跌额": "range",
        "成交额": "amount",
        "成交量": "volume",
        "换手率": "exchange",
        "量比": "quantity_ratio",
        "代码": "symbol",
        "名称": "name",
        "最高价": "high",
        "最低价": "low",
        "开盘价": "open",
        "昨收": "yesterday_price",
        "总市值": "total_mv",
        "流通市值": "flow_mv",
        "委比": "wei_bi",
        "外盘": "outer_disk",
        "内盘": "inner_disk",
        "主力净流入-净额": "today_main_net_inflow",
        "超大单净流入-净额": "super_large_order_net_inflow",
        "超大单净流入-净占比": "super_large_order_net_inflow_ratio",
        "大单净流入-净额": "large_order_net_inflow",
        # "f78": "medium_order_net_inflow",
        # "f84": "small_order_net_inflow",
        # "f103": "concept",
        "主力净流入-净占比": "today_main_net_inflow_ratio",
        "买一": "buy_1_num",
        "卖一": "sell_1_num",
        "最新份额": "latest_share",
        "数据日期": "data_time",
        "更新时间": "update_time"
    })

    fund_etf_spot_em_df = fund_etf_spot_em_df[[
        "now_price",
        "chg",
        "fund_discount_rate",
        "pct_chg",
        "range",
        "amount",
        "volume",
        "exchange",
        "quantity_ratio",
        "symbol",
        "name",
        "high",
        "low",
        "open",
        "yesterday_price",
        "total_mv",
        "flow_mv",
        "wei_bi",
        "outer_disk",
        "inner_disk",
        "today_main_net_inflow",
        "super_large_order_net_inflow",
        "super_large_order_net_inflow_ratio",
        "large_order_net_inflow",
        "today_main_net_inflow_ratio",
        "buy_1_num",
        "sell_1_num",
        "latest_share",
        "data_time",
        "update_time",
        "market",
        'list_date'
    ]]

    fund_etf_spot_em_df['disk_ratio'] = round(
        (fund_etf_spot_em_df['outer_disk'] - fund_etf_spot_em_df['inner_disk']) / fund_etf_spot_em_df['inner_disk'], 2)

    fund_etf_spot_em_df.loc[:, 'reference_main_inflow'] = round(
        (fund_etf_spot_em_df['flow_mv'] * (1 / 1000)), 2)

    fund_etf_spot_em_df.loc[:, 'main_inflow_multiple'] = round(
        (fund_etf_spot_em_df['today_main_net_inflow'] / fund_etf_spot_em_df['reference_main_inflow']), 2)

    fund_etf_spot_em_df.loc[:, 'super_main_inflow_multiple'] = round(
        (fund_etf_spot_em_df['super_large_order_net_inflow'] / fund_etf_spot_em_df['reference_main_inflow']), 2)
    fund_etf_spot_em_df['large_inflow_multiple'] = round(
        (fund_etf_spot_em_df['large_order_net_inflow'] / fund_etf_spot_em_df['reference_main_inflow']), 2)

    fund_etf_spot_em_df['disk_diff_amount'] = round(
        (fund_etf_spot_em_df['outer_disk'] - fund_etf_spot_em_df['inner_disk']) * fund_etf_spot_em_df[
            "now_price"] * 100,
        2)

    fund_etf_spot_em_df['disk_diff_amount_exchange'] = round(
        (fund_etf_spot_em_df['disk_diff_amount'] / fund_etf_spot_em_df['reference_main_inflow']), 2)
    fund_etf_spot_em_df.loc[:, 'sum_main_inflow_disk'] = fund_etf_spot_em_df['main_inflow_multiple'] + \
                                                         fund_etf_spot_em_df['disk_diff_amount_exchange']
    fund_etf_spot_em_df = fund_etf_spot_em_df.fillna(0)

    fund_etf_spot_em_df.replace([np.inf, -np.inf], 0, inplace=True)
    return fund_etf_spot_em_df


def repeated_acquisition_ask_etf_async(time_out, max_number, num_threads, pages_per_thread):
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
                page_df = get_fund_etf_page_df(current_page, proxies, page_number, time_out)
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

    return rename_etf(result_df)


def get_etf_real_time_quotes(time_out, pages_per_thread):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        proxies = {"https": proxy_ip,
                   "http": proxy_ip}

        max_number = get_etf_count(1, proxies, 20, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        return pd.DataFrame()

    total_pages = (max_number + page_number - 1) // page_number  # 向上取整

    num_threads = int((total_pages / pages_per_thread) + 1)
    return repeated_acquisition_ask_etf_async(time_out, max_number, num_threads, pages_per_thread)


if __name__ == '__main__':
    test_df = get_etf_real_time_quotes(30, 6)
    print(test_df)
