#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:08
# @Author  : Cjun  Mao
# @Site    : 
# @File    : encode.py
# @Project : mysite_diy
# @Software: PyCharm


def tounicode(s, enc='utf8', err='strict'):
    # return s.decode(enc, err) if isinstance(s, bytes) else str(s)
    if isinstance(s, bytes):
        return s.decode(enc, err)
    return str("" if s is None else s)


def tobytes(s, enc='utf8'):
    # return s.encode(enc) if isinstance(s, str) else bytes(s)
    if isinstance(s, str):
        return s.encode(enc)
    return bytes("" if s is None else s)
