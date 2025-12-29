import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from enum import Enum


class Pattern_Enum(Enum):
    # 十字星
    CROSS_STAR = 'CROSS_STAR'
    # 下跌中的长上影线
    DOWN_OVER_LINING = 'DOWN_OVER_LINING'
    # 上涨中的长上影线
    UP_OVER_LINING = 'UP_OVER_LINING'
    # 高开低走
    OPEM_HIGH_AND_WALK_LOW = 'OPEM_HIGH_AND_WALK_LOW'

    OTHER = 'OTHER'
