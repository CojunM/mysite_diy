#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/7/6 0006 16:22
# @Author  : CJ  Mao
# @Site    : 
# @File    : 123.py
# @Project : WebFrame
# @Software: PyCharm
from webcore.apps.wsgiapp import server_run, route


@route('/hello/<id:int>')
def hello(id):
    return "Hello1 %d" % id


@route('/hello/<id:float>')
def hello3(id):
    return "Hello3 %3.3f" % id


@route('/hello/<id>')
def hello2(id):
    return "Hello2 %s" % id


@route('/hello')
def hello1():
    return "Hello World1234zhong 中"


server_run(host='localhost', port=8080, debug=True, reloader=True)
