#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2023/11/8 10:39
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm https://arq-docs.helpmanual.io/#install
# @Description  : 生产队列: from devtools import debug

from meutils.pipe import *
import asyncio
from httpx import AsyncClient
from arq import create_pool
from arq.connections import RedisSettings


async def download_content(ctx, url):
    session: AsyncClient = ctx['session']
    response = await session.get(url)
    print(f'{url}: {response.text:.80}...')
    return len(response.text)


async def startup(ctx):
    ctx['session'] = AsyncClient()


async def shutdown(ctx):
    await ctx['session'].aclose()


async def main():
    redis = await create_pool(RedisSettings())
    for url in ('https://facebook.com', 'https://microsoft.com', 'https://github.com'):
        print(url)
        await redis.enqueue_job('download_content', url)


# WorkerSettings defines the settings to use when creating the work,
# it's used by the arq cli.
# For a list of available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions = [download_content]
    on_startup = startup
    on_shutdown = shutdown


from rq.decorators import job


if __name__ == '__main__':
    asyncio.run(main())
