import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
WINDOWS_MAC_ADDRESS_CD = '04-33-C2-67-85-8B'
APPLE_AIR_MAC_ADDRESS = '74:0e:a4:7a:79:cd'

import psutil
import socket


def get_host_ip():
    """
    查询本机ip地址
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


# 获取当前主机物理地址 mac
def get_mac_address():
    # Get all interfaces
    interfaces = psutil.net_if_addrs()
    for interface, address_list in interfaces.items():
        stats = psutil.net_if_stats()[interface]
        if stats.isup:
            for addr in address_list:
                if addr.family == psutil.AF_LINK:
                    return addr.address

    return None
