#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : backgroundtasks
# @Time         : 2024/6/25 08:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://apifox.com/apiskills/fastapi-backgroundtasks-answer/

# 异步任务

from meutils.pipe import *

import asyncio


# 协程
async def write_notification(email, message):
    await notify(email, message)  # 使用 asyncio.sleep 代替 time.sleep


def background_tasks(email, message):
    loop = asyncio.get_event_loop()
    loop.create_task(write_notification(email, message))
