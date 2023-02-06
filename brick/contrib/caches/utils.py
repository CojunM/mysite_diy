#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/1/20 21:10
# @Author  : Cojun 
# @Site    : 
# @File    : utils.py
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
import os
import threading as _threading
import warnings
import weakref

from brick.contrib.caches._compat import unicode_text

sha1 = None
class SyncDict(object):
    """
    An efficient/threadsafe singleton map algorithm, a.k.a.
    "get a value based on this key, and create if not found or not
    valid" paradigm:

        exists && isvalid ? get : create

    Designed to work with weakref dictionaries to expect items
    to asynchronously disappear from the dictionary.

    Use python 2.3.3 or greater !  a major bug was just fixed in Nov.
    2003 that was driving me nuts with garbage collection/weakrefs in
    this section.

    """
    def __init__(self):
        self.mutex = _threading.Lock()
        self.dict = {}

    def get(self, key, createfunc, *args, **kwargs):
        try:
            if key in self.dict:
                return self.dict[key]
            else:
                return self.sync_get(key, createfunc, *args, **kwargs)
        except KeyError:
            return self.sync_get(key, createfunc, *args, **kwargs)

    def sync_get(self, key, createfunc, *args, **kwargs):
        self.mutex.acquire()
        try:
            try:
                if key in self.dict:
                    return self.dict[key]
                else:
                    return self._create(key, createfunc, *args, **kwargs)
            except KeyError:
                return self._create(key, createfunc, *args, **kwargs)
        finally:
            self.mutex.release()

    def _create(self, key, createfunc, *args, **kwargs):
        self[key] = obj = createfunc(*args, **kwargs)
        return obj

    def has_key(self, key):
        return key in self.dict

    def __contains__(self, key):
        return self.dict.__contains__(key)

    def __getitem__(self, key):
        return self.dict.__getitem__(key)

    def __setitem__(self, key, value):
        self.dict.__setitem__(key, value)

    def __delitem__(self, key):
        return self.dict.__delitem__(key)

    def clear(self):
        self.dict.clear()


class WeakValuedRegistry(SyncDict):
    def __init__(self):
        self.mutex = _threading.RLock()
        self.dict = weakref.WeakValueDictionary()

def verify_directory(dir):
    """
    验证并创建目录。试图忽略与其他线程和进程的冲突。
    :param dir:
    :return:
    """

    tries = 0
    while not os.access(dir, os.F_OK):
        try:
            tries += 1
            os.makedirs(dir)
        except:
            if tries > 5:
                raise


def encoded_path(root, identifiers, extension=".enc", depth=3,
                 digest_filenames=True):
    """
    从给定列表中生成唯一的文件可访问路径从给定根目录开始的标识符。
    :param root:
    :param identifiers:
    :param extension:
    :param depth:
    :param digest_filenames:
    :return:
    """
    ident = "_".join(identifiers)

    global sha1
    if sha1 is None:
        from beaker.crypto import sha1

    if digest_filenames:
        if isinstance(ident, unicode_text):
            ident = sha1(ident.encode('utf-8')).hexdigest()
        else:
            ident = sha1(ident).hexdigest()

    ident = os.path.basename(ident)

    tokens = []
    for d in range(1, depth):
        tokens.append(ident[0:d])

    dir = os.path.join(root, *tokens)
    verify_directory(dir)

    return os.path.join(dir, ident + extension)


def deprecated(message):
    def wrapper(fn):
        def deprecated_method(*args, **kargs):
            warnings.warn(message, DeprecationWarning, 2)
            return fn(*args, **kargs)
        # TODO: use decorator ?  functools.wrapper ?
        deprecated_method.__name__ = fn.__name__
        deprecated_method.__doc__ = "%s\n\n%s" % (message, fn.__doc__)
        return deprecated_method
    return wrapper

