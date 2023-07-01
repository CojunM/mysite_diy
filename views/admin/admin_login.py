#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/4 17:05
# @Author  : Cojun
# @Site    : 
# @File    : admin_login.py
# @Software: PyCharm
from brick.contrib import web_helper, security_helper, encrypt_helper
from brick.contrib.except_helper import exception_handling
from brick.core.httphelper.response import JsonResponse
from brick.core.wsgiapp import put
from views.db_logic import db_logic
from views.models import User


@put('/api/login2/')
@exception_handling
def post_login():
    """用户登陆验证"""
    ##############################################################
    # 获取并验证客户端提交的参数
    ##############################################################
    username = web_helper.get_form('username', '帐号')
    password = web_helper.get_form('password', '密码')
    if not all([username, password]):
        return JsonResponse({'state': 400, 'msg': '缺少必传参数'})

    ip = web_helper.get_ip()

    ##############################################################
    # 判断用户登录失败次数，超出次做登录限制 ###
    # 获取管理员登录密码错误限制次数，0=无限制，x次/小时
    limit_login_count = 10
    # 获取操作出错限制值
    is_ok, msg, operation_times_key, error_count = security_helper.check_operation_times('login_error_count',
                                                                                         limit_login_count,
                                                                                         ip, False)
    # 判断操作的出错次数是否已超出了限制
    if not is_ok:
        # return web_helper.return_msg(-1, msg)
        return JsonResponse({'state': -1, 'msg': msg})
    ##############################################################
    # 获取登录用户记录，并进行登录验证 ###
    ##############################################################

    # if user is None:
    #     return JsonResponse({'code': 400,
    #                          'message': '用户名或密码错误'})
    # 生成实体缓存key
    model_cache_key = User.create_time + encrypt_helper.md5(str(username))

    # 初始化操作日志记录类
    # _User_operation_log_logic = User_operation_log_logic.UserOperationLogLogic()

    # 初始化管理员逻辑类
    _User_logic = db_logic(User)
    # 从数据库中读取用户信息
    User_result = _User_logic.get_model_for_cache_of_where(User.login_name == str(username))
    ##############################################################
    # 从session中读取验证码信息
    ##############################################################
    # s = web_helper.get_session()

    # User_result =User.select().where(User.login_name ==  str(username))
    # User_result = User.get(User.login_name == str(username))
    # print('pathnfo:12')
    # 判断用户记录是否存在
    if not User_result:
        # return web_helper.return_msg(-1, '账户不存在')
        return JsonResponse({'state': -1, 'msg': '账户不存在'})

    # 获取管理员id
    User_id = User_result.id
    # 获取管理员姓名
    User_name = User_result.login_name

    ##############################################################
    # 验证用户登录密码与状态 ###
    ##############################################################
    # 对客户端提交上来的验证进行md5加密将转为大写（为了密码的保密性，这里进行双重md5加密，加密时从第一次加密后的密串中提取一段字符串出来进行再次加密，提取的串大家可以自由设定）
    # pwd = encrypt_helper.md5(encrypt_helper.md5(password)[1:30]).upper()
    # 对客户端提交上来的验证进行md5加密将转为大写（只加密一次）
    pwd = encrypt_helper.md5(password).upper()
    # 检查登录密码输入是否正确
    if pwd != User_result.login_password.upper():
        # 记录出错次数
        security_helper.add_operation_times(operation_times_key)
        # 记录日志 _User_operation_log_logic.add_operation_log(User_id, User_name, ip, '【' + User_name +
        # '】输入的登录密码错误')
        # return web_helper.return_msg(-1, '密码错误')
        return JsonResponse({'state': -1, 'msg': '密码错误'})
    # 检查该账号虽否禁用了
    if not User_result.is_enabled:
        # 记录出错次数
        security_helper.add_operation_times(operation_times_key)
        # 记录日志
        # _User_operation_log_logic.add_operation_log(User_id, User_name, ip, '【' + User_name +
        # '】账号已被禁用，不能登录系统')
        # return web_helper.return_msg(-1, '账号已被禁用')
        return JsonResponse({'state': -1, 'msg': '账号已被禁用'})
    # 登录成功，清除登录错误记录
    security_helper.del_operation_times(operation_times_key)

    ##############################################################
    # 把用户信息保存到session中 ###
    ##############################################################

    s = web_helper.get_session()

    User_id = User_result.id
    s['id'] = User_id
    s['login_name'] = username
    s['roles'] = [role.id for role in User_result.roles]
    s['groups'] = [group for group in User_result.groups]
    s.save()
    # print(s)



    ##############################################################
    # 更新用户信息到数据库 ###
    ##############################################################
    # 更新当前管理员最后登录时间、Ip与登录次数（字段说明，请看数据字典）
    fields = {
        'last_login_time': 'now()',
        'last_login_ip': str(ip),
        'login_count': User_result.login_count + 1,
    }

    # 写入数据库
    _User_logic.add(fields, User.login_name == str(username))
    #     # 记录日志
    # _User_operation_log_logic.add_operation_log(User_id, User_name, ip, '【' + User_name + '】登陆成功')

    # return web_helper.return_msg(0, '登录成功1')
    return JsonResponse({'state': 0, 'msg': '登录成功'})
