from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from py_mini_racer import py_mini_racer
from akshare.utils.tqdm import get_tqdm
from loguru import logger
import mns_common.api.ths.concept.web.ths_common_js_api as ths_common_js_api

'''
   同花顺-数据中心-资金流向-概念资金流
'''


def stock_fund_flow_concept(symbol: str = "即时") -> pd.DataFrame:
    """
    同花顺-数据中心-资金流向-概念资金流
    https://data.10jqka.com.cn/funds/gnzjl/#refCountId=data_55f13c2c_254
    :param symbol: choice of {“即时”, "3日排行", "5日排行", "10日排行", "20日排行"}
    :type symbol: str
    :return: 概念资金流
    :rtype: pandas.DataFrame
    """
    try:
        js_code = py_mini_racer.MiniRacer()
        js_content = ths_common_js_api.get_file_content_ths()
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
            "Referer": "http://data.10jqka.com.cn/funds/gnzjl/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        url = (
            "http://data.10jqka.com.cn/funds/gnzjl/field/tradezdf/order/desc/ajax/1/free/1/"
        )
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "lxml")
        raw_page = soup.find("span", attrs={"class": "page_info"}).text
        page_num = raw_page.split("/")[1]
        if symbol == "3日排行":
            url = "http://data.10jqka.com.cn/funds/gnzjl/board/3/field/tradezdf/order/desc/page/{}/ajax/1/free/1/"
        elif symbol == "5日排行":
            url = "http://data.10jqka.com.cn/funds/gnzjl/board/5/field/tradezdf/order/desc/page/{}/ajax/1/free/1/"
        elif symbol == "10日排行":
            url = "http://data.10jqka.com.cn/funds/gnzjl/board/10/field/tradezdf/order/desc/page/{}/ajax/1/free/1/"
        elif symbol == "20日排行":
            url = "http://data.10jqka.com.cn/funds/gnzjl/board/20/field/tradezdf/order/desc/page/{}/ajax/1/free/1/"
        else:
            url = "http://data.10jqka.com.cn/funds/gnzjl/field/tradezdf/order/desc/page/{}/ajax/1/free/1/"
        big_df = pd.DataFrame()
        tqdm = get_tqdm()
        for page in tqdm(range(1, int(page_num) + 1), leave=False):
            js_code = py_mini_racer.MiniRacer()
            js_content = ths_common_js_api.get_file_content_ths()
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
                "Referer": "http://data.10jqka.com.cn/funds/gnzjl/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
            }
            r = requests.get(url.format(page), headers=headers)
            temp_df = pd.read_html(StringIO(r.text))[0]
            big_df = pd.concat([big_df, temp_df], ignore_index=True)

        del big_df["序号"]
        big_df.reset_index(inplace=True)
        big_df["index"] = range(1, len(big_df) + 1)
        if symbol == "即时":
            big_df.columns = [
                "序号",
                "行业",
                "行业指数",
                "行业-涨跌幅",
                "流入资金",
                "流出资金",
                "净额",
                "公司家数",
                "领涨股",
                "领涨股-涨跌幅",
                "当前价",
            ]
            big_df["行业-涨跌幅"] = big_df["行业-涨跌幅"].str.strip("%")
            big_df["领涨股-涨跌幅"] = big_df["领涨股-涨跌幅"].str.strip("%")
            big_df["行业-涨跌幅"] = pd.to_numeric(big_df["行业-涨跌幅"], errors="coerce")
            big_df["领涨股-涨跌幅"] = pd.to_numeric(big_df["领涨股-涨跌幅"], errors="coerce")
        else:
            big_df.columns = [
                "序号",
                "行业",
                "公司家数",
                "行业指数",
                "阶段涨跌幅",
                "流入资金",
                "流出资金",
                "净额",
            ]

        stock_fund_flow_concept_df = big_df.rename(columns={
            "序号": "index",
            "行业": "concept_name",
            "行业指数": "concept_index",
            "行业-涨跌幅": "concept_chg",
            "流入资金": "inflows",
            "流出资金": "outflow",
            "净额": "netflow",
            "公司家数": "company_num",
            "领涨股": "leading_stock",
            "领涨股-涨跌幅": "leading_chg",
            "当前价": "now_price",
        })
        return stock_fund_flow_concept_df
    except BaseException as e:
        logger.error("获取概念资金流信息异常:{}", e)


# 获取概念名称信息
def get_concept_name(symbol: str = "881121") -> pd.DataFrame:
    try:
        url = f"http://q.10jqka.com.cn/thshy/detail/code/{symbol}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 iOS AYLCAPP/9.1.2.0/h4526a24eb9445522492fd64caae11b1f scheme/anelicaiapp deviceinfo/I|9.1.2.0|NA|h4526a24eb9445522492fd64caae11b1f pastheme/0",
            "Cookie": "ps_login_app_name=AYLCAPP;ps_login_token_id=N_C993F777ACC500B354C762A2627A8862348FC8163799A08EBEB2301C28A2135D220475787D0E81425C1134E15D8CC8761D639FEDBD46C00FE8EA6482C1E42D9801B19918FB3F5C34;ps_login_union_id=edc29089a2b64e3882062297030a0386;PAS.CURRENTUNIONID=edc29089a2b64e3882062297030a0386"
        }
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content.decode("gbk"), 'lxml')
        temp_df = soup.find(attrs={'class': 'board-hq'}).find_all('h3')
        temp_df = str(temp_df)
        start_index = temp_df.index('[<h3>')
        if start_index >= 0:
            start_index += len('[<h3>')
        end_index = temp_df.index('<span>')
        concept_name = temp_df[start_index:end_index]
        return concept_name

    except BaseException as e:
        logger.error("获取symbol基本信息异常:{},{}", symbol, e)


if __name__ == '__main__':
    stock_fund_flow_concept = stock_fund_flow_concept()
    print(stock_fund_flow_concept)
