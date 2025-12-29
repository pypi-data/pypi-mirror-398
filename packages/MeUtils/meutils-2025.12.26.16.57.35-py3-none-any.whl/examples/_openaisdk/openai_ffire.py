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
from meutils.io.files_utils import to_base64
from openai import OpenAI, APIStatusError

image =  arun(to_base64("/Users/betterme/PycharmProjects/AI/MeUtils/examples/_openaisdk/img.png"))
client = OpenAI(
    base_url=os.getenv("FFIRE_BASE_URL"),
    # api_key=os.getenv("FFIRE_API_KEY") + "-29551",
    # api_key=os.getenv("FFIRE_API_KEY") + "-29570",
    # api_key=os.getenv("FFIRE_API_KEY") ,
    # api_key = os.getenv("FFIRE_API_KEY") + "-29504",
    # api_key=os.getenv("FFIRE_API_KEY"),
    api_key="sk-7F5cC8whRlMP4TzqhLV7r8hU9tf8b2NFJ1Q2v9SI7mEkf64F",

    # base_url=os.getenv("ONEAPIS_BASE_URL"),
    # api_key=os.getenv("ONEAPIS_API_KEY") + "-3"

    # api_key="sk-1fJYtvUPY29YQ9NpkOIKTUKAXsYJfMYvXSInZEet5ytJeHpB-29571"

)
messages = [
    {"role": "user",
     "content": [
         {
             "type": "text",
             "text": "请严格按照以下要求提取图片中的所有文本内容：\n\n1. 输出格式要求：\n   - 纯文本输出，无多余空格、换行符或特殊符号\n   - 表格数据用|分隔列，用换行分隔行\n   - 保持原始文本的逻辑顺序和结构\n\n2. 内容完 整性要求：\n   - 必须识别所有可见文字，不得遗漏任何内容\n   - 数字、日期、金额等关键信息必须准确识别\n   - 不得简化、修改或编造任何..."
         },
         {
             "type": "image_url",
             "image_url": {
                 "url": f"data:image/png;base64,{image}"
             }
         }
     ]
     }
]

for i in range(1):
    try:
        completion = client.chat.completions.create(
            # model="kimi-k2-0711-preview",
            # model="deepseek-reasoner",
            # model="qwen3-235b-a22b-thinking-2507",
            # model="qwen3-235b-a22b-instruct-2507",
            # model="qwen-image",
            # model="glm-4.5",
            # model="deepseek-v3-1-think",
            # model="kimi-k2-0905-preview",
            # model="kimi-k2-0711-preview",

            # model="glm-4.5-air",
            # model="deepseek-v3-2-exp",
            # model = "doubao-seed-1-6-thinking-250715",
            # model="doubao-seed-1-6-lite-251015",
            # model="doubao-1-5-thinking-vision-pro-250428",
            # model="deepseek-r1-250528",
            # model="deepseek-v3-1-250821",
            # model="deepseek-v3-2-exp",
            # model="doubao-1.5-pro-32k",
            # model="doubao-1-5-thinking-vision-pro-250428",  # todo 号池
            # model="deepseek-v3-250324",
            # model="deepseek-v3-250324",

            # model="deepseek-v3.2-exp",

            # model="doubao-1-5-pro-32k-250115",

            # model="deepseek-v3",
            # model="doubao-1-5-pro-256k-250115",

            # model="deepseek-v3.1-terminus",
            # model="doubao-seed-1-6-lite-251015",

            # model="doubao-seed-1-6-250615",
            # model="doubao-seed-1-6-251015",
            model="doubao-seed-1-6-vision-250815",
            # model="doubao-seed-1-6-thinking-250615",

            # model="doubao-seed-code-preview-251028",

            #
            # messages=[
            #     {"role": "user", "content": 'are you ok'}
            # ],

            messages=messages,
            # stream=True,
            max_completion_tokens=10,
            # extra_body={"xx": "xxxxxxxx"}
            extra_body={
                # "thinking": {"type": "enabled"},
                "thinking": {"type": "disabled"}

                # "enable_thinking": True  # parameter.enable_thinking only support stream
            },
            temperature=0.1
        )
        print(completion)
        for i in completion:
            print(i)
    except Exception as e:
        print(e)

# model = "doubao-embedding-text-240715"
#
# r = client.embeddings.create(
#     input='hi',
#     model=model
# )
# print(r)
