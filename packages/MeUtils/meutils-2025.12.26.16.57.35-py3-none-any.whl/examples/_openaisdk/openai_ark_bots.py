#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_ark_bots
# @Time         : 2025/4/1 16:52
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import os
from openai import OpenAI

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Openai客户端，从环境变量中读取您的API Key
client = OpenAI(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    # 从环境变量中获取您的 API Key
    api_key=os.environ.get("ARK_BOTS_API_KEY")
)

# Non-streaming:
print("----- standard request -----")
completion = client.chat.completions.create(
    model="bot-20250401164325-s7945",  # bot-20250401164325-s7945 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
    messages=[
        {"role": "user", "content": "今天有什么热点新闻？"},
    ],
)
print(completion.choices[0].message.content)
if hasattr(completion, "references"):
    print(completion.references)

# Streaming:
print("----- streaming request -----")
stream = client.chat.completions.create(
    model="bot-20250401164325-s7945",  # bot-20250401164325-s7945 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
    messages=[
        {"role": "user", "content": "今天有什么热点新闻？"},
    ],
    stream=True,
)
for chunk in stream:
    if hasattr(chunk, "references"):
        print(chunk.references)
    if not chunk.choices:
        continue
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()

print("----- standard request -----")
completion = client.chat.completions.create(
    max_tokens=10,
    model="bot-20250401164325-s7945",  # bot-20250401164325-s7945 为您当前的智能体的ID，注意此处与Chat API存在差异。差异对比详见 SDK使用指南
    messages=[
        {"role": "user", "content": "今天有什么热点新闻"},
    ],
)
print(completion.choices[0].message.content)
if hasattr(completion, "references"):
    print(completion.references)
