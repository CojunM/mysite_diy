#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:33
# @Author  : CJ  Mao
# @Site    : ${SITE}
# @File    : test_yieldroutes.py
# @Project : mysite_diy
# @Software: PyCharm
# from unittest import TestCase

# from brick.app.defaultapp import yieldroutes
from inspect import getfullargspec


def yieldroutes(func):
    """返回与签名（name，args）匹配的路由的生成器func参数的。如果函数
     接受可选的关键字参数。最好用以下示例来描述输出：
      a()         -> '/a'
        b(x, y)     -> '/b/<x>/<y>'
        c(x, y=5)   -> '/c/<x>' and '/c/<x>/<y>'
        d(x=5, y=6) -> '/d' and '/d/<x>' and '/d/<x>/<y>'"""
    path = '/' + func.__name__.replace('__', '/').lstrip('/')  # lstrip() 方法用于截掉字符串左边的空格或指定字符。
    spec = getfullargspec(func)
    argc = len(spec[0]) - len(spec[3] or [])
    path += ('/<%s>' * argc) % tuple(spec[0][:argc])
    print(path)
    # yield path
    for arg in spec[0][argc:]:
        path += '/<%s>' % arg
        print(path)
        # yield path


# 带yield的函数是一个生成器，而不是一个函数了，这个生成器有一个函数就是next函数，
# next就相当于“下一步”生成哪个数，这一次的next开始的地方是接着上一次的next停止的地方执行的，
# 所以调用next的时候，生成器并不会从foo函数的开始执行，只是接着上一步停止的地方开始，
# 然后遇到yield后，return出要生成的数，此步就结束。
def foo():
    print("starting...")
    while True:
        res = yield 4
        print("res:", res)


def func(args, a, b, c=1):
    pass


def func1(args):
    pass


def func2(args, a):
    pass


def _func3(args):
    pass


# class TestYieldroutes(TestCase):
if __name__ == '__main__':
    # while True:
    #     print(yieldroutes(func).__next__())
    #     # print(yieldroutes(func1).__next__())
    #     # print(yieldroutes(func2).__next__())
    #     # print(yieldroutes(_func3).__next__())
    # yieldroutes(func)
    g = foo()
    print(next(g))
    print("*" * 20)
    print(next(g))
    print(g.send(7))
