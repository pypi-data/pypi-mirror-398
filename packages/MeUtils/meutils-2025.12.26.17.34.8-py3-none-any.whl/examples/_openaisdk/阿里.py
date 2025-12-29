#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 阿里
# @Time         : 2024/5/24 10:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from http import HTTPStatus
from dashscope import Application, Generation


def call_agent_app():
    response = Application.call(
        app_id='3e27fc43adf5410c919cc4aaae03c88d',
        prompt='如何做炒西红柿鸡蛋？',
        api_key='sk-4e6489ba597541dfa7a51f43e3912ca2',
        stream=False,
    )

    if response.status_code != HTTPStatus.OK:
        print('request_id=%s, code=%s, message=%s\n' % (response.request_id, response.status_code, response.message))
    else:
        print('request_id=%s\n output=%s\n usage=%s\n' % (response.request_id, response.output, response.usage))


#
# if __name__ == '__main__':
#     call_agent_app()
api_key = 'sk-4e6489ba597541dfa7a51f43e3912ca2'

# response = Generation.call(
#     model='farui-plus',
#     messages=[{'role': 'user', 'content': 'hi'}],
#     api_key=api_key,
#     stream=False,
#     # incremental_output=False,
#     # enable_search=True
# )
# print(response)
# for i in response:
#     print(i)

# 业务空间模型调用请参考文档传入workspace信息: https://help.aliyun.com/document_detail/2746874.html

from dashscope import MultiModalConversation

from meutils.io.image import image_to_base64


def simple_multimodal_conversation_call():
    """Simple single round multimodal conversation call.
    """
    messages = [

        {
            "role": "user",
            "content": [
                {"image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"},

                {"text": "这是什么?"}
            ]
        }
    ]
    messages = [{'role': 'user', 'content': [{'text': '解释下'}, {'image': 'https://oss.chatfire.cn/app/qun.png'}]}]
    responses = MultiModalConversation.call(
        model='qwen-vl-max',
        messages=messages,
        stream=True,
        api_key=api_key
    )
    for response in responses:
        print(response)


if __name__ == '__main__':
    simple_multimodal_conversation_call()
