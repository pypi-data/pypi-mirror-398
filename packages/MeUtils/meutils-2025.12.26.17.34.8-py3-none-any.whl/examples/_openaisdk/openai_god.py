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
from openai import OpenAI, APIStatusError

from meutils.llm.openai_utils import to_openai_params
from meutils.schemas.image_types import ImageRequest, RecraftImageRequest, ImagesResponse

client = OpenAI(
    api_key=os.getenv("GOD_API_KEY"),
    base_url=os.getenv("GOD_BASE_URL"),
)

# try:
# completion = client.chat.completions.create(
#         # model="net-gpt-3.5-turbo",
#         # model="net-gpt-3.5-turbo-16k",
#         # model="net-gpt-4o-mini",
#         # model="net-gpt-4o",
#         model="net-claude-1.3-100k",
#         messages=[
#             {"role": "user", "content": "南京天气如何"}
#         ],
#         # top_p=0.7,
#         top_p=None,
#         temperature=None,
#         stream=True,
#         max_tokens=6000
#     )
# except APIStatusError as e:
#     print(e.status_code)
#
#     print(e.response)
#     print(e.message)
#     print(e.code)
#
# for chunk in completion:
#     print(chunk.choices[0].delta.content)


model = "gemini-3-pro-image-preview-4k"
# model = "gemini-3-pro-image-preview"

request = ImageRequest(
    model=model,
    prompt="将鸭子放在女人的t恤上",
    # aspect_ratio="9:16",
    # size="1024x1024",
    # size="1024x1024",

    # image=[
    #     "https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
    #     "https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"
    # ],

    # image=["https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"]

    image="https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"

)


print(request)


data = to_openai_params(request)

logger.debug(bjson(data))

r = client.images.generate(
    **data
)
