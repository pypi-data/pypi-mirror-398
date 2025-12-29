#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : minimax
# @Time         : 2024/5/23 14:01
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
from asgiref.sync import async_to_sync

from meutils.pipe import *

from openai import OpenAI, AsyncOpenAI

api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJjaGF0ZmlyZSIsIlVzZXJOYW1lIjoiY2hhdGZpcmUiLCJBY2NvdW50IjoiIiwiU3ViamVjdElEIjoiMTc2ODUzODA1NjAwMTg2NDQ2NCIsIlBob25lIjoiMTg1NTAyODgyMzMiLCJHcm91cElEIjoiMTc2ODUzODA1NTk5MzQ3NTg1NiIsIlBhZ2VOYW1lIjoiIiwiTWFpbCI6IiIsIkNyZWF0ZVRpbWUiOiIyMDI0LTA1LTIzIDEzOjMxOjU0IiwiaXNzIjoibWluaW1heCJ9.Gd4gBPZiI9VxAN-iRsNM4J4c0vNENtaV2TE4_OYPDSB5oYslZ_wx49b4lcm-rsfzJY65GWH-ATaqHQj-a28q4IfntbWFbVwvpd16n8hTnhoY2adkSKNSShtCuSdxMQgpCWI7UXVc-dwJ2LAwAwpe7t24Y_uuDy41KME07cm4_lFELgOQo7TcNI4sPeXKKmwrdv2uRkCNG1jzeI3sZF53ck-bdjTQl6k3qwE6XIbFOFpEgWWQXUK6-jP5MLIHpdJZ6_uax_OCQxx52apm0YRJqULTpiTqEB2dojINbLfexQpMtc8MPKjmx3d3Md_LANvYuQv5lPejuG1tDAuajzZ2Ww"

data = {
    "model": "abab6.5-chat",
    "messages": [
        {
            "role": "user",
            "content": "你是谁”"
        }
    ],
    "stream": True,
}

# _ = OpenAI(
#     api_key=api_key,
#     base_url='https://any2chat.chatfire.cn/minimax/v1'
# ).chat.completions.create(**data)
# for i in _:
#     print(i)

_ = AsyncOpenAI(
    api_key=api_key,
    base_url='https://any2chat.chatfire.cn/minimax/v1'
).chat.completions.create(**data)


@async_to_sync()
async def gen():
    x = await _
    logger.debug(type(x))
    async for chunk in x:
        logger.debug(chunk)
    #
    #     yield chunk
    # yield "[DONE]"  # 兼容标准格式


# async def gen():
#     x = await _
#     logger.debug(type(x))
#     async for chunk in x:
#         logger.debug(chunk)
#     #
#     #     yield chunk
#     # yield "[DONE]"  # 兼容标准格式
#
#
# gen()
#
from meutils.llm.openai_utils import create_chat_completion_chunk


async def main():

    async for i in create_chat_completion_chunk(_):
        print(i)


if __name__ == '__main__':
    arun(main())
