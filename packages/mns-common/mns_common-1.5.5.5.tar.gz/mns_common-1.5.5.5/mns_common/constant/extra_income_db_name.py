import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

# db_name

EXTRA_INCOME = 'extraIncome'

# us_stock 美股信息数据表
US_STOCK = 'us_stock'
# a股数据表
A_STOCK = 'a_stock'
# hk股票数据
HK_STOCK = 'hk_stock'

# 东方财富a股信息
EM_A_STOCK_INFO = 'em_a_stock_info'

# 东方财富A股 ETF信息
EM_ETF_INFO = 'em_etf_info'

# 东方财富A股 KZZ信息
EM_KZZ_INFO = 'em_kzz_info'

# 东方财富HK股信息
EM_HK_STOCK_INFO = 'em_hk_stock_info'

# 东方财富港股通信息
EM_HK_GGT_STOCK_INFO = 'em_hk_ggt_stock_info'

# 东方财富US股信息
EM_US_STOCK_INFO = 'em_us_stock_info'

# 东方财富US ETF信息
EM_US_ETF_INFO = 'em_us_etf_info'

# 创业板分钟集合数据
ONE_MINUTE_K_LINE_BFQ_C = 'one_minute_k_line_bfq_c'

# 北交所分钟集合数据
ONE_MINUTE_K_LINE_BFQ_BJ = 'one_minute_k_line_bfq_bj'

# 上海主板分钟集合数据
ONE_MINUTE_K_LINE_BFQ_H = 'one_minute_k_line_bfq_h'

# 科创板分钟集合数据
ONE_MINUTE_K_LINE_BFQ_K = 'one_minute_k_line_bfq_k'

# 深圳主板分钟集合数据
ONE_MINUTE_K_LINE_BFQ_S = 'one_minute_k_line_bfq_s'

# 可转债分钟集合数据
ONE_MINUTE_K_LINE_BFQ_KZZ = 'one_minute_k_line_bfq_kzz'

# ETF分钟集合数据
ONE_MINUTE_K_LINE_BFQ_ETF = 'one_minute_k_line_bfq_etf'

# 沪深主要指数分钟集合数据
ONE_MINUTE_K_LINE_BFQ_MAIN_INDEX = 'one_minute_k_line_bfq_main_index'
# 沪深主要指数前复权k线
INDEX_QFQ_DAILY = 'index_qfq_daily'

# 可转债qfq 日k线
KZZ_QFQ_DAILY = 'kzz_qfq_daily'
# ETF qfq 日k线
ETF_QFQ_DAILY = 'etf_qfq_daily'

# 一分钟同步失败集合

ONE_MINUTE_SYNC_FAIL = 'one_minute_sync_fail'

# us stock daily_k_line

US_STOCK_DAILY_QFQ_K_LINE = 'us_stock_daily_qfq_k_line'

US_STOCK_DAILY_BFQ_K_LINE = 'us_stock_daily_bfq_k_line'

US_STOCK_DAILY_HFQ_K_LINE = 'us_stock_daily_hfq_k_line'

# us stock 1分钟集合数据
US_STOCK_MINUTE_K_LINE_BFQ = 'us_stock_one_minute_k_line_bfq'

# us etf 1分钟集合数据
US_ETF_MINUTE_K_LINE_BFQ = 'us_etf_one_minute_k_line_bfq'

# us 主要etf 1分钟集合数据
US_MAIN_ETF_MINUTE_K_LINE_BFQ = 'us_main_etf_one_minute_k_line_bfq'

# hk stock daily_k_line
HK_STOCK_DAILY_QFQ_K_LINE = 'hk_stock_daily_qfq_k_line'
# hk stock 1分钟集合数据
HK_STOCK_MINUTE_K_LINE_BFQ = 'hk_stock_one_minute_k_line_bfq'

# hk etf 1分钟集合数据
HK_ETF_MINUTE_K_LINE_BFQ = 'hk_etf_one_minute_k_line_bfq'

# 雪球利润表
XUE_QIU_LRB_INCOME = 'xue_qiu_lrb_income'

# 雪球资产负债表
XUE_QIU_ASSET_DEBT = 'xue_qiu_asset_debt'

# 雪球资产现金流量表
XUE_QIU_CASH_FLOW = 'xue_qiu_cash_flow'
