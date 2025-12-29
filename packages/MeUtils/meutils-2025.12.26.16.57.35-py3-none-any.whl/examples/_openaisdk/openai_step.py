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
    # api_key=os.getenv("STEP_API_KEY"),
    # base_url="https://api.stepfun.com/v1",
    base_url = "https://new.xjai.cc/v1",
    api_key="sk-EmIYmk0Jiw4FWkHQ6SNnoPJpTqyCcu8P5e5nXolmS6eRKvNp"
)

try:
    completion = client.chat.completions.create(
        # model="step-1-8k",
        model="o1-mini",
        messages=[
            {"role": "user", "content": "1+1"}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        stream=False,
        max_tokens=1
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    print(chunk.choices[0].delta.content)

