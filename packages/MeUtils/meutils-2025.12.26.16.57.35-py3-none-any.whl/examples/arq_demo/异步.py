#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 异步
# @Time         : 2025/8/28 15:29
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *


async def f():
    1/0



async def main():
    future_task = asyncio.create_task(f())  # 异步执行
    # future_task.exception()

    try:
        await future_task
    except Exception as e:
        raise e
        # print(e)
        # print(future_task.exception())


if __name__ == '__main__':
    asyncio.run(main())
