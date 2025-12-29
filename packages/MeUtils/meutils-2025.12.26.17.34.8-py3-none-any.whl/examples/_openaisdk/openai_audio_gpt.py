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
from meutils.schemas.openai_types import ChatCompletionRequest
from meutils.llm.openai_utils import to_openai_completion_params
from meutils.io.files_utils import to_base64

# base64_audio = arun(to_base64("https://oss.ffire.cc/files/lipsync.mp3"))
# base64_image = arun(to_base64("https://oss.ffire.cc/cdn/2025-04-01/duTeRmdE4G4TSdLizkLx2B", content_type="image/jpg"))

client = OpenAI(

)

import base64
import requests
from openai import OpenAI

# Fetch the audio file and convert it to a base64 encoded string
url = "https://cdn.openai.com/API/docs/audio/alloy.wav"
response = requests.get(url)
response.raise_for_status()
wav_data = response.content
encoded_string = base64.b64encode(wav_data).decode('utf-8')

completion = client.chat.completions.create(
    model="gemini-2.0-flash-audio",
    # stream=True,
    modalities=["text", "audio"],  # todo gemini规避掉
    # audio={"voice": "alloy", "format": "wav"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this recording?"
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": encoded_string,
                        "format": "wav"
                    }
                }
            ]
        },
    ]
)

print(completion.choices[0].message)

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
