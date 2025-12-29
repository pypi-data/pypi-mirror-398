#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : gr_vl
# @Time         : 2024/6/3 20:33
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://huggingface.co/spaces/Dzkaka/ChatTTS

from meutils.pipe import *
from gradio_client import Client, file

# client = Client("Dzkaka/ChatTTS", hf_token="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")
#
#
# result = client.predict(
#     text="四川美食确实以辣闻名，但也有不辣的选择。比如甜水面、赖汤圆、蛋烘糕、叶儿粑等，这些小吃口味温和，甜而不腻，也很受欢迎。",
#     temperature=0.3,
#     top_P=0.7,
#     top_K=20,
#     audio_seed_input=42,
#     text_seed_input=42,
#     refine_text_flag=True,
#     api_name="/generate_audio"
# )
# print(result)


from gradio_client import Client

client = Client("https://playgroundai-playground-v2-5.hf.space/--replicas/yd7l4/",
                hf_token="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")

result = client.predict(
    "Hello!!",  # str  in 'Prompt' Textbox component
    "Hello!!",  # str  in 'Negative prompt' Textbox component
    True,  # bool  in 'Use negative prompt' Checkbox component
    0,  # float (numeric value between 0 and 2147483647) in 'Seed' Slider component
    256,  # float (numeric value between 256 and 1536) in 'Width' Slider component
    256,  # float (numeric value between 256 and 1536) in 'Height' Slider component
    0.1,  # float (numeric value between 0.1 and 20) in 'Guidance Scale' Slider component
    True,  # bool  in 'Randomize seed' Checkbox component
    api_name="/run"
)
print(result)
