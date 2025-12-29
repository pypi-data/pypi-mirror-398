#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : kimi_qa
# @Time         : 2024/2/8 13:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

client = OpenAI(
    api_key=api_key or os.getenv('MOONSHOT_API_KEY'),
    base_url=os.getenv('MOONSHOT_BASE_URL'),
)



file_list = client.files.list()

print(file_list.data)

# for file in file_list.data:
#     print(file)  # 查看每个文件的信息
#
#     print(client.files.delete(file_id=file.id))

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL'),
)

file_object = client.files.create(file=Path("xlnet.pdf"), purpose="file-extract")
file_content = client.files.content(file_id=file_object.id).text

messages = [
    {
        "role": "system",
        "content": "你是 ChatfireBot，由 Chatfire AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Chatfire AI 为专有名词，不可翻译成其他语言。",
    },
    {
        "role": "system",
        "content": file_content,
    },
    {"role": "user", "content": "请简单介绍文件讲了啥"},
]

completion = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=0.3,
)

print(completion.choices[0].message)
