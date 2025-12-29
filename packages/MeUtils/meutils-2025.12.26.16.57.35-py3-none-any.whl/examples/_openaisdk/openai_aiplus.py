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
    base_url="https://api.aiplus.ai/v1",
    api_key="sk-RiTYytBkTFqnfNnDE7B6A7DaC7Dc4cBeAb8d0b021e855c34",

)
print(client.models.list())


try:
    completion = client.chat.completions.create(
        model="claude-3-5-sonnet-1022",
        # model="xxxxxxxxxxxxx",
        messages=[
            {"role": "user", "content": "你是谁"}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        stream=True,
        max_tokens=6000
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    print(chunk.choices[0].delta.content)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
