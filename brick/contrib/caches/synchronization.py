#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/1/20 21:08
# @Author  : Cojun 
# @Site    : 
# @File    : synchronization.py
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
import sys
import threading as _threading
from brick.contrib.caches import utils
# check for fcntl module
try:
    sys.getwindowsversion()
    has_flock = False
except:
    try:
        import fcntl
        has_flock = True
    except ImportError:
        has_flock = False

class NameLock(object):
    """a proxy for an RLock object that is stored in a name based
    registry.

    Multiple threads can get a reference to the same RLock based on the
    name alone, and synchronize operations related to that name.

    """
    locks = utils.WeakValuedRegistry()

    class NLContainer(object):
        def __init__(self, reentrant):
            if reentrant:
                self.lock = _threading.RLock()
            else:
                self.lock = _threading.Lock()

        def __call__(self):
            return self.lock

    def __init__(self, identifier=None, reentrant=False):
        if identifier is None:
            self._lock = NameLock.NLContainer(reentrant)
        else:
            self._lock = NameLock.locks.get(identifier, NameLock.NLContainer,
                                            reentrant)

    def acquire(self, wait=True):
        return self._lock().acquire(wait)

    def release(self):
        self._lock().release()


_synchronizers = utils.WeakValuedRegistry()


def _synchronizer(identifier, cls, **kwargs):
    return _synchronizers.sync_get((identifier, cls), cls, identifier, **kwargs)


def file_synchronizer(identifier, **kwargs):
    if not has_flock or 'lock_dir' not in kwargs:
        return mutex_synchronizer(identifier)
    else:
        return _synchronizer(identifier, FileSynchronizer, **kwargs)


def mutex_synchronizer(identifier, **kwargs):
    return _synchronizer(identifier, ConditionSynchronizer, **kwargs)
