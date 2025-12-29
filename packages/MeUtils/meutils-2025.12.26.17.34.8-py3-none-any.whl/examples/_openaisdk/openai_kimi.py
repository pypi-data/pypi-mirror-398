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

api_key = """
eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTczOTY4NDk3NywiaWF0IjoxNzMxOTA4OTc3LCJqdGkiOiJjc3RkYXNmZDBwODBpaGtkNTY5MCIsInR5cCI6InJlZnJlc2giLCJhcHBfaWQiOiJraW1pIiwic3ViIjoiY2tpMDk0YjNhZXNsZ2xqNmZvMzAiLCJzcGFjZV9pZCI6ImNraTA5NGIzYWVzbGdsajZmbzJnIiwiYWJzdHJhY3RfdXNlcl9pZCI6ImNraTA5NGIzYWVzbGdsajZmbzMwIn0.CYXj16LIV6yLG9TJCYm9oZ8GGW6jhA6kRhBp4k3elDznwl8XM4U9xxm4K58XIAkuf2f0Rom6xoTKByyqOAZgPQ
"""
client = OpenAI(
    # base_url="https://free.chatfire.cn/v1",
    base_url="https://all.chatfire.cn/kimi/v1",
    api_key=api_key.strip()

)

try:
    _ = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "你是谁"}
        ],
        model="azure/gpt-4o-mini",
    )
    print(_)
except Exception as e:
    print(e)
