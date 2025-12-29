#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : redis队列
# @Time         : 2023/6/9 15:39
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import time

from meutils.pipe import *
from meutils.db.redis_db import redis_client
from meutils.notice.feishu import send_message

from rq import Queue

queue = Queue(connection=redis_client)
# queue = Queue(name='test', connection=redis_client)

# send_message('xxx')
task = queue.enqueue(
    send_message,
    content="xxx",
)  # 通用函数


task = queue.enqueue(
    print,
    "xxx",
)  # 通用函数