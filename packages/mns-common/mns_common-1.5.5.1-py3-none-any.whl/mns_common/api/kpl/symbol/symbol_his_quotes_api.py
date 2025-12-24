import sys
import os
import requests
import threading
from loguru import logger

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.api.kpl.symbol.kpl_symbol_common_field_constant as kpl_symbol_common_field_constant

# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = pd.DataFrame()

MAX_PAGE_NUMBER = 60


def get_stock_count(str_day, page_number, begin, end):
    index = page_number * MAX_PAGE_NUMBER

    url = "https://apphis.longhuvip.com/w1/api/index.php?" + \
          "Date=" + str_day + \
          "&Filter=0&FilterGem=0&FilterMotherboard=0&FilterTIB=0" + \
          "&Isst=0&Order=1&PhoneOSNew=2" + \
          "&REnd=" + end + \
          "&RStart=" + begin + \
          "&Ratio=6&Type=1&VerSion=5.11.0.3&a=HisRankingInfo_W8&apiv=w33&c=HisStockRanking" + \
          "&index=" + str(index) + \
          "&st=" + str(MAX_PAGE_NUMBER)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    r = requests.get(url, headers=headers)
    data_json = r.json()
    return data_json['Count']


def get_stock_quotes_his(str_day, page_number, begin, end):
    global result
    index = page_number * MAX_PAGE_NUMBER

    url = ("https://apphis.longhuvip.com/w1/api/index.php?"
           "Date=" + str_day +
           "&Filter=0&FilterGem=0&FilterMotherboard=0&FilterTIB=0"
           "&Isst=0&Order=1&PhoneOSNew=2"
           "&REnd=" + end +
           "&RStart=" + begin +
           "&Ratio=6&Type=1&VerSion=5.11.0.3&a=HisRankingInfo_W8&apiv=w33&c=HisStockRanking"
           "&index=" + str(index) +
           "&st=" + str(MAX_PAGE_NUMBER)
           )

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    r = requests.get(url, headers=headers)
    try:
        data_json = r.json()
        data_list = data_json['list']
        data_df = pd.DataFrame(data_list)
    except BaseException as e:
        logger.error("出现异常:{},{},{},{},{}", str_day, page_number, begin, end, e)

    with result_lock:
        # 使用锁来保护 result 变量的访问，将每页的数据添加到结果中
        result = pd.concat([result, data_df], ignore_index=True)


def sync_stock_his_quotes(str_day, begin, end):
    count = get_stock_count(str_day, 0, begin, end)
    global result
    result = pd.DataFrame()  # 重新初始化 result 变量
    threads = []
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        thread = threading.Thread(target=get_stock_quotes_his, args=(str_day, page, begin, end))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 返回获取的接口数据
    result.columns = kpl_symbol_common_field_constant.SYNC_FIELD
    result = result[kpl_symbol_common_field_constant.CHOOSE_FIELD]
    result = result.sort_values(by=['chg'], ascending=False)
    return result


def his_test(str_day):
    url = ("https://apphis.longhuvip.com/w1/api/index.php?" + \
           "Date=" + str_day + \
           "&Filter=0&FilterGem=0&FilterMotherboard=0&FilterTIB=0&Isst=0&Order=1&PhoneOSNew=2&REnd=1315&RStart=1045&Ratio=6"
           "&Type=1&VerSion=5.11.0.3&a=HisRankingInfo_W8&apiv=w33&c=HisStockRanking&index=0&st=20")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    r = requests.get(url, headers=headers)
    data_json = r.json()
    return data_json['Count']


if __name__ == '__main__':
    # 2021-10-25,45,0925,0955 2023-09-15,11,0925,1005

    # get_stock_quotes_his('2023-09-20', 11, '0925', '1005')
    df = sync_stock_his_quotes('2025-04-18', '0935', '0940')
    get_stock_count('2023-09-14', 0, '0925', '1500')

    his_test('2021-10-20')
