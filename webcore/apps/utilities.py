#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:25
# @Author  : Cjun  Mao
# @Site    : 
# @File    : util.py
# @Project : mysite_diy
# @Software: PyCharm


def makelist(data):  # This is just to handy
    if isinstance(data, (tuple, list, set, dict)):
        return list(data)
    elif data:
        return [data]
    else:
        return []


class WSGIFileWrapper(object):

    def __init__(self, fp, buffer_size=1024 * 64):
        self.fp, self.buffer_size = fp, buffer_size
        for attr in ('fileno', 'close', 'read', 'readlines', 'tell', 'seek'):
            if hasattr(fp, attr): setattr(self, attr, getattr(fp, attr))

    def __iter__(self):
        buff, read = self.buffer_size, self.read
        while True:
            part = read(buff)
            if not part: return
            yield part


class _closeiter(object):
    ''' This only exists to be able to attach a .close method to iterators that
        do not support attribute assignment (most of itertools). '''

    def __init__(self, iterator, close=None):
        self.iterator = iterator
        self.close_callbacks = makelist(close)

    def __iter__(self):
        return iter(self.iterator)

    def close(self):
        for func in self.close_callbacks:
            func()
