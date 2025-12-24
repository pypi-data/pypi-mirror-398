import sys
import os

import pandas as pd
import requests
from py_mini_racer import py_mini_racer
from akshare.datasets import get_ths_js
import mns_common.utils.data_frame_util as data_frame_util


file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
# 大单页面数量
PAGE_NUMBER = 10


def _get_file_content_ths(file: str = "ths.js") -> str:
    """
    获取 JS 文件的内容
    :param file:  JS 文件名
    :type file: str
    :return: 文件内容
    :rtype: str
    """
    setting_file_path = get_ths_js(file)
    with open(setting_file_path) as f:
        file_data = f.read()
    return file_data


def stock_fund_flow_big_deal(begin_date, end_date) -> pd.DataFrame:
    """
    同花顺-数据中心-资金流向-大单追踪
    https://data.10jqka.com.cn/funds/ddzz
    :return: 大单追踪
    :rtype: pandas.DataFrame
    """
    js_code = py_mini_racer.MiniRacer()
    js_content = _get_file_content_ths("../concept/web/ths.js")
    js_code.eval(js_content)
    v_code = js_code.call("v")
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "hexin-v": v_code,
        "Host": "data.10jqka.com.cn",
        "Pragma": "no-cache",
        "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    url = "http://data.10jqka.com.cn/funds/ddzz/order/desc/ajax/1/free/1/"
    r = requests.get(url, headers=headers)

    page_num = PAGE_NUMBER
    url = "http://data.10jqka.com.cn/funds/ddzz/order/asc/page/{}/ajax/1/free/1/"
    big_df = pd.read_html(r.text)[0]
    page = 1
    while page <= page_num:
        js_code = py_mini_racer.MiniRacer()
        js_content = _get_file_content_ths("../concept/web/ths.js")
        js_code.eval(js_content)
        v_code = js_code.call("v")
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "hexin-v": v_code,
            "Host": "data.10jqka.com.cn",
            "Pragma": "no-cache",
            "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        r = requests.get(url.format(page), headers=headers)
        temp_df = pd.read_html(r.text)[0]

        # temp_df = temp_df.loc[(temp_df['deal_time'] >= begin_date) & (temp_df['deal_time'] <= end_date)]
        # if data_frame_util.is_empty(temp_df):
        #     break

        big_df = pd.concat([big_df, temp_df], ignore_index=True)
        page = page + 1

    if data_frame_util.is_empty(big_df):
        return None
    big_df.columns = [
        "deal_time",
        "symbol",
        "name",
        "price",
        "volume",
        "amount",
        "type",
        "chg",
        "change",
        "detail",
    ]
    del big_df['detail']
    big_df['symbol'] = big_df['symbol'].astype(str).str.zfill(6)
    return big_df
