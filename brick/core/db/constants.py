#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/11/4 17:12
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : constants.py
# @Project : mysite_diy
# @Software: PyCharm
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""


OP_LIKE = 28
OP_ILIKE = 29

RESULTS_NAIVE = 1
RESULTS_MODELS = 2
RESULTS_TUPLES = 3
RESULTS_DICTS = 4
RESULTS_AGGREGATE_MODELS = 5
RESULTS_NAMEDTUPLES = 6



unicode_type = str
string_type = bytes
basestring = str
long = int
DATETIME_PARTS = ['year', 'month', 'day', 'hour', 'minute', 'second']
DATETIME_LOOKUPS = set(DATETIME_PARTS)
SQLITE_DATETIME_FORMATS = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d',
    '%H:%M:%S',
    '%H:%M:%S.%f',
    '%H:%M')

SQLITE_DATE_TRUNC_MAPPING = {
    'year': '%Y',
    'month': '%Y-%m',
    'day': '%Y-%m-%d',
    'hour': '%Y-%m-%d %H',
    'minute': '%Y-%m-%d %H:%M',
    'second': '%Y-%m-%d %H:%M:%S'}
MYSQL_DATE_TRUNC_MAPPING = SQLITE_DATE_TRUNC_MAPPING.copy()
MYSQL_DATE_TRUNC_MAPPING['minute'] = '%Y-%m-%d %H:%i'
MYSQL_DATE_TRUNC_MAPPING['second'] = '%Y-%m-%d %H:%i:%S'
