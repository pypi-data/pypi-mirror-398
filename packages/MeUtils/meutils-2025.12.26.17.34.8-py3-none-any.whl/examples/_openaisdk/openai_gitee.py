#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_gitee
# @Time         : 2025/1/3 10:34
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://ai.gitee.com/hf-models/Kwai-Kolors/Kolors/api

from meutils.pipe import *
from openai import OpenAI
from meutils.io.files_utils import to_file

client = OpenAI(
    base_url="https://ai.gitee.com/v1",
    # api_key="WPCSA3ZYD8KBQQ2ZKTAPVUA059J2Q47TLWGB2ZMQ",
    api_key="TICKEDYPY8XTF9ZIMKOFRTQ8IT7UDCE7EC7JRV10"
    # default_headers={"X-Failover-Enabled": "true", "X-Package": "1910"},
)

print(client.models.list())


client.embeddings.create(
    model="Qwen3-Embedding-0.6B",
    input="Your text string goes here"
)
#
# response = client.images.generate(
#     model="Kolors",
#     size="1024x1024",
#     # extra_body={
#     #     "num_inference_steps": 25,
#     #     "guidance_scale": 7.5,
#     # },
#     prompt="a white siamese cat",
# )
#
# to_file(response.data[0].b64_json, 'x.png')

# #
# r = client.chat.completions.create(
#     # model="DeepSeek-R1-Distill-Qwen-32B",
#     model="DeepSeek-V3",
#
#     messages=[
#         {"role": "user", "content": "鲁迅暴打周树人"*10000},
#     ],
#     stream=False,
#     temperature=0.1,
# )

# print(r)


