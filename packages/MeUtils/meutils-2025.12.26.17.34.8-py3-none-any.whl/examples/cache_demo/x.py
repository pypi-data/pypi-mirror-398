# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : x
# @Time         : 2024/12/12 19:05
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.caches.redis_cache import cache

if __name__ == '__main__':
    @cache
    def func(x):
        time.sleep(3)
        logger.debug('没缓存')

        return x


    class Request(BaseModel):
        a: str = "a"

        class Config:
            frozen = True


    arun(func(1))
    # arun(func_ignore(1, 11))
