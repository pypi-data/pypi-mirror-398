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
    api_key="sk_-k7BdwRII1GbBEy-1plcgH8aPRfzzXV56HaCBVe2Zqk",

    base_url="https://api.ppinfra.com/v3/openai"
)

# print(client.models.list().data)
models = [m.id for m in client.models.list().data]

print(','.join(models))


try:
    completion = client.chat.completions.create(
        # model="deepseek/deepseek-r1/community",
        # model="deepseek/deepseek-r1-turbo",
        # model="deepseek/deepseek-v3-0324",
        model="deepseek/deepseek-r1-0528",
        messages=[
            {"role": "system", "content": '你是个内容审核助手'},

            {"role": "user", "content": 'hi'}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        # stream=True,
        max_tokens=10,
        # extra_body={"separate_reasoning": True}
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

print(completion)
for chunk in completion:
    # print(bjson(chunk))
    print(chunk.choices[0].delta.content, flush=True)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
# deepseek/deepseek-r1-turbo
# deepseek/deepseek-r1
# deepseek/deepseek-r1/community
#
# deepseek/deepseek-v3-turbo
# deepseek/deepseek-v3
# deepseek/deepseek-v3/community
# deepseek/deepseek-v3-0324

