#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_cache
# @Time         : 2024/2/28 13:23
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import time

from meutils.pipe import *
from openai import OpenAI, AsyncOpenAI

client = OpenAI()


@timer()
@lru_cache
def create(client, arg=None):

    data = {
        'model': 'gpt-3.5-turbo',

        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'hi'}
        ],
        'stream': True,

    }

    return client.chat.completions.create(**data)


if __name__ == '__main__':
    create(client)
