#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:04
# @Author  : Cojun  Mao
# @Site    : 
# @File    : pewe.py
# @Project : mysite_diy
# @Software: PyCharm
from peewee import SqliteDatabase,Model
# 测试
sqlite_db = SqliteDatabase('mypp.db')


class BaseModel(Model):
    """A base model that will use our Sqlite database."""

    class Meta:
        database = sqlite_db


class User(BaseModel):
    name = TextField()


new_user = User(name='LiMing')
if __name__ == "__main__":
    new_user.create_table()
    new_user.save()
