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
# https://web.aaai.me/api/v1/auths/api_key

client = OpenAI(
    base_url="https://web.aaai.me/api",

    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImMyNWNmZDljLTViMDUtNDk1Ni04NDgzLTg1M2I4MGY4MDg5ZiJ9.Y6S8nnnqxcz6iGLUPNIGeG8h1dq2SCYfH4FqMDpwO9M",
)

print(client.models.list())

try:
    completion = client.chat.completions.create(
        # model="glm-4-flash",
        # model="claude-3-5-sonnet-20241022",
        model="claude-3.5-sonnet",
        # model="gpt-4o",

        messages=[
            {"role": "user", "content": "讲个故事"}
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


