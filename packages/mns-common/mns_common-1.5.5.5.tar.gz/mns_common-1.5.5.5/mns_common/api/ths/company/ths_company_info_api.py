import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger


# 获取参股公司 子公司 孙公司 联营企业
def get_company_hold_info(symbol, ths_cookie):
    try:

        url = "https://basic.10jqka.com.cn/new/" + symbol + "/company.html"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "cookie": ths_cookie
        }
        cookies = {
            "searchGuide": "sg",
            "skin_color": "white",
            "Hm_lvt_722143063e4892925903024537075d0d": "1725031809,1725842892,1726621825,1727227162",
            "Hm_lvt_929f8b362150b1f77b477230541dbbc2": "1725031809,1725842892,1726621825,1727227162",
            "spversion": "20130314",
            "user": "MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo1LDEsMjA7NiwxLDIwOzcsMTExMTExMTExMTEwLDIwOzgsMTExMTAxMTEwMDAwMTExMTEwMDEwMDEwMDEwMDAwMDAsMjA7MzMsMDAwMTAwMDAwMDAwLDIwOzM2LDEwMDExMTExMDAwMDExMDAxMDExMTExMSwyMDs0NiwwMDAwMTExMTEwMDAwMDExMTExMTExMTEsMjA7NTEsMTEwMDAwMDAwMDAwMDAwMCwyMDs1OCwwMDAwMDAwMDAwMDAwMDAwMSwyMDs3OCwxLDIwOzg3LDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMCwyMDsxMTksMDAwMDAwMDAwMDAwMDAwMDAwMTAxMDAwMDAsMjA7MTI1LDExLDIwOzQ0LDExLDQwOzEsMTAxLDQwOzIsMSw0MDszLDEsNDA7MTAyLDEsNDA6Mjc6Ojo2MDM5ODU0NDg6MTcyODQ4NzEyNjo6OjE2MzQ1NjY5ODA6NjA0ODAwOjA6MTRhZjIxYmRiNTgzODUxOTgxZWVjZGQ4NjQxZjA2NDg5OmRlZmF1bHRfNDox",
            "userid": "603985448",
            "u_name": "%BE%B0%D0%D0pM",
            "escapename": "%25u666f%25u884cpM",
            "ticket": "955f0ee44d86aede75787f64ae45bae9",
            "user_status": "0",
            "utk": "2df15e757efe7d4a489cf764fa371ff9",
            "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1": "1728463065,1728526291,1728541890,1728550124",
            "historystock": "301551%7C*%7C002205%7C*%7C000627%7C*%7C300746%7C*%7C300139",
            "reviewJump": "nojump",
            "usersurvey": "1",
            "v": "A8mumxxpynGwb7YF90Bxvvav2P4mFrxUJwzh32s-RzXtX-dgs2bNGLda8aj4"
        }
        response = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(response.content, "lxml")

        # 找到表格
        table = soup.find('table', id='ckg_table')

        # 提取表头
        table_headers = [header.get_text(strip=True) for header in table.find_all('th')]

        # 提取表格数据
        data = []
        for row in table.find_all('tr')[1:]:  # 跳过表头
            cells = [cell.get_text(strip=True) for cell in row.find_all('td')]
            if cells:  # 确保行不为空
                data.append(cells)

        # 创建 DataFrame
        df = pd.DataFrame(data, columns=table_headers)
        if data_frame_util.is_empty(df):
            return pd.DataFrame()
        del df['序号']

        ['序号', '关联公司名称', '参控关系', '参控比例', '投资金额(元)', '被参控公司净利润(元)', '是否报表合并',
         '被参股公司主营业务']

        df = df.rename(columns={"关联公司名称": "holding_company",
                                "参控关系": "holding_relation",
                                "参控比例": "holding_percent_name",
                                "投资金额(元)": "invest_amount_name",
                                "被参控公司净利润(元)": "holding_net_profit_name",
                                "是否报表合并": "consolidation_report",
                                "被参股公司主营业务": "holding_main_business"
                                })
        df['holding_percent'] = df['holding_percent_name'].apply(convert_to_float)
        df['invest_amount'] = df['invest_amount_name'].apply(convert_to_float)
        df['holding_net_profit'] = df['holding_net_profit_name'].apply(convert_to_float)
        df['symbol'] = symbol

        return df
    except BaseException as e:
        logger.error("获取公司参股公司信息异常:{},{}", symbol, e)
        return pd.DataFrame()


# 数据清洗与转换
# 定义一个函数将带有单位的字符串转换为数字
def convert_to_float(value):
    if '亿' in value:
        return float(value.replace('亿', '').replace(' ', '').replace('元', '')) * 1e8
    elif '%' in value:
        return float(value.replace('%', '').replace(' ', '')) / 100
    elif '万' in value:
        return float(value.replace('万', '').replace(' ', '').replace('元', '')) * 1e4
    elif '未披露' in value:
        return 0
    return -1


# 获取公司热点
def get_company_hot_info(symbol, ths_cookie):
    try:

        url = "https://basic.10jqka.com.cn/new/" + symbol + "/"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "cookie": ths_cookie
        }
        cookies = {
            "searchGuide": "sg",
            "skin_color": "white",
            "Hm_lvt_722143063e4892925903024537075d0d": "1725031809,1725842892,1726621825,1727227162",
            "Hm_lvt_929f8b362150b1f77b477230541dbbc2": "1725031809,1725842892,1726621825,1727227162",
            "spversion": "20130314",
            "user": "MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo1LDEsMjA7NiwxLDIwOzcsMTExMTExMTExMTEwLDIwOzgsMTExMTAxMTEwMDAwMTExMTEwMDEwMDEwMDEwMDAwMDAsMjA7MzMsMDAwMTAwMDAwMDAwLDIwOzM2LDEwMDExMTExMDAwMDExMDAxMDExMTExMSwyMDs0NiwwMDAwMTExMTEwMDAwMDExMTExMTExMTEsMjA7NTEsMTEwMDAwMDAwMDAwMDAwMCwyMDs1OCwwMDAwMDAwMDAwMDAwMDAwMSwyMDs3OCwxLDIwOzg3LDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMCwyMDsxMTksMDAwMDAwMDAwMDAwMDAwMDAwMTAxMDAwMDAsMjA7MTI1LDExLDIwOzQ0LDExLDQwOzEsMTAxLDQwOzIsMSw0MDszLDEsNDA7MTAyLDEsNDA6Mjc6Ojo2MDM5ODU0NDg6MTcyODQ4NzEyNjo6OjE2MzQ1NjY5ODA6NjA0ODAwOjA6MTRhZjIxYmRiNTgzODUxOTgxZWVjZGQ4NjQxZjA2NDg5OmRlZmF1bHRfNDox",
            "userid": "603985448",
            "u_name": "%BE%B0%D0%D0pM",
            "escapename": "%25u666f%25u884cpM",
            "ticket": "955f0ee44d86aede75787f64ae45bae9",
            "user_status": "0",
            "utk": "2df15e757efe7d4a489cf764fa371ff9",
            "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1": "1728463065,1728526291,1728541890,1728550124",
            "historystock": "301551%7C*%7C002205%7C*%7C000627%7C*%7C300746%7C*%7C300139",
            "reviewJump": "nojump",
            "usersurvey": "1",
            "v": "A8mumxxpynGwb7YF90Bxvvav2P4mFrxUJwzh32s-RzXtX-dgs2bNGLda8aj4"
        }
        response = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(response.content, "html.parser")
        analysis_txt = ''
        for a in soup.find_all("a", class_="check_details f12"):
            if "涨停分析" in a.get_text():
                # 找到其后的兄弟节点中 class 为 check_else 的 div，包含详细内容
                parent = a.find_parent("span", class_="performance_trailer")
                if parent:
                    detail_div = parent.find("div", class_="check_else")
                    if detail_div:
                        analysis_txt = detail_div.get_text(separator="\n", strip=True)
                        break  # 如果只要第一条，找到就结束
        return analysis_txt
    except BaseException as e:
        logger.error("获取公司参股公司信息异常:{},{}", symbol, e)
        return ''


from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
if __name__ == '__main__':
    stock_account_info = mongodb_util.find_query_data('stock_account_info', {"type": "ths_cookie", })
    ths_cookie_test = list(stock_account_info['cookie'])[0]
    company_df_test = get_company_hot_info('600756', ths_cookie_test)
    target_title = company_df_test.split("\n")[0]  # 关键修改：提取第一行
    print(company_df_test)
