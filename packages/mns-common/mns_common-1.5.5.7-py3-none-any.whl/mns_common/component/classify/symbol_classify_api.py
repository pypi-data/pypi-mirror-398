import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.component.classify.symbol_classify_param import stock_type_classify_param


# 深沪普通股票  选择 10cm涨幅的
def choose_sh_symbol(realtime_quotes_now):
    return realtime_quotes_now.loc[
        (realtime_quotes_now['classification'].isin(['S', 'H']))]


# 选择科创 创业板 20厘米的
def choose_kc_symbol(realtime_quotes_now):
    return realtime_quotes_now.loc[
        realtime_quotes_now['classification'].isin(['K', 'C'])]


# 选择北交所的 30厘米的
def choose_bjs_symbol(realtime_quotes_now):
    return realtime_quotes_now.loc[
        realtime_quotes_now['classification'].isin(['X'])]


# 设置新股次新标记 通过交易时间
def set_stock_type_by_deal_days(real_time_quotes_now_init):
    if data_frame_util.is_empty(real_time_quotes_now_init):
        return None
    real_time_quotes_now = real_time_quotes_now_init.copy()
    real_time_quotes_now.loc[:, "stock_type"] = stock_type_classify_param['normal_stock']
    # 交易天数五个交易日的股票
    real_time_quotes_now.loc[(real_time_quotes_now['name'].str.startswith('C'))
                             | (real_time_quotes_now['deal_days'] < stock_type_classify_param[
        'sub_stock_new_min_deal_days']), "stock_type"] = stock_type_classify_param['new_stock']

    # 交易上市6-100天的次新股票
    real_time_quotes_now.loc[
        (real_time_quotes_now['stock_type'] != stock_type_classify_param['new_stock'])
        & (real_time_quotes_now['deal_days'] >= stock_type_classify_param['sub_stock_new_min_deal_days'])
        & (real_time_quotes_now['deal_days'] < stock_type_classify_param['sub_new_stock_max_deal_days']),
        "stock_type"] = stock_type_classify_param['sub_stock_new']

    # 上市次新股 100-365
    real_time_quotes_now.loc[
        (real_time_quotes_now['deal_days'] >= stock_type_classify_param['sub_new_stock_max_deal_days'])
        & (real_time_quotes_now['deal_days'] < stock_type_classify_param['sub_stock_max_deal_days']),
        "stock_type"] = stock_type_classify_param['sub_stock']

    # 交易天数 366-730
    real_time_quotes_now.loc[
        (real_time_quotes_now['deal_days'] >= stock_type_classify_param['sub_stock_max_deal_days'])
        & (real_time_quotes_now['deal_days'] < stock_type_classify_param['normal_stock_max_deal_days']),
        "stock_type"] = stock_type_classify_param['normal_sub_stock']

    return real_time_quotes_now


# 设置新股次新标记 通过上市时间
def set_stock_type_by_diff_days(real_time_quotes_now_init):
    if data_frame_util.is_empty(real_time_quotes_now_init):
        return None
    real_time_quotes_now = real_time_quotes_now_init.copy()
    real_time_quotes_now.loc[:, "stock_type"] = stock_type_classify_param['normal_stock']
    # 上市五个交易日的股票
    real_time_quotes_now.loc[(real_time_quotes_now['name'].str.startswith('C')) | (
            real_time_quotes_now['diff_days'] < stock_type_classify_param[
        'sub_stock_new_min_diff_days']), "stock_type"] = \
        stock_type_classify_param[
            'new_stock']
    # 交易上市7-150天的次新股票
    real_time_quotes_now.loc[
        (real_time_quotes_now['stock_type'] != stock_type_classify_param['new_stock'])
        & (real_time_quotes_now['diff_days'] <= stock_type_classify_param['sub_stock_new_max_diff_days']),
        "stock_type"] = stock_type_classify_param['sub_stock_new']

    # 上市次新股 150-465
    real_time_quotes_now.loc[
        (real_time_quotes_now['diff_days'] > stock_type_classify_param['sub_stock_new_max_diff_days'])
        & (real_time_quotes_now['diff_days'] <= stock_type_classify_param['sub_stock_max_diff_days']),
        "stock_type"] = stock_type_classify_param['sub_stock']

    # 上市天数 465-930
    real_time_quotes_now.loc[
        (real_time_quotes_now['diff_days'] > stock_type_classify_param['sub_stock_max_diff_days'])
        & (real_time_quotes_now['diff_days'] <= stock_type_classify_param['normal_sub_stock_max_diff_days']),
        "stock_type"] = stock_type_classify_param['normal_sub_stock']

    return real_time_quotes_now


# 新上市注册股票 交易天数1-5天
def choose_new_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] == stock_type_classify_param['new_stock']]

    return real_time_quotes_now


# 排除新股
def exclude_new_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] != stock_type_classify_param['new_stock']]
    return real_time_quotes_now


# 选择次新new     # 交易上市6-100天的次新股票
def choose_sub_new(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] == stock_type_classify_param['sub_stock_new']]

    return real_time_quotes_now


# 排除次新new      # 交易上市6-100天的次新股票
def exclude_sub_new(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] != stock_type_classify_param['sub_stock_new']]
    return real_time_quotes_now


# 选择次新 # 交易上市100-365天的次新股票
def choose_sub_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] == stock_type_classify_param['sub_stock']]

    return real_time_quotes_now


# 排除次新  交易上市100-365天的次新股票
def exclude_sub_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] != stock_type_classify_param['sub_stock']]
    return real_time_quotes_now


# 选择普通sub 交易日 365-730 的股票
def choose_normal_sub_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] == stock_type_classify_param['normal_sub_stock']]

    return real_time_quotes_now


# 排除普通sub 交易日 365-730 的股票
def exclude_normal_sub_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] != stock_type_classify_param['normal_sub_stock']]
    return real_time_quotes_now


# 选择普通 交易日 731 到无穷天的股票
def choose_normal_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] == stock_type_classify_param['normal_stock']]

    return real_time_quotes_now


# 排除普通 交易日 731 到无穷天的股票
def exclude_normal_stock(real_time_quotes_now):
    real_time_quotes_now = real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'] != stock_type_classify_param['normal_stock']]
    return real_time_quotes_now


# 根据类型列表选择
def choose_stock_by_type_list(real_time_quotes_now, type_list):
    return real_time_quotes_now.loc[
        real_time_quotes_now['stock_type'].isin(type_list)]


# 增加市场后缀
def add_symbol_suffix(stock='600031.SH'):
    '''
    调整代码
    '''
    if (stock[-2:] == 'SH'
            or stock[-2:] == 'SZ'
            or stock[-2:] == 'sh'
            or stock[-2:] == 'sz'
            or stock[-2:] == 'BJ'
            or stock[-2:] == 'bj'):
        stock = stock.upper()
    else:
        if stock[:3] in ['600', '601', '603', '688', '510', '511',
                         '512', '513', '515', '113', '110', '118', '501'] or stock[:2] in ['11']:
            stock = stock + '.SH'
        elif stock.startswith('8') or stock.startswith('4') or stock.startswith('9'):
            stock = stock + '.BJ'
        else:
            stock = stock + '.SZ'
    return stock
