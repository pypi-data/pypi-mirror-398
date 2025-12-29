#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 4v
# @Time         : 2023/11/20 10:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.io.image import image_to_base64, file_to_base64
from openai import OpenAI, AsyncOpenAI
from openai.types.chat.completion_create_params import ResponseFormat
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest

base_url = os.getenv('OPENAI_BASE_URL')
base_url = 'https://apis.chatfire.cn/v1'
# openai = OpenAI(api_key='sk-pVU2SlVDgz4cLOXn52E081A18566433188AcF2Fa4eFf5e72', base_url=base_url)
openai = OpenAI()

# image_url = image_to_base64('/Users/betterme/PycharmProjects/AI/ChatLLM/data/invoice.jpg', for_image_url=True)
base64_image = image_to_base64('demo.png', for_image_url=True)

# file_to_base64("/Users/betterme/PycharmProjects/AI/ChatLLM/examples/openaisdk/new.pdf")
# print(image_url2)

image_url = "https://api.chatllm.vip/minio/chatfire/fire.png"
image_url = "https://taosha01-1253585015.cos.ap-shanghai.myqcloud.com/typora/24951712814992_.pic_thumbnail.jpg"

image_urls = [
    {"type": "image_url", "image_url": {"url": image_to_base64(p, for_image_url=True)}}
    for p in Path().glob('img_7.png')
]
#
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": f"解释图片"},
            # {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
            # {"type": "image_url", "image_url": {"url": base64_image}},
            # {"type": "image_url", "image_url": {"url": image_url}},

            # sparkai 格式
            # {'type': 'image_url', 'image_url': 'http://ai.chatfire.cn/files/images/demo-sparkai-1713835902026-sparkai-a43123877.jpg'},
            {'type': 'image_url', 'image_url': {'url': 'http://ai.chatfire.cn/files/images/demo-sparkai-1713835902026-sparkai-a43123877.jpg'}}

        ],

    }
]

response = openai.chat.completions.create(
    # model='gpt-4-vision-preview',
    # model="gemini-pro-vision",

    # model="claude-3-haiku-20240307",
    # model="claude-3-sonnet-20240229",
    # model="claude-3-opus-20240229",

    # model='glm-4v',
    model='step-1v',
    # model='yi-vl-plus',

    # model='kimi', # ocr

    messages=messages,
    max_tokens=100,
    temperature=0,
    # response_format={"type": "json_object"}
)

print(response.dict())

# response = client.chat.completions.create(input='你好', model='tts-1', voice='alloy')
