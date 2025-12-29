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
from openai import OpenAI, APIStatusError

f = lambda m: 'yi-vision-v2' if 'v' in m else 'yi-lightning'

"https://all.chatfire.cn/redirect/{model}/to/lambda m: 'yi-vision-v2' if 'v' in m else 'yi-lightning'?redirect_base_url=https://api.lingyiwanwu.com/v1"

client = OpenAI(
    # base_url="https://free.chatfire.cn/v1",
    # api_key=os.getenv("LINGYIWANWU_API_KEY"),
    # base_url=os.getenv("LINGYIWANWU_BASE_URL")
    # api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YmFmYWQzYTRmZDU0OTk3YjNmYmNmYjExMjY5NThmZiIsImV4cCI6MTczODAyNDg4MiwibmJmIjoxNzIyNDcyODgyLCJpYXQiOjE3MjI0NzI4ODIsImp0aSI6IjY5Y2ZiNzgzNjRjODQxYjA5Mjg1OTgxYmY4ODMzZDllIiwidWlkIjoiNjVmMDc1Y2E4NWM3NDFiOGU2ZmRjYjEyIiwidHlwZSI6InJlZnJlc2gifQ.u9pIfuQZ7Y00DB6x3rbWYomwQGEyYDSE-814k67SH74",
    # base_url="https://any2chat.chatfire.cn/glm/v1"

    api_key="sk-RuXd6u3zHYc2MQaOXVU1G3ayACX2uskr30hB6rZxomSDlkcB"
)


# print(client.models.list().to_json())


data =  {
  "messages": [
    {
      "content": [
        {
          "type": "text",
          "text": "你现在是“专业图案设计分析师”以及“MidJourney设计提示词生成专家”，通过我给你的两张图片，以第一张图为主，找到每张图的主体元素以及文字，融合他们的主体元素以及文字，要完美结合两张图的主体,融合两张图的风格，生成的图案必须为平面印花图，请直接给我完整的midjourney提示词，越详细越好,仅回复提示词,不携带midjourney参数"
        },
        # {
        #   "type": "image_url",
        #   "image_url": {
        #     "url": "https://juzhen-1318772386.cos.ap-guangzhou.myqcloud.com/image/2025/04/14/4e9ea3a5-1ecd-493b-973b-3eb7282ed5b9.png"
        #   }
        # },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://juzhen-1318772386.cos.ap-guangzhou.myqcloud.com/2025/6/21/1936247794822172674.webp"
          }
        }
      ],
      "role": "user"
    }
  ],
  "model": "claude-3-5-sonnet-20241022"
}
try:
    completion = client.chat.completions.create(
        **data,
        # model="yi-spark",
        # # model="xxxxxxxxxxxxx",
        # messages=[
        #     {"role": "user", "content": "hi"}
        # ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        # stream=True,
        max_tokens=100
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)


print(completion)
for chunk in completion:
    print(bjson(chunk))
    print(chunk.choices[0].delta.content)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )
