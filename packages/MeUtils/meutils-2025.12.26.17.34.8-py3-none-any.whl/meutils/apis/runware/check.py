#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : check
# @Time         : 2025/11/12 14:02
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from openai import Client

payload = [
  {
    "taskType": "accountManagement",
    "taskUUID": str(uuid.uuid4()),
    "operation": "getDetails"
  }
]


api_key="P8nkXmMKfoPlSR3iR48Jbl4vs8aLP1TT"

client = Client(base_url="https://api.runware.ai/v1", api_key=api_key, timeout=300)
response = client.post(
    "/",
    body=payload,
    cast_to=object
)

response['data'][0]['balance']