#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_moon
# @Time         : 2024/6/14 17:27
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://api.moonshot.cn/v1/users/me/balance get查余额
# https://api-docs.deepseek.com/zh-cn/guides/function_calling


from meutils.pipe import *
from openai import OpenAI

# base_url = os.getenv('DEEPSEEK_BASE_URL')
# api_key = os.getenv('DEEPSEEK_API_KEY') #
client = OpenAI(
    # api_key=api_key,
    # base_url=base_url,
)
completion = client.chat.completions.create(
    model="deepseek-v3-128k",
    messages=[
        {"role": "user", "content": "`你好`"*80000},
    ],
    # stream=True,
)

print(completion)
#
# for chunk in completion:
#     print(chunk.choices[0].delta.content, end='')
#
#


# from openai import OpenAI
#
# def send_messages(messages):
#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=messages,
#         tools=tools
#     )
#     return response.choices[0].message
#
#
#
# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_weather",
#             "description": "Get weather of an location, the user shoud supply a location first",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "location": {
#                         "type": "string",
#                         "description": "The city and state, e.g. San Francisco, CA",
#                     }
#                 },
#                 "required": ["location"]
#             },
#         }
#     },
# ]
#
# messages = [{"role": "user", "content": "How's the weather in Hangzhou?"}]
# message = send_messages(messages)
# print(f"User>\t {messages[0]['content']}")
#
# tool = message.tool_calls[0]
# messages.append(message)
#
# messages.append({"role": "tool", "tool_call_id": tool.id, "content": "24℃"})
# message = send_messages(messages)
# print(f"Model>\t {message.content}")

