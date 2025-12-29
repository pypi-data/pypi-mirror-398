#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : redis队列
# @Time         : 2023/6/9 15:39
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
# from MeUtils.examples.redis队列 import queue
from meutils.pipe import *
from rq import Queue
from redis import Redis

from MeUtils.examples.demo import fn, fn666
from meutils.db.redis_db import redis_client
from meutils.serving.rq import rq_fn

queue = Queue(name='default', connection=redis_client)

task = queue.enqueue(rq_fn, time.time())  # 通用函数
task = queue.enqueue(fn, time.time())  # 通用函数
task = queue.enqueue(fn666, time.time())  # 通用函数
queue.enqueue
print("queue key", queue.key)
print("queue.jobs", len(queue.jobs))

time.sleep(3)
v = task.return_value()
print(type(v), v)
