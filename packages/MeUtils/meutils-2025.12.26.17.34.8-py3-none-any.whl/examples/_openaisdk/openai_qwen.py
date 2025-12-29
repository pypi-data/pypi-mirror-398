#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_qwen
# @Time         : 2024/12/31 18:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://help.aliyun.com/zh/model-studio/developer-reference/qwenvl-video-understanding

from meutils.pipe import *

import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    # model="qwen3-1.7b",
    # model="qwen3-235b-a22b",
    # model="qwen3-vl-plus",
    model="qwen-vl-max",
    stream=True,
    # extra_body={"enable_thinking": True, "thinking_budget": 1024},
    # stream_options={"include_usage": True},
    # reasoning_effort="low",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://lmdbk.com/5.mp4"
                }
            },
            {
                "type": "text",
                "text": "总结"
            }
        ]
    }]
)
# glm-zero-preview
# completion = client.chat.completions.create(
#     model="qwen-vl-max-latest",
#     messages=[{
#         "role": "user",
#         "content": [
#             {
#                 "type": "video",
#                 "video": [
#                     "https://img.alicdn.com/imgextra/i3/O1CN01K3SgGo1eqmlUgeE9b_!!6000000003923-0-tps-3840-2160.jpg",
#                     "https://img.alicdn.com/imgextra/i4/O1CN01BjZvwg1Y23CF5qIRB_!!6000000003000-0-tps-3840-2160.jpg",
#                     "https://img.alicdn.com/imgextra/i4/O1CN01Ib0clU27vTgBdbVLQ_!!6000000007859-0-tps-3840-2160.jpg",
#                     "https://img.alicdn.com/imgextra/i1/O1CN01aygPLW1s3EXCdSN4X_!!6000000005710-0-tps-3840-2160.jpg"]
#             },
#             {
#                 "type": "text",
#                 "text": "描述这个视频的具体过程"
#             }]}]
# )

print(completion)

# print(completion.model_dump_json())

for i in completion:
    print(i)
