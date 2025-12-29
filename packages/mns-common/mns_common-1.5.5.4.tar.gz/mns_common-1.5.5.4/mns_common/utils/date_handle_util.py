import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from datetime import datetime, time
from datetime import timedelta
from functools import lru_cache
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')


@lru_cache(maxsize=None)
def is_trade_date(str_now_day):
    query_trade_date = {'_id': str_now_day}
    return mongodb_util.exist_data_query('trade_date_list', query_trade_date)


def is_afternoon_time(now_date):
    hour = now_date.hour
    return hour >= 13


def is_begin_one_hour(now_date):
    hour = now_date.hour
    minute = now_date.minute
    return ((hour == 9 and minute >= 30) or
            (hour == 10 and minute < 30))


def is_end_trade_ten_minute(now_date):
    hour = now_date.hour
    minute = now_date.minute
    weekday = now_date.isoweekday()
    no_trade_time = (hour >= 9 and minute >= 40) or weekday == 6 or weekday == 7
    return no_trade_time


def is_end_trade(now_date):
    hour = now_date.hour
    minute = now_date.minute
    weekday = now_date.isoweekday()
    no_trade_time = (hour >= 15 and minute >= 1) or weekday == 6 or weekday == 7
    return no_trade_time


def is_no_trade_time(now_date):
    hour = now_date.hour
    minute = now_date.minute
    weekday = now_date.isoweekday()
    no_trade_time = (
            (hour >= 15 and minute >= 0)
            or weekday == 6 or weekday == 7)
    return no_trade_time


def is_close_time(now_date):
    hour = now_date.hour
    weekday = now_date.isoweekday()
    no_trade_time = (hour >= 15) \
                    or weekday == 6 or weekday == 7
    return no_trade_time


# 是否是交易时间 9:26 同步一下数据 第25 分钟的内外盘数据还会变动
def is_trade_time(now_date):
    # return True
    hour = now_date.hour
    minute = now_date.minute
    second = now_date.second
    str_now_day = now_date.strftime('%Y-%m-%d')
    is_trade_day = is_trade_date(str_now_day)
    trade_time = (hour == 9 and minute == 25 and second > 20) \
                 or (hour == 9 and minute == 26 and second < 20) \
                 or (hour == 9 and minute >= 30) \
                 or (hour == 10) \
                 or (hour == 11 and minute < 30) \
                 or (hour == 11 and minute == 30 and second < 5) \
                 or (hour == 13) \
                 or (hour == 14 and minute < 57) \
                 or (hour == 15 and minute == 0 and second < 10)

    return is_trade_day and trade_time


# 是否是策略运行时间
def is_strategy_time(now_date):
    # return True
    hour = now_date.hour
    minute = now_date.minute
    second = now_date.second
    str_now_day = now_date.strftime('%Y-%m-%d')
    is_trade_day = is_trade_date(str_now_day)
    trade_time = (hour == 9 and minute == 25 and second > 10) \
                 or (hour == 9 and minute == 26 and second < 10) \
                 or (hour == 9 and minute >= 30) \
                 or (hour == 10) \
                 or (hour == 11 and minute < 30) \
                 or (hour == 13) \
                 or (hour == 14) \
                 or (hour == 15 and minute < 0)

    return is_trade_day and trade_time


# 是否是交易时间
def is_trade_time_save_data(now_date):
    hour = now_date.hour
    minute = now_date.minute
    weekday = now_date.isoweekday()
    str_now_day = now_date.strftime('%Y-%m-%d')
    is_trade_day = is_trade_date(str_now_day)
    no_trade_time = hour < 9 or (hour == 9 and minute < 30) or (
            hour == 11 and minute > 30) or hour == 12 or (hour >= 15 and minute >= 1) or weekday == 6 or weekday == 7

    first_sync = hour == 9 and minute == 26
    return (is_trade_day and bool(1 - no_trade_time)) or first_sync


# 是否是开盘时间 包含集合竞价
def is_open_time(now_date):
    hour = now_date.hour
    minute = now_date.minute
    weekday = now_date.isoweekday()
    str_now_day = now_date.strftime('%Y-%m-%d')
    is_trade_day = is_trade_date(str_now_day)
    no_trade_time = hour < 9 or (hour == 9 and 25 < minute < 30) or (hour == 9 and minute < 15) or \
                    (hour == 11 and minute > 30) or hour == 12 or hour >= 15 or weekday == 6 or weekday == 7
    return is_trade_day and bool(1 - no_trade_time)


def add_date(date_str, add_count=1):
    date = datetime.strptime(date_str, '%Y-%m-%d')
    new_date = date + timedelta(days=add_count)

    new_str_day = new_date.strftime('%Y-%m-%d')
    return new_str_day


def add_date_day(date_str, add_count=1):
    date = datetime.strptime(date_str, '%Y%m%d')
    new_date = date + timedelta(days=add_count)
    return new_date


def str_to_date(date_str, for_mart):
    date_time = datetime.strptime(date_str, for_mart)
    return date_time


def lash_date(date_str):
    date_time_begin = datetime.strptime(date_str, '%Y%m%d')
    date_str = date_time_begin.strftime('%Y-%m-%d')
    return date_str


# 已经交易的时间
def calculate_had_trade_minute(now_date):
    hour = now_date.hour
    minute = now_date.minute
    trade_minute = 1
    if hour == 9:
        if minute == 30:
            trade_minute = 1
        elif minute > 30:
            trade_minute = minute - 30
        else:
            trade_minute = 1
    elif hour == 10:
        trade_minute = minute + 30
    elif hour == 11:
        if minute <= 30:
            trade_minute = minute + 30 + 60
        elif minute > 30:
            trade_minute = 120
    elif hour == 12:
        trade_minute = 120
    elif hour == 13:
        trade_minute = minute + 30 + 30 + 60
    elif hour == 14:
        trade_minute = minute + 30 + 30 + 60 + 60
    elif hour < 9:
        trade_minute = 0
    elif hour >= 15:
        trade_minute = 60 + 60 + 60 + 60
    return trade_minute


def no_slash_date(date='-'):
    date = str(date)
    date = date.replace('-', '')
    return date


def calculate_mouth(date):
    return date.month


def calculate_year(date):
    return date.year


def last_day_of_week(date):
    return date.weekday() == 4


def last_day_month(date):
    month = date.month
    day = date.day
    if month in [1, 3, 5, 7, 8, 10, 12] and day == 31:
        return True
    elif month in [4, 6, 9, 11] and day == 30:
        return True
    elif run_nian(date) and month == 2 and day == 29:
        return True
    elif bool(1 - run_nian(date)) and month == 2 and day == 28:
        return True
    return False


def run_nian(date):
    year = date.year
    if (year % 4) == 0:
        if (year % 100) == 0:
            if (year % 400) == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False


def days_diff(d1, d2):
    return (d1 - d2).days


def is_call_auction(str_now_date):
    now_date = str_to_date(str_now_date, "%Y-%m-%d %H:%M:%S")
    now_date_time = now_date.time()
    target_time_09_30 = time(9, 30)
    if now_date_time > target_time_09_30:
        return False
    else:
        return True


def is_new_concept_sync_time(now_date):
    # return True
    hour = now_date.hour
    if hour < 8 or hour > 15:
        return False
    return True


if __name__ == '__main__':
    is_call_auction("2023-07-05 09:29:01")
