#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : kl
# @Time         : 2024/8/30 16:09
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
import requests

url = "https://api.chatfire.cn/v1/files"

payload={"purpose": 'kling'}
files=[

   ('file',('',open('lzp.jpg','rb'),'application/octet-stream'))
]
headers = {
   'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
   'Authorization': 'Bearer sk-94piBrPZi2DriPw23142114aFeDc4c73Bd350aA64fBd6d0d'
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
