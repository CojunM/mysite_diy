#!/usr/bin/env python
# coding=utf-8

from brick.contrib import string_helper, web_helper
from brick.core.httphelper.request import request

from views.db_logic import db_logic
from views.models import Menu_info, Positions


def check_user_power():
    """检查当前用户是否有访问当前接口的权限"""
    # 读取session

    session = web_helper.get_session()

    # session不存在则表示登录失效了
    if not session:
        web_helper.return_raise(web_helper.return_msg(-404, "您的登录已失效，请重新登录"))
    # print('读取sesion0')
    # 获取当前页面原始路由
    rule = request.route.rule
    # print(rule)
    # 获取当前访问接口方式（get/post/put/delete）
    method = request.method.lower()
    # print('method',request.url )
    # 获取当前访问的url地址
    url = string_helper.filter_str(request.url, '<|>|%|\'')
    print( 'url   ',url)
    # print('读取session')
    # 初始化日志相关变量
    # _manager_operation_log_logic = manager_operation_log_logic.ManagerOperationLogLogic()
    ip = web_helper.get_ip()
    manager_id = session.get('id')
    manager_name = session.get('name')
    cache_key = session.get('cache_key')
    # 设置访问日志信息
    if method == 'get':
        method_name = '访问'
    else:
        method_name = '进行'
    # print('读取session1')
    # 获取来路url
    http_referer = request.environ.get('HTTP_REFERER')
    if http_referer:
        # 提取页面url地址
        index = http_referer.find('?')
        if index == -1:
            web_name = http_referer[http_referer.find('/', 8) + 1:].split('/')[-1]
        else:
            web_name = http_referer[http_referer.find('/', 8) + 1: index].split('/')[-1]
    else:
        web_name = ''
    print('http_referer:', http_referer)
    # print('index:', index)
    print('web_name:', web_name)
    # 组合当前接口访问的缓存key值
    key = web_name + method + '(' + rule + ')'
    # 从菜单权限缓存中读取对应的菜单实体
    print('  key  ',  key)
    _menu_info_logic = db_logic(Menu_info)
    model = _menu_info_logic.get_model_for_url(key)
    print('model   ',model)
    if not model:
        # 添加访问失败日志
        # _manager_operation_log_logic.add_operation_log(manager_id, manager_name, ip, '用户访问[%s]接口地址时，检测没有操作权限' % (url))
        web_helper.return_raise(web_helper.return_msg(-1, "您没有访问权限1" + key))

    # 初始化菜单名称
    menu_name = getattr(model,'name')
    if  getattr(model,'parent_id') > 0:
        # 读取父级菜单实体
        _menu_info_logic = db_logic(Menu_info)
        parent_model = _menu_info_logic.get_model_for_cache(getattr(model,'parent_id'))
        # parent_model = _menu_info_logic.get_model_for_cache(model.get('parent_id'))
        if parent_model:
            menu_name = getattr(parent_model,'name').replace('列表', '').replace('管理', '') + menu_name

    # 从session中获取当前用户登录时所存储的职位id
    positions = db_logic(Positions)
    page_power =  positions.get_page_power(session.get('positions_id'))
    # 从菜单实体中提取菜单id，与职位权限进行比较，判断当前用户是否拥有访问该接口的权限
    if page_power.find(',' + str(getattr(model,'id', -1)) + ',') == -1:
        # 添加访问失败日志
        # _manager_operation_log_logic.add_operation_log(manager_id, manager_name, ip, '用户%s[%s]操作检测没有权限' % (method_name, menu_name))
        web_helper.return_raise(web_helper.return_msg(-1, "您没有访问权限2"))

    # if not (method == 'get' and model.get('name') in ('添加', '编辑')):
    # 添加访问日志
    # _manager_operation_log_logic.add_operation_log(manager_id, manager_name, ip, '用户%s[%s]操作' % (method_name, menu_name))

