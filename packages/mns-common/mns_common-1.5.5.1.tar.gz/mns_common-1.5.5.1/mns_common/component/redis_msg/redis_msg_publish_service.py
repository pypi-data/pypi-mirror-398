import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import redis

# 连接到Redis服务器
r = redis.Redis(host='localhost', port=6379, db=0)


# 发送消息
def send_redis_msg(topic, message):
    # 将消息推送到队列中
    r.publish(topic, message)
