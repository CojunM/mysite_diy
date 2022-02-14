#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:18
# @Author  : Cojun  Mao
# @Site    : 
# @File    : test.py
# @Project : mysite_diy
# @Software: PyCharm

# 测试
from brick.orm.databases import SqliteDatabase
from brick.orm.felds import TextField
from brick.orm.models import Model

sqlite_db = SqliteDatabase('apptest.db')


class BaseModel(Model):
    """A base model that will use our Sqlite database."""

    class Meta:
        database = sqlite_db


class User(BaseModel):
    name = TextField()


new_user = User(name='LiMinghhj')
if __name__ == "__main__":
    # new_user.create_table()
    # new_user.save()
    # User.delete().where(User.name == 'LiMing').execute()
    r = User.select().where(User.name == 'LiMingt')
    for row in r:
        print('row', row.age)