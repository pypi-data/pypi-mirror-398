import sys
import os
import requests
import pandas as pd
import threading
from loguru import logger
import mns_common.api.kpl.symbol.kpl_symbol_common_field_constant as kpl_symbol_common_field_constant
import mns_common.utils.data_frame_util as data_frame_util

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = pd.DataFrame()

MAX_PAGE_NUMBER = 60


# 定义一个函数用于获取接口数据
def fetch_data(page_number, end_date):
    global result
    index = page_number * MAX_PAGE_NUMBER

    # url = "https://apphq.longhuvip.com/w1/api/index.php?" \
    #       "Filter=0&FilterGem=0&FilterMotherboard=0&FilterTIB=0&Isst=0&Order=1&" \
    #       "PhoneOSNew=2&Ratio=6&Type=1&VerSion=5.11.0.3&a=RealRankingInfo_W8&apiv=w33&c=NewStockRanking&index=" \
    #       + str(index) + \
    #       "&st=" + str(MAX_PAGE_NUMBER)

    # url = "https://apphq.longhuvip.com/w1/api/index.php?Filter=0&FilterGem=0&FilterMotherboard=0" \
    #       "&FilterTIB=0&Isst=0&Order=1&PhoneOSNew=2&Ratio=6&Type=1&VerSion=5.11.0.3" \
    #       "&a=RealRankingInfo_W8&apiv=w33&c=NewStockRanking" \
    #       "&index=" + str(index) + \
    #       "&st=" + str(MAX_PAGE_NUMBER)

    url = "https://apphq.longhuvip.com/w1/api/index.php?Filter=0&FilterGem=0&FilterMotherboard=0" \
          "&FilterTIB=0&Isst=0&Order=1&PhoneOSNew=2&REnd=" + end_date + \
          "&RStart=0925&Ratio=6&Type=1&VerSion=5.11.0.3" \
          "&a=RealRankingInfo_W8&apiv=w33&c=NewStockRanking&" \
          "index=0" + str(index) + \
          "&st=" + str(MAX_PAGE_NUMBER)

    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    r = requests.get(url, headers=headers)
    data_json = r.json()
    data_list = data_json['list']
    data_df = pd.DataFrame(data_list)

    with result_lock:
        # 使用锁来保护 result 变量的访问，将每页的数据添加到结果中
        try:
            if data_frame_util.is_not_empty(data_df):
                result = pd.concat([result, data_df], ignore_index=True)
        except BaseException as e:
            logger.error("同步开盘啦数据异常:{}", e)
            return None


def get_stock_count(end_date):
    url = "https://apphq.longhuvip.com/w1/api/index.php?Filter=0&FilterGem=0&FilterMotherboard=0" \
          "&FilterTIB=0&Isst=0&Order=1&PhoneOSNew=2&REnd=" + end_date + \
          "&RStart=0925&Ratio=6&Type=1&VerSion=5.11.0.3" \
          "&a=RealRankingInfo_W8&apiv=w33&c=NewStockRanking&index=0&st=20"

    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    r = requests.get(url, headers=headers)
    data_json = r.json()

    return data_json['Count']


# 获取当期交易股票的数量
def sync_real_time_quotes(count, end_date):
    global result
    result = pd.DataFrame()  # 重新初始化 result 变量
    threads = []
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        thread = threading.Thread(target=fetch_data, args=(page, end_date,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 返回获取的接口数据

    kpl_real_time_quotes_df = kpl_symbol_common_field_constant.rename_kpl_real_time_quotes(result)
    kpl_real_time_quotes_df = kpl_real_time_quotes_df[kpl_symbol_common_field_constant.CHOOSE_FIELD]

    return kpl_real_time_quotes_df


def get_kpl_real_time_quotes():
    try:
        end_date = '1500'
        symbol_count = get_stock_count(end_date)
        return sync_real_time_quotes(symbol_count, end_date)

    except BaseException as e:
        logger.error("同步开盘啦数据异常:{}", e)
        return None


#### todo 拿不到实时数据 只能五分钟拿一次
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')

if __name__ == '__main__':
    df = get_kpl_real_time_quotes()

    fetch_data(1, '1500')
    # end_date = '1110'
    # count = get_stock_count(end_date)
    # number = 1
    # while True:
    #     logger.info(number)
    #     result = sync_real_time_quotes(count, end_date)
    #     result = result.sort_values(by=['main_flow_net'], ascending=False)
    #     # mongodb_util.drop_collection('kpl_real_time_quotes')
    #     # mongodb_util.insert_mongo(result, 'kpl_real_time_quotes')
    #     logger.info(result)
    #
    #     number = number + 1
