#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : main
# @Time         : 2024/7/18 11:31
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://google.github.io/mesop/demo/

from meutils.pipe import *
import time

import mesop as me
import mesop.labs as mel
me.stateclass

@me.page()
def app():
    me.text("Hello World")


@me.page(path="/text_to_text", title="Text I/O Example")
def app():
    mel.text_to_text(
        upper_case_stream,
        title="Text I/O Example",
    )


def upper_case_stream(s: str):
    yield s.capitalize()
    time.sleep(0.5)
    yield "Done"
