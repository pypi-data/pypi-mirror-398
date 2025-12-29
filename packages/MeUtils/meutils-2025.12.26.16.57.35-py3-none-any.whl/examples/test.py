#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : test
# @Time         : 2024/6/11 11:58
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import time
import typing

from meutils.pipe import *
from starlette.background import BackgroundTask as _BackgroundTask, BackgroundTasks as _BackgroundTasks
from asgiref.sync import async_to_sync
from meutils.decorators import background_task


class BackgroundTask(_BackgroundTask):

    @background_task
    def call(self):
        async_to_sync(super().__call__)()


class BackgroundTasks(_BackgroundTasks):

    @background_task
    def call(self):
        async_to_sync(super().__call__)()


async def f(x):
    logger.debug(x)

    for i in range(100):
        logger.debug(i)
        await asyncio.sleep(1)


BackgroundTask(f, x='xxxxxxxxxx').call()

# def f(x):
#     logger.debug(x)
#
#     for i in range(100):
#         logger.debug(i)
#         time.sleep(1)


# BackgroundTask(f, x='xxxxxxxxxx').call()


# bt = BackgroundTasks()
# bt.add_task(f, x='xxxxxxxxxx')
# bt.call()
print("#########")
# while 1:
#     pass
