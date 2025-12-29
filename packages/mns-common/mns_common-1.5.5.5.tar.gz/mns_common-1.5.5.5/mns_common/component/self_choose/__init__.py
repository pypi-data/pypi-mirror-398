import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import requests


def get_qq_hang_qing():
    url = 'https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?_appver=11.17.0&board_code=aStock&sort_type=turnover&direct=down&offset=1&count=1'
    return requests.get(url)


if __name__ == '__main__':
    while True:
        r = get_qq_hang_qing()
        print(r.status_code)
