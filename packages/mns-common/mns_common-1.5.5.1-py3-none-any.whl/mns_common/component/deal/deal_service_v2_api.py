import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import json
import requests

'''

'''


def trade_buy(symbol, buy_price, buy_volume, terminal):
    '''
    买入
    :param symbol:
    :param buy_price:
    :param buy_volume:
    :param terminal:
    :return:
    '''
    param_buy = {
        'symbol': symbol,
        'buy_price': buy_price,
        'buy_volume': buy_volume,
        'terminal': terminal}
    param_json = json.dumps(param_buy)
    response = request_trader_post('/buy', param_json)
    if response.status_code != 200:
        buy_result = {"message": '买入失败'}
    else:
        buy_result = response.json()
    return buy_result


def trade_sell(symbol, sell_price, sell_volume, terminal):
    '''
    卖出
    :param symbol:
    :param sell_price:
    :param sell_volume:
    :param terminal:
    :return:
    '''
    param_sell = {
        'symbol': symbol,
        'sell_price': sell_price,
        'sell_volume': sell_volume,
        'terminal': terminal}
    param_json = json.dumps(param_sell)
    response = request_trader_post('/sell', param_json)
    if response.status_code != 200:
        sell_result = {"message": '卖出失败'}
    else:
        sell_result = response.json()
    return sell_result


def auto_ipo_buy(terminal):
    '''
    自动打新
    :param terminal:
    :return:
    '''
    param_auto_ipo = {
        'terminal': terminal}
    param_json = json.dumps(param_auto_ipo)
    response = request_trader_get('/auto/ipo/buy', param_json)
    if response.status_code != 200:
        result = {"message": '自动打新失败'}
    else:
        result = response.json()
    return result


def get_position(terminal):
    '''
    获取持仓
    :param terminal:
    :return:
    '''
    param_position = {
        'terminal': terminal}
    param_json = json.dumps(param_position)
    response = request_trader_get('/position', param_json)
    if response.status_code != 200:
        result = {"message": '获取持仓失败'}
    else:
        result = response.json()
    return result


def order_cancel(entrust_no, terminal):
    '''
    撤单
       :param entrust_no:
    :param terminal:
    :return:
    '''
    param_cancel = {
        "entrust_no": entrust_no,
        'terminal': terminal}
    param_json = json.dumps(param_cancel)
    response = request_trader_post('/cancel', param_json)
    if response.status_code != 200:
        result = {"message": '撤单失败'}
    else:
        result = response.json()
    return result


# 自动登陆接口
def auto_login(terminal):
    '''
      自动登陆客户端
      :param terminal:
      :return:
      '''
    param_position = {
        'terminal': terminal}
    param_json = json.dumps(param_position)
    response = request_trader_post('/auto/login', param_json)
    if response.status_code != 200:
        result = {"message": '获取持仓失败'}
    else:
        result = response.json()
    return result


def request_trader_post(url, param):
    total_url = "http://127.0.0.1:5002/api/trade" + url
    headers = {
        "Content-Type": "application/json"
    }
    return requests.post(total_url, data=param, headers=headers)


def request_trader_get(url, param):
    total_url = "http://127.0.0.1:5002/api/trade" + url
    headers = {
        "Content-Type": "application/json"
    }
    return requests.get(total_url, data=param, headers=headers)


if __name__ == '__main__':
    # auto_login('qmt')
    # get_position('qmt')
    # terminal_test = 'easy_trader'
    # order_cancel('251145121', terminal_test)
    # get_position(terminal_test)
    # auto_ipo_buy(terminal_test)
    buy_result_test = trade_buy(
        '688693.SH',
        36.39,
        1000,
        'ths')
    entrust_no_test = buy_result_test['entrust_no']
    order_cancel(entrust_no_test, 'ths')
    # trade_sell(
    #     '301314',
    #     35.77,
    #     100,
    #     'easy_trader')
