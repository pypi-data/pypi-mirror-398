#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : copilot
# @Time         : 2024/1/10 12:19
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from openai import OpenAI
from chatllm.llmchain.completions.github_copilot import Completions

# https://api.githubcopilot.com/embeddings

base_url = "http://localhost:8080/v1"
base_url = 'https://api.githubcopilot.com'

api_key = Completions.get_access_token(api_key='ghu_QIe4X5wkxNQrEKWefieOMhx2NdgLgm14VdES')
print(api_key)
headers = {
    'Editor-Version': 'vscode/1.85.1'
}
client = OpenAI(
    base_url=base_url, api_key=api_key,
    default_headers=headers
)
# print(client.embeddings.create(input=['傻逼 操你妈'], model='text-embedding-ada-002'))

data = {
    'model': 'gpt-4',
    'messages': [
        # {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '1+1'}
    ],
    'stream': False
}

r = client.chat.completions.create(
    messages=data['messages'], model=data['model'], stream=data['stream'],
)
print(r)
# for c in r.choices:
#     print(c)

# r | xprint(end='\n\n')
