#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : mj
# @Time         : 2025/5/8 16:57
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.io.files_utils import to_base64

1746694459127528

url = "https://api.chatfire.cn/mj/submit/modal"


image = "https://cdn.gptbest.vip/mj/attachments/1285976818721226842/1369960682639986849/hunter6_palmer26386_aute_laborum_fugiat_Ut_ipsum_2ff0eb18-dcb9-4ee3-9cba-4bc2f0f3926c.png?ex=681dc2cf&is=681c714f&hm=24be632ccb365c7daff5453876a63be6aef28ceb4d07da244250a0846b929983&"

b64 = arun(to_base64(image))


httpx.post(url, json={
  "maskBase64": b64,
  "prompt": "",
  "taskId": "14001934816969359"
})