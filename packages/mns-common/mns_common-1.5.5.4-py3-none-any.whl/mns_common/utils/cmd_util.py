import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import re
import psutil
import subprocess
import pandas as pd
from loguru import logger

'''
cmd 操作方法
'''


# 执行bat文件 打开新的cmd窗口
def open_bat_file(bat_file):
    # 使用 subprocess 模块执行批处理文件
    try:
        subprocess.Popen(bat_file, creationflags=subprocess.CREATE_NEW_CONSOLE)
    except BaseException as e:
        logger.error("Error occurred:{}", e)


# 获取所有cmd bat窗口
def get_cmd_processes():
    cmd_processes_df = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'cmd.exe':
                process_pid = proc.pid
                process_name = proc.info['name']
                if len(proc.cmdline()) == 3:

                    sub_process_path = proc.cmdline()[2]
                    sub_process_path = sub_process_path.replace(' ', '')
                    sub_process_name = extract_bat_filename(sub_process_path)
                else:
                    sub_process_path = '/'
                    sub_process_name = ''
                if sub_process_name is None:
                    continue
                total_info = "".join(proc.cmdline())
                dict_result = {
                    "process_pid": process_pid,
                    "process_name": process_name,
                    "sub_process_path": sub_process_path,
                    "sub_process_name": sub_process_name,
                    "total_info": total_info
                }
                result_df = pd.DataFrame(dict_result, index=[0])
                if cmd_processes_df is None:
                    cmd_processes_df = result_df
                else:
                    cmd_processes_df = pd.concat([result_df, cmd_processes_df])

        except BaseException as e:
            logger.error("Error occurred:{}", e)
    return cmd_processes_df


# 关闭进程by pid
def kill_process_by_pid(pid):
    # 构建命令
    command = f'taskkill /PID {pid} /F'

    # 以管理员权限运行命令
    subprocess.run(command, shell=True, check=True)


# 关闭进程通过名称
def kill_process_by_name(process_name):
    # 遍历所有进程
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 如果进程名称匹配，则终止该进程
            if proc.info['name'] == process_name:
                proc.kill()
                logger.info("Process {} with PID {} has been terminated.", process_name, proc.pid)
        except BaseException as e:
            logger.error("Error occurred:{}", e)


# 提取bat 后缀开结尾的
def extract_bat_filename(path):
    # 定义正则表达式模式
    pattern = re.compile(r'\\([^\\]+\.bat)$')

    # 搜索匹配的字符串
    match = pattern.search(path)

    if match:
        return match.group(1)  # 返回匹配的部分
    else:
        return None


# 获取所有进程
def get_all_process():
    all_process_df = None
    # 获取所有当前运行的进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            process_pid = proc.pid
            process_name = proc.info['name']
            if len(proc.cmdline()) == 3:

                sub_process_path = proc.cmdline()[2]
                sub_process_path = sub_process_path.replace(' ', '')
                sub_process_name = extract_bat_filename(sub_process_path)
            else:
                sub_process_path = '/'
                sub_process_name = ''
            if sub_process_name is None:
                continue
            total_info = "".join(proc.cmdline())
            result = {"process_pid": process_pid,
                      "process_name": process_name,
                      "sub_process_path": sub_process_path,
                      "sub_process_name": sub_process_name,
                      "total_info": total_info}
            result_df = pd.DataFrame(result, index=[0])
            if all_process_df is None:
                all_process_df = result_df
            else:
                all_process_df = pd.concat([all_process_df, result_df])
        except BaseException as e:
            pass
    return all_process_df


# 进程是否运行
def is_process_running(process_name):
    # 获取所有当前运行的进程
    for proc in psutil.process_iter(['name']):
        try:
            # 检查进程名称是否匹配
            if proc.info['name'] == process_name:
                return True
        except BaseException as e:
            logger.error("Error occurred:{}", e)
    return False


if __name__ == '__main__':
    #
    cmd_processes_df_list = get_all_process()
    print(cmd_processes_df_list)
