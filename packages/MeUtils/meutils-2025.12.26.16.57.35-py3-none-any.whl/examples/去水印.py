#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 去水印
# @Time         : 2024/3/22 09:10
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://www.jb51.net/article/278222.htm

from meutils.pipe import *
import poimage

# 支持jpg、png等所有图片格式
poimage.del_watermark(
    input_image="img.png",
    output_image='img_.png')


# https://h1.inkwai.com/bs2/upload-ylab-stunt/special-effect/output/HB1_PROD_ai_web_28605986/5266660862308034344/temp.png