import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

import json
from datetime import datetime
import requests
import pandas as pd
from loguru import logger

'''
concept_code:概念代码
code_list:概念对应下组成代码 长度小于898
获取概念入选详情
'''


def get_concept_explain(concept_code, code_list):
    # Define the URL and headers
    url = "http://eq.10jqka.com.cn/plateTimeSharing/index.php"
    params = {
        "con": "concept",
        "act": "getAnalysisData",
        "codeList": code_list,
        "plateCode": concept_code
    }
    headers = {
        "Host": "eq.10jqka.com.cn",
        "Accept": "*/*",
        "Cookie": 'IFUserCookieKey={"userid":"6039843748",'
                  '"escapename":"%25u666f%25u884cpM"};'
                  ' v=A-iUPPjIGuc01TZjuSWY1OIHvdz_EUwbLnUgn6IZNGNW_YfDSiEcq36F8CTx; '
                  'hxmPid=hqMarketPkgVersionControl; '
                  'escapename=%25u666f%25u884cpM;'
                  ' ticket=64f17cffa039bb0b46189c21f97036c6; '
                  'u_name=%BE%B0%D0%D0pM;'
                  ' user=MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoyNzo6OjYwMzk4NTQ0ODoxNzE4MTU2MTE4Ojo6MTYzNDU2Njk4MDoyNjc4NDAwOjA6MTQwNDg3ODkxMWJmY2IzYTVlZjcwOWIxMDdiYTQ2YjVhOjox; '
                  'user_status=0; userid=6039843748; voiceStatus=open',
        "User-Agent": "IHexin/11.50.61 (iPhone; iOS 17.5.1; Scale/3.00)",
        "Accept-Language": "zh-Hans-CN;q=1, en-GB;q=0.9, en-CN;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    try:
        # Make the GET request
        response = requests.get(url, headers=headers, params=params)

        # Print the response content
        result_json = response.json()
        status_code = result_json['status_code']
        status_msg = result_json['status_msg']
        if status_code == 0 and status_msg == 'ok':
            result_data = result_json['data']
            result_data_df = pd.DataFrame(result_data)
            return result_data_df
        else:
            return None
    except BaseException as e:
        logger.error("获取新概念入选信息异常:{}", e)
        return None


# 获取同花顺新概念信息--APP 端接口 容易被封
def get_ths_concept_detail_by_app(symbol: str = "886019") -> pd.DataFrame:
    current_time = datetime.now()
    # 将时间格式化成 Sat, 15 Jun 2024 02:18:53 GMT 这样的格式
    formatted_time = current_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
    try:
        url = f'https://d.10jqka.com.cn/v2/blockrank/{symbol}/199112/d1000.js'
        # headers = {
        #     'Host': 'd.10jqka.com.cn',
        #     'Connection': 'keep-alive',
        #     'Accept': 'text/javascript, application/javascript, application/x-javascript',
        #     'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a13) XWEB/9165 Flue",
        #     'Origin': 'https://m.10jqka.com.cn',
        #     'Sec-Fetch-Dest': 'empty',
        #     'Sec-Fetch-Mode': 'cors',
        #     'Sec-Fetch-Site': 'same-site',
        #     'Referer': 'https://m.10jqka.com.cn',
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Accept-Language': 'zh-CN,zh;q=0.9',
        #     'If-Modified-Since': formatted_time
        # }

        headers = {
            'Accept': 'text/javascript, application/javascript, application/x-javascript',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'd.10jqka.com.cn',
            'Origin': 'https://m.10jqka.com.cn',
            'Referer': 'https://m.10jqka.com.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        r = requests.get(url, headers=headers)
        result = r.content.decode("unicode-escape")

        start_index = result.index('{"block"')
        end_index = result.index('}]}')

        result = result[start_index:end_index + 3]

        data_json = json.loads(result)
        block = data_json['block']
        items = data_json['items']

        items_df = pd.DataFrame(items)
        items_df = items_df.rename(columns={
            "5": "symbol",
            "199112": "chg",
            "264648": "change",
            "2034120": "pe",
            "3475914": "flow_mv",
            "3541450": "total_mv",
            "1968584": "exchange",
            "10": "now_price",
            "7": "open",
            "8": "high",
            "9": "low",
            "13": "volume",
            "19": "amount",
            "55": "name",
            "6": "last_day_price",

        })
        items_df['concept_code'] = symbol
        items_df['concept_name'] = block['name']
        items_df['index'] = 0
        items_df['pct_chg'] = 0
        items_df['q_ratio'] = 0

        if 'change' not in items_df.columns:
            items_df['change'] = 0
        if 'exchange' not in items_df.columns:
            items_df['exchange'] = 0
        if 'q_ratio' not in items_df.columns:
            items_df['q_ratio'] = 0
        if 'pct_chg' not in items_df.columns:
            items_df['pct_chg'] = 0
        if 'pe' not in items_df.columns:
            items_df['pe'] = 0
        if 'flow_mv' not in items_df.columns:
            items_df['flow_mv'] = 0
        if 'total_mv' not in items_df.columns:
            items_df['total_mv'] = 0

        items_df = items_df[
            [
                'index',
                'symbol',
                'name',
                'now_price',
                'chg',
                'change',
                'exchange',
                'q_ratio',
                'pct_chg',
                'amount',
                'flow_mv',
                'total_mv',
                'pe',
                'concept_code',
                'concept_name',
            ]
        ]

        return items_df
    except BaseException as e:
        logger.error("(通过app分享链接)获取新概念信息异常:{},{}", symbol, e)
        return None


if __name__ == '__main__':
    ths_concept_detail = get_ths_concept_detail_by_app('881165')
    print(ths_concept_detail)
