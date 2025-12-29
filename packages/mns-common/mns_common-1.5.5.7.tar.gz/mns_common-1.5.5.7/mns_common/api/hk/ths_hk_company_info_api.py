import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

import requests
from bs4 import BeautifulSoup
import pandas as pd
from loguru import logger


def get_hk_company_info(symbol, ths_cookie):
    symbol_copy = symbol
    symbol = symbol[1:5]
    symbol = "HK" + symbol
    url = "https://basic.10jqka.com.cn/new/" + symbol + "/company.html"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Referer": "https://basic.10jqka.com.cn/new/HK1456/news.html",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "cookie": ths_cookie
    }
    cookies = {
        "Hm_lvt_722143063e4892925903024537075d0d": "1728263496",
        "Hm_lvt_929f8b362150b1f77b477230541dbbc2": "1728263496",
        "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1": "1728263496",
        "u_ukey": "A10702B8689642C6BE607730E11E6E4A",
        "u_uver": "1.0.0",
        "u_dpass": "mZuXjNOJ5najLo9im8e7OFWfVDerAPcR%2F4NwI5iI52Z9Il1%2FHk%2FIWnu2ARoy1hTUHi80LrSsTFH9a%2B6rtRvqGg%3D%3D",
        "u_did": "5DC9AE36023C4F578A90F6BD333F757C",
        "u_ttype": "WEB",
        "ttype": "WEB",
        "user": "MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo1LDEsMjM7NiwxLDIzOzcsMTExMTExMTExMTEwLDIzOzgsMTExMTAxMTEwMDAwMTExMTEwMDEwMDEwMDEwMDAwMDAsMjM7MzMsMDAwMTAwMDAwMDAwLDIzOzM2LDEwMDExMTExMDAwMDExMDAxMDExMTExMSwyMzs0NiwwMDAwMTExMTEwMDAwMDExMTExMTExMTEsMjM7NTEsMTEwMDAwMDAwMDAwMDAwMCwyMzs1OCwwMDAwMDAwMDAwMDAwMDAwMSwyMzs3OCwxLDIzOzg3LDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMCwyMzsxMTksMDAwMDAwMDAwMDAwMDAwMDAwMTAxMDAwMDAsMjM7MTI1LDExLDIzOzQ0LDExLDQwOzEsMTAxLDQwOzIsMSw0MDszLDEsNDA7MTAyLDEsNDA6Mjc6Ojo2MDM5ODU0NDg6MTcyODI2MzUyMjo6OjE2MzQ1NjY5ODA6NjA0ODAwOjA6MTI4OGMyYzVhNjQ4OTBmNDM2MDE0YWM4NDkzMjA3ODFmOmRlZmF1bHRfNDox",
        "userid": "603985448",
        "u_name": "%BE%B0%D0%D0pM",
        "escapename": "%25u666f%25u884cpM",
        "ticket": "0ace7c286307aca34a80cbe0fb1d75a6",
        "user_status": "0",
        "utk": "9f7d91056c3e5b72e2559a2b45ba1e17",
        "reviewJump": "nojump",
        "searchGuide": "sg",
        "usersurvey": "1",
        "v": "A1DK4qi1A9ChlN_UVszdo2J-J5WnGTRlVv2IZ0ohHKt-hf6L8ikE86YNWPSZ",
        "reviewJumphk": "nojump"
    }

    response = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, "lxml")

    table_data_list = soup.find(attrs={'class': 'm_table'}).find_all('td')
    # 初始化一个空的字典，用于存储数据
    data = {}
    # 遍历每个单元格
    for cell in table_data_list:
        try:
            # 提取标题和内容
            strong_tag = cell.find('strong')
            span_tag = cell.find('span')

            if strong_tag and span_tag:
                key = strong_tag.get_text(strip=True).replace('：', '')  # 获取标题
                value = span_tag.get_text(strip=True)  # 获取内容

                # 将数据添加到字典中
                data[key] = value
        except BaseException as e:
            logger.error("转换公司信息异常:{}", e)

    # 将字典转换为 DataFrame
    company_hk_df = pd.DataFrame([data])
    company_hk_df.rename(columns={
        '公司名称': "company_name",
        '注册地址': "registered_address",
        '英文名称': "english_name",
        '所属行业': "industry",
        '公司成立日期 ': "list_date",
        '公司网址': "company_web_site",
        '主营业务': "main_business",
        '董 事 长': "chairman",
        '证券事务代表': "securities_representative",
        '员工人数': "employees",
        '核 数 师 ': "auditor",
        '法律顾问': "legal_adviser",
        '年 结 日 ': "closing_date",
        '电\u3000\u3000话': "telephone",
        '传\u3000\u3000真': "fax",
        '电\u3000\u3000邮': "e_mail",
        '办公地址': "office_address"
    }, inplace=True)
    company_detail = soup.find(attrs={'class': 'yellow tip lh24'})

    soup = BeautifulSoup(company_detail.next, 'html.parser')
    text = soup.text
    company_hk_df['company_detail'] = text
    company_hk_df['symbol'] = symbol_copy
    return company_hk_df


from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
if __name__ == '__main__':
    stock_account_info = mongodb_util.find_query_data('stock_account_info', {"type": "ths_cookie", })
    ths_cookie_test = list(stock_account_info['cookie'])[0]
    company_hk_df_test = get_hk_company_info('00839', ths_cookie_test)
    print(company_hk_df_test)
