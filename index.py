#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:26
# @Author  : CJ  Mao
# @Site    : 
# @File    : index.py
# @Project : mysite_diy
# @Software: PyCharm
from webcore.apps.wsgiapp import route, server_run, default_app, DefaultApp, static_file
from os.path import abspath, join, dirname

from webcore.contrib.sessions.middleware import SessionMiddleware
from webcore.templates.simpletemplate import template, TEMPLATE_PATH

# from beaker.middleware import SessionMiddleware
# from bottle import route, run, default_app, static_file, template, TEMPLATE_PATH

# 设置session参数
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 3600,
    'session.data_dir': '/tmp/sessions/simple',
    'session.auto': True
}
# 指定的模板路径
CUSTOM_TPL_PATH = abspath(join(dirname(__file__), "html/"))
print('CUSTOM_TPL_PATH:', CUSTOM_TPL_PATH)
# 静态文件
WEB_Bin_PATH = abspath(join(dirname(__file__), "html/temp/"))
WEB_css_PATH = abspath(join(dirname(__file__), "html/static/h-ui/css/"))
TEMPLATE_PATH.insert(0, WEB_Bin_PATH)
TEMPLATE_PATH.insert(0, CUSTOM_TPL_PATH)
TEMPLATE_PATH.insert(0, WEB_css_PATH)
print('WEB_Bin_PATH:', WEB_Bin_PATH)


# app1 = DefaultApp()
# @app1.route('/hello')
# def hel():
#     return "Hello World1234中"
@route('/hello')
def hel():
    # return template('Hello {{name}}!', name='World12')
    # return template('index',template_lookup=TEMPLATE_PATH)
    return template('index')


@route('/hello/<id:int>')
def hello(id):
    return "Hello1 %d" % id


@route('/static/h-ui/css/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root=WEB_css_PATH)


@route('/lib/Hui-iconfont/1.0.8/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root='./html/lib/Hui-iconfont/1.0.8/')


@route('static/h-ui/js/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root='.static/h-ui/js/')


@route('/lib/jquery.SuperSlide/2.1.1/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root='./html/lib/jquery.SuperSlide/2.1.1/')


@route('/lib/jquery/1.9.1/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root='./html/lib/jquery/1.9.1/')


@route('/lib/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root='./html/lib/')


@route('/temp/<bootstrap>')
def server_static(bootstrap):
    return static_file(bootstrap, root=WEB_Bin_PATH)


#
# @route('/hello/<id:float>')
# def hello3(id):
#     return "Hello3 %3.3f" % id
#
#
# @route('/he/<id>')
# def he2(id):
#     return "Hello2 %s" % id
#
#
@route('/hello/<id>')
def hello2(id):
    return "Hello2 %s" % id


# 函数主入口
if __name__ == '__main__':
    # app_argv = SessionMiddleware(app1, session_opts)
    app_argv = SessionMiddleware(default_app, session_opts)
    server_run(app=app_argv, debug=True, reloader=True)
    # server_run(debug=True, reloader=True)
    # app_argv = SessionMiddleware(default_app(), session_opts)
    # run(app=app_argv, debug=True, reloader=True)
    # run(debug=True, reloader=True)
