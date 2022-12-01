#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:26
# @Author  : Cojun  Mao
# @Site    : 
# @File    : teststpl.py
# @Project : mysite_diy
# @Software: PyCharm

# import re
#
# from brick.template.templateerror import TemplateError
#
#
# class SimpleTemplate(object):
#     re_block = re.compile(r'^\s*%\s*((if|elif|else|try|except|finally|for|while|with).*:)\s*$')
#     re_end = re.compile(r'^\s*%\s*end(.*?)\s*$')
#     re_code = re.compile(r'^\s*%\s*(.*?)\s*$')
#     # ? \{\{(.* ?)\}\} 作一个简单的分析匹配以{{开头， 和}}结束的字符串中间的(. *?) 表示惰性匹配，
#     # 将匹配最少的结果，如果我们传递进来的是{{name}}}(右边有三个}) ，那么只会匹配{{name}},
#     # 不会把最后一个} 给匹配上
#     re_inc = re.compile(r'\{\{(.*?)\}\}')
#
#     # # 惰性匹配不会匹配到 }
#     # In[4]: re_inline = re.compile(r'\{\{(.*?)\}\}')
#     # In[5]: m = re_inline.match("{{name}}}")
#     # In[6]: m.groups()
#     # Out[6]: ('name',)
#     #
#     # # 贪婪匹配会匹配到 }
#     # In[7]: re_inline2 = re.compile("\{\{(.*)\}\}")
#     # In[10]: m2 = re_inline2.match("{{name}}}")
#     # In[11]: m2.groups()
#     # Out[11]: ('name}',)
#
#     # xrange(1, len(splits), 2)# 的用途，
#     #
#     # In[1]:
#     # import re
#     #
#     # In[2]: re_inline = re.compile(r'\{\{(.*?)\}\}')
#     #
#     # In[3]: re_inline.split("name")
#     # Out[3]: ['name']
#     #
#     # In[4]: re_inline.split("{{name}}")
#     # Out[4]: ['', 'name', '']
#     # # name 和 age 字段index为1, 3 即 range(1, 5, 2)
#     # In[5]: re_inline.split("My name is {{name}}. I am {{age}} years old.")
#     # Out[5]: ['My name is ', 'name', '. I am ', 'age', ' years old.']
#     #
#     # In[6]: range(1, 5, 2)
#     # Out[6]: [1, 3]
#     def __init__(self, template):
#         self.code = "\n".join(self.compile(template))
#         self.co = compile(self.code, '<string>', 'exec')
#
#     def render(self, **args):
#         ''' Returns the rendered template using keyword arguments as local variables. '''
#         args['stdout'] = []
#         # __builtins__ 是对内建模块__builtin__的引用，并且有如下两个方面差异：
#         # 在主模块中，即没有被其他文件导入。__builtins__是对__builtin__本身的引用，两者是相同的。
#         # 通过__builtins__ is __builtin__.__dict__ 猜想：在非__main__'模块中，也就是模块被导入后，
#         # __builtins__应该属于__builtin__.__dict__的一部分，是对__builtin__.__dict__
#         # 的引用，而非builtin本身，它在任何地方都可见，此时builtins的类型是字典。
#         args['__builtins__'] = __builtins__
#         eval(self.co, {}, args)  # 执行Python代码
#         return ''.join(args['stdout'])
#
#     def compile(self, template):
#         '''
#         将模板转换为可执行的Python代码
#         '''
#
#         def code_str(level, line, value):  # 可直接输出的字符串
#             value = "".join(value)
#             value = value.replace("'", "\'").replace('\\', '\\\\')
#             return '    ' * level + "stdout.append(r'''%s''')" % value
#
#         def code_print(level, line, value):  # {{...}}中的内容，需要执行代码后取得字符串再输出
#             return '    ' * level + "stdout.append(str(%s)) # Line: %d" % (value.strip(), line)
#
#         def code_raw(level, line, value):  # 以%开头，需要作为代码执行
#             return '    ' * level + value.strip() + ' # Line: %d' % line
#
#         level = 0  # 缩进深度
#         ln = 0  # 行号（无具体作用，方便定位问题）
#         sbuffer = []  # 模板中的普通字符串
#         for line in template.splitlines(True):
#             ln += 1
#             # Line with block starting code
#             m = self.re_block.match(line)
#             if m:
#                 if sbuffer:
#                     yield code_str(level, ln, sbuffer)
#                     sbuffer = []
#                 if m.group(2).strip().lower() in ('elif', 'else', 'except', 'finally'):
#                     if level == 0:
#                         raise TemplateError('Unexpected end of block in line %d' % ln)
#                     level -= 1
#                 yield code_raw(level, ln, m.group(1).strip())
#                 level += 1
#                 continue
#             # Line with % end marker
#             m = self.re_end.match(line)
#             if m:
#                 if sbuffer:
#                     yield code_str(level, ln, sbuffer)
#                     sbuffer = []
#                 if level == 0:
#                     raise TemplateError('Unexpected end of block in line %d' % ln)
#                 level -= 1
#                 continue
#             # Line with % marker
#             m = self.re_code.match(line)
#             if m:
#                 yield code_raw(level, ln, m.group(1).strip())
#                 continue
#             # Line with inline code
#             lasts = 0
#             for m in self.re_inc.finditer(line):
#                 sbuffer.append(line[lasts:m.start(0)])
#                 yield code_str(level, ln, sbuffer)
#                 sbuffer = []
#                 lasts = m.end(0)
#                 yield code_print(level, ln, m.group(1))
#             if lasts:
#                 sbuffer.append(line[lasts:])
#                 continue
#             # Stupid line
#             sbuffer.append(line)
#
#         if sbuffer:
#             yield code_str(level, ln, sbuffer)

import functools
import os
import re
import warnings
from collections.abc import MutableMapping

from Scripts.bottle import TemplateError

from brick.core.httphelper.response import HTTPError
from brick.utils.cachehelper import cached_property
from brick.utils.encode import tounicode
from brick.utils.htmlescape import html_escape

# './' 代表当前所在目录下的某个文件夹或文件
TEMPLATE_PATH = ['./', './views/']
TEMPLATES = {}


class BaseTemplate(object):
    """ 模板适配器的基类和最小API"""
    extensions = ['tpl', 'html', 'thtml', 'stpl']  # 扩展名
    settings = {}  # used in prepare()
    defaults = {}  # used in render()

    def __init__(self, source=None, name=None, lookup=[], encoding='utf8', **settings):
        """ 创建新模板。
            如果缺少源参数（str或buffer），则name参数用于猜测模板文件名。子类可以假设
            自身来源和/或self.filename文件名已设置。两者都是弦。查找、编码和设置参数存储为实例
            变量。lookup参数存储包含目录路径的列表。编码参数应用于解码字节字符串或文件。
            settings参数包含特定于引擎设置的dict.
        """
        self.name = name
        self.source = source.read() if hasattr(source, 'read') else source
        self.filename = source.filename if hasattr(source, 'filename') else None
        self.lookup = [os.path.abspath(x) for x in lookup]  # os.path.abspath(path)	返回绝对路径
        self.encoding = encoding
        # b = a.copy(): 浅拷贝, a 和 b 是一个独立的对象，但他们的子对象还是指向统一对象（是引用）。
        # https://www.runoob.com/w3cnote/python-understanding-dict-copy-shallow-or-deep.html
        self.settings = self.settings.copy()  # Copy from class variable 从类变量复制
        self.settings.update(settings)  # Apply
        if not self.source and self.name:
            self.filename = self.search(self.name, self.lookup)
            if not self.filename:
                raise TemplateError('Template %s not found.' % repr(name))
        if not self.source and not self.filename:
            raise TemplateError('No template specified.')
        self.prepare(**self.settings)

    @classmethod
    def search(cls, name, lookup=[]):  # cls在静态方法中使用，并通过cls()方法来实例化一个对象。
        """在查找中指定的所有目录中搜索名称。没有，然后有共同的扩展。返回第一次命中. """
        if not lookup:
            warnings.warn('The template lookup path list should not be empty.')  # 0.12
            lookup = ['.']
        # isabs(path)判断是否为绝对路径isfile(path)判断路径是否为文件
        if os.path.isabs(name) and os.path.isfile(name):
            warnings.warn('Absolute template path names are deprecated.')  # 0.12
            return os.path.abspath(name)

        for spath in lookup:
            # os.sep系统路径中的分隔符Windows系统通过是“\\”，
            # Linux类系统如Ubuntu的分隔符是“/”，而苹果Mac OS系统中是“:”。
            spath = os.path.abspath(spath) + os.sep
            # os.path.join(path1[, path2[, ...]])    把目录和文件名合成一个路径
            fname = os.path.abspath(os.path.join(spath, name))
            if not fname.startswith(spath): continue
            if os.path.isfile(fname): return fname
            for ext in cls.extensions:
                if os.path.isfile('%s.%s' % (fname, ext)):
                    return '%s.%s' % (fname, ext)

    @classmethod
    def global_config(cls, key, *args):
        """ 这将读取或设置存储在中的全局设置类设置. """
        if args:
            cls.settings = cls.settings.copy()  # 使设置成为类的本地设置
            cls.settings[key] = args[0]
        else:
            return cls.settings[key]

    def prepare(self, **options):
        """ 运行准备（解析、缓存等）。应该可以再次调用它来刷新模板或更新设置。
        """
        raise NotImplementedError

    def render(self, *args, **kwargs):
        """ 使用指定的局部变量呈现模板并返回单字节或unicode字符串。如果是字节字符串，则编码必须匹配自我编码.
         此方法必须是线程安全的！局部变量可以在字典（arg）中提供或者直接作为关键字（kwargs）。
        """
        raise NotImplementedError


class SimpleTemplate(BaseTemplate):

    def prepare(self, escape_func=html_escape, noescape=False, syntax=None, html_escape=None, **ka):
        """ 运行准备（解析、缓存等）。应该可以再次调用它来刷新模板或更新设置。
                """
        self.cache = {}
        enc = self.encoding
        self._str = lambda x: tounicode(x, enc)
        self._escape = lambda x: escape_func(tounicode(x, enc))
        self.syntax = syntax
        if noescape:
            self._str, self._escape = self._escape, self._str

    @cached_property
    def co(self):
        #  compile() 函数将一个字符串编译为字节代码。
        #  https://www.runoob.com/python/python-func-compile.html
        return compile(self.code, self.filename or '<string>', 'exec')  # 编译为字节代码对象

    @cached_property
    def code(self):
        source = self.source
        if not source:
            # open()函数用于打开一个文件，创建一个file对象，相关的方法才可以调用它进行读写。
            # rb 以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。这是默认模式。
            # 一般用于非文本文件如图片等。
            with open(self.filename, 'rb') as f:
                source = f.read()
        try:
            source, encoding = tounicode(source), 'utf8'
        except UnicodeError:
            warnings.warn('Template encodings other than utf8 are no longer supported.')  # 0.11
            source, encoding = tounicode(source, 'latin1'), 'latin1'
        parser = StplParser(source, encoding=encoding, syntax=self.syntax)
        code = parser.translate()
        self.encoding = parser.encoding
        print('code:', code)
        return code

    def _rebase(self, _env, _name=None, **kwargs):
        # if _name is None:
        warnings.warn('Rebase function called without arguments.'
                      ' You were probably looking for {{base}}?', True)  # 0.12
        _env['_rebase'] = (_name, kwargs)

    def _include(self, _env, _name=None, **kwargs):
        # if _name is None:
        warnings.warn('Rebase function called without arguments.'
                      ' You were probably looking for {{base}}?', True)  # 0.12
        env = _env.copy()
        env.update(kwargs)
        if _name not in self.cache:
            self.cache[_name] = self.__class__(name=_name, lookup=self.lookup)
        # 实例调用__class__属性时会指向该实例对应的类，然后可以再去调用其它类属性__class_()实例
        return self.cache[_name].execute(env['_stdout'], env)

    def execute(self, _stdout, kwargs):
        env = self.defaults.copy()
        env.update(kwargs)
        env.update({'_stdout': _stdout, '_printlist': _stdout.extend,
                    'include': functools.partial(self._include, env),
                    'rebase': functools.partial(self._rebase, env), '_rebase': None,
                    '_str': self._str, '_escape': self._escape, 'get': env.get,
                    'setdefault': env.setdefault, 'defined': env.__contains__})
        # extend() 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）。
        # 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）。
        # functools.partial偏函数的作用就是部分使用某个函数，即冻结住某个函数的某些参数，
        # 让它们保证为某个值，并生成一个可调用的新函数对象，这样你就能够直接调用该新对象，
        # 并且仅用使用很少的参数
        # __contains__(key) 替代字典(Dictionary) has_key() 函数
        eval(self.co, env)  # eval() 函数用来执行一个字符串表达式，并返回表达式的值。
        # print( 'eval(self.co, env):', eval(self.co, env))
        if env.get('_rebase'):
            subtpl, rargs = env.pop('_rebase')
            rargs['base'] = ''.join(_stdout)  # copy stdout
            del _stdout[:]  # clear stdout
            return self._include(env, subtpl, **rargs)
        # return env

    def render(self, *args, **kwargs):
        """使用关键字参数作为局部变量呈现模板。 使用指定的局部变量呈现模板并返回单字节或unicode字符串。
        如果是字节字符串，则编码必须匹配自我编码此方法必须是线程安全的！局部变量可以在字典（arg）中提供或者直接作为关键字（kwargs）。"""
        env = {}
        stdout = []
        # print('args', args)
        # print('kwargs', kwargs)
        for dictarg in args: env.update(dictarg)  # args ({'name': 'a', 'dictarg': 'a'},)
        env.update(kwargs)
        self.execute(stdout, env)  # 执行Python代码
        print("stdout:", stdout)
        print("join(stdout):", ''.join(stdout))
        return ''.join(stdout)


class StplParser(object):
    """ stpl模板的解析器。 """
    _re_cache = {}  #: Cache for compiled re patterns已编译模式的缓存
    # This huge pile of voodoo magic splits python code into 8 different tokens.
    # 1: All kinds of python strings (trust me, it works)
    # 将python代码分成8个不同的标记。
    # 字符串前加u后面字符串以 Unicode 格式 进行编码，一般用在中文字符串前面，防止因为源码储存格式问题，导致再次使用时出现乱码。
    # 'r'是防止字符转义的， 如果字符串中出现'\n'的话 ，不加r的话，\n就会被转义成换行符,而加了'r'之后'\n'就能保留原有的样子。
    # 字符串前加 b表示后面字符串是bytes 类型。
    _re_tok = '([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}' \
              '|\'(?:[^\\\\\']|\\\\.)+?\'|"(?:[^\\\\"]|\\\\.)+?"' \
              '|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}' \
              '|"{3}(?:[^\\\\]|\\\\.|\\n)+?"{3}))'
    _re_inl = _re_tok.replace('|\\n', '')  # 换行 (\n) We re-use this string pattern later我们稍后再使用这个字符串模式
    # 2: Comments (until end of line, but not the newline itself)注释（直到行尾，但不是换行本身）
    _re_tok += '|(#.*)'
    # 3,4: Open and close grouping tokens打开和关闭分组令牌
    _re_tok += '|([\\[\\{\\(])'
    _re_tok += '|([\\]\\}\\)])'
    # 5,6: Keywords that start or continue a python block (only start of line)
    # 开始或继续python块的关键字（仅从行开始）
    _re_tok += '|^([ \\t]*(?:if|for|while|with|try|def|class)\\b)' \
               '|^([ \\t]*(?:elif|else|except|finally)\\b)'  # ”\t”表示Tab”\b”退格
    # 7: Our special 'end' keyword (but only if it stands alone)
    # 我们的特殊“结束”关键字（但仅当它单独存在时）
    _re_tok += '|((?:^|;)[ \\t]*end[ \\t]*(?=(?:%(block_close)s[ \\t]*)?\\r?$|;|#))'  # (\r)回车
    # 8: A customizable end-of-code-block template token (only end of line)
    # 可自定义的代码块结束模板标记（仅限行结束）
    _re_tok += '|(%(block_close)s[ \\t]*(?=\\r?$))'
    # 9: And finally, a single newline. The 10th token is 'everything else'
    # 最后，一条新线。第十个标记是“其他所有”
    _re_tok += '|(\\r?\\n)'
    # Match the start tokens of code areas in a template
    # 匹配模板中代码区域的起始标记
    _re_split = '(?m)^[ \t]*(\\\\?)((%(line_start)s)|(%(block_start)s))(%%?)'  # 用%%表示一个%
    # Match inline statements (may contain python strings)
    #   匹配内联语句（可能包含python字符串）
    #   (?m)只有在正则表达式中涉及到多行的“^”和“$”的匹配时，才使用Multiline模式。
    _re_inl = '(?m)%%(inline_start)s((?:%s|[^\'"\n]*?)+)%%(inline_end)s' % _re_inl
    _re_tok = '(?m)' + _re_tok
    # \s 匹配任何空白字符，包括空格、制表符、换页符等等。\S匹配任何非空白字符，包括换行。
    # \t 匹配一个制表符。
    default_syntax = '<% %> % {{ }}'

    def __init__(self, source, syntax=None, encoding='utf8'):
        self.source, self.encoding = tounicode(source, encoding), encoding
        self.set_syntax(syntax or self.default_syntax)
        self.code_buffer, self.text_buffer = [], []
        self.lineno, self.offset = 1, 0
        self.indent, self.indent_mod = 0, 0
        self.paren_depth = 0

    def get_syntax(self):
        """ 作为空格分隔字符串的标记（默认值：<%%>%{{}}） """
        return self._syntax

    def set_syntax(self, syntax):
        self._syntax = syntax
        self._tokens = syntax.split()
        if not syntax in self._re_cache:
            names = 'block_start block_close line_start inline_start inline_end'
            # map() 会根据提供的函数对指定序列做映射，返新列表。
            # https://www.runoob.com/python/python-func-map.html
            etokens = map(re.escape, self._tokens)  # re.escape()函数实现去除转义字符
            # etokens: ['<%', '%>', '%', '\\{\\{', '\\}\\}']
            # print('etokens: ', list(etokens))  # etokens:  <map object at 0x02C29388>
            # zip() 函数用于将可迭代的对象作为参数，将对象中对应的元素打包成一个个元组，然后返回由这些元组组成的列表。
            # dict() 函数用于创建一个字典。
            # print(' zip(names.split(), etokens) : ', list(zip(names.split(), list(etokens).))
            # zip(names.split(), etokens): [('block_start', '<%'), ('block_close', '%>'), ('line_start', '%'),
            #                                ('inline_start', '\\{\\{'), ('inline_end', '\\}\\}')]
            pattern_vars = dict(zip(names.split(), etokens))
            # pattern_vars: {'block_start': '<%', 'block_close': '%>', 'line_start': '%', 'inline_start': '\\{\\{',
            #                'inline_end': '\\}\\}'}
            patterns = (self._re_split, self._re_tok, self._re_inl)
            # patterns:  ('(?m)^[ \t]*(\\\\?)((%(line_start)s)|(%(block_start)s))(%%?)', '
            # (?m)([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}|\'(?:[^\\\\\']|\\\\.)+?\'
            # |"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}|"{3}(?:[^\\\\]
            # |\\\\.|\\n)+?"{3}))|(#.*)|([\\[\\{\\(])|([\\]\\}\\)])|^([ \\t]*(?:if|for
            # |while|with|try|def|class)\\b)|^([ \\t]*(?:elif|else|except|finally)\\b)
            # |((?:^|;)[ \\t]*end[ \\t]*(?=(?:%(block_close)s[ \\t]*)?\\r?$|;|#))
            # |(%(block_close)s[ \\t]*(?=\\r?$))|(\\r?\\n)', '(?m)%(inline_start)s
            # ((?:([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}|\'(?:[^\\\\\']|\\\\.)+?\'
            # |"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.)+?\'{3}|"{3}(?:[^\\\\]
            # |\\\\.)+?"{3}))|[^\'"\n]*?)+)%(inline_end)s')

            # print(' pattern_vars : %s ' % pattern_vars)
            # print(' patterns: ', patterns)

            # for p1 in patterns:
            #     print(' p % pattern_vars:  ', p1 % pattern_vars)
            # p % pattern_vars: (?m) ^ [ ]* (\\?)((%) | (< %))( %?)
            # p % pattern_vars: (?m)([urbURB]?(
            #     ?:''(?!')|""(?!")|'{6} | "{6}|'(?:[^\\']|\\.)+?'|"(?:[^ \\"]|\\.)+?" | '{3}(?:[^\\]|\\.|\n)+?'{3} | "{3}(?:[^\\]|\\.|\n)+?"{3})) | (
            #     # .*)|([\[\{\(])|([\]\}\)])|^([ \t]*(?:if|for|while|with|try|def|class)\b)|^([ \t]*(?:elif|else|except|finally)\b)|((?:^|;)[ \t]*end[ \t]*(?=(?:%>[ \t]*)?\r?$|;|#))|(%>[ \t]*(?=\r?$))|(\r?\n)
            #         p % pattern_vars:   (?m)\{\{((
            #     ?:([urbURB]?(?:''(?!')|""(?!")|'{6} | "{6}|'(?:[^\\']|\\.)+?'|"(?:[^ \\"]|\\.)+?" | '{3}(?:[^\\]|\\.)+?'{3} | "{3}(?:[^\\]|\\.)+?"{3})) | [ ^ '"
            # ] * ?)+)\}\}
            patterns = [re.compile(p % pattern_vars) for p in patterns]
            # print(self._re_tok % pattern_vars)
            # print(re.compile(self._re_tok % pattern_vars))
            self._re_cache[syntax] = patterns
        self.re_split, self.re_tok, self.re_inl = self._re_cache[syntax]

    syntax = property(get_syntax, set_syntax)

    def translate(self):
        if self.offset: raise RuntimeError('Parser is a one time instance.')
        while True:
            m = self.re_split.search(self.source[self.offset:])  # re_split以%为界将文本进行分割
            # print('re_split:', self.re_split)
            # re_split = re.compile('(?m)^[ \t]*(\\\\?)((%)|(<%))(%?)', re.MULTILINE)
            if m:
                text = self.source[self.offset:self.offset + m.start()]  # #取得普通文本
                self.text_buffer.append(text)  # 将普通html代码存入text_buffer
                self.offset += m.end()
                print(' m:', m)
                print('m.start():', m.start())
                print('m.start(1):', m.start(1))
                if m.group(1):  # New escape syntax新转义语法
                    line, sep, _ = self.source[self.offset:].partition('\n')
                    # partition() 方法用来根据指定的分隔符将字符串进行分割，如果字符串包含指定的分隔符，
                    # 则返回一个3元的元组，第一个为分隔符左边的子串，第二个为分隔符本身，第三个为分隔符右边的子串。
                    self.text_buffer.append(m.group(2) + m.group(5) + line + sep)
                    self.offset += len(line + sep) + 1
                    print('TRtext_buffer1:', self.text_buffer)
                    continue
                elif m.group(5):  # Old escape syntax
                    warnings.warn('Escape code lines with a backslash.')  # 0.12
                    line, sep, _ = self.source[self.offset:].partition('\n')
                    self.text_buffer.append(m.group(2) + line + sep)
                    self.offset += len(line + sep) + 1
                    continue
                print('TRtext_buffer:', self.text_buffer)
                self.flush_text()  # #在%之前的text中搜索inline code并存入code_buffer
                self.read_code(multiline=bool(m.group(4)))  # 解析%当行的code并存入code_buffer
            else:
                break
        print('TRtext_buffer1:', self.text_buffer)
        self.text_buffer.append(self.source[self.offset:])
        print('TRtext_buffer2:', self.text_buffer)
        self.flush_text()
        return ''.join(self.code_buffer)

    def read_code(self, multiline):
        code_line, comment = '', ''
        # print('re_tok: ', self.re_tok)
        # print('_tokens[1]: ', self._tokens[1])
        # re_tok = re.compile(
        #         '(?m)([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}|\'(?:[^\\\\\']|\\\\.)+?\''
        #         '|"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}|"{3}(?:[^\\\\]'
        #         '|\\\\.|\\n)+?"{3}))|(#.*)|([\\[\\{\\(])|([\\]\\}\\)])|^([ \t]*(?:if|for'
        #         '|while|with|try|def|class)\b)|^([ \t]*(?:elif|else|except|finally)\b)|((?:^'
        #         '|;)[ \t]*end[ \t]*(?=(?:%>[ \t]*)?\r?$|;|#))|(%>[ \t]*(?=\r?$))|(\r?\n)'
        #         '', re.MULTILINE)
        while True:
            m = self.re_tok.search(self.source[self.offset:])
            if not m:
                code_line += self.source[self.offset:]
                print(' read_code_line1:', code_line)
                self.offset = len(self.source)
                self.write_code(code_line.strip(), comment)
                return
            print('read_code m:', m)
            code_line += self.source[self.offset:self.offset + m.start()]
            print(' read_code_line:', code_line)
            self.offset += m.end()
            print(' read_code m.groups():', m.groups())
            _str, _com, _po, _pc, _blk1, _blk2, _end, _cend, _nl = m.groups()
            if (code_line or self.paren_depth > 0) and (_blk1 or _blk2):  # a if b else c
                code_line += _blk1 or _blk2
                print(' read_code_line1:', code_line)
                continue
            if _str:  # Python string
                code_line += _str
                print(' read_code_line2:', code_line)
            elif _com:  # Python comment (up to EOL)Python注释
                comment = _com
                print(' read_codes_tokens[1]:', self._tokens[1])
                if multiline and _com.strip().endswith(self._tokens[1]):
                    multiline = False  # Allow end-of-block in comments允许注释中的块结尾
            elif _po:  # open parenthesis左圆括号
                self.paren_depth += 1
                code_line += _po
                print(' read_code_line3:', code_line)
                print('self.paren_depth:', self.paren_depth)
            elif _pc:  # close parenthesis右圆括号
                if self.paren_depth > 0:
                    # we could check for matching parentheses here, but it's
                    # easier to leave that to python - just check counts
                    # 我们可以在这里检查匹配的括号，但是
                    # 更容易让python来处理-只需检查计数
                    self.paren_depth -= 1
                code_line += _pc
                print(' read_code_line4:', code_line)
                print('self.paren_depth1:', self.paren_depth)
            elif _blk1:  # Start-block keyword (if/for/while/def/try/...)开始块关键字（if/for/while/def/try/…）
                code_line, self.indent_mod = _blk1, -1
                self.indent += 1
                print(' read_code_line5:', code_line)
                print('read_code self.indent:', self.indent)
            elif _blk2:  # Continue-block keyword (else/elif/except/...)Continue block关键字（else/elif/除/..）
                code_line, self.indent_mod = _blk2, -1
                print(' read_code_line6:', code_line)
            elif _end:  # The non-standard 'end'-keyword (ends a block)非标准的“end”关键字（结束块）
                self.indent -= 1
            elif _cend:  # The end-code-block template token (usually '%>')结束代码块模板标记（通常为“%>”）
                if multiline:
                    multiline = False
                else:
                    code_line += _cend
                    print(' read_code_line7:', code_line)
            else:  # \n
                self.write_code(code_line.strip(), comment)
                self.lineno += 1
                code_line, comment, self.indent_mod = '', '', 0
                if not multiline:
                    break

    def flush_text(self):
        text = ''.join(self.text_buffer)
        del self.text_buffer[:]
        if not text: return
        parts, pos, nl = [], 0, '\\\n' + '  ' * self.indent
        # print('re_inl', self.re_inl)
        #  re_inl = re.compile('(?m)\\{\\{((?:([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}
        #  |\'(?:[^\\\\\']|\\\\.)+?\'|"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.)+?\'{3}
        #  |"{3}(?:[^\\\\]|\\\\.)+?"{3}))|[^\'"\n]*?)+)\\}\\}', re.MULTILINE)
        for m in self.re_inl.finditer(text):
            prefix, pos = text[pos:m.start()], m.end()  # 在%之前的text中搜索inline code将之前文本存prefix
            print('flush_textprefix:', prefix)
            if prefix:
                # splitlines() 按照行('\r', '\r\n', \n')分隔，返回一个包含各行作为元素的列表，
                # 如果参数 keepends 为 False，不包含换行符，如果为 True，则保留换行符。
                # https://www.runoob.com/python3/python3-string-splitlines.html
                parts.append(nl.join(map(repr, prefix.splitlines(True))))
                print('map:', list(map(repr, prefix.splitlines(True))))
                print('flush_textparts0:', parts)
            if prefix.endswith('\n'):
                parts[-1] += nl
                print('parts[-1]:', parts[-1])
                print('m.group(0,1,2):', m.group(0, 1, 2))
            parts.append(self.process_inline(m.group(1).strip()))
        if pos < len(text):
            prefix = text[pos:]
            lines = prefix.splitlines(True)
            print('flush_textlines:', lines)
            if lines[-1].endswith('\\\\\n'):
                lines[-1] = lines[-1][:-3]
                print('flush_textlines1:', lines[-1])
            elif lines[-1].endswith('\\\\\r\n'):
                lines[-1] = lines[-1][:-4]
                print('flush_textlines2:', lines[-1])
            parts.append(nl.join(map(repr, lines)))
            print('flush_textparts1:', parts)
        code = '_printlist((%s,))' % ', '.join(parts)
        print('flush_text self.indent:', self.indent)
        print('flush_textcode:', code)
        self.lineno += code.count('\n') + 1
        print('self.lineno:', self.lineno)
        self.write_code(code)

    def process_inline(self, chunk):
        """检测 '!'是否需要转换"""
        if chunk[0] == '!': return '_str(%s)' % chunk[1:]
        return '_escape(%s)' % chunk

    def write_code(self, line, comment=''):
        line, comment = self.fix_backward_compatibility(line, comment)
        code = '  ' * (self.indent + self.indent_mod)
        code += line.lstrip() + comment + '\n'
        print(' write_code:', code)
        self.code_buffer.append(code)
        print('code_buffer:', self.code_buffer)

    def fix_backward_compatibility(self, line, comment):
        parts = line.strip().split(None, 2)
        print('parts1ine:', parts)
        if parts and parts[0] in ('include', 'rebase'):
            warnings.warn('The include and rebase keywords are functions now.')  # 0.12
            if len(parts) == 1:
                return "_printlist([base])", comment
            elif len(parts) == 2:
                return "_=%s(%r)" % tuple(parts), comment
            else:
                return "_=%s(%r, %s)" % tuple(parts), comment
        if self.lineno <= 2 and not line.strip() and 'coding' in comment:
            m = re.match(r"#.*coding[:=]\s*([-\w.]+)", comment)
            if m:
                warnings.warn('PEP263 encoding strings in template are deprecated.')  # 0.12
                enc = m.group(1)
                self.source = self.source.encode(self.encoding).decode(enc)
                self.encoding = enc
                return line, comment.replace('coding', 'coding*')
        return line, comment


DEBUG = True


# 单星号（*）：*agrs将所有参数以元组(tuple)的形式导入(1,2,3,4,5)->1,(2,3,4,5)
# **kwargs双星号（**）将参数以字典的形式导入(1,a=2,b=3)->1 ,{'a': 2, 'b': 3}
def template(*args, **kwargs):
    """    获取作为字符串迭代器的呈现模板。可以使用名称、文件名或模板字符串作为第一个参数。
        模板呈现参数可以作为字典传递或者直接（作为关键字参数）。
    """
    tpl = args[0] if args else None
    print('args:', args)
    # 字典 pop() 方法删除字典给定键 key 及对应的值，返回值为被删除的值。
    # key 值必须给出。 否则，返回 default 值。
    adapter = kwargs.pop('template_adapter', SimpleTemplate)
    lookup = kwargs.pop('template_lookup', TEMPLATE_PATH)
    # id() 函数返回对象的唯一标识符，标识符是一个整数。
    # CPython 中 id() 函数用于获取对象的内存地址。
    tplid = (id(lookup), tpl)
    if tplid not in TEMPLATES or DEBUG:
        settings = kwargs.pop('template_settings', {})
        if isinstance(tpl, adapter):
            TEMPLATES[tplid] = tpl
            if settings: TEMPLATES[tplid].prepare(**settings)
        elif "\n" in tpl or "{" in tpl or "%" in tpl or '$' in tpl:
            TEMPLATES[tplid] = adapter(source=tpl, lookup=lookup, **settings)
        else:
            TEMPLATES[tplid] = adapter(name=tpl, lookup=lookup, **settings)
    if not TEMPLATES[tplid]:
        abort(500, 'Template (%s) not found' % tpl)
    for dictarg in args[1:]:
        print('dictarg:', dictarg)
        if isinstance(dictarg, dict):
            kwargs.update(dictarg)
        print('kwargs:', kwargs)
    # tp =TEMPLATES[tplid].render(kwargs)
    # return tp,print('TEMPLATES[tplid].render(kwargs):', tp)
    return TEMPLATES[tplid].render(kwargs)


def abort(code=500, text='Unknown Error.'):
    """ Aborts execution and causes a HTTP error. """
    raise HTTPError(code, text)


def view(tpl_name, **defaults):
    """ Decorator：呈现处理程序的模板。处理程序可以这样控制其行为：-返回模板变量的dict以填写模板
    -返回dict以外的内容，视图装饰器将不会返回处理模板，但按原样返回处理程序结果。
    这包括返回HTTPResponse（dict）以获取，例如，带有autojson或其他castfilter的JSON。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, (dict, MutableMapping)):
                tplvars = defaults.copy()
                # 字典 update() 函数把字典参数 dict2 的 key/value(键/值) 对更新到字典 dict 里。
                tplvars.update(result)
                return template(tpl_name, **tplvars)
            elif result is None:
                return template(tpl_name, defaults)
            return result

        return wrapper

    return decorator


def testmod():
    pattern_vars = {'block_start': '<%', 'block_close': '%>', 'line_start': '%', 'inline_start': '\\{\\{',
                    'inline_end': '\\}\\}'}
    # pattern1 = '(?m)^[ \t]*(\\\\?)((%(line_start)s)|(%(block_start)s))(%%?)'
    # pattern2 = """(?m)([urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}|\'(?:[^\\\\\']|\\\\.)+?\'|"(?:[^\\\\"]|\\\\.)+?"|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}|"{3}(?:[^\\\\]|\\\\.|\\n)+?"{3}))|(#.*)|([\\[\\{\\(])|([\\]\\}\\)])|^([ \\t]*(?:if|for|while|with|try|def|class)\\b)|^([ \\t]*(?:elif|else|except|finally)\\b)|((?:^|;)[ \\t]*end[ \\t]*(?=(?:%(block_close)s[ \\t]*)?\\r?$|;|#))|(%(block_close)s[ \\t]*(?=\\r?$))|(\\r?\\n)', '(?m)%(inline_start)s"""
    # pattern3 = '(?m) %(line_start)s'
    # print('pattern1 % pattern_vars', pattern1 % pattern_vars)
    # print('pattern2 % pattern_vars', pattern2 % pattern_vars)
    # print('pattern3 % pattern_vars', pattern3 % pattern_vars)
    # p = "(ab)c"
    # p1 = {"ab": "cd"}
    # p2 = ["acd", "acd"]
    p3 = ('abc', 'xyz')
    # print(p1, p % p1)
    # print(p2, p % p2)
    # print(p % p3)yu元组不可以
    for dictarg in p3:
        p = pattern_vars.update(dictarg)
        print(dictarg)
        print(p)


def testdict_updata():
    d = {'a': 'b', 'c': ' d'}
    d1 = {'a': 'b1', 'c': 'd'}
    d.update(d1)
    print(d)


def test_translate():
    source = """    <pre>{{e.body}}</pre>
            %%if DEBUG and e.exception:
              <h2>Exception:</h2>
              <pre>{{repr(e.exception)}}</pre>
            %%end
"""
    offset = 0
    code_buffer, text_buffer = [], []
    while True:
        re_split = re.compile('(?m)^[ \t]*(\\\\?)((%)|(<%))(%?)', re.MULTILINE)
        m = re_split.search(source[offset:])
        # print('m:', m)
        # m: < re.Match  object; span = (132, 146), match = '            %%' >
        if m:
            text = source[offset:offset + m.start()]
            text_buffer.append(text)
            # text_buffer: [ '   <p>Sorry, the requested URL <tt>{{repr(request.url)}}</tt>\n
            # caused an error:</p>\n            <pre>{{e.body}}</pre>\n']
            print('text_buffer:', text_buffer)
            offset += m.end()
            if m.group(1):  # New escape syntax新转义语法
                line, sep, _ = source[offset:].partition('\n')
                # partition() 方法用来根据指定的分隔符将字符串进行分割，如果字符串包含指定的分隔符，
                # 则返回一个3元的元组，第一个为分隔符左边的子串，第二个为分隔符本身，第三个为分隔符右边的子串。
                text_buffer.append(m.group(2) + m.group(5) + line + sep)
                print('text_buffer1:', text_buffer)
                offset += len(line + sep) + 1
                continue
            elif m.group(5):  # Old escape syntax
                warnings.warn('Escape code lines with a backslash.')  # 0.1212
                line, sep, _ = source[offset:].partition('\n')
                print('line:', line)
                text_buffer.append(m.group(2) + line + sep)
                print('text_buffer2:', text_buffer)
                offset += len(line + sep) + 1
                continue
            flush_text()
            read_code(source, offset, multiline=bool(m.group(4)))
        else:
            break


# self.text_buffer.append(self.source[self.offset:])
# self.flush_text()
# return ''.join(code_buffer)


if __name__ == "__main__":
    # test_translate()
    # testdict_updata()
    # 简单替换
    # t1 = SimpleTemplate('Hello {{name}}!')
    # print(t1.render(name='<b>World</b>'))
    # print(template('Hello {{name}}!', ' Hi{{name}}', name='a'))
    # # 嵌入python语句（必须返回str）
    # t2 = SimpleTemplate('Hello {{name.title() if name else "stranger"}}!')
    # print(t2.render(name=None))
    # print(t2.render(name="tuzkee"))
    #
    # # %执行Python语句
    #     tmp3 = """<p>More plain text</p>
    #              % name = "Bob"  # a line of python code
    #      <p>Some plain text in between</p>
    #
    # <ul>
    # <li>
    # {{name}}
    #      </li>
    #  </ul>
    # """
    # print(template(tmp3))
    # t3 = SimpleTemplate(tmp3)
    # print(t3.render(name=None))
    #
    # tmp4 = """
    # %for i in range(3):
    # %for j in range(3):
    #     {{"%s:%s"%(i,j)}}
    # %end
    # %end"""
    # t4 = SimpleTemplate(tmp4)
    # print(t4.render())
    # testmod()
    message = """% name = "aBobc"  # a line of python code
<p>Some plain text in between</p>
<%
  # A block of python code
  name = name.strip("B"  if name else "o")
%>
         <p><img src="/images/linuxyw.png"></img></p>
     <p>Some plain text in between</p>
        %for i in range(3):
        %for j in range(3):
            {{"%s:%s"%(i,j)}}
        %end
        %end  
<%
  # A block of python code
  name = name.title().strip()
%>
<ul>
<li>
{{name if name else "stranger"}}
     </li>
 </ul>
"""
    t5 = SimpleTemplate(message)
    print(t5.render())
