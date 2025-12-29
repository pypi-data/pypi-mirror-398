#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chatbot
# @Time         : 2023/10/27 14:31
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://nicedouble-streamlitantdcomponentsdemo-app-middmy.streamlit.app/

import streamlit as st

from meutils.pipe import *
from meutils.serving.streamlit import st_chat_message, ChatMessage

################################################################################################
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from openai._streaming import Stream

base_url = os.getenv('OPENAI_BASE_URL')

api_key = 'sk-'
openai = OpenAI(api_key=api_key, base_url=base_url)


def ai_reply(image_url):
    messages = [
        {
            "role": "system",
            "content": """
            你是一名数学专家，非常擅长解决中小学的数学问题。。
            要求：
             1. Let's think step by step.
             2. 如果答案遇到公式请用标准的latex输出，公式用$包裹，例如：$\sqrt{{x^2+y^2}}=1$ 或者 $$\sqrt{{x^2+y^2}}=1$$
             3. 务必用中文回答
             """
        },
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "，请解题"},
                # {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "image_url", "image_url": {"url": image_url}},

            ],

        }
    ]

    response: Stream[ChatCompletionChunk] = openai.chat.completions.create(
        model='gpt-4-vision-preview',
        messages=messages,
        max_tokens=4096,
        temperature=0,
        stream=True
    )

    for chunk in response:
        _ = chunk.choices[0].delta.content
        if _ is not None:
            yield _


################################################################################################

def display_image(image):
    with st.columns(3)[1]:
        st.image(image)


if __name__ == '__main__':
    st.markdown('### 🔥解题小能手')

    file = st.file_uploader('上传题目图片', type=[".jpg", ".jpeg", '.png'])

    # 欢迎语
    st_chat_message(
        ChatMessage(generator='😘😘😘 嗨，我是你的解题小能手！\n\n **参考示例**：'),
        bhook=lambda: st.latex(r"\lim_{x\to0}\frac{e^x-e^{-x}-2x}{x-\sin x}")
    )

    if file:
        st_chat_message(
            ChatMessage(generator='输入的题目是', name='user'),
            bhook=lambda: display_image(file)
        )

        with st.spinner('AI 正在思考🤔'):
            image_url = f"data:image/jpeg;base64,{base64.b64encode(file.getvalue()).decode('utf-8')}"
            # st.markdown(image_url)

            output = ai_reply(image_url)
            st_chat_message(ChatMessage(generator=output))
