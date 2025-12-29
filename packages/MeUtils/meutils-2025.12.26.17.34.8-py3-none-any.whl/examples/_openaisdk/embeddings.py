#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : embeddings
# @Time         : 2024/1/4 11:05
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

client = OpenAI(
    # base_url='https://apis.chatfire.cn/v1',
)
model = "text-embedding-ada-002"
# model = "text-embedding-3-small"
model = "text-embedding-3-large"

# model = "jina-embedding"
# model = "text-embedding-3-small"
# model='bge-large-zh-v1.5-q4'
# model='acge_text_embedding'
# model = 'doubao-embedding'
model = 'BAAI/bge-m3'
_ = client.embeddings.create(input='1', model=model)
print(_)

#
# curl http://111.173.117.175:11434/api/embeddings -d '{
#   "model": "bge-large-zh-v1.5-q4",
#   "prompt": "Here is an article about llamas..."
# }'
