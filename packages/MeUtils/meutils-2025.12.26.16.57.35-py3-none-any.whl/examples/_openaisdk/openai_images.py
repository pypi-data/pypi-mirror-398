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
import langchain
from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

from openai import OpenAI

# response = OpenAI().images.generate(
#     model="stable-diffusion-3",
#     # model="kling",
#
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="standard",
#     style="vividx",
#     n=1,
#     extra_body={
#         "guidance_scale": 4.5,
#         "num_inference_steps": 25,
#         "negative_prompt": ""
#     }
# )
#

# from openai import OpenAI
#
# response = OpenAI().images.generate(
#     # model="stable-diffusion-3",
#     model="kling",
#
#     prompt="漫天的星河，浪漫，神秘。超高清，最好的质量，超高细节的画质，8K分辨率",
#     size="1024x1024",
#     n=1
# )


data = {
    'prompt': '一只可爱的边牧在坐公交车，卡通贴纸。动漫3D风格，超写实油画，超高分辨率，最好的质量，8k',

    # 'model': 'step-1x-medium',
    'model': 'seededit',

    # 'n': 2, 'quality': 'hd', 'response_format': 'url', 'size': '1024x1024', 'style': 'vivid',
    # 'extra_body': {'guidance_scale': 4.5, 'num_inference_steps': 25, 'seed': None, 'negative_prompt': None}
}

from openai import OpenAI

# model = "stable-diffusion-3"
# with timer(model):
#     response = OpenAI(
#         # base_url="http://0.0.0.0:8000/v1"
#         # base_url="https://openai-dev.chatfire.cn/images/v1",
#         # base_url="https://openai.chatfire.cn/images/v1"
#
#         # base_url="http://111.173.117.175:40001/images/v1"
#         # base_url="https://api.stepfun.com/v1",
#         # api_key="4ewbnANQogxIX8DUY3Cz2VAMlB3ij39cwDrgQfkDtuNAoexu3E7CEJbR8USXVa3pA"
#     ).images.generate(
#         model=model,
#         prompt=prompt,
#     )
#     print(response)

# with timer('image'):
#     model = 'flux-schnell'
#
#     response = OpenAI(
#     ).images.generate(
#         model=model,
#         prompt=prompt,
#     )
#     print(response)
#
# with timer('image'):
#     model = 'flux-pro'
#
#     response = OpenAI(
#     ).images.generate(
#         model=model,
#         prompt=prompt,
#     )
#     print(response)

# model = 'step-1x-medium'
# with timer(model):
#     response = OpenAI().images.generate(
#         model=model,
#         prompt=prompt,
#     )
#     print(response)
#
# model = 'kling'
# with timer(model):
#     response = OpenAI().images.generate(
#         model=model,
#         prompt=prompt,
#     )
#     print(response)
#


with timer('image'):
    model = 'flux-pro'
    model = 'flux-dev'
    model = 'flux-schnell'
    # model = "cogview-3"

    # model = "cogview-3-plus"
    # model = "cogview-3-plus"

    # model = "cogview-3-plus"

    # model = 'step-1x-medium'
    # model = 'stable-diffusion-xl-base-1.0'
    # model = "black-forest-labs/flux.1.1-pro"

    # model = "black-forest-labs/FLUX.1-schnell"
    # model = "black-forest-labs/FLUX.1-dev"
    # model = "flux-dev"

    client = OpenAI(
        # api_key=os.getenv("GOD_API_KEY"),
        # base_url=os.getenv("GOD_BASE_URL"),

        api_key=os.getenv("FFIRE_API_KEY"),
        base_url=os.getenv("FFIRE_BASE_URL"),

        # api_key="6b419ce2-096c-44ce-b2f5-0914ee8f3cf8",
        # base_url=os.getenv("VOLC_BASE_URL")

        # api_key=os.getenv("OPENAI_API_KEY") +,
        # api_key=os.getenv("OPENAI_API_KEY") + "-359", # 3083
        # api_key=os.getenv("OPENAI_API_KEY") + "-21227", # 3083

        # base_url="https://api.pisces.ink/v1",
        # base_url="https://all.chatfire.cn/pisces/v1",
        # api_key="pisces-76e2d5da837d4575847abc06bda84d20",
        # api_key="pisces-03dedafafcbf4c1b9c87530858510932"

        # api_key=os.getenv("OPENAI_API_KEY_OPENAI") + "-3083",

        # api_key=os.getenv("SILICONFLOW_API_KEY"),
        # base_url=os.getenv("SILICONFLOW_BASE_URL"),

        # base_url='https://api.stepfun.com/v1',
        # base_url="http://0.0.0.0:8000/v1",
        # base_url='https://api-dev.chatfire.cn/v1',
        # base_url='https://openai-dev.chatfire.cn/api/v1',
        # base_url='https://openai.chatfire.cn/api/v1',
        # base_url="https://openai-dev.chatfire.cn/v1",

        # base_url="http://110.42.51.201:40009/v1"

        # base_url="https://oneapi.chatfire.cn/v1",

        # base_url=os.getenv("MODELSCOPE_BASE_URL"),
        # api_key=os.getenv("MODELSCOPE_API_KEY"),

        # default_query=

    )

    # print(client.models.list())
    # model = 'flux1.0-turbo'
    # model = 'flux1.0-schnell'
    model = 'flux-dev'
    model = "flux-schnell"
    model = "gpt-image-1"

    # model = 'flux1.0-dev'
    # model = 'flux1.0-pro'
    # model = 'flux1.1-pro'
    # model = 'kling'
    # model = 'hunyuan'
    # model = 'cogview-3'
    # model = 'stable-diffusion'
    # model = 'flux.1.1-pro'
    # model = 'flux'
    # model = 'stable-diffusion-3-5-large'
    # model = 'flux-schnell'
    # model = 'flux-schnell'
    # model = 'seededit'
    # model = 'dall-e-3'
    # model = 'kolors'
    # model = 'images'

    # model = "deepseek-ai/janus-pro-7b"
    # model="deepseek-ai/Janus-Pro-7B"

    # model = "flux.1.1-pro"
    # model = "ideogram-ai/ideogram-v2-turbo"

    # response = client.images.generate(
    #     model=model,
    #     prompt=prompt,
    #     extra_body={
    #         "num_inference_steps": 1,
    #         "prompt_enhancement": True
    #     },
    #     # size="1700x1275"
    # )

    # model = "recraft-v3"
    # model = "fal-ai/recraft-v3"
    # model = "flux-pro-1.1-ultra"
    # prompt = '一只可爱的边牧在坐公交车，卡通贴纸。动漫3D风格，超写实油画，超高分辨率，最好的质量，8k'
    prompt = "裸体女孩"

    model = "doubao-seedream-3-0-t2i-250415"
    model = "black-forest-labs/FLUX.1-Krea-dev"
    model = "Qwen/Qwen-Image"
    model = "MusePublic/FLUX.1-Kontext-Dev"
    model = "doubao-seedream-4-0-250828"  # https://ark.cn-beijing.volces.com/api/v3/chat/completions
    # model = "DiffSynth-Studio/FLUX.1-Kontext-dev-lora-SuperOutpainting"
    # model = "DiffSynth-Studio/FLUX.1-Kontext-dev-lora-highresfix"
    # # model = "black-forest-labs/FLUX.1-Kontext-dev"
    # model="DiffSynth-Studio/FLUX.1-Kontext-dev-lora-ArtAug"

    model = "gemini-2.5-flash-image-preview"
    model = "Qwen/Qwen-Image"

    # flux-kontext-dev

    model = "gemini-3-pro-image-preview-2k"

    model="doubao-seedream-4-0-250828"

    prompt = """
            Seedream 4.5 是字节跳动最新推出的图像多模态模型，整合了文生图、图生图、组图输出等能力，融合常识和推理能力。相比前代4.0模型生成效果大幅提升，具备更好的编辑一致性和多图融合效果，能更精准的控制画面细节，小字、小人脸生成更自然

    ### 模型名

    - `doubao-seedream-4-5-251128`

    ### [同步端点](https://oneapis.apifox.cn/65246320f0)

    - /v1/chat/completions
    - /v1/images/generations
    - /v1/images/edits
    ---
    根据以上内容做个海报
            """

    response = client.images.generate(
        model=model,
        # prompt=prompt,
        # prompt="把图1 里面的人物的背景替换成图2的，保证自然，人物一致性不能改变，只更改背景",
        # prompt="把小黄鸭放在T恤上",
        prompt=prompt,

        response_format="url",
        # extra_body={
        #     "Style": "True",
        #     "controls": {}, ######### 这个看起来更通用些
        #     "aspect_ratio": "1",
        #
        #     "Width": 1024,
        #     "Height": 1024,
        #     "prompt_enhancement": True,
        # },

        # size="1700x1275",

        extra_headers={
            # "X-ModelScope-Async-Mode": "true",
            # "X-ModelScope-Task-Type": "image_generation"

        },

        extra_body={
            # "image": [
            #     "https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
            #     "https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"
            #
            # ],
            # "extra_fields": {
            #
            #     "watermark": False,
            #
            # }

            "watermark": True,
        }
    )

    logger.debug(response)

    logger.debug(bjson(response.model_dump()))

    # openai.AuthenticationError: Error code: 401 - {'error': {'message': 'Incorrect API key provided', 'type': 'invalid_api_key'}}
    # openai.APIStatusError: Error code: 402 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details', 'type': 'quota_exceeded'}}

    # client.images.edit()
    # client.images.generate()
