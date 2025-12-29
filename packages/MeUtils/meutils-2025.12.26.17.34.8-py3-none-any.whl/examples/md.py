#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : md
# @Time         : 2024/11/25 15:33
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://readpo.com/en/poster#%201

from meutils.pipe import *
from urllib.parse import quote


@background_task
def get(url):
    resp = httpx.get(url, timeout=30)
    # Path('x.png').write_bytes(resp.content)
    # logger.debug(resp.text)
    logger.debug(resp.status_code)


def markdown2poster(title="MarkdownTest", content="# fire"):
    # content = f"""https://readpo.com/p/{quote(content)}"""

    content = f"""https://md.chatfire.cn/{quote(content)}"""
    get(content)

    return f"![{title}]({content})"
