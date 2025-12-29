import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
from datetime import datetime
import pandas as pd
import requests
import json
import execjs
from loguru import logger
import mns_common.api.msg.push_msg_api as push_msg_api
script_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接文件名
file_path = os.path.join(script_dir, 'ths.js')
'''
操作ths 自选股票
'''


def get_js_code():
    '''
    获取js
    :return:
    '''
    '''
       获取js
       :return:
       '''
    with open(file_path) as f:
        comm = f.read()
    com_result = execjs.compile(comm)
    result = com_result.call('v')
    return result


def get_headers(cookie):
    '''
    获取请求头
    :param cookie:
    :return:
    '''
    v = get_js_code()
    cookie_js = cookie.split('v=')
    cookie_js = cookie_js[0] + 'v=' + v
    headers = {
        'Cookie': cookie_js,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
    }
    return headers


# 获取所有自选股票
def get_all_self_choose_stock_list(cookie):
    '''
    获取全部自选股
    :param cookie:
    :return:
    '''

    headers = get_headers(cookie)
    url = 'https://t.10jqka.com.cn/newcircle/group/getSelfStockWithMarket/?'
    now_date = datetime.now()
    now_time = int(now_date.timestamp() * 1000)
    now_time = str(now_time)
    params = {
        'callback': 'selfStock',
        '_': now_time
    }
    res = requests.get(url=url, params=params, headers=headers)
    text = res.text[10:len(res.text) - 2]
    json_text = json.loads(text)
    df = pd.DataFrame(json_text['result'])
    return df


# 添加自选股
def add_stock_to_account(stock, cookie):
    '''
    添加股票到自选股
    :param stock:
    :param cookie:
    :return:
    '''
    now_date = datetime.now()
    now_time = int(now_date.timestamp() * 1000)
    now_time = str(now_time)
    url = 'https://t.10jqka.com.cn/newcircle/group/modifySelfStock/?'
    headers = get_headers(cookie)
    params = {
        'callback': 'modifyStock',
        'op': 'add',
        'stockcode': stock,
        '_': now_time,
    }
    res = requests.get(url=url, params=params, headers=headers)
    text = res.text[12:len(res.text) - 2]
    json_text = json.loads(text)
    err = json_text['errorMsg']
    if err == '修改成功':
        logger.info('{}加入自选股成功', stock)

    elif '当前用户未登录' in err:
        push_msg_api.push_msg_to_wechat('加入自选股失败', err)
        logger.error('{}加入自选股失败,{}', stock, err)
    else:
        logger.error('{}加入自选股失败,{}', stock, err)


# 删除自选股
def del_stock_from_account(stock, cookie):
    '''
    删除股票从自选股
     :param stock:
    :param cookie:
    :return:
    '''
    url = 'https://t.10jqka.com.cn/newcircle/group/modifySelfStock/?'
    headers = get_headers(cookie)
    try:
        params = {
            'op': 'del',
            'stockcode': stock
        }
        res = requests.get(url=url, params=params, headers=headers)
        text = res.text
        json_text = json.loads(text)
        err = json_text['errorMsg']
        if err == '修改成功':
            logger.info('{}删除自选股成功', stock)
        elif '当前用户未登录' in err:
            push_msg_api.push_msg_to_wechat('加入自选股失败', err)
            logger.error('{}加入自选股失败,{}', stock, err)
        else:
            logger.error('{}删除自选股失败,{}', stock, err)
    except BaseException as e:
        logger.error('{}删除自选股异常,{}', stock, e)


import mns_common.api.ths.zt.ths_stock_zt_pool_api as ths_stock_zt_pool_api
import mns_common.component.common_service_fun_api as common_service_fun_api

if __name__ == '__main__':

    cookie_test = "searchGuide=sg; skin_color=white; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1721641603,1721715758,1721752612,1721755151; historystock=688037%7C*%7C600272%7C*%7C603939%7C*%7C601607%7C*%7C002670; log=; Hm_lvt_722143063e4892925903024537075d0d=1720407580,1720593398,1721195153,1721780857; HMACCOUNT=53655417BE159764; Hm_lvt_929f8b362150b1f77b477230541dbbc2=1720407580,1720593398,1721195153,1721780857; u_ukey=A10702B8689642C6BE607730E11E6E4A; u_uver=1.0.0; u_dpass=alFQbk%2FO8c9WqN3Z4WkYGuoYg0Z6SiiU4OnEchI5ynMcu0H9Wl0vit1Uov34KlrNHi80LrSsTFH9a%2B6rtRvqGg%3D%3D; u_did=756121025AC347DABE0B7B9BFCDC0511; u_ttype=WEB; ttype=WEB; user=MDq%2BsNDQcE06Ok5vbmU6NTAwOjYxMzk4NTQ0ODo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoyNzo6OjYwMzk4NTQ0ODoxNzIxNzgwODg1Ojo6MTYzNDU2Njk4MDo2MDQ4MDA6MDoxNzNiNDhmZjI2NmM1MzE3ZDgwYmUwYmZiMDQzMDhiZTY6ZGVmYXVsdF80OjE%3D; userid=603985448; u_name=%BE%B0%D0%D0pM; escapename=%25u666f%25u884cpM; ticket=8a8e55aeb05c9160e88dab69492aa048; user_status=0; utk=6420dd34039fbeb3d1f4bffe699ec7e4; Hm_lpvt_722143063e4892925903024537075d0d=1721780886; Hm_lpvt_929f8b362150b1f77b477230541dbbc2=1721780887; Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1721780896; Hm_lvt_da7579fd91e2c6fa5aeb9d1620a9b333=1721780896; Hm_lpvt_da7579fd91e2c6fa5aeb9d1620a9b333=1721780896; v=A2kO-7xJKzhydheMMbjLkzbIeB7GNlqaxy6B_wte4BOPXIdAU4ZtOFd6kcGY"

    res = ths_stock_zt_pool_api.get_zt_reason(None)
    res = res.loc[res['connected_boards_numbers'] > 1]
    res = common_service_fun_api.exclude_st_symbol(res)
    res = res.sort_values(by=['connected_boards_numbers'], ascending=False)
    for stock_one in res.itertuples():
        add_stock_to_account(stock_one.symbol, cookie_test)

    all_self_choose_df = get_all_self_choose_stock_list(cookie_test)

    print(all_self_choose_df)
