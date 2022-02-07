#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:38
# @Author  : CJ  Mao
# @Site    : 
# @File    : wsgiapp.py
# @Project : mysite_diy
# @Software: PyCharm

import functools
import itertools
import mimetypes
import os
import subprocess
import sys
import time
from _thread import interrupt_main
from inspect import signature, getargspec, getfullargspec
from threading import Thread
from traceback import print_exc, format_exc

from webcore.apps.utilities import _closeiter, makelist, WSGIFileWrapper

from webcore.httphandles.request import localrequest
from webcore.httphandles.response import localresponse, HTTPError, HTTPResponse, parse_date
from webcore.routes.routeerror import RouteReset

from webcore.routes.router import Router
from webcore.routes.route import Route
from webcore.servers.baseserver import WSGIRefServer
from webcore.templates.simpletemplate import template
from webcore.utilities.cachehelper import cached_property
from webcore.utilities.dicthelper import DictProperty, ConfigDict
from webcore.utilities.encode import tobytes
from webcore.utilities.htmlescape import html_escape
from webcore.utilities.loadhelper import load_module, load_app
from webcore.utilities.sysinfo import _e


def yieldroutes(func):
    """返回与签名（name，args）匹配的路由的生成器func参数的。如果函数
     接受可选的关键字参数。最好用以下示例来描述输出：
      a()         -> '/a'
        b(x, y)     -> '/b/<x>/<y>'
        c(x, y=5)   -> '/c/<x>' and '/c/<x>/<y>'
        d(x=5, y=6) -> '/d' and '/d/<x>' and '/d/<x>/<y>'"""
    path = '/' + func.__name__.replace('__', '/').lstrip('/')  # lstrip() 方法用于截掉字符串左边的空格或指定字符。
    spec = getfullargspec(func)
    argc = len(spec[0]) - len(spec[3] or [])
    path += ('/<%s>' * argc) % tuple(spec[0][:argc])
    yield path
    for arg in spec[0][argc:]:
        path += '/<%s>' % arg
        yield path


class DefaultApp(object):
    def __init__(self, catchall=True, autojson=True):
        self.config = ConfigDict()
        self.config['catchall'] = catchall
        self.config['autojson'] = autojson
        self.routelist = []
        self.router = Router()
        #: If true, most exceptions are caught and returned as :exc:`HTTPError`
        self.error_handler = {}
        # self.routes = []
        # Core plugins
        self.plugins = []  # List of installed plugins.
        # if self.config['autojson']:
        #     self.install(JSONPlugin())
        # self.install(TemplatePlugin())

    catchall = DictProperty('config', 'catchall')
    __hook_names = 'before_request', 'after_request', 'app_reset', 'config'
    __hook_reversed = 'after_request'

    @cached_property
    def _hooks(self):
        return dict((name, []) for name in self.__hook_names)

    def add_hook(self, name, func):
        ''' Attach a callback to a hook. Three hooks are currently implemented:

            before_request
                Executed once before each request. The request context is
                available, but no routing has happened yet.
            after_request
                Executed once after each request regardless of its outcome.
            app_reset
                Called whenever :meth:`Bottle.reset` is called.
                将回调附加到钩子。目前实施了三个挂钩：
                请求前
                在每个请求之前执行一次。请求上下文是
                可用，但尚未进行路由。
                请求后
                在每个请求之后执行一次，无论其结果如何。
                应用程序重置
                什么时候叫：冰毒：瓶子。重置`被调用。
        '''
        if name in self.__hook_reversed:
            self._hooks[name].insert(0, func)
        else:
            self._hooks[name].append(func)

    def remove_hook(self, name, func):
        ''' Remove a callback from a hook. 从钩子中移除回调。'''
        if name in self._hooks and func in self._hooks[name]:
            self._hooks[name].remove(func)
            return True

    def trigger_hook(self, __name, *args, **kwargs):
        ''' Trigger a hook and return a list of results.
         触发钩子并返回结果列表 '''
        return [hook(*args, **kwargs) for hook in self._hooks[__name][:]]

    def hook(self, name):
        """ Return a decorator that attaches a callback to a hook. See
            :meth:`add_hook` for details.
            返回将回调附加到挂钩的装饰器。看见：meth:'add_hook'了解详细信息。"""

        def decorator(func):
            self.add_hook(name, func)
            return func

        return decorator

    def _handle(self, environ):
        path = environ['webcore.raw_path'] = environ['PATH_INFO']
        try:
            environ['PATH_INFO'] = path.encode('latin1').decode('utf8')  # latin-1就是ISO-8859-1的别名
        except UnicodeError:
            return HTTPError(400, 'Invalid path string. Expected UTF-8')
        try:
            environ['webcore.app'] = self
            localrequest.bind(environ)
            localresponse.bind()
            try:
                # self.trigger_hook('before_request')
                route, args = self.router.match(environ)
                # print("routes：%s" % route)
                environ['route.handle'] = route
                environ['webcore.route'] = route
                environ['route.url_args'] = args
                return route.call(**args)
            except UnicodeError:
                pass
            # finally:
            # self.trigger_hook('after_request')
        except HTTPResponse:
            return _e()
        except RouteReset:
            route.reset()
            return self._handle(environ)
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            stacktrace = format_exc()
            environ['wsgi.errors'].write(stacktrace)
            return HTTPError(500, "Internal Server Error", _e(), stacktrace)

    def install(self, plugin):
        ''' Add a plugin to the list of plugins and prepare it for being
            applied to all routes of this application. A plugin may be a simple
            decorator or an object that implements the :class:`Plugin` API.
        '''
        if hasattr(plugin, 'setup'): plugin.setup(self)
        if not callable(plugin) and not hasattr(plugin, 'apply'):
            raise TypeError("Plugins must be callable or implement .apply()")
        self.plugins.append(plugin)
        self.reset()
        return plugin

    def uninstall(self, plugin):
        ''' Uninstall plugins. Pass an instance to remove a specific plugin, a type
            object to remove all plugins that match that type, a string to remove
            all plugins with a matching ``name`` attribute or ``True`` to remove all
            plugins. Return the list of removed plugins. '''
        removed, remove = [], plugin
        for i, plugin in list(enumerate(self.plugins))[::-1]:
            if remove is True or remove is plugin or remove is type(plugin) \
                    or getattr(plugin, 'name', True) == remove:
                removed.append(plugin)
                del self.plugins[i]
                if hasattr(plugin, 'close'): plugin.close()
        if removed: self.reset()
        return removed

    def _cast(self, out):
        """  尝试将参数转换为WSGI兼容的内容并设置如果可能，请更正HTTP头。
               支持：False、str、unicode、dict、HTTPResponse、HTTPError、file-like，
               字符串的iterable和Unicode的iterable
               """
        # Empty output is done here
        if not out:
            if 'Content-Length' not in localresponse:
                localresponse['Content-Length'] = 0
            return []
        # Join lists of byte or unicode strings. Mixed lists are NOT supported
        if isinstance(out, (tuple, list)) and isinstance(out[0], (bytes, str)):
            out = out[0][0:0].join(out)  # b'abc'[0:0] -> b'',[n:n]表示不提取元素为空
        # Encode unicode strings
        if isinstance(out, str):
            out = out.encode(localresponse.charset)
        # Byte Strings are just returned
        if isinstance(out, bytes):
            if 'Content-Length' not in localresponse:
                localresponse['Content-Length'] = len(out)
            return [out]
        # HTTPError or HTTPException (recursive, because they may wrap anything)
        # TODO: Handle these explicitly in handle() or make them iterable.
        # HTTPError或HTTPException(递归，因为它们可以包装任何东西)
        # TODO:在Handle()中显式处理这些，或者使它们可迭代。
        if isinstance(out, HTTPError):
            out.apply(localresponse)
            out = self.error_handler.get(out.status_code, self.default_error_handler)(
                out)  # 默认调用default_error_handler函数(out)作为参数
            return self._cast(out)
        if isinstance(out, HTTPResponse):
            out.apply(localresponse)
            return self._cast(out.body)
        # File-like objects.
        if hasattr(out, 'read'):
            if 'wsgi.file_wrapper' in localrequest.environ:
                return localrequest.environ['wsgi.file_wrapper'](out)
            elif hasattr(out, 'close') or not hasattr(out, '__iter__'):
                return WSGIFileWrapper(out)

        # Handle Iterables. We peek into them to detect their inner type.
        # 处理列表。我们窥视它们以发现它们的内部类型。
        try:
            iout = iter(out)  # 用来生成迭代器。
            first = next(iout)  # 当我们已经迭代完最后⼀个数据之后，再次调⽤next()函数会抛出 StopIteration的异常，来告诉我们所有数据都已迭代完成，不⽤再执⾏ next()函数了。
            while not first:  # 如果是（） [] {}等就下一个
                first = next(iout)
        except StopIteration:
            return self._cast('')
        except HTTPResponse:
            first = _e()
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            first = HTTPError(500, 'Unhandled exception', _e(), format_exc())

        # These are the inner types allowed in iterator or generator objects.
        if isinstance(first, HTTPResponse):
            return self._cast(first)
        elif isinstance(first, bytes):
            new_iter = itertools.chain([first], iout)  # Itertools.chain功能1：去除iterable里的内嵌iterable,如去除列表中的内嵌列表
        elif isinstance(first, str):
            encoder = lambda x: x.encode(localresponse.charset)
            new_iter = map(encoder, itertools.chain([first], iout))
        else:
            msg = 'Unsupported response type: %s' % type(first)
            return self._cast(HTTPError(500, msg))
        if hasattr(out, 'close'):
            new_iter = _closeiter(new_iter, out.close)
        return new_iter

    def wsgi_app(self, environ, start_response):
        # start_response('200 OK', [('Content-Type', 'text/html')])
        # path = environ['PATH_INFO'].encode('latin1')  # .decode('utf8')
        # body = '<h1>Hello, %s!</h1>' % path[1:] or 'web'
        # return [body.encode()]
        # response_body = "Hello, %s!" % environ['PATH_INFO'][1:].encode('latin1') or 'web'
        # status = "200 OK"
        # start_response(status, headers=[])
        # return iter([response_body.encode('utf-8')])
        try:
            out = self._cast(self._handle(environ))
            if localresponse._status_code in (100, 101, 204, 304) \
                    or environ['REQUEST_METHOD'] == 'HEAD':
                if hasattr(out, 'close'): out.close()
                out = []
            start_response(localresponse._status_line, localresponse.headerlist)
            return out
        except (KeyboardInterrupt, SystemExit, MemoryError):
            raise
        except Exception:
            if not self.catchall: raise
            err = '<h1>Critical error while processing request: %s</h1>' \
                  % html_escape(environ.get('PATH_INFO', '/'))
            err += '<h2>Error:</h2>\n<pre>\n%s\n</pre>\n' \
                   '<h2>Traceback:</h2>\n<pre>\n%s\n</pre>\n' \
                   % (html_escape(repr(_e())), html_escape(format_exc()))
            environ['wsgi.errors'].write(err)
            headers = [('Content-Type', 'text/html; charset=UTF-8')]
            start_response('500 INTERNAL SERVER ERROR', headers, sys.exc_info())
            return [tobytes(err)]

    def __call__(self, environ, start_response):
        """每个实例都是一个WSGI应用程序。"""
        return self.wsgi_app(environ, start_response)
        # response_body = b"Hello, World!"
        # status = "200 OK"
        # start_response(status, headers=[])
        # return iter([response_body])
        # self.wsgi_app(environ, start_response)

    def run(self, **kwargs):
        server_run(**kwargs)

    def route(self, path=None, method='GET', callback=None, name=None,
              apply=None, skip=None, **config):
        """     将函数绑定到请求URL的修饰程序。例子：：@应用程序路由（'/hello/：name'）
                def hello（name）：返回'Hello%s'%name“name”部分是通配符。语法请参见：
                类：`Router`细节。：param path：请求路径或要侦听的路径列表。如果没有路径
                是指定的，它是从函数的签名。：param method:HTTP方法（`GET`，`POST`，`PUT`，…）
                或听的方法。（默认值：“GET”）：param callback：避免decorator的可选快捷方式语
                法。``route（…，callback=func）``equals``路由（…）（func）：param name:此路由
                的名称。（默认值：无）：param apply：一个装饰器或插件或插件列表。这些是除了已安
                装的插件外，还应用于路由回调。：param skip：插件、插件类或名称的列表。匹配插件未
                安装到此路由。``真的``全部跳过。任何其他关键字参数都存储为路由特定的配置并传递给
                插件（请参阅：meth:`Plugin.apply插件`).
            """
        if callable(path): path, callback = None, path  # callable(path)path是字符串是 false

        def decorator(func):
            # TODO: Documentation and tests
            if isinstance(func, str):
                func = load_module(func)
            for rule in makelist(path) or yieldroutes(func):
                for verb in makelist(method):
                    verb = verb.upper()
                    route = Route(self, rule, verb, func, name=name, **config)
                    self.add_route(route)
            return func

        return decorator(callback) if callback else decorator

    def add_route(self, route):
        self.routelist.append(route)
        self.router.add(route.rule, route.method, route, name=route.name)

    @staticmethod
    def default_error_handler(res):
        return tobytes(template(ERROR_PAGE_TEMPLATE, e=res))

    # class AppStack(list):
    #     """ 一个堆叠的列表。调用它将返回堆栈的头. """
    #
    #     def __call__(self):
    #         """返回当前默认应用程序。 """
    #         return self[-1]
    #
    #     def push(self, value=None):
    #         """ 向堆栈添加一个新的：class:`bDefaultApp`实例 """
    #         if not isinstance(value, DefaultApp):
    #             value = DefaultApp()
    #         self.append(value)
    #         return value
    #
    #
    # default_app = AppStack()
    # default_app.push()


def static_file(filename, root, mimetype='auto', download=False, charset='UTF-8'):
    """ Open a file in a safe way and return :exc:`HTTPResponse` with status
        code 200, 305, 403 or 404. The ``Content-Type``, ``Content-Encoding``,
        ``Content-Length`` and ``Last-Modified`` headers are set if possible.
        Special support for ``If-Modified-Since``, ``Range`` and ``HEAD``
        requests.

        :param filename: Name or path of the file to send.
        :param root: Root path for file lookups. Should be an absolute directory
            path.
        :param mimetype: Defines the content-type header (default: guess from
            file extension)
        :param download: If True, ask the browser to open a `Save as...` dialog
            instead of opening the file with the associated program. You can
            specify a custom filename as a string. If not specified, the
            original filename is used (default: False).
        :param charset: The charset to use for files with a ``text/*``
            mime-type. (default: UTF-8)
    """

    root = os.path.abspath(root) + os.sep
    filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))
    headers = dict()
    print('filename:', filename)
    if not filename.startswith(root):
        return HTTPError(403, "Access denied.")
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return HTTPError(404, "File does not exist.")
    if not os.access(filename, os.R_OK):
        return HTTPError(403, "You do not have permission to access this file.")
    # mimetypes：   主要处理文件文件类型问题
    if mimetype == 'auto':
        mimetype, encoding = mimetypes.guess_type(filename)
        if encoding: headers['Content-Encoding'] = encoding

    if mimetype:
        if mimetype[:5] == 'text/' and charset and 'charset' not in mimetype:
            mimetype += '; charset=%s' % charset
        headers['Content-Type'] = mimetype

    if download:
        download = os.path.basename(filename if download == True else download)
        headers['Content-Disposition'] = 'attachment; filename="%s"' % download

    stats = os.stat(filename)
    headers['Content-Length'] = clen = stats.st_size
    lm = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime))
    headers['Last-Modified'] = lm

    ims = localrequest.environ.get('HTTP_IF_MODIFIED_SINCE')
    if ims:
        ims = parse_date(ims.split(";")[0].strip())
    if ims is not None and ims >= int(stats.st_mtime):
        headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        return HTTPResponse(status=304, **headers)

    body = '' if localrequest.method == 'HEAD' else open(filename, 'rb')

    headers["Accept-Ranges"] = "bytes"
    ranges = localrequest.environ.get('HTTP_RANGE')
    if 'HTTP_RANGE' in localrequest.environ:
        ranges = list(parse_range_header(localrequest.environ['HTTP_RANGE'], clen))
        if not ranges:
            return HTTPError(416, "Requested Range Not Satisfiable")
        offset, end = ranges[0]
        headers["Content-Range"] = "bytes %d-%d/%d" % (offset, end - 1, clen)
        headers["Content-Length"] = str(end - offset)
        if body: body = _file_iter_range(body, offset, end - offset)
        return HTTPResponse(body, status=206, **headers)
    return HTTPResponse(body, **headers)


def _file_iter_range(fp, offset, bytes, maxread=1024 * 1024):
    ''' Yield chunks from a range in a file. No chunk is bigger than maxread.'''
    fp.seek(offset)
    while bytes > 0:
        part = fp.read(min(bytes, maxread))
        if not part: break
        bytes -= len(part)
        yield part


def parse_range_header(header, maxlen=0):
    ''' Yield (start, end) ranges parsed from a HTTP Range header. Skip
        unsatisfiable ranges. The end index is non-inclusive
        从HTTP范围标头解析的产量（开始、结束）范围。跳过
        无法满足的范围。结束索引是非包容性的。.'''
    if not header or header[:6] != 'bytes=': return
    ranges = [r.split('-', 1) for r in header[6:].split(',') if '-' in r]
    for start, end in ranges:
        try:
            if not start:  # bytes=-100    -> last 100 bytes
                start, end = max(0, maxlen - int(end)), maxlen
            elif not end:  # bytes=100-    -> all but the first 99 bytes
                start, end = int(start), maxlen
            else:  # bytes=100-200 -> bytes 100-200 (inclusive)
                start, end = int(start), min(int(end) + 1, maxlen)
            if 0 <= start < end <= maxlen:
                yield start, end
        except ValueError:
            pass


ERROR_PAGE_TEMPLATE = """
%%try:
    %%#from %s import DEBUG, HTTP_CODES, localrequest, tounicode
   %%from webcore.httphandles.request import localrequest
   %%DEBUG = True
    <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
    <html>
        <head>
            <title>Error: {{e.status}}</title>
            <style type="text/css">
              html {background-color: #eee; font-family: sans;}
              body {background-color: #fff; border: 1px solid #ddd;
                    padding: 15px; margin: 15px;}
              pre {background-color: #eee; border: 1px solid #ddd; padding: 5px;}
            </style>
        </head>
        <body>
            <h1>Error: {{e.status}}</h1>
            <p>Sorry, the requested URL <tt>{{repr(localrequest.environ.get('PATH_INFO', ''))}}</tt>
               caused an error:</p>
            <pre>{{e.body}}</pre>
            %%if DEBUG and e.exception:
              <h2>Exception:</h2>
              <pre>{{repr(e.exception)}}</pre>
            %%end
            %%if DEBUG and e.traceback:
              <h2>Traceback:</h2>
              <pre>{{e.traceback}}</pre>
            %%end
        </body>
    </html>
%%except ImportError:
    <b>ImportError:</b> Could not generate the error page. Please add bottle to
    the import path. %s
%%end
""" % (__name__,  __name__)


class FileCheckerThread(Thread):
    """ 一旦检测到更改的模块文件，立即中断主线程，锁文件被删除或变旧. """

    def __init__(self, interval):  # 继承自Thread类，重写了它的构造函数
        Thread.__init__(self)
        self.interval = interval
        #: Is one of 'reload', 'error' or 'exit'
        self.status = None

    def run(self):  # 继承自Thread类，重写了它的run()方法
        exists = os.path.exists  # 判断括号里的文件是否存在的意思，括号内的可以是文件路径。
        mtime = lambda path: os.stat(path).st_mtime  # st_mtime最后一次修改时间
        files = dict()

        for module in list(sys.modules.values()):  # 当某个模块第一次导入，字典sys.modules将自动记录该模块
            path = getattr(module, '__file__', '') or ''  # __file__属性：查看模块的源文件路径
            if path[-4:] in ('.pyo', '.pyc'): path = path[:-1]  # .pyc 作扩展名的文件是 python 编译文件,pyo 文件是优化编译后的程序
            if path and exists(path): files[path] = mtime(path)  # 拿到所有导入模块文件的modify time

        while not self.status:
            for path, lmtime in list(files.items()):  # items() 函数以列表返回可遍历的(键, 值) 元组数组 list() 方法用于将元组转换为列表。
                if not exists(path) or mtime(path) > lmtime:  # 如果文件发生改动
                    self.status = 'reload'
                    interrupt_main()  # raise 一个 KeyboardInterrupt exception in 主线程
                    break  # 跳出循环
            time.sleep(self.interval)

        # 当with语句在开始运行时，会在上下文管理器对象上调用 __enter__ 方法。
        # with语句运行结束后，会在上下文管理器对象上调用 __exit__ 方法

    def __enter__(self):
        self.start()  # 开始线程活动，调用它的run()方法

        # 这个地方是重新载入更新后模块的关键
        # 当检测到文件变化时，终止主线程使监听请求停止，退出上下文管理器时，如果返回True则重现异常捕获

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.status: self.status = 'exit'  # silent exit
        self.join()
        return exc_type is not None and issubclass(exc_type, KeyboardInterrupt)


def server_run(app=None, host='127.0.0.1', port=8080, interval=1, reloader=False, quiet=False,
               plugins=None, debug=None, **kargs):
    # 第一次进来的时候，必然会进这个分支，因为没有地方设置过RUN_MAIN

    if reloader and not os.environ.get("RUN_MAIN"):
        try:
            while True:
                # 其实这里会创建一个新的子进程来运行服务
                args = [sys.executable] + sys.argv  # sys.executable 是获取当前python解释器的路径
                new_environ = os.environ.copy()
                new_environ['RUN_MAIN'] = 'true'
                p = subprocess.Popen(args, env=new_environ)
                while p.poll() is None:  # Busy wait...如果返回None表示子进程未结束
                    time.sleep(interval)
                if p.poll() != 3:
                    sys.exit(p.poll())

        except KeyboardInterrupt:
            sys.exit(3)
    else:
        try:
            # app = app or DefaultApp()
            app = app or default_app
            if isinstance(app, str):
                load_app(app)
            if not callable(app):
                raise ValueError("Application is not callable: %r" % app)
            for plugin in plugins or []:
                app.install(plugin)
            server = WSGIRefServer(host=host, port=port, **kargs)
            server.quiet = server.quiet or quiet
            if not server.quiet:
                try:
                    _stdout, _stderr = sys.stdout.write, sys.stderr.write
                except IOError:
                    _stdout = lambda x: sys.stdout.write(x)
                    _stderr = lambda x: sys.stderr.write(x)
                _stderr(" server starting up (using %s)...\n" % (repr(server)))
                _stderr("Listening on http://%s:%d/   at :%s\n" % (
                    server.host, server.port, time.asctime(time.localtime())))
                _stderr("Hit Ctrl-C to quit.\n\n")
            # 当选择自动重载时，如果解释器进程已经启动
            # 则只需要检测应用相关内容有没有变化,如果有变化终止主线程并重新实现异常捕获
            if reloader:
                bgcheck = FileCheckerThread(interval)
                with bgcheck:  # 开启新线程检测文件修改，如果修改终止当前主线程，抛出异常
                    # 主线程监听请求
                    server.run(app)
                if bgcheck.status == 'reload':
                    sys.exit(3)
            else:
                server.run(app)
        except KeyboardInterrupt:
            print('quit as KeyboardInterrupt')
            sys.exit(3)
        except (SystemExit, MemoryError):

            print('quit as SystemExit ')
            raise
        except:
            if not reloader: raise
            # if not getattr(server, 'quiet', quiet):
            print_exc()
            time.sleep(interval)
            sys.exit(3)


# def make_default_app_wrapper(name, app=None):
# def make_default_app_wrapper(name):
#     """ Return a callable that relays calls to the current default app. """
#     # app = app or DefaultApp()
#     # if not isinstance(app, DefaultApp):
#     #     app = DefaultApp()
#
#     @functools.wraps(getattr(app, name))
#     def wrapper(*a, **ka):
#         return getattr(app, name)(*a, **ka)
#
#     return wrapper
#

def make_default_app_wrapper(name):
    """ Return a callable that relays calls to the current default app. """

    @functools.wraps(getattr(DefaultApp, name))
    def wrapper(*a, **ka):
        # return getattr(app(), name)(*a, **ka)
        return getattr(default_app, name)(*a, **ka)

    return wrapper


route = make_default_app_wrapper('route')

#
# class AppStack(list):
#     """ 一个堆叠的列表。调用它将返回堆栈的头. """
#
#     def __call__(self):
#         """返回当前默认应用程序。 """
#         return self[-1]
#
#     def push(self, value=None):
#         """ 向堆栈添加一个新的：class:`battle`实例 """
#         if not isinstance(value, DefaultApp):
#             value = DefaultApp()
#         self.append(value)
#         return value


default_app = DefaultApp()
# app = default_app = AppStack()
# app.push()

if __name__ == '__main__':
    from optparse import OptionParser

    _cmd_parser = OptionParser(usage="usage: %prog [options] package.module:app")
    _opt = _cmd_parser.add_option
    _opt("--version", action="store_true", help="show version number.")
    _opt("-b", "--bind", metavar="ADDRESS", help="bind socket to ADDRESS.")
    _opt("-s", "--server", default='wsgiref', help="use SERVER as backend.")
    _opt("-p", "--plugin", action="append", help="install additional plugin/s.")
    _opt("--debug", action="store_true", help="start server in debug mode.")
    _opt("--reload", action="store_true", help="auto-reload on file changes.")
    _cmd_options, _cmd_args = _cmd_parser.parse_args()
    if _cmd_options.server and _cmd_options.server.startswith('gevent'):
        import gevent.monkey;

        gevent.monkey.patch_all()
    server_run(reloader=True)
