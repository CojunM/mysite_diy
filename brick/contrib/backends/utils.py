#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/1/20 21:10
# @Author  : Cojun 
# @Site    : 
# @File    : utils.py
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
import json
import os
import pickle
import re
import threading as _threading
import warnings
import weakref
import zlib
from threading import local as _tlocal
from datetime import timedelta, datetime

from inspect import signature as func_signature, getsourcefile

DEFAULT_CACHE_KEY_LENGTH = 250
NoneType = type(None)
xrange_ = range

string_type = str
unicode_text = str
byte_string = bytes
sha1 = None


def dictkeyslist(d):
    return list(d.keys())


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


def has_self_arg(func):
    """Return True if the given function has a 'self' argument."""
    args = list(func_signature(func).parameters)
    if args and args[0] in ('self', 'cls'):
        return True
    else:
        return False


class SyncDict(object):
    """
    An efficient/threadsafe singleton map algorithm, a.k.a.
    "get a value based on this key, and create if not found or not
    valid" paradigm:

        exists && isvalid ? get : create

    Designed to work with weakref dictionaries to expect items
    to asynchronously disappear from the dictionary.

    Use python 2.3.3 or greater !  a major bug was just fixed in Nov.
    2003 that was driving me nuts with garbage collection/weakrefs in
    this section.

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
        try:
            try:
                if key in self.dict:
                    return self.dict[key]
                else:
                    return self._create(key, createfunc, *args, **kwargs)
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
    def __init__(self):
        self.mutex = _threading.RLock()
        self.dict = weakref.WeakValueDictionary()


class ThreadLocal(object):
    """stores a value on a per-thread basis"""

    __slots__ = '_tlocal'

    def __init__(self):
        self._tlocal = _tlocal()

    def put(self, value):
        self._tlocal.value = value

    def has(self):
        return hasattr(self._tlocal, 'value')

    def get(self, default=None):
        return getattr(self._tlocal, 'value', default)

    def remove(self):
        del self._tlocal.value


def verify_directory(dir):
    """
    验证并创建目录。试图忽略与其他线程和进程的冲突。
    :param dir:
    :return:
    """

    tries = 0
    while not os.access(dir, os.F_OK):
        try:
            tries += 1
            os.makedirs(dir)
        except:
            if tries > 5:
                raise


def encoded_path(root, identifiers, extension=".enc", depth=3,
                 digest_filenames=True):
    """
    从给定列表中生成唯一的文件可访问路径从给定根目录开始的标识符。
    :param root:
    :param identifiers:
    :param extension:
    :param depth:
    :param digest_filenames:
    :return:
    """
    ident = "_".join(identifiers)

    global sha1
    if sha1 is None:
        from hashlib import sha1

    if digest_filenames:
        if isinstance(ident, unicode_text):
            ident = sha1(ident.encode('utf-8')).hexdigest()
        else:
            ident = sha1(ident).hexdigest()

    ident = os.path.basename(ident)

    tokens = []
    for d in range(1, depth):
        tokens.append(ident[0:d])

    dir = os.path.join(root, *tokens)
    verify_directory(dir)

    return os.path.join(dir, ident + extension)


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


def func_namespace(func):
    """Generates a unique namespace for a function"""
    kls = None
    if hasattr(func, 'im_func') or hasattr(func, '__func__'):
        kls = im_class(func)
        func = im_func(func)

    if kls:
        return '%s.%s' % (kls.__module__, kls.__name__)
    else:
        return '%s|%s' % (getsourcefile(func), func.__name__)


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


def asint(obj):
    if isinstance(obj, int):
        return obj
    elif isinstance(obj, string_type) and re.match(r'^\d+$', obj):
        return int(obj)
    else:
        raise Exception("This is not a proper int")


def verify_options(opt, types, error):
    if not isinstance(opt, types):
        if not isinstance(types, tuple):
            types = (types,)
        coerced = False
        for typ in types:
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
    elif isinstance(opt, str) and not opt.strip():
        raise Exception("Empty strings are invalid for: %s" % error)
    return opt


def verify_rules(params, ruleset):
    for key, types, message in ruleset:
        if key in params:
            params[key] = verify_options(params[key], types, message)
    return params


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


def safe_write(filepath, contents):
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


def u_(s):
    return str(s)


def bindfuncargs(arginfo, args, kwargs):
    boundargs = func_signature(arginfo).bind(*args, **kwargs)
    return boundargs.args, boundargs.kwargs

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

    if opts.get('timeout') is not None and not opts.get('save_accessed_time', True):
        raise Exception("save_accessed_time must be true to use timeout")

    return opts


class PickleSerializer(object):
    def loads(self, data_string):
        return pickle.loads(data_string)

    def dumps(self, data):
        return pickle.dumps(data, 2)


class JsonSerializer(object):
    def loads(self, data_string):
        return json.loads(zlib.decompress(data_string).decode('utf-8'))

    def dumps(self, data):
        return zlib.compress(json.dumps(data).encode('utf-8'))

class BrickWarning(RuntimeWarning):
    """Issued at runtime."""

def warn(msg, stacklevel=3):
    """Issue a warning."""
    if isinstance(msg, string_type):
        warnings.warn(msg,  BrickWarning, stacklevel=stacklevel)
    else:
        warnings.warn(msg, stacklevel=stacklevel)

