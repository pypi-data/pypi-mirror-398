#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : dalle3
# @Time         : 2023/11/23 15:19
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI, AsyncOpenAI

# client = OpenAI(
#     http_client=httpx.Client(
#         follow_redirects=True
#     ),
#
#     # base_url=os.getenv("OPENAI_BASE_URL"),
#     # api_key='sk-',
#
#     # base_url='https://api.gptgod.online/v1',
#     base_url="https://ngedlktfticp.cloud.sealos.io/v1",
#     # api_key="sk-"
# )
# response = client.images.generate(
#     prompt='画条可爱的狗',  # 图片描述
#     # model='gpt-4-dalle',
#     # model='dall-e-3',
#     model='midjourney',
#     n=1,
# )


client = OpenAI()

response = client.images.generate(
    prompt='画条可爱的狗',  # 图片描述
    model='dall-e-3',
    size='1024x1792',
    n=1,
)

print(response.data)
print(response.data[0])
image_url = response.data[0].url

print(image_url)

from urllib.parse import unquote