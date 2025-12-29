#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_moon
# @Time         : 2024/6/14 17:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://api.moonshot.cn/v1/users/me/balance get查余额
import os

from meutils.pipe import *
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
    # base_url="http://ppu.chatfire.cc/v1"
)

# print(client.models.list())

# completion = client.chat.completions.create(
#     model="moonshot-v1-8k",
#     messages=[
#         {"role": "user", "content": "1+1"},
#     ],
#     # temperature=0.3, extra_body={"refs": ["cn0bmk198onv4v01aafg"]}
# )
#
#
# api_key="eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTcyNjQ3NDc2NCwiaWF0IjoxNzE4Njk4NzY0LCJqdGkiOiJjcG9rNjMzM2Flc3Vob2FmMGVmMCIsInR5cCI6InJlZnJlc2giLCJzdWIiOiJja2kwOTRiM2Flc2xnbGo2Zm8zMCIsInNwYWNlX2lkIjoiY2tpMDk0YjNhZXNsZ2xqNmZvMmciLCJhYnN0cmFjdF91c2VyX2lkIjoiY2tpMDk0YjNhZXNsZ2xqNmZvMzAifQ.MMv3lWzE8SldliJjAobFMgu7r8qpwZX5HlHjDew4xAtU1Ftw8VGOXxncT9hwALshHlWnEXlF7Uv_oeSq0nroGw"
# client = OpenAI(
#     api_key=api_key,
#     base_url="http://154.3.0.117:39001/v1",
# )
#
# completion = client.chat.completions.create(
#     model="moonshot-v1-8k",
#     messages=[
#         {"role": "user", "content": "1+1"},
#     ],
#     # temperature=0.3, extra_body={"refs": ["cn0bmk198onv4v01aafg"]}
# )
#
#

if __name__ == '__main__':

    from meutils.pipe import timer

    with timer():
        completion = client.chat.completions.create(
            model="kimi-k2-0905-preview",
            messages=[
                {"role": "user", "content": "你好"*100000 + "\n\n上文一共有多少个字"},
            ],
            # temperature=0.3, extra_body={"refs": ["cn0bmk198onv4v01aafg"]}
        )