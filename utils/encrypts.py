#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/1/4 15:02
# @Author  : Cojun
# @Site    : 
# @File    : encrypts.py
# @Software: PyCharm
import hashlib


def encrytp_md5(text):
    """md5加密函数"""
    md5 = hashlib.md5()
    if not isinstance(text, bytes):
        text = str(text).encode('utf-8')
    md5.update(text)
    return md5.hexdigest()
