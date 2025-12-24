import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import requests

'''
announce_type = all
业绩预告
announce_type ='eq-f1001'
重大事项
announce_type ='eq-f1002'
股份变动公告
announce_type ='eq-f1003'

'''


# 公司公告数据
def get_company_announce_info(symbol, market_id, announce_type, page_size, page_number):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://basic.10jqka.com.cn/new/" + str(symbol) + "/news.html",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "hexin-v": "A26_5Ky-hXryQvEeROXOP_Umv881bzAERDPmR5g32nEsewBxAP-CeRTDNldr",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "searchGuide": "sg",
        "Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1": "1729691262",
        "skin_color": "white",
        "historystock": "870357%7C*%7C833781%7C*%7C873576%7C*%7C835892%7C*%7C873693",
        "reviewJump": "nojump",
        "usersurvey": "1",
        "v": "A26_5Ky-hXryQvEeROXOP_Umv881bzAERDPmR5g32nEsewBxAP-CeRTDNldr"
    }
    url = "https://basic.10jqka.com.cn/basicapi/notice/pub"
    params = {
        "type": "stock",
        "limit": str(page_size),
        "page": str(page_number),
        "code": str(symbol),
        "classify": announce_type,
        "market": str(market_id)
    }
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    data_json = response.json()
    temp_df = pd.DataFrame(data_json["data"]["data"])
    return temp_df


if __name__ == '__main__':
    get_company_announce_info('300085', '33', 'eq-f1003', 100, 1)
