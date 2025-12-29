import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import os


# 查找文件详细路径
def find_file_path(file_name, search_path):
    for root, dirs, files in os.walk(search_path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None
    # 示例用法


# 查找文件加详细路径
def find_folder_path(folder_name, search_path):
    for root, dirs, files in os.walk(search_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None


# 示例用法


if __name__ == '__main__':
    file_name1 = "userdata_mini"  # 你要查找的 exe 文件名
    search_path1 = "D:\\"  # 搜索的起始路径
    exe_path = find_folder_path(file_name1, search_path1)
    if exe_path:
        print(f"找到 {file_name1} 文件路径: {exe_path}")
    else:
        print(f"未找到 {search_path1} 文件路径")
