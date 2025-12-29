#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : zhipu_files
# @Time         : 2024/6/3 16:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *


from openai import OpenAI, AsyncOpenAI


client = OpenAI(
    base_url=os.getenv('ZHIPU_BASE_URL'),
    api_key=os.getenv('ZHIPU_API_KEY'),
)

print(client.files.list())


file_object = client.files.create(
    # file=Path("batchs-glm-4.jsonl"),
    # purpose="file-extract",

    file=Path("xx.pdf"),
    purpose="fine-tune",
)
input_file_id = file_object.id

input_file_id = "1717404627_7f72d886abb845019c856533c521abf7"
create = client.batches.create(
    input_file_id=input_file_id,
    endpoint="/v4/chat/completions",
    completion_window="24h", #完成时间只支持 24 小时
    metadata={
        "description": "Sentiment classification"
    }
)
batch_id = create.id

batch_id = "batch_1797552096863199232"
batch_job = client.batches.retrieve("batch_id")
print(batch_job)
