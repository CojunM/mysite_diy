#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/16 12:39
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : util.py
# @Project : mysite_diy
# @Software: PyCharm
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""

import binascii
# import hashlib
import json
import os
import pickle
import re
import socket
import threading as _threading
import warnings
import weakref
import zlib
from base64 import b64decode as _b64decode, b64encode as _b64encode
from datetime import datetime, timedelta
from hashlib import md5
from inspect import signature as func_signature, getsourcefile
from threading import local as _tlocal
# from beaker.converters import asbool
from unittest import SkipTest

from brick.contrib.sessions import exceptions

#
# py3k = getattr(sys, 'py3kwarning', False) or sys.version_info >= (3, 0)
# py24 = sys.version_info < (2, 5)
# jython = sys.platform.startswith('java')
# if py3k or jython:
#     import pickle
# else:
#     import cPickle as pickle

xrange_ = range
NoneType = type(None)

string_type = str
unicode_text = str
byte_string = bytes
DEFAULT_CACHE_KEY_LENGTH = 250


def im_func(f):
    return getattr(f, '__func__', None)


def default_im_func(f):
    return getattr(f, '__func__', f)


def im_self(f):
    return getattr(f, '__self__', None)


def im_class(f):
    self = im_self(f)
    if self is not None:
        return self.__class__
    else:
        return None


def b64decode(b):
    return _b64decode(b.encode('ascii'))


def b64encode(s):
    return _b64encode(s).decode('ascii')


def u_(s):
    return str(s)


def bytes_(s):
    if isinstance(s, byte_string):
        return s
    return str(s).encode('ascii', 'strict')


def dictkeyslist(d):
    return list(d.keys())


__all__ = ["ThreadLocal", "WeakValuedRegistry", "SyncDict", "encoded_path",
           "verify_directory", 'parse_cache_config_options',
           "serialize", "deserialize", 'coerce_session_params']


def function_named(fn, name):
    """Return a function with a given __name__.

    Will assign to __name__ and return the original function if possible on
    the Python implementation, otherwise a new function will be constructed.

    """
    fn.__name__ = name
    return fn


def skip_if(predicate, reason=None):
    """Skip a test if predicate is true."""
    reason = reason or predicate.__name__

    # from nose import SkipTest#测试框架nose

    def decorate(fn):
        fn_name = fn.__name__

        def maybe(*args, **kw):
            if predicate():
                msg = "'%s' skipped: %s" % (
                    fn_name, reason)
                raise SkipTest(msg)

            else:
                return fn(*args, **kw)

        return function_named(maybe, fn_name)

    return decorate


def assert_raises(except_cls, callable_, *args, **kw):
    """Assert the given exception is raised by the given function + arguments."""

    try:
        callable_(*args, **kw)
        success = False
    except except_cls:
        success = True

    # assert outside the block so it works for AssertionError too !
    assert success, "Callable did not raise an exception"


def verify_directory(dir):
    """verifies and creates a directory.  tries to
    ignore collisions with other threads and processes.
    验证并创建目录。尝试忽略与其他线程和进程的冲突。"""

    tries = 0
    while not os.access(dir, os.F_OK):  # 用来检测是否有访问权限的路径
        try:
            tries += 1
            os.makedirs(dir)  # 用于递归创建目录
            print(tries)
        except:
            if tries > 5:
                raise


def has_self_arg(func):
    """Return True if the given function has a 'self' argument.
    如果给定函数具有“self”参数，则返回true。"""
    args = list(func_signature(func).parameters)# 获取函数签名
    if args and args[0] in ('self', 'cls'):
        return True
    else:
        return False


def warn(msg, stacklevel=3):
    """Issue a warning."""
    if isinstance(msg, string_type):
        warnings.warn(msg, exceptions.BeakerWarning, stacklevel=stacklevel)
    else:
        warnings.warn(msg, stacklevel=stacklevel)


def deprecated(message):
    def wrapper(fn):
        def deprecated_method(*args, **kargs):
            warnings.warn(message, DeprecationWarning, 2)
            return fn(*args, **kargs)

        # TODO: use decorator ?  functools.wrapper ?
        deprecated_method.__name__ = fn.__name__
        deprecated_method.__doc__ = "%s\n\n%s" % (message, fn.__doc__)
        return deprecated_method

    return wrapper


class ThreadLocal(object):
    """stores a value on a per-thread basis"""

    __slots__ = '_tlocal'

    def __init__(self):
        self._tlocal = _tlocal()

    def put(self, value):
        self._tlocal.value = value

    def has(self):
        """
        是否有值
        :return: bool
        """
        return hasattr(self._tlocal, 'value')

    def get(self, default=None):
        return getattr(self._tlocal, 'value', default)

    def remove(self):
        del self._tlocal.value


class SyncDict(object):
    """同步字典
    An efficient/threadsafe singleton map algorithm, a.k.a.
    "get a value based on this key, and create if not found or not
    valid" paradigm:

        exists && isvalid ? get : create

    Designed to work with weakref dictionaries to expect items
    to asynchronously disappear from the dictionary.

    Use python 2.3.3 or greater !  a major bug was just fixed in Nov.
    2003 that was driving me nuts with garbage collection/weakrefs in
    this section.
    一种高效/线程安全的单例映射算法，简称a.k.a。“基于此键获取值，如果未找到或未找到，则创建
    “有效”范例：是否存在有效（&amp;I）？获取：创建设计用于与weakref字典一起使用，以预期项目
    从字典中异步消失。使用python 2.3.3或更高版本！去年11月，一个主要错误刚刚修复。
    2003年，垃圾收集/垃圾收集让我抓狂
    这部分。
    """

    def __init__(self):
        self.mutex = _threading.Lock()
        self.dict = {}

    def get(self, key, createfunc, *args, **kwargs):
        try:
            if key in self.dict:
                return self.dict[key]
            else:
                return self.sync_get(key, createfunc, *args, **kwargs)
        except KeyError:
            return self.sync_get(key, createfunc, *args, **kwargs)

    def sync_get(self, key, createfunc, *args, **kwargs):
        self.mutex.acquire()
        # print('key: ',key)
        # print('createfunc: ', createfunc)
        try:
            try:
                if key in self.dict:
                    # print('key in self.dict')
                    return self.dict[key]
                else:
                    # print('_create')
                    return self._create(key, createfunc, *args, **kwargs)  # createfunc  返回ConditionSynchronizer实列
            except KeyError:
                return self._create(key, createfunc, *args, **kwargs)
        finally:
            self.mutex.release()

    def _create(self, key, createfunc, *args, **kwargs):
        self[key] = obj = createfunc(*args, **kwargs)
        return obj

    def has_key(self, key):
        return key in self.dict

    def __contains__(self, key):
        return self.dict.__contains__(key)

    def __getitem__(self, key):
        return self.dict.__getitem__(key)

    def __setitem__(self, key, value):
        self.dict.__setitem__(key, value)

    def __delitem__(self, key):
        return self.dict.__delitem__(key)

    def clear(self):
        self.dict.clear()


class WeakValuedRegistry(SyncDict):
    """
    弱值注册
    """

    def __init__(self):
        super().__init__()
        self.mutex = _threading.RLock()
        # 使用weakref模块，你可以创建到对象的弱引用，Python在对象的引用计数为0或只存在对象的弱引用时将回收这个对象。
        # https: // blog.csdn.net / qdx411324962 / article / details / 47291265
        # https://blog.csdn.net/lijiachang8/article/details/115772641
        self.dict = weakref.WeakValueDictionary()


sha1 = None


def encoded_path(root, identifiers, extension=".enc", depth=3,
                 digest_filenames=True):
    """Generate a unique file-accessible path from the given list of
    identifiers starting at the given root directory.
    从给定的文件列表中生成唯一的文件可访问路径从给定根目录开始的标识符"""
    ident = "_".join(identifiers)
    # print('ident: ', ident)
    global sha1
    if sha1 is None:
        from hashlib import sha1

    if digest_filenames:  # 摘要文件名
        if isinstance(ident, unicode_text):
            ident = sha1(ident.encode('utf-8')).hexdigest()  # 返回摘要，作为十六进制数据字符串值
        else:
            ident = sha1(ident).hexdigest()

    # os.path.basename()
    # 返回path最后的文件名。若path以 / 或\结尾，则返回空值。 即os.path.split(path)
    # 的第二个元素。
    ident = os.path.basename(ident)
    print('ident1: ', ident)
    tokens = []
    for d in range(1, depth):
        tokens.append(ident[0:d])
        print('ident[0:d]: ', ident[0:d])
    dir = os.path.join(root, *tokens)
    print('dir: ', dir)
    verify_directory(dir)
    print(os.path.join(dir, ident + extension))
    return os.path.join(dir, ident + extension)


def asint(obj):
    if isinstance(obj, int):
        return obj
    elif isinstance(obj, string_type) and re.match(r'^\d+$', obj):
        return int(obj)
    else:
        raise Exception("This is not a proper int")


def asbool(obj):
    if isinstance(obj, string_type):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError(
                "String is not true/false: %r" % obj)
    return bool(obj)


def verify_options(opt, types, error):
    # #print("opt:", opt)
    # #print("types:", types)
    if not isinstance(opt, types):
        if not isinstance(types, tuple):
            types = (types,)
        coerced = False
        for typ in types:
            # #print("typ:", typ)
            try:
                if typ in (list, tuple):
                    opt = [x.strip() for x in opt.split(',')]
                else:
                    if typ == bool:
                        typ = asbool
                    elif typ == int:
                        typ = asint
                    elif typ in (timedelta, datetime):
                        if not isinstance(opt, typ):
                            raise Exception("%s requires a timedelta type", typ)
                    opt = typ(opt)
                coerced = True
            except:
                pass
            if coerced:
                break
        if not coerced:
            raise Exception(error)
        # #print("opt1:", opt)
    elif isinstance(opt, str) and not opt.strip():
        raise Exception("Empty strings are invalid for: %s" % error)
    # #print("opt2:", opt)
    return opt


def verify_rules(params, ruleset):
    for key, types, message in ruleset:
        if key in params:
            # #print('keyvr:', key)
            params[key] = verify_options(params[key], types, message)
    return params


def coerce_session_params(params):
    rules = [
        ('data_dir', (str, NoneType), "data_dir must be a string referring to a directory."),
        ('lock_dir', (str, NoneType), "lock_dir must be a string referring to a directory."),
        ('type', (str, NoneType), "Session type must be a string."),
        ('cookie_expires', (bool, datetime, timedelta, int),
         "Cookie expires was not a boolean, datetime, int, or timedelta instance."),
        ('cookie_domain', (str, NoneType), "Cookie domain must be a string."),
        ('cookie_path', (str, NoneType), "Cookie path must be a string."),
        ('id', (str,), "Session id must be a string."),
        ('key', (str,), "Session key must be a string."),
        ('secret', (str, NoneType), "Session secret must be a string."),
        ('validate_key', (str, NoneType), "Session encrypt_key must be a string."),
        ('encrypt_key', (str, NoneType), "Session validate_key must be a string."),
        ('encrypt_nonce_bits', (int, NoneType), "Session encrypt_nonce_bits must be a number"),
        ('secure', (bool, NoneType), "Session secure must be a boolean."),
        ('httponly', (bool, NoneType), "Session httponly must be a boolean."),
        ('timeout', (int, NoneType), "Session timeout must be an integer."),
        ('save_accessed_time', (bool, NoneType),
         "Session save_accessed_time must be a boolean (defaults to true)."),
        ('auto', (bool, NoneType), "Session is created if accessed."),
        ('webtest_varname', (str, NoneType), "Session varname must be a string."),
        ('data_serializer', (str,), "data_serializer must be a string.")
    ]
    opts = verify_rules(params, rules)
    cookie_expires = opts.get('cookie_expires')
    if cookie_expires and isinstance(cookie_expires, int) and \
            not isinstance(cookie_expires, bool):
        opts['cookie_expires'] = timedelta(seconds=cookie_expires)
        # timedelta对象代表两个时间之间的时间差，两个date或datetime对象相减就可以返回一个timedelta对象。

    if opts.get('timeout') is not None and not opts.get('save_accessed_time', True):
        raise Exception("save_accessed_time must be true to use timeout")
    # print("opts:", opts)
    return opts


def coerce_cache_params(params):
    rules = [
        ('data_dir', (str, NoneType), "data_dir must be a string referring to a directory."),
        ('lock_dir', (str, NoneType), "lock_dir must be a string referring to a directory."),
        ('type', (str,), "Cache type must be a string."),
        ('enabled', (bool, NoneType), "enabled must be true/false if present."),
        ('expire', (int, NoneType),
         "expire must be an integer representing how many seconds the cache is valid for"),
        ('regions', (list, tuple, NoneType),
         "Regions must be a comma separated list of valid regions"),
        ('key_length', (int, NoneType),
         "key_length must be an integer which indicates the longest a key can be before hashing"),
    ]
    return verify_rules(params, rules)


def coerce_memcached_behaviors(behaviors):
    rules = [
        ('cas', (bool, int), 'cas must be a boolean or an integer'),
        ('no_block', (bool, int), 'no_block must be a boolean or an integer'),
        ('receive_timeout', (int,), 'receive_timeout must be an integer'),
        ('send_timeout', (int,), 'send_timeout must be an integer'),
        ('ketama_hash', (str,),
         'ketama_hash must be a string designating a valid hashing strategy option'),
        ('_poll_timeout', (int,), '_poll_timeout must be an integer'),
        ('auto_eject', (bool, int), 'auto_eject must be an integer'),
        ('retry_timeout', (int,), 'retry_timeout must be an integer'),
        ('_sort_hosts', (bool, int), '_sort_hosts must be an integer'),
        ('_io_msg_watermark', (int,), '_io_msg_watermark must be an integer'),
        ('ketama', (bool, int), 'ketama must be a boolean or an integer'),
        ('ketama_weighted', (bool, int), 'ketama_weighted must be a boolean or an integer'),
        ('_io_key_prefetch', (int, bool), '_io_key_prefetch must be a boolean or an integer'),
        ('_hash_with_prefix_key', (bool, int),
         '_hash_with_prefix_key must be a boolean or an integer'),
        ('tcp_nodelay', (bool, int), 'tcp_nodelay must be a boolean or an integer'),
        ('failure_limit', (int,), 'failure_limit must be an integer'),
        ('buffer_requests', (bool, int), 'buffer_requests must be a boolean or an integer'),
        ('_socket_send_size', (int,), '_socket_send_size must be an integer'),
        ('num_replicas', (int,), 'num_replicas must be an integer'),
        ('remove_failed', (int,), 'remove_failed must be an integer'),
        ('_noreply', (bool, int), '_noreply must be a boolean or an integer'),
        ('_io_bytes_watermark', (int,), '_io_bytes_watermark must be an integer'),
        ('_socket_recv_size', (int,), '_socket_recv_size must be an integer'),
        ('distribution', (str,),
         'distribution must be a string designating a valid distribution option'),
        ('connect_timeout', (int,), 'connect_timeout must be an integer'),
        ('hash', (str,), 'hash must be a string designating a valid hashing option'),
        ('verify_keys', (bool, int), 'verify_keys must be a boolean or an integer'),
        ('dead_timeout', (int,), 'dead_timeout must be an integer')
    ]
    return verify_rules(behaviors, rules)


def parse_cache_config_options(config, include_defaults=True):
    """Parse configuration options and validate for use with the
    CacheManager"""

    # Load default cache options
    if include_defaults:
        options = dict(type='memory', data_dir=None, expire=None,
                       log_file=None)
    else:
        options = {}
    for key, val in config.items():
        if key.startswith('beaker.cache.'):
            options[key[13:]] = val
        if key.startswith('cache.'):
            options[key[6:]] = val
    coerce_cache_params(options)

    # Set cache to enabled if not turned off
    if 'enabled' not in options and include_defaults:
        options['enabled'] = True

    # Configure region dict if regions are available
    regions = options.pop('regions', None)
    if regions:
        region_configs = {}
        for region in regions:
            if not region:  # ensure region name is valid
                continue
            # Setup the default cache options
            region_options = dict(data_dir=options.get('data_dir'),
                                  lock_dir=options.get('lock_dir'),
                                  type=options.get('type'),
                                  enabled=options['enabled'],
                                  expire=options.get('expire'),
                                  key_length=options.get('key_length', DEFAULT_CACHE_KEY_LENGTH))
            region_prefix = '%s.' % region
            region_len = len(region_prefix)
            for key in dictkeyslist(options):
                if key.startswith(region_prefix):
                    region_options[key[region_len:]] = options.pop(key)
            coerce_cache_params(region_options)
            region_configs[region] = region_options
        options['cache_regions'] = region_configs
    return options


def parse_memcached_behaviors(config):
    """Parse behavior options and validate for use with pylibmc
    client/PylibMCNamespaceManager, or potentially other memcached
    NamespaceManagers that support behaviors"""
    behaviors = {}

    for key, val in config.items():
        if key.startswith('behavior.'):
            behaviors[key[9:]] = val

    coerce_memcached_behaviors(behaviors)
    return behaviors


def func_namespace(func):
    """Generates a unique namespace for a function
    为函数生成唯一的命名空间
    """
    kls = None
    if hasattr(func, 'im_func') or hasattr(func, '__func__'):
        kls = im_class(func)
        func = im_func(func)

    if kls:
        return '%s.%s' % (kls.__module__, kls.__name__)
    else:
        return '%s|%s' % (getsourcefile(func), func.__name__)  # getsourcefile 返回object的python源文件名


class PickleSerializer(object):
    def loads(self, data_string):
        return pickle.loads(data_string)

    def dumps(self, data):
        return pickle.dumps(data, 2)


class JsonSerializer(object):
    def loads(self, data_string):
        return json.loads(zlib.decompress(data_string).decode('utf-8'))

    # zlib.compress返回的是压缩后的字节
    def dumps(self, data):
        return zlib.compress(json.dumps(data).encode('utf-8'))


def serialize(data, method):
    if method == 'json':
        serializer = JsonSerializer()
    else:
        serializer = PickleSerializer()
    return serializer.dumps(data)


def deserialize(data_string, method):
    if method == 'json':
        serializer = JsonSerializer()
    else:
        serializer = PickleSerializer()
    return serializer.loads(data_string)


def machine_identifier():
    machine_hash = md5()
    machine_hash.update(socket.gethostname().encode())

    return binascii.hexlify(machine_hash.digest()[0:3]).decode('ascii')


def safe_write(filepath, contents):
    """
    创建并写入文件
    :param filepath:
    :param contents:
    :return:
    """
    # print('wb')
    if os.name == 'posix':
        tempname = '%s.temp' % (filepath)
        fh = open(tempname, 'wb')
        fh.write(contents)
        fh.close()
        os.rename(tempname, filepath)
    else:
        fh = open(filepath, 'wb')
        fh.write(contents)
        fh.close()
