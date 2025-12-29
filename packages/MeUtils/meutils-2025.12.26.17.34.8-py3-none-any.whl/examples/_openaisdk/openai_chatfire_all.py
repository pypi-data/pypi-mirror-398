#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_chatfire_all
# @Time         : 2024/7/23 19:44
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from openai.types.chat import ChatCompletionToolParam

from meutils.pipe import *
from meutils.schemas.openai_types import TOOLS

from zhipuai import ZhipuAI
from openai import OpenAI

client = OpenAI(
    # api_key=os.getenv("ZHIPU_API_KEY"),
    # base_url=os.getenv("ZHIPU_BASE_URL")
    # api_key=os.getenv("OPENAI_API_KEY"),
    # base_url=os.getenv("OPENAI_BASE_URL"),
)  # 请填写您自己的APIKey

# messages = [
#     # {
#     #     "role": "system",
#     #     "content": "牢记，你的名字叫火宝，由Chatfire AI 开发",
#     # },
#
#     {
#         "role": "user",
#         # "content": "画画，帮我画一条狗画条狗",
#         "content": [
#             {
#                 "type": "text",
#                 "text": "画画，帮我画一条狗画条狗"
#             }
#         ]
#     }
# ]

messages = [
    {
        "role": "system",
        "content": "你叫火宝，由Chatfire AI 开发"
    },
    {
        "role": "system",
        "content": "你叫火宝，由Chatfire AI 开发"
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                # "text": "帮我查询南京07/05至07/15的日平均气温。并用日平均气温数列绘出折线图显示趋势。",
                # "text": "用python写个冒泡排序并且执行结果",

                "text": "画条可爱的狗",

            }
        ]
    },
    # {
    #     "role": "assistant",
    #     "content": "arguments='{city\":\"慕尼黑\", \"from_day\":\"07/05\",\" to_day\":\"07/15\"}', name='get_average_temperature_data_by_date'"
    # },
    # {
    #     "role": "tool",
    #     "content": "[21.7, 16.6, 29.2, 25.0, 22.2, 25.9, 18.8, 22.2, 26.2, 26.1, 19.6]"
    # }
]
tools: List[ChatCompletionToolParam] = [

    {
        "type": "web_browser",  # 联网搜索
        "function": None
    },

    # {'id': '', 'type': 'web_browser', 'function': {'name': 'web_browser', 'parameters': 'web_browser'}}
    {
        "type": "code_interpreter",  # 联网搜索
        # "function": {"name": '空'}
    },
    {
        "type": "drawing_tool",  # 联网搜索
        "function": None
    },

]

# tools[0].function.parameters:不能为空
response = client.chat.completions.create(
    model="glm-4-alltools",  # 填写需要调用的模型名称
    # model="chatfire-test",  # 填写需要调用的模型名称

    stream=True,
    messages=messages,
    tools=TOOLS,
)
import jsonpath

# for trunk in response:
#     delta = trunk.choices[0].delta
#     # print(trunk)
#     #
#     # print(delta)
#     if delta.content is not None or delta.tool_calls is not None:
#         #     # print(trunk.choices[0].delta.content, end="")
#         #     # print(trunk.choices[0].delta.content, end="")
#         #     # print(trunk.choices[0].delta)
#         #     print(trunk.choices[0].tool_calls)
#         #     print(delta)
#         tool_info = jsonpath.jsonpath(delta.model_dump(), '$..[input,outputs]')
#         tool_context = []
#         if tool_info:
#             # print(f"{tool_info}\n\n")
#             for info in tool_info:  # 触发其他画画工具
#                 print(info, end=" ")
#         if delta.content:
#             print(delta.content, end="")
#         # break
#
#     # if delta.tool_calls:
#     #         print(delta.tool_calls[0].model_dump())

tool_name = ""
tool_outputs = []
for trunk in response:
    print(trunk)
    delta = trunk.choices[0].delta
    # print(delta)
    if delta.tool_calls:
        tool_delta = delta.tool_calls[0]
        tool_type = tool_delta.type
        if tool_name != tool_type:
            tool_name = tool_type
            print(tool_name)
            if tool_name == "drawing_tool":
                print(f"""```inputs\n""", end='')
            if tool_name == "web_browser":
                print(f"""```inputs\n""", end='')
            if tool_name == "code_interpreter":
                print(f"""```inputs\n""", end='')
        # print(tool_delta)

        # print(f"TOOL_TYPE: {tool_type}")
        tool_input = tool_delta.__getattr__(tool_type).get('input')  # {'input': 'A'}
        if tool_input:
            print(tool_input, end="")
        if tool_input == "":
            print("\n```\n\n")

        tool_outputs = tool_delta.__getattr__(tool_type).get('outputs')  # {'input': 'A'}
        if tool_outputs:
            print(tool_outputs)

        # print(tool_input, end="")
        # print(tool_outputs, end="")

    # print(delta)
    if delta.content:
        print(delta.content, end="")
