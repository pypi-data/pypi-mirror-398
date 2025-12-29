#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
"""
Qwen/Qwen2.5-Coder-32B-InstructQwen/Qwen2.5-Coder-14B-InstructQwen/Qwen2.5-Coder-7B-InstructQwen/Qwen2.5-72B-InstructQwen/Qwen2.5-32B-InstructQwen/Qwen2.5-14B-InstructQwen/Qwen2.5-7B-Instruct

Qwen/QVQ-72B-Preview
"""
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

client = OpenAI(
    # api_key=os.getenv("STEP_API_KEY"),
    # base_url="https://api.stepfun.com/v1",
    base_url=os.getenv("MODELSCOPE_BASE_URL"),
    # api_key=os.getenv("MODELSCOPE_API_KEY"),
    api_key="81ccebd2-1933-4996-8c65-8e170d4f4264"
)

# print(client.models.list().model_dump_json(indent=4))

models = client.models.list().data

print(','.join([m.id for m in models]))

qwen = {m.id.removeprefix("Qwen/").lower(): m.id for m in models if m.id.startswith('Qwen')}

print(','.join(qwen))
print(bjson(qwen))

"""
LLM-Research/c4ai-command-r-plus-08-2024, mistralai/Mistral-Small-Instruct-2409, mistralai/Ministral-8B-Instruct-2410, mistralai/Mistral-Large-Instruct-2407, Qwen/Qwen2.5-Coder-32B-Instruct, Qwen/Qwen2.5-Coder-14B-Instruct, Qwen/Qwen2.5-Coder-7B-Instruct, Qwen/Qwen2.5-72B-Instruct, Qwen/Qwen2.5-32B-Instruct, Qwen/Qwen2.5-14B-Instruct, Qwen/Qwen2.5-7B-Instruct, Qwen/QwQ-32B-Preview, LLM-Research/Llama-3.3-70B-Instruct, opencompass/CompassJudger-1-32B-Instruct, Qwen/QVQ-72B-Preview, LLM-Research/Meta-Llama-3.1-405B-Instruct, LLM-Research/Meta-Llama-3.1-8B-Instruct, Qwen/Qwen2-VL-7B-Instruct, LLM-Research/Meta-Llama-3.1-70B-Instruct, Qwen/Qwen2.5-14B-Instruct-1M, Qwen/Qwen2.5-7B-Instruct-1M, Qwen/Qwen2.5-VL-3B-Instruct, Qwen/Qwen2.5-VL-7B-Instruct, Qwen/Qwen2.5-VL-72B-Instruct, deepseek-ai/DeepSeek-R1-Distill-Llama-70B, deepseek-ai/DeepSeek-R1-Distill-Llama-8B, deepseek-ai/DeepSeek-R1-Distill-Qwen-32B, deepseek-ai/DeepSeek-R1-Distill-Qwen-14B, deepseek-ai/DeepSeek-R1-Distill-Qwen-7B, deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B, deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-V3, Qwen/QwQ-32B, XGenerationLab/XiYanSQL-QwenCoder-32B-2412, Qwen/Qwen2.5-VL-32B-Instruct, deepseek-ai/DeepSeek-V3-0324, Wan-AI/Wan2.1-T2V-1.3B, LLM-Research/Llama-4-Scout-17B-16E-Instruct, LLM-Research/Llama-4-Maverick-17B-128E-Instruct, Qwen/Qwen3-0.6B, Qwen/Qwen3-1.7B, Qwen/Qwen3-4B, Qwen/Qwen3-8B, Qwen/Qwen3-14B, Qwen/Qwen3-30B-A3B, Qwen/Qwen3-32B, Qwen/Qwen3-235B-A22B, XGenerationLab/XiYanSQL-QwenCoder-32B-2504, deepseek-ai/DeepSeek-R1-0528

"""


# client.images.generate(
#     model="DiffSynth-Studio/FLUX.1-Kontext-dev-lora-SuperOutpainting",
#     prompt='a dog'
# )

def main():
    try:
        completion = client.chat.completions.create(
            # model="step-1-8k",
            # model="deepseek-ai/DeepSeek-R1-0528",
            # model="deepseek-ai/DeepSeek-R1-0528",
            model="ZhipuAI/GLM-4.5",

            # model="Qwen/QVQ-72B-Preview",
            # model="qwen/qvq-72b-preview",

            messages=[
                {"role": "user", "content": "你是谁"}
            ],
            # top_p=0.7,
            top_p=None,
            temperature=None,
            stream=True,
            max_tokens=100
        )
    except APIStatusError as e:
        print(e.status_code)

        print(e.response)
        print(e.message)
        print(e.code)

    for chunk in completion:
        content = chunk.choices[0].delta.content
        reasoning_content = chunk.choices[0].delta.reasoning_content
        print(content or reasoning_content)
    print(chunk)


if __name__ == '__main__':
    for i in tqdm(range(1)):
        # break
        main()
