#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : 模型测试
# @Time         : 2024/2/8 08:50
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from openai import OpenAI
from chatllm.schemas.openai_api_protocol import ChatCompletionRequest, ChatCompletionResponse

client = OpenAI()
client.base_url = 'http://154.3.0.117:39010/v1'
client.api_key = 'ghu_H1Fg9SLKgaiUgS2NGFf2JyWue0VJER498Rt5'

data = {'messages': [{'role': 'system',
                      'content': '现在我会给你一段文本，以上内容是这段文本的前后文,请你接下来充当分镜编剧,这是分镜的相关说明：\n 运动:运动摄影，亦称“运动拍摄”。摄影机在推、拉、摇、移、跟、升、降、旋转和晃动等不同形式的运动中进行拍摄。运动摄影是电影区别于其他造型艺术的独特表现手段，是电影语言的独特表达方式，也是电影作为艺术的重要标志之一。\n 画面:用简明、清晰的语言描述电影画面的具体内容。表现画面内容。\n 台词:此镜头内人物的台词，即人物说的话语。\n 声音:此镜头内的重要声音，包括人声、音乐、音响等。"将这段文本总结为对于一个分镜的描述，请注意只能输出一个你认为最符合的分镜的相关描述。并且不超过70字！并且，你需要在你给出的分镜场景前，加上你认为可能出现在这个分镜场景中的人物,不允许添加任何你的想象！\n 以下为输出格式”\n 人物：{可能出现在这个分镜场景中的人物}；\n 景别：{}；\n 运动：{}；\n 画面：{用一句话描述画面，内容要简练，不要出现对话}；'},
                     {'role': 'assistant',
                      'content': '抱歉，文本长度超过了要求的字数上限。我需要把你的文本长度减少到70个字以内。'},
                     {'role': 'user',
                      'content': '我爹扶额：大意了，可不是大意吗，他在庆功宴上只说与自家小女与顾家公子青梅竹马，一没说是哪个女儿，二没说是哪个顾家的公子'},
                     {'role': 'assistant',
                      'content': '人物：庶妹、庶妹父亲；\n景别：宫殿；\n运动：无；\n画面：庶妹父亲扶额叹息，解释庆功宴上的误会，庶妹眼含泪光，心中犹豫不决。'},
                     {'role': 'user',
                      'content': '七日前，我爹凯旋归京，皇帝大喜，赐宴庆祝，按照我们景朝的旧例，庆功宴上陛下会让重功之臣提一个要求'},
                     {'role': 'assistant',
                      'content': '人物：庶妹、庶妹父亲、皇帝；\n景别：宫殿；\n运动：无；\n画面：庶妹父亲向庶妹解释庆功宴上的情况，庶妹眼中闪过一丝明悟，她明白了皇帝赐宴时的规矩。'},
                     {'role': 'user',
                      'content': '我爹一到家，沈嘉柔就嚷嚷着要嫁给顾砚行，要我爹去请旨，庆功宴那天，我爹对外宣称我染病在家，只带了沈嘉柔一个女儿去赴宴'}],
        'model': 'gpt-3.5-turbo', 'frequency_penalty': 0.0, 'function_call': None, 'max_tokens': None, 'n': 1,
        'presence_penalty': 0.0, 'response_format': None, 'stop': None, 'stream': False, 'temperature': 0.6,
        'top_p': 1.0,
        'user': None}
for _ in range(100):
    with timer(_):
        _ = client.chat.completions.create(**data)

        # _ = client.chat.completions.create(
        #     **dict(
        #         model="gpt-4",
        #         stream=True,
        #         temperature=1,
        #         messages=[{'role': 'user',
        #                    'content': '讲个故事几千字的故事，你可以随便编写，越长越好，这对我真重要，我将按照文章长度给你1000美元小费'}])
        #
        # )
        print(_)
        # for i in _:
        #     print(i.choices[0].delta.content, end='')
        break
