import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.component.k_line.clean.k_line_param import sh_small_normal_k_line_param
import pandas as pd
from io import StringIO
from loguru import logger


def recent_day_zt_check(real_time_quotes_now_sh):
    # 排除昨日涨停的股票
    real_time_quotes_now_sh.loc[
        real_time_quotes_now_sh['daily01'] >= sh_small_normal_k_line_param['zt_chg'], 'exclude'] = True
    real_time_quotes_now_sh = handle_02_day_zt(real_time_quotes_now_sh.copy())
    real_time_quotes_now_sh = handle_03_day_zt(real_time_quotes_now_sh.copy())
    real_time_quotes_now_sh = handle_04_day_zt(real_time_quotes_now_sh.copy())
    real_time_quotes_now_sh = handle_05_day_zt(real_time_quotes_now_sh.copy())

    return real_time_quotes_now_sh


def handle_02_day_zt(real_time_quotes_now_sh):
    real_time_quotes_now_sh_02_zt = real_time_quotes_now_sh.loc[
        real_time_quotes_now_sh['daily02'] >= sh_small_normal_k_line_param['zt_chg']]
    if data_frame_util.is_empty(real_time_quotes_now_sh_02_zt):
        return real_time_quotes_now_sh

    for stock_one in real_time_quotes_now_sh_02_zt.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one.close_last

            history_data = stock_one.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_02_df = history_data_df.iloc[1:2]
            daily_02_close = list(daily_02_df['close'])[0]
            # 当前收盘价格高于02日涨停价格 排除
            if close_last > daily_02_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理02日涨停数据异常:{},{}", e, stock_one.symbol)
    return real_time_quotes_now_sh


def handle_03_day_zt(real_time_quotes_now_sh):
    # 只有03日涨停
    real_time_quotes_now_sh_03_zt_one_day = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily03'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] < sh_small_normal_k_line_param['zt_chg'])]
    # 02 03日涨停
    real_time_quotes_now_sh_03_zt_two_day = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily03'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] >= sh_small_normal_k_line_param['zt_chg'])]

    if data_frame_util.is_empty(real_time_quotes_now_sh_03_zt_one_day) and data_frame_util.is_empty(
            real_time_quotes_now_sh_03_zt_two_day):
        return real_time_quotes_now_sh

    for stock_one in real_time_quotes_now_sh_03_zt_one_day.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one.close_last

            history_data = stock_one.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_03_df = history_data_df.iloc[2:3]
            daily_03_close = list(daily_03_df['close'])[0]
            # 当前收盘价格高于03日涨停价格 排除
            if close_last > daily_03_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理03日涨停数据异常:{},{}", e, stock_one.symbol)

    for stock_one_two in real_time_quotes_now_sh_03_zt_two_day.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one_two.close_last

            history_data = stock_one_two.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_02_df = history_data_df.iloc[1:2]
            daily_02_close = list(daily_02_df['close'])[0]
            # 当前收盘价格高于02日涨停价格 排除
            if close_last > daily_02_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one_two.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理03日涨停数据异常:{},{}", e, stock_one_two.symbol)
    return real_time_quotes_now_sh


def handle_04_day_zt(real_time_quotes_now_sh):
    real_time_quotes_now_sh_04_zt = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily04'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] < sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] < sh_small_normal_k_line_param['zt_chg'])]
    # 只有04日涨停
    for stock_one in real_time_quotes_now_sh_04_zt.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one.close_last

            history_data = stock_one.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_04_df = history_data_df.iloc[3:4]
            daily_04_close = list(daily_04_df['close'])[0]
            # 当前收盘价格高于04日涨停价格 排除
            if close_last > daily_04_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理03日涨停数据异常:{},{}", e, stock_one.symbol)

    real_time_quotes_now_sh_04_03 = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily04'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] < sh_small_normal_k_line_param['zt_chg'])]

    # 03 04日涨停
    for stock_one_03_04 in real_time_quotes_now_sh_04_03.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one_03_04.close_last

            history_data = stock_one_03_04.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_03_df = history_data_df.iloc[2:3]
            daily_03_close = list(daily_03_df['close'])[0]
            # 当前收盘价格高于03日涨停价格 排除
            if close_last > daily_03_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one_03_04.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理03日涨停数据异常:{},{}", e, stock_one_03_04.symbol)
    # 04 02 涨停
    real_time_quotes_now_sh_04_02_zt = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily04'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] < sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] >= sh_small_normal_k_line_param['zt_chg'])]

    if data_frame_util.is_not_empty(real_time_quotes_now_sh_04_02_zt):
        real_time_quotes_now_sh.loc[
            real_time_quotes_now_sh['symbol'].isin(list(real_time_quotes_now_sh_04_02_zt['symbol'])),
            'exclude'] = True

    # 04 03 02 涨停
    real_time_quotes_now_sh_04_03_02_zt = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily04'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] >= sh_small_normal_k_line_param['zt_chg'])]

    if data_frame_util.is_not_empty(real_time_quotes_now_sh_04_03_02_zt):
        real_time_quotes_now_sh.loc[
            real_time_quotes_now_sh['symbol'].isin(list(real_time_quotes_now_sh_04_03_02_zt['symbol'])),
            'exclude'] = True

    return real_time_quotes_now_sh


def handle_05_day_zt(real_time_quotes_now_sh):
    real_time_quotes_now_sh_05_zt = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily05'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily04'] < sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] < sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] < sh_small_normal_k_line_param['zt_chg'])]
    # 只有05日涨停
    for stock_one in real_time_quotes_now_sh_05_zt.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one.close_last

            history_data = stock_one.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_05_df = history_data_df.iloc[4:5]
            daily_05_close = list(daily_05_df['close'])[0]
            # 当前收盘价格高于05日涨停价格 排除
            if close_last > daily_05_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理05日涨停数据异常:{},{}", e, stock_one.symbol)
    real_time_quotes_now_sh_05_04_zt = real_time_quotes_now_sh.loc[
        (real_time_quotes_now_sh['daily05'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily04'] >= sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily03'] < sh_small_normal_k_line_param['zt_chg'])
        & (real_time_quotes_now_sh['daily02'] < sh_small_normal_k_line_param['zt_chg'])]

    # 04 05日涨停
    for stock_one_04_05 in real_time_quotes_now_sh_05_04_zt.itertuples():
        try:
            # 当前收盘价格
            close_last = stock_one_04_05.close_last

            history_data = stock_one_04_05.history_data
            history_data_df = pd.read_csv(StringIO(history_data), delim_whitespace=True)
            daily_04_df = history_data_df.iloc[3:4]
            daily_04_close = list(daily_04_df['close'])[0]
            # 当前收盘价格高于04日涨停价格 排除
            if close_last > daily_04_close:
                real_time_quotes_now_sh.loc[
                    real_time_quotes_now_sh['symbol'] >= stock_one_04_05.symbol, 'exclude'] = True

        except BaseException as e:
            logger.error("处理05日涨停数据异常:{},{}", e, stock_one_04_05.symbol)

    # 最近五天有三板以上的
    real_time_quotes_now_sh_05_exclude = real_time_quotes_now_sh.loc[
        ((real_time_quotes_now_sh['daily05'] >=
          sh_small_normal_k_line_param['zt_chg'])
         & (real_time_quotes_now_sh['daily04'] >=
            sh_small_normal_k_line_param['zt_chg'])
         & (real_time_quotes_now_sh['daily03'] >=
            sh_small_normal_k_line_param['zt_chg'])
         & (real_time_quotes_now_sh['daily02'] <
            sh_small_normal_k_line_param['zt_chg']))

        | (
                (real_time_quotes_now_sh['daily05'] >=
                 sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily04'] >=
                   sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily03'] >=
                   sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily02'] >=
                   sh_small_normal_k_line_param['zt_chg'])
        )
        | (  # 05 04 02 涨停
                (real_time_quotes_now_sh['daily05'] >=
                 sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily04'] >=
                   sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily03'] <=
                   sh_small_normal_k_line_param['zt_chg'])
                & (real_time_quotes_now_sh['daily02'] >=
                   sh_small_normal_k_line_param['zt_chg'])
        )
        ]

    if data_frame_util.is_not_empty(real_time_quotes_now_sh_05_exclude):
        real_time_quotes_now_sh.loc[
            real_time_quotes_now_sh['symbol'].isin(list(real_time_quotes_now_sh_05_exclude['symbol'])),
            'exclude'] = True
    return real_time_quotes_now_sh
