#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:52
# @Author  : Cojun  Mao
# @Site    : 
# @File    : test_re.py
# @Project : mysite_diy
# @Software: PyCharm

import re


# a = "123abc456"
# pattern = "([0-9]*)([a-z]*)([0-9]*)"
# print(re.search(pattern, a).group(0, 1, 2, 3))
#
# pattern = "(?:[0-9]*)([a-z]*)([0-9]*)"
# print(re.search(pattern, a).group(0, 1, 2))
#
# pattern = "(?:(?:([0-9]*)(?:[a-z]*))([0-9]*))"
# print(re.search(pattern, a).group(0, 1, 2))
#
# pattern = "(?:(?:([0-9]*)([a-z]*))([0-9]*)(?:[a-z]*))"
# print(re.search(pattern, a).group(0, 1, 2,3))

# a = """ name = "Bob" """
# pattern = """([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}|\'(?:[^\\\\\']|\\\\.)+?\'''|"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}|"{3}(?:[^\\\\]''|\\\\.|\\n)+?"{3})) """
# print(re.search(pattern, a).groups())
