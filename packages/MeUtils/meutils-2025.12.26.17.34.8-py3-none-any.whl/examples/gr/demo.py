#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2024/8/7 09:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import gradio as gr

from gradio_client import Client, file

# client = Client("http://120.92.209.146:8887")
# print(client.view_api(all_endpoints=True))

# print(client.view_api())

#
# decode_type='sampling'
# parameter_13 = {
#     'files': '/Users/betterme/PycharmProjects/AI/QR.png',
#     'text': '解释下',
#     'index': 0
# }
#
# client.predict(parameter_13, api_name="/respond")
# print(client.predict("parameter_14", api_name="/select_chat_type"))

from gradio_client import Client, handle_file

client = Client("khang119966/DeepSeek-OCR-DEMO")
# client = Client("axiilay/DeepSeek-OCR-Demo")
result = client.predict(
		image=handle_file('https://s3.ffire.cc/files/pdf_to_markdown.jpg'),
		model_size="Gundam (Recommended)",
		task_type="📄 Convert to Markdown",
		ref_text="Hello!!",
		api_name="/process_ocr_task"
)
print(result)