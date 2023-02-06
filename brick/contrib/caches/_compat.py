#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/1/20 21:53
# @Author  : Cojun 
# @Site    : 
# @File    : _compat.py
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
xrange_ = range
NoneType = type(None)

string_type = str
unicode_text = str
byte_string = bytes

from urllib.parse import urlencode as url_encode
from urllib.parse import quote as url_quote
from urllib.parse import unquote as url_unquote
from urllib.parse import urlparse as url_parse
from urllib.request import url2pathname
import http.cookies as http_cookies
from base64 import b64decode as _b64decode, b64encode as _b64encode

try:
    import dbm as anydbm
except:
    import dumbdbm as anydbm


def b64decode(b):
    return _b64decode(b.encode('ascii'))


def b64encode(s):
    return _b64encode(s).decode('ascii')


def u_(s):
    return str(s)


def bytes_(s):
    if isinstance(s, byte_string):
        return s
    return str(s).encode('ascii', 'strict')


def dictkeyslist(d):
    return list(d.keys())
