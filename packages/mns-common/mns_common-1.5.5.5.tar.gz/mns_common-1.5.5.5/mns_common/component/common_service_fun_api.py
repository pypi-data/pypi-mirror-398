import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd

mongodb_util = MongodbUtil('27017')

# 涨停涨幅
ZT_CHG = 9.57

# 亿元
HUNDRED_MILLION = 100000000

# 万元
TEN_THOUSAND = 10000


def total_mv_classification(real_time_quotes_now):
    real_time_quotes_now.loc[:, 'flow_mv_sp'] = round((real_time_quotes_now['flow_mv'] / HUNDRED_MILLION), 2)
    real_time_quotes_now.loc[:, 'total_mv_sp'] = round((real_time_quotes_now['total_mv'] / HUNDRED_MILLION), 2)
    real_time_quotes_now.loc[:, 'flow_mv_level'] = 0

    real_time_quotes_now.reset_index(drop=True, inplace=True)
    real_time_quotes_now.loc[(real_time_quotes_now["flow_mv_sp"] >= 0), ['flow_mv_level']] \
        = (real_time_quotes_now["flow_mv_sp"] // 10) + 1
    return real_time_quotes_now


# 股票分类
def classify_symbol(real_time_quotes_now_df):
    real_time_quotes_now_df['classification'] = real_time_quotes_now_df['symbol'].apply(
        lambda symbol: classify_symbol_one(symbol))
    return real_time_quotes_now_df


# 增加前缀
def add_pre_prefix(real_time_quotes_now_df):
    real_time_quotes_now_df['symbol_prefix'] = real_time_quotes_now_df['symbol'].apply(
        lambda symbol: add_pre_prefix_one(symbol))
    return real_time_quotes_now_df


# 增加后缀
def add_after_prefix(real_time_quotes_now_df):
    real_time_quotes_now_df['symbol_prefix'] = real_time_quotes_now_df['symbol'].apply(
        lambda symbol: add_after_prefix_one(symbol))
    return real_time_quotes_now_df


# 单个股票分类
def classify_symbol_one(symbol):
    if symbol.startswith('3'):
        return 'C'
    elif symbol.startswith('6'):
        if symbol.startswith('68'):
            return 'K'
        else:
            return 'H'
    elif symbol.startswith('0'):
        return 'S'
    else:
        return 'X'


# 添加前缀
def add_pre_prefix_one(symbol):
    symbol_simple = symbol[0:6]
    if bool(1 - is_valid_symbol(symbol_simple)):
        return symbol

    if symbol_simple.startswith('6'):
        return 'SH' + symbol_simple
    elif symbol_simple.startswith('0') or symbol_simple.startswith('3'):
        return 'SZ' + symbol_simple
    else:
        return 'BJ' + symbol_simple


def is_valid_symbol(symbol):
    # 确保输入是字符串（避免数字或其他类型）
    if not isinstance(symbol, str):
        return False
    # 检查长度是否为6且所有字符都是数字
    return len(symbol) == 6 and symbol.isdigit()


# 添加后缀
def add_after_prefix_one(symbol):
    symbol_simple = symbol[0:6]
    if bool(1 - is_valid_symbol(symbol_simple)):
        return symbol
    if symbol_simple.startswith('6'):
        return symbol_simple + '.SH'
    elif symbol_simple.startswith('0') or symbol_simple.startswith('3'):
        return symbol_simple + '.SZ'
    else:
        return symbol_simple + '.BJ'


def symbol_amount_simple(real_time_quotes_now_df):
    real_time_quotes_now_df['amount_level'] = round(real_time_quotes_now_df['amount'] / HUNDRED_MILLION, 2)
    return real_time_quotes_now_df


# 排除 新股
def exclude_new_stock(real_time_quotes_now_df):
    return real_time_quotes_now_df.loc[~(real_time_quotes_now_df['name'].str.contains('N'))]


# 排除 包含名字中包含特定字母的数据
def exclude_str_name_stock(real_time_quotes_now_df, str_name):
    return real_time_quotes_now_df.loc[~(real_time_quotes_now_df['name'].str.contains(str_name))]


# 排除st
def exclude_st_symbol(real_time_quotes_now_df):
    exclude_st_symbol_list = list(
        real_time_quotes_now_df.loc[(real_time_quotes_now_df['name'].str.contains('ST'))
                                    | (real_time_quotes_now_df['name'].str.contains('退'))]['symbol'])
    return real_time_quotes_now_df.loc[
        ~(real_time_quotes_now_df['symbol'].isin(
            exclude_st_symbol_list))]


# 排除带星的ST 容易退市
def exclude_star_st_symbol(df):
    exclude_st_symbol_list = list(
        df.loc[(df['name'].str.contains(r'\*')) | (df['name'].str.contains('退'))]['symbol'])
    return df.loc[
        ~(df['symbol'].isin(
            exclude_st_symbol_list))]


# 排除b股数据
def exclude_b_symbol(real_time_quotes_now_df):
    return real_time_quotes_now_df.loc[(real_time_quotes_now_df.symbol.str.startswith('3'))
                                       | (real_time_quotes_now_df.symbol.str.startswith('0'))
                                       | (real_time_quotes_now_df.symbol.str.startswith('6'))
                                       | (real_time_quotes_now_df.symbol.str.startswith('4'))
                                       | (real_time_quotes_now_df.symbol.str.startswith('9'))
                                       | (real_time_quotes_now_df.symbol.str.startswith('8'))]


def exclude_ts_symbol(real_time_quotes_now_df):
    return real_time_quotes_now_df.loc[~(real_time_quotes_now_df['name'].str.contains('退'))]


# 排除成交量为0 停牌的股票
def exclude_amount_zero_stock(real_time_quotes_now_df):
    return real_time_quotes_now_df.loc[~(real_time_quotes_now_df['amount'] == 0)]


# 获取最大number
def realtime_quotes_now_max_number(db_name, field):
    query = {'symbol': '000001'}
    df = mongodb_util.descend_query(query, db_name, field, 1)
    if df is None or df.shape[0] == 0:
        return 1
    else:
        return list(df[field])[0]


# 获取集合最新实时数据
def get_last_new_real_time_data(db_name, number):
    query = {'number': number}
    return mongodb_util.find_query_data(db_name, query)


# 获取当天 new stock
def get_new_stock(real_time_quotes_now_df):
    return real_time_quotes_now_df.loc[(real_time_quotes_now_df['name'].str.contains('N'))]


# 计算指数
def calculate_index(real_time_quotes_now_df):
    concept_flow_mv = sum(real_time_quotes_now_df['flow_mv'])
    real_time_quotes_now_df.loc[:, 'flow_mv_ratio'] = round(
        (real_time_quotes_now_df['flow_mv'] / concept_flow_mv), 4)
    real_time_quotes_now_df.loc[:, "chg_ratio"] = real_time_quotes_now_df["flow_mv_ratio"] * \
                                                  real_time_quotes_now_df["chg"]
    return round(sum(real_time_quotes_now_df["chg_ratio"]), 2)


# 按照字段field1分组  对field2 求和
def group_by_industry_sum(real_time_quotes_now, field1, field2):
    df_series = real_time_quotes_now.groupby(by=[field1])[field2].sum()
    return pd.DataFrame({field1: df_series.index, field2: df_series.values})


def symbol_add_prefix(symbol):
    if bool(1 - symbol.isdigit()):
        return symbol
    symbol_simple = symbol[0:6]
    if symbol_simple.startswith('6'):
        return '1.' + symbol_simple
    elif symbol_simple.startswith('0') or symbol_simple.startswith('3'):
        return '0.' + symbol_simple
    else:
        return '0.' + symbol_simple


# 排除改变代码的北交所
def exclude_change_bjs_code(df):
    return df[~df['symbol'].str.startswith(('8', '4'))]
