import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import time
import requests

import mns_common.utils.data_frame_util as data_frame_util
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from akshare.utils.tqdm import get_tqdm
import mns_common.component.cookie.cookie_info_service as cookie_info_service

'''
获取单只股票代码 symbol 所有概念详情
'''
# 获取单个股票新增概念
# https://basic.10jqka.com.cn/basicph/briefinfo.html#/concept?broker=anelicaiapp&showtab=1&code=301016&code_name=%E9%9B%B7%E5%B0%94%E4%BC%9F&market_id=33
'''

'''


def get_one_symbol_all_ths_concepts(symbol: str = "305794") -> pd.DataFrame:
    try:
        url = f"http://basic.10jqka.com.cn/api/stockph/conceptdetail/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 iOS AYLCAPP/9.1.2.0/h4526a24eb9445522492fd64caae11b1f scheme/anelicaiapp deviceinfo/I|9.1.2.0|NA|h4526a24eb9445522492fd64caae11b1f pastheme/0",
            "Cookie": "ps_login_app_name=AYLCAPP;"
                      "ps_login_token_id=N_C993F777ACC500B354C762A2627A8862348FC8163799A08EBEB2301C28A2135D220475787D0E81425C1134E15D8CC8761D639FEDBD46C00FE8EA6482C1E42D9801B19918FB3F5C34;"
                      "ps_login_union_id=edc29089a2b64e3882062297030a0386;PAS.CURRENTUNIONID=edc29089a2b64e3882062297030a0386"
        }
        r = requests.get(url, headers=headers)
        data_json = r.json()
        data_concept = data_json['data']
        errorcode = data_json['errorcode']
        errormsg = data_json['errormsg']
        if errorcode == '0' and errormsg == '':
            data_concept_df = pd.DataFrame(data_concept)
            return data_concept_df
        else:
            return None
    except BaseException as e:
        logger.error("获取symbol概念信息异常:{},{}", symbol, e)


# web端口 获取概念详情 极容易被封 最好不使用了
def stock_board_cons_ths(symbol: str = "301558") -> pd.DataFrame:
    """
    通过输入行业板块或者概念板块的代码获取成份股
    https://q.10jqka.com.cn/thshy/detail/code/881121/
    https://q.10jqka.com.cn/gn/detail/code/301558/
    :param symbol: 行业板块或者概念板块的代码
    :type symbol: str
    :return: 行业板块或者概念板块的成份股
    :rtype: pandas.DataFrame
    """
    ths_cookie = cookie_info_service.get_ths_cookie()

    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://q.10jqka.com.cn/thshy/detail/code/881160/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "hexin-v": "A8KlBtusEcYFfQ2aigv4OairE8Mhk8SaeJa61gzb7ZTh7mx99CMWvUgnCuLf",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "cookie": ths_cookie
    }
    url = f"https://q.10jqka.com.cn/thshy/detail/field/199112/order/desc/page/1/ajax/1/code/{symbol}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "lxml")
    url_flag = "thshy"
    if soup.find(name="td", attrs={"colspan": "14"}):
        new_url = f"https://q.10jqka.com.cn/gn/detail/field/199112/order/desc/page/1/ajax/1/code/{symbol}"
        r = requests.get(new_url, headers=headers)
        soup = BeautifulSoup(r.text, features="lxml")
        url_flag = "gn"
    try:
        page_num = int(
            soup.find_all(name="a", attrs={"class": "changePage"})[-1]["page"]
        )
    except IndexError:
        page_num = 1
    big_df = pd.DataFrame()
    tqdm = get_tqdm()
    for page in tqdm(range(1, page_num + 1), leave=False):
        try:
            time.sleep(2)
            new_url = f"https://q.10jqka.com.cn/{url_flag}/detail/field/199112/order/desc/page/{page}/ajax/1/code/{symbol}"
            r_detail = requests.get(new_url, headers=headers)
            if r_detail.status_code == 200:
                temp_df = pd.read_html(StringIO(r_detail.text))[0]
                big_df = pd.concat(objs=[big_df, temp_df], ignore_index=True)
        except BaseException as e:
            logger.error("获取概念详细信息异常:{},{}", symbol, e)
    big_df.rename(
        {
            "涨跌幅(%)": "涨跌幅",
            "涨速(%)": "涨速",
            "换手(%)": "换手",
            "振幅(%)": "振幅",
        },
        inplace=True,
        axis=1,
    )
    if '加自选' in big_df.columns:
        del big_df["加自选"]
    if '代码' not in big_df.columns:
        return None
    big_df["代码"] = big_df["代码"].astype(str).str.zfill(6)
    if data_frame_util.is_not_empty(big_df):
        big_df.rename(columns={"序号": "index",
                               "代码": "symbol",
                               "名称": "name",
                               "现价": "now_price",
                               "涨跌幅": "chg",
                               "涨跌": "change",
                               "涨速": "r_increase",
                               "换手": "exchange",
                               "量比": "q_ratio",
                               "振幅": "pct_chg",
                               "成交额": "amount",
                               "流通股": "tradable_shares",
                               "流通市值": "flow_mv",
                               "市盈率": "pe"
                               }, inplace=True)
        stock_board_cons_ths_df = big_df[
            big_df["index"] != '暂无成份股数据']

        if stock_board_cons_ths_df is None or stock_board_cons_ths_df.shape[0] == 0:
            return
        length = len(list(stock_board_cons_ths_df))
        stock_board_cons_ths_df.insert(length, 'concept_code', symbol)

        stock_board_cons_ths_df['amount'] = stock_board_cons_ths_df['amount'].apply(
            lambda x: pd.to_numeric(x.replace('亿', ''), errors="coerce"))

        stock_board_cons_ths_df['tradable_shares'] = stock_board_cons_ths_df['tradable_shares'].apply(
            lambda x: pd.to_numeric(x.replace('亿', ''), errors="coerce"))

        stock_board_cons_ths_df['flow_mv'] = stock_board_cons_ths_df['flow_mv'].apply(
            lambda x: pd.to_numeric(x.replace('亿', ''), errors="coerce"))
    return stock_board_cons_ths_df


if __name__ == '__main__':
    concept_df = stock_board_cons_ths('886076')

    print(concept_df)
