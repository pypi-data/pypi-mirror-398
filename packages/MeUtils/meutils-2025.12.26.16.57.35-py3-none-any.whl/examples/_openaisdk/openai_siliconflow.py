#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.llm.clients import OpenAI

from openai import OpenAI
from openai import APIStatusError

client = OpenAI(
    # api_key=os.getenv("SILICONFLOW_API_KEY"),
    api_key="sk-hygxhbsktjvjzxvljpbccjtkkpsnjuueuuacjoqefgnvhesi",
    base_url="https://api.siliconflow.cn/v1",
    # http_client=httpx.Client(
    #     proxy=p,
    #     timeout=30)
)

models = client.models.list().data
models = {
    m.id.removeprefix("Pro/").split('/', maxsplit=1)[1].lower(): m.id.removeprefix("Pro/") for m in models
}

model = "01-ai/Yi-1.5-6B-Chat"
# model = "THUDM/glm-4-9b-chat"
# model = "google/gemma-2-9b-it"
# model = "internlm/internlm2_5-7b-chat"
# model = "google/gemma-2-27b-it"
# model = 'chat-kolors'
# model = "deepseek-ai/DeepSeek-V2-Chat"
# model = "meta-llama/Meta-Llama-3.1-8B-Instruct"
# model = "meta-llama/Meta-Llama-3.1-70B-Instruct"
# model = 'meta-llama/Meta-Llama-3.1-405B-Instruct'
model = "deepseek-ai/DeepSeek-V2.5"
# model = "deepseek-ai/DeepSeek-R1"
# model = "Qwen/Qwen3-8B"
model = "zai-org/GLM-4.5V"
# api black-forest-labs/FLUX.1-schnell
messages = [
    {'role': 'user', 'content': '详细说明 9.8 9.11那个大'}
]

try:
    response = client.chat.completions.create(
        # model='alibaba/Qwen1.5-110B-Chat',
        model=model,
        # messages=[
        #     {'role': 'user', 'content': "抛砖引玉是什么意思呀"}
        # ],
        messages=messages,
        stream=True,
        max_tokens=1,
        # extra_body={"enable_thinking": False}
    )
    print(response)
    for chunk in response:
        print(chunk)
except APIStatusError as e:
    print(e)
    print("status_code", type(e.response.status_code))


def request_many():
    for i in tqdm(range(1000)):
        response = client.chat.completions.create(
            # model='alibaba/Qwen1.5-110B-Chat',
            model=model,
            messages=[
                {'role': 'user', 'content': "1+1"},
                {'role': 'assistant', 'content': """
                <think>
                reasoning_content
                </think>
                content
"""},

                {'role': 'user', 'content': "抛砖引玉是什么意思呀" * 1}
            ],
            # messages=messages,
            stream=True,
            max_tokens=1,
            extra_body={"enable_thinking": False}

        )
        print(response)
        # for chunk in response:
        #     print(chunk)


""""
curl -i --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header 'Authorization: Bearer sk-x' \
  --header 'Content-Type: application/json' \
  --data '{
  "model": "THUDM/GLM-4-9B-0414",
  "max_tokens": 5,
  "stream": true,
  "messages": [
    {
      "role": "user",
      "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
    }
  ]
}'



curl --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header 'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE' \
  --header 'Authorization: Bearer sk-qucqfujlfogrbzswzgfctbmzjbmprqhcgbsniwruqfeuvcus' \
  --header 'Content-Type: application/json' \
  --data '{
  "model": "deepseek-ai/DeepSeek-V3.2-Exp",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ]
}'


"""
