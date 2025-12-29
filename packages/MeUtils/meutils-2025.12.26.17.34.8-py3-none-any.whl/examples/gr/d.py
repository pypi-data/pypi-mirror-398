#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : d
# @Time         : 2024/8/16 14:07
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from gradio_client import Client, handle_file

client = Client("https://s5k.cn/api/v1/studio/Kwai-Kolors/Kolors-Virtual-Try-On/gradio/",
                hf_token="a22224b9-b276-45b5-b8d1-10f3c81c8eec")
result = client.predict(
		person_img=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
		garment_img=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
		seed=0,
		randomize_seed=True,
		api_name="/tryon"
)
print(result)
