#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:44
# @Author  : Cojun  Mao
# @Site    : 
# @File    : testpeewee.py
# @Project : mysite_diy
# @Software: PyCharm
# 测试
from peewee import SqliteDatabase, Model, TextField, IntegerField

sqlite_db = SqliteDatabase('myapp2.db')


class BaseModel0(Model):
    """A base model that will use our Sqlite database."""

    class Meta:
        database = sqlite_db


class User(BaseModel0):
    name = TextField()
    age = IntegerField()


new_user = User(name='LiMing', age="18")
if __name__ == "__main__":
    # new_user.create_table()
    # new_user.save()
    # r = User.select().where(User.age=="8")
    # print(r)
    # for row in r:
    #     print('row',row.name, row.age)
    User.delete().where(User.name == 'LiMing').execute()
