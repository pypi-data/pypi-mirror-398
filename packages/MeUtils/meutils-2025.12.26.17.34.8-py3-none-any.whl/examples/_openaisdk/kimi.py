#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : kimi
# @Time         : 2024/2/5 18:24
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI

api_key = os.getenv('MOONSHOT_API_KEY')
client = OpenAI(
    api_key=api_key,
    base_url="https://api.moonshot.cn/v1",
)

completion = client.chat.completions.create(
  model="moonshot-v1-8k",
  messages=[
    {"role": "user", "content": "总结下这篇文章的主要观点。"},
  ],
  # temperature=0.3, extra_body={"refs": ["cn0bmk198onv4v01aafg"]}
)
#
#
#
# print(completion.choices[0].message)
file_object = client.files.create(
    file=Path("/Users/betterme/PycharmProjects/AI/ChatLLM/examples/openaisdk/xx.pdf"),
    purpose="file-extract"
)
print(file_object)

# url = "https://ichat.chatfire.cn/uploads/20240313/1710300916647.pdf"
# url = "https://ichat.chatfire.cn/#/chat/1710309600703"
# r = requests.get(url)
# file_object = client.files.create(
#     file=r.content,
#     purpose="file-extract"
# )
print(file_object)
# print(client.files.retrieve(file_id=file_object.id))

print(client.files.retrieve_content(file_id=file_object.id))
# {"content":"品牌情况\n一、阿迪达斯三叶草（FDD）\n1、品牌位置：B 区 1F（102-105 铺）\n2、主要经营内容：福州市区最高级次三叶草门店，销售涵盖经典贝壳头鞋款，夏季透气清\n风，monkey kingdom 系列联名款，迪士尼联名系列潮流鞋服、配件等\n3、新品两件 8.8 折，夏季部分款式 6-8 折，更有联名款式和限量发售。\n二、NIKE 750\n1、品牌位置：苏宁广场 B 区一楼进门右转（近星巴克）\n2、主要经营内容：\n苏宁广场 NIKEBEACON750 店是福州 NIKE 全系列演绎体验旗舰店，涵括 Ain Jordan、\nBasketball、Running、Training，Sportswear、Football 等系列，完美演绎全品类产品。\n3、BEACON 寓意灯塔，是 NIKE 品牌的“旗舰店”等级！\nNIKE 全系列产品 热门爆款 发售款 当季最新款都会第一时间到店 目前春夏装两件 75 折\n起 品类基本涵盖全场 主要鞋款 8 折起 可使用滔博积分等 不定期有升值劵可享","file_type":"application/pdf","filename":"福州商场.pdf","title":"","type":"file"}

# for i in range(10):
#     file_object = client.files.create(file=file, purpose="file-extract")
#     filename = file_object.filename
#     #
#     print(file_object)  # cn0bmk198onv4v01aafg
#     break
#
# # print(client.files.retrieve(file_id="cn0bmk198onv4v01aafg"))
# try:
#     client.files.retrieve_content(file_id=file_object.id)  # 单文档，多路召回
# except Exception as e:
#     print(e)  # Error code: 500 - {'error': {'message': 'extract task failed: failed', 'type': ''}}

# openai.InternalServerError: Error code: 500 - {'error': {'message': 'extract task failed: failed', 'type': ''}}
# file_content = client.files.content(file_id=file_object.id).text
#
# file_content = client.files.retrieve_content(file_id=file_object.id)
# print(file_content)

# # 把它放进请求中
# messages=[
#     {
#         "role": "system",
#         "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
#     },
#     {
#         "role": "system",
#         "content": file_content,
#     },
#     {"role": "user", "content": "请简单介绍 xlnet.pdf 讲了啥"},
# ]
#
#
# file_list = client.files.list()
#
# print(file_list.data)
#
# for file in tqdm(file_list.data):
#     print(file)  # 查看每个文件的信息
#
#     print(client.files.delete(file_id=file.id))
# FileObject(id='cnhgqnucp7f5h7jfb3s0', bytes=505444, created_at=1709378911, filename='福州商场.pdf', object='file', purpose='file-extract', status='ok', status_details='')
