import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from cacheout import Cache
import time

# ttl – Default TTL for all cache entries. Defaults to 0 which means that entries do not expire.
cache = Cache(maxsize=1024 * 4, ttl=21600, timer=time.time, default=None)


def set_cache(key, value):
    cache.set(key, value)


def get_cache(key):
    return cache.get(key)


def delete_cache(key):
    cache.delete(key)


def set_cache_time_out(key, value, time_out):
    cache.set(key, value, time_out)


if __name__ == '__main__':
    set_cache_time_out("test", 'success', 3)
    time.sleep(1)
    print(get_cache('test'))
    time.sleep(3)
    print(get_cache('test'))
