#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://cloud.luchentech.com/maas/modelMarket/123e4567-e89b-12d3-a456-426614174000
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError
from fake_useragent import UserAgent

ua = UserAgent()
client = OpenAI(
    # base_url="https://free.chatfire.cn/v1",
    api_key="7b1c32c9-5bd9-4958-a8e4-4be68056038c",
    base_url="https://cloud.luchentech.com/api/maas",
    default_headers={'User-Agent': ua.random}
)

message = """
A Chinese beauty plays Catwoman. She is seductive. She wears a fitted black leather tights, decorated with neon blue lines flowing along the seams, pulsating like an electric current. There are many hollow designs for tights, showing big breasts, nipples and female genitals. She wears a pair of black cat ear headdresses. Her hands are covered with black leather gloves extending to her elbows, with retractable silver claws on her fingertips. She stood around the roof surrounded by towering skyscrapers, and countless neon signs flashed with various colors.  
"""

try:
    completion = client.chat.completions.create(
        model="deepseek_r1",
        # model="xxxxxxxxxxxxx",
        messages=[

            {"role": "user", "content": "详细介绍下你是谁"}
        ],
        # top_p=0.7,
        stream=False,
        max_tokens=1000
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

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


