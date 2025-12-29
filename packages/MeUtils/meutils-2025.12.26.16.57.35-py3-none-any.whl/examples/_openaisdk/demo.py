#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : gpt4all
# @Time         : 2024/1/2 13:28
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI, _base_client

# _base_client.BaseClient.default_headers = {}

base_url = "https://api.chatllm.vip/v1"  # 更快
base_url = "https://api.chatfire.cn/v1"
base_url = "https://chat.aifree.best/api/openai/v1"


# base_url="https://api.gptgod.online/v1"


class MeOpenAI(OpenAI):
    # @default_headers.default_headers.setter
    # def default_headers(self, value):
    #     self._default_headers = value
    @property
    def default_headers(self):
        return {}


client = MeOpenAI(
    base_url=base_url,
)

with timer('聊天模型'):
    data = {
        'model': 'gpt-3.5-turbo',
        # 'model': 'gpt-3.5-turbo-0125',
        # "model": "rag-gpt-3.5-turbo",
        # "model": "rag-gpt-4",
        # 'model': 'gpt-4-0125-preview',
        # 'model': 'gpt-4-turbo-preview',
        # 'model': 'gemini-pro',
        # 'model': 'gpt-4',
        # 'model': 'backup-gpt',
        # 'model': 'test',
        # 'model': 'per',

        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'hi'}
        ],
        'stream': True,

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
