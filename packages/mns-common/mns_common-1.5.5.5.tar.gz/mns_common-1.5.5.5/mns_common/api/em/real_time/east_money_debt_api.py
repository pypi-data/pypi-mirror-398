import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

import json
import akshare as ak
import pandas as pd
from loguru import logger
import requests
import time
import numpy as np
import mns_common.component.proxies.proxy_common_api as proxy_common_api
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import concurrent.futures
import mns_common.utils.data_frame_util as data_frame_util

# 分页条数
page_number = 100

fields = ("f352,f2,f3,f5,f6,f8,f10,f11,f22,f12,f14,f15,f16,f17,f18,f20,f21,f26,f33,f34,f35,f62,f66,f69,f72,f184,"
          "f211,f212,f232,f233,f234")


def get_kzz_count(pn, proxies, page_size, time_out):
    current_timestamp = str(int(round(time.time() * 1000, 0)))
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    params = {
        "cb": "jQuery34103608466964799838_" + current_timestamp,
        "pn": str(pn),
        "np": 3,
        "ut": "8a086bfc3570bdde64a6a1c585cccb35",
        "fltt": 1,
        "invt": 1,
        "fs": "m:0+e:11,m:1+e:11,m:1+e:11+s:4194304,m:0+e:11+s:8388608",
        "dpt": "zqsc.zpg",
        "fields": fields,
        "wbp2u": "|0|0|0|wap",
        "fid": "f12",
        "po": 1,
        "pz": str(page_size),
        "_": current_timestamp
    }
    try:
        if proxies is None:
            r = requests.get(url, params, timeout=time_out)
        else:
            r = requests.get(url, params, proxies=proxies, timeout=time_out)
        data_text = r.text

        begin_index_total = data_text.index('"total":')

        end_index_total = data_text.index('"diff"')
        max_number = int(data_text[begin_index_total + 8:end_index_total - 1])
        return max_number


    except Exception as e:
        logger.error("获取可转债列表,实时行情异常:{}", e)
        return 0


#
# url = https://push2.eastmoney.com/api/qt/clist/get?cb=jQuery34103608466964799838_1718163189869&pn=1&np=1&ut
# =8a086bfc3570bdde64a6a1c585cccb35&fltt=1&invt=1&fs=m:0+e:11,m:1+e:11,m:1+e:11+s:4194304,
# m:0+e:11+s:8388608&dpt=zqsc.zpg&fields=f1,f2,f3,f4,f5,f6,f8,f10,f12,f13,f14,f18,f22,f152,
# f237&wbp2u=|0|0|0|wap&fid=f3&po=1&pz=2000&_=1718163189870
def get_debt_page_data(pn, proxies, page_size, time_out) -> pd.DataFrame:
    current_timestamp = str(int(round(time.time() * 1000, 0)))
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    params = {
        "cb": "jQuery34103608466964799838_" + current_timestamp,
        "pn": str(pn),
        "np": 3,
        "ut": "8a086bfc3570bdde64a6a1c585cccb35",
        "fltt": 1,
        "invt": 1,
        "fs": "m:0+e:11,m:1+e:11,m:1+e:11+s:4194304,m:0+e:11+s:8388608",
        "dpt": "zqsc.zpg",
        "fields": fields,
        "wbp2u": "|0|0|0|wap",
        "fid": "f12",
        "po": 1,
        "pz": str(page_size),
        "_": current_timestamp
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
                logger.error(f"获取第{pn}页可转债列表异常: {e}")
                return pd.DataFrame()

        begin_index = data_text.index('[')
        end_index = data_text.index(']')
        data_json = data_text[begin_index:end_index + 1]
        data_json = json.loads(data_json)
        if data_json is None:
            return pd.DataFrame()
        else:
            return pd.DataFrame(data_json)
    except Exception as e:
        logger.error("获取可转债列表,实时行情异常:{}", e)
        return pd.DataFrame()


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
        # "f103": "concept",
        "f184": "today_main_net_inflow_ratio",
        "f352": "average_price",
        "f211": "buy_1_num",
        "f212": "sell_1_num",
        "f232": "stock_symbol",
        "f234": "stock_name",
        "f233": "market"
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
    # 大单比例
    temp_df['large_order_net_inflow_ratio'] = round((temp_df['large_order_net_inflow'] / temp_df['amount']) * 100, 2)

    # 外盘是内盘倍数
    temp_df['disk_ratio'] = round((temp_df['outer_disk'] - temp_df['inner_disk']) / temp_df['inner_disk'], 2)
    # 只有外盘没有内盘
    temp_df.loc[temp_df["inner_disk"] == 0, ['disk_ratio']] = 1688

    temp_df['now_price'] = round(temp_df['now_price'] / 1000, 3)
    temp_df['chg'] = round(temp_df['chg'] / 100, 2)
    temp_df['exchange'] = round(temp_df['exchange'] / 100, 2)
    temp_df['quantity_ratio'] = round(temp_df['quantity_ratio'] / 100, 2)

    temp_df['up_speed'] = round(temp_df['up_speed'] / 100, 2)
    temp_df['up_speed_05'] = round(temp_df['up_speed_05'] / 100, 2)

    temp_df['high'] = round(temp_df['high'] / 1000, 2)
    temp_df['low'] = round(temp_df['low'] / 1000, 2)

    temp_df['open'] = round(temp_df['open'] / 1000, 2)
    temp_df['yesterday_price'] = round(temp_df['yesterday_price'] / 1000, 2)
    temp_df['wei_bi'] = round(temp_df['wei_bi'] / 100, 2)
    temp_df['super_large_order_net_inflow_ratio'] = round(temp_df['super_large_order_net_inflow_ratio'] / 100, 2)
    temp_df['today_main_net_inflow_ratio'] = round(temp_df['today_main_net_inflow_ratio'] / 100, 2)
    temp_df['average_price'] = round(temp_df['average_price'] / 1000, 2)

    temp_df.loc[:, 'reference_main_inflow'] = round(
        (temp_df['flow_mv'] * (1 / 1000)), 2)

    temp_df.loc[:, 'main_inflow_multiple'] = round(
        (temp_df['today_main_net_inflow'] / temp_df['reference_main_inflow']), 2)

    temp_df.loc[:, 'super_main_inflow_multiple'] = round(
        (temp_df['super_large_order_net_inflow'] / temp_df['reference_main_inflow']), 2)
    temp_df['large_inflow_multiple'] = round(
        (temp_df['large_order_net_inflow'] / temp_df['reference_main_inflow']), 2)

    # 债权是10
    temp_df['disk_diff_amount'] = round(
        (temp_df['outer_disk'] - temp_df['inner_disk']) * temp_df[
            "average_price"] * 10,
        2)

    temp_df['disk_diff_amount_exchange'] = round(
        (temp_df['disk_diff_amount'] / temp_df['reference_main_inflow']), 2)
    temp_df.loc[:, 'sum_main_inflow_disk'] = temp_df['main_inflow_multiple'] + \
                                             temp_df['disk_diff_amount_exchange']
    temp_df.replace([np.inf, -np.inf], 0, inplace=True)
    temp_df = temp_df.fillna(0)
    return temp_df


# 可转债信息
def get_kzz_bond_info():
    try:
        bond_zh_cov_info_ths_df = ak.bond_zh_cov_info_ths()
        bond_zh_cov_info_ths_df = bond_zh_cov_info_ths_df.rename(columns={
            "债券代码": "symbol",
            "债券简称": "name",
            "申购日期": "apply_date",
            "申购代码": "apply_code",
            "原股东配售码": "config_code",
            "每股获配额": "per_share_limit",
            "计划发行量": "planned_circulation",
            "实际发行量": "actual_circulation",
            "中签公布日": "winning_date",
            "中签号": "winning_number",
            "上市日期": "list_date",
            "正股代码": "stock_code",
            "正股简称": "stock_name",
            "转股价格": "conversion_price",
            "到期时间": "due_date",
            "中签率": "lot_winning_rate"
        })
        return bond_zh_cov_info_ths_df
    except BaseException as e:
        logger.error("获取可转债信息异常:{}", e)


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
                page_df = get_debt_page_data(current_page, proxies, page_number, time_out)
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

    return rename_real_time_quotes_df(result_df)


def get_kzz_real_time_quotes(time_out, pages_per_thread):
    try_numer = 3
    while try_numer > 0:
        proxy_ip = proxy_common_api.generate_proxy_ip_api(1)
        proxies = {"https": proxy_ip,
                   "http": proxy_ip}

        max_number = get_kzz_count(1, proxies, 20, time_out)
        if max_number > 0:
            break
        try_numer = try_numer - 1
    if max_number == 0:
        return pd.DataFrame()

    total_pages = (max_number + page_number - 1) // page_number  # 向上取整

    num_threads = int((total_pages / pages_per_thread) + 1)
    return repeated_acquisition_ask_etf_async(time_out, max_number, num_threads, pages_per_thread)


if __name__ == '__main__':
    test_df = get_kzz_real_time_quotes(30, 6)
    print(test_df)
