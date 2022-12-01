#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/9/26 19:23
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : testreload.py
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
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
import os
import subprocess
import sys


def run(code):
    if os.environ.get("BRICK_AUTORELOAD_ENV") == "true":
        print('b')
        sys.exit(code)
    else:
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ['BRICK_AUTORELOAD_ENV'] = 'true'
        while True:
            p = subprocess.run(args, env=new_environ, close_fds=True)
            exit_code = p.returncode
            if exit_code != 3:
                print('a')
                sys.exit(exit_code)


if __name__ == '__main__':
    # run(2)
    run(3)
    run(2)