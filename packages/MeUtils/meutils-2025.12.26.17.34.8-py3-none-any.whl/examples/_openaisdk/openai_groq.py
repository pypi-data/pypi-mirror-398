#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_tts
# @Time         : 2024/3/27 12:10
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI, AsyncOpenAI
import os

#
# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "system",
#             "content": "you are a helpful assistant."
#         },
#         {
#             "role": "user",
#             "content": "Explain the importance of fast language models",
#         }
#     ],
#     model="llama3-8b-8192",
# )
#
# print(chat_completion.choices[0].message.content)
#
# base_url = 'http//:0.0.0.0:8000/v1'
# api_key = 'xx'
# client = OpenAI(base_url=base_url, api_key=base_url)
#
#
#
#
# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Project      : AI.  @by PyCharm
# # @File         : openai_asr
# # @Time         : 2023/11/23 13:10
# # @Author       : betterme
# # @WeChat       : meutils
# # @Software     : PyCharm
# # @Description
# import io
# import os
#
# import requests
#
# from meutils.pipe import *
from openai import OpenAI

from groq import Groq

client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY", "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"),
    # base_url="https://api.groq.com/openai/v1",

)

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    # base_url=os.getenv("GROQ_BASE_URL"),
    base_url="https://groq.chatfire.cc/v1",

)
#
# # # response_format: Literal["json", "text", "srt", "verbose_json", "vtt"]
# file = open("/Users/betterme/PycharmProjects/AI/MeUtils/meutils/ai_audio/asr/whisper-1719913495729-54f08dde5.wav.mp3.mp3", 'rb')  # 正确
#
# with timer():
#     _ = client.audio.transcriptions.create(
#         file=file,
#         model="whisper-large-v3",
#         # model="hailuo2whisper",
#         response_format="text",  # ["json", "text", "srt", "verbose_json", "vtt"]
#         # response_format="srt",  # ["json", "text", "srt", "verbose_json", "vtt"]
#         # response_format="verbose_json",  # ["json", "text", "srt", "verbose_json", "vtt"]
#         # response_format="vtt",  # ["json", "text", "srt", "verbose_json", "vtt"]
#         # response_format="json",  # ["json", "text", "srt", "verbose_json", "vtt"]
#         # language='ja'
# # [sv no br mn pa sa ja pt jv ko gu lv sq mg mi sk la ml lb ln ha tr cs sl kn ne mr uz bo ca fi ur bg et eu lo su es nl fa gl km af tg el te ro hu bs si sn ka en fr am fo so yi ta hy sr is zh th kk be as cy bn hr sw mt ru pl uk ms az ht my haw ar he hi vi da lt mk yo de id tl tt yue sd ps tk nn ba it oc]',
#
#     )
#     print(_)

# _ = client.audio.translations.create(
#     file=file,
#     model="whisper-large-v3",
#     # model="hailuo2whisper",
#     # response_format="text",  # ["json", "text", "srt", "verbose_json", "vtt"]
#     # response_format="srt",  # ["json", "text", "srt", "verbose_json", "vtt"]
#     # response_format="verbose_json",  # ["json", "text", "srt", "verbose_json", "vtt"]
#     # response_format="vtt",  # ["json", "text", "srt", "verbose_json", "vtt"]
#     response_format="json",  # ["json", "text", "srt", "verbose_json", "vtt"]
#     prompt="将其翻译成日语"
#
# )
# print(_)


# model = "llama-3.1-8b-instant"
# messages = [
#     {'role': 'user', 'content': '你是谁'}
# ]
# response = client.chat.completions.create(
#     # model='alibaba/Qwen1.5-110B-Chat',
#     model=model,
#     # messages=[
#     #     {'role': 'user', 'content': "抛砖引玉是什么意思呀"}
#     # ],
#     messages=messages,
#     stream=False
# )
#
# print(response)


# print(client.models.list().model_dump_json(indent=4))
# {
#     "data": [
#         {
#             "id": "gemma2-9b-it",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Google",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "gemma-7b-it",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Google",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "llama-3.1-405b-reasoning",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Meta",
#             "active": true,
#             "context_window": 131072,
#             "public_apps": [
#                 "chat"
#             ]
#         },
#         {
#             "id": "llama-3.1-70b-versatile",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Meta",
#             "active": true,
#             "context_window": 131072,
#             "public_apps": null
#         },
#         {
#             "id": "llama-3.1-8b-instant",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Meta",
#             "active": true,
#             "context_window": 131072,
#             "public_apps": null
#         },
#         {
#             "id": "llama3-70b-8192",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Meta",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "llama3-8b-8192",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Meta",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "llama3-groq-70b-8192-tool-use-preview",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Groq",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "llama3-groq-8b-8192-tool-use-preview",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Groq",
#             "active": true,
#             "context_window": 8192,
#             "public_apps": null
#         },
#         {
#             "id": "mixtral-8x7b-32768",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "Mistral AI",
#             "active": true,
#             "context_window": 32768,
#             "public_apps": null
#         },
#         {
#             "id": "whisper-large-v3",
#             "created": 1693721698,
#             "object": "model",
#             "owned_by": "OpenAI",
#             "active": true,
#             "context_window": 1500,
#             "public_apps": null
#         }
#     ],
#     "object": "list"
# }
# from meutils.schemas.openai_types import ChatCompletionRequest
# from meutils.llm.openai_utils import to_openai_completion_params, token_encoder, token_encoder_with_cache
#
# request = ChatCompletionRequest(
#     model="llama-3.1-8b-instant",
#     messages=[{'role': 'user', 'content': '你是谁'}])
#
# data = to_openai_completion_params(request)
#
# data.pop('extra_body')
# client.chat.completions.create(**data)
