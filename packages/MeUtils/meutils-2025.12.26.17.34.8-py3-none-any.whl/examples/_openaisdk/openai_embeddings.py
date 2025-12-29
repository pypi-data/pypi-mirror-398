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
from openai.types.create_embedding_response import CreateEmbeddingResponse

client = OpenAI(

    # api_key=os.getenv("OPENAI_API_KEY_OPENAI"),
    # api_key=os.getenv("SILICONFLOW_API_KEY"),
    # api_key="sk-gcxjtocodgggxwnhqqsaqznpkpxndktwlgmgkmzljyajjsfp",
    # base_url="https://api.siliconflow.cn/v1",

    # base_url="https://api.bltcy.ai/v1"
)

model = "BAAI/bge-large-zh-v1.5"
model = "bge-large-zh-v1.5"
model = "text-embedding-ada-002"
# model = "text-embedding-ada-002"
#
model = "BAAI/bge-m3"
# model = "bge-m3"
# with timer("bs1"):
#     response = client.embeddings.create(
#         input=["查" * 1000] * 1,
#         model=model
#     )


with timer("bs1"):
    response = client.embeddings.create(
        input="xx",
        model=model,
        # encoding_format=None
    )



# from langchain_openai import OpenAIEmbeddings
#
# OpenAIEmbeddings()
#
# model_kwargs = {"encoding_format": "float"}

