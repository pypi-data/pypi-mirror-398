#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : size_map
# @Time         : 2024/12/13 15:03
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *


def find_nearest_standard_size(width, height, standard_sizes):
    """
    找到最接近的标准尺寸
    standard_sizes: 标准尺寸列表，如 [(256,256), (512,512), ...]
    """
    min_diff = float('inf')
    nearest_size = None

    for std_width, std_height in standard_sizes:
        diff = abs(width - std_width) + abs(height - std_height)
        if diff < min_diff:
            min_diff = diff
            nearest_size = (std_width, std_height)

    return nearest_size


# 标准尺寸列表
standard_sizes = [
    (256, 256),
    (512, 512),
    (1024, 1024),
    (1792, 1024),
    (1024, 1792)
]

# 使用示例
width, height = 600, 600
nearest = find_nearest_standard_size(width, height, standard_sizes)
print(f"最接近 {width}x{height} 的标准尺寸是: {nearest}")
