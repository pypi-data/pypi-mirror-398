#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_search
# @Time         : 2024/11/14 09:01
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 



from meutils.pipe import *
from openai import OpenAI

base_url = "https://api.yiweixingchen.com/v1"
api_key = "sk-s64oF9rOJCT42V0NmVUH5WzvDKTYqZU3qBFZLyrbl2vJGi0m"
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)


for i in tqdm(range(1000)):
    try:
        completion = client.chat.completions.create(
            model="metaso-free-api",
            # model="openai/gpt-4o-mini",
            # model="openai/gpt-4o",
            # model="anthropic/claude-3.5-sonnet",

            messages=[
                {"role": "user", "content": "1+1"},
            ],
            # max_tokens=10
        )
        print(completion)

    except Exception as e:
        print(e)


