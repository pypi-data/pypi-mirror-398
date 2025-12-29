#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 文档解析
# @Time         : 2024/11/18 10:47
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *


from pathlib import Path
from openai import OpenAI, files
import os

# os.environ["OPENAI_API_KEY"] = "sk-xx"
client = OpenAI(
    api_key="你的sk", # 获取地址 https://api.chatfire.cn/token
    base_url="https://api.chatfire.cn/v1",
)

file_id = files.create(
  file=Path("/Users/betterme/PycharmProjects/AI/MeUtils/examples/_openaisdk/xx.pdf"),
  purpose="moonshot-fileparser" # textin-fileparser
)
print(file_id)


# file_id = file_id.id
# file_content = client.files.content(file_id=file_id).text
#
# print(file_content)