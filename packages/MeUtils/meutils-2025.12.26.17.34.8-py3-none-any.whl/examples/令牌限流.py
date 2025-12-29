#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 令牌限流
# @Time         : 2023/11/28 10:36
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

import time
from ratelimiter import RateLimiter


def limited(until):
    duration = int(round(until - time.time()))
    print('Rate limited, sleeping for {:d} seconds'.format(duration))


max_calls, period = '1/3'.split('/')

# 3秒之内只能访问2次
rate_limiter = RateLimiter(max_calls=2, period=3, callback=limited)

# for i in range(3):
#     with rate_limiter:
#         print('Iteration', i)



def limit_rate(max_calls, period):
    def decorator(func):
        limiter = RateLimiter(max_calls=max_calls, period=period)

        def wrapper(*args, **kwargs):
            with limiter:
                return func(*args, **kwargs)

        return wrapper
    return decorator

@limit_rate(max_calls=5, period=10)
def my_function():
    print("Function called")

# 测试
for _ in range(7):
    my_function()
    time.sleep(2)