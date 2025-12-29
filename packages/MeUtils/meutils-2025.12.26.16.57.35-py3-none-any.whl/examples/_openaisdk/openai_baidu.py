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


client = OpenAI(
    # api_key="bce-v3/ALTAK-jjasPcXYfdCD51QIO84GW/51b5e882be284463ab99ea8c03f20cce818c21eb",
    api_key="bce-v3/ALTAK-agwWy579fTIawmcCfD0j6/3964bf0b39ac01bb6045c02670e3e0723acee85c;ZjkyZmQ2YmQxZTQ3NDcyNjk0ZTg1ZjYyYjlkZjNjODB8AAAAABMCAAASj16tiXir0pctis9aaYY7OkInbGYHyI2AJqNe9knwoNulTnF6LJ4jE+t1sE0N5HkGG9Dq0Lg8UclYz16mdTm/jTld58Vjv11EKELz9EFb9yIPOIVt7gH3s7TGdvYLllTMoBFpy+TIsUiGZsxMiROVMGGY0xjrCnzd8UU6x7bxOSdih+FnhOB4TEr3HIC4lj6eKo6gRh2DLxPhFIBFf1FTsheXBAl/BVsUcO/Ec6jkmZAx1OyHsD5MJWB3IrcbJrFJavlqh2OjMhF1nxie7LVcmKWElrht230QZWZTSzR8ACLlyfATqMUu82Y3tT2RqTMLqdyNJgjIxJ2uK4tuXy5o0gEhdee3YyD1IZru4nbKOQL8KpanH7s6i+8YumaMeY/vjfxGZPNQ7X43Wr9+jfStdqD/NHouJZ9puZVqenSlT2pUC5GFrVWBiEuV9iZ+zV4=",
    base_url="https://qianfan.baidubce.com/v2",
    # default_headers={"appid": "app-MuYR79q6"}

)



try:
    completion = client.chat.completions.create(
        model="DeepSeek-V3",
        # model = "ernie-3.5-8k",
        # model="xxxxxxxxxxxxx",
        messages=[
            {"role": "system", "content": '你是个内容审核助手'},

            {"role": "user", "content": "你是谁"}
        ],
        # top_p=0.7,
        top_p=None,
        temperature=None,
        stream=True,
        max_tokens=1000
    )
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    # print(bjson(chunk))
    print(chunk.choices[0].delta.content, flush=True)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )

