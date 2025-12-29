import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import akshare as ak
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.utils.date_handle_util as date_handle_util


def stock_em_dt_pool_df(date):
    try:
        date = date_handle_util.no_slash_date(date)
        stock_dt_pool_df = ak.stock_zt_pool_dtgc_em(date)
        if data_frame_util.is_empty(stock_dt_pool_df):
            return None
        stock_dt_pool_df.rename(columns={"序号": "index",
                                         "代码": "symbol",
                                         "名称": "name",
                                         "涨跌幅": "chg",
                                         "最新价": "now_price",
                                         "成交额": "amount",
                                         "流通市值": "flow_mv",
                                         "总市值": "total_mv",
                                         "动态市盈率": "ttm_pe",
                                         "换手率": "exchange",
                                         "封单资金": "closure_funds",
                                         "最后封板时间": "last_closure_time",
                                         "板上成交额": "plates_deal",
                                         "连续跌停": "connected_boards_numbers",
                                         "开板次数": "frying_plates_numbers",
                                         "所属行业": "industry"
                                         }, inplace=True)
        stock_dt_pool_df.loc[stock_dt_pool_df['amount'] == '-', 'amount'] = 0
        stock_dt_pool_df.loc[stock_dt_pool_df['exchange'] == '-', 'exchange'] = 0
        stock_dt_pool_df.loc[stock_dt_pool_df['closure_funds'] == '-', 'closure_funds'] = 0
        return stock_dt_pool_df
    except BaseException as e:
        logger.error("同步股票跌停数据出现异常:{},{}", date, e)
        return None


if __name__ == '__main__':
    stock_em_dt_pool_df('20231215')
