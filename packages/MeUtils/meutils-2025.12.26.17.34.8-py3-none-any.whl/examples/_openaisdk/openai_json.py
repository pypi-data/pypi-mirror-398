#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_json
# @Time         : 2024/4/11 13:10
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *

from openai import OpenAI

# base_url = "https://api.chatllm.vip/v1"
# base_url = "http://0.0.0.0:8000/v1"
# base_url="https://api.gptgod.online/v1"


from openai import OpenAI


client = OpenAI(
    # api_key=os.getenv('OPENAI_API_KEY_OPENAI'),
)

with timer('聊天模型'):
    data = {
        # 'model': 'gpt-3.5-turbo',
        # 'model': 'gpt-3.5-turbo-0125',
        # "model": "rag-gpt-3.5-turbo",
        # "model": "rag-gpt-4",
        # 'model': 'gpt-4-0125-preview',
        # 'model': 'gpt-4-turbo-preview',
        # 'model': 'gemini-pro',
        'model': 'gpt-4o',
        # 'model': 'gpt-4o-mini',
        # 'model': "gpt-4o-2024-08-06",

        # 'model': 'backup-gpt',
        # 'model': 'test',
        # 'model': 'per',
        # 'model': 'glm-4-all',
        # 'model': '65f41c8a9c0ebbcbe28bb9c1',

        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant designed to output JSON.'},

            {'role': 'user', 'content': "请将1改为2 {'a': 1}"}

        ],
        'stream': False,

        'response_format': {"type": "json_object"}

    }

    try:
        # r = client.chat.completions.create(**data, extra_body={"file_ids": ["cn2a0s83r07am0knkeag"]})
        r = client.chat.completions.create(**data)

        print(isinstance(r, Iterator))

        print(type(r))

        for i in r:
            print(i)

    except Exception as e:
        print(e)

# 向量模型
# model = 'text-embedding-3-small'
# model = 'text-embedding-3-large'
# r = client.embeddings.create(input='hi', model=model)
# print(r)


