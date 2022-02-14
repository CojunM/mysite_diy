#!/usr/bin/env python
# coding=utf-8

#遍历当前文件夹下的所有.py文件，然后用__import__导入到程序中
import os,sys
from brick.contrib import log_helper

pro_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(pro_path)
# os.walk() 方法用于通过在目录树中游走输出在目录中的文件名，向上或者向下。
# https://www.runoob.com/python/os-walk.html
for root,dirs,files in os.walk(pro_path):
    # print('files:', files)
    # print('dirs:', dirs)
    for file in files:
        name,ext = os.path.splitext(file)
        if ext == '.py' and name != '__init__' and pro_path == root:
            try:
                __import__(name)
            except Exception as e:
                log_helper.error('初始化导入py文件出现异常:' + str(e.args))
    for dir in dirs:
        if dir != '.svn':
            try:
                __import__(__name__ + '.' + dir)
            except Exception as e:
                log_helper.error('初始化导入py文件出现异常:' + str(e.args))
    break