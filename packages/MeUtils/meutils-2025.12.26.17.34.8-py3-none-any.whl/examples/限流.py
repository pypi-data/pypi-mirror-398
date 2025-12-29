#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 限流
# @Time         : 2023/11/27 10:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from limits import storage
from limits import strategies
from limits import parse

memory_storage = storage.MemoryStorage()
# or memcached
memcached_storage = storage.MemcachedStorage("memcached://localhost:11211")
# or redis
redis_storage = storage.RedisStorage("redis://localhost:6379")
# or use the factory
storage_uri = "memcached://localhost:11211"
some_storage = storage.storage_from_string(storage_uri)

moving_window = strategies.MovingWindowRateLimiter(memory_storage)

one_per_minute = parse("1/minute")

from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/home")
@limiter.limit("5/minute")
async def homepage(request: Request):
    return PlainTextResponse("test")


@app.get("/mars")
@limiter.limit("5/minute")
async def homepage(request: Request, response: Response):
    return {"key": "value"}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)




