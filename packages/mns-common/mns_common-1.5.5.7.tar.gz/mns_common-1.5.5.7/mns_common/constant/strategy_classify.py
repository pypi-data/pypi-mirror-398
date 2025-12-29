from enum import Enum


class StrategyClassify(Enum):
    # 731 到无穷天的股票 kc
    KC_NORMAL = ('kc_normal', 'kc_normal')

    # 365 到730的股票 kc
    KC_NORMAL_SUB = ('kc_normal_sub', 'kc_normal_sub')

    # 100 到 365 天的股票 kc
    KC_SUB = ('kc_sub', 'kc_sub')

    # 6 到 100的股票 kc
    KC_SUB_NEW = ('kc_sub_new', 'kc_sub_new')

    # 731 到无穷天的股票 sh
    SH_NORMAL = ('sh_normal', 'sh_normal')

    # 365 到730的股票 sh
    SH_NORMAL_SUB = ('sh_normal_sub', 'sh_normal_sub')

    # 100 到 365天的股票 sh
    SH_SUB = ('sh_sub', 'sh_sub')

    # 6 到 100的股票 sh
    SH_SUB_NEW = ('sh_sub_new', 'sh_sub_new')

    # 北交所股票 普通
    BJS_NORMAL = ('bjs_normal', 'bjs_normal')

    # 北交所股票 次新
    BJS_SUB_NEW = ('bjs_sub_new', 'bjs_sub_new')

    # 上市交易 1-5天的股票
    NEW_STOCK = ('new_stock', 'new_stock')

    # 集合竞价 高外盘买入 科创
    HIGH_OUT_DISK_BUY_KC = ('high_out_disk_buy_kc', 'high_out_disk_buy_kc')

    # 集合竞价 高外盘买入 沪深
    HIGH_OUT_DISK_BUY_SH = ('high_out_disk_buy_sh', 'high_out_disk_buy_sh')

    # 集合竞价 高外盘买入 北交所
    HIGH_OUT_DISK_BUY_BJS = ('high_out_disk_buy_bjs', 'high_out_disk_buy_bjs')

    # 所有策略
    ALL = ('all', '所有')

    def __init__(self, strategy_code, strategy_name):
        self.strategy_name = strategy_name
        self.strategy_code = strategy_code


# 获取策略分类
def get_strategy_classify(strategy_code, data_choose_df):
    return data_choose_df.loc[data_choose_df['strategy_code'] == strategy_code]


class StrategyTimePeriod(Enum):
    # 第一阶段
    FIRST_PERIOD = ('first_period', 'first_period')
    # 第二阶段
    SECOND_PERIOD = ('second_period', 'second_period')
    # 第三阶段
    THIRD_PERIOD = ('third_period', 'third_period')
    # 集合竞价阶段
    CALL_AUCTION_PERIOD = ('call_auction_period', 'call_auction_period')

    def __init__(self, time_code, time_name):
        self.time_name = time_name
        self.time_code = time_code
