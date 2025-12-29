#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/call-vertex-using-openai-library?hl=zh-cn#supported_parameters

"""

response_format 直接传递“application/json”。
"""
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.llm.openai_utils import to_openai_completion_params
from meutils.io.files_utils import to_base64

# base64_audio = arun(to_base64("https://oss.ffire.cc/files/lipsync.mp3"))
# base64_image = arun(to_base64("https://oss.ffire.cc/cdn/2025-04-01/duTeRmdE4G4TSdLizkLx2B", content_type="image/jpg"))

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),

    base_url=os.getenv("GOOGLE_BASE_URL"),
)

model = "models/gemini-2.5-pro-exp-03-25"
# model = "gemini-2.5-pro-preview-03-25"
# model = "gemini-2.0-flash"
# model = "gemini-2.0-flash"  # openai.BadRequestError: Error code: 400 - [{'error': {'code': 400, 'message': 'Unable to submit request because thinking_budget is only supported when enable_thinking is true. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini', 'status': 'INVALID_ARGUMENT'}}]

print(client.models.list().model_dump_json(indent=4))

print([model.id.removeprefix("models/") for model in client.models.list().data if
       'flash' in model.id or 'gemma' in model.id] | xjoin(','))

print([model.id.removeprefix("models/") for model in client.models.list().data if
       'flash' in model.id or 'gemma' in model.id or 'pro' in model.id] | xjoin(','))# {
#     "gemini-2.0-pro-exp": "models/gemini-2.0-pro-exp",
#     "gemini-2.0-pro-exp-02-05": "models/gemini-2.0-pro-exp-02-05",
#     "gemini-2.5-pro-exp-03-25": "models/gemini-2.5-pro-exp-03-25",
#     "gemini-2.0-flash-thinking-exp": "models/gemini-2.0-flash-thinking-exp",
#     "gemini-2.0-flash": "models/gemini-2.0-flash"
#
# }


import base64
import requests
from openai import OpenAI


prompt = "1+1"


completion = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    # "text": "9个8如何加减乘除运直得到1000",
                    # "text": "如何比较9.8 9.11哪个大"
                    "text": prompt,
                },
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         "url": uri,
                #     }
                # }
            ]
        },
    ],
    # reasoning_effort="high",
    # reasoning_effort="low",
    # reasoning_effort="none",

    # reasoning_effort=None,
    temperature=0.1

)
print(completion)

#
# tools = [
#   {
#     "type": "function",
#     "function": {
#       "name": "google_search",
#
#     }
#   }
# ]
# #
# messages = [{"role": "user", "content": "今天南京天气"}]
# response = client.chat.completions.create(
#   model="gemini-2.0-flash-thinking-exp",
#   messages=messages,
#   # tools=tools,
#   # tool_choice="auto"
# )
#
# "generationConfig": {
#     "thinkingConfig": {
#         "includeThoughts": true,
#           "thinkingBudget": 1024
#     }
#   }

# print(response)

# gemini-2.0-flash-audio
# completion = client.chat.completions.create(
#     model="gemini-2.0-flash",
#     # modalities=["text", "audio"],
#     audio={"voice": "alloy", "format": "wav"},
#     messages=[
#         {
#             "role": "user",
#             "content": "Is a golden retriever a good family dog?"
#         }
#     ]
# )
# print(completion.choices[0].message)
# if __name__ == '__main__':
#     messages = [
#
#         {
#             "role": "user", "content": [
#             {
#                 "type": "text",
#                 "text": "一句话总结"
#             },
#             # {
#             #     "type": "image_url",
#             #     "image_url": {
#             #         "url": base64_image
#             #     }
#             # }
#         ]
#         }
#
#     ]
#     # messages = [
#     #     {
#     #         "role": "user",
#     #         "content": [
#     #             {
#     #                 "type": "text",
#     #                 "text": "一句话总结",
#     #             },
#     #             {
#     #                 "type": "input_audio",
#     #                 "input_audio": {
#     #                     "data": base64_audio,
#     #                     "format": "wav"
#     #                 }
#     #             }
#     #         ],
#     #     }
#     # ]
#
#     # messages = [
#     #     {
#     #         "role": "user",
#     #         "content": [
#     #             {
#     #                 "type": "text",
#     #                 "text": "画条狗",
#     #             }
#     #         ],
#     #     }
#     # ]
#     #
#     try:
#         completion = client.chat.completions.create(
#             # model="models/gemini-2.5-pro-preview-03-25",
#             model="models/gemini-2.5-pro-exp-03-25",
#             # model="models/gemini-2.0-flash",
#             # model="models/gemini-2.0-flash-exp-image-generation",
#             messages=messages,
#             # top_p=0.7,
#             top_p=None,
#             temperature=None,
#             # stream=True,
#             stream=False,
#
#             max_tokens=None,
#             # extra_body=dict(response_modalities = ['Text', 'Image'],)
#
#         )
#     except APIStatusError as e:
#         print(e.status_code)
#
#         print(e.response)
#         print(e.message)
#         print(e.code)
#     print(completion)
#     for chunk in completion:  # 剔除extra body
#         print(chunk)
#         if chunk.choices:
#             print(chunk.choices[0].delta.content)
