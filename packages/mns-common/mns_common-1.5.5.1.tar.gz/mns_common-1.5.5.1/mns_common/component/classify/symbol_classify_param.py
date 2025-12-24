import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

# 按照上市时间对股票分类

# 股票类型
stock_type_classify_param = {
    #  上市五个交易日的股票 名字以C开头 1-5个交易日
    "new_stock": "new",
    # 交易日 6-100天的次新股票  6-100个交易日
    'sub_stock_new': "sub_new",
    # 交易日 100-365天的股票
    "sub_stock": "sub",
    # 交易日 365-730 的股票
    "normal_sub_stock": "normal_sub",
    # 交易日 731 到无穷天的股票
    "normal_stock": "normal",

    # 最小交易天数不带C
    'sub_stock_new_min_deal_days': 5,
    # 一个月最大交易天数 23天 三个月 4*23+1 =93  加1是上市第一天
    'sub_new_stock_max_deal_days': 100,
    # 上市交易 100-365天次新的股票
    'sub_stock_max_deal_days': 365,
    # 交易日 731 到无穷天的股票
    'normal_stock_max_deal_days': 731,

    # 最小上市天数不带C
    'sub_stock_new_min_diff_days': 7,
    # 上市天数 只能方便测试,粗略计算
    'sub_stock_new_max_diff_days': 150,
    # 上市天数 150-465天次新的股票
    'sub_stock_max_diff_days': 465,
    # 上市天数 930以上的股票
    'normal_sub_stock_max_diff_days': 930,

}
