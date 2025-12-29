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
from openai import AsyncOpenAI as _OpenAI
from openai import AsyncClient


OpenAI = lru_cache(_OpenAI)

print(type(_OpenAI))



with timer():
    client = OpenAI(
        api_key="e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN",
        base_url="https://ppu.chatfire.cn/"
    )

with timer():
    client = OpenAI(
        api_key="e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN",
        base_url="https://ppu.chatfire.cn/"
    )

with timer():
    client = OpenAI(
        api_key="e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN1",
        base_url="https://ppu.chatfire.cn/"
    )



arun(client.chat.completions.create(
    model="glm-4-flash",
    messages=[
        {"role": "user", "content": "hi"}
    ],))