import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

# 东方财富a股信息
EM_A_STOCK_INFO = 'em_a_stock_info'

# 东方财富ETF信息
EM_ETF_INFO = 'em_etf_info'

# 东方财富KZZ信息
EM_KZZ_INFO = 'em_kzz_info'

# 东方财富HK股信息
EM_HK_STOCK_INFO = 'em_hk_stock_info'

# 东方财富US股信息
EM_US_STOCK_INFO = 'em_us_stock_info'

# ip代理池
IP_PROXY_POOL = 'ip_proxy_pool'

# ip代理城市信息
IP_PROXY_CITY_PROVINCE = 'ip_proxy_city_province'

# 大单同步表
BIG_DEAL_NAME = "ths_big_deal_fund"
# 大单选择表
BIG_DEAL_CHOOSE_NAME = "big_deal_fund_choose"
# 实时行情表 临时数据
REAL_TIME_QUOTES_NOW = 'realtime_quotes_now'
# 当前实时涨停表
TODAY_ZT_POOL = 'today_zt_pool'
# 集合竞价表
CALL_AUCTION_DB_NAME = 'call_auction_signal'
# 实时竞价表
CALL_AUCTION_DB_NAME_REAL_TIME = 'call_auction_signal_realtime'
# 涨停打板表
NOW_TIME_ZT_DA_BAN = 'now_time_zt_da_ban'
# 开盘啦精选指数表
KPL_BEST_CHOOSE_INDEX = 'kpl_best_choose_index'
# 开盘啦详细组成
KPL_BEST_CHOOSE_INDEX_DETAIL = "kpl_best_choose_index_detail"

# 同花顺概念表
THS_CONCEPT_LIST = "ths_concept_list"

# 同花顺概念详情表
THS_STOCK_CONCEPT_DETAIL = "ths_stock_concept_detail"

# 同花顺概念详情表 app端
THS_STOCK_CONCEPT_DETAIL_APP = "ths_stock_concept_detail_app"

# 今日排除买入股票
TODAY_EXCLUDE_STOCK = "today_exclude_stocks"

# 今日买入股票
BUY_STOCK_NAME = 'trade_stocks'

# TODAY_NEW_CONCEPT_LIST
TODAY_NEW_CONCEPT_LIST = 'today_new_concept_list'

# 开票啦历史数据
KPL_BEST_CHOOSE_HIS = 'kpl_best_choose_his'

# 开票啦每日数据
KPL_BEST_CHOOSE_DAILY = 'kpl_best_choose_daily'

# 当前持仓股票
POSITION_STOCK = 'position_stock'

# 订单委托表
STOCK_TRADE_ORDERS = 'stock_trade_orders'

# 个股黑名单
SELF_BLACK_STOCK = 'self_black_stock'
# 长期自选板块
SELF_CHOOSE_PLATE = 'self_choose_plate'
# 长期自选个股
SELF_CHOOSE_STOCK = 'self_choose_stock'

# 今日自选个股
TODAY_SELF_CHOOSE_STOCK = 'today_self_choose_stock'

# 利润表
EM_STOCK_PROFIT = 'em_stock_profit'

# 资产负债表
EM_STOCK_ASSET_LIABILITY = 'em_stock_asset_liability'

# 退市股票列表
DE_LIST_STOCK = 'de_list_stock'

# 当前涨停列表
STOCK_ZT_POOL = 'stock_zt_pool'

# ths问财涨停股票池
THS_ZT_POOL = 'ths_zt_pool'

# 五板以上的历史高标
STOCK_ZT_POOL_FIVE = 'stock_zt_pool_five'

# 香港公司信息
COMPANY_INFO_HK = 'company_info_hk'

# k线前复权
STOCK_QFQ_DAILY = 'stock_qfq_daily'

# 最近高涨股票
RECENT_HOT_STOCKS = 'recent_hot_stocks'

# 互动提问
STOCK_INTERACTIVE_QUESTION = 'stock_interactive_question'

# 上交所 互动ID映射代码

SH_INFO_UID = 'sh_info_uid'

# 深交所 互动ID映射代码
SZ_INFO_UID = 'sz_info_uid'

# kcx 高涨幅>9.5 当天开盘数据
KCX_HIGH_CHG_OPEN_DATA = 'realtime_quotes_now_zt_new_kc_open'

# 涨停股票(chg>=9.57)实时行情数据
ZT_STOCK_REAL_TIME_QUOTES = "realtime_quotes_now_zt_new"

# 高涨幅和涨停表
STOCK_HIGH_CHG_POOL = 'stock_high_chg_pool'

# 股票账户信息
STOCK_ACCOUNT_INFO = 'stock_account_info'

# 可转债信息
KZZ_DEBT_INFO = 'kzz_debt_info'
# 交易配置信息
TRADE_CONFIG_INFO = 'trade_config_info'

#  打板待选
DA_BAN_SELF_CHOOSE = 'da_ban_self_choose'
#  打板排除
DA_BAN_SELF_EXCLUDE = 'da_ban_self_exclude'

#  港股公司行业列表
HK_COMPANY_INDUSTRY = 'hk_company_industry'

# 公司基本信息
COMPANY_BASE_INFO = 'company_base_info'

#  公司控股信息 子孙公司 联营公司
COMPANY_HOLDING_INFO = 'company_holding_info'
#  公司业务组成
COMPANY_BUSINESS_INFO = 'company_business_info'

#  公司公告信息
COMPANY_ANNOUNCE_INFO = 'company_announce_info'

#  公司行业信息
COMPANY_INDUSTRY_INFO = 'company_industry_info'

# 公司信息临时表
COMPANY_INFO_TEMP = 'company_info_temp'

#  公司信息表
COMPANY_INFO = 'company_info'
#  公司信息历史表
COMPANY_INFO_HIS = 'company_info_his'

#  行业和概念自己的备注
INDUSTRY_CONCEPT_REMARK = 'industry_concept_remark'

#  ths行业对应的股票的备注
INDUSTRY_CONCEPT_SYMBOL_REMARK = 'industry_symbol_remark'

# 复盘日记
FU_PAN_NOTE = 'fu_pan_note'

# 公司停复牌
STOCK_TFP_INFO = 'stock_tfp_info'

# 隔夜打板
OVER_NIGHT_DA_BAN = 'over_night_da_ban'

# 流通十大股东
STOCK_GDFX_FREE_TOP_10 = 'stock_gdfx_free_top_10'

# 十大股东
STOCK_GDFX_TOP_10 = 'stock_gdfx_top_10'

# 同花顺行业列表
THS_INDUSTRY_LIST = 'ths_industry_list'

# 同花顺行业股票详情
THS_STOCK_INDUSTRY_DETAIL = 'ths_stock_industry_detail'

# 年k线前复权
STOCK_QFQ_YEAR = 'stock_qfq_year'

# 涨停原因 详情
ZT_REASON_ANALYSIS = 'zt_reason_analysis'
# 主线详情
MAIN_LINE_DETAIL = 'main_line_detail'

# 主线龙头
MAIN_LINE_LEADER = 'main_line_leader'

# 整体选择表
STRATEGY_TOTAL_CHOOSE_PARAM = 'strategy_total_choose_param'
# k 线参数表
STRATEGY_K_LINE_PARAM = 'strategy_k_line_param'
# 评分参数
STRATEGY_SCORE_PARAM = 'strategy_score_param'
