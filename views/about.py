#!/usr/bin/env python
# coding=utf-8
from brick.apps.wsgiapp import get, put
from brick.contrib import web_helper, string_helper
from brick.contrib.except_helper import exception_handling
from brick.contrib.string_helper import string
# from logic import infomation_logic, _common_logic

@get('/api/about/')
@exception_handling
def callback():
    """
    获取指定记录
    """
    # _infomation_logic = infomation_logic.InfomationLogic()
    # result = _infomation_logic.get_model('id=1')
    # if result:
    #     return web_helper.return_msg(0, '成功', result)
    # else:
    #     return web_helper.return_msg(-1, "查询失败")
    return web_helper.return_msg(-1, "查询失败")

@put('/api/about/')
@exception_handling
def callback():
    """
    修改记录
    """
    # 检查用户权限
    # _common_logic.check_user_power()

    front_cover_img = web_helper.get_form('front_cover_img', '图片')
    content = web_helper.get_form('content', '内容', is_check_special_char=False)
    # 防sql注入攻击处理
    content = string_helper.filter_str(content, "'")
    # 防xss攻击处理
    content = string_helper.clear_xss(content)

    fields = {
        'front_cover_img': string(front_cover_img),
        'content': string(content),
    }
    # 更新记录
    # _infomation_logic = infomation_logic.InfomationLogic()
    # result = _infomation_logic.edit_model(1, fields)
    # if result:
    #     return web_helper.return_msg(0, '成功')
    # else:
    #     return web_helper.return_msg(-1, "提交失败")
