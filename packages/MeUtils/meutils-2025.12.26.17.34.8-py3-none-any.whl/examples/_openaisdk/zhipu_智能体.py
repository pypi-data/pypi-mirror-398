#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : zhipu_智能体
# @Time         : 2024/12/30 17:34
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://bigmodel.cn/dev/api/intelligent-agent-model/assistantapi

from meutils.pipe import *
from meutils.llm.clients import zhipuai_sdk_client
from meutils.schemas.openai_types import chat_completion_chunk

from zhipuai import ZhipuAI

# api_key = "YOUR API KEY"
# url = "https://open.bigmodel.cn/api/paas/v4"
# client = ZhipuAI(
#     api_key="e21bd630f681c4d90b390cd609720483.WSFVgA3KkwNCX0mN",
#     base_url="https://open.bigmodel.cn/api/paas/v4/"
# )


#
#
# # print(bjson(client.assistant.query_support()))
generate = zhipuai_sdk_client.assistant.conversation(
    assistant_id="65940acff94777010aa6b796",
    # assistant_id="65a265419d72d299a9230616",
    # assistant_id="659d051a5f14eb8ce1235b96",
    # assistant_id="65d2f07bb2c10188f885bd89",

    # assistant_id="659e54b1b8006379b4b2abd6",
    # conversation_id=None,  # 多轮：从messages获取
    # conversation_id="67dd1317d7c8fe4c9efe459a",
    model="glm-4-assistant",
    messages=[
        {
            "role": "user",
            "content": [{
                "type": "text",
                # "text": "北京未来七天气温，做个折线图",
                "text": "南京天气",
                # "text": "周杰伦 【最新动态、相关信息或新闻】",

                # "text": "画条狗"
                # "text": "周杰伦",
                # "text": "PPT主题：二战各国战地将领传奇",
                # "text": "生成PPT"

            }]
        }
    ],
    stream=True,
    attachments=None,
    metadata=None
)

for resp in generate:
    delta = resp.choices[0].delta
    if hasattr(delta, "tool_calls") and delta.tool_calls:
        # print(delta)

        # print(delta.model_dump_json(indent=4, exclude_none=True))
        # logger.debug(delta)
        print(delta.model_dump_json(indent=4, exclude_none=True))
    elif hasattr(delta, "content"):
        print(delta.content, end="")

    else:
        logger.debug(delta)
    # print(resp.model_dump_json(indent=4, exclude_none=True))
    # for tc in delta.tool_calls:
    #     tc.web_browser

    # print(resp.choices[0])

    # if hasattr(delta, "content"):
    #     print(delta.content)

    # 输入 输出
    # input
# {
#     "assistant_id": "65d2f07bb2c10188f885bd89",
#     "conversation_id": "67d932d5e579c3ded42aa80e",
#     "meta_data": {
#         "if_plus_model": false,
#         "is_test": false,
#         "input_question_type": "xxxx",
#         "channel": "",
#         "draft_id": "",
#         "quote_log_id": "",
#         "platform": "pc"
#     },
#     "messages": [
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "基于这个内容做个ppt"
#                 },
#                 {
#                     "type": "file",
#                     "file": [
#                         {
#                             "file_id": "chatglm4/3db10f79-a952-4987-83d2-cf0cfd5d5530.pdf",
#                             "file_url": "https://sfile.chatglm.cn/chatglm4/3db10f79-a952-4987-83d2-cf0cfd5d5530.pdf",
#                             "file_name": "附件.大模型在合规管理工作中的应用.pdf",
#                             "file_size": 2571523,
#                             "order": 0,
#                             "maxReadPercent": 0,
#                             "cover_images": [],
#                             "url": "https://sfile.chatglm.cn/chatglm4/3db10f79-a952-4987-83d2-cf0cfd5d5530.pdf"
#                         }
#                     ]
#                 }
#             ]
#         }
#     ]
# }