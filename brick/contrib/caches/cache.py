#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/1/18 22:20
# @Author  : Cojun 
# @Site    : 
# @File    : cache.py
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

import time

from functools import wraps
from itertools import chain

from brick.contrib.backends import utils
from brick.contrib.backends.base import clsmap
from brick.contrib.backends.container import debug

from brick.contrib.caches.exceptions import InvalidCacheBackendError
from brick.contrib.backends.utils import sha1, unicode_text, u_, bindfuncargs

cache_managers = {}


#
# class _backends(object):
#     initialized = False
#
#     def __init__(self, clsmap):
#         self._clsmap = clsmap
#         self._mutex = _threading.Lock()
#
#     def __getitem__(self, key):
#         try:
#             return self._clsmap[key]
#         except KeyError as e:
#             if not self.initialized:
#                 self._mutex.acquire()
#                 try:
#                     if not self.initialized:
#                         self._init()
#                         self.initialized = True
#
#                     return self._clsmap[key]
#                 finally:
#                     self._mutex.release()
#
#             raise e
#
#     def _init(self):
#         try:
#             import pkg_resources
#
#             # Load up the additional entry point defined backends
#             for entry_point in pkg_resources.iter_entry_points('beaker.backends'):
#                 try:
#                     namespace_manager = entry_point.load()
#                     name = entry_point.name
#                     if name in self._clsmap:
#                         raise CacheException("NamespaceManager name conflict,'%s' "
#                                              "already loaded" % name)
#                     self._clsmap[name] = namespace_manager
#                 except (InvalidCacheBackendError, SyntaxError):
#                     # Ignore invalid backends
#                     pass
#                 except:
#                     import sys
#                     from pkg_resources import DistributionNotFound
#                     # Warn when there's a problem loading a NamespaceManager
#                     if not isinstance(sys.exc_info()[1], DistributionNotFound):
#                         import traceback
#                         try:
#                             from StringIO import StringIO  # Python2
#                         except ImportError:
#                             from io import StringIO  # Python3
#
#                         tb = StringIO()
#                         traceback.print_exc(file=tb)
#                         warnings.warn(
#                             "Unable to load NamespaceManager "
#                             "entry point: '%s': %s" % (
#                                 entry_point,
#                                 tb.getvalue()),
#                             RuntimeWarning, 2)
#         except ImportError:
#             pass
#
#
# # Initialize the basic available backends
# clsmap = _backends({
#     'memory': container.MemoryNamespaceManager,
#     'dbm': container.DBMNamespaceManager,
#     'file': container.FileNamespaceManager,
#     # 'ext:memcached': memcached.MemcachedNamespaceManager,
#     # 'ext:database': database.DatabaseNamespaceManager,
#     # 'ext:sqla': sqla.SqlaNamespaceManager,
#     # 'ext:google': google.GoogleNamespaceManager,
#     # 'ext:mongodb': mongodb.MongoNamespaceManager,
#     # 'ext:redis': redisnm.RedisNamespaceManager
# })


class Cache(object):
    """Front-end to the containment API implementing a data cache.

    :param namespace: the namespace of this Cache

    :param type: type of cache to use

    :param expire: seconds to keep cached data

    :param expiretime: seconds to keep cached data (legacy support)

    :param starttime: time when cache was cache was

    """

    def __init__(self, namespace, type='memory', expiretime=None,
                 starttime=None, expire=None, **nsargs):
        try:
            cls = clsmap[type]
            if isinstance(cls, InvalidCacheBackendError):
                raise cls
        except KeyError:
            raise TypeError("Unknown cache implementation %r" % type)

        if expire is not None:
            expire = int(expire)

        self.namespace_name = namespace
        self.namespace = cls(namespace, **nsargs)
        self.expiretime = expiretime or expire
        self.starttime = starttime
        self.nsargs = nsargs

    # @classmethod
    # def _get_cache(cls, namespace, kw):
    #     key = namespace + str(kw)
    #     try:
    #         return cache_managers[key]
    #     except KeyError:
    #         cache_managers[key] = cache = cls(namespace, **kw)
    #         return cache
    #
    # def put(self, key, value, **kw):
    #     self._get_value(key, **kw).set_value(value)

    # set_value = put

    # get_value = get

    # def remove_value(self, key, **kw):
    #     mycontainer = self._get_value(key, **kw)
    #     mycontainer.clear_value()
    #
    # remove = remove_value

    @utils.deprecated("Specifying a "
                      "'type' and other namespace configuration with cache.get()/put()/etc. "
                      "is deprecated. Specify 'type' and other namespace configuration to "
                      "cache_manager.get_cache() and/or the Cache constructor instead.")
    def _legacy_get_value(self, key, type, **kw):
        expiretime = kw.pop('expiretime', self.expiretime)
        starttime = kw.pop('starttime', None)
        createfunc = kw.pop('createfunc', None)
        kwargs = self.nsargs.copy()
        kwargs.update(kw)
        c = Cache(self.namespace.namespace, type=type, **kwargs)
        return c._get_value(key, expiretime=expiretime, createfunc=createfunc,
                            starttime=starttime)

    def clear(self):
        """Clear all the values from the namespace"""
        self.namespace.remove()

    def has_value(self, key):
        """return true if the container has a value stored.

        This is regardless of it being expired or not.

        """
        self.namespace.acquire_read_lock()
        try:
            return key in self.namespace
        finally:
            self.namespace.release_read_lock()

    def can_have_value(self):
        return self.has_current_value() or self.createfunc is not None

    def has_current_value(self, key):
        self.namespace.acquire_read_lock()
        try:
            has_value = key in self.namespace
            if has_value:
                try:
                    stored, expired, value = self._get_value()
                    return not self._is_expired(stored, expired)
                except KeyError:
                    pass
            return False
        finally:
            self.namespace.release_read_lock()

    def _is_expired(self, storedtime, expiretime):
        """Return true if this container's value is expired."""
        return (
                (
                        self.starttime is not None and
                        storedtime < self.starttime
                )
                or
                (
                        expiretime is not None and
                        time.time() >= expiretime + storedtime
                )
        )

    def get_value(self, key, **kw):
        if isinstance(key, unicode_text):
            key = key.encode('ascii', 'backslashreplace')

        if 'type' in kw:
            return self._legacy_get_value(key, **kw)

        # kw.setdefault('expiretime', self.expiretime)
        # kw.setdefault('starttime', self.starttime)
        self.namespace.acquire_read_lock()
        try:
            has_value = self.has_value(key)
            if has_value:
                try:
                    stored, expired, value = self._get_value(key)
                    if not self._is_expired(stored, expired):
                        return value
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    has_value = False
        finally:
            self.namespace.release_read_lock()
        createfunc = kw.get('createfunc', None)
        if createfunc:
        # raise KeyError(key)
            has_createlock = False
            creation_lock = self.namespace.get_creation_lock(key)
            if has_value:
                if not creation_lock.acquire(wait=False):
                    debug("get_value returning old value while new one is created")
                    return value
                else:
                    debug("lock_creatfunc (didnt wait)")
                    has_createlock = True

            if not has_createlock:
                debug("lock_createfunc (waiting)")
                creation_lock.acquire()
                debug("lock_createfunc (waited)")

            try:
                # see if someone created the value already
                self.namespace.acquire_read_lock()
                try:
                    if self.has_value(key):
                        try:
                            stored, expired, value = self._get_value(key)
                            if not self._is_expired(stored, expired):
                                return value
                        except KeyError:
                            # guard against un-mutexed backends raising KeyError
                            pass
                finally:
                    self.namespace.release_read_lock()

                debug("get_value creating new value")
                v = createfunc()
                self.set_value(key, v)
                return v
            finally:
                creation_lock.release()
                debug("released create lock")
        else:
            return None

    def _get_value(self, key):
        value = self.namespace[key]
        try:
            stored, expired, value = value
        except ValueError:
            if not len(value) == 2:
                raise
            # Old format: upgrade
            stored, value = value
            expired = self.expiretime
            debug("get_value upgrading time %r expire time %r", stored, self.expire_argument)
            self.namespace.release_read_lock()
            self.set_value(value, stored)
            self.namespace.acquire_read_lock()
        except TypeError:
            # occurs when the value is None.  memcached
            # may yank the rug from under us in which case
            # that's the result
            raise KeyError(key)
        return stored, expired, value

    def set_value(self, key, value, storedtime=None):
        self.namespace.acquire_write_lock()
        try:
            if storedtime is None:
                storedtime = time.time()
            debug("set_value stored time %r expire time %r", storedtime, self.expiretime)
            self.namespace.set_value(key, (storedtime, self.expiretime, value),
                                     expiretime=self.expiretime)
        finally:
            self.namespace.release_write_lock()

    def clear_value(self, key):
        self.namespace.acquire_write_lock()
        try:
            debug("clear_value")
            if  key in self.namespace:
                try:
                    del self.namespace[ key]
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    pass
            self.storedtime = -1
        finally:
            self.namespace.release_write_lock()

    # dict interface
    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return self._get_value(key).has_current_value()

    def has_key(self, key):
        return key in self

    def __delitem__(self, key):
        self.clear_value(key)

    def __setitem__(self, key, value):
        self.put(key, value)


class CacheManager(object):
    def __init__(self, **kwargs):
        """Initialize a CacheManager object with a set of options

        Options should be parsed with the
        :func:`~beaker.util.parse_cache_config_options` function to
        ensure only valid options are used.

        """
        self.kwargs = kwargs
        self.regions = kwargs.pop('cache_regions', {})

        # Add these regions to the module global
        # cache_regions.update(self.regions)

    def get_cache(self, name, **kwargs):
        kw = self.kwargs.copy()
        kw.update(kwargs)
        # return Cache._get_cache(name, kw)
        key = name + str(kw)
        try:
            return cache_managers[key]
        except KeyError:
            cache_managers[key] = cache = Cache(name, **kw)
            return cache

    def cache(self, *args, **kwargs):
        """Decorate a function to cache itself with supplied parameters

        :param args: Used to make the key unique for this function, as in region()
            above.

        :param kwargs: Parameters to be passed to get_cache(), will override defaults

        Example::

            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)


            def populate_things():

                @cache.cache('mycache', expire=15)
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)

                return load('rabbits', 20, 0)

        .. note::

            The function being decorated must only be called with
            positional arguments.

        """
        return _cache_decorate(args, self, kwargs )

    def invalidate(self, func, *args, **kwargs):
        """Invalidate a cache decorated function

        This function only invalidates cache spaces created with the
        cache decorator.

        :param func: Decorated function to invalidate

        :param args: Used to make the key unique for this function, as in region()
            above.

        :param kwargs: Parameters that were passed for use by get_cache(), note that
            this is only required if a ``type`` was specified for the
            function

        Example::

            # Assuming a cache object is available like:
            cache = CacheManager(dict_of_config_options)


            def populate_things(invalidate=False):

                @cache.cache('mycache', type="file", expire=15)
                def load(search_term, limit, offset):
                    return load_the_data(search_term, limit, offset)

                # If the results should be invalidated first
                if invalidate:
                    cache.invalidate(load, 'mycache', 'rabbits', 20, 0, type="file")
                return load('rabbits', 20, 0)

        """
        namespace = func._arg_namespace

        cache = self.get_cache(namespace, **kwargs)
        # if hasattr(func, '_arg_region'):
        #     cachereg = cache_regions[func._arg_region]
        #     key_length = cachereg.get('key_length', util.DEFAULT_CACHE_KEY_LENGTH)
        # else:
        #     key_length = kwargs.pop('key_length', util.DEFAULT_CACHE_KEY_LENGTH)
        key_length = kwargs.pop('key_length', utils.DEFAULT_CACHE_KEY_LENGTH)
        _cache_decorator_invalidate(cache, key_length, args)


def _cache_decorate(deco_args, manager, options ):
    """Return a caching function decorator."""

    cache = [None]

    def decorate(func):
        namespace = utils.func_namespace(func)
        skip_self = utils.has_self_arg(func)

        # signature = func_signature(func)
        # signature = func_signature(func)

        @wraps(func)
        def cached(*args, **kwargs):
            if not cache[0]:  # 列表没有内容走这里
                if manager:
                    cache[0] = manager.get_cache(namespace, **options)
                else:
                    raise Exception("'manager + kwargs'  argument is required")
            cache_key_kwargs = []
            if kwargs:
                # kwargs provided, merge them in positional args
                # to avoid having different cache keys.
                args, kwargs = bindfuncargs(func, args, kwargs)
                cache_key_kwargs = [u_(':').join((u_(key), u_(value))) for key, value in kwargs.items()]

            cache_key_args = args
            if skip_self:
                cache_key_args = args[1:]

            cache_key = u_(" ").join(map(u_, chain(deco_args, cache_key_args, cache_key_kwargs)))

            key_length = options.pop('key_length', utils.DEFAULT_CACHE_KEY_LENGTH)

            # TODO: This is probably a bug as length is checked before converting to UTF8
            # which will cause cache_key to grow in size.
            if len(cache_key) + len(namespace) > int(key_length):
                cache_key = sha1(cache_key.encode('utf-8')).hexdigest()

            def go():
                return func(*args, **kwargs)

            # save org function name
            go.__name__ = '_cached_%s' % (func.__name__,)

            return cache[0].get_value(cache_key, createfunc=go)

        cached._arg_namespace = namespace

        return cached

    return decorate


def _cache_decorator_invalidate(cache, key_length, args):
    """Invalidate a cache key based on function arguments."""

    cache_key = u_(" ").join(map(u_, args))
    if len(cache_key) + len(cache.namespace_name) > key_length:
        cache_key = sha1(cache_key.encode('utf-8')).hexdigest()
    cache.remove_value(cache_key)


# 1. 实例化CacheManager
cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '../../../tmp/cache/data',
    'cache.lock_dir': '../../../tmp/cache/lock'
}

cache = CacheManager(**utils.parse_cache_config_options(cache_opts))


def get_data(filename):
    '''获取数据的方式'''
    print(filename)
    with open(filename) as f:
        return f.read()


# 2. 通过装饰器使用缓存
@cache.cache('temp', type='file', expire=100)
def get_results(filename):
    '''要缓存的函数'''
    data = get_data(filename)
    print("----")
    return data

@cache.cache('temp', type='file', expire=10)
def get_results(data):
    data= data
    print("----")
    return data
if __name__ == '__main__':
    # 3. 创建&读取缓存
    # filename = '../../../tmp/test.txt'
    # filename = '../../../tmp/test1'
    # results = get_results(filename)
    # print(results)
    results = get_results(2)
    print(results)
    results1 = get_results(12)
    print(results1)

    # cache.invalidate(get_results, 'temp', filename, type='file')  # 删除特定缓存