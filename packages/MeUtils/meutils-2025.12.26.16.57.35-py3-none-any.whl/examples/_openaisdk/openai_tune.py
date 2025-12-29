#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_tune
# @Time         : 2024/9/20 20:12
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from openai import OpenAI

client = OpenAI(
    base_url="https://all.chatfire.cn/kimi/v1",
    api_key="eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc0MTQ4ODQyMiwiaWF0IjoxNzMzNzEyNDIyLCJqdGkiOiJjdGI1azloMDUyMmt2YjVnM2Z2ZyIsInR5cCI6InJlZnJlc2giLCJhcHBfaWQiOiJraW1pIiwic3ViIjoiY3RiNWs5aDA1MjJrdmI1ZzNmdWciLCJzcGFjZV9pZCI6ImN0YjVrOWgwNTIya3ZiNWczZnUwIiwiYWJzdHJhY3RfdXNlcl9pZCI6ImN0YjVrOWgwNTIya3ZiNWczZnRnIn0.93kaSswYJR3Bk9QfDKdluh1pzKNBVmISkhK3niV5UpSAM7K5-jGg_thRjMxFEbZDETksMxGL9-UOU7nJCH0GeQ"
)

completion = client.chat.completions.create(
    # model="anthropic/claude-3.5-sonnet",
    # model="openai/gpt-4o-mini",
    # model="openai/gpt-4o",
    # model="anthropic/claude-3.5-sonnet",
    # model="gpt-4o-mini",
    model="gpt-4-turbo",

    messages=[
        {"role": "user", "content": "你是谁"},
    ],
    max_tokens=10000
)

print(completion)
#
#
# a7yu5a3je@vv.beitekeji.run----9z1kdi0k----emgcbo1m76@163.com
#  maginfic