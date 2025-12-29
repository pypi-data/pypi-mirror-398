import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')


@lru_cache(maxsize=None)
def get_hk_company_info():
    return mongodb_util.find_query_data(db_name_constant.COMPANY_INFO_HK,
                                        {})


@lru_cache(maxsize=None)
def get_hk_company_industry_info():
    query_field = {'_id': 1,
                   'industry': 1,
                   'number': 1}
    return mongodb_util.find_query_data_choose_field(db_name_constant.HK_COMPANY_INDUSTRY,
                                                     {}, query_field)
