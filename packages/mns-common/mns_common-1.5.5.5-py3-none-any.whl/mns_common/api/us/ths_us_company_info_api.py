import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

# 同花顺 美股地址:https://basic.10jqka.com.cn/168/PINS/company.html
