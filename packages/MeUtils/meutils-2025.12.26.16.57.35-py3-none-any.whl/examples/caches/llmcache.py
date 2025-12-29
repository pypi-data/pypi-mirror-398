#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : llmcache
# @Time         : 2024/12/16 11:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *


from gptcache import cache
from gptcache.adapter import openai

cache.init()
cache.set_openai_key()