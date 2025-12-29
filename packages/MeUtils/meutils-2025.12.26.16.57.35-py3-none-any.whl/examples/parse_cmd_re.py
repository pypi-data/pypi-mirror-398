import re


def parse_command_string_recommended(text):
    """推荐的解析方法 - 简洁且有效"""
    # 分离描述和参数
    match = re.search(r'\s+--', text)

    if match:
        description = text[:match.start()].strip()
        args_part = text[match.start():].strip()

    return description, args_part


if __name__ == '__main__':
    import shlex

    # 测试
    # text = "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验 你好呀  --resolution 1080p   --duration  5 --camerafixed false"
    text = "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验 你好呀"

    # result = parse_command_string_recommended(text)
    # print(result)

    print(shlex.split(text))

    args = shlex.split(text)
    prompt = ""
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            break
        else:
            prompt += arg

    print(args[i:])
    #
    # # text = "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验"
    #
    # prompt, *args = shlex.split(text)

    # text =
    print(re.split(r'\s+--', text, maxsplit=1))
    args = re.split(r'\s+--', text, maxsplit=1)
    if len(args) == 2:
        prompt, args = args
        args = shlex.split(args)
    else:
        prompt = args[0]
