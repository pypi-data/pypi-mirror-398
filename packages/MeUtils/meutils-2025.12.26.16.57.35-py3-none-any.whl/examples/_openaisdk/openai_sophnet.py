#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :

from meutils.pipe import *
from meutils.llm.clients import OpenAI

# from openai import OpenAI


client = OpenAI(
    base_url=os.getenv("SOPHNET_BASE_URL"),
    # api_key=os.getenv("SOPHNET_API_KEY"),

    api_key="7XUcXdO6sf2GEnfbHou9J8-J4NBcZ0eo2kL4ziK43qznHlUS5d5amQtS1uApdOsUbS6UMHoMQbjSBJOscVraSg"

)

# EZvbHTgRIFKQaRpT92kFVCnVZBJXuWCsqw89nAfZZQC5T4A_57QXba21ZKpVCIcBpFb-WBemZ7BNZdJjCHyn1A

model = "DeepSeek-Prover-V2"
# model = "DeepSeek-R1"
# model = "DeepSeek-v3"

prompt = """
Complete the following Lean 4 code:

```lean4
import Mathlib


theorem putnam_2015_a4
(S : ℝ → Set ℤ)
(f : ℝ → ℝ)
(p : ℝ → Prop)
(hS : S = fun (x : ℝ) ↦ {n : ℤ | n > 0 ∧ Even ⌊n * x⌋})
(hf : f = fun (x : ℝ) ↦ ∑' n : S x, 1 / 2 ^ (n : ℤ))
(hp : ∀ l, p l ↔ ∀ x ∈ Set.Ico 0 1, f x ≥ l)
: IsGreatest p ((4 / 7) : ℝ ) := by
```

Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan outlining the main proof steps and strategies.
The plan should highlight key ideas, intermediate lemmas, and proof structures that will guide the construction of the final formal proof.
"""

prompt = "1+1"

messages = [
    {'role': 'user', 'content': prompt}
]
response = client.chat.completions.create(
    model=model,

    messages=messages,
    stream=True,
    # max_tokens=10,
)
print(response)
for chunk in response:
    print(chunk)
