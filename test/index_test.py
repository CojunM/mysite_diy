#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:00
# @Author  : CJ  Mao
# @Site    : 
# @File    : index_test.py
# @Project : mysite_diy
# @Software: PyCharm
from wsgiref.simple_server import make_server


class App2():
    def __init__(self):
        pass

    def method(self):
        pass

    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['Hello world']


app = App2()

if __name__ == '__main__':
    httpd = make_server('localhost', 8000, app)
    httpd.serve_forever()
