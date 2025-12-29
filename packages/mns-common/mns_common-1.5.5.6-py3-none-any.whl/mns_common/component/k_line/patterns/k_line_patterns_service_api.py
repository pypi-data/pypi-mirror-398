import sys
import os

import mns_common.component.k_line.patterns.pattern_Enum as pattern_Enum

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)


# k线形态分类
def k_line_patterns_classify(open, close, high, low, max_chg, chg):
    if cross_star(open, close, high, low):
        return pattern_Enum.Pattern_Enum.CROSS_STAR
    elif down_over_lining(open, close, high, low):
        return pattern_Enum.Pattern_Enum.DOWN_OVER_LINING

    elif open_high_and_walk_low(open, close, high, low, max_chg, chg):
        return pattern_Enum.Pattern_Enum.OPEM_HIGH_AND_WALK_LOW

    elif up_over_lining(open, close, high, low):
        return pattern_Enum.Pattern_Enum.UP_OVER_LINING

    return pattern_Enum.Pattern_Enum.OTHER


# 十字星状态
def cross_star(open, close, high, low):
    if abs(open - close) < 0.01 * open and (high - max(open, close)) > 2 * (max(open, close) - min(open, close)) and (
            min(open, close) - low) > 2 * (max(open, close) - min(open, close)):
        return True
    else:
        return False


# 高开低走
def open_high_and_walk_low(open, close, high, low, max_chg, chg):
    if open > close and max_chg >= 7 and max_chg - chg >= 7:
        return True
    else:
        return False


# 下跌带长上影线
def down_over_lining(open, close, high, low):
    diff_chg_high = round((high - open) / open, 2)
    if open > close and diff_chg_high >= 7:
        return True
    else:
        return False


# 上涨带长上影线
def up_over_lining(open, close, high, low):
    diff_chg_high = round((high - open) / open, 2)
    if open < close and diff_chg_high >= 7:
        return True
    else:
        return False
