import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')
import mns_common.constant.db_name_constant as db_name_constant
from functools import lru_cache


# 保存黑名单操作

def save_black_stock(
        id_key,
        symbol,
        name,
        str_day,
        str_now_date,
        choose_reason,
        choose_reason_detail,
        announce_url,
        up_level_code,
        up_level_name,
        level_code,
        level_name):
    query_exist = {'_id': id_key}
    if mongodb_util.exist_data_query(db_name_constant.SELF_BLACK_STOCK, query_exist):
        return
    black_choose_dict = {
        "_id": id_key,
        "symbol": symbol,
        "name": name,
        "str_day": str_day,
        "str_now_date": str_now_date,
        "choose_reason": choose_reason,
        "choose_reason_detail": choose_reason_detail,
        'announce_url': announce_url,
        'up_level_code': up_level_code,
        "up_level_name": up_level_name,
        "level_code": level_code,
        "level_name": level_name,
        'valid': True
    }
    black_choose_df = pd.DataFrame(black_choose_dict, index=[1])
    mongodb_util.save_mongo(black_choose_df, db_name_constant.SELF_BLACK_STOCK)


# 获取黑名单 列表
@lru_cache(maxsize=None)
def get_black_stock_list(begin_day):
    if begin_day is None:
        query = {"valid": True}
    else:
        query = {'str_day': {"$lte": begin_day}, "valid": True}
    self_black_stock_df = mongodb_util.find_query_data(db_name_constant.SELF_BLACK_STOCK, query)
    if data_frame_util.is_not_empty(self_black_stock_df):
        return list(self_black_stock_df['symbol'])
    else:
        return ['000001']
