import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd


def is_empty(df):
    if df is None or df.shape[0] == 0:
        return True
    else:
        return False


def is_not_empty(df):
    if df is None or df.shape[0] == 0:
        return False
    else:
        return True


def is_string_empty(s):
    if s is None:
        return True
    else:
        if len(s) == 0:
            return True
        else:
            return False


def is_string_not_empty(s):
    return bool(1 - is_string_empty(s))


def merge_choose_data_no_drop(df1, df2):
    if is_empty(df1) and is_empty(df2):
        return None
    if is_not_empty(df1) and is_empty(df2):
        return df1
    if is_empty(df1) and is_not_empty(df2):
        return df2

    return pd.concat([df1, df2])


def merge_choose_data_with_drop_duplicates(df1, df2):
    if is_empty(df1) and is_empty(df2):
        return None
    if is_not_empty(df1) and is_empty(df2):
        return df1
    if is_empty(df1) and is_not_empty(df2):
        return df2

    result = pd.concat([df1, df2])

    result.drop_duplicates('symbol', keep='last', inplace=True)
    return result
