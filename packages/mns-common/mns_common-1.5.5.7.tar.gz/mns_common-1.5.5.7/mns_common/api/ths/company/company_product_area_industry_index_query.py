import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests


def company_product_area_industry(symbol, market, date):
    if date is None:
        url = (
            f"https://basic.10jqka.com.cn/basicapi/operate/index/v1/product_index_query/?code={symbol}&market={market}"
            f"&type=stock&account=1&timeField=date&analysisTypes=product,area,industry&sortIndex=income&currency=CNY&level=1&expands=product_introduction&locale=zh_CN")
    else:

        url = (
            f"https://basic.10jqka.com.cn/basicapi/operate/index/v1/product_index_query/?code={symbol}&market={market}&date={date}"
            f"&type=stock&account=1&timeField=date&analysisTypes=product,area,industry&sortIndex=income&currency=CNY&level=1&expands=product_introduction&locale=zh_CN")

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }

    response = requests.get(url, headers=headers)
    data_json = response.json()
    data_list = data_json['data']
    return data_list


if __name__ == '__main__':
    company_product_area_industry('688551', '17', None)
