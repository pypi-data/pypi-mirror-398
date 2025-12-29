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

os.getenv("ZHIPUAI_API_KEY")

client = OpenAI(
    api_key=os.getenv("DEEPINFRA_API_KEY"),
    base_url=os.getenv("DEEPINFRA_BASE_URL")
)



try:
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        # model="xxxxxxxxxxxxx",
        messages=[
            {"role": "user", "content": "你是deepseek什么版本"*10000}
        ],
        # # top_p=0.7,
        # top_p=None,
        # temperature=None,
        stream=False,
        max_tokens=100
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

