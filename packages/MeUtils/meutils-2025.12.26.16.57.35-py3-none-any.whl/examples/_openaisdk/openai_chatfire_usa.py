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


client = OpenAI(
    api_key="sk-5pMaS37pVZXH9s2dMwRK984QiwIRh9qQbQGnkv5fAFNaxMK6-16207",
    base_url="https://usa.chatfire.cn"
)



r = client.images.generate(
    model="cogview-3-plus",
    prompt="a white siamese cat",
    size="1024x1024",
    extra_body={
        ""
    },
    n=1,
)
