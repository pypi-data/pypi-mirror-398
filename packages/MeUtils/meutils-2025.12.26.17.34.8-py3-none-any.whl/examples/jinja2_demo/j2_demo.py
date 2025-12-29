#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : MeUtils.
# @File         : j2_demo
# @Time         : 2021/2/23 9:07 下午
# @Author       : yuanjie
# @WeChat       : 313303303
# @Software     : PyCharm
# @Description  : 


from jinja2 import Template

class A:
    safe=1

daxin = A()

s = """
<dl>
    {% for key, value in my_dict.items() %}
        <dt>{{ key }}</dt>
        <dd>{{ value }}</dd>
    {% endfor %}
</dl>
"""
template = Template(s)

print(template.render(my_dict={'a': 111}))


messages = [
    {"role": "system", "content": "U1"},
    {"role": "user", "content": "U1"},
    {"role": "assistant", "content": "A1"},
    {"role": "user", "content": "U2"},
    {"role": "assistant", "content": "A2"},
]

s = """
{% for message in messages %}
<|im_start|>{{message.get("role")}}\n{{message.get("content")}}<|im_end|>\n
{% endfor %}

"""
template = Template(s)

print(template.render(messages=messages))