#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:27
# @Author  : CJ  Mao
# @Site    : 
# @File    : testroute.py
# @Project : untitled1
# @Software: PyCharm
#
# from route.route import Router, Route
# from Application.Bottle import Bottle
import re

"""
'(\\\\*)' \
'(?:(?::([a-zA-Z_][a-zA-Z_0-9]*)?()(?:#(.*?)#)?)' \
'|(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)' \
'(?::((?:\\\\.|[^\\\\>]+)+)?)?)?>))'
"""
rule_syntax = re.compile('(\\\\*)' \
                         '(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)' \
                         '(?::((?:\\\\.|[^\\\\>]+)+)?)?)?>)')

default_pattern = '[^/]+'
default_filter = 're'

_MAX_GROUPS_PER_PATTERN = 99  # 最大分组模式


def _itertokens(rule):
    offset, prefix = 0, ''
    for match in rule_syntax.finditer(rule):  # finditer()函数来实现每次只返回一个，并且返回所在的位置
        prefix += rule[offset:match.start()]  # 这里很有意思，它只匹配动态形式的路径，prefix代表两个动态路径中的静态路径
        g = match.groups()

        if len(g[0]) % 2:  # Escaped wildcard转义通配符
            prefix += match.group(0)[len(g[0]):]
            offset = match.end()
            continue
        if prefix:
            yield prefix, None, None
        name, filtr, conf = g[1:4]
        yield name, filtr or 'default', conf or None
        offset, prefix = match.end(), ''
    if offset <= len(rule) or prefix:
        yield prefix + rule[offset:], None, None


def test_itertokens(rule):
    """Test method _itertokens(self, rule)"""
    offset, prefix = 0, ''
    it = rule_syntax.finditer(rule)
    # print(it)
    # match = it.__next__()
    # print(match)
    for match in rule_syntax.finditer(rule):  # finditer()函数来实现每次只返回一个，并且返回所在的位置
        prefix += rule[offset:match.start()]  # 这里很有意思，它只匹配动态形式的路径，prefix代表两个动态路径中的静态路径
        print(prefix)
        g = match.groups()  # groups()：所有group组成的一个元组，group(1)是与patttern中第一个“()”group匹配成功的子- 串，
        # group(2)是第二个，依次类推，如果index超了边界，抛出IndexError；
        print(g)
        print(g[0])
        print(match.group(2))
        # print(match.group(0)[len(g[0]):])
        a = 5
        if a % 2:
            print("t")  # a = 1,5,print t
        else:
            print("f")  # a = 0,4print f
        print(len(g[0]))
        if len(g[0]) % 2:  # Escaped wildcard转义通配符
            prefix += match.group(0)[len(g[0]):]
            offset = match.end()
            continue
        if prefix:
            print("yield prefix ：%s" % prefix)
        #         yield prefix, None, None
        name, filtr, conf = g[1:4]
        print(g[2])
        print("yieldname, filtr conf：%s  %s   %s" % (
            name, filtr or 'default', conf or None))  # ('', None, None, None, 'id', 'int', None)
        # yield name, filtr or 'default', conf or None
        offset, prefix = match.end(), ''
    if offset <= len(rule) or prefix:
        print(" yieldprefix + rule[offset:]：%s" % prefix + rule[offset:])
    #     yield prefix + rule[offset:], None, None


def _re_flatten(p):
    """将正则表达式模式中的所有捕获组变成非捕获组"""
    # if '(' not in p: return p
    # m = re.match(r'(\\*)(\((?!\?))', p)m.group(1) +
    # print(m.group(0))\(\?P<[^>]+>|
    # print(m.group(1))
    if '(' not in p: return p
    # re.sub()用于替换字符串中的匹配项。
    return re.sub(r'(\\*)(\((?!\?))',
                  lambda m: m.group(0) if len(m.group(1)) % 2 else '(?:', p)


filters = {'re': lambda conf: (_re_flatten(conf or default_pattern), None, None),
           'int': lambda conf: (r'-?\d+', int, lambda x: str(int(x))),
           'float': lambda conf: (r'-?[\d.]+', float, lambda x: str(float(x))),
           'path': lambda conf: (r'.+?', None, None)}
builder = []
builde = {}


def test_re():
    a = "123abc456"
    pattern = "([0-9]*)([a-z]*)([0-9]*)"
    print(re.search(pattern, a).group(0, 1, 2, 3))
    pattern = "(?:[0-9]*)([a-z]*)([0-9]*)"
    print(re.search(pattern, a).group(0, 1, 2))
    pattern = "(?:(?:(?:[0-9]*)(?:[a-z]*)([0-9]*)))"
    print(re.search(pattern, a).group(0, 1))


def test_add(rule, method, target, name=None):
    """  添加新规则或替换现有规则的目标。"""
    anons = 0  # Number of anonymous wildcards found 找到的匿名通配符数量
    keys = []  # Names of keys
    pattern = ''  # Regular expression pattern with named groups具有命名组的正则表达式模式
    filter = []  # Lists of wildcard input filters通配符输入过滤器列表
    builder = []  # Data structure for the URL builder URL生成器的数据结构
    is_static = True
    # _itertokens 通过一个正则表达式将动态 url 里面的参数信息提取出来
    # 如 /user/<name:re:.*>，key 为 name, mode 为 re, conf 为 .*
    # 对于没有参数的部分， key 就为那段 url，如 '/user'，mode 和 conf 为空
    # 因此，这段循环的用意就是提却出 rule 里面的参数信息，收集它的 filter，
    # 并由此构建出一个用来匹配路径的正则表达式
    for key, mode, conf in _itertokens(rule):  # ('id', 'int', None)
        print("key：%s" % key)
        print("mode：%s" % mode)
        print("conf：%s" % conf)
        if mode:
            # is_static = False
            if mode == 'default': mode = default_filter
            mask, in_filter, out_filter = filters[mode](
                conf)  # mask代表int/float等的对应正则匹配形式，in代表类型int/float，out是个匿名函数
            print("mask：%s" % mask)
            print("in_filter：%s" % in_filter)
            print("out_filter：%s" % out_filter)
            if not key:
                pattern += '(?:%s)' % mask
                print("no key pattern：%s" % pattern)
                key = 'anon%d' % anons
                anons += 1
            else:
                pattern += '(?P<%s>%s)' % (key, mask)
                print("pattern：%s" % pattern)
                keys.append(key)
            if in_filter: filter.append((key, in_filter))
            builder.append((key, out_filter or str))
            print("mode builder：%s" % builder)

        elif key:
            pattern += re.escape(key)  # 实现去除转义字符
            print("no mode pattern：%s" % pattern)
            builder.append((None, key))  # [(None, 'key')]
            print("key builder：%s" % builder)
    builde[rule] = builder  # {'rule': [(None, 'key')]}
    print("builde：%s" % builde)
    if name: builde[name] = builder

    # if is_static and not self.strict_order:
    #     self.static.setdefault(method, {})
    #     self.static[method][self.build(rule)] = (target, None)
    #
    #     return
    #
    try:
        re_pattern = re.compile('^(%s)$' % pattern)
        re_match = re_pattern.match
    except re.error:
        raise ("Could not add Route: %s (%s)" % (rule, _e()))
    print("filter：%s" % filter)
    if filter:  # filters：[('id', <class 'int'>)]
        def getargs(path):
            url_args = re_match(path).groupdict()  # groupdict返回一个包含所有匹配到的命名组的组名为键值和命名组匹配到的搜索文本子串为值作为元素的字典
            for name, wildcard_filter in filter:
                try:
                    url_args[name] = wildcard_filter(url_args[name])
                except ValueError:
                    raise (400, 'Path has wrong format.')
            return url_args
    elif re_pattern.groupindex:
        def getargs(path):
            return re_match(path).groupdict()  # groupdict返回一个包含所有匹配到的命名组的组名为键值和命名组匹配到的搜索文本子串为值作为元素的字典
    else:
        getargs = None

    # flatpat = _re_flatten(pattern)  # 将正则表达式模式中的所有捕获组变成非捕获组
    # whole_rule = (rule, flatpat, target, getargs)
    # print("getargs：%s" % getargs)
    # if (flatpat, method) in self._groups:
    #     if DEBUG:
    #         msg = 'Route <%s %s> overwrites a previously defined route'  # 路由< %s %s >覆盖以前定义的路由
    #         warnings.warn(msg % (method, rule), RuntimeWarning)
    #     self.dyna_routes[method][self._groups[flatpat, method]] = whole_rule
    # else:
    #     self.dyna_routes.setdefault(method, []).append(whole_rule)
    #     self._groups[flatpat, method] = len(self.dyna_routes[method]) - 1
    # print("self.dyna_routes：%s" % self.dyna_routes)
    # # self.dyna_routes：{'GET': [('/hello/<id:int>', '/hello/(?:-?\\d+)', <GET '/hello/<id:int>'
    # # <function hello at 0x023AEB20>>, <function Router.add.<locals>.getargs at 0x02842A48>)]}
    # self._compile(method)


def test_lamd(mode, conf):
    mask, in_filter, out_filter = filters[mode](conf)# mask代表int/float等的对应正则匹配形式，in代表类型int/float，out是个匿名函数
    print("mask：%s" % mask)
    print("in_filter：%s" % in_filter)
    print("out_filter：%s" % out_filter)
# print("out_filter：%s" % out_filter(conf))

if __name__ == '__main__':
    rule = "/hello/<id:int>"
    rule3 = "/hello/<id>"
    rule2 = "/hello"
    rule1 = "/user/<name:re:.*>"
    # test_itertokens(rule)
    # dict = {'Name': 'Zara', 'Age': 7, 'Name': 'Manni'}
    # comborules = dict['Name'] = []
    test_lamd('int', 'a')
    # print(comborules)
    # p = "(?: < \\([a-zA-Z_][a-zA-Z_0-9] *))"
    # print(_re_flatten(p))
    # mask, in_filter, out_filter = filters["int"](1)
    # print(mask)
    # print(in_filter)
    # print(out_filter)
    # builder.append((None, "key"))
    # builde["rule"] = builder
    # print(builde)
    # test_re()
    # test_add(rule, "GET", 'target')
