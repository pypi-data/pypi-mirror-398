import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import pandas as pd
import requests
from bs4 import BeautifulSoup


# 获取股票基本信息
# https://basic.10jqka.com.cn/mobile/301016/companyprofilen.html?showtab=1&broker=anelicaiapp
def get_company_info(symbol: str = "688272") -> pd.DataFrame:
    url = f"http://basic.10jqka.com.cn/mobile/{symbol}/companyprofilen.html?broker=pingan"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 iOS AYLCAPP/9.1.2.0/h4526a24eb9445522492fd64caae11b1f scheme/anelicaiapp deviceinfo/I|9.1.2.0|NA|h4526a24eb9445522492fd64caae11b1f pastheme/0",
        "Cookie": "ps_login_app_name=AYLCAPP;ps_login_token_id=N_C993F777ACC500B354C762A2627A8862348FC8163799A08EBEB2301C28A2135D220475787D0E81425C1134E15D8CC8761D639FEDBD46C00FE8EA6482C1E42D9801B19918FB3F5C34;ps_login_union_id=edc29089a2b64e3882062297030a0386;PAS.CURRENTUNIONID=edc29089a2b64e3882062297030a0386"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content.decode("utf-8"), 'lxml')
    soup.find('table', attrs={'class': 'leveldatail-tab'}).find_all('tr')
    temp_df = pd.read_html(r.content)[0]
    temp_df = temp_df.T
    temp_df = temp_df.iloc[1:2]
    temp_df.rename(columns={
        0: "name",
        1: "former_name",
        2: "registered_address",
        3: "chairman",
        4: "board_secretary",
        5: "main_business",
        6: "company_type",
        7: "controlling_shareholder",
        8: "actual_controller",
        9: "ultimate_controller",
        10: "list_date",
        11: "issue_price",
        12: "number_workers",
        13: "tel",
        14: "url",
        15: "email"
    }, inplace=True)

    return temp_df


# 获取股票详细信息
# HK市场 https://basic.10jqka.com.cn/mobile/HK1456/profile.html  https://basic.10jqka.com.cn/mobile/HK1456/company.html
# https://basic.10jqka.com.cn/new/HK1456/company.html
# https://basic.10jqka.com.cn/astockph/briefinfo/index.html?showhead=0&fromshare=1&code=300430&marketid=33&client_userid=ESgcM&back_source=hyperlink&share_hxapp=isc&fontzoom=no#/company/ziliao
def get_company_info_detail(symbol: str = "688272", market_id: str = "31") -> pd.DataFrame:
    url = f'https://basic.10jqka.com.cn/basicapi/company_info/merge_info/v1/base_info/?code={symbol}&market={market_id}&type=stock'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Host': 'basic.10jqka.com.cn',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cookie': 'v=A0CN8EBXN21LtMtpV6ldAxf6Ec8XySSbxq14l7rRDNvuNe77Ytn0Ixa9SDQJ',
        'Upgrade-Insecure-Requests': '1',

    }
    r = requests.get(url, headers=headers)
    data_json = r.json()
    status_code = data_json['status_code']
    status_msg = data_json['status_msg']
    if status_code != 0 or status_msg != 'success':
        logger.error("获取symbol公司详细信息异常:{}", symbol)
        return pd.DataFrame()
    if len(data_json['data']['industry']) == 0:
        return pd.DataFrame()
    data_df = pd.DataFrame(data_json['data']['industry'], index=[0])
    data_df = data_df[[
        'hy',
        'hycode',
        'hy2',
        'hy2code',
        'hy3',
        'hy3code',
    ]]

    business_nature = data_json['data']['business_nature']
    name = data_json['data']['code_name']
    intro = data_json['data']['intro']
    base_business = data_json['data']['base_business']

    address = data_json['data']['address']
    data_df['symbol'] = symbol
    data_df['name'] = name

    data_df['business_nature'] = business_nature

    if len(data_json['data']['management']['holder_controller']) > 0:
        holder_controller = pd.DataFrame(data_json['data']['management']['holder_controller'])
        holder_controller_name = str(list(holder_controller['name'])).strip('[').strip(']').replace("'", "")
        holder_controller_rate = holder_controller['rate']
        data_df['holder_controller_name'] = holder_controller_name
        data_df['holder_controller_rate'] = sum(holder_controller_rate)
    else:
        data_df['holder_controller_name'] = '暂无'
        data_df['holder_controller_rate'] = 0
    if len(data_json['data']['management']['final_controller']) > 0:
        final_controller = pd.DataFrame(data_json['data']['management']['final_controller'])
        final_controller_name = str(list(final_controller['name'])).strip('[').strip(']').replace("'", "")
        final_controller_rate = sum(final_controller['rate'])
        data_df['final_controller_name'] = final_controller_name
        data_df['final_controller_rate'] = final_controller_rate
    else:
        data_df['final_controller_name'] = '暂无'
        data_df['final_controller_rate'] = 0
    if len(data_json['data']['management']['actual_controller']) > 0:
        actual_controller = pd.DataFrame(data_json['data']['management']['actual_controller'])
        actual_controller_name = str(list(actual_controller['name'])).strip('[').strip(']').replace("'", "")
        actual_controller_rate = sum(actual_controller['rate'])
        data_df['actual_controller_name'] = actual_controller_name
        data_df['actual_controller_rate'] = actual_controller_rate
    else:
        data_df['actual_controller_name'] = '暂无'
        data_df['actual_controller_rate'] = 0

    data_df['base_business'] = base_business
    data_df['intro'] = intro
    data_df['address'] = address
    market_id = data_json['data']['market_id']
    data_df['market_id'] = market_id
    # 初始化数据
    data_df['main_business_list'] = [[]]
    data_df['most_profitable_business'] = ''
    data_df['most_profitable_business_rate'] = ''
    data_df['most_profitable_business_profit'] = ''

    # 业务构成
    main_business_list = data_json['data']['main_business']

    if len(main_business_list) > 0:
        # 最盈利业务
        profitable_business = data_json['data']['profitable_business']

        data_df['main_business_list'] = [main_business_list]

        most_profitable_business = profitable_business['name']

        most_profitable_business_rate = profitable_business['profit_rate']

        most_profitable_business_profit = profitable_business['profit']

        data_df['most_profitable_business'] = most_profitable_business
        data_df['most_profitable_business_rate'] = most_profitable_business_rate
        data_df['most_profitable_business_profit'] = most_profitable_business_profit
    return data_df


if __name__ == '__main__':
    get_company_info_detail('603683','17')
