#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:37
# @Author  : CJ  Mao
# @Site    : 
# @File    : routeerr.py
# @Project : mysite_diy
# @Software: PyCharm


class RouteError(Exception):
    """ This is a base class for all routing related exceptions
    这是所有路由相关异常的基类"""


class RouteReset(Exception):
    """ If raised by a plugin or request handler, the route is reset and all
        plugins are re-applied.
        如果由插件或请求处理程序引发，则会重置路由并全部插件被重新应用 """


class RouterUnknownModeError(RouteError):
    pass


class RouteSyntaxError(RouteError):
    """ The route parser found something not supported by this router.
    路由分析器发现此路由器不支持的内容"""


class RouteBuildError(RouteError):
    """ The route could not be built. 无法建立路由"""
