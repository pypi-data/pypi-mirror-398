#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : deeplx
# @Time         : 2024/4/23 18:40
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

messages = [{'role': 'user', 'content': '如果text为空，默认翻译这一句'}]
deeplx_payload = {
    "text": "文本不为空，就翻译这一句",
    "source_lang": "auto",
    "target_lang": 'EN',
}

model = 'deeplx'  # deeplx-zh deeplx-en 根据后缀会覆盖参数target_lang

reps = OpenAI().chat.completions.create(
    model=model,
    messages=messages,
    extra_body={"payload": deeplx_payload},
    stream=False
)

# print(reps)
print(reps.model_dump_json())
