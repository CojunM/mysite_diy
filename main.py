#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/1/20 14:35
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : main.py
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
                ┃  永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
import logging
import os
import sys
import urllib.parse

# 导入工具函数包
# from common import web_helper, log_helper
# 导入api代码模块（初始化api文件夹里的各个访问路由，这一句不能删除，删除后将无法访问api文件夹里的各个接口）
import views
from brick.contrib import web_helper, log_helper
from brick.contrib.sessions.middleware import SessionMiddleware
from brick.core.httphelper import response
from brick.core.httphelper.request import request, BaseRequest
from brick.core.simpletemplate import template
from brick.core.wsgiapp import route, hook, server_run, default_app, static_file, get

#############################################
# 初始化框架相关参数
#############################################
# 获取当前main.py文件所在服务器的绝对路径
program_path = os.path.split(os.path.realpath(__file__))[0]
# 将路径添加到python环境变量中
sys.path.append(program_path)
# 让提交数据最大改为2M（如果想上传更多的文件，可以在这里进行修改）
BaseRequest.MEMFILE_MAX = 1024 * 1024 * 2
# 定义upload为上传文件存储路径
upload_path = os.path.join(program_path, 'upload')
#############################################
# 初始化日志相关参数
#############################################
# 如果日志目录log文件夹不存在，则创建日志目录
if not os.path.exists('log'):
    os.mkdir('log')
# 初始化日志目录路径
log_path = os.path.join(program_path, 'log')
# 定义日志输出格式与路径
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    filename="%s/info.log" % log_path,
                    filemode='a')

# 设置session参数
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 3600,
    'session.data_dir': './tmp/sessions/simple',
    'session.auto': True
}


@hook('before_request')
def validate():
    """使用勾子处理接口访问事件"""

    # 获取当前访问的Url路径
    path_info = request.environ.get("PATH_INFO")

    # 过滤不用做任何操作的路由（即过滤不用进行判断是否登录和记录日志的url）
    # 过滤不用进行登录权限判断的路由（登录与退出登录不用检查是否已经登录）
    if path_info in ['/favicon.ico', '/', '/api/verify/'] or not str(
            path_info).startswith('/api'):
        return
    ### 记录客户端提交的参数 ###
    # 获取当前访问url路径与ip
    request_log = 'url:' + path_info + ' ip:' + web_helper.get_ip()

    try:
        # 添加json方式提交的参数
        if request.json:
            request_log = request_log + ' params(json):' + urllib.parse.unquote(str(request.json))
    except:
        pass

    try:
        # 添加GET方式提交的参数
        if request.query_string:
            request_log = request_log + ' params(get):' + urllib.parse.unquote(str(request.query_string))

        # 添加POST方式提交的参数
        if request.method == 'POST':
            request_log = request_log + ' params(post):' + urllib.parse.unquote(str(request.params.__dict__))

        # 存储到日志文件中
        log_helper.info(request_log)
    except:
        pass

    # 处理ajax提交的put、delete等请求转换为对应的请求路由（由于AJAX不支持RESTful风格提交，所以需要在这里处理一下，对提交方式进行转换）
    if request.method == 'POST' and request.POST.get('_method'):
        request.environ['REQUEST_METHOD'] = request.POST.get('_method', '')

    # 过滤不用进行登录权限判断的路由（登录与退出登录不用检查是否已经登录）
    url_list = ["/api/login/", "/api/login1/", "/api/logout/", "/api/login2/"]
    if path_info in url_list:
        pass
        # print('0112332')
    else:
        print('112332')
        # 已经登录成功的用户session肯定有值，没有值的就是未登录
        session = web_helper.get_session()
        # 获取用户id
        manager_id = session.get('id', 0)
        login_name = session.get('login_name', 0)
        # 判断用户是否登录
        if not manager_id or not login_name:
            web_helper.return_raise(web_helper.return_msg(-404, "您的登录已失效，请重新登录"))


@get('/<filename:path>')
def send_static(filename):
    ''''加载静态文件'''
    return static_file(filename, root='./html/')


# 使其成为样式表专用
# @get('/<filename:re:.*\.css>')
# def stylesheets(filename):
#     return static_file(filename, root='static/')
@get('/upload/<filepath:path>')
def upload_static(filepath):
    """设置静态内容路由"""
    response.add_header('Content-Type', 'application/octet-stream')
    return static_file(filepath, root=upload_path)


@route('/')
def hel():
    return template('index')


@route('/api/login2/admin_main')
def hel():
    return template('admin_main')


@route('/api/login2/admin_index')
def hel():
    return template('admin_index')


@route('/api/login2/admin_base')
def hel():
    return template('admin_base')


@route('/api/login/products_list')
def hel():
    return template('products_list')


# @route('/api/login/main/')
# def hel():
#     # return template('Hello {{name}}!', name='World12')
#     # return template('index',template_lookup=TEMPLATE_PATH)
#     return template('main')


@route('/api/login/main')
def hel():
    return template('main')


@route('/api/login2/desk')
@route('/api/login1/desk')
def hel():
    return template('desk')


@get('/api/products')
def hel():
    return template('products')


@get('/contact_us')
def hel():
    return template('contact_us')


@get('/products')
def hel():
    return template('products')


@get('/about')
def hel():
    return template('about')

@route('/api/login2/welcome')
@route('/api/login/welcome')
@route('/api/login1/welcome')
def hel():
    return template('welcome')


# @route('/api/main/menu_info/?<<id:int>>')
@get('/api/login/menu_info')
@get('/api/login1/menu_info')
def hel():
    return template('menu_info')

@get('/api/login2/menu_info')
def hel():
    return template('menu')


@get('/api/login/department')
def hel():
    return template('department')


@get('/api/login1/')
def helo():
    return template('login1')


@get('/api/login2/')
def helo():
    return template('admin_login')


@get('/api/login/')
def helo():
    return template('login')


@get('/api/login/manager_edit')
@get('/api/login1/manager_edit')
def helo():
    return template('manager_edit')


@get('/api/login/positions')
@get('/api/login1/positions')
def helo():
    return template('positions')


@get('/api/login/menu_info_edit')
@get('/api/login1/menu_info_edit')
def helo():
    return template('menu_info_edit')


@get('/api/login/products_class')
def helo():
    return template('products_class')


@get('/api/login/manager_operation_log')
def helo():
    return template('manager_operation_log')


@get('/api/login/manager')
def helo():
    return template('manager')


# @get('/api/login/products_class')
# def helo():
#     return template('products_class')

# 函数主入口
if __name__ == '__main__':
    app_argv = SessionMiddleware(default_app, session_opts)
    server_run(app=app_argv, debug=True, reloader=True)

    # server_run(default_app, debug=True, reloader=True)
else:
    # 使用uwsgi方式处理python访问时，必须要添加这一句代码，不然无法访问
    application = SessionMiddleware(default_app, session_opts)
