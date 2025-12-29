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
from rq import Queue
from redis import Redis

# from MeUtils.examples.demo import fn, fn666

from meutils.serving.rq import rq_fn

queue = Queue(connection=Redis())
queue_test = Queue(name='test', connection=Redis())



print("queue key", queue.key)
print("queue key", queue_test.key)


import time


print("queue.jobs", len(queue.jobs))

task = queue.enqueue(rq_fn, time.time())  # 通用函数
print(f"task key: {queue.key}")


time.sleep(3)
v = task.return_value()
print(type(v), v)
