#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : open_router
# @Time         : 2024/10/14 19:04
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from openai import OpenAI
from os import getenv
from meutils.io.files_utils import to_url
from meutils.str_utils import parse_base64

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
    # base_url="https://openrouter.ai/api/v1",
    # base_url="https://all.chatfire.cn/openrouter/v1",
    # api_key=os.getenv("OPENROUTER_API_KEY"),
    #
    base_url="http://38.46.219.252:9001/v1",

    api_key="sk-Azgp1thTIonR7IdIEqlJU51tpDYNIYYpxHvAZwFeJiOdVWiz",

    # base_url="https://api.huandutech.com/v1",
    # api_key = "sk-qOpbMHesasoVgX75ZoeEeBEf1R9dmsUZVAPcu5KkvLFhElrn"
    # api_key="sk-MAZ6SELJVtGNX6jgIcZBKuttsRibaDlAskFAnR7WD6PBSN6M",
    # base_url="https://new.yunai.link/v1"

    # base_url="https://api.pisces.ink/v1",
    # api_key="pisces-03dedafafcbf4c1b9c87530858510932"
)

# (content=' \n'
completion = client.chat.completions.create(
    # extra_headers={
    #   "HTTP-Referer": $YOUR_SITE_URL, # Optional, for including your app on openrouter.ai rankings.
    #   "X-Title": $YOUR_APP_NAME, # Optional. Shows in rankings on openrouter.ai.
    # },
    # model="meta-llama/llama-3.2-11b-vision-instruct:free",
    # model="openai/o1",
    # model="deepseek/deepseek-r1-0528-qwen3-8b:free",
    # model="google/gemini-2.5-flash-image-preview:free",
    # model="deepseek/deepseek-chat-v3.1:free",
    # model="gemini-2.0-flash-exp-image-generation",
    model="gemini-2.5-flash-image-preview",
    stream=True,
    # max_tokens=10,
    # extra_body={"reasoning_stream": True},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请按下面的提示绘图：\n\n a cat"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://oss.ffire.cc/files/kling_watermark.png"
                    }
                }
            ]
        }
    ]
)
# print(completion.choices[0].message.content)
# # arun(to_url(completion.choices[0].message.images[0]['image_url']['url'], content_type="image/png"))
#
#
# b64_list = parse_base64(completion.choices[0].message.content)
#
# arun(to_url(b64_list, content_type="image/png"))

# '好的，旁边加一只戴墨镜的狗。\n\n![image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABAAAAAQACAIAAADwf7zUAAAgAElEQ'
# arun(to_url(completion.choices[0].message.images[0]['image_url']['url'], content_type="image/png"))

# print(dict(completion.choices[0].message).keys())

# {
#     "index": 0,
#     "type": "image_url",
#     "image_url": {
#         "url": "b64"
#     }
#
# }

for chunk in completion:
    print(chunk.choices[0].delta.content)
