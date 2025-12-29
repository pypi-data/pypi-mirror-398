#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : mysql_orm
# @Time         : 2024/11/18 20:32
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os
import time

from meutils.pipe import *

from sqlmodel import Field, Session, SQLModel, create_engine, select, insert, update
from sqlalchemy import JSON


class Hero(SQLModel, table=True):
    # __table_args__ = {'extend_existing': True}  # includes this line

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None

hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

class Tasks(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}  # includes this line

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[int] = Field(default=None)
    updated_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    task_id: Optional[str] = Field(default=None, max_length=50)
    platform: Optional[str] = Field(default=None, max_length=30)
    user_id: Optional[int] = Field(default=None)
    channel_id: Optional[int] = Field(default=None)
    quota: Optional[int] = Field(default=None)
    action: Optional[str] = Field(default=None, max_length=40)
    status: Optional[str] = Field(default=None, max_length=20)
    fail_reason: Optional[str] = Field(default=None)
    submit_time: Optional[int] = Field(default=None)
    start_time: Optional[int] = Field(default=None)
    finish_time: Optional[int] = Field(default=None)
    progress: Optional[str] = Field(default=None, max_length=20)
    properties: Optional[dict] = Field(default=None, sa_type=JSON)
    data: Optional[dict] = Field(default=None, sa_type=JSON)
    remote_task_id: Optional[str] = Field(default=None, max_length=50)

    class Config:
        arbitrary_types_allowed = True


# hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
# hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
# hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

# engine = create_engine("sqlite:///database.db")
# connect_args = {"check_same_thread": False}

engine = create_engine(os.getenv("ONEAPI_MYSQL_URL"), pool_recycle=3600, echo=True)
#
# #
# SQLModel.metadata.create_all(engine)
#
with Session(engine) as session:
    statement = select(Hero).where(Hero.name == "Spider-Boy")
    hero = session.exec(statement)

    print(hero.first())
    session.commit()


# with Session(engine) as session:
#     # statement = insert(Tasks).values(
#     #     progress=100,
#     #     status='500',
#     #     fail_reason="测试",
#     #     platform="chatfire",
#     #     action="GET TASK",
#     #     channel_id=888,
#     #     # finish_time=time.time(),
#     #     remote_task_id='666',
#     # )
#
#     tasks = [
#         Tasks(
#             status='500',
#             fail_reason="测试",
#             platform="chatfire",
#             action="GET TASK",
#             channel_id=888,
#             # finish_time=time.time(),
#             remote_task_id='666',
#         ),
#         Tasks(
#             status='500',
#             fail_reason="测试",
#             platform="chatfire",
#             action="GET TASK",
#             channel_id=888,
#             # finish_time=time.time(),
#             remote_task_id='666',
#         ),
#     ]
#
#     session.add_all(tasks)
#
#     # _ = session.exec(statement)
#     session.commit()
