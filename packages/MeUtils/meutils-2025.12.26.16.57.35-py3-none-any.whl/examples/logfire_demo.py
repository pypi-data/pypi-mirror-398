#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : logfire_demo
# @Time         : 2025/5/13 09:39
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : /Users/betterme/.logfire/default.toml

from meutils.pipe import *


import logfire
from datetime import date

logfire.configure()
logfire.info('Hello, {name}!', name='world')

with logfire.span('Asking the user their {question}', question='age'):
    user_input = input('How old are you [YYYY-mm-dd]? ')
    dob = date.fromisoformat(user_input)
    logfire.debug('{dob=} {age=!r}', dob=dob, age=date.today() - dob)