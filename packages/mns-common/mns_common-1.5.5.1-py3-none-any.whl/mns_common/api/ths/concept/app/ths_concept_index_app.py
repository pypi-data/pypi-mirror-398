import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger

import requests
import pandas as pd

'''
begin_time:开始时间  只能是交易时间
end_time: 结束时间 只能是交易时间
page_size:分页大小
type: 类型 1:行业 2 概念  3 风格 4 地域
地址:https://eq.10jqka.com.cn/webpage/sector-retrospect/home.html#/
'''


# 获取同花顺概念概念历史详情
def get_ths_concept_his_info(begin_time, end_time, page_size, query_type):
    url = "https://dq.10jqka.com.cn/interval_calculation/block_info/v1/get_block_list"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "192",
        "Content-Type": "application/json",
        "Cookie": "searchGuide=sg; historystock=301041%7C*%7C002156; "
                  "Hm_lvt_722143063e4892925903024537075d0d=1717667296,1718442548; "
                  "Hm_lpvt_722143063e4892925903024537075d0d=1718442548; "
                  "Hm_lvt_929f8b362150b1f77b477230541dbbc2=1717667296,1718442548; "
                  "Hm_lpvt_929f8b362150b1f77b477230541dbbc2=1718442548; "
                  "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1717667297,1718105758,1718442548; "
                  "Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1718442548;"
                  " u_ukey=A10702B8689642C6BE607730E11E6E4A;"
                  " u_uver=1.0.0; "
                  "u_dpass=FiQNmw4Vyp2vyGzE6%2FEbtrgPtUViMbFi%2BSUJ1bTSIaqQP7Dl6EmBT0Xu4HBksFjJHi80LrSsTFH9a%2B6rtRvqGg%3D%3D; "
                  "u_did=0112000691F9476ABA607A0E4F06AF9B; "
                  "u_ttype=WEB; user=MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoyNzo6OjYwMzk4NTQ0ODoxNzE4NDQyNTkzOjo6MTYzNDU2Njk4MDo4NjQwMDowOjE5NjMyMzc1ZWNjOGUzNTJmYTczMmFhZjM4OTg3ZGMzNDpkZWZhdWx0XzQ6MQ%3D%3D;"
                  " userid=603985669;"
                  " u_name=jack_love_michael; "
                  "escapename=%25u666f%25u884cpM; "
                  "ticket=092428c703980b80d5d407acddb6b474; "
                  "user_status=0; "
                  "utk=628aa7def3a67c0b3c66869803ab9e23;"
                  " v=AwEzs-sjAz2MWm8JVzGy7KH9FkYeLnSXn6cZXGNX-e9nci-4q36F8C_yKQ3w",
        "Host": "dq.10jqka.com.cn",
        "Origin": "https://eq.10jqka.com.cn",
        "Referer": "https://eq.10jqka.com.cn/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\""
    }

    payload = {
        "type": query_type,
        "history_info": {
            "history_type": "0",
            "start_date": begin_time,
            "end_date": end_time
        },
        "page_info": {
            "page": 1,
            "page_size": page_size
        },
        "sort_info": {
            "sort_field": "0",
            "sort_type": "desc"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        result_json = response.json()
        status_code = result_json['status_code']
        status_msg = result_json['status_msg']
        if status_code == 0 and status_msg == 'success':
            result_list = result_json['data']['list']
            result_total = result_json['data']['total']
            result_df = pd.DataFrame(result_list)
            result_df.fillna(0, inplace=True)
            result_df['chg'] = round(result_df['margin_of_increase'] * 100, 2)
            del result_df['margin_of_increase']
            result_df['result_total'] = result_total
            return result_df
        else:
            return None
    except BaseException as e:
        logger.error("获取ths板块信息异常:{},{},{}", e, query_type, begin_time)
        return None


# 获取同花顺APP 端搜索概念结果
def get_new_concept_from_app_search(symbol: str = "886019"):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cookie': 'v=A2A7Vv5CF9c_javTJ4_ZJx3_N283aUQt5k2YN9pxLHsO1Q5bgnkUwzZdaMEp; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1668578108',
        'Host': 'd.10jqka.com.cn',
        'If-Modified-Since': "Wed, 16 Nov 2022 09:31:32 GMT",
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:106.0) Gecko/20100101 Firefox/106.0",

    }
    # userId 随便写 https://dict.hexin.cn:9531/stocks?pattern=886019&isauto=1&associate=1&pl=i&isrealcode=1&json=1&br=sc&style=1&userid=656258250&markettype=2	200	GET	dict.hexin.cn:9531	/stocks?pattern=886019&isauto=1&associate=1&pl=i&isrealcode=1&json=1&br=sc&style=1&userid=656258250&markettype=2
    url = f'https://dict.hexin.cn:9531/stocks?pattern={symbol}&isauto=1&associate=1&pl=i&isrealcode=1&json=1&br=sc&style=1&userid=603985000&markettype=2'

    try:
        r = requests.get(url, headers)
        data_json = r.json()
        type = data_json['type']
        if type == '0':

            body_list = data_json['data']['body']
            search_concept_code = body_list[0][0]
            search_concept_name = body_list[0][1]
            if str(symbol) == str(search_concept_code):
                concept_dict = {
                    'concept_code': int(search_concept_code),
                    'concept_name': search_concept_name
                }
                concept_df = pd.DataFrame([concept_dict], index=[0])

                return concept_df
            else:
                return None
        else:
            return None

    except BaseException as e:
        logger.error("获取新概念信息异常:{}", e)
        return None


from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
if __name__ == '__main__':
    get_new_concept_from_app_search('886104')

    end_time_test = '20241011093500'
    result_df_test = get_ths_concept_his_info('20241011093000', end_time_test, 500, 2)
    result_df_test['block_code'] = result_df_test['block_code'].astype(int)
    result_df_test['_id'] = result_df_test['block_code']

    mongodb_util.save_mongo(result_df_test, 'ths_concept_info')

    exist_ths_concept_list = mongodb_util.find_all_data('ths_concept_list')
    not_in_exist_list = result_df_test.loc[~(result_df_test['block_code'].isin(exist_ths_concept_list['symbol']))]
    mongodb_util.save_mongo(not_in_exist_list, 'not_in_exist_list')
    print(result_df_test)

    # while True:
    #     now_date = datetime.now()
    #     str_day = now_date.strftime('%Y%m%d')
    #     hour = now_date.hour
    #     minute = now_date.minute
    #     second = now_date.second
    #     second = 0
    #     if hour < 10:
    #         hour = '0' + str(hour)
    #     if minute < 10:
    #         minute = '0' + str(minute)
    #     if second < 10:
    #         second = '0' + str(second)
    #
    #     end_time_test = str_day + str(hour) + str(minute) + str(second)
    #     end_time_test = str(end_time_test)
    #
    #     result_df_test = get_ths_concept_his_info('20241008093000', end_time_test, 500, 2)
    #     print(result_df_test)
    # search_result = get_new_concept_from_app_search('886078')
    # print(search_result)
