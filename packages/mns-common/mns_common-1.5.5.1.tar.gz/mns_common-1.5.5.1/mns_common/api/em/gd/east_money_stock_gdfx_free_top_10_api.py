import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import akshare as ak
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.utils.date_handle_util as date_handle_util
from loguru import logger
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
from datetime import datetime

mongodb_util = MongodbUtil('27017')


# 获取十大股东

def get_stock_gdfx_free_top_10_em_api(str_day, symbol):
    try:
        stock_gdfx_free_top_10_em_df = ak.stock_gdfx_free_top_10_em(symbol=symbol, date=str_day)
        stock_gdfx_free_top_10_em_df.rename(columns={
            "名次": "index",
            "股东名称": "shareholder_name",
            "股东性质": "shareholder_nature",
            "股份性质": "shares_nature",
            "股份类型": "shares_type",
            "持股数": "shares_number",
            "占总流通股本持股比例": "circulation_ratio",
            "增减": "change",
            "变动比率": "change_ratio"
        }, inplace=True)
    except BaseException as e:
        # logger.error("同步十大流通股东信息异常:{}", e)
        return None
    stock_gdfx_free_top_10_em_df = stock_gdfx_free_top_10_em_df.fillna(0)
    stock_gdfx_free_top_10_em_df.index = stock_gdfx_free_top_10_em_df.index.astype(str)
    stock_gdfx_free_top_10_em_df.drop_duplicates('shareholder_name', keep='last', inplace=True)

    return stock_gdfx_free_top_10_em_df


def get_stock_gdfx_top_10_em_api(str_day, symbol):
    try:
        stock_gdfx_top_10_em_df = ak.stock_gdfx_top_10_em(symbol=symbol, date=str_day)
        stock_gdfx_top_10_em_df.rename(columns={
            "名次": "index",
            "股东名称": "shareholder_name",
            "股份类型": "shares_type",
            "持股数": "shares_number",
            "占总股本持股比例": "circulation_ratio",
            "增减": "change",
            "变动比率": "change_ratio"
        }, inplace=True)
    except BaseException as e:
        # logger.error("同步十大股东信息异常:{}", e)
        return None
    stock_gdfx_top_10_em_df = stock_gdfx_top_10_em_df.fillna(0)
    stock_gdfx_top_10_em_df.index = stock_gdfx_top_10_em_df.index.astype(str)
    stock_gdfx_top_10_em_df.drop_duplicates('shareholder_name', keep='last', inplace=True)
    return stock_gdfx_top_10_em_df


def get_stock_gdfx_free_top_10_em(str_day, symbol):
    symbol_init = symbol
    classification = common_service_fun_api.classify_symbol_one(symbol)
    if classification in ["S", "C"]:
        symbol = 'sz' + symbol
    elif classification in ["K", "H"]:
        symbol = 'sh' + symbol
    else:
        symbol = 'bj' + symbol

    str_day_no_slash = date_handle_util.no_slash_date(str_day)
    date_day = date_handle_util.str_to_date(str_day_no_slash, '%Y%m%d')
    month = date_day.month
    year = date_day.year
    one = '0331'
    two = '0630'
    three = '0930'
    four = '1231'

    if 0 < month <= 4:
        period_04 = str(year - 1) + four
        # 流通十大股东
        stock_gdfx_free_top_10_04 = get_stock_gdfx_free_top_10_em_api(period_04, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_04, period_04, symbol_init, str_day)

        # 十大股东
        stock_gdfx_top_10_04 = get_stock_gdfx_top_10_em_api(period_04, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_04, period_04, symbol_init, str_day)

        if stock_gdfx_free_top_10_04 is None or stock_gdfx_free_top_10_04.shape[0] == 0:
            period_03 = str(year - 1) + three
            stock_gdfx_free_top_10_03 = get_stock_gdfx_free_top_10_em_api(period_03, symbol)
            sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_03, period_03, symbol_init, str_day)

            # 十大股东
            stock_gdfx_top_10_03 = get_stock_gdfx_top_10_em_api(period_03, symbol)
            sync_stock_gdfx_top_10(stock_gdfx_top_10_03, period_03, symbol_init, str_day)

        period_01 = str(year) + one
        stock_gdfx_free_top_10_01 = get_stock_gdfx_free_top_10_em_api(period_01, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_01, period_01, symbol_init, str_day)

        # 十大股东
        stock_gdfx_top_10_01 = get_stock_gdfx_top_10_em_api(period_01, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_01, period_01, symbol_init, str_day)

    elif 4 < month <= 6:
        # 十大流通股东
        period_01 = str(year) + one
        stock_gdfx_free_top_10_01 = get_stock_gdfx_free_top_10_em_api(period_01, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_01, period_01, symbol_init, str_day)
        period_02 = str(year) + two
        stock_gdfx_free_top_10_02 = get_stock_gdfx_free_top_10_em_api(period_02, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_02, period_02, symbol_init, str_day)

        # 十大股东
        stock_gdfx_top_10_01 = get_stock_gdfx_top_10_em_api(period_01, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_01, period_01, symbol_init, str_day)

        stock_gdfx_top_10_02 = get_stock_gdfx_top_10_em_api(period_02, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_02, period_02, symbol_init, str_day)

    elif 6 < month <= 10:
        # 十大流通股东
        period_02 = str(year) + two
        stock_gdfx_free_top_10_02 = get_stock_gdfx_free_top_10_em_api(period_02, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_02, period_02, symbol_init, str_day)
        period_03 = str(year) + three
        stock_gdfx_free_top_10_03 = get_stock_gdfx_free_top_10_em_api(period_03, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_03, period_03, symbol_init, str_day)

        # 十大股东

        stock_gdfx_top_10_02 = get_stock_gdfx_top_10_em_api(period_02, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_02, period_02, symbol_init, str_day)

        stock_gdfx_top_10_03 = get_stock_gdfx_top_10_em_api(period_03, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_03, period_03, symbol_init, str_day)
    elif 10 < month <= 12:
        # 十大流通股东
        period_03 = str(year) + three
        stock_gdfx_free_top_10_03 = get_stock_gdfx_free_top_10_em_api(period_03, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_03, period_03, symbol_init, str_day)
        period_04 = str(year) + four
        stock_gdfx_free_top_10_04 = get_stock_gdfx_free_top_10_em_api(period_04, symbol)
        sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_04, period_04, symbol_init, str_day)

        # 十大股东
        stock_gdfx_top_10_03 = get_stock_gdfx_top_10_em_api(period_03, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_03, period_03, symbol_init, str_day)

        stock_gdfx_top_10_04 = get_stock_gdfx_top_10_em_api(period_04, symbol)
        sync_stock_gdfx_top_10(stock_gdfx_top_10_04, period_04, symbol_init, str_day)


# 保存10大流通股东
def sync_stock_gdfx_free_top_10(stock_gdfx_free_top_10_em_df, period, symbol, str_day):
    if stock_gdfx_free_top_10_em_df is not None and stock_gdfx_free_top_10_em_df.shape[0] > 0:
        # 更新日期
        stock_gdfx_free_top_10_em_df['str_day'] = str_day

        stock_gdfx_free_top_10_em_df['symbol'] = symbol

        stock_gdfx_free_top_10_em_df['shares_number_str'] = stock_gdfx_free_top_10_em_df['shares_number'].astype(str)

        stock_gdfx_free_top_10_em_df[
            '_id'] = symbol + '_' + period + '_' + stock_gdfx_free_top_10_em_df.shares_number_str
        stock_gdfx_free_top_10_em_df['period'] = period

        query_exist = {'symbol': symbol, 'period': period}
        exist_df = mongodb_util.find_query_data(db_name_constant.STOCK_GDFX_FREE_TOP_10, query_exist)
        now_date = datetime.now()
        str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
        # 不存在的时候更新创建时间
        if exist_df.shape[0] == 0:
            stock_gdfx_free_top_10_em_df['create_day'] = str_day
            stock_gdfx_free_top_10_em_df['sync_time'] = str_now_date
        else:
            if 'create_day' in exist_df.columns:
                stock_gdfx_free_top_10_em_df['create_day'] = list(exist_df['create_day'])[0]
            else:
                stock_gdfx_free_top_10_em_df['create_day'] = str_day
            if 'sync_time' in exist_df.columns:
                stock_gdfx_free_top_10_em_df['sync_time'] = list(exist_df['sync_time'])[0]
            else:
                stock_gdfx_free_top_10_em_df['sync_time'] = str_now_date
        mongodb_util.save_mongo(stock_gdfx_free_top_10_em_df, db_name_constant.STOCK_GDFX_FREE_TOP_10)


# 保存10大股东
def sync_stock_gdfx_top_10(stock_gdfx_top_10_em_df, period, symbol, str_day):
    if stock_gdfx_top_10_em_df is not None and stock_gdfx_top_10_em_df.shape[0] > 0:
        stock_gdfx_top_10_em_df['str_day'] = str_day
        stock_gdfx_top_10_em_df['symbol'] = symbol

        stock_gdfx_top_10_em_df['shares_number_str'] = stock_gdfx_top_10_em_df['shares_number'].astype(str)

        stock_gdfx_top_10_em_df['_id'] = symbol + '_' + period + '_' + stock_gdfx_top_10_em_df.shares_number_str
        stock_gdfx_top_10_em_df['period'] = period

        query_exist = {'symbol': symbol, 'period': period}
        exist_df = mongodb_util.find_query_data(db_name_constant.STOCK_GDFX_TOP_10, query_exist)
        now_date = datetime.now()
        str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

        # 不存在的时候更新创建时间
        if exist_df.shape[0] == 0:
            stock_gdfx_top_10_em_df['create_day'] = str_day
            stock_gdfx_top_10_em_df['sync_time'] = str_now_date
        else:
            if 'create_day' in exist_df.columns:
                stock_gdfx_top_10_em_df['create_day'] = list(exist_df['create_day'])[0]


            else:
                stock_gdfx_top_10_em_df['create_day'] = str_day

            if 'sync_time' in exist_df.columns:
                stock_gdfx_top_10_em_df['sync_time'] = list(exist_df['sync_time'])[0]
            else:
                stock_gdfx_top_10_em_df['sync_time'] = str_now_date

        mongodb_util.save_mongo(stock_gdfx_top_10_em_df, db_name_constant.STOCK_GDFX_TOP_10)


# 十大股东+十大流通股东
def sync_stock_gdfx_free_top_10_one_day(str_day):
    real_time_quotes = em_stock_info_api.get_a_stock_info()
    real_time_quotes = real_time_quotes.loc[~(
        real_time_quotes['symbol'].isin(company_common_service_new_api.get_de_list_company()))]
    for real_time_one in real_time_quotes.itertuples():
        try:
            get_stock_gdfx_free_top_10_em(str_day, real_time_one.symbol)
            logger.info('同步股票前十大流通东:{},{}', real_time_one.symbol, real_time_one.name)
        except BaseException as e:
            logger.error('同步所有股票前十大流通股本异常:{},{}', real_time_one.symbol, e)
    logger.info('同步所有股票股东列表完成:{}', str_day)


if __name__ == '__main__':
    get_stock_gdfx_free_top_10_em('20250930', '300697')
    now_date_test = datetime.now()
    str_day_test = now_date_test.strftime('%Y-%m-%d')
    logger.info('同步所有股票前十大流通股本')
    sync_stock_gdfx_free_top_10_one_day(str_day_test)
