import sys
import os
import requests
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.kpl.common.kpl_common_api as kpl_common_api
from loguru import logger

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)


# 精选板块指数
def best_choose():
    try:
        return kpl_common_api.get_plate_index(kpl_common_api.BEST_CHOOSE)
    except Exception as e:
        logger.error("获取开盘啦指数异常:{}", e)
        return None


# 精选股票组成
# Order 排序参数
# st 分页最大数量
# index 股票排名index
def best_choose_stock(plate_code):
    return kpl_common_api.plate_detail_info(plate_code)


# 精选股票 组成详情 子版块
def best_choose_sub_index(plateId):
    url = (
            f" https://apphq.longhuvip.com/w1/api/index.php?DEnd=&Date=&PhoneOSNew=2"
            f"&PlateID=" + plateId +
            f"&VerSion=5.11.0.3&a=SonPlate_Info&apiv=w33&c=ZhiShuRanking")
    headers = {
        "User-Agent": "Content-Type: application/x-www-form-urlencoded; charset=utf-8"
    }
    r = requests.post(url, headers=headers)
    data_json = r.json()
    data_concept = data_json['List']
    data_df = pd.DataFrame(data_concept)
    if data_frame_util.is_empty(data_df):
        return None
    data_df.columns = [
        "plate_code",
        "plate_name",
        "heat_score"]
    return data_df


if __name__ == '__main__':
    # while True:
    #     df = best_choose()
    #     df = df[['plate_code', 'plate_name', 'heat_score', 'chg', 'amount']]
    #     print(df)
    df = best_choose_sub_index('801218')
    print(df)
    # df_detail = best_choose_stock('801511')
    # print(df_detail)
    # df_detail = df_detail.sort_values(by=['chg'], ascending=False)
    # print(df_detail)
