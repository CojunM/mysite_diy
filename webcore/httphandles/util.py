#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:41
# @Author  : CJ  Mao
# @Site    : 
# @File    : util.py
# @Project : mysite_diy
# @Software: PyCharm
import base64
import functools
import hashlib
import hmac
import os
import pickle
import re
import threading
from collections.abc import MutableMapping
from unicodedata import normalize
try: from simplejson import dumps as json_dumps, loads as json_lds
except ImportError: # pragma: no cover
    try: from json import dumps as json_dumps, loads as json_lds
    except ImportError:
        try: from django.utils.simplejson import dumps as json_dumps, loads as json_lds
        except ImportError:
            def json_dumps(data):
                raise ImportError("JSON support requires Python 2.6 or simplejson.")
            json_lds = json_dumps

from webcore.utilities.cachehelper import cached_property
from webcore.utilities.encode import tobytes, tounicode


# try: from simplejson import dumps as json_dumps, loads as json_lds
# except ImportError: # pragma: no cover
#     try: from json import dumps as json_dumps, loads as json_lds
#     except ImportError:
#         try: from django.utilities.simplejson import dumps as json_dumps, loads as json_lds
#         except ImportError:
#             def json_dumps(data):
#                 raise ImportError("JSON support requires Python 2.6 or simplejson.")
#             json_lds = json_dumps

def local_property(name=None):
    # if name: depr('local_property() is deprecated and will be removed.')  # 0.12
    ls = threading.local()

    def fget(self):
        try:
            return ls.var
        except AttributeError:
            raise RuntimeError("Request context not initialized.")

    def fset(self, value):
        ls.var = value

    def fdel(self):
        del ls.var

    return property(fget, fset, fdel, 'Thread-local property')


json_loads = lambda s: json_lds(tounicode(s))


def cookie_is_encoded(data):
    """ 如果参数看起来像编码的cookie，则返回True。"""
    return bool(data.startswith(tobytes('!')) and tobytes('?') in data)


def _lscmp(a, b):
    """以加密安全的方式比较两个字符串：运行时不受公共前缀长度的影响. """
    return not sum(0 if x == y else 1 for x, y in zip(a, b)) and len(a) == len(b)


def cookie_decode(data, key):
    """验证并解码编码字符串。返回对象或不返回."""
    data = tobytes(data)
    if cookie_is_encoded(data):
        sig, msg = data.split(tobytes('?'), 1)
        if _lscmp(sig[1:], base64.b64encode(hmac.new(tobytes(key), msg, digestmod=hashlib.md5).digest())):
            return pickle.loads(base64.b64decode(msg))
    return None


def _hkey(key):
    if '\n' in key or '\r' in key or '\0' in key:
        raise ValueError("Header names must not contain control characters: %r" % key)
    return key.title().replace('_', '-')


def _hval(value):
    value = tounicode(value)
    if '\n' in value or '\r' in value or '\0' in value:
        raise ValueError("Header value must not contain control characters: %r" % value)
    return value


class MultiDict(MutableMapping):
    """ 此dict为每个键存储多个值，但其行为与普通dict，
    它只返回任何给定键的最新值。有一些特殊的方法可以访问完整的值列表。
    """

    def __init__(self, *a, **k):
        self.dict = dict((k, [v]) for (k, v) in dict(*a, **k).items())

    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return key in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, key):
        return self.dict[key][-1]

    def __setitem__(self, key, value):
        self.append(key, value)

    def keys(self):
        return self.dict.keys()

    def values(self):
        return (v[-1] for v in self.dict.values())

    def items(self):
        return ((k, v[-1]) for k, v in self.dict.items())

    def allitems(self):
        return ((k, v) for k, vl in self.dict.items() for v in vl)

    iterkeys = keys
    itervalues = values
    iteritems = items
    iterallitems = allitems

    def get(self, key, default=None, index=-1, type=None):
        """ 返回键的最新值。
        ：param default：如果未指定键，则返回的默认值存在或类型转换失败。
        ：param index:可用值列表的索引。
        ：param type：如果已定义，则此可调用项用于强制转换值转换为特定类型。
        异常被抑制并导致要返回的默认值。
        """
        try:
            val = self.dict[key][index]
            return type(val) if type else val
        except Exception:
            pass
        return default

    def append(self, key, value):
        """ 将新值添加到此键的值列表中。 """
        self.dict.setdefault(key, []).append(value)

    def replace(self, key, value):
        ''' Replace the list of values with a single value. '''
        self.dict[key] = [value]

    def getall(self, key):
        """ 将值列表替换为单个值"""
        return self.dict.get(key) or []

    #: Aliases for WTForms to mimic other multi-dict APIs (Django)
    getone = get
    getlist = getall


class HeaderDict(MultiDict):
    """不区分大小写的版本：class:`MultiDict`默认为替换旧值而不是附加它。 """

    def __init__(self, *a, **ka):
        self.dict = {}
        if a or ka: self.update(*a, **ka)

    def __contains__(self, key):
        return _hkey(key) in self.dict

    def __delitem__(self, key):
        del self.dict[_hkey(key)]

    def __getitem__(self, key):
        return self.dict[_hkey(key)][-1]

    def __setitem__(self, key, value):
        self.dict[_hkey(key)] = [_hval(value)]

    def append(self, key, value):
        self.dict.setdefault(_hkey(key), []).append(_hval(value))

    def replace(self, key, value):
        self.dict[_hkey(key)] = [_hval(value)]

    def getall(self, key):
        return self.dict.get(_hkey(key)) or []

    def get(self, key, default=None, index=-1):
        return MultiDict.get(self, _hkey(key), default, index)

    def filter(self, names):
        for name in (_hkey(n) for n in names):
            if name in self.dict:
                del self.dict[name]


class FormsDict(MultiDict):
    r"""  class:`MultiDict`   子类用于存储请求表单数据。
    除了正常的dict-like项访问方法（返回此容器还支持属性类似于对其值的访问。
    属性将自动取消-    或重新编码以匹配：attr:`input\u encoding`
    （默认值：'utf8'）。失踪属性默认为空字符串.
    """

    #: Encoding used for attribute values.
    input_encoding = 'utf8'
    #: If true (default), unicode strings are first encoded with `latin1`
    #: and then decoded to match :attr:`input_encoding`.
    recode_unicode = True

    def _fix(self, s, encoding=None):
        if isinstance(s, str) and self.recode_unicode:  # Python 3 WSGI
            return s.encode('latin1').decode(encoding or self.input_encoding)
        elif isinstance(s, bytes):  # Python 2 WSGI
            return s.decode(encoding or self.input_encoding)
        else:
            return s

    def decode(self, encoding=None):
        r""" 返回一个副本，其中所有键和值都经过反编码或重新编码以匹配
         ：attr:`input\u encoding`。有些库（如WTForms）需要unicode字典。"""

        copy = FormsDict()
        enc = copy.input_encoding = encoding or self.input_encoding
        copy.recode_unicode = False
        for key, value in self.allitems():
            copy.append(self._fix(key, enc), self._fix(value, enc))
        return copy

    def getunicode(self, name, default=None, encoding=None):
        """ 以unicode字符串或默认值形式返回值. """
        try:
            return self._fix(self[name], encoding)
        except (UnicodeError, KeyError):
            return default

    def __getattr__(self, name, default=str()):
        # Without this guard, pickle generates a cryptic TypeError:
        if name.startswith('__') and name.endswith('__'):
            return super(FormsDict, self).__getattr__(name)
        return self.getunicode(name, default=default)


class WSGIHeaderDict(MutableMapping):
    """ 这个类似dict的类包装了一个WSGI环境dict，并提供了方便的
    访问HTTP\*字段。键和值是本机字符串（2.x字节或3.x unicode）
    和键不区分大小写。如果WSGI环境包含非本机字符串值，这些值是
    反式或编码的使用无损的“拉丁1”字符集。即使相关政治公众人物
    发生变化，API仍将保持稳定。目前支持PEP 333、444和3333。
    （PEP 444是唯一的一个使用非本机字符串的。）
    """
    #: List of keys that do not have a ``HTTP_`` prefix.
    cgikeys = ('CONTENT_TYPE', 'CONTENT_LENGTH')

    def __init__(self, environ):
        self.environ = environ

    def _ekey(self, key):
        """ 将标题字段名转换为CGI/WSGI环境键。 """
        key = key.replace('-', '_').upper()
        if key in self.cgikeys:
            return key
        return 'HTTP_' + key

    def raw(self, key, default=None):
        """ 按原样返回标头值（可以是字节或unicode）. """
        return self.environ.get(self._ekey(key), default)

    def __getitem__(self, key):
        return tounicode(self.environ[self._ekey(key)], 'latin1')

    def __setitem__(self, key, value):
        raise TypeError("%s is read-only." % self.__class__)

    def __delitem__(self, key):
        raise TypeError("%s is read-only." % self.__class__)

    def __iter__(self):
        for key in self.environ:
            if key[:5] == 'HTTP_':
                yield key[5:].replace('_', '-').title()
            elif key in self.cgikeys:
                yield key.replace('_', '-').title()

    def keys(self):
        return [x for x in self]

    def __len__(self):
        return len(self.keys())

    def __contains__(self, key):
        return self._ekey(key) in self.environ


class HeaderProperty(object):
    def __init__(self, name, reader=None, writer=None, default=''):
        self.name, self.default = name, default
        self.reader, self.writer = reader, writer
        self.__doc__ = 'Current value of the %r header.' % name.title()

    def __get__(self, obj, cls):
        if obj is None: return self
        value = obj.get_header(self.name, self.default)
        return self.reader(value) if self.reader else value

    def __set__(self, obj, value):
        obj[self.name] = self.writer(value) if self.writer else value

    def __delete__(self, obj):
        del obj[self.name]


class FileUpload(object):

    def __init__(self, fileobj, name, filename, headers=None):
        """ 文件上传的包装器。 """
        #: Open file(-like) object (BytesIO buffer or temporary file)
        self.file = fileobj
        #: Name of the upload form field
        self.name = name
        #: Raw filename as sent by the client (may contain unsafe characters)
        self.raw_filename = filename
        #: A :class:`HeaderDict` with additional headers (e.g. content-type)
        self.headers = HeaderDict(headers) if headers else HeaderDict()

    content_type = HeaderProperty('Content-Type')
    content_length = HeaderProperty('Content-Length', reader=int, default=-1)

    def get_header(self, name, default=None):
        """ 返回mulripart部分中的头的值. """
        return self.headers.get(name, default)

    @cached_property
    def filename(self):
        """ 客户端文件系统上的文件名，但已规范化以确保文件系统兼容性。空文件名返回为“empty”。
        只能使用ASCII字母、数字、破折号、下划线和点在最终文件名中允许。如果可能的话，口音会被去除。
        空白被一个破折号代替。前导点或尾随点或删除破折号。文件名限制为255个字符。
        """
        fname = self.raw_filename
        if not isinstance(fname, str):
            fname = fname.decode('utf8', 'ignore')
        fname = normalize('NFKD', fname).encode('ASCII', 'ignore').decode('ASCII')
        fname = os.path.basename(fname.replace('\\', os.path.sep))
        fname = re.sub(r'[^a-zA-Z0-9-_.\s]', '', fname).strip()
        fname = re.sub(r'[-\s]+', '-', fname).strip('.-')
        return fname[:255] or 'empty'

    def _copy_file(self, fp, chunk_size=2 ** 16):
        read, write, offset = self.file.read, fp.write, self.file.tell()
        while 1:
            buf = read(chunk_size)
            if not buf: break
            write(buf)
        self.file.seek(offset)

    def save(self, destination, overwrite=False, chunk_size=2 ** 16):
        R""" 将文件保存到磁盘或将其内容复制到打开的文件（-like）对象。
        如果*destination*是目录，：attr:`filename`将添加到路径。
        默认情况下不会覆盖现有文件（IOError）。
        ：param destination:文件路径、目录或文件（-like）对象。
        ：param overwrite：如果为True，则替换现有文件。（默认值：False）
        ：param chunk\u size：一次读取的字节数。（默认值：64kb）
        """
        if isinstance(destination, str):  # Except file-likes here
            if os.path.isdir(destination):
                destination = os.path.join(destination, self.filename)
            if not overwrite and os.path.exists(destination):
                raise IOError('File exists.')
            with open(destination, 'wb') as fp:
                self._copy_file(fp, chunk_size)
        else:
            self._copy_file(destination, chunk_size)
