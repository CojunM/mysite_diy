#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/4 19:48
# @Author  : Cojun
# @Site    : 
# @File    : loger.py
# @Software: PyCharm
import os
import sys
import logging
import logging.handlers
import traceback



def info(content):
    """记录日志信息"""
    if content:
        logging.info(content)

def detailtrace():
    """获取程序当前运行的堆栈信息"""
    retStr = ""
    f = sys._getframe()
    f = f.f_back  # first frame is detailtrace, ignore it
    while hasattr(f, "f_code"):
        co = f.f_code
        retStr = "%s(%s:%s)->" % (os.path.basename(co.co_filename),
                                  co.co_name,
                                  f.f_lineno) + retStr
        f = f.f_back
    return retStr

def error(content='', is_send_mail=True):
    """记录错误日志信息"""
    if traceback:
        content = content + '\n' + traceback.format_exc() + '\n'
    # 获取程序当前运行的堆栈信息
    content = content + '程序调用堆栈的日志：' + detailtrace() + '\n'

    logging.info(content)
    logging.error(content)

    # 发送邮件通知相关人员
    # if is_send_mail:
    #     info = mail_helper.send_error_mail(context=content)
    #     if info: logging.info(info)
#
# logging.basicConfig(level=logging.DEBUG,
#                     format='当前时间:%(asctime)s - 所在文件:%(filename)s - 行号:[%(lineno)d] - 级别:%(levelname)s - 日志信息:%(message)s',
#                     filename='log2.txt', filemode='a')
#
#
# def main():
#     # 命令行方式执行
#     if len(sys.argv) != 2:  # 判断命令行参数个数是否为2
#         print("请执行格式为[ python3 xx.py 9000 ] 的命令")
#         logging.warning('用户命令行执行程序参数个数输入错误，请输入两个参数')
#         return
#     if not sys.argv[1].isdigit():  # 判断字符串是否为数字组成
#         print("请执行格式为[ python3 xx.py 9000 ]的命令")
#         logging.warning('用户命令行执行程序第二个参数不是数字')
#         return
#     port = int(sys.argv[1])  # 获取终端命令行参数
#     web_server = HttpWebServer(port)
#
#     # # 指定端口
#     # web_server = HttpWebServer(9000)
#     web_server.start()
#
#
# -----------------------HttpWebServer类中handle_client_request()
# 函数 - ----------------------
# if request_path.endswith(".html"):  # 判断是否是动态资源请求
#     # 动态资源请求需找web框架进行处理，把请求参数给webFrame框架
#
#     logging.info('动态资源请求日志信息为:' + request_path)
#
#     # 准备需要给webFrame框架的参数信息，放在以下env字典中
#     env = {  # 字典存储用户的请求信息
#         "request_path": request_path
#         # 还可传入其他请求信息，如请求头
#     }
#
# else:  # 静态资源请求
# logging.info('静态资源请求日志信息为:' + request_path)
# try:
#     with open('static' + request_path, 'rb') as file:  # 动态打开指定文件
#         file_data = file.read()  # 读取指定文件数据