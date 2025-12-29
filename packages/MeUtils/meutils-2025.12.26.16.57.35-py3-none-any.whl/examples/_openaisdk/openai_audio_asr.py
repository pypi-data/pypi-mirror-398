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
    base_url="https://ai.gitee.com/v1",

    api_key="5PJFN89RSDN8CCR7CRGMKAOWTPTZO6PN4XVZV2FQ"

).audio.transcriptions.create(
    # file=open("./audio.mp3", "rb"),
    file=open("./xx.mp3", "rb"),
    model="whisper-large-v3-turbo",
    # response_format='srt'
)

# r.stream_to_file('xx.mp3')
