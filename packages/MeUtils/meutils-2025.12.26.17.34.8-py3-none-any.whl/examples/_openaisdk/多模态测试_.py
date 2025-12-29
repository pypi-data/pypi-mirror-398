#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 4v
# @Time         : 2023/11/20 10:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


import base64
from pathlib import Path

from openai import OpenAI, AsyncOpenAI

base_url = 'https://apis.chatfire.cn/v1'
api_key = 'sk-...'
openai = OpenAI(api_key=api_key, base_url=base_url)
# openai = OpenAI()

image_path = 'demo.png'  # 替换你的图片
base64_image = base64.b64encode(Path(image_path).read_bytes()).decode('utf-8')

#
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": f"解释图片"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
            # {"type": "image_url", "image_url": {"url": image_url}},

        ],

    }
]

response = openai.chat.completions.create(
    # model='gpt-4-vision-preview',
    # model="gemini-pro-vision",

    # model="claude-3-haiku-20240307",
    # model="claude-3-sonnet-20240229",
    # model="claude-3-opus-20240229",

    # model='glm-4v',
    model='step-1v',
    # model='yi-vl-plus',

    messages=messages,
    max_tokens=100,
    temperature=0,
)

print(response.dict())
