#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:53
# @Author  : CJ  Mao
# @Site    : 
# @File    : request.py
# @Project : mysite_diy
# @Software: PyCharm
import functools
from http.cookies import SimpleCookie

# from Scripts.bottle import FormsDict

from webcore.httphandles.util import WSGIHeaderDict, cookie_decode, FileUpload, json_loads, \
    local_property, FormsDict
from webcore.utilities.dicthelper import DictProperty


def _parse_qsl(qs):
    r = []
    for pair in qs.replace(';', '&').split('&'):
        if not pair: continue
        nv = pair.split('=', 1)
        if len(nv) != 2: nv.append('')
        key = urlunquote = functools.partial(urlunquote, encoding='latin1')(nv[0].replace('+', ' '))
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
        self.environ['webcore.request'] = self

    @DictProperty('environ', 'webcore.app', read_only=True)
    def app(self):
        ''' Bottle application handling this request处理此请求的应用程序. '''
        raise RuntimeError('This request is not connected to an application.')

    @DictProperty('environ', 'webcore.route', read_only=True)
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

    @DictProperty('environ', 'webcore.request.headers', read_only=True)
    def headers(self):
        """ A :class:`WSGIHeaderDict` that provides case-insensitive access to
            HTTP request headers. A:类：`WSGIHeaderDict`提供对HTTP请求头。"""
        return WSGIHeaderDict(self.environ)

    def get_header(self, name, default=None):
        """ Return the value of a request header, or a given default value.返回请求标头的值，或给定的默认值 """
        return self.headers.get(name, default)

    @DictProperty('environ', 'webcore.request.cookies', read_only=True)
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

    @DictProperty('environ', 'webcore.request.query', read_only=True)
    def query(self):
        """ The :attr:`query_string` parsed into a :class:`FormsDict`. These
            values are sometimes called "URL arguments" or "GET parameters", but
            not to be confused with "URL wildcards" as they are provided by the
            :class:`Router`.
            ：attr:`query_string`解析为：class:`FormsDict`。这些值有时被称为“URL参
            数”或“GET parameters”，但是不要与“URL通配符”混淆，因为它们是由：类：`Router`。 """
        get = self.environ['bottle.get'] = FormsDict()
        pairs = _parse_qsl(self.environ.get('QUERY_STRING', ''))
        for key, value in pairs:
            get[key] = value
        return get

    @DictProperty('environ', 'webcore.request.forms', read_only=True)
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

    @DictProperty('environ', 'webcore.request.params', read_only=True)
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
        return params

    @DictProperty('environ', 'webcore.request.files', read_only=True)
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

    @DictProperty('environ', 'webcore.request.json', read_only=True)
    def json(self):
        """ If the ``Content-Type`` header is ``application/json``, this
            property holds the parsed content of the request body. Only requests
            smaller than :attr:`MEMFILE_MAX` are processed to avoid memory
            exhaustion.
            如果“Content-Type”头是“application/json”，则属性保存请求正文的已分析
            内容。仅请求处理小于：attr:`MEMFILE_MAX`以避免内存疲惫。"""
        ctype = self.environ.get('CONTENT_TYPE', '').lower().split(';')[0]
        if ctype == 'application/json':
            b = self._get_body_string()
            if not b:
                return None
            return json_loads(b)
        return None

    def __repr__(self):
        return '<%s: %s %s>' % (self.__class__.__name__, self.method, self.url)


class LocalRequest(BaseRequest):
    """ `BaseRequest` 类的线程本地子类每个线程的属性集。通常只有一个全局此类的实例（：data:`request`）。
         如果在请求/响应周期，此实例始终引用*当前*请求（即使在多线程服务器上）。"""
    bind = BaseRequest.__init__
    environ = local_property()


localrequest = LocalRequest()
