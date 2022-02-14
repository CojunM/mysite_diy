#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/3/10 17:05
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : testdicthelper.py
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
import functools
from collections import MutableMapping


class DictProperty(object):
    """ 属性，该属性映射到本地dict-like属性中的键。 """

    def __init__(self, attr, key=None, read_only=False):
        self.attr, self.key, self.read_only = attr, key, read_only
        print(attr)
        print(key)
    def __call__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter, self.key = func, self.key or func.__name__
        return self

    # 当访问request.GET的时候，就会调用该方法, obj为当前对象，cls为当前类
    def __get__(self, obj, cls):  # obj则对应将某个属性托管给描述的实例对象的引用，对应的应该为request对象；而cls则为Request类的引用。
        if obj is None: return self  # obj为None说明被装饰的方法作为类变量来访问(Bottle.query)，返回描述符自身
        key, storage = self.key, getattr(obj, self.attr)  # getattr() 函数用于返回一个对象属性值
        # key='bottle.get.query'
        # storage = environ 即包含HTTP请求的信息的environ

        # 判断envrion中是否包含key来决定是否需要解析
        # 如果bottle.request.query不在storage也就是不在request.environ中的时候，
        # 在request.environ中添加'bottle.request.query':request.query(self)， 即reqeuest.query(self)的返回值：GET参数的字典.
        # self.getter(obj)就是调用了原来的query方法，不过要传入一个Request实例，也就是obj
        if key not in storage: storage[key] = self.getter(obj)

        return storage[key]

    def __set__(self, obj, value):
        if self.read_only: raise AttributeError("Read-Only property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only: raise AttributeError("Read-Only property.")
        del getattr(obj, self.attr)[self.key]
class MultiDict(MutableMapping):
    """ 此dict为每个键存储多个值，但其行为与普通dict，
    它只返回任何给定键的最新值。有一些特殊的方法可以访问完整的值列表。
    """

    def __init__(self, *a, **k):
        self.dict = dict((k, [v]) for (k, v) in dict(*a,**k).items())
        print(self.dict)
    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return key in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, key):
        return self.dict[key][-1]

    def __setitem__(self, key, value):
        self.append(key, value)

    def keys(self):
        return self.dict.keys()

    def values(self):
        return (v[-1] for v in self.dict.values())

    def items(self):
        return ((k, v[-1]) for k, v in self.dict.items())

    def allitems(self):
        return ((k, v) for k, vl in self.dict.items() for v in vl)
if __name__== '__main__':
    # catchall = DictProperty('config', 'catchall')
    # pairs=[(1,2),(3,4)]
    # for key, value in pairs:
    #         # get[key] = value
    #      print(10*"*")
    #      print(key, value)
    a=('a','2','3')
    k={'c':12,'d':34}
    dt = MultiDict(a,k)
    # dt = dict((k, [v]) for (k, v) in dict(*a, **k).items())
    print(dt)