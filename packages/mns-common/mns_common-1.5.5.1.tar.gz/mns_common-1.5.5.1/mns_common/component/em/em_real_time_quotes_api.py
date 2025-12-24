import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.db_util as db_util

mongodb_util = MongodbUtil('27017')


# 获取当天最新实时数据
def get_real_time_quotes_now(symbol_list, selected_date):
    db_name = db_name_constant.REAL_TIME_QUOTES_NOW
    if selected_date is not None:
        query_day = selected_date[0:10]
        db_name = db_name + '_' + query_day
        db_util_mongo = db_util.get_db(query_day)
        query = {'symbol': '000001'}
        query_field = {"str_now_date": 1, "number": 1, "symbol": 1}
        df = db_util_mongo.find_query_data_choose_field(db_name, query, query_field)
        if df is None or df.shape[0] == 0:
            number = 1
        else:
            df = df[df['str_now_date'] <= selected_date]
            df = df.sort_values(by=['str_now_date'], ascending=False)
            number = list(df['number'])[0]
            # 最新number数据可能还正在写库

        query = {'number': number}
        real_time_quotes_now = db_util_mongo.find_query_data(db_name, query)

    else:

        number = common_service_fun_api.realtime_quotes_now_max_number(db_name,
                                                                       'number')
        # 最新number数据可能还正在写库
        real_time_quotes_now = common_service_fun_api.get_last_new_real_time_data(
            db_name
            , number - 1)
    if (symbol_list is not None
            and data_frame_util.is_not_empty(real_time_quotes_now)):
        real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['symbol'].isin(symbol_list)]

    return real_time_quotes_now


if __name__ == '__main__':
    df = get_real_time_quotes_now(None, None)
    print(df)
