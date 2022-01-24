#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:44
# @Author  : CJ  Mao
# @Site    : 
# @File    : test_call_.py
# @Project : mysite_diy
# @Software: PyCharm

class CLanguage:
    # 定义__call__方法
    def __call__(self, name, add):
        print("调用__call__()方法", name, add)


# clangs = CLanguage()
# clangs("C语言中文网", "http://c.biancheng.net")


class CLang(object):
    # 定义__call__方法
    def __call__(self):
        print("调用__call__()方法")

    def __repr__(self):
        return "调用 __repr__()方法"
        # print("调用 __repr__()方法")

    def __init__(self, name, add):
        self.name = name
        #: 路径规则字符串（例如“`/wiki/：page```”）。
        self.add = add


if __name__ == "__main__":
    # print(clangs)
    # clang = CLang("C语言中文网", "http://c.biancheng.net")
    # print(clang)
    _sort_key = (1 or 2), 3
    print(_sort_key)
