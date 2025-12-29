import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

# 同花顺概念 有代码 可以添加同花顺客户端
SELF_CHOOSE_THS_CONCEPT = 'ths_concept'

# 同花顺行业  有代码 可以添加同花顺客户端
SELF_CHOOSE_THS_INDUSTRY = 'ths_industry'

# 本地行业
LOCAL_INDUSTRY = 'local_industry'

# sw一级行业
SW_FIRST_INDUSTRY = 'sw_first_industry'


# sw二级行业
SW_SECOND_INDUSTRY = 'sw_second_industry'

# sw三级级行业
SW_THIRD_INDUSTRY = 'sw_third_industry'

# 开盘啦一级概念
SELF_CHOOSE_KPL_FIRST_CONCEPT = 'kpl_first_concept'

# 开盘啦二级概念
SELF_CHOOSE_KPL_SECOND_CONCEPT = 'kpl_second_concept'
