#!/usr/bin/env python
# coding=utf-8


# from common import web_helper
# from common.except_helper import exception_handling
from brick.apps.wsgiapp import get
from brick.contrib import web_helper
from brick.httphandles.request import request
from logic import manager_operation_log_logic
from brick.contrib.except_helper import exception_handling


@get('/api/logout/')
@exception_handling
def logout():
    """退出系统"""
    s = request.environ.get('web.session')
    try:
        # 添加退出登录日志
        # _manager_operation_log_logic = manager_operation_log_logic.ManagerOperationLogLogic()
        # _manager_operation_log_logic.add_operation_log(s.get('id', 0), s.get('name', ''), web_helper.get_ip(), '【' + s.get('name', '') + '】退出登录')

        s.delete()
    except Exception:
        pass
    return web_helper.return_msg(0, '成功')
