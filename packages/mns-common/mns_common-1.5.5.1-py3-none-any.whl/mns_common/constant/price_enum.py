import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from enum import Enum

'''
价格枚举
'''


class PriceEnum(Enum):
    BUY_5 = ('buy_5', '买五')
    BUY_4 = ('buy_4', '买四')
    BUY_3 = ('buy_3', '买三')
    BUY_2 = ('buy_2', '买二')
    BUY_1 = ('buy_1', '买一')

    SELL_5 = ('sell_5', '卖五')
    SELL_4 = ('sell_4', '卖四')
    SELL_3 = ('sell_3', '卖三')
    SELL_2 = ('sell_2', '卖二')
    SELL_1 = ('sell_1', '卖一')

    ZT_PRICE = ('zt_price', '涨停价格')
    DT_PRICE = ('dt_price', '跌停价格')
    # 实时竞价买入上限 2%
    BUY_PRICE_LIMIT = ('buy_price_limit', '实时竞价买入上限')
    # 实时竞价卖出下限 -2%
    SEll_PRICE_LIMIT = ('sell_price_limit', '实时竞价卖出上限')

    ZT_WEI_BI = ('zt_wei_bi', 100)
    DT_WEI_BI = ('dt_wei_bi', -100)


    def __init__(self, price_code, price_name):
        self.price_code = price_code
        self.price_name = price_name
