#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : sqlalchemy_demo
# @Time         : 2023/8/23 17:17
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
# 逆向工具 !sqlacodegen "sqlite:///test.db" > models.py
from sqlalchemy import create_engine, func, Column, Integer, String, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
# from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
from contextlib import contextmanager

# 创建数据库连接引擎和Session
engine = create_engine("sqlite:///test.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


@contextmanager
def session_maker(session=session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


# 创建表
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

    def __repr__(self):
        return f"<User(name='{self.name}', age={self.age})>"


# 创建表
metadata = MetaData()
metadata.create_all(engine)
# Base.metadata.create_all(engine)

# 插入数据
user1 = User(name='John', age=30)
user2 = User(name='Jane', age=25)
session.add(user1)
session.add(user2)
session.commit()

# 查询数据
# session.query(User).filter(User.age > 25).first()
users = session.query(User).filter(User.age > 25).all()
for user in users:
    print(user)



class A:
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', age={self.age})>"