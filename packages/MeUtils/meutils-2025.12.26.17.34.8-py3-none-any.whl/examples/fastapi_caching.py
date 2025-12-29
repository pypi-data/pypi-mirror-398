#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fastapi_caching
# @Time         : 2024/7/24 08:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from starlette.requests import Request
from starlette.responses import Response

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from redis import asyncio as aioredis

router = APIRouter()


@cache()
async def get_cache():
    return 1

#
# @router.get("/")
# @cache(expire=60)
# async def index():
#     return dict(hello="world")
#
#
# @asynccontextmanager
# async def lifespan(_: FastAPI) -> AsyncIterator[None]:
#     redis = aioredis.from_url("redis://localhost")
#     FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
#     yield
#
#
#
# if __name__ == '__main__':
#     from meutils.serving.fastapi import App
#
#     app = App(lifespan=lifespan)
#
#     app.include_router(router, '')
#
#     app.run()
#     # for i in range(10):
#     #     send_message(f"兜底模型", title="github_copilot")


arun(get_cache())