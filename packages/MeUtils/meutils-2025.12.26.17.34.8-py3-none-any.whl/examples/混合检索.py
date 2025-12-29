#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 混合检索
# @Time         : 2023/10/10 17:26
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://zhuanlan.zhihu.com/p/603116315


from meutils.pipe import *

# (1*s1 + α*s2)/(1+α)

s1 = {'a': 15.34, 'b': 10.14, 'c': 3.81}  # bm25
s2 = {'c': 0.9, 'd': 0.8, 'e': 0.6}  # cosine

df = pd.concat([pd.Series(s1).to_frame('s1'), pd.Series(s2).to_frame('s2')], axis=1)
df = df.fillna(df.min())
df.s1 = df.s1 / (df.s1 + 10)

df
α = 5
s = (df.s1 + α * df.s2) / (1 + α)
s.sort_values(ascending=False)
