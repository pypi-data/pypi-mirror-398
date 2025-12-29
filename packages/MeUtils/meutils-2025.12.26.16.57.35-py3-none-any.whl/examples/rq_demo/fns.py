#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : fns
# @Time         : 2024/6/20 15:54
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *

from meutils.notice.feishu import send_message


def send(*args):
    logger.debug(args)
    return send_message(args)
