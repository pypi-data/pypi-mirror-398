#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2024/1/23 18:33
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.decorators.retry import retrying

for i in range(1, 101):
    cmd = f"wget https://progress-bar.dev/{i} -O ./progress_bar/{i}.svg"
    os.system(cmd)
    # break
