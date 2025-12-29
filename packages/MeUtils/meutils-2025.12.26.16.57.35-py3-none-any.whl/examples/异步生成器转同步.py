#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 异步生成器转同步
# @Time         : 2023/8/25 18:29
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import asyncio


# 异步生成器示例
async def async_generator():
    for i in range(10):
        await asyncio.sleep(1)
        yield i


# 将异步生成器转换成同步生成器
# def sync_generator():
#     loop = asyncio.get_event_loop()
#     async_gen = async_generator()
#
#     while True:
#         try:
#             item = loop.run_until_complete(async_gen.__anext__())
#             yield item
#         except StopAsyncIteration:
#             break

def asyn2sync_generator(generator):
    if inspect.isasyncgen(generator):
        while True:
            try:
                yield asyncio.run(generator.__anext__())
            except StopAsyncIteration:
                break
    else:
        yield from generator


if __name__ == '__main__':

    # 使用同步生成器
    for item in asyn2sync_generator(range(10)):
        print(item)
