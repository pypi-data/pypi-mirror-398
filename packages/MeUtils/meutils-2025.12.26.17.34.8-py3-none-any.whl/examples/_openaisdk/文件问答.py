#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 文件问答
# @Time         : 2024/11/6 09:54
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *

import os
from openai import OpenAI, AsyncOpenAI

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.chatfire.cn/v1")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text","text": "一句话总结"
             },
            # {"type": "image_url", "image_url": {"url": "<base64/url>"}},

            {"type": "file_url", "file_url": "https://mj101-1317487292.cos.ap-shanghai.myqcloud.com/ai/test.pdf"},

        ],

    }
]
response = openai.chat.completions.create(
    model='glm-4-all',
    messages=messages,
)
