#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : sql_creater
# @Time         : 2024/11/18 20:45
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel, Field, Integer, BigInteger, String
from typing import Optional

# 创建数据库连接
engine = create_engine(os.getenv("ONEAPI_SQL_URL"))

# 创建检查器
inspector = inspect(engine)


# 获取表的列信息
def get_table_columns(table_name):
    columns = inspector.get_columns(table_name)

    # 动态创建 SQLModel 类
    class_attrs = {}
    for column in columns:
        column_name = column['name']
        column_type = column['type']
        nullable = column.get('nullable', True)
        primary_key = column.get('primary_key', False)

        # 根据不同的列类型选择合适的 Field
        if primary_key:
            field = Field(primary_key=True)
        elif isinstance(column_type, (Integer, BigInteger)):
            field = Field(default=None) if nullable else Field()
        elif isinstance(column_type, String):
            field = Field(default=None) if nullable else Field()
        else:
            field = Field()

        class_attrs[column_name] = Optional[type(column_type)] if nullable else type(column_type)
        class_attrs[f'{column_name}_field'] = field

    # 动态创建 SQLModel 类
    model_class = type(f'{table_name.capitalize()}Model', (SQLModel, BaseModel), class_attrs)
    return model_class



if __name__ == '__main__':
    # 使用示例
    UserModel = get_table_columns('hero')
