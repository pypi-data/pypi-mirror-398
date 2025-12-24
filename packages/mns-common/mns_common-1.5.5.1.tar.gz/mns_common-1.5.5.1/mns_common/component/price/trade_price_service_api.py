import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.api.akshare.stock_bid_ask_api as stock_bid_ask_api
from mns_common.constant.price_enum import PriceEnum
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')

'''

'''


def get_trade_price(symbol, price_code, limit_chg):
    stock_bid_ask_df = stock_bid_ask_api.stock_bid_ask_em(symbol)
    wei_bi = list(stock_bid_ask_df['wei_bi'])[0]
    now_price = list(stock_bid_ask_df['now_price'])[0]
    if wei_bi == PriceEnum.ZT_WEI_BI.price_name:
        trade_price = list(stock_bid_ask_df['buy_1'])[0]
    elif wei_bi == PriceEnum.DT_WEI_BI.price_name:
        trade_price = list(stock_bid_ask_df['sell_1'])[0]
    elif price_code == PriceEnum.BUY_1.price_code:
        trade_price = list(stock_bid_ask_df['buy_1'])[0]
    elif price_code == PriceEnum.BUY_2.price_code:
        trade_price = list(stock_bid_ask_df['buy_2'])[0]
    elif price_code == PriceEnum.BUY_3.price_code:
        trade_price = list(stock_bid_ask_df['buy_3'])[0]
    elif price_code == PriceEnum.BUY_4.price_code:
        trade_price = list(stock_bid_ask_df['buy_4'])[0]
    elif price_code == PriceEnum.BUY_5.price_code:
        trade_price = list(stock_bid_ask_df['buy_5'])[0]

    elif price_code == PriceEnum.SELL_1.price_code:
        trade_price = list(stock_bid_ask_df['sell_1'])[0]
    elif price_code == PriceEnum.SELL_2.price_code:
        trade_price = list(stock_bid_ask_df['sell_2'])[0]
    elif price_code == PriceEnum.SELL_3.price_code:
        trade_price = list(stock_bid_ask_df['sell_3'])[0]
    elif price_code == PriceEnum.SELL_4.price_code:
        trade_price = list(stock_bid_ask_df['sell_4'])[0]
    elif price_code == PriceEnum.SELL_5.price_code:
        trade_price = list(stock_bid_ask_df['sell_5'])[0]

    elif price_code == PriceEnum.BUY_PRICE_LIMIT.price_code:
        trade_price = round(now_price * (1 + limit_chg), 2)
    elif price_code == PriceEnum.SEll_PRICE_LIMIT.price_code:
        trade_price = round(now_price * (1 - limit_chg), 2)

    elif price_code == PriceEnum.ZT_PRICE.price_code:
        trade_price = list(stock_bid_ask_df['zt_price'])[0]

    elif price_code == PriceEnum.DT_PRICE.price_code:
        trade_price = list(stock_bid_ask_df['dt_price'])[0]
    else:
        trade_price = list(stock_bid_ask_df['now_price'])[0]

    trade_price = round(trade_price, 2)
    return trade_price


# 计算涨停价格
def calculate_zt_price(last_close_price, symbol):
    classification = common_service_fun_api.classify_symbol_one(symbol)
    if classification in ['K', 'C']:
        zt_chg = 0.2
    elif classification in ['S', 'H']:
        zt_chg = 0.1
    elif classification in ['X']:
        zt_chg = 0.3
    else:
        zt_chg = 0.05

    zt_price = round((1 + zt_chg) * last_close_price, 2)
    return zt_price


# 获取最近一个交易日收盘价格
def get_last_close_price(symbol, str_day):
    if str_day is not None:
        query = {"symbol": symbol, 'date': date_handle_util.no_slash_date(str_day)}
        stock_qfq_daily_df = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_DAILY, query)
        if data_frame_util.is_empty(stock_qfq_daily_df):
            query_descend = {"symbol": symbol}
            stock_qfq_daily_df = mongodb_util.descend_query(query_descend,
                                                            db_name_constant.STOCK_QFQ_DAILY,
                                                            "date", 1)
    else:
        query_descend = {"symbol": symbol}
        stock_qfq_daily_df = mongodb_util.descend_query(query_descend,
                                                        db_name_constant.STOCK_QFQ_DAILY,
                                                        "date", 1)
    close = list(stock_qfq_daily_df['close'])[0]
    return close


if __name__ == '__main__':
    price = get_last_close_price('300085', None)
    print(price)
