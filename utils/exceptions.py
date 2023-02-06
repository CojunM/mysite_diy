#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/4 19:31
# @Author  : Cojun
# @Site    : 
# @File    : exceptions.py
# @Software: PyCharm

from brick.contrib import log_helper, web_helper
from brick.core.httphelper.response import HTTPResponse




def exception_handling(func):
    """接口异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            # 执行接口方法
            return func(*args, **kwargs)
        except Exception as e:
            # 捕捉异常，如果是中断无返回类型操作，则再执行一次
            if isinstance(e, HTTPResponse):
                # print("ssss")
                func(*args, **kwargs)
            # 否则写入异常日志，并返回错误提示
            else:
                log_helper.error(str(e.args))
                return web_helper.return_msg(-1, "操作失败")
    return wrapper