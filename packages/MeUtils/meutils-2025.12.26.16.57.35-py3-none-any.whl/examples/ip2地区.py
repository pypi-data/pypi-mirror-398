#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : ip2地区
# @Time         : 2024/5/27 10:38
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from twoip import TwoIP

twoip = TwoIP(key=None)
twoip.provider(ip='192.0.2.0')
print(twoip.provider(ip='117.136.66.124'))
