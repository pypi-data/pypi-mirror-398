import re
def universal_command_parser(text):
    """
    通用的命令行参数解析器，可以处理未知参数
    """
    # 分离描述和参数
    match = re.search(r'\s+--', text)
    print(match)
    if match:
        description = text[:match.start()].strip()
        args_part = text[match.start():].strip()

        print(description)
        print(args_part)
    else:
        return {"description": text.strip(), "parameters": {}}

    # 改进的正则表达式，处理带引号的值
    pattern = r'--(\w+)\s+(".*?"|\'.*?\'|[^\s--]+)'
    matches = re.findall(pattern, args_part)

    parameters = {}
    for param, value in matches:
        # 去除引号
        if (value.startswith('"') and value.endswith('"')) or \
                (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # 智能类型转换
        converted_value = smart_type_conversion(value)
        parameters[param] = converted_value

    return {
        "description": description,
        "parameters": parameters
    }

def smart_type_conversion(value):
    """智能类型转换"""
    # 布尔值
    if value.lower() in ['true', 'yes', 'on', '1']:
        return True
    elif value.lower() in ['false', 'no', 'off', '0']:
        return False

    # 整数
    try:
        return int(value)
    except ValueError:
        pass

    # 浮点数
    try:
        return float(value)
    except ValueError:
        pass

    # 字符串
    return value

# 完整示例
if __name__ == "__main__":
    test_string = "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验  --resolution 1080p  --duration 5 --camerafixed false"

    result = universal_command_parser(test_string)

    print(result)

    # print("解析结果:")
    # print(f"描述: {result['description']}")
    # print("参数:")
    # for key, value in result['parameters'].items():
    #     print(f"  {key}: {value} ({type(value).__name__})")