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


def stock_zb_pool_df(date):
    try:
        date = date_handle_util.no_slash_date(date)
        stock_zb_pool = ak.stock_zt_pool_zbgc_em(date)
        if data_frame_util.is_empty(stock_zb_pool):
            return None
        stock_zb_pool.rename(columns={"序号": "index",
                                      "代码": "symbol",
                                      "名称": "name",
                                      "涨跌幅": "chg",
                                      "最新价": "now_price",
                                      "炸板股价": "zt_price",
                                      "成交额": "amount",
                                      "流通市值": "flow_mv",
                                      "总市值": "total_mv",
                                      "动态市盈率": "ttm_pe",
                                      "换手率": "exchange",
                                      "涨速": "speed",
                                      "首次封板时间": "first_closure_time",
                                      "炸板次数": "frying_plates_numbers",
                                      "炸板股统计": "statistics",
                                      "涨停统计": "zt_statistics",
                                      "涨停价": "zt_price",
                                      "振幅": "pct_chg",
                                      "所属行业": "industry"
                                      }, inplace=True)
        stock_zb_pool.loc[stock_zb_pool['amount'] == '-', 'amount'] = 0
        stock_zb_pool.loc[stock_zb_pool['exchange'] == '-', 'exchange'] = 0
        return stock_zb_pool
    except BaseException as e:
        logger.error("同步股票炸板数据出现异常:{},{}", date, e)
        return None


if __name__ == '__main__':
    df = stock_zb_pool_df('2024-09-04')
    print(df)
