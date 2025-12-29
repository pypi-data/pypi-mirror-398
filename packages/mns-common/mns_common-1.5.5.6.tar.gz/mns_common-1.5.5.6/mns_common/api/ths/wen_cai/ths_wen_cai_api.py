import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger
import pywencai
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.cookie.cookie_info_service as cookie_info_service
'''

# https://github.com/zsrl/pywencai 文档
# stock	股票
# zhishu	指数
# fund	基金
# hkstock	港股
# usstock	美股
# threeboard	新三板
# conbond	可转债
# insurance	保险
# futures	期货
# lccp	理财
# foreign_exchange	外汇
'''


def wen_cai_api(question, q_type):
    cookie = cookie_info_service.get_ths_cookie()
    response = pywencai.get(question=question, loop=True, query_type=q_type, cookie=cookie)
    return response


# 获取同花顺概念指数 by wen_cai
def get_concept_index_by_wen_cai():
    try:
        concept_index_df = wen_cai_api('同花顺概念指数', 'zhishu')
        concept_index_df.columns = ["code",
                                    "concept_name",
                                    "price",
                                    "chg",
                                    "detail",
                                    "market_code",
                                    "concept_code"]
        return concept_index_df
    except BaseException as e:
        logger.error("通过问财获取概念指数异常:{}", e)
        return None


# 获取同花顺行业指数 by wen_cai
def get_industry_index_by_wen_cai():
    try:
        industry_index_df = wen_cai_api('同花顺行业指数', 'zhishu')
        industry_index_df.columns = ["code",
                                     "industry_name",
                                     "price",
                                     "chg",
                                     "detail",
                                     "industry_class",
                                     "market_code",
                                     "industry_code"]
        if data_frame_util.is_not_empty(industry_index_df):
            industry_index_df = industry_index_df.loc[industry_index_df['industry_class'].isin([
                '二级行业', '三级行业'
            ])]
            return industry_index_df
        else:
            return None
    except BaseException as e:
        logger.error("通过问财获取行业指数异常:{}", e)
        return None


# 获取概念股票组成详情 通过问财
def get_concept_detail_by_wen_cai(concept_name):
    try:
        concept_name = concept_name.replace("（", "(")
        concept_name = concept_name.replace("）", ")")
        concept_name = concept_name.replace(" ", "")
        concept_all_detail_df = wen_cai_api("所属同花顺概念包含" + concept_name, 'stock')
        if data_frame_util.is_empty(concept_all_detail_df):
            return None
        if len(concept_all_detail_df.columns) == 9:
            concept_all_detail_df.columns = ["code",
                                             "name",
                                             "price",
                                             "chg",
                                             "concept_detail",
                                             "concept_num",
                                             "flow_mv",
                                             "market_code",
                                             'symbol']
            concept_all_detail_df['concept_name'] = concept_name
            concept_all_detail_df['explain'] = ''
            concept_all_detail_df['explain_url'] = ''
        if len(concept_all_detail_df.columns) == 11:
            concept_all_detail_df.columns = ["code",
                                             "name",
                                             "price",
                                             "chg",
                                             "concept_name",
                                             "explain",
                                             "explain_url",
                                             "concept_num",
                                             "flow_mv",
                                             "market_code",
                                             'symbol']
            concept_all_detail_df['concept_detail'] = ''
        return concept_all_detail_df
    except BaseException as e:
        logger.error("通过问财获取概念组成详情异常:{},{}", e, concept_name)
        return None


if __name__ == '__main__':
    zt_df = wen_cai_api('001203涨停分析', 'stock', )
    print(zt_df)
    # concept_detail_df = get_concept_detail_by_wen_cai("光纤概念")
    # concept_df = get_concept_index_by_wen_cai()
    # print(concept_df)
    # industry_index = get_industry_index_by_wen_cai()
    # print(industry_index)
