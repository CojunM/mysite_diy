#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:02
# @Author  : CJ  Mao
# @Site    : 
# @File    : loadhelper.py
# @Project : mysite_diy
# @Software: PyCharm
import sys


def load_app(target):
    """ 从模块加载瓶子应用程序并确保导入
        不影响当前默认应用程序，但返回一个单独的
        应用程序对象。有关目标参数，请参见：func:`load'。 """
    global NORUN;



def load_module(target, **namespace):
    """导入模块或从模块中获取对象。
        * ``包.模块``将“module”作为module对象返回。
        * ``包装型号：name``从中返回模块变量'name'`包装型号`.
        * ``包装型号：func（）``调用`pack.mod.func包（）`并返回结果。
        最后一个表单不仅接受函数调用，还接受任何类型的
        表达式。传递给此函数的关键字参数可用作
        局部变量。示例：``import_string（'re:compile（x）”，x='[a-z]'）``
    """
    module, target = target.split(":", 1) if ':' in target else (
        target, None)  # split() 通过指定分隔符对字符串进行切片，如果参数 num 有指定值，则分隔 num+1 个子字符串
    if module not in sys.modules: __import__(module)
    if not target: return sys.modules[module]
    if target.isalnum(): return getattr(sys.modules[module], target)  # isalnum() 方法检测字符串是否由字母和数字组成。
    package_name = module.split('.')[0]
    namespace[package_name] = sys.modules[package_name]
    return eval('%s.%s' % (module, target), namespace)  # 用来执行一个字符串表达式，并返回表达式的值。
