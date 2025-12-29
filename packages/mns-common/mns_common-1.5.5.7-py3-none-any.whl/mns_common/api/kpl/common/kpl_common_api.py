import sys
import os
import requests

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.kpl.common.kpl_common_field_constant as kpl_common_field_constant
from loguru import logger

BEST_CHOOSE = '7'
AREA = '6'
CONCEPT = '5'
INDUSTRY = '4'

PAGE_MAX_COUNT = 80

HIS_PAGE_MAX_COUNT = 70


# index_type= 4 行业   index_type= 5 概念  index_type= 6 地域 ndex_type= 7 精选板块
def get_plate_index(index_type):
    result = pd.DataFrame()
    page_number = 0
    page_index = 0
    headers = {
        "User-Agent": "Content-Type: application/x-www-form-urlencoded; charset=utf-8"
    }
    while True:
        r = requests.post("https://apphq.longhuvip.com/w1/api/index.php?"
                          "Index=" + str(page_index) + "&Order=1&PhoneOSNew=2&Type=1&VerSion=5.13.0.3&ZSType="
                          + str(index_type) +
                          "&a=RealRankingInfo&apiv=w35&c=ZhiShuRanking&st="
                          + str(PAGE_MAX_COUNT), headers=headers)

        data_json = r.json()
        data_concept = data_json['list']
        data_df_plate = pd.DataFrame(data_concept)
        if data_frame_util.is_empty(data_df_plate):
            break
        data_df_plate = kpl_common_field_constant.rename_plate_index(data_df_plate)
        result = pd.concat([result, data_df_plate])
        if data_df_plate.shape[0] < PAGE_MAX_COUNT:
            break
        else:
            page_number = page_number + 1
            page_index = page_number * PAGE_MAX_COUNT

    return result


# 板块股票组成# 精选板块 # 行业板块

# Order 排序参数
# st 分页最大数量
# index 股票排名index
def plate_detail_info(plate_code):
    index = 0
    result = None
    while True:
        url = (
                f"https://apphq.longhuvip.com/w1/api/index.php?"
                f"Index=" + str(index) +
                f"&IsKZZType=0"
                f"&IsZZ=0"
                f"&Order=1"
                f"&PhoneOSNew=3"
                f"&PlateID=" + str(plate_code) +
                f"&Token=e4b1267830dc99626a1e95394980d769&Type=6&UserID=2289803"
                f"&VerSion=5.11.0.3&a=ZhiShuStockList_W8&apiv=w33&c=ZhiShuRanking"
                f"&old=1&st=100")
        headers = {
            "User-Agent": "Content-Type: application/x-www-form-urlencoded; charset=utf-8"
        }
        r = requests.post(url, headers=headers)
        data_json = r.json()
        data_concept = data_json['list']
        count = data_json['Count']
        data_df = pd.DataFrame(data_concept)
        result = data_frame_util.merge_choose_data_no_drop(result, data_df)
        index = index + 100
        if count < index:
            break
    if data_frame_util.is_empty(result):
        return None
    result = kpl_common_field_constant.rename_kpl_plate_detail(result)
    return result


# 历史区间强度

# begin到end之间的强度
def get_plate_index_his(index, index_type, str_day, begin, end):
    url = "https://apphis.longhuvip.com/w1/api/index.php?Date" \
          "=" + str(str_day) + \
          "&Index=" + str(index) + \
          "&Order=1&PhoneOSNew=2" \
          "&REnd=" + str(end) + \
          "&RStart=" + str(begin) + \
          "&Type=1&VerSion=5.14.0.1" \
          "&ZSType=" + str(index_type) + \
          "&a=RealRankingInfo&apiv=w36&c=ZhiShuRanking" \
          "&st=" + str(HIS_PAGE_MAX_COUNT)

    headers = {
        "User-Agent": "Content-Type: application/x-www-form-urlencoded; charset=utf-8"
    }
    r = requests.post(url, headers=headers)
    data_json = r.json()
    data_concept = data_json['list']
    data_df_his = pd.DataFrame(data_concept)
    if data_frame_util.is_empty(data_df_his):
        return None
    data_df_his = kpl_common_field_constant.rename_plate_index(data_df_his)
    return data_df_his


# 获取开盘啦 股票入选概念原因
def get_kpl_concept_choose_reason(plate_id, symbol_list_str):
    try:
        response = requests.get(
            url="https://apphwshhq.longhuvip.com/w1/api/index.php",
            params={
                "PhoneOSNew": "2",
                "PlateID": plate_id,
                "Stocks": symbol_list_str,
                "VerSion": "5.21.0.3",
                "a": "PlateIntroduction_Info",
                "apiv": "w42",
                "c": "ZhiShuRanking"
            },
            headers={
                "User-Agent": "lhb/5.21.3 (com.kaipanla.www; build:0; iOS 18.6.2) Alamofire/4.9.1"
            }
        )

        json_result = response.json()
        symbol_list_reason = json_result.get('List')

        df_simple = pd.DataFrame(symbol_list_reason, columns=['symbol', 'choose_reason', 'flag', 'remark'])
        return df_simple
    except BaseException as e:
        logger.error("获取开盘啦股票入选原因异常:{},{},{}", plate_id, symbol_list_str, e)
        return pd.DataFrame()


if __name__ == '__main__':
    plate_id_test = '801133'
    symbol_list_str_test = "002017,002104,301678,003040,300689,300608,300698,600941,002313,002881,002467,300579,002355,300205,300638,002049"

    df_simple_test = get_kpl_concept_choose_reason(plate_id_test, symbol_list_str_test)

    df = plate_detail_info('801359')

    df = get_plate_index(7)
    print(df)
    data_df = get_plate_index_his(0, 7, '2024-04-24', '0925', '0930')
    print(data_df)
