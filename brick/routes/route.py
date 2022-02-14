#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:30
# @Author  : CJ  Mao
# @Site    : 
# @File    : route.py
# @Project : mysite_diy
# @Software: PyCharm
import re
from urllib.parse import urlencode

from brick.httphandles.response import HTTPError
from brick.routes.routeerror import RouteReset, RouteBuildError, RouteSyntaxError
from functools import update_wrapper
from brick.utilities.cachehelper import cached_property
from brick.utilities.sysinfo import _e


class Route(object):
    """
          此类将路由回调与特定于路由的元数据一起包装，并配置并按需应用插件。它还负责
          将URL路径规则转换成路由器可用的正则表达式。
      """

    def __init__(self, app, rule, method, callback, name=None,
                 plugins=None, skiplist=None, **config):
        # 安装此路由的应用程序。
        self.app = app
        #: 路径规则字符串（例如“`/wiki/：page```”）。
        self.rule = rule
        #: 作为字符串的HTTP方法（例如“GET”）。
        self.method = method
        #: 未应用插件的原始回调。有助于反省。
        self.callback = callback
        #: 路由的名称（如果指定）或“无”。
        self.name = name or None
        #: 路由特定插件的列表（参见：meth:`瓶子。路线`)
        self.plugins = plugins or []
        #: 不适用于此路由的插件列表（参见：meth:`瓶子。路线`).
        self.skiplist = skiplist or []
        #: 传递给：meth:`瓶子。路线`
        # decorator存储在此字典中。用于特定路线
        # 插件配置和元数据。

    def __call__(self, *a, **ka):  # 现在可以对实例直接调用
        """一些API更改为返回Route（）实例，而不是调用。一定要使用路由.呼叫方法，而不是直接调用路由实例"""
        return self.call(*a, **ka)

    # 修饰过的函数，变成是对象的属性，该对象第一次引用该属性时，会调用函数，
    # 对象第二次引用该属性时就直接从词典中取了，这也说明引用属性是经过__getattritue__。
    @cached_property
    def call(self):
        """ 应用了所有插件的路由回调。这个财产是按需创建，然后缓存以加速后续请求"""
        return self._make_callback()

    def all_plugins(self):
        """ 生成影响此路由的所有插件。"""
        pass

    # __repr__() 方法是类的实例化对象用来做“自我介绍”的方法，默认情况下，它会返回当前对象的“类名+object at+内存地址”，而如果对该方法进行重写，可以为其制作自定义的自我描述信息。
    # def __repr__(self):
    #     return ""

    def _make_callback(self):
        callback = self.callback
        # for plugin in self.all_plugins():
        #     try:
        #         if hasattr(plugin, 'apply'):
        #             api = getattr(plugin, 'api', 1)
        #             context = self if api > 1 else self._context
        #             callback = plugin.apply(callback, context)
        #         else:
        #             callback = plugin(callback)
        #     except RouteReset:  # 请使用已更改的配置重试。
        #         return self._make_callback()
        if not callback is self.callback:
            # update_wrapper或者wrap这样的函数来把被装饰的函数的属性（包括名称，doc等）放到装饰的函数上。
            update_wrapper(callback, self.callback)
        return callback

#
# def _re_flatten(p):
#     """将正则表达式模式中的所有捕获组变成非捕获组"""
#     if '(' not in p: return p
#     return re.sub(r'(\\*)(\(\?P<[^>]+>|\((?!\?))',
#                   lambda m: m.group(0) if len(m.group(1)) % 2 else m.group(1) + '(?:', p)
#
#
# class Router(object):
#     """     路由器是路由->目标对的有序集合。它习惯于根据多个路由有效地匹配WSGI请求并返回
#         满足请求的第一个目标。目标可能是任何东西，通常是字符串、ID或可调用对象。路由由
#         路径规则组成以及一个HTTP方法。路径规则是静态路径（例如`/contact`）或动态路径包
#         含通配符的路径（例如`/wiki/<page>`）。通配符语法有关匹配顺序的详细信息，请参见文档：`routing`。
#     """
#
#     default_pattern = '[^/]+'
#     default_filter = 're'
#
#     #: The current CPython regexp implementation does not allow more
#     #: than 99 matching groups per regular expression.
#     # ：当前的CPython regexp实现不允许
#     # ：每个正则表达式有99个以上的匹配组。
#     _MAX_GROUPS_PER_PATTERN = 99  # 最大分组模式
#
#     def __init__(self, strict=False):
#         self.rules = []  # All rules in order #按顺序排列的所有规则
#         self._groups = {}  # index of regexps to find them in dyna_routes 在动态路由中查找正则表达式的索引
#         self.builder = {}  # Data structure for the url builder url 生成器的数据结构
#         self.static = {}  # Search structure for static routes 静态路由的搜索结构
#         self.dyna_routes = {}  # 动态路由
#         self.dyna_regexes = {}  # Search structure for dynamic routes动态路由的搜索结构
#         #: If true, static routes are no longer checked first.如果为true，则不再首先检查静态路由。
#         self.strict_order = strict  # 严格的
#         self.filters = {
#             're': lambda conf:
#             (_re_flatten(conf or self.default_pattern), None, None),
#             'int': lambda conf: (r'-?\d+', int, lambda x: str(int(x))),
#             'float': lambda conf: (r'-?[\d.]+', float, lambda x: str(float(x))),
#             'path': lambda conf: (r'.+?', None, None)}
#
#     def add_filter(self, name, func):
#         """ 添加筛选器。使用配置调用提供的函数字符串作为参数，必须返回（regexp，to_python，to_url）元组。
#         第一个元素是一个字符串，最后两个是可调用的或不可调用的"""
#         self.filters[name] = func
#
#     # compile    函数用于编译正则表达式，生成一个    Pattern    对象
#     # '(\\\\*)'  # 匹配转义，捕获组中的第一个元素
#     # '(?:(?::([a-zA-Z_][a-zA-Z_0-9]*)?()(?:#(.*?)#)?)'
#     # '|(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)' #rule = "/hello/<id:int>" 匹配:int 匹配<name:int>类型分 第56个元素
#     # '(?::((?:\\\\.|[^\\\\>]+)+)?)?)?>))')  # 匹配 :re[:exp]  中的:exp 第七个元素
#     rule_syntax = re.compile('(\\\\*)' \
#                              '(?:(?::([a-zA-Z_][a-zA-Z_0-9]*)?()(?:#(.*?)#)?)' \
#                              '|(?:<([a-zA-Z_][a-zA-Z_0-9]*)?(?::([a-zA-Z_]*)' \
#                              '(?::((?:\\\\.|[^\\\\>]+)+)?)?)?>))')
#
#     def _itertokens(self, rule):
#         offset, prefix = 0, ''
#         for match in self.rule_syntax.finditer(rule):  # finditer()函数来实现每次只返回一个，并且返回所在的位置
#             prefix += rule[offset:match.start()]  # 这里很有意思，它只匹配动态形式的路径，prefix代表两个动态路径中的静态路径
#             g = match.groups()
#             if len(g[0]) % 2:  # Escaped wildcard转义通配符
#                 prefix += match.group(0)[len(g[0]):]
#                 offset = match.end()
#                 continue
#             if prefix:
#                 yield prefix, None, None
#             name, filtr, conf = g[4:7] if g[2] is None else g[1:4]
#             yield name, filtr or 'default', conf or None
#             offset, prefix = match.end(), ''
#         if offset <= len(rule) or prefix:
#             yield prefix + rule[offset:], None, None
#
#     def add(self, rule, method, target, name=None):
#         """      添加新规则或替换现有规则的目标。"""
#         anons = 0  # Number of anonymous wildcards found 找到的匿名通配符数量
#         keys = []  # Names of keys
#         pattern = ''  # Regular expression pattern with named groups具有命名组的正则表达式模式
#         filters = []  # Lists of wildcard input filters通配符输入过滤器列表
#         builder = []  # Data structure for the URL builder
#         is_static = True
#         # _itertokens 通过一个正则表达式将动态 url 里面的参数信息提取出来
#         # 如 /user/<name:re:.*>，key 为 name, mode 为 re, conf 为 .*
#         # 对于没有参数的部分， key 就为那段 url，如 '/user'，mode 和 conf 为空
#         # 因此，这段循环的用意就是提却出 rule 里面的参数信息，收集它的 filter，
#         # 并由此构建出一个用来匹配路径的正则表达式
#         for key, mode, conf in self._itertokens(rule):  # ('id', 'int', None)
#             if mode:
#                 is_static = False
#                 if mode == 'default': mode = self.default_filter
#                 mask, in_filter, out_filter = self.filters[mode](
#                     conf)  # mask代表int/float等的对应正则匹配形式，in代表类型int/float，out是个匿名函数
#                 if not key:
#                     pattern += '(?:%s)' % mask
#                     key = 'anon%d' % anons
#                     anons += 1
#                 else:
#                     pattern += '(?P<%s>%s)' % (key, mask)
#                     # keys.append(key)
#                 if in_filter: filters.append((key, in_filter))
#                 builder.append((key, out_filter or str))
#                 # #print("mode,builder：%s" % builder)
#                 # #print("pattern：%s" % pattern)
#             elif key:
#                 pattern += re.escape(key)  # 实现去除转义字符
#                 builder.append((None, key))  # [(None, 'key')]
#                 # ##print("key,builder：%s" % builder)  # [(None, '/hello')]
#                 # #print("keypattern：%s" % pattern)
#         self.builder[rule] = builder  # {'rule': [(None, 'key')]}
#         # #print("self.builder：%s" % self.builder)  # {'/hello': [(None, '/hello')]}
#         if name: self.builder[name] = builder
#
#         if is_static and not self.strict_order:
#             self.static.setdefault(method, {})
#             self.static[method][self.build(rule)] = (target, None)
#             # #print("self.static：%s" % self.static)
#             # {'GET': {'/hello': (<GET '/hello' <function hello at 0x0130EB20>>, None)}}
#             return
#
#         try:
#             re_pattern = re.compile('^(%s)$' % pattern)
#             # #print("pattern：%s" % pattern)
#             re_match = re_pattern.match
#         except re.error:
#             raise RouteSyntaxError("Could not add Route: %s (%s)" % (rule, _e()))
#         # #print("filters：%s" % filters)
#         if filters:  # filters：[('id', <class 'int'>)]
#             def getargs(path):
#                 # groupdict返回一个包含所有匹配到的命名组的组名为键值和命名组匹配到的搜索文本子串为值作为元素的字典
#                 url_args = re_match(path).groupdict()
#                 for name, wildcard_filter in filters:
#                     try:
#                         # #print("wildcard_filter(：%s" % wildcard_filter)
#                         url_args[name] = wildcard_filter(url_args[name])
#                         # #print("url_args[name]：%s" % url_args[name])
#                     except ValueError:
#                         raise HTTPError(400, 'Path has wrong format.')
#                 # #print("url_args：%s" % url_args)
#                 return url_args
#         elif re_pattern.groupindex:
#             def getargs(path):
#                 # #print("re_match(path).groupdict()：%s" % re_match(path).groupdict())
#                 return re_match(path).groupdict()  # groupdict返回一个包含所有匹配到的命名组的组名为键值和命名组匹配到的搜索文本子串为值作为元素的字典
#         else:
#             getargs = None
#
#         flatpat = _re_flatten(pattern)  # 将正则表达式模式中的所有捕获组变成非捕获组
#         whole_rule = (rule, flatpat, target, getargs)
#         # #print("getargs：%s" % getargs)
#         # #print("target：%s" % target)
#         if (flatpat, method) in self._groups:
#             # if DEBUG:
#             #     msg = 'Route <%s %s> overwrites a previously defined route'  # 路由< %s %s >覆盖以前定义的路由
#             #     warnings.warn(msg % (method, rule), RuntimeWarning)
#             self.dyna_routes[method][self._groups[flatpat, method]] = whole_rule
#         else:
#             self.dyna_routes.setdefault(method, []).append(whole_rule)
#             self._groups[flatpat, method] = len(self.dyna_routes[method]) - 1
#         # #print("self.dyna_routes：%s" % self.dyna_routes)
#         # #print("self._groups[flatpat, method]：%s" % self._groups[flatpat, method])
#         # self.dyna_routes：{'GET': [('/hello/<id:int>', '/hello/(?:-?\\d+)', <GET '/hello/<id:int>'
#         # <function hello at 0x023AEB20>>, <function Router.add.<locals>.getargs at 0x02842A48>)]}
#         self._compile(method)
#
#     def _compile(self, method):
#         """ "这个函数的目的是将同属于某一method(GET/POST)的所有path的无捕获组正则
#         用|连起来最后将结果存入dyna_regexes"""
#         all_rules = self.dyna_routes[method]
#         # #print("all_rules：%s" % all_rules)
#         # #print("len(all_rules)：%s" % len(all_rules))
#         comborules = self.dyna_regexes[method] = []
#         maxgroups = self._MAX_GROUPS_PER_PATTERN
#         for x in range(0, len(all_rules), maxgroups):
#             some = all_rules[x:x + maxgroups]
#             # #print(" x ：%s" % x)
#             # #print(" some ：%s" % some)
#             combined = [flatpat for (_, flatpat, _, _) in some]  # （）改[]好一些
#             # #print(" combined  ：%s" % combined)
#             # #print(" combined  ：%s" % [flatpat for (_, flatpat, _, _) in some])
#             combined = '|'.join('(^%s$)' % flatpat for flatpat in combined)  # join() 方法用于将序列中的元素以指定的字符连接生成一个新的字符串
#             # #print(" combined1 ：%s" % combined)
#             combined = re.compile(combined).match
#             # #print(" combined2：%s" % combined)
#             rules = [(target, getargs) for (_, _, target, getargs) in some]  # _ 代表不要用的变量
#             # #print(" rules ：%s" % rules)
#             comborules.append((combined, rules))
#             # #print(" comborules ：%s" % comborules)
#
#     def build(self, _name, *anons, **query):
#         """   通过在规则中填充通配符来构建URL。"""
#         builder = self.builder.get(_name)  # [(None, '/hello')]
#         if not builder: raise RouteBuildError("No route with that name.", _name)
#         try:
#             for i, value in enumerate(anons):  # enumerate() 函数用于将一个可遍历的数据对象(如列表、元组或字符串)组合为一个索引序列，同时列出数据和数据下标
#                 query['anon%d' % i] = value
#                 # #print("query：%s" % query)
#             url = ''.join([f(query.pop(n)) if n else f for (n, f) in builder])
#             url = url if not query else url + '?' + urlencode(query)
#             # #print("url：%s" % url)
#             # return url if not query else url + '?' + urlencode(query)
#             return url
#         except KeyError:
#             raise RouteBuildError('Missing URL argument: %r' % _e().args[0])
#
#     def match(self, environ):
#         """ Return a (target, url_agrs) tuple or raise HTTPError(400/404/405).
#         返回（target，url-agrs）元组或引发HTTPError（400/404/405）"""
#         verb = environ['REQUEST_METHOD'].upper()
#         path = environ['PATH_INFO'] or '/'  # 如果 environ['PATH_INFO']为空 path = '/'
#         # target = None
#         if verb == 'HEAD':
#             methods = ['PROXY', verb, 'GET', 'ANY']
#         else:
#             methods = ['PROXY', verb, 'ANY']
#         # #print("self.static：%s" % self.static)
#         # #print("dyna_regexes：%s" % self.dyna_regexes)
#         for method in methods:
#             if method in self.static and path.rstrip('/') in self.static[method]:
#                 target, getargs = self.static[method][path]
#                 # #print("statictarget：%s" % target)
#                 # #print("staticgetargs：%s" % getargs)
#                 return target, getargs(path) if getargs else {}
#             elif method in self.dyna_regexes:
#                 for combined, rules in self.dyna_regexes[method]:
#                     match = combined(path)
#                     if match:
#                         target, getargs = rules[match.lastindex - 1]  # lastindex表示匹配成功时候，匹配内容最后一个字符所在原字符串中的位置 + 1
#                         # #print("dynatarget：%s" % target)
#                         # #print("dynagetargs：%s" % getargs)
#                         return target, getargs(path) if getargs else {}
#
#         # No matching route found. Collect alternative methods for 405 response
#         # 找不到匹配的路由。收集405响应的替代方法
#         allowed = set([])
#         nocheck = set(methods)
#         for method in set(self.static) - nocheck:  # 求差集
#             if path in self.static[method]:
#                 allowed.add(verb)
#         for method in set(self.dyna_regexes) - allowed - nocheck:
#             for combined, rules in self.dyna_regexes[method]:
#                 match = combined(path)
#                 if match:
#                     allowed.add(method)
#         if allowed:
#             allow_header = ",".join(sorted(allowed))
#             raise HTTPError(405, "Method not allowed.", Allow=allow_header)
#
#         # No matching route and no alternative method found. We give up
#         # 找不到匹配的路由和替代方法。我们放弃了
#         raise HTTPError(404, "Not found: " + repr(path))
