#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:56
# @Author  : CJ  Mao
# @Site    : 
# @File    : makelist_test.py
# @Project : mysite_diy
# @Software: PyCharm
from webcore.app.defaultapp import makelist


def test_list(l):
    lt = makelist(l)
    print(lt)


def test_tuple(t):
    lt = makelist(t)
    print(lt)


def test_dict(d):
    lt = makelist(d)
    print(lt)


def test_str(s):
    lt = makelist(s)
    print(lt)


if __name__ == '__main__':
    test_list([1, 2, 3])
    test_tuple((1, 2, 3, 4))
    test_dict({"name": "hongming", "age": "18"})
    test_str('http://127.0.0.1:8080/hello%E4%B8%AD')
