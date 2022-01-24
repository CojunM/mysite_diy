#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:28
# @Author  : CJ  Mao
# @Site    : 
# @File    : cachedhelper.py
# @Project : mysite_diy
# @Software: PyCharm


class cached_property(object):
    """ A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property. """

    def __init__(self, func):
        # getattr() 是python 中的一个内置函数，用来获取对象中的属性值，getattr(obj,name[,default])
        # 其中obj为对象名，name是对象中的属性，必须为字符串。
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None: return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
