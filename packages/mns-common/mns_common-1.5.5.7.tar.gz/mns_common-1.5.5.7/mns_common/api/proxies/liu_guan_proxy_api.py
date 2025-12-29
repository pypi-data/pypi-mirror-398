import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger
import requests
import time
import hashlib
import json
from mns_common.db.MongodbUtil import MongodbUtil
from functools import lru_cache
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')

import random

# 提取订单
"""
    orderId:提取订单号
    secret:用户密钥
    num:提取IP个数
    pid:省份
    cid:城市
    type：请求类型，1=http/https,2=socks5
    unbindTime:使用时长，秒/s为单位
    noDuplicate:去重，0=不去重，1=去重
    lineSeparator:分隔符
    singleIp:切换,0=切换，1=不切换
"""


@lru_cache(maxsize=None)
def query_province_and_city_info():
    return mongodb_util.find_all_data(db_name_constant.IP_PROXY_CITY_PROVINCE)


def get_proxy_api(order_id, secret, unbind_time):
    province_and_city_info_df = query_province_and_city_info()
    random_row = province_and_city_info_df.sample(n=1)
    cid = str(list(random_row['cid'])[0])
    pid = str(list(random_row['pid'])[0])

    num = "1"
    noDuplicate = "1"
    lineSeparator = "0"
    singleIp = "0"
    time_str = str(int(time.time()))  # 时间戳

    # 计算sign
    txt = "orderId=" + order_id + "&" + "secret=" + secret + "&" + "time=" + time_str
    sign = hashlib.md5(txt.encode()).hexdigest()
    # 访问URL获取IP
    url = (
            "http://api.hailiangip.com:8422/api/getIp?type=1" + "&num=" + num + "&pid=" + pid
            + "&unbindTime=" + unbind_time + "&cid=" + cid
            + "&orderId=" + order_id + "&time=" + time_str + "&sign=" + sign + "&dataType=0"
            + "&lineSeparator=" + lineSeparator + "&noDuplicate=" + noDuplicate + "&singleIp=" + singleIp)
    my_response = requests.get(url).content
    js_res = json.loads(my_response)
    for dic in js_res["data"]:
        try:
            ip = dic["ip"]
            # ip = dic["realIp"]
            port = dic["port"]
            ip_port = ip + ":" + str(port)
            return ip_port
        except BaseException as e:
            logger.error("获取ip地址异常:{}", e)
            return None


# 线程池
def get_proxy_pool_api(order_id, secret, unbind_time, ip_num):
    num = str(ip_num)
    pid = "-1"
    cid = ""
    noDuplicate = "1"
    lineSeparator = "0"
    singleIp = "0"
    time_str = str(int(time.time()))  # 时间戳

    # 计算sign
    txt = "orderId=" + order_id + "&" + "secret=" + secret + "&" + "time=" + time_str
    sign = hashlib.md5(txt.encode()).hexdigest()
    # 访问URL获取IP
    url = (
            "http://api.hailiangip.com:8422/api/getIp?type=1" + "&num=" + num + "&pid=" + pid
            + "&unbindTime=" + unbind_time + "&cid=" + cid
            + "&orderId=" + order_id + "&time=" + time_str + "&sign=" + sign + "&dataType=0"
            + "&lineSeparator=" + lineSeparator + "&noDuplicate=" + noDuplicate + "&singleIp=" + singleIp)
    my_response = requests.get(url).content
    js_res = json.loads(my_response)
    ip_pool_list = []
    for dic in js_res["data"]:
        try:
            ip = dic["ip"]
            port = dic["port"]
            ip_port = ip + ":" + str(port)
            ip_pool_list.append(ip_port)
        except BaseException as e:
            logger.error("获取ip地址异常:{}", e)
            return None
    return ip_pool_list


if __name__ == '__main__':
    order_id_test = ''
    secret_test = ''
    unbind_time_test = str(60 * 10)
    ip = get_proxy_api(order_id_test, secret_test, unbind_time_test)
    print(ip)
