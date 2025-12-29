#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : baichuan
# @Time         : 2024/1/18 09:33
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

base_url = "http://api.chatllm.vip/v1"

with timer("client"):
    client = OpenAI(
        base_url="https://api.githubcopilot.com",
        api_key="xxx"
    )

data = {
    'model': 'gpt-3.5-turbo',
    # 'model': 'gemini-pro',
    # 'model': 'Baichuan2-Turbo',
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '你是谁'}
    ],
    'stream': False
}

with timer("xxxxxxxxx"):
    r = client.chat.completions.create(
        messages=data['messages'], model=data['model'], stream=data['stream'],
    )

    print(r)
