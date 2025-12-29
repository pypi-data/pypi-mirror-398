import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 7
project_path = file_path[0:end]
sys.path.append(project_path)

# 股票类型
sh_small_normal_k_line_param = {
    # 涨停
    'zt_chg': 9
}
