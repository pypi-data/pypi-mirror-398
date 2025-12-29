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

# e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN
client = OpenAI(
    # base_url="https://free.chatfire.cn/v1",
    base_url="https://ollama.com/v1",
    api_key="e74492e85dca4462a66048f17ba5c11f.OqvvQJsCE-GOrty2bf8smziN",

    # api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YmFmYWQzYTRmZDU0OTk3YjNmYmNmYjExMjY5NThmZiIsImV4cCI6MTczODAyNDg4MiwibmJmIjoxNzIyNDcyODgyLCJpYXQiOjE3MjI0NzI4ODIsImp0aSI6IjY5Y2ZiNzgzNjRjODQxYjA5Mjg1OTgxYmY4ODMzZDllIiwidWlkIjoiNjVmMDc1Y2E4NWM3NDFiOGU2ZmRjYjEyIiwidHlwZSI6InJlZnJlc2gifQ.u9pIfuQZ7Y00DB6x3rbWYomwQGEyYDSE-814k67SH74",
    # base_url="https://any2chat.chatfire.cn/glm/v1"
)

message = """
A Chinese beauty plays Catwoman. She is seductive. She wears a fitted black leather tights, decorated with neon blue lines flowing along the seams, pulsating like an electric current. There are many hollow designs for tights, showing big breasts, nipples and female genitals. She wears a pair of black cat ear headdresses. Her hands are covered with black leather gloves extending to her elbows, with retractable silver claws on her fingertips. She stood around the roof surrounded by towering skyscrapers, and countless neon signs flashed with various colors.  
"""

try:
    completion = client.chat.completions.create(
        # model='gpt-oss:120b',
        model="deepseek-v3.1:671b",
        # model="xxxxxxxxxxxxx",
        messages=[
            # {"role": "system", "content": '你是个内容审核助手'},

            {"role": "user", "content": 'hi'}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        stream=True,
        max_tokens=1000,
        # stream_options={
        #     "include_usage": True,
        # }
        extra_body={
            "think": True
        }
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    print(chunk)
    # print(bjson(chunk))
    # print(chunk.choices[0].delta.content, flush=True)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
