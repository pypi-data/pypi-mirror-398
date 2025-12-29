#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : demo
# @Time         : 2023/8/24 13:22
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.notice.feishu import send_message

dic = {}


@background_task
def update_var():
    global dic

    from watchfiles import watch
    for changes in watch('./'):
        # {'modified': '/Users/betterme/PycharmProjects/AI/MeUtils/examples/watchdogssss/x.py'}
        dic = {k.name: v for k, v in changes}
        logger.debug(dic)
        send_message('Watchdog', str(dic))


if __name__ == '__main__':
    update_var()
    while 1:
        time.sleep(5)
        print(dic)
