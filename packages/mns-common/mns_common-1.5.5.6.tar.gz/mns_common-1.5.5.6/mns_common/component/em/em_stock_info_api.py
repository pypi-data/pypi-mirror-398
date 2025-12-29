import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.extra_income_db_name as extra_income_db_name

mongodb_util = MongodbUtil('27017')


# 获取东方财富A股全部信息
def get_a_stock_info():
    em_a_stock_info = mongodb_util.find_all_data(extra_income_db_name.EM_A_STOCK_INFO)
    em_a_stock_info = em_a_stock_info[~em_a_stock_info['symbol'].str.startswith(('8', '4'))]
    return em_a_stock_info


# 获取东方财富ETF全部信息
def get_etf_info():
    return mongodb_util.find_all_data(extra_income_db_name.EM_ETF_INFO)


# 获取东方财富可转债全部信息
def get_kzz_info():
    return mongodb_util.find_all_data(extra_income_db_name.EM_KZZ_INFO)


# 获取东方财富美股全部信息
def get_us_stock_info():
    return mongodb_util.find_all_data(extra_income_db_name.EM_US_STOCK_INFO)


# 获取东方财富美股 eft全部信息
def get_us_etf_info():
    return mongodb_util.find_all_data(extra_income_db_name.EM_US_ETF_INFO)


# 获取东方财富港股全部信息

def get_hk_stock_info():
    return mongodb_util.find_all_data(extra_income_db_name.EM_HK_STOCK_INFO)


if __name__ == '__main__':
    get_a_stock_info()