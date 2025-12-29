#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : main
# @Time         : 2024/12/9 16:53
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import pandas as pd

from meutils.pipe import *
from openai import OpenAI

openai = OpenAI()

df = pd.read_json('tbInfo2.txt', lines=True)
texts = df["表字段信息"].map(lambda d: d.values() | xjoin('\n'))

# 表字段信息

@diskcache
def create_embeddings(text):
    return openai.embeddings.create(input=text, model="BAAI/bge-m3").data[0].embedding


if __name__ == '__main__':
    pass

    # for text in tqdm(df['表字段信息']):
    #     r = create_embeddings(str(text))
