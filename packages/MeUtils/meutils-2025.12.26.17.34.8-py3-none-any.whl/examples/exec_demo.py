#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : MeUtils.
# @File         : exec_demo
# @Time         : 2021/2/5 5:31 下午
# @Author       : yuanjie
# @WeChat       : 313303303
# @Software     : PyCharm
# @Description  : 


s = """
def f(x):
    return x
print(f(x))
"""

ss = """lambda x: x+1"""

exec(s, {'x': 1111})


# curl -X POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer $ARK_API_KEY" \
#   -d '{
#     "model": "doubao-seedance-1-0-pro-250528",
#     "content": [
#         {
#             "type": "text",
#             "text": "多个镜头。一名侦探进入一间光线昏暗的房间。他检查桌上的线索，手里拿起桌上的某个物品。镜头转向他正在思索。 --ratio 16:9"
#         }
#     ]
# }'

import typer
import shlex  # 用于将命令字符串拆分为参数列表


command = """
无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验  --resolution 1080p  --duration 5 --camerafixed false
"""
tokens = shlex.split(command)
