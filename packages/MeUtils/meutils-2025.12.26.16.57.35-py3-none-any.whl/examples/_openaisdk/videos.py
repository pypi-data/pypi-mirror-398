#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/12/21 21:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.io.files_utils import to_base64
from meutils.llm.clients import OpenAI

"""
prompt: str,
input_reference: FileTypes | Omit = omit,
model: VideoModel | Omit = omit,
seconds: VideoSeconds | Omit = omit,
size: VideoSize | Omit = omit,
# Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
# The extra values given here take precedence over values defined on the client or passed to this method.
extra_headers: Headers | None = None,
extra_query: Query | None = None,
extra_body: Body | None = None,
timeout: float | httpx.Timeout | None | NotGiven = not_given,
"""
model = "doubao-seedance-1-0-pro_480p"
image = arun(to_base64("https://s3.ffire.cc/files/jimeng.jpg", content_type="image/jpeg"))

extra_headers = {
    "Content-Type": "multipart/form-data",
    # **(extra_headers or {})
}
extra_body = {
    "first_frame_image": image,
}
r = OpenAI(
    base_url="https://test.chatfire.cc/videos/v1",
api_key=None,
    # api_key="sk-0tyxTuSf23wyTMPXsrfUKftAOtMYRtjDDJgASVE4QY6hrnU22"
).videos.create(
    model=model,
    prompt="比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。",
    seconds="5",

    extra_headers=extra_headers,
    extra_body=extra_body,
)

logger.debug(r)
