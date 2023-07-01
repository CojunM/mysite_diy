#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:38
# @Author  : CJ  Mao
# @Site    : 
# @File    : wsgiapp.py
# @Project : mysite_diy
# @Software: PyCharm
import email
import functools
import hashlib
import itertools
import mimetypes
import os
import sys
import time
from inspect import getfullargspec
from traceback import print_exc, format_exc
from urllib.parse import urljoin

from brick.core.baseserver import WSGIRefServer, FileCheckerThread
from brick.core.httphelper.request import request
from brick.core.httphelper.response import response, HTTPError, HTTPResponse, parse_date
from brick.core.routes import Route
from brick.core.routes import Router, RouteReset
from brick.core.simpletemplate import template
from brick.utils.cachehelper import cached_property
from brick.utils.dicthelper import DictProperty, ConfigDict
from brick.utils.encode import tobytes
from brick.utils.htmlescape import html_escape
from brick.utils.loadhelper import load, load_app
from brick.utils.sysinfo import _e


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


def makelist(data):  # This is just to handy
    if isinstance(data, (tuple, list, set, dict)):
        return list(data)
    elif data:
        return [data]
    else:
        return []


class WSGIFileWrapper(object):

    def __init__(self, fp, buffer_size=1024 * 64):
        self.fp, self.buffer_size = fp, buffer_size
        for attr in ('fileno', 'close', 'read', 'readlines', 'tell', 'seek'):
            if hasattr(fp, attr): setattr(self, attr, getattr(fp, attr))

    def __iter__(self):
        buff, read = self.buffer_size, self.read
        while True:
            part = read(buff)
            if not part: return
            yield part


class _closeiter(object):
    ''' This only exists to be able to attach a .close method to iterators that
        do not support attribute assignment (most of itertools).
         它只存在于能够将.close方法附加到不支持属性赋值（大多数itertools）'''

    def __init__(self, iterator, close=None):
        self.iterator = iterator
        self.close_callbacks = makelist(close)

    def __iter__(self):
        return iter(self.iterator)

    def close(self):
        for func in self.close_callbacks:
            func()


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
        """ Attach a callback to a hook. Three hooks are currently implemented:

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
        """
        if name in self.__hook_reversed:
            self._hooks[name].insert(0, func)
        else:
            self._hooks[name].append(func)

    def remove_hook(self, name, func):
        """ Remove a callback from a hook. 从钩子中移除回调。"""
        if name in self._hooks and func in self._hooks[name]:
            self._hooks[name].remove(func)
            return True

    def trigger_hook(self, __name, *args, **kwargs):
        """ Trigger a hook and return a list of results.
         触发钩子并返回结果列表 """
        return [hook(*args, **kwargs) for hook in self._hooks[__name][:]]

    def hook(self, name):
        """ Return a decorator that attaches a callback to a hook. See
            :meth:`add_hook` for details.
            返回将回调附加到挂钩的装饰器。看见：meth:'add_hook'了解详细信息。"""

        def decorator(func):
            self.add_hook(name, func)
            return func

        return decorator

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

    def _handle(self, environ):
        path = environ['brick.raw_path'] = environ['PATH_INFO']
        try:
            environ['PATH_INFO'] = path.encode('latin1').decode('utf8')  # latin-1就是ISO-8859-1的别名
        except UnicodeError:
            return HTTPError(400, 'Invalid path string. Expected UTF-8')
        try:
            environ['brick.app'] = self
            request.bind(environ)
            response.bind()
            try:
                self.trigger_hook('before_request')
                route, args = self.router.match(environ)
                # print("routes：%s" % route)
                environ['route.handle'] = route
                environ['brick.route'] = route
                environ['route.url_args'] = args
                return route.call(**args)
            except UnicodeError:
                pass
            finally:
                self.trigger_hook('after_request')
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

    def _cast(self, out):
        """  尝试将参数转换为WSGI兼容的内容并设置如果可能，请更正HTTP头。
               支持：False、str、unicode、dict、HTTPResponse、HTTPError、file-like，
               字符串的iterable和Unicode的iterable
               """
        # Empty output is done here
        if not out:
            if 'Content-Length' not in response:
                response['Content-Length'] = 0
            return []
        # Join lists of byte or unicode strings. Mixed lists are NOT supported
        if isinstance(out, (tuple, list)) and isinstance(out[0], (bytes, str)):
            out = out[0][0:0].join(out)  # b'abc'[0:0] -> b'',[n:n]表示不提取元素为空
        # Encode unicode strings
        if isinstance(out, str):
            out = out.encode(response.charset)
        # Byte Strings are just returned
        if isinstance(out, bytes):
            if 'Content-Length' not in response:
                response['Content-Length'] = len(out)
            return [out]
        # HTTPError or HTTPException (recursive, because they may wrap anything)
        # TODO: Handle these explicitly in handle() or make them iterable.
        # HTTPError或HTTPException(递归，因为它们可以包装任何东西)
        # TODO:在Handle()中显式处理这些，或者使它们可迭代。
        if isinstance(out, HTTPError):
            out.apply(response)
            out = self.error_handler.get(out.status_code, self.default_error_handler)(
                out)  # 默认调用default_error_handler函数(out)作为参数
            return self._cast(out)
        if isinstance(out, HTTPResponse):
            out.apply(response)
            return self._cast(out.body)
        # File-like objects.
        if hasattr(out, 'read'):
            if 'wsgi.file_wrapper' in request.environ:
                return request.environ['wsgi.file_wrapper'](out)
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
            encoder = lambda x: x.encode(response.charset)
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
            if response._status_code in (100, 101, 204, 304) \
                    or environ['REQUEST_METHOD'] == 'HEAD':
                if hasattr(out, 'close'): out.close()
                out = []
            # exc_info = environ.get('brick.exc_info')
            # if exc_info is not None:
            #     del environ['brick.exc_info']
            # print('response._status_line', response._status_line)
            start_response(response._status_line, response.headerlist)
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
                func = load(func)
            for rule in makelist(path) or yieldroutes(func):
                for verb in makelist(method):
                    verb = verb.upper()
                    route = Route(self, rule, verb, func, name=name, **config)
                    self.add_route(route)
            return func

        return decorator(callback) if callback else decorator

    def get_url(self, routename, **kargs):
        """ Return a string that matches a named route """
        scriptname = request.environ.get('SCRIPT_NAME', '').strip('/') + '/'
        location = self.router.build(routename, **kargs).lstrip('/')
        return urljoin(urljoin('/', scriptname), location)

    def add_route(self, route):
        self.routelist.append(route)
        self.router.add(route.rule, route.method, route, name=route.name)

    def get(self, path=None, method='GET', **options):
        """ Equals :meth:`route`. """
        return self.route(path, method, **options)

    def post(self, path=None, method='POST', **options):
        """ Equals :meth:`route` with a ``POST`` method parameter. """
        return self.route(path, method, **options)

    def put(self, path=None, method='PUT', **options):
        """ Equals :meth:`route` with a ``PUT`` method parameter. """
        return self.route(path, method, **options)

    def delete(self, path=None, method='DELETE', **options):
        """ Equals :meth:`route` with a ``DELETE`` method parameter. """
        return self.route(path, method, **options)

    def error(self, code=500):
        """ Decorator: Register an output handler for a HTTP error code"""

        def wrapper(handler):
            self.error_handler[int(code)] = handler
            return handler

        return wrapper

    @staticmethod
    def default_error_handler(res):
        return tobytes(template(ERROR_PAGE_TEMPLATE, e=res))


def static_file1(filename, root, mimetype='auto', download=False, charset='UTF-8'):
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
    print('static_filename:', filename)
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

    ims = request.environ.get('HTTP_IF_MODIFIED_SINCE')
    if ims:
        ims = parse_date(ims.split(";")[0].strip())
    if ims is not None and ims >= int(stats.st_mtime):
        headers['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        return HTTPResponse(status=304, **headers)

    body = '' if request.method == 'HEAD' else open(filename, 'rb')

    headers["Accept-Ranges"] = "bytes"
    ranges = request.environ.get('HTTP_RANGE')
    if 'HTTP_RANGE' in request.environ:
        ranges = list(parse_range_header(request.environ['HTTP_RANGE'], clen))
        if not ranges:
            return HTTPError(416, "Requested Range Not Satisfiable")
        offset, end = ranges[0]
        headers["Content-Range"] = "bytes %d-%d/%d" % (offset, end - 1, clen)
        headers["Content-Length"] = str(end - offset)
        if body: body = _file_iter_range(body, offset, end - offset)
        return HTTPResponse(body, status=206, **headers)
    return HTTPResponse(body, **headers)


def static_file(filename, root, mimetype=True, download=False, charset='UTF-8', etag=None, headers=None):
    """ Open a file in a safe way and return an instance of :exc:`HTTPResponse`
        that can be sent back to the client.

        :param filename: Name or path of the file to send, relative to ``root``.
        :param root: Root path for file lookups. Should be an absolute directory
            path.
        :param mimetype: Provide the content-type header (default: guess from
            file extension)
        :param download: If True, ask the browser to open a `Save as...` dialog
            instead of opening the file with the associated program. You can
            specify a custom filename as a string. If not specified, the
            original filename is used (default: False).
        :param charset: The charset for files with a ``text/*`` mime-type.
            (default: UTF-8)
        :param etag: Provide a pre-computed ETag header. If set to ``False``,
            ETag handling is disabled. (default: auto-generate ETag header)
        :param headers: Additional headers dict to add to the response.

        While checking user input is always a good idea, this function provides
        additional protection against malicious ``filename`` parameters from
        breaking out of the ``root`` directory and leaking sensitive information
        to an attacker.

        Read-protected files or files outside of the ``root`` directory are
        answered with ``403 Access Denied``. Missing files result in a
        ``404 Not Found`` response. Conditional requests (``If-Modified-Since``,
        ``If-None-Match``) are answered with ``304 Not Modified`` whenever
        possible. ``HEAD`` and ``Range`` requests (used by download managers to
        check or continue partial downloads) are also handled automatically.

    """

    root = os.path.join(os.path.abspath(root), '')
    filename = os.path.abspath(os.path.join(root, filename.strip('/\\')))
    headers = headers.copy() if headers else {}

    if not filename.startswith(root):
        return HTTPError(403, "Access denied.")
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return HTTPError(404, "File does not exist.")
    if not os.access(filename, os.R_OK):
        return HTTPError(403, "You do not have permission to access this file.")

    if mimetype is True:
        if download and download is not True:
            mimetype, encoding = mimetypes.guess_type(download)
        else:
            mimetype, encoding = mimetypes.guess_type(filename)
        if encoding:
            headers['Content-Encoding'] = encoding

    if mimetype:
        if (mimetype[:5] == 'text/' or mimetype == 'application/javascript') \
                and charset and 'charset' not in mimetype:
            mimetype += '; charset=%s' % charset
        headers['Content-Type'] = mimetype

    if download:
        download = os.path.basename(filename if download is True else download)
        headers['Content-Disposition'] = 'attachment; filename="%s"' % download

    stats = os.stat(filename)
    headers['Content-Length'] = clen = stats.st_size
    headers['Last-Modified'] = email.utils.formatdate(stats.st_mtime,
                                                      usegmt=True)
    headers['Date'] = email.utils.formatdate(time.time(), usegmt=True)

    getenv = request.environ.get

    if etag is None:
        etag = '%d:%d:%d:%d:%s' % (stats.st_dev, stats.st_ino, stats.st_mtime,
                                   clen, filename)
        etag = hashlib.sha1(tobytes(etag)).hexdigest()

    if etag:
        headers['ETag'] = etag
        check = getenv('HTTP_IF_NONE_MATCH')
        if check and check == etag:
            return HTTPResponse(status=304, **headers)

    ims = getenv('HTTP_IF_MODIFIED_SINCE')
    if ims:
        ims = parse_date(ims.split(";")[0].strip())
        if ims is not None and ims >= int(stats.st_mtime):
            return HTTPResponse(status=304, **headers)

    body = '' if request.method == 'HEAD' else open(filename, 'rb')

    headers["Accept-Ranges"] = "bytes"
    range_header = getenv('HTTP_RANGE')
    if range_header:
        ranges = list(parse_range_header(range_header, clen))
        if not ranges:
            return HTTPError(416, "Requested Range Not Satisfiable")
        offset, end = ranges[0]
        rlen = end - offset
        headers["Content-Range"] = "bytes %d-%d/%d" % (offset, end - 1, clen)
        headers["Content-Length"] = str(rlen)
        if body: body = _closeiter(_rangeiter(body, offset, rlen), body.close)
        return HTTPResponse(body, status=206, **headers)
    return HTTPResponse(body, **headers)


def _rangeiter(fp, offset, limit, bufsize=1024 * 1024):
    """ Yield chunks from a range in a file. """
    fp.seek(offset)
    while limit > 0:
        part = fp.read(min(limit, bufsize))
        if not part:
            break
        limit -= len(part)
        yield part


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
    %%#from %s import DEBUG, HTTP_CODES, request, tounicode
   %%from brick.http.request import request
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
            <p>Sorry, the requested URL <tt>{{repr(request.environ.get('PATH_INFO', ''))}}</tt>
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
    <b>ImportError:</b> Could not generate the error page. Please add :brick to
    the import path. %s
%%end
""" % (__name__, __name__)


def make_default_app_wrapper(name):
    """ Return a callable that relays calls to the current default app. """

    @functools.wraps(getattr(DefaultApp, name))
    def wrapper(*a, **ka):
        # return getattr(app(), name)(*a, **ka)
        return getattr(default_app, name)(*a, **ka)

    return wrapper


default_app = DefaultApp()

get = make_default_app_wrapper('get')
post = make_default_app_wrapper('post')
put = make_default_app_wrapper('put')
delete = make_default_app_wrapper('delete')
error = make_default_app_wrapper('error')
route = make_default_app_wrapper('route')
hook = make_default_app_wrapper('hook')
url = make_default_app_wrapper('get_url')


def server_run(app=default_app, host='127.0.0.1', port=8080, interval=1, reloader=False, quiet=False,
               plugins=None, debug=None, **kargs):
    # 第一次进来的时候，必然会进这个分支，因为没有地方设置过BRICK_AUTORELOAD_ENV
    if reloader and not os.environ.get("BRICK_AUTORELOAD_ENV"):
        import subprocess
        # 其实这里会创建一个新的子进程来运行服务
        args = [sys.executable] + sys.argv  # sys.executable 是获取当前python解释器的路径
        # If a package was loaded with `python -m`, then `sys.argv` needs to be
        # restored to the original value, or imports might break. See #1336
        if getattr(sys.modules.get('__main__'), '__package__', None):
            args[1:1] = ["-m", sys.modules['__main__'].__package__]
        new_environ = os.environ.copy()
        new_environ['BRICK_AUTORELOAD_ENV'] = "true"
        while True:
            p = subprocess.run(args, env=new_environ, close_fds=True)
            exit_code = p.returncode
            if exit_code != 3:
                sys.exit(exit_code)
    else:
        try:
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
                finally:
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
