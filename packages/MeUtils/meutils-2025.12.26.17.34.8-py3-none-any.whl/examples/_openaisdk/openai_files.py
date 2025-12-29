#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_files
# @Time         : 2023/12/29 14:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *


from openai import OpenAI, AsyncOpenAI

from meutils.llm.clients import zhipuai_client

# base_url = os.getenv('OPENAI_BASE_URL')
# base_url = "https://api-dev.chatfire.cn/v1"

# base_url = "http://0.0.0.0:9000/v1"
# base_url = "http://154.3.0.117:39010/v1"
# base_url = "http://jupyter.skyman.cloud:37777/v0"
# base_url = "http://111.173.117.175:37777/files-extraction/v1"

openai = OpenAI(
    base_url=os.getenv("MOONSHOT_BASE_URL"),
    # base_url="https://chat.qwen.ai/api/v1",
    api_key="sk-XoVvLPHxztikGmcKpBWEjzoxhauBI1YQeApLNnxUQxEHZqFG"
)

# openai = OpenAI(
#     api_key=os.getenv("MOONSHOT_API_KEY"),
#     base_url=os.getenv("MOONSHOT_BASE_URL")
# )
# 上传文件
# _ = files.create(file=open('bpo.py', 'rb'), purpose="assistants", extra_body={'a': 1})  # extra_body在fomdata
# file_object = openai.files.create(
#     file=Path("招标文件备案表（第二次）.pdf"),
#     purpose="file-extract"
# )

# file_object = openai.files.create(
#     file=Path("招标文件备案表（第二次）.pdf"),
#     purpose="file-extract"
# )

file_object = zhipuai_client.files.create(
    file=Path("招标文件备案表（第二次）.pdf"),
    purpose="file-extract"
)
# print(file_object)
# # 查文件
# print(openai.files.retrieve(file_id=file_object.id))
#
# # 参照kimi
# file_id = "3MvAKgEoBrBdPgWsQSdTB8.pdf"
# file_id = file_object.id
# file_content = files.content(file_id=file_id).text
# print(file_content)
# print(type(file_content))

# print(files.retrieve(file_id))

# 二进制
# openai.files.content(file_id).stream_to_file('xx.pdf')


# file_list = files.list()
#
# for file in file_list.data:
#     print(file)
#     print(files.delete(file_id=file.id))  # 删除文件


arun(zhipuai_client.files.content(file_id=file_object.id).text)