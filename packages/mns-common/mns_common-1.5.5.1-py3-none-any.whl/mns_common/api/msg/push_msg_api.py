import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import json
import pandas as pd
import requests


token_list = ['AT_WfcsTxfwZT4LxXAhblyVsj4Zsu0x2iZW', 'AT_vL1h0mFSHtyRvbAED2mRozcEj8eFm4xh']

token_df = pd.DataFrame([
    ['AT_vL1h0mFSHtyRvbAED2mRozcEj8eFm4xh', 'UID_vqzsUn5qXDROV2dbIZuZrioewJ9D'],
    ['AT_FXkVqdVKZPFI6AabVqCouEAZPXdupERN', 'UID_8iDrFBd754aBgKHTeWcGofW8clRn']

], columns=['token',
            'uids'
            ])


# token= AT_vL1h0mFSHtyRvbAED2mRozcEj8eFm4xh
def push_msg_to_wechat(title, msg):
    for token_one in token_df.itertuples():
        appToken = token_one.token
        uids = token_one.uids
        # push = PushDeer(pushkey=appToken)
        # push.send_text(title, desp=msg)

        url = 'http://wxpusher.zjiecode.com/api/send/message'

        s = json.dumps({'appToken': appToken,
                        'content': msg,
                        'summary': title,
                        'contentType': 1,
                        'uids': [uids]
                        })
        headers = {
            "Content-Type": "application/json"
        }

        r= requests.post(url, data=s, headers=headers)
        print(r)


if __name__ == '__main__':
    push_msg_to_wechat('test', 'big win')
