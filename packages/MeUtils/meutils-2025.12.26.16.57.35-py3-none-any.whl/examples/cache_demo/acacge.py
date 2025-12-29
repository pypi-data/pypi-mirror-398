#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : acacge
# @Time         : 2024/9/30 15:19
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

from aiocache import cached, Cache


from collections import namedtuple

from aiocache import RedisCache, cached, SimpleMemoryCache
from aiocache.serializers import PickleSerializer
# With this we can store python objects in backends like Redis!

# Result = namedtuple('Result', "content, status")
# redis_client = redis.Redis(host="127.0.0.1", port=6379)
# redis_cache = RedisCache(redis_client, namespace="main")

# cache = Cache.from_url(os.getenv('REDIS_URL'))

@cached(ttl=10, cache=Cache.REDIS, key="key")
async def cached_call():
    print("Sleeping for three seconds zzzz.....")
    await asyncio.sleep(3)
    return time.time()




if __name__ == '__main__':
    # arun(cached_call())
    connection_kwargs = {}
    if REDIS_URL := os.getenv("REDIS_URL"):
        user_password, base_url = REDIS_URL.split("@")
        endpoint, port = base_url.split(':')
        password = user_password.split(":")[-1]

        connection_kwargs['endpoint'] = endpoint
        connection_kwargs['port'] = port
        connection_kwargs['password'] = password

    cache = RedisCache(**connection_kwargs)

    arun(cache.set('keykeykeykeykeykey', 'value'))
    arun(cache.get('key'))
