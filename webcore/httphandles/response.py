#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:52
# @Author  : CJ  Mao
# @Site    : 
# @File    : response.py
# @Project : mysite_diy
# @Software: PyCharm

import email
import time
from http import client
from http.cookies import SimpleCookie
from datetime import date, datetime

from webcore.httphandles.util import HeaderDict, _hkey, _hval, HeaderProperty, local_property

HTTP_CODES = client.responses  # 将 HTTP 1.1 状态码映射到 W3C 名字的字典。
HTTP_CODES[418] = "I'm a teapot"  # RFC 2324
HTTP_CODES[422] = "Unprocessable Entity"  # RFC 4918
HTTP_CODES[428] = "Precondition Required"
HTTP_CODES[429] = "Too Many Requests"
HTTP_CODES[431] = "Request Header Fields Too Large"
HTTP_CODES[511] = "Network Authentication Required"
_HTTP_STATUS_LINES = dict((k, '%d %s' % (k, v)) for (k, v) in HTTP_CODES.items())


def parse_date(ims):
    """ 解析rfc1123、rfc850和asctime时间戳并返回UTC epoch。 """
    try:
        ts = email.utils.parsedate_tz(ims)
        return time.mktime(ts[:8] + (0,)) - (ts[9] or 0) - time.timezone
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def http_date(value):
    if isinstance(value, (date, datetime)):
        value = value.utctimetuple()
    elif isinstance(value, (int, float)):
        value = time.gmtime(value)
    if not isinstance(value, str):
        value = time.strftime("%a, %d %b %Y %H:%M:%S GMT", value)
    return value


class BaseResponse(object):
    """ 响应主体以及标头和cookies的存储类。此类不支持类似dict的不区分大小写的项访问
    标题，但不是格言。最值得注意的是，迭代一个响应产生身体的一部分，而不是头部。
    :参数体:作为支持类型之一的响应体。:参数状态:HTTP状态代码(例如200)或状态行包括原因
    短语(例如，“200 OK”)。:参数头:字典或名称-值对列表。额外的关键字参数被添加到标题列
    表中。标题名称中的下划线被替换为破折号。
    """
    default_status = 200
    default_content_type = 'text/html; charset=UTF-8'
    bad_headers = {204: set(('Content-Type',)),
                   304: set(('Allow', 'Content-Encoding', 'Content-Language',
                             'Content-Length', 'Content-Range', 'Content-Type',
                             'Content-Md5', 'Last-Modified'))}

    def __init__(self, body='', status=None, headers=None, **more_headers):
        self._cookies = None
        self._headers = {}
        self.body = body
        self.status = status or self.default_status
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for name, value in headers:
                self.add_header(name, value)
        if more_headers:
            for name, value in more_headers.items():
                self.add_header(name, value)

    def copy(self, cls=None):
        """ Returns a copy of self. 返回self的副本。"""
        cls = cls or BaseResponse
        assert issubclass(cls, BaseResponse)  # assert（断言）用于判断一个表达式，在表达式条件为 false 的时候触发异常。
        copy = cls()
        copy.status = self.status
        copy._headers = dict((k, v[:]) for (k, v) in self._headers.items())
        if self._cookies:
            copy._cookies = SimpleCookie()
            copy._cookies.load(self._cookies.output(header=''))
        return copy

    def __iter__(self):
        return iter(self.body)

    def close(self):
        if hasattr(self.body, 'close'):
            self.body.close()

    @property
    def status_line(self):
        """ 以字符串形式显示的HTTP状态行（例如“404 Not Found”）。"""
        return self._status_line

    @property
    def status_code(self):
        """ .HTTP状态代码为整数（例如404）"""
        return self._status_code

    def _set_status(self, status):
        if isinstance(status, int):
            code, status = status, _HTTP_STATUS_LINES.get(status)
        elif ' ' in status:
            status = status.strip()
            code = int(status.split()[0])
        else:
            raise ValueError('String status line without a reason phrase.')
        if not 100 <= code <= 999: raise ValueError('Status code out of range.')
        self._status_code = code
        self._status_line = str(status or ('%d Unknown' % code))

    def _get_status(self):
        return self._status_line

    status = property(_get_status, _set_status, None,
                      ''' A writeable property to change the HTTP response status. It accepts
                          either a numeric code (100-999) or a string with a custom reason
                          phrase (e.g. "404 Brain not found"). Both :data:`status_line` and
                          :data:`status_code` are updated accordingly. The return value is
                          always a status string. ''')
    del _get_status, _set_status

    @property
    def headers(self):
        """ An instance of :class:`HeaderDict`, a case-insensitive dict-like
            view on the response headers.
            类的一个实例：`HeaderDict'，一个不区分大小写的dict-like查看响应标头。"""
        hdict = HeaderDict()
        hdict.dict = self._headers
        return hdict

    def __contains__(self, name):
        return _hkey(name) in self._headers

    def __delitem__(self, name):
        del self._headers[_hkey(name)]

    def __getitem__(self, name):
        return self._headers[_hkey(name)][-1]

    def __setitem__(self, name, value):
        self._headers[_hkey(name)] = [_hval(value)]

    def get_header(self, name, default=None):
        """  Return the value of a previously defined header. If there is no
            header with that name, return a default value.
            返回先前定义的标头的值。如果没有具有该名称的标头，返回默认值。"""
        return self._headers.get(_hkey(name), [default])[-1]

    def set_header(self, name, value):
        """ Create a new response header, replacing any previously defined
            headers with the same name.
            创建一个新的响应头，替换以前定义的任何响应头具有相同名称的标题。"""
        self._headers[_hkey(name)] = [_hval(value)]

    def add_header(self, name, value):
        """ Add an additional response header, not removing duplicates. 添加额外的响应头，而不是删除重复项。"""
        self._headers.setdefault(_hkey(name), []).append(_hval(value))

    def iter_headers(self):
        """ Yield (header, value) tuples, skipping headers that are not
            allowed with the current response status code.
            Yield（header，value）元组，跳过不是允许使用当前响应状态代码。"""
        return self.headerlist

    @property
    def headerlist(self):
        """ WSGI conform list of (header, value) tuples. WSGI符合（头，值）元组的列表。"""
        out = []
        headers = list(self._headers.items())
        if 'Content-Type' not in self._headers:
            headers.append(('Content-Type', [self.default_content_type]))
        if self._status_code in self.bad_headers:
            bad_headers = self.bad_headers[self._status_code]
            headers = [h for h in headers if h[0] not in bad_headers]
        out += [(name, val) for (name, vals) in headers for val in vals]
        if self._cookies:
            for c in self._cookies.values():
                out.append(('Set-Cookie', _hval(c.OutputString())))
        out = [(k, v.encode('utf8').decode('latin1')) for (k, v) in out]
        return out

    content_type = HeaderProperty('Content-Type')
    content_length = HeaderProperty('Content-Length', reader=int)
    expires = HeaderProperty('Expires',
                             reader=lambda x: datetime.utcfromtimestamp(parse_date(x)),
                             writer=lambda x: http_date(x))

    @property
    def charset(self, default='UTF-8'):
        """ Return the charset specified in the content-type header (default: utf8)
        .返回内容类型头中指定的字符集（默认值：utf8）。 """
        if 'charset=' in self.content_type:
            return self.content_type.split('charset=')[-1].split(';')[0].strip()
        return default


class LocalResponse(BaseResponse):
    """ `BaseResponse`的线程本地子类每个线程的属性集。通常只有一个全局
        此类的实例（：data:`response`）。它的属性被使用在请求/响应周期结束时构建HTTP响应。
    """
    bind = BaseResponse.__init__
    _status_line = local_property()
    _status_code = local_property()
    _cookies = local_property()
    _headers = local_property()
    body = local_property()


localresponse = LocalResponse()


class HTTPResponse(BaseResponse, Exception):
    def __init__(self, body='', status=None, headers=None, **more_headers):
        super(HTTPResponse, self).__init__(body, status, headers, **more_headers)

    def apply(self, response):
        response._status_code = self._status_code
        response._status_line = self._status_line
        response._headers = self._headers
        response._cookies = self._cookies
        response.body = self.body


class HTTPError(HTTPResponse):
    default_status = 500

    def __init__(self, status=None, body=None, exception=None, traceback=None,
                 **options):
        self.exception = exception
        self.traceback = traceback
        super(HTTPError, self).__init__(body, status, **options)
