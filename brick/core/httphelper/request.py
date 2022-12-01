#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:53
# @Author  : CJ  Mao
# @Site    : 
# @File    : request.py
# @Project : mysite_diy
# @Software: PyCharm
import cgi
import functools
from http.cookies import SimpleCookie
from urllib.parse import quote as urlquote, unquote as urlunquote, urljoin, SplitResult as UrlSplitResult

urlunquote = functools.partial(urlunquote, encoding='latin1')
# from Scripts.bottle import FormsDict
from io import BytesIO
from tempfile import TemporaryFile

from brick.core.httphelper.response import HTTPError
from brick.core.httphelper.util import WSGIHeaderDict, cookie_decode, FileUpload, json_loads, \
    local_property, FormsDict
from brick.utils.dicthelper import DictProperty
from brick.utils.encode import tobytes, tounicode


def _parse_qsl(qs):
    r = []
    for pair in qs.replace(';', '&').split('&'):
        if not pair: continue
        nv = pair.split('=', 1)
        if len(nv) != 2: nv.append('')
        # key = urlunquote = functools.partial(urlunquote, encoding='latin1')(nv[0].replace('+', ' '))
        key = urlunquote(nv[0].replace('+', ' '))
        value = urlunquote(nv[1].replace('+', ' '))
        r.append((key, value))
    return r


class BaseRequest(object):
    """ 一个用于WSGI环境字典的包装器，它添加了很多
        方便的访问方法和属性。大多数是只读的。
        向请求添加新属性实际上会将它们添加到环境中
        字典（'bottle.request.ext.<name>'）。这是推荐的
        存储和访问请求特定数据的方法。
    """

    __slots__ = ('environ')
    #: Maximum size of memory buffer for :attr:`body` in bytes.
    MEMFILE_MAX = 102400  # 内存文件最大值

    def __init__(self, environ=None):
        """ Wrap a WSGI environ dictionary. 包装一个WSGI环境字典。"""
        #: The wrapped WSGI environ dictionary. This is the only real attribute.
        #: All other attributes actually are read-only properties.
        self.environ = {} if environ is None else environ
        # print('environ:',environ)
        self.environ['brick.request'] = self

    @DictProperty('environ', 'brick.app', read_only=True)
    def app(self):
        ''' Bottle application handling this request处理此请求的应用程序. '''
        raise RuntimeError('This request is not connected to an application.')

    @DictProperty('environ', 'brick.route', read_only=True)
    def route(self):
        """ The bottle :class:`Route` object that matches this request. """
        raise RuntimeError('This request is not connected to a route.')

    @DictProperty('environ', 'route.url_args', read_only=True)
    def url_args(self):
        """ The arguments extracted from the URL. """
        raise RuntimeError('This request is not connected to a route.')

    @property
    def path(self):
        """ 只有一个前缀斜杠的“PATH_INFO”的值（修复断开客户机并避免“空路径”边缘情况） """
        return '/' + self.environ.get('PATH_INFO', '').lstrip('/')
        # lstrip('/')返回截掉字符串左边的空格或指定字符后生成的新字符串。

    @property
    def method(self):
        """ The ``REQUEST_METHOD`` value as an uppercase string. """
        return self.environ.get('REQUEST_METHOD', 'GET').upper()

    @DictProperty('environ', 'brick.request.headers', read_only=True)
    def headers(self):
        """ A :class:`WSGIHeaderDict` that provides case-insensitive access to
            HTTP request headers. A:类：`WSGIHeaderDict`提供对HTTP请求头。"""
        return WSGIHeaderDict(self.environ)

    def get_header(self, name, default=None):
        """ Return the value of a request header, or a given default value.返回请求标头的值，或给定的默认值 """
        return self.headers.get(name, default)

    @DictProperty('environ', 'brick.request.cookies', read_only=True)
    def cookies(self):
        """ Cookies parsed into a :class:`FormsDict`. Signed cookies are NOT
            decoded. Use :meth:`get_cookie` if you expect signed cookies
            .Cookies解析为：class:`FormsDict`。签名的Cookie不是
            解码。用法：meth:如果您需要签名cookie，请使用“get_cookie” """
        cookies = SimpleCookie(self.environ.get('HTTP_COOKIE', '')).values()
        return FormsDict((c.key, c.value) for c in cookies)

    def get_cookie(self, key, default=None, secret=None):
        """ Return the content of a cookie. To read a `Signed Cookie`, the
            `secret` must match the one used to create the cookie (see
            :meth:`BaseResponse.set_cookie`). If anything goes wrong (missing
            cookie or wrong signature), return a default value.
            返回cookie的内容。要读取“签名Cookie”，则`secret`必须与创建cookie
            所用的匹配（请参见：方法：`BaseResponse.set_cookie`). 如果出了什么
            问题（丢失cookie或错误签名），返回默认值。"""
        value = self.cookies.get(key)
        if secret and value:
            # (key, value) tuple or None
            dec = cookie_decode(value, secret)
            return dec[1] if dec and dec[0] == key else default
        return value or default

    @DictProperty('environ', 'brick.request.query', read_only=True)
    def query(self):
        """ The :attr:`query_string` parsed into a :class:`FormsDict`. These
            values are sometimes called "URL arguments" or "GET parameters", but
            not to be confused with "URL wildcards" as they are provided by the
            :class:`Router`.
            ：attr:`query_string`解析为：class:`FormsDict`。这些值有时被称为“URL参
            数”或“GET parameters”，但是不要与“URL通配符”混淆，因为它们是由：类：`Router`。 """
        get = self.environ['brick.get'] = FormsDict()
        pairs = _parse_qsl(self.environ.get('QUERY_STRING', ''))
        for key, value in pairs:
            get[key] = value
        return get
    #: An alias for :attr:`query`.
    GET = query
    @DictProperty('environ', 'brick.request.forms', read_only=True)
    def forms(self):
        """ Form values parsed from an `url-encoded` or `multipart/form-data`
            encoded POST or PUT request body. The result is returned as a
            :class:`FormsDict`. All keys and values are strings. File uploads
            are stored separately in :attr:`files`.
             从“url encoded”或“multipart/Form数据”分析的表单值`编码的POST或
             PUT请求正文。结果作为：类：`FormsDict`。所有键和值都是字符串。文件
             上传分别存储在：attr:`files中`"""
        forms = FormsDict()
        for name, item in self.POST.allitems():
            if not isinstance(item, FileUpload):
                forms[name] = item
        return forms

    @DictProperty('environ', 'brick.request.params', read_only=True)
    def params(self):
        """ A :class:`FormsDict` with the combined values of :attr:`query` and
            :attr:`forms`. File uploads are stored in :attr:`files`.
             A:class:`FormsDict'，其组合值为：attr:`query`和：attr:`forms`。文件
             上载存储在：attr:`files`。"""

        params = FormsDict()
        for key, value in self.query.allitems():
            params[key] = value
        for key, value in self.forms.allitems():
            params[key] = value
        print('gfff',params )
        return params

    @DictProperty('environ', 'brick.request.files', read_only=True)
    def files(self):
        """ File uploads parsed from `multipart/form-data` encoded POST or PUT
            request body. The values are instances of :class:`FileUpload`.
            从“multipart/form data”编码的POST或PUT解析的文件上载
            请求正文。这些值是：class:`FileUpload的实例`
        """
        files = FormsDict()
        for name, item in self.POST.allitems():
            if isinstance(item, FileUpload):
                files[name] = item
        return files

    @DictProperty('environ', 'brick.request.json', read_only=True)
    def json(self):
        """ If the ``Content-Type`` header is ``application/json``, this
            property holds the parsed content of the request body. Only requests
            smaller than :attr:`MEMFILE_MAX` are processed to avoid memory
            exhaustion.
            如果“Content-Type”头是“application/json”，则属性保存请求正文的已分析
            内容。仅请求处理小于：attr:`MEMFILE_MAX`以避免内存疲惫。"""
        ctype = self.environ.get('CONTENT_TYPE', '').lower().split(';')[0]
        # Content - Type 详解
        # https://blog.csdn.net/qq_14869093/article/details/86307084
        if ctype == 'application/json':
            b = self._get_body_string()
            if not b:
                return None
            return json_loads(b)
        return None
    def _iter_body(self, read, bufsize):
        maxread = max(0, self.content_length)
        while maxread:
            part = read(min(maxread, bufsize))
            if not part: break
            yield part
            maxread -= len(part)

    def _iter_chunked(self, read, bufsize):
        err = HTTPError(400, 'Error while parsing chunked transfer body.')
        rn, sem, bs = tobytes('\r\n'), tobytes(';'), tobytes('')
        while True:
            header = read(1)
            while header[-2:] != rn:
                c = read(1)
                header += c
                if not c: raise err
                if len(header) > bufsize: raise err
            size, _, _ = header.partition(sem)
            try:
                maxread = int(tounicode(size.strip()), 16)
            except ValueError:
                raise err
            if maxread == 0: break
            buff = bs
            while maxread > 0:
                if not buff:
                    buff = read(min(maxread, bufsize))
                part, buff = buff[:maxread], buff[maxread:]
                if not part: raise err
                yield part
                maxread -= len(part)
            if read(2) != rn:
                raise err

    @DictProperty('environ', 'brick.request.body', read_only=True)
    def _body(self):
        body_iter = self._iter_chunked if self.chunked else self._iter_body
        read_func = self.environ['wsgi.input'].read
        body, body_size, is_temp_file = BytesIO(), 0, False
        for part in body_iter(read_func, self.MEMFILE_MAX):
            body.write(part)
            body_size += len(part)
            if not is_temp_file and body_size > self.MEMFILE_MAX:
                body, tmp = TemporaryFile(mode='w+b'), body
                body.write(tmp.getvalue())
                del tmp
                is_temp_file = True
        self.environ['wsgi.input'] = body
        body.seek(0)
        return body

    def _get_body_string(self):
        '''  read body until content-length or MEMFILE_MAX into a string. Raise
            HTTPError(413) on requests that are to large.
            读取正文，直到内容长度或MEMFILE_MAX变成字符串。提升HTTPError（413）处理过大的请求。'''
        clen = self.content_length
        if clen > self.MEMFILE_MAX:
            raise HTTPError(413, 'Request to large')
        if clen < 0: clen = self.MEMFILE_MAX + 1
        data = self.body.read(clen)
        if len(data) > self.MEMFILE_MAX: # Fail fast
            raise HTTPError(413, 'Request to large')
        return data

    @property
    def body(self):
        """ The HTTP request body as a seek-able file-like object. Depending on
            :attr:`MEMFILE_MAX`, this is either a temporary file or a
            :class:`io.BytesIO` instance. Accessing this property for the first
            time reads and replaces the ``wsgi.input`` environ variable.
            Subsequent accesses just do a `seek(0)` on the file object. """
        self._body.seek(0)
        return self._body

    @property
    def chunked(self):
        ''' True if Chunked transfer encoding was. '''
        return 'chunked' in self.environ.get('HTTP_TRANSFER_ENCODING', '').lower()

    @DictProperty('environ', 'brick.request.post', read_only=True)
    def POST(self):
        """ The values of :attr:`forms` and :attr:`files` combined into a single
            :class:`FormsDict`. Values are either strings (form values) or
            instances of :class:`cgi.FieldStorage` (file uploads).
        """
        post = FormsDict()
        # We default to application/x-www-form-urlencoded for everything that
        # is not multipart and take the fast path (also: 3.1 workaround)
        if not self.content_type.startswith('multipart/'):
            pairs = _parse_qsl(tounicode(self._get_body_string(), 'latin1'))
            for key, value in pairs:
                post[key] = value
            return post

        safe_env = {'QUERY_STRING': ''}  # Build a safe environment for cgi
        for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
            if key in self.environ: safe_env[key] = self.environ[key]
        args = dict(fp=self.body, environ=safe_env, keep_blank_values=True)
        # if py31:
        #     args['fp'] = NCTextIOWrapper(args['fp'], encoding='utf8',
        #                                  newline='\n')
        # elif py3k:
        #     args['encoding'] = 'utf8'
        args['encoding'] = 'utf8'
        data = cgi.FieldStorage(**args)
        self['_cgi.FieldStorage'] = data  # http://bugs.python.org/issue18394#msg207958
        data = data.list or []
        for item in data:
            if item.filename:
                post[item.name] = FileUpload(item.file, item.name,
                                             item.filename, item.headers)
            else:
                post[item.name] = item.value
        return post

    @property
    def url(self):
        """ The full request URI including hostname and scheme. If your app
            lives behind a reverse proxy or load balancer and you get confusing
            results, make sure that the ``X-Forwarded-Host`` header is set
            correctly. """
        print('request.url', )
        return self.urlparts.geturl()

    @DictProperty('environ', 'bottle.request.urlparts', read_only=True)
    def urlparts(self):
        ''' The :attr:`url` string as an :class:`urlparse.SplitResult` tuple.
            The tuple contains (scheme, host, path, query_string and fragment),
            but the fragment is always empty because it is not visible to the
            server. '''
        env = self.environ
        http = env.get('HTTP_X_FORWARDED_PROTO') or env.get('wsgi.url_scheme', 'httphelper')
        host = env.get('HTTP_X_FORWARDED_HOST') or env.get('HTTP_HOST')
        if not host:
            # HTTP 1.1 requires a Host-header. This is for HTTP/1.0 clients.
            host = env.get('SERVER_NAME', '127.0.0.1')
            port = env.get('SERVER_PORT')
            if port and port != ('80' if http == 'httphelper' else '443'):
                host += ':' + port
        path = urlquote(self.fullpath)
        return UrlSplitResult(http, host, path, env.get('QUERY_STRING'), '')

    @property
    def fullpath(self):
        """ Request path including :attr:`script_name` (if present). """
        return urljoin(self.script_name, self.path.lstrip('/'))

    @property
    def query_string(self):
        """ The raw :attr:`query` part of the URL (everything in between ``?``
            and ``#``) as a string. """
        return self.environ.get('QUERY_STRING', '')

    @property
    def script_name(self):
        ''' The initial portion of the URL's `path` that was removed by a higher
            level (server or routing middleware) before the application was
            called. This script path is returned with leading and tailing
            slashes.
            URL的“路径”的初始部分，该部分已被较高级别的应用程序启动前的级别
            （服务器或路由中间件）打电话。此脚本路径返回前导和尾随斜杠。'''
        script_name = self.environ.get('SCRIPT_NAME', '').strip('/')
        return '/' + script_name + '/' if script_name else '/'

    def path_shift(self, shift=1):
        ''' Shift path segments from :attr:`path` to :attr:`script_name` and
            vice versa.

           :param shift: The number of path segments to shift. May be negative
                         to change the shift direction. (default: 1)
        '''
        script = self.environ.get('SCRIPT_NAME', '/')
        self['SCRIPT_NAME'], self['PATH_INFO'] = path_shift(script, self.path, shift)

    @property
    def content_length(self):
        ''' The request body length as an integer. The client is responsible to
            set this header. Otherwise, the real length of the body is unknown
            and -1 is returned. In this case, :attr:`body` will be empty. '''
        return int(self.environ.get('CONTENT_LENGTH') or -1)

    @property
    def content_type(self):
        ''' The Content-Type header as a lowercase-string (default: empty). '''
        return self.environ.get('CONTENT_TYPE', '').lower()

    @property
    def is_xhr(self):
        ''' True if the request was triggered by a XMLHttpRequest. This only
            works with JavaScript libraries that support the `X-Requested-With`
            header (most of the popular libraries do). '''
        requested_with = self.environ.get('HTTP_X_REQUESTED_WITH', '')
        return requested_with.lower() == 'xmlhttprequest'

    @property
    def is_ajax(self):
        ''' Alias for :attr:`is_xhr`. "Ajax" is not the right term. '''
        return self.is_xhr

    @property
    def auth(self):
        """ HTTP authentication data as a (user, password) tuple. This
            implementation currently supports basic (not digest) authentication
            only. If the authentication happened at a higher level (e.g. in the
            front web-server or a middleware), the password field is None, but
            the user field is looked up from the ``REMOTE_USER`` environ
            variable. On any errors, None is returned. """
        basic = parse_auth(self.environ.get('HTTP_AUTHORIZATION', ''))
        if basic: return basic
        ruser = self.environ.get('REMOTE_USER')
        if ruser: return (ruser, None)
        return None

    @property
    def remote_route(self):
        """ A list of all IPs that were involved in this request, starting with
            the client IP and followed by zero or more proxies. This does only
            work if all proxies support the ```X-Forwarded-For`` header. Note
            that this information can be forged by malicious clients. """
        proxy = self.environ.get('HTTP_X_FORWARDED_FOR')
        if proxy: return [ip.strip() for ip in proxy.split(',')]
        remote = self.environ.get('REMOTE_ADDR')
        return [remote] if remote else []

    @property
    def remote_addr(self):
        """ The client IP as a string. Note that this information can be forged
            by malicious clients. """
        route = self.remote_route
        return route[0] if route else None

    def copy(self):
        """ Return a new :class:`Request` with a shallow :attr:`environ` copy. """
        return Request(self.environ.copy())

    def get(self, value, default=None):
        return self.environ.get(value, default)

    def __getitem__(self, key):
        return self.environ[key]

    def __delitem__(self, key):
        self[key] = ""; del (self.environ[key])

    def __iter__(self):
        return iter(self.environ)

    def __len__(self):
        return len(self.environ)

    def keys(self):
        return self.environ.keys()

    def __setitem__(self, key, value):
        """ Change an environ value and clear all caches that depend on it. """

        if self.environ.get('brick.request.readonly'):
            raise KeyError('The environ dictionary is read-only.')

        self.environ[key] = value
        todelete = ()

        if key == 'wsgi.input':
            todelete = ('body', 'forms', 'files', 'params', 'post', 'json')
        elif key == 'QUERY_STRING':
            todelete = ('query', 'params')
        elif key.startswith('HTTP_'):
            todelete = ('headers', 'cookies')

        for key in todelete:
            self.environ.pop('bottle.request.' + key, None)

    def __getattr__(self, name):
        ''' Search in self.environ for additional user defined attributes. '''
        try:
            var = self.environ['bottle.request.ext.%s'%name]
            return var.__get__(self) if hasattr(var, '__get__') else var
        except KeyError:
            raise AttributeError('Attribute %r not defined.' % name)

    def __setattr__(self, name, value):
        if name == 'environ': return object.__setattr__(self, name, value)
        self.environ['bottle.request.ext.%s'%name] = value

    def __repr__(self):
        return '<%s: %s %s>' % (self.__class__.__name__, self.method, self.url)


class LocalRequest(BaseRequest):
    """ `BaseRequest` 类的线程本地子类每个线程的属性集。通常只有一个全局此类的实例（：data:`request`）。
         如果在请求/响应周期，此实例始终引用*当前*请求（即使在多线程服务器上）。"""
    bind = BaseRequest.__init__
    environ = local_property()

Request=BaseRequest
request = LocalRequest()
