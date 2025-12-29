#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat_dev
# @Time         : 2024/7/8 21:18
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from openai import OpenAI
from meutils.pipe import *

# base_url = "https://openai-dev.chatfire.cn/audio/v1"

# model = "FunAudioLLM/CosyVoice2-0.5B"
# voice = "FunAudioLLM/CosyVoice2-0.5B:alex"

text = """
融合 创新 专注 至简

“融合”：融入市场、融通资源、融合发展

“创新”：勇于突破、追求卓越、超越自我

“专注”：专一专业、忠诚敬业、重德守律、做到极致

“至简”：简约简朴、脚踏实地、知行合一
"""
r = OpenAI(
    # base_url="https://api.chatfire.cn/audio/v1",
    # base_url="http://0.0.0.0:8000/audio/v1",
    # base_url="https://openai.chatfire.cn/audio/v1",
    # api_key='xx'

    # api_key=os.getenv("OPENAI_API_KEY_OPENAI") + "-2738",

).audio.speech.create(
    # input=text*10,
    input=text,

    # model='tts-1',
    # model='tts-pro',
    model='test',

    voice="柔美女友",
    response_format="url",
    # response_format="mp3",
    extra_body={
        "emotion": "fear"
    }
)

# r.stream_to_file('xx.mp3')
