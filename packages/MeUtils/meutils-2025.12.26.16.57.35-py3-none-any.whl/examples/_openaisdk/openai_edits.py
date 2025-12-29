#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_edits
# @Time         : 2025/6/23 16:51
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from meutils.llm.openai_utils import to_openai_params
from meutils.schemas.image_types import ImageRequest, ImageEditRequest

from openai import OpenAI

client = OpenAI(
    # base_url=os.getenv("GITEE_BASE_URL"),
    # api_key=os.getenv("GITEE_API_KEY"),
    base_url="http://0.0.0.0:8000/v1",
    api_key="null",

)

# r = client.images.edit(
#     model="4x-UltraSharp",
#     prompt="",
#     image=open("/Users/betterme/PycharmProjects/AI/MeUtils/examples/img.png", "rb"),
#     response_format="url"
# )

model = "FLUX.1-Kontext-dev"
# model ="qwen-image"
model = "fal-ai/flux-pro/kontext"
# model = "fal-ai/flux-pro/kontext/max"

# model = "fal-ai/gemini-25-flash-image"

data = {
    'model': model,
    'prompt': "将小黄鸭放在衣服上",
    'size': "1024x1024",
    'steps': "20",
    'guidance_scale': "2.5",
    'return_image_quality': "80",
    'return_image_format': "PNG",
    # 'lora_weights': json.dumps(lora_weights_data),  # 将字典转换为 JSON 字符串
    'lora_scale': "1",

    # 'image': open('/Users/betterme/PycharmProjects/AI/MeUtils/meutils/apis/images/image2.webp', 'rb').read(),
    'image': [

        # open('/Users/betterme/PycharmProjects/AI/MeUtils/meutils/apis/images/image1.webp', 'rb'),
        # open('/Users/betterme/PycharmProjects/AI/MeUtils/meutils/apis/images/image2.webp', 'rb')
        open('/Users/betterme/PycharmProjects/AI/MeUtils/meutils/apis/images/image1.webp', 'rb').read(),
        open('/Users/betterme/PycharmProjects/AI/MeUtils/meutils/apis/images/image2.webp', 'rb').read()
    ]

}

data = to_openai_params(ImageEditRequest(**data))

r = client.images.edit(
    **data
)

# import requests
#
# API_URL = "https://ai.gitee.com/v1/images/upscaling"
# API_TOKEN = "5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"
# headers = {
# 	"Content-Type": "application/json",
# 	"Authorization": f"Bearer {API_TOKEN}"
# }
#
# def query(payload):
# 	response = requests.post(API_URL, headers=headers, data=payload)
# 	return response.content
#
# output = query({
# 	"prompt": "变成一幅油画",
# 	"model": "AnimeSharp",
# 	"model_name": "4x-UltraSharp",
# 	"outscale": 4,
# 	"image_url": "https://juzhen-1318772386.cos.ap-guangzhou.myqcloud.com/mj/2025/05/07/25fc47e6-ed58-482b-bb14-a3df00d9b92c.png",
# 	"output_format": "png"
# })
#
# with open("output.png", "wb") as file:
# 	file.write(output)
