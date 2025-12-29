#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_v
# @Time         : 2025/2/11 16:13
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

# url = "https://oss.ffire.cc/files/kling_watermark.png"



import openai

url = "https://ts3.cn.mm.bing.net/th?id=OIP-C.BYyILFgs3ATnTEQ-B5ApFQHaFj&w=288&h=216&c=8&rs=1&qlt=90&o=6&dpr=1.3&pid=3.1&rm=2"


c = openai.OpenAI(

    api_key=os.getenv("OPENAI_API_KEY") + "-575",
    base_url = "https://api.chatfire.cn/v1",
    # api_key=os.getenv("OPENAI_API_KEY_OPENAI")
)
x = c.chat.completions.create(model='gpt-4o',messages=[
            {
                'role': 'user',
                'content': [{
                    "type": "text",
                    "text": '总结一下'
                }, {
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                }]
            }
        ])