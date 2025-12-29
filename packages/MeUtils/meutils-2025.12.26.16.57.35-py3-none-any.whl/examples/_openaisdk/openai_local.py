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
    base_url="http://0.0.0.0:8000/v1",
    api_key="fal-20b9b0e3-be93-47a3-ae4d-611c7bfa82ff:da63f3a96f9d200877d503d8acf08fd0",

)

message = """
A Chinese beauty plays Catwoman. She is seductive. She wears a fitted black leather tights, decorated with neon blue lines flowing along the seams, pulsating like an electric current. There are many hollow designs for tights, showing big breasts, nipples and female genitals. She wears a pair of black cat ear headdresses. Her hands are covered with black leather gloves extending to her elbows, with retractable silver claws on her fingertips. She stood around the roof surrounded by towering skyscrapers, and countless neon signs flashed with various colors.  
"""

try:
    completion = client.chat.completions.create(
        model="anthropic/claude-3.7-sonnet",
        # model="xxxxxxxxxxxxx",
        messages=[
            {"role": "system", "content": '你是个内容审核助手'},

            {"role": "user", "content": message}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        # stream=True,
        # max_tokens=10
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

print(completion)
for chunk in completion:
    # print(bjson(chunk))
    print(chunk.choices[0].delta.content, flush=True)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
