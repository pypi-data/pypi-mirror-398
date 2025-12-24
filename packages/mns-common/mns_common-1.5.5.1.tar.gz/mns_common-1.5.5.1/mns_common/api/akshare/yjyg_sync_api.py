import sys
import os
import akshare as ak
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
from datetime import datetime

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
mongodb_util = MongodbUtil('27017')

predictor_translation_map = {
    "主营业务收入": "main_operating_revenue",
    "净利润": "net_profit",
    "归属于上市公司股东的净利润": "net_profit_attributable_to_shareholders",
    "扣除后营业收入": "operating_revenue_deducted",
    "扣除非经常性损益后的净利润": "net_profit_excluding_non_recurring_items",
    "扣非后每股收益": "earnings_per_share_excluding_non_recurring_items",
    "每股收益": "earnings_per_share",
    "营业收入": "operating_revenue",
    "非经常性损益": "non_recurring_items"
}
# ['net_profit', 'net_profit_attributable_to_shareholders', 'net_profit_excluding_non_recurring_items',
#  'earnings_per_share_excluding_non_recurring_items', 'earnings_per_share']
predict_type_translation_map = {
    "不确定": "uncertain",
    "减亏": "loss_reduction",
    "增亏": "increased_loss",
    "扭亏": "turnaround",
    "略减": "slight_decrease",
    "略增": "slight_increase",
    "续亏": "continued_loss",
    "续盈": "continued_profit",
    "预减": "pre_loss",
    "预增": "pre_increase",
    "首亏": "first_loss"
}


# ['turnaround', 'slight_increase', 'continued_profit', 'pre_increase']


def sync_yjyg_data(period):
    stock_yjyg_em_df = ak.stock_yjyg_em(date=period)
    if data_frame_util.is_empty(stock_yjyg_em_df):
        return None
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    sync_day = now_date.strftime('%Y-%m-%d')
    stock_yjyg_em_df.rename(columns={"序号": "index",
                                     "股票代码": "symbol",
                                     "股票简称": "name",
                                     "预测指标": "predictor",
                                     "业绩变动": "perform_change_detail",
                                     "预测数值": "predicted_value",
                                     "业绩变动幅度": "perform_chg",
                                     "业绩变动原因": "perform_change_reason",
                                     "预告类型": "predict_type",
                                     "上年同期值": "last_year_period",
                                     "公告日期": "release_day"}, inplace=True)

    stock_yjyg_em_df['predictor_en'] = stock_yjyg_em_df['predictor'].map(lambda x: predictor_translation_map.get(x, x))
    stock_yjyg_em_df['predict_type_en'] = stock_yjyg_em_df['predict_type'].map(
        lambda x: predict_type_translation_map.get(x, x))

    stock_yjyg_em_df.loc[:, 'period'] = period
    stock_yjyg_em_df.loc[:, 'sync_day'] = sync_day
    stock_yjyg_em_df.loc[:, 'str_now_date'] = str_now_date
    stock_yjyg_em_df['release_day'] = pd.to_datetime(stock_yjyg_em_df['release_day'])
    stock_yjyg_em_df['release_day'] = stock_yjyg_em_df['release_day'].dt.strftime('%Y-%m-%d')

    stock_yjyg_em_df['perform_chg'].fillna(0, inplace=True)
    stock_yjyg_em_df['_id'] = stock_yjyg_em_df['symbol'] + '_' + period + '_' + stock_yjyg_em_df[
        'predictor_en'] + '_' + stock_yjyg_em_df['predict_type_en']
    stock_yjyg_em_df = stock_yjyg_em_df[
        ['_id', 'symbol', 'name', 'predictor',
         'predictor_en',
         'perform_change_detail',
         'predicted_value',
         'perform_chg',
         'perform_change_reason',
         'predict_type',
         'predict_type_en',
         'last_year_period',
         'release_day',
         'period',
         'sync_day',
         'str_now_date',
         'index']]

    mongodb_util.save_mongo(stock_yjyg_em_df, 'stock_yjyg_em_df')


if __name__ == '__main__':
    sync_yjyg_data('20230630')
