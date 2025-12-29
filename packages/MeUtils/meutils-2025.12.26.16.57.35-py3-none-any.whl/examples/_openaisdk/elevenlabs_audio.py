#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : elevenlabs_audio
# @Time         : 2025/7/4 08:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from elevenlabs.client import ElevenLabs

elevenlabs = ElevenLabs(
  api_key='sk_fdd289ca9705e3062af59cb275c5fdd131593a6eece96e4e',
)

print(elevenlabs.user.get())