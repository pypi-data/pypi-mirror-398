#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : x
# @Time         : 2025/8/25 15:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *



def parse_command_string(command_str: str) -> dict:
    """
    解析一个类似 "prompt --key1 value1 --key2 value2" 格式的字符串。

    Args:
        command_str: 输入的命令行字符串。

    Returns:
        一个包含 prompt 和解析后参数的字典。
        例如: {"prompt": "画条狗", "size": "1:1", "n": 10}
    """
    # 初始化结果字典
    result = {}

    # 使用正则表达式找到第一个参数 '--' 的位置
    # 这比简单的 split 更健壮，可以处理 prompt 中包含 '--' 的情况（虽然不常见）
    match = re.search(r'\s--\w', command_str)

    if not match:
        # 如果没有找到任何参数，整个字符串都是 prompt
        result['prompt'] = command_str.strip()
        return result

    first_arg_index = match.start()

    # 提取 prompt 和参数部分
    prompt = command_str[:first_arg_index].strip()
    args_str = command_str[first_arg_index:].strip()

    result['prompt'] = prompt

    # 将参数字符串按空格分割成列表
    # 例如 "--size 1:1 --n 10" -> ['--size', '1:1', '--n', '10']
    args_list = args_str.split()

    # 遍历参数列表，每次处理一个键值对
    i = 0
    while i < len(args_list):
        arg = args_list[i]

        # 确认当前项是一个参数键（以 '--' 开头）
        if arg.startswith('--'):
            key = arg[2:]  # 去掉 '--' 前缀

            # 检查后面是否跟着一个值
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('--'):
                value = args_list[i + 1]

                # 尝试将值转换为整数，如果失败则保留为字符串
                try:
                    processed_value = int(value)
                except ValueError:
                    processed_value = value

                # 布尔型
                if processed_value in ['true', 'yes', 'on']:
                    processed_value = True
                elif processed_value in ['false', 'no', 'off']:
                    processed_value = False

                result[key] = processed_value

                i += 2  # 跳过键和值，移动到下一个参数
            else:
                # 处理没有值的参数，例如 --test，可以设为 True 或忽略
                result[key] = True  # 或者可以写 pass 直接忽略
                i += 1
        else:
            # 如果某一项不是以 '--' 开头，它可能是格式错误，直接跳过
            i += 1

    return result


if __name__ == "__main__":
    # # --- 使用示例 ---
    # command = "画条狗 --size 1:1 --n 10"
    # parsed_result = parse_command_string(command)
    #
    # print(f"原始字符串: '{command}'")
    # print(f"解析结果: {parsed_result}")
    # print("-" * 20)
    #
    # # 测试其他例子
    # command_2 = "a cat in a space suit, cinematic lighting --n 4 --size 16:9"
    # parsed_result_2 = parse_command_string(command_2)
    # print(f"原始字符串: '{command_2}'")
    # print(f"解析结果: {parsed_result_2}")
    # print("-" * 20)
    #
    # command_3 = "一只赛博朋克风格的狐狸"  # 没有参数的情况
    # parsed_result_3 = parse_command_string(command_3)
    # print(f"原始字符串: '{command_3}'")
    # print(f"解析结果: {parsed_result_3}")
    #
    # 测试输入
    test_input = "画条狗 --size 1:1 --n 10 --aspect_ratio 1:1 --f       --a aa"
    test_input = "画条狗"

    output = parse_command_string(test_input)
    print(output)
