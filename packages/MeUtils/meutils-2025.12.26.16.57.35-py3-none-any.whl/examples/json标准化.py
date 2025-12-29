#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : json标准化
# @Time         : 2024/5/17 15:32
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : pip install json-repair

# https://github.com/josdejong/jsonrepair

from meutils.pipe import *
import json_repair






if __name__ == '__main__':
    data = '''
    data: {"type":"progress","value":0.08333333333333333,"code":200}
    data: {"type":"progress","value":0.16666666666666666,"code":200}
    data: {"type":"progress","value":0.25,"code":200}
    data: {"type":"progress","value":0.3333333333333333,"code":200}
    data: {"type":"progress","value":0.4166666666666667,"code":200}
    data: {"type":"progress","value":0.5,"code":200}
    data: {"type":"progress","value":0.5833333333333334,"code":200}
    data: {"type":"progress","value":0.6666666666666666,"code":200}
    data: {"type":"progress","value":0.75,"code":200}
    data: {"type":"progress","value":0.8333333333333334,"code":200}
    
    data: {"type":"removewatermark","id":"328b7ecd-87a1-11ef-9c4d-b21cc02dca41","imageUrl":"https://hunyuan-prod-1258344703.cos.ap-guangzhou.myqcloud.com/removewatermark/20a9f6cd03a660d155fe4b47ded00ecb/20241011151958h0_238f7aea93a3c626587aa14ec1fd422b.png?q-sign-algorithm=sha1\u0026q-ak=AKID0qSq0xJRL7h3A4nIYJFrFOJ1VlnbIm26\u0026q-sign-time=1728631198;1760167198\u0026q-key-time=1728631198;1760167198\u0026q-header-list=host\u0026q-url-param-list=\u0026q-signature=a85d02fb5ed97977b4b36023181fcee3a651bb84","source":"inspiration","code":200,"thumbnailUrl":"https://hunyuan-prod-1258344703.cos.ap-guangzhou.myqcloud.com/removewatermark/20a9f6cd03a660d155fe4b47ded00ecb/20241011151958h0_238f7aea93a3c626587aa14ec1fd422b.png?q-sign-algorithm=sha1\u0026q-ak=AKID0qSq0xJRL7h3A4nIYJFrFOJ1VlnbIm26\u0026q-sign-time=1728631198;1760167198\u0026q-key-time=1728631198;1760167198\u0026q-header-list=host\u0026q-url-param-list=\u0026q-signature=a85d02fb5ed97977b4b36023181fcee3a651bb84\u0026imageMogr2/strip/format/jpg/size-limit/500k!/ignore-error/1"}
    
    data: [TRACEID:9c49f848b20110761fb93bf3722ce0f2]
    
    data: [DONE]
    '''
    # print(json_repair.repair_json("""你们是{'a': 1, "b": 2, "c": 3}"""))
    # print(json_repair.repair_json(data, return_objects=True))

    # pattern = r'data: {"type":"removewatermark".*}'
    #
    # # 使用正则表达式查找匹配
    # match = re.findall(pattern, data)
    #
    # print(match)



    json_repair.repair_json(data.rsplit(""""code":200}""")[-1], return_objects=True)

    json_repair.repair_json(data, return_objects=True)