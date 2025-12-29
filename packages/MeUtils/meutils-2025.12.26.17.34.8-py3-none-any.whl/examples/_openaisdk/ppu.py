#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ppu
# @Time         : 2024/1/9 17:37
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

from openai import OpenAI

base_url = "https://api.chatfire.cn/v1"

client = OpenAI(base_url=base_url, api_key="sk-1UNhOrvuJ4PeBBpsB202577c14114f7fA234F32d3e8dF767")

q = "hi"
data = {
    'model': 'ppu-1',
    'messages': [
        {'role': 'user', 'content': q}
    ],
    'stream': False
}

print(client.chat.completions.create(**data))
