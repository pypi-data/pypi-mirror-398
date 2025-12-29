#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_x
# @Time         : 2025/1/18 15:08
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
# 'X-API-KEY': "hl_sk_dae400bf07e363d414525f38ad73803701c499f1891ef583"


from openai import OpenAI

client = OpenAI(
    base_url="https://openai-dev.chatfire.cn/r/v1",
    default_query={"base_url": "https://ai.gitee.com/v1"},
    api_key="AHKZ65ARNFH8QGMUUVCPECDTZVOLRPUXIKPGAC1Y",
)

r = client.chat.completions.create(
    # model="DeepSeek-R1-Distill-Qwen-1.5B",
    model="deepseek-r1-Distill-Qwen-1.5B",

    stream=True,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(r)



from openai import OpenAI

client = OpenAI(
    base_url="https://api.chatfire.cn/v1",
    api_key="sk-kGCanp849XTgj6IYKNiGuicMonCnS0RIPkzZV6jccUBURF4p",
)

r = client.chat.completions.create(
    model="gpt-4o",

    stream=False,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(r)


client.embeddings.create()