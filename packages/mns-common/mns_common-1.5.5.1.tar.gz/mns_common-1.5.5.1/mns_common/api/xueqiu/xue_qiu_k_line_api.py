import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import pandas as pd


# year 年
#  quarter 季度
# month 月度
# week 周
# day 日
def get_xue_qiu_k_line(symbol, period, cookie, end_time, hq):
    url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"

    params = {
        "symbol": symbol,
        "begin": end_time,
        "period": period,
        "type": hq,
        "count": "-120084",
        "indicator": "kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "origin": "https://xueqiu.com",
        "priority": "u=1, i",
        "referer": "https://xueqiu.com/S/SZ300879?md5__1038=n4%2BxgDniDQeWqxYwq0y%2BbDyG%2BYDtODuD7q%2BqRYID",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "cookie": cookie
    }

    response = requests.get(
        url=url,
        params=params,
        headers=headers
    )

    if response.status_code == 200:
        response_data = response.json()
        df = pd.DataFrame(
            data=response_data['data']['item'],
            columns=response_data['data']['column']
        )

        # 1. 转换为 datetime（自动处理毫秒级时间戳）
        df["beijing_time"] = pd.to_datetime(df["timestamp"], unit="ms")

        # 2. 设置 UTC 时区
        df["beijing_time"] = df["beijing_time"].dt.tz_localize("UTC")

        # 3. 转换为北京时间（UTC+8）
        df["beijing_time"] = df["beijing_time"].dt.tz_convert("Asia/Shanghai")

        # 4. 提取年月日（格式：YYYY-MM-DD）
        df["str_day"] = df["beijing_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        del df["beijing_time"]

        return df
    else:
        # 直接抛出带有明确信息的异常
        raise ValueError("调用雪球接口失败")


if __name__ == '__main__':
    number = 1
    cookies ='cookiesu=291756518429127; device_id=8c5eef4332e51dbcbcd92943b0dd91e4; s=bz17174k1c; xq_a_token=b9c7e702181cba3ed732d5019efe2dfe2fb054b0; xqat=b9c7e702181cba3ed732d5019efe2dfe2fb054b0; xq_r_token=c1edaf05e1c6fdf8122671eced8049e8df8a4290; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc2MTYxNDEwNywiY3RtIjoxNzU5OTc2NzUxOTI3LCJjaWQiOiJkOWQwbjRBWnVwIn0.JwQMnAT6E1lPSqfK-GnFpLNQz-Jr-xtZ6HoUfnCfeRTNKrDJqf0l5_iY7dhEo6A5m38MmXj0hgR-xYkzPm35fFcQCQnZ06dOK0XCP6AE9r5KVFd73GyqbXLijKDFPQVM0sPgbgCs9fTOmB7Nlju_7B_raPmZ8IIHzZRU6uSK9oXsrnwpo4TD0Mr2nMF3ktVwEQHdkZsjm9mdSZaT9fkDvayFKKmg_O-JbHDZ6mTF1i-zR6oH-5r3g6HJJU9-_NwzZMeBEVnLG8IWwO8_n9CWdpbqQ-qC-iue4yEHFdiTLBCRRgyFauVv0kJS1ZNKvvefxkETTVr-WgXobT82ED7ApA; u=291756518429127; Hm_lvt_1db88642e346389874251b5a1eded6e3=1759765103,1759808830,1759970243,1759976801; HMACCOUNT=4C4F802C04F4D70A; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1759978805'
    while True:
        test_df = get_xue_qiu_k_line('SZ300188', '1m', cookies, '1760065317680', '')
        print(number)
        number = number + 1
