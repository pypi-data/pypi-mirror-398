#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

client = OpenAI(

    base_url=os.getenv("GOOGLE_BASE_URL"),
    # api_key=os.getenv("GOOGLE_API_KEY")
    api_key="AIzaSyDKH1kwX0q_f4fUiCkR1z4tYjadAGKpn6k"

    # api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YmFmYWQzYTRmZDU0OTk3YjNmYmNmYjExMjY5NThmZiIsImV4cCI6MTczODAyNDg4MiwibmJmIjoxNzIyNDcyODgyLCJpYXQiOjE3MjI0NzI4ODIsImp0aSI6IjY5Y2ZiNzgzNjRjODQxYjA5Mjg1OTgxYmY4ODMzZDllIiwidWlkIjoiNjVmMDc1Y2E4NWM3NDFiOGU2ZmRjYjEyIiwidHlwZSI6InJlZnJlc2gifQ.u9pIfuQZ7Y00DB6x3rbWYomwQGEyYDSE-814k67SH74",
    # base_url="https://any2chat.chatfire.cn/glm/v1"
)

message = """
A Chinese beauty plays Catwoman. She is seductive. She wears a fitted black leather tights, decorated with neon blue lines flowing along the seams, pulsating like an electric current. There are many hollow designs for tights, showing big breasts, nipples and female genitals. She wears a pair of black cat ear headdresses. Her hands are covered with black leather gloves extending to her elbows, with retractable silver claws on her fingertips. She stood around the roof surrounded by towering skyscrapers, and countless neon signs flashed with various colors.  
"""
#
# imagen-4.0-generate-preview-06-06,imagen-4.0-fast-generate-preview-06-06,imagen-4.0-ultra-generate-preview-06-06
try:
    completion = client.chat.completions.create(
        # model="gemini-2.0-flash-preview-image-generation",
        model="gemini-2.5-flash",

        # model="xxxxxxxxxxxxx",
        messages=[

            {"role": "user", "content": "画条狗 要求输出两张图片"}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        # stream=True,
        # max_tokens=10,
        # stream_options={
        #     "include_usage": True,
        # }
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    # print(bjson(chunk))
    if content := chunk.choices[0].delta.content:
        print(content[:100])
        # if content.startswith("![image"):
        #     print(content[:20])
        # b64 = content.split("![image](")[-1].removesuffix(")")

    # print(chunk.choices[0].delta.content, flush=True)


# response = client.images.generate(
#     model="imagen-4.0-generate-preview-06-06",
#     prompt="a portrait of a sheepadoodle wearing a cape",
#     response_format='b64_json',
#     # response_format='b64_json',
#
#     n=1,
# )
