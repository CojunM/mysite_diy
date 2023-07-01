#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/2/17 10:36
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : base.py
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
import threading as _threading
import warnings

from brick.contrib.backends import container


class _backends(object):
    initialized = False

    def __init__(self, clsmap):
        self._clsmap = clsmap
        self._mutex = _threading.Lock()

    def __getitem__(self, key):
        try:
            return self._clsmap[key]
        except KeyError as e:
            if not self.initialized:
                self._mutex.acquire()
                try:
                    if not self.initialized:
                        self._init()
                        self.initialized = True

                    return self._clsmap[key]
                finally:
                    self._mutex.release()

            raise e

    def _init(self):
        try:
            import pkg_resources

            # Load up the additional entry point defined backends
            for entry_point in pkg_resources.iter_entry_points('brick.backends'):
                try:
                    namespace_manager = entry_point.load()
                    name = entry_point.name
                    if name in self._clsmap:
                        raise Exception("NamespaceManager name conflict,'%s' "
                                        "already loaded" % name)
                    self._clsmap[name] = namespace_manager
                except (InvalidCacheBackendError, SyntaxError):
                    # Ignore invalid backends
                    pass
                except:
                    import sys
                    from pkg_resources import DistributionNotFound
                    # Warn when there's a problem loading a NamespaceManager
                    if not isinstance(sys.exc_info()[1], DistributionNotFound):
                        import traceback
                        try:
                            from StringIO import StringIO  # Python2
                        except ImportError:
                            from io import StringIO  # Python3

                        tb = StringIO()
                        traceback.print_exc(file=tb)
                        warnings.warn(
                            "Unable to load NamespaceManager "
                            "entry point: '%s': %s" % (
                                entry_point,
                                tb.getvalue()),
                            RuntimeWarning, 2)
        except ImportError:
            pass


class InvalidCacheBackendError(ImportError,Exception ):
    pass


# Initialize the basic available backends
clsmap = _backends({
    'memory': container.MemoryNamespaceManager,
    'dbm': container.DBMNamespaceManager,
    'file': container.FileNamespaceManager,
    # 'ext:memcached': memcached.MemcachedNamespaceManager,
    # 'ext:database': database.DatabaseNamespaceManager,
    # 'ext:sqla': sqla.SqlaNamespaceManager,
    # 'ext:google': google.GoogleNamespaceManager,
    # 'ext:mongodb': mongodb.MongoNamespaceManager,
    # 'ext:redis': redisnm.RedisNamespaceManager
})
