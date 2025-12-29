#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo: assistants
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError
from meutils.schemas.oneapi.models import BAICHUAN

client = OpenAI(
    api_key=os.getenv("BAICHUAN_API_KEY"),
    base_url=os.getenv("BAICHUAN_BASE_URL")
)

# tool:search

for model in BAICHUAN:
    model="baichuan3-turbo-128k"
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                # {"role": "system", "content": "你是个画图工具"},
                # {"role": "user", "content": "你是谁"},

                {"role": "user", "content": "今天南京天气如何"}

            ],
            # top_p=0.7,
            stream=True,

            tools=[
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_mode": "performance_first"
                    }
                }
            ]

        )
    except APIStatusError as e:
        print(e.status_code)

        print(e.response)
        print(e.message)
        print(e.code)

    for chunk in completion:
        print(chunk)
        # print(chunk.choices[0].delta.content.replace('百川', '火哥'))
        print(chunk.choices[0].delta.content.replace('百川', '百度'))

    break

