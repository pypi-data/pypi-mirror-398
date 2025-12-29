#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_moderations
# @Time         : 2025/2/5 08:38
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.io.image import image_to_base64

from openai import OpenAI

base64_image = image_to_base64('1.png', for_image_url=True)
client = OpenAI(
    # base_url="https://ai.gitee.com/v1",
    # api_key="AHKZ65ARNFH8QGMUUVCPECDTZVOLRPUXIKPGAC1Y",

    # base_url="https://api-proxy.oaipro.com/v1",
    base_url="https://api.openai.com/v1",

    api_key="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"
)
#
response = client.moderations.create(
    model="omni-moderation-latest",
    input=[
        {
            "type": "text",
            "text": "...text to classify goes here..."
        },
        {
            "type": "image_url",
            "image_url": {
                "url": base64_image
            }
        }
    ],
)

#
# response = client.moderations.create(
# 	model="omni-moderation-latest",
# 	input=[
# 		{
# 			"type": "image_url",
# 			"image_url": {
# 				"url": base64_image
# 			}
# 		}
# 	],
# )
#
# print(response.model_dump_json(indent=2))
