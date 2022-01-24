#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:29
# @Author  : Cojun  Mao
# @Site    : 
# @File    : util.py
# @Project : mysite_diy
# @Software: PyCharm


def dict_update(orig, extra):
    new = {}
    new.update(orig)
    new.update(extra)
    return new


unicode = str
basestring = bytes


def format_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s
    elif isinstance(s, basestring):
        return s.decode(encoding)
    # Python3的话就只能用__str__方法，如果是Python2的话就使用__unicode__方法。
    elif hasattr(s, '__unicode__'):
        return s.__unicode__()
    else:
        return unicode(bytes(s), encoding)
