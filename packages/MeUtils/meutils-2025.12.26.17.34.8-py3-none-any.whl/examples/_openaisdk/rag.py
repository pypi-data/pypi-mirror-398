#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : rag
# @Time         : 2024/1/4 18:48
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
import httpx
import base64
from openai import OpenAI

# base_url = "https://oneapi.chatllm.vip/v1"  # 有问题 映射的问题
base_url = "https://api.chatllm.vip/v1/"  # 有问题 映射的问题

# base_url = "http://0.0.0.0:39999/v1"
# base_url = "http://111.173.117.175:39009/v1"  # 没问题
api_key = "sk-eEFIr6SEuegUOh1S0c8910A652A9428fAd4aD452C97631Ac"

client = OpenAI(
    # http_client=httpx.Client(
    #     follow_redirects=True
    # ),
    base_url=base_url, api_key=api_key)

# 上传文件
file_obj = client.files.create(file=open("rag.py", 'rb'), purpose="assistants")
logger.debug(file_obj)
file_id = file_obj.id

# file_id = "file-ec9fdc5146479136ec1197b9a8b51676"  # file_obj.id
#
# # 问答
# q = "录取办法有哪些"
# data = {
#     'model': 'gpt-3.5-turbo-16k',  # todo: 超长提示
#     'messages': [
#         {'role': 'user', 'content': q}
#     ],
#     'stream': True
# }
#
# r = client.chat.completions.create(
#     messages=data['messages'], model=data['model'], stream=data['stream'],
#     extra_body={"file_id": file_id}
# )
#
# print(r)
# for i in r:
#     print(i)
