#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 兜底测试
# @Time         : 2024/1/9 15:14
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

base_url = "https://api.chatllm.vip/v1"
api_key = "sk-eEFIr6SEuegUOh1S0c8910A652A9428fAd4aD452C97631Acc"

# base_url = "http://0.0.0.0:39999/v1"
client = OpenAI(base_url=base_url, api_key=api_key)

# 触发风控
s = """
Question:已知节点类型只有六种：原因分析、排故方法、故障时间、故障现象、故障装备单位、训练地点，现在我给你一个问题，你需要根据这个句子来推理出这个问题的答案在哪个节点类型中，问题是”管道细长、阻力太大时的轴向柱塞泵故障如何解决？“,输出格式形为：["节点类型1"], ["节点类型2"], …。除了这个列表以外请不要输出别的多余的话。
['排故方法']

Question:已知节点类型只有六种：原因分析、排故方法、故障时间、故障现象、故障装备单位、训练地点，现在我给你一个问题，你需要根据这个句子来推理出这个问题的答案在哪个节点类型中，问题是”转向缸出现爬行现象，但是压力表却忽高忽低，相对应的解决方案是？“输出格式形为：["节点类型1"], ["节点类型2"], …。除了这个列表以外请不要输出别的多余的话。
['原因分析']、['排故方法']

Question:已知节点类型只有六种：原因分析、排故方法、故障时间、故障现象、故障装备单位、训练地点，现在我给你一个问题，你需要根据这个句子来推理出这个问题的答案在哪个节点类型中，问题是”在模拟训练场A，轴向柱塞马达出现过什么故障？“输出格式形为：["节点类型1"], ["节点类型2"], …。除了这个列表以外请不要输出别的多余的话。

['故障现象']

已知节点类型只有六种：原因分析、排故方法、故障时间、故障现象、故障装备单位、训练地点，现在我给你一个问题，你需要根据这个句子来推理出这个问题的答案在哪个节点类型中，问题是”密封圈挤出间隙的解决方法是什么？“。输出格式形为：["节点类型1"], ["节点类型2"], …。除了这个列表以外请不要输出别的多余的话。
"""

# s = "讲个故事"
# s = '树上9只鸟，打掉1只，还剩几只'

data = {
    'model': 'gpt-3.5-turbo-1106',
    'messages': [
        {'role': 'system', 'content': "你是gpt4, Let's think things through one step at a time."},
        {'role': 'user', 'content': s}
    ],
    'stream': False}

_ = client.chat.completions.create(**data)
print(_)
for i in _:
    print(i)
    # print(i.choices[0].delta.content, end='')
