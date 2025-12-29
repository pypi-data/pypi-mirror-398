#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo 区分能thinking的模型
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

# 404 403 429
client = OpenAI(
    #
    base_url=os.getenv("VOLC_BASE_URL"),  # /chat/completions
    # api_key=os.getenv("VOLC_API_KEY"),

    api_key="36344348-e28a-4e8c-aa65-996c5c3a9a78"


    # api_key=os.getenv("OPENAI_API_KEY") +'-3587'

)
models = """
doubao-1.5-vision-pro-250328
doubao-1-5-vision-pro-32k-250115
doubao-1-5-ui-tars-250428
doubao-1-5-pro-32k-250115
doubao-1-5-pro-256k-250115
doubao-1-5-pro-32k-character-250715
doubao-1-5-pro-32k-character-250228
doubao-1-5-thinking-pro-250415
doubao-1-5-thinking-pro-m-250428
doubao-1-5-thinking-vision-pro-250428
""".split()

models = """
doubao-seed-1.6-250615
doubao-seed-1-6-250615
doubao-seed-1-6-vision-250815

doubao-seed-1-6-flash-250715
doubao-seed-1-6-flash-250615

doubao-seed-1-6-thinking-250615
doubao-seed-1-6-thinking-250715
""".split()

models = ['doubao-seed-1-6-vision-250815']

models = ["doubao-1-5-pro-32k-250115"]
models = {
    "doubao-1-5-pro-32k-250115",
    "doubao-1-5-pro-256k-250115",
    "doubao-1-5-pro-32k-character-250715",
    "doubao-1-5-pro-32k-character-250228",
    "doubao-1.5-vision-pro-250328",
    "doubao-1-5-vision-pro-32k-250115",
    "doubao-1-5-thinking-pro-250415",
    "doubao-1-5-thinking-pro-m-250428",
    "doubao-1-5-thinking-vision-pro-250428",
    "doubao-1-5-ui-tars-250428",
}

models = {
    "doubao-1-5-thinking-pro-250415",
    "doubao-1-5-thinking-pro-m-250428",
    "doubao-1-5-thinking-vision-pro-250428",
    "doubao-1-5-ui-tars-250428",
}

models = {
    # "doubao-seed-1.6-250615",
    # "doubao-seed-1-6-250615",
    # "doubao-seed-1-6-vision-250815",
    # "doubao-seed-1-6-thinking-250615",
    "doubao-seed-1-6-thinking-250715"
}
models = {
    # "deepseek-r1-250528",

    "doubao-1-5-ui-tars-250428"
}

models = {
    "doubao-seed-1-6-lite-251015"
}

models = {
    "doubao-seed-1-6-flash-250828",
    "doubao-seed-1-6-251015"
}
def run(model="deepseek-r1-250528", thinking="disabled"):
    try:
        completion = client.chat.completions.create(
            # model="ep-20241225184145-7nf5n",
            model=model,
            # model="doubao-1-5-pro-32k-250115",
            # model="doubao-1-5-thinking-vision-pro-250428",

            # model="doubao-lite-32k-character",
            # model="doubao-pro-32k-character",

            # model="doubao-pro-32k-search",

            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ' '.join(['hi']*32000)
                        },
                        # {
                        #     "type": "image_url",
                        #     "image_url": {
                        #         "url": "https://ark-project.tos-cn-beijing.ivolces.com/images/view.jpeg"
                        #     }
                        # }
                    ]
                }
            ],
            # top_p=0.7,
            top_p=None,
            temperature=None,
            stream=True,
            stream_options={"include_usage": True},
            max_tokens=1,

            extra_body={
                "thinking": {
                    "type": thinking
                }
            }
        )
        for i in completion:
            logger.debug(i)
    except APIStatusError as e:
        print(e.status_code)

        print(e.response)
        print(e.message)
        print(e.code)
        logger.debug(f'{model} {thinking}')


if __name__ == '__main__':
    models = {"kimi-k2-thinking-251104"}
    models = {"doubao-seed-1-6-lite-251015"}
    for i in range(1):
        for model in models:
            # run(model)
            run(model, thinking="enabled")
            # run(model, thinking="auto")
            # run(model, thinking="disabled")
