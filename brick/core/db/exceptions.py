#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/11/4 11:43
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : exceptions.py
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

class PeeweeException(Exception): pass


class ImproperlyConfigured(PeeweeException): pass


class DatabaseError(PeeweeException): pass


class DataError(DatabaseError): pass


class IntegrityError(DatabaseError): pass


class InterfaceError(PeeweeException): pass


class InternalError(DatabaseError): pass


class NotSupportedError(DatabaseError): pass


class OperationalError(DatabaseError): pass


class ProgrammingError(DatabaseError): pass


class ExceptionWrapper(object):
    __slots__ = ['exceptions']

    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return
        if exc_type.__name__ in self.exceptions:
            new_type = self.exceptions[exc_type.__name__]
            if PY26:
                exc_args = exc_value
            else:
                exc_args = exc_value.args
            reraise(new_type, new_type(*exc_args), traceback)

