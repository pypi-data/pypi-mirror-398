import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import json
import requests
from loguru import logger

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
    response = request_trader('/buy', param_json)
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
    response = request_trader('/sell', param_json)
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
    response = request_trader('/auto/ipo/buy', param_json)
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
    response = request_trader('/position', param_json)
    if response.status_code != 200:
        result = {"message": '获取持仓失败'}
    else:
        try:
            result = response.json()
        except BaseException as e:
            result_test = response.text
            result = json.loads(result_test)

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
    response = request_trader('/cancel', param_json)
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
    response = request_trader('/auto/login', param_json)
    if response.status_code != 200:
        result = {"message": '获取持仓失败'}
    else:

        result = response.json()

    return result


# 查询订单
def query_orders(terminal):
    param_order = {
        'terminal': terminal}
    param_json = json.dumps(param_order)
    response = request_trader('/order', param_json)
    if response.status_code != 200:
        result = {"message": '查询订单失败'}
    else:

        result = response.json()

    return result


def request_trader(url, param):
    total_url = "http://127.0.0.1:5001/api/trade" + url
    headers = {
        "Content-Type": "application/json"
    }
    return requests.post(total_url, data=param, headers=headers)


# 获取交易价格
def get_trade_price(terminal, symbol, price_code, limit_chg):
    param_position = {
        'symbol': symbol,
        'terminal': terminal,
        'price_code': price_code,
        'limit_chg': limit_chg}

    param_json = json.dumps(param_position)
    response = request_trader('/trade/price', param_json)
    if response.status_code != 200:
        result = {"message": '获取行情失败'}
    else:
        result = response.json()
    return result


# 获取qmt 行情
def get_qmt_real_time_quotes_detail(terminal, symbol_list):
    param_position = {
        'symbol_list': symbol_list,
        'terminal': terminal}

    param_json = json.dumps(param_position)
    response = request_trader('/qmt/real/time/quotes/detail', param_json)
    if response.status_code != 200:
        result = {"message": '获取行情失败'}
    else:
        result = response.json()
    return result


from mns_common.component.deal.terminal_enum import TerminalEnum

if __name__ == '__main__':
    terminal_test = TerminalEnum.QMT.terminal_code
    get_position(terminal_test)
    symbol_one_test = ['301181.SZ']
    result_json = get_qmt_real_time_quotes_detail(terminal_test, symbol_one_test)
    print(result_json)
    # auto_login('qmt')
    # get_position('qmt')
    # terminal_test = 'easy_trader'
    # order_cancel('251145121', terminal_test)
    # get_position(terminal_test)
    # auto_ipo_buy(terminal_test)
    # trade_buy(
    #     '301314.SZ',
    #     35.77,
    #     1000000,
    #     'qmt')
    # trade_sell(
    #     '301314',
    #     35.77,
    #     100,
    #     'easy_trader')
