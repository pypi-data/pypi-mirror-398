#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_chatfire
# @Time         : 2024/6/27 17:41
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *

from openai import OpenAI, ChatCompletion

model = "moonshot-v1-8k"

from meutils.llm.openai_utils import to_openai_completion_params


# data = {'model': 'glm-4-9b-chat', 'messages': [{'role': 'user', 'content': '请你担任资深产品经理和资深DBA。\n为“芜湖佳羽信息科技有限公司”，设计名为《智能控制系统安全保护与防护软件》的后台管理系统。请你根据这个课题，设计该系统的模块功能。只需要你输出模块名称。\n - 至少输出12个模块, 所有模块都需要与该课题的业务紧密相关\n - 不需要用户管理, 角色管理, 菜单管理, 权限管理, 字典管理, 通知管理, 系统配置管理，登录模块，登录日志，操作日志等模块。'}, {'role': 'assistant', 'content': '\n1. 安全策略配置模块\n2. 防火墙设置模块\n3. 入侵检测系统管理模块\n4. 数据库安全模块\n5. 访问控制管理模块\n6. 定制化防护规则模块\n7. 安全事件响应与处理模块\n8. 安全漏洞扫描与修复模块\n9. 审计日志分析模块\n10. 用户行为分析模块\n11. 安全漏洞库管理模块\n12. 安全防护仪表盘模块'}, {'role': 'user', 'content': '请根据上述的模块, 设计使用MySQL实现数据库建表语句\n- 要求数据库建表语句有描述信息，对每个字段加上Comment注释，对每个表加上Comment注释；\n- 不需要除主键外的任何索引，请帮我移除索引和外键关系等约束；\n- 需要把关联其它表的信息，除了关联的ID还需要增加name的冗余字段方便我展示，每张表都需要\n- 枚举类型的字段，需要使用varchar类型代替，枚举值需要使用注释进行说明\n- 主键需要进行自增；\n- 所有的表名都需要有统一前缀tb_\n- 表名和字段名都需要小写，并且用下划线进行分割\n- 请给每张表都加上，创建人、创建时间、修改人、修改时间字段, 放在最后。\n- 数据表的字段根据业务，尽量多，尽量丰富些\n不要说别的信息，只需要给我提供MYSQL建表（CREATE TABLE）语句即可，\n因为篇幅的原因，需要你分批输出，每次输出5张表。继续输出的表，不要和前面输出的重复了。不需要用户表, 角色表, 菜单表, 权限表, 字典表, 通知表, 系统配置表，登录相关的表，日志相关的表等数据表。'}, {'role': 'assistant', 'content': "\n以下是第一组5张数据库建表语句：\n\nsql\n-- 表：tb_firewall_settings\nCREATE TABLE tb_firewall_settings (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  name varchar(255) NOT NULL COMMENT '防火墙策略名称',\n  description varchar(500) COMMENT '描述',\n  action varchar(50) NOT NULL COMMENT '动作：允许或拒绝',\n  port_range varchar(255) COMMENT '端口号范围',\n  protocol varchar(50) COMMENT '协议：TCP, UDP等',\n  enable boolean NOT NULL COMMENT '是否启用',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='防火墙策略设置表';\n\n-- 表：tb_intrusion_detection_system\nCREATE TABLE tb_intrusion_detection_system (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  name varchar(255) NOT NULL COMMENT '入侵检测系统名称',\n  type varchar(100) NOT NULL COMMENT '类型：网络型，系统型等',\n  description varchar(500) COMMENT '描述',\n  status varchar(50) COMMENT '状态：启用，禁用等',\n  last_scanned datetime COMMENT '最后扫描时间',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='入侵检测系统信息表';\n\n-- 表：tb_database_security\nCREATE TABLE tb_database_security (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  database_name varchar(255) NOT NULL COMMENT '数据库名称',\n  username varchar(255) NOT NULL COMMENT '用户名',\n  password_hash varchar(255) NOT NULL COMMENT '密码哈希',\n  last_login datetime COMMENT '最后登录时间',\n  access_level varchar(100) COMMENT '访问级别：读，写，读写等',\n  block_status boolean NOT NULL COMMENT '是否被阻止',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='数据库安全信息表';\n\n-- 表：tb_access_control_rules\nCREATE TABLE tb_access_control_rules (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  resource_name varchar(255) NOT NULL COMMENT '资源名称',\n  action varchar(50) NOT NULL COMMENT '动作：查看，修改等',\n  allowed_users varchar(500) COMMENT '允许的用户列表',\n  denied_users varchar(500) COMMENT '拒绝的用户列表',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='访问控制规则表';\n\n-- 表：tb_custom_protection_rules\nCREATE TABLE tb_custom_protection_rules (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  rule_name varchar(255) NOT NULL COMMENT '规则名称',\n  conditions TEXT COMMENT '规则条件',\n  actions TEXT COMMENT '规则动作',\n  enabled boolean NOT NULL COMMENT '是否启用',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='自定义防护规则表';\n\n\n继续输出下一组5张表：\n\nsql\n-- 表：tb_security_incident_response\nCREATE TABLE tb_security_incident_response (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  incident_id varchar(255) NOT NULL COMMENT '事件ID',\n  event_time datetime NOT NULL COMMENT '事件时间',\n  response_time datetime COMMENT '响应时间',\n  action_taken TEXT COMMENT '采取的行动',\n  notes TEXT COMMENT '备注',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='安全事件响应与处理记录表';\n\n-- 表：tb_vulnerability_scanning_and_fix\nCREATE TABLE tb_vulnerability_scanning_and_fix (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  scan_id varchar(255) NOT NULL COMMENT '扫描ID',\n  scan_time datetime NOT NULL COMMENT '扫描时间',\n  vulnerability_id varchar(255) NOT NULL COMMENT '漏洞ID',\n  severity_level varchar(50) NOT NULL COMMENT '严重程度：高，中，低等',\n  description TEXT COMMENT '漏洞描述',\n  fix_status varchar(50) COMMENT '修复状态：待修复，已修复等',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='漏洞扫描与修复记录表';\n\n-- 表：tb_audit_log_analysis\nCREATE TABLE tb_audit_log_analysis (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  log_id varchar(255) NOT NULL COMMENT '日志ID',\n  user_id varchar(255) NOT NULL COMMENT '用户ID',\n  action_time datetime NOT NULL COMMENT '操作时间',\n  resource_name varchar(255) COMMENT '资源名称',\n  action_type varchar(100) COMMENT '动作类型：登录，退出等',\n  result varchar(50) COMMENT '结果：成功，失败等',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='审计日志分析表';\n\n-- 表：tb_user_behavior_analysis\nCREATE TABLE tb_user_behavior_analysis (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  user_id varchar(255) NOT NULL COMMENT '用户ID',\n  behavior_type varchar(100) NOT NULL COMMENT '行为类型：登录异常，操作异常等',\n  behavior_detail TEXT COMMENT '行为详情',\n  detected_time datetime NOT NULL COMMENT '检测时间',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='用户行为分析表';\n\n-- 表：tb_vulnerability_library\nCREATE TABLE tb_vulnerability_library (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  vulnerability_id varchar(255) NOT NULL COMMENT '漏洞ID',\n  category varchar(100) COMMENT '类别：SQL注入，跨站脚本等',\n  description TEXT COMMENT '漏洞描述',\n  severity_level varchar(50) COMMENT '严重程度：高，中，低等',\n  fix_document TEXT COMMENT '修复文档',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='安全漏洞库管理表';\n\n\n继续输出下一组5张表：\n\n```sql\n-- 表：tb_security_dashboard\nCREATE TABLE tb_security_dashboard (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  dashboard_name varchar(255) NOT NULL COMMENT '仪表盘名称',\n  summary_report TEXT COMMENT '总结报告',\n  metrics_data TEXT COMMENT '指标数据',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='安全防护仪表盘表';\n\n-- 表：tb_security_policy\nCREATE TABLE tb_security_policy (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  policy_name varchar(255) NOT NULL COMMENT '策略名称',\n  policy_content TEXT COMMENT '策略内容',\n  target_systems TEXT COMMENT '目标系统',\n  apply_method varchar(100) COMMENT '应用方法：自动，手动等',\n  status varchar(50) COMMENT '状态：启用，禁用等',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='安全策略表';\n\n-- 表：tb_network_packet_analysis\nCREATE TABLE tb_network_packet_analysis (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  packet_id varchar(255) NOT NULL COMMENT '数据包ID',\n  source_ip varchar(255) NOT NULL COMMENT '源IP地址',\n  destination_ip varchar(255) NOT NULL COMMENT '目的IP地址',\n  protocol varchar(50) NOT NULL COMMENT '协议：TCP, UDP, ICMP等',\n  packet_size int NOT NULL COMMENT '数据包大小',\n  packet_capture_time datetime NOT NULL COMMENT '捕获时间',\n  create_by varchar(255) COMMENT '创建人',\n  create_time datetime COMMENT '创建时间',\n  update_by varchar(255) COMMENT '修改人',\n  update_time datetime COMMENT '修改时间',\n  PRIMARY KEY (id)\n) COMMENT='网络数据包分析表';\n\n-- 表：tb_device_management\nCREATE TABLE tb_device_management (\n  id int NOT NULL AUTO_INCREMENT COMMENT '主键',\n  device_id varchar(255) NOT NULL COMMENT '设备ID',\n  device_name varchar(255)"}, {'role': 'user', 'content': '继续'}], 'temperature': 0.99, 'top_p': 0.99, 'n': 1, 'max_tokens': 2048, 'stop': None, 'stream': False, 'presence_penalty': 0.0, 'frequency_penalty': 0.0, 'user': None, 'response_format': None, 'function_call': None, 'last_content': '继续', 'payload': {}, 'return_raw_response': None, 'additional_kwargs': {}, 'refs': [], 'file_ids': [], 'search': None, 'use_search': None, 'assistant_id': '65940acff94777010aa6b796', 'conversation_id': ''}
def check_models(models, api_key=os.getenv("OPENAI_API_KEY_GUOCHAN")):
    messages = [

        # {
        #     "role": "system",
        #     "content": [
        #         {
        #             "type": "text",
        #             "text": "你是AI"
        #         }
        #     ]
        # },
        # {"role": "user", "content": "1+1"},
        # {"role": "assistant", "content": "好的"},

        # {"role": "system", "content": "你是个机器人"},
        {"role": "user", "content": "9.8 9.11哪个大"},
    ]

    for model in models:
        print(f"""\n\n{"-" * 32}{model}{"-" * 32}\n\n""")
        try:

            completion = OpenAI(
                api_key=api_key,
                base_url="https://api.chatfire.cn/v1"
                # base_url="https://api.chatfire.cc/v1"
                # base_url="https://rix.chatfire.cn/v1"

            ).chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                # temperature=1,
                # top_p=0.9,
                # top_p=1,
                # max_tokens=100,

                # **to_openai_completion_params(data)

            )
            print(f"""\n\n{"-" * 32}非流{"-" * 32}\n\n""")
            print(completion)

            completion = OpenAI(
                api_key=api_key
            ).chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                # temperature=0,
                # top_p=0,
                # max_tokens=100,

            )
            print(f"""\n\n{"-" * 32}流{"-" * 32}\n\n""")

            for chunk in completion:
                print(chunk)

        except Exception as e:
            logger.debug(e)
            logger.error(model)


if __name__ == '__main__':
    # models = """
    # yi-large
    # yi-large-rag
    # yi-large-turbo
    # yi-medium
    # yi-medium-200k
    # """

    # models = """
    # qwen-long
    # qwen-plus
    # qwen-max
    # qwen-max-longcontext
    # farui-plus
    # """.split()

    # models = """
    # deepseek-coder
    # deepseek-chat
    # """
    #
    # models ="""
    # moonshot-v1-8k
    # moonshot-v1-32k
    # moonshot-v1-128k
    # """

    # models = """
    # qwen-turbo,qwen2-1.5b-instruct,qwen2-7b-instruct,qwen2-72b-instruct,qwen2-57b-a14b-instruct,qwen1.5-7b-chat,qwen1.5-14b-chat,qwen1.5-32b-chat,qwen1.5-110b-chat
    # """.strip().split(',')

    # models = ['glm-4']
    models = {
        # "SenseChat-Turbo": 1,
        # "SenseChat": 6,
        # "SenseChat-32K": 18, # 不支持
        # "SenseChat-128K": 30, # 不支持
        # "SenseChat-5": 20,  # 最新版本
        #
        # "SenseChat-Vision": 50,  # 图生文 待调整参数
        # "SenseChat-Character": 6, # 不支持
        # "SenseChat-Character-Pro": 7.5,  # 不支持

        "SenseChat-5-Cantonese": 13.5,  # 粤语大模型
    }
    # models = list(models.keys())
    # models = ['gemini-1.5-pro-latest']
    # check_models(models)
    # models = [
    #     # 'spark-lite',
    #     # 'spark-pro',
    #     'spark-max',
    #     'spark-ultra',
    #
    # ]
    # models = ['gemma2-27b-it', "gemini-1.5-pro-latest"]
    # models = ['farui-plus'] # qwen-max-longcontext
    # models = [
    #     # 'llama-3.1-405b-reasoning',
    #     'llama-3.1-70b-versatile', 'llama-3.1-8b-instant']
    # models = ['llama-3.1-70b-versatile']
    models = [
        'ERNIE-Speed-8K',
        'ERNIE-Speed-128K'

    ]

    models = [
        "claude-3-haiku-20240307",
        "gemini-pro"]
    # check_models(models)
    models = [
        "claude-3-5-sonnet-20240620"
    ]

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY") + '-403')
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))

    models = [
        # "gpt-3.5-turbo",
        # "gpt-4o"
        "deepseek-chat"
    ]

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_35"))
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))

    models = [
        'o1-mini'
    ]
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_OPENAI"))

    models = [
        "claude-3-5-sonnet-20240620"
    ]

    models = [
        # "gpt-4o-mini",
        "gpt-3.5-turbo"
        # "openai/gpt-4o-mini-2024-07-18",
        # "openai/gpt-3.5-turbo-0613"
    ]

    models = [
        "gemini-1.5-flash-002",
        # "google/gemini-flash-1.5-8b-exp"
        # "google/gemini-flash-1.5-exp"
    ]

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY")+"-451")
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY") + "-461")
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY") + "-442")

    # models = [
    #     'gpt-4o'
    # ]
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_SSVIP"))

    models = [
        # 'doubao-pro-128k',
        # "ai-search-pro:scholar",
        "o1"
    ]

    models = [
        # 'doubao-pro-128k',
        # "ai-search-pro:scholar",
        # "gpt-4o-2024-11-20"
        # "grok-2-1212"
        # 'o1-mini',
        # 'gpt-4o',
        # 'gemini-2.0-flash-exp',
        # 'gpt-4-turbo',
        # 'gemini-2.0-flash-thinking-exp',
        # 'cursor-claude',
        # "claude-3-5-sonnet-20241022"

        # "deepseek-r1:1.5b"
        # "deepseek-reasoner",
        # "deepseek-r1:1.5b"
        # "deepseek-v3-128k",
        # "qwen2.5-32b-instruct"
        # "deepseek-r1:1.5b"
        # "deepseek-r1:1.5b"

        # "deepseek-r1",
        # "deepseek-v3"
        # "deepseek-r1"
        # "qwen2.5-max"
        # "deepseek-r1-distill-qwen-7b",
        # "deepseek-r1-distill-qwen-32b"

        # "o1"

        # "claude-3-5-sonnet-20241022"

        # "gemini-2.0-flash-lite-preview-02-05"

        # "ds",

        # "qwen-max"
        "deepseek-r1-search-pro"

    ]
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_OPENAI"))
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_35"))
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_GUOCHAN"))

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_FREE"))

    # check_models(models)

    #
    # for i in range(5):
    #     check_models(models, api_key=os.getenv("OPENAI_API_KEY_GUOCHAN") + "-302")

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY_GUOCHAN") + "-725")

    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))
    # check_models(models)
    models = ['gemini-2.5-pro-preview-03-25']

    models = [
        "qwen3-235b-a22b"
    ]

    models = ["longcat-flash"]

    models = ['qwen3-0.6b']
    models = ['gpt-5.1']

    for i in range(1):

        check_models(models, api_key=os.getenv("OPENAI_API_KEY") + "-21183")
    # check_models(models, api_key=os.getenv("OPENAI_API_KEY"))

#############神奇 #############reasoning_content 神奇

#############
