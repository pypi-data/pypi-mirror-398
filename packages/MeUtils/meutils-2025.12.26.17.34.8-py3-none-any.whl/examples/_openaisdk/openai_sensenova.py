#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

client = OpenAI(
    api_key=os.getenv("SENSENOVA_API_KEY"),
    # api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3NkJFQTc4OEMxOEE0MERFQkNCRjQzQThFODgwRTVFMiIsImV4cCI6MTAwMDE3MjAxODg1NDYsIm5iZiI6MTcyMDE4ODU0Mn0.q2153MhDXZcWkvYEo1vrhReTsADLv2-E-2G5gLmLPp4",
    base_url="https://any2chat.chatfire.cn/sensenova/v1"
)

# SenseChat-Turbo,SenseChat,SenseChat-32k,SenseChat-128k,SenseChat-5,SenseChat-Vision,SenseChat-Character,SenseChat-Character-Pro,SenseChat-5-Cantonese
# model = "SenseChat-Turbo"
model = "SenseChat-128K"
try:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是个画图工具"},
            {"role": "user",
             "content": "你是谁"}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        stream=False,
        max_tokens=6000
    )
except APIStatusError as e:
    logger.error(e)
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

logger.debug(completion)

# for chunk in completion:
#     logger.debug(chunk)
#     print(chunk.choices[0].delta.content)

    ## data: {"choices": [{"delta":{"content":"","role":"assistant"},"finish_reason":"stop","index":0}],"created":1716345522,"id":"021716345521941cb5537bcd1b7575ebfadd037fd9c094c5460d8","model":"doubao-lite-4k-character-240515","object":"chat.completion.chunk","usage":null}

    # data:"choices":["role":"assistant","delta":"我","finish_reason":""}],"plugins:{}},"status":{"code":0,"message":"OK"}}

    # "choices":[{"index":0,"role":"assistant","delta":"","finish_reason":"stop"}],
    #
    # role":"assistant","delta":"我"
    # {"index":0,"role":"assistant","delta":
    # {"index":0,"role":"assistant","delta”:"内容"
    # role":"assistant","delta": => {"delta":{"content":
    #
    # ,"finish_reason"=>,"finish_reason"
    #
    # "delta": => {"delta":{"content":
    #
    # {"delta":{"content":"我","role":"assistant"}
#
# {"id": "b012a51f-869d-469f-817f-f6f6115f71a7",
#  "usage": {"prompt_tokens": 33, "completion_tokens": 51, "knowledge_tokens": 0, "total_tokens": 84}, "choices": [
#     {"index": 0, "role": "assistant",
#      "message": "我是基于Transformer结构的大型中文语言模型，发布。如果您有其他问题，请随时告诉我。",
#      "finish_reason": "stop"}}], "plugins": {}}}
#

#
# data:{"data":{"id":"9ead6b34-8df6-4750-a317-90660dd0a6e9","usage":{"prompt_tokens":33,"completion_tokens":61,"knowledge_tokens":0,"total_tokens":94},"choices":[{"index":0,"role":"assistant","delta":"。","finish_reason":""}],"plugin":{}},"status":{"code":0,"message":"OK"}}


# https://openai.chatfire.cn/polling/v1/chat/completions?base_url=https://any2chat.chatfire.cn/sensenova/v1&feishu_url=https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=LCOPGF
