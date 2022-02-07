"""Container and Namespace classes"""
# 该模块实现标准的 errno 系统符号，每一个对应于一个整数，名称和描述借鉴了 linux/include/errno.h
import errno  # https://www.cnblogs.com/madsnotes/articles/5688008.html

# from ._compat import pickle, anydbm, add_metaclass, PYVER, unicode_text

# import beaker.util as util
import logging
import os
import time

from webcore.contrib.sessions.exceptions import CreationAbortedError, MissingCacheParameter
from webcore.contrib.sessions.synchronization import _threading, file_synchronizer, \
    mutex_synchronizer, NameLock, null_synchronizer

__all__ = ['Value', 'Container', 'ContainerContext',
           'MemoryContainer', 'DBMContainer', 'NamespaceManager',
           'MemoryNamespaceManager', 'DBMNamespaceManager', 'FileContainer',
           'OpenResourceNamespaceManager',
           'FileNamespaceManager', 'CreationAbortedError']



logger = logging.getLogger('beaker.container')
if logger.isEnabledFor(logging.DEBUG):
    debug = logger.debug
else:
    def debug(message, *args):
        pass


class NamespaceManager(object):
    """Handles dictionary operations and locking for a namespace of
    values.

    :class:`.NamespaceManager` provides a dictionary-like interface,
    implementing ``__getitem__()``, ``__setitem__()``, and
    ``__contains__()``, as well as functions related to lock
    acquisition.

    The implementation for setting and retrieving the namespace data is
    handled by subclasses.

    NamespaceManager may be used alone, or may be accessed by
    one or more :class:`.Value` objects.  :class:`.Value` objects provide per-key
    services like expiration times and automatic recreation of values.

    Multiple NamespaceManagers created with a particular name will all
    share access to the same underlying datasource and will attempt to
    synchronize against a common mutex object.  The scope of this
    sharing may be within a single process or across multiple
    processes, depending on the type of NamespaceManager used.

    The NamespaceManager itself is generally threadsafe, except in the
    case of the DBMNamespaceManager in conjunction with the gdbm dbm
    implementation.
        处理的命名空间的字典操作和锁定
        价值观
        ：班级：`。NamespaceManager提供了一个类似字典的界面，
        实现```getitem```````getitem```````````setitem``````，以及
        ``__包含_（）``，以及与锁相关的函数
        获得
        设置和检索名称空间数据的实现是
        由子类处理。
        NamespaceManager可以单独使用，也可以由用户访问
        一个或多个：类：`。值对象：班级：`。Value`对象为每个键提供
        过期时间和自动重新创建值等服务。
        使用特定名称创建的多个名称空间管理器将
        共享对同一基础数据源的访问，并将尝试
        针对公共互斥对象进行同步。这个范围
        共享可以在单个进程内进行，也可以跨多个进程进行
        进程，具体取决于使用的名称空间管理器的类型。
        NamespaceManager本身通常是线程安全的，但在
        DBMNamespaceManager与gdbm dbm结合的情况
        实施
    """

    @classmethod
    def _init_dependencies(cls):
        """Initialize module-level dependent libraries required
              by this :class:`.NamespaceManager`.
              需要初始化模块级依赖库通过这个：类：`。名称空间管理器`"""

    def __init__(self, namespace):
        self._init_dependencies()
        self.namespace = namespace

    def get_creation_lock(self, key):
        """Return a locking object that is used to synchronize
        multiple threads or processes which wish to generate a new
        cache value.

        This function is typically an instance of
        :class:`.FileSynchronizer`, :class:`.ConditionSynchronizer`,
        or :class:`.null_synchronizer`.

        The creation lock is only used when a requested value
        does not exist, or has been expired, and is only used
        by the :class:`.Value` key-management object in conjunction
        with a "createfunc" value-creation function.
        返回用于同步的锁定对象
        希望生成新线程的多个线程或进程
        缓存值。
        此函数通常是
        ：班级：`。文件同步器“，：类：`。条件同步器`，
        或者：课堂：`。空同步器`。
        创建锁仅在请求值时使用
        不存在，或已过期，仅用于
        作者：班级：`。Value`密钥管理对象
        具有“createfunc”值创建功能。
        """
        raise NotImplementedError()

    def do_remove(self):
        """Implement removal of the entire contents of this
        :class:`.NamespaceManager`.

        e.g. for a file-based namespace, this would remove
        all the files.

        The front-end to this method is the
        :meth:`.NamespaceManager.remove` method.
        执行删除此文件的全部内容
        ：班级：`。NamespaceManager`。
        e、 g.对于基于文件的命名空间，这将删除
        所有的文件。
        这种方法的前端是
        ：冰毒：`。名称空间管理器。删除`方法。
        """
        raise NotImplementedError()

    def acquire_read_lock(self):
        """Establish a read lock.

        This operation is called before a key is read.    By
        default the function does nothing.
        建立一个读锁。  在读取密钥之前调用此操作。通过
        默认情况下，该函数不执行任何操作。
        """

    def release_read_lock(self):
        """Release a read lock.

        This operation is called after a key is read.    By
        default the function does nothing.
        释放读锁。  读取密钥后调用此操作。通过
        默认情况下，该函数不执行任何操作。
        """

    def acquire_write_lock(self, wait=True, replace=False):
        """Establish a write lock.

        This operation is called before a key is written.
        A return value of ``True`` indicates the lock has
        been acquired.

        By default the function returns ``True`` unconditionally.

        'replace' is a hint indicating the full contents
        of the namespace may be safely discarded. Some backends
        may implement this (i.e. file backend won't unpickle the
        current contents).
        建立写锁。在写入密钥之前调用此操作。返回值为“`True`”表示锁已关闭
        已经被收购了。默认情况下，函数无条件返回“True”。
        “replace”是指示全部内容的提示
        可以安全地丢弃名称空间的名称。一些后端可能会实现这一点（即，文件后端不会解锁
        当前内容）。
        """
        return True

    def release_write_lock(self):
        """Release a write lock.

        This operation is called after a new value is written.
        By default this function does nothing.

        """

    def has_key(self, key):
        """Return ``True`` if the given key is present in this
        :class:`.Namespace`.
        """
        return self.__contains__(key)

    def __getitem__(self, key):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def set_value(self, key, value, expiretime=None):
        """Sets a value in this :class:`.NamespaceManager`.

        This is the same as ``__setitem__()``, but
        also allows an expiration time to be passed
        at the same time.

        """
        self[key] = value

    # 在Class里添加__contains__(self, x) 函数,
    # 可判断我们输入的数据是否在Class里.参数x就是我们传入的数据.
    def __contains__(self, key):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def keys(self):
        """Return the list of all keys.

        This method may not be supported by all
        :class:`.NamespaceManager` implementations.

        """
        raise NotImplementedError()

    def remove(self):
        """Remove the entire contents of this
        :class:`.NamespaceManager`.

        e.g. for a file-based namespace, this would remove
        all the files.
        """
        self.do_remove()


class OpenResourceNamespaceManager(NamespaceManager):
    """A NamespaceManager where read/write operations require opening/
    closing of a resource which is possibly mutexed.
    读/写操作需要打开的名称空间管理器/关闭可能已静音的资源。
    """

    def __init__(self, namespace):
        NamespaceManager.__init__(self, namespace)
        self.access_lock = self.get_access_lock()
        self.openers = 0
        self.mutex = _threading.Lock()

    def get_access_lock(self):
        raise NotImplementedError()

    def do_open(self, flags, replace):
        raise NotImplementedError()

    def do_close(self):
        raise NotImplementedError()

    def acquire_read_lock(self):
        self.access_lock.acquire_read_lock()
        try:
            self.open('r', checkcount=True)
        except:
            self.access_lock.release_read_lock()
            raise

    def release_read_lock(self):
        try:
            self.close(checkcount=True)
        finally:
            self.access_lock.release_read_lock()

    def acquire_write_lock(self, wait=True, replace=False):
        r = self.access_lock.acquire_write_lock(wait)
        try:
            if (wait or r):
                self.open('c', checkcount=True, replace=replace)
            return r
        except:
            self.access_lock.release_write_lock()
            raise

    def release_write_lock(self):
        try:
            self.close(checkcount=True)
        finally:
            self.access_lock.release_write_lock()

    def open(self, flags, checkcount=False, replace=False):
        self.mutex.acquire()
        try:
            if checkcount:
                if self.openers == 0:
                    self.do_open(flags, replace)
                self.openers += 1
            else:
                self.do_open(flags, replace)
                self.openers = 1
        finally:
            self.mutex.release()

    def close(self, checkcount=False):
        self.mutex.acquire()
        try:
            if checkcount:
                self.openers -= 1
                if self.openers == 0:
                    self.do_close()
            else:
                if self.openers > 0:
                    self.do_close()
                self.openers = 0
        finally:
            self.mutex.release()

    def remove(self):
        self.access_lock.acquire_write_lock()
        try:
            self.close(checkcount=False)
            self.do_remove()
        finally:
            self.access_lock.release_write_lock()


class Value(object):
    """Implements synchronization, expiration, and value-creation logic
    for a single value stored in a :class:`.NamespaceManager`.
    实现同步、过期和价值创建逻辑对于存储在：类中的单个值：`。NamespaceManager`。
    """

    __slots__ = 'key', 'createfunc', 'expiretime', 'expire_argument', 'starttime', 'storedtime', \
                'namespace'

    def __init__(self, key, namespace, createfunc=None, expiretime=None, starttime=None):
        self.key = key
        self.createfunc = createfunc
        self.expire_argument = expiretime
        self.starttime = starttime
        self.storedtime = -1
        self.namespace = namespace

    def has_value(self):
        """return true if the container has a value stored.

        This is regardless of it being expired or not.

        """
        self.namespace.acquire_read_lock()
        try:
            return self.key in self.namespace
        finally:
            self.namespace.release_read_lock()

    def can_have_value(self):
        return self.has_current_value() or self.createfunc is not None

    def has_current_value(self):
        self.namespace.acquire_read_lock()
        try:
            has_value = self.key in self.namespace
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

    def get_value(self):
        self.namespace.acquire_read_lock()
        try:
            has_value = self.has_value()
            if has_value:
                try:
                    stored, expired, value = self._get_value()
                    if not self._is_expired(stored, expired):
                        return value
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    has_value = False

            if not self.createfunc:
                raise KeyError(self.key)
        finally:
            self.namespace.release_read_lock()

        has_createlock = False
        creation_lock = self.namespace.get_creation_lock(self.key)
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
                if self.has_value():
                    try:
                        stored, expired, value = self._get_value()
                        if not self._is_expired(stored, expired):
                            return value
                    except KeyError:
                        # guard against un-mutexed backends raising KeyError
                        pass
            finally:
                self.namespace.release_read_lock()

            debug("get_value creating new value")
            v = self.createfunc()
            self.set_value(v)
            return v
        finally:
            creation_lock.release()
            debug("released create lock")

    def _get_value(self):
        value = self.namespace[self.key]
        try:
            stored, expired, value = value
        except ValueError:
            if not len(value) == 2:
                raise
            # Old format: upgrade
            stored, value = value
            expired = self.expire_argument
            debug("get_value upgrading time %r expire time %r", stored, self.expire_argument)
            self.namespace.release_read_lock()
            self.set_value(value, stored)
            self.namespace.acquire_read_lock()
        except TypeError:
            # occurs when the value is None.  memcached
            # may yank the rug from under us in which case
            # that's the result
            raise KeyError(self.key)
        return stored, expired, value

    def set_value(self, value, storedtime=None):
        self.namespace.acquire_write_lock()
        try:
            if storedtime is None:
                storedtime = time.time()
            debug("set_value stored time %r expire time %r", storedtime, self.expire_argument)
            self.namespace.set_value(self.key, (storedtime, self.expire_argument, value),
                                     expiretime=self.expire_argument)
        finally:
            self.namespace.release_write_lock()

    def clear_value(self):
        self.namespace.acquire_write_lock()
        try:
            debug("clear_value")
            if self.key in self.namespace:
                try:
                    del self.namespace[self.key]
                except KeyError:
                    # guard against un-mutexed backends raising KeyError
                    pass
            self.storedtime = -1
        finally:
            self.namespace.release_write_lock()


class AbstractDictionaryNSManager(NamespaceManager):
    """A subclassable NamespaceManager that places data in a dictionary.

    Subclasses should provide a "dictionary" attribute or descriptor
    which returns a dict-like object.   The dictionary will store keys
    that are local to the "namespace" attribute of this manager, so
    ensure that the dictionary will not be used by any other namespace.

    e.g.::

        import collections
        cached_data = collections.defaultdict(dict)

        class MyDictionaryManager(AbstractDictionaryNSManager):
            def __init__(self, namespace):
                AbstractDictionaryNSManager.__init__(self, namespace)
                self.dictionary = cached_data[self.namespace]

    The above stores data in a global dictionary called "cached_data",
    which is structured as a dictionary of dictionaries, keyed
    first on namespace name to a sub-dictionary, then on actual
    cache key to value.
    将数据放入字典的子类命名空间管理器。子类应该提供“dictionary”属性或描述符
    返回一个类似dict的对象。这本字典会储存钥匙这是这个管理器的“namespace”属性的本地属性，所以
    确保字典不会被任何其他命名空间使用。
    例如。：：
    导入集合
    缓存的数据=集合。默认dict（dict）
    类MyDictionarySManager（AbstractDictionarySManager）：
    def______________;（self，名称空间）：
    抽象词典管理员__初始化（self，名称空间）
    自己dictionary=缓存的_数据[self.namespace]
    上面的代码将数据存储在一个名为“cached_data”的全局字典中，
    它的结构是一个字典字典，键入
    首先是子字典的名称空间名称，然后是实际名称
    缓存键到值。
    """

    def get_creation_lock(self, key):
        return NameLock(
            identifier="memorynamespace/funclock/%s/%s" %
                       (self.namespace, key),
            reentrant=True
        )

    def __getitem__(self, key):
        return self.dictionary[key]

    def __contains__(self, key):
        return self.dictionary.__contains__(key)

    def has_key(self, key):
        return self.dictionary.__contains__(key)

    def __setitem__(self, key, value):
        self.dictionary[key] = value

    def __delitem__(self, key):
        del self.dictionary[key]

    def do_remove(self):
        self.dictionary.clear()

    def keys(self):
        return self.dictionary.keys()


class MemoryNamespaceManager(AbstractDictionaryNSManager):
    """:class:`.NamespaceManager` that uses a Python dictionary for storage."""

    namespaces = util.SyncDict()

    def __init__(self, namespace, **kwargs):
        AbstractDictionaryNSManager.__init__(self, namespace)
        self.dictionary = MemoryNamespaceManager. \
            namespaces.get(self.namespace, dict)


class DBMNamespaceManager(OpenResourceNamespaceManager):
    """:class:`.NamespaceManager` that uses ``dbm`` files for storage."""

    def __init__(self, namespace, dbmmodule=None, data_dir=None,
                 dbm_dir=None, lock_dir=None,
                 digest_filenames=True, **kwargs):
        self.digest_filenames = digest_filenames

        if not dbm_dir and not data_dir:
            raise MissingCacheParameter("data_dir or dbm_dir is required")
        elif dbm_dir:
            self.dbm_dir = dbm_dir
        else:
            self.dbm_dir = data_dir + "/container_dbm"
        util.verify_directory(self.dbm_dir)

        if not lock_dir and not data_dir:
            raise MissingCacheParameter("data_dir or lock_dir is required")
        elif lock_dir:
            self.lock_dir = lock_dir
        else:
            self.lock_dir = data_dir + "/container_dbm_lock"
        util.verify_directory(self.lock_dir)

        self.dbmmodule = dbmmodule or anydbm

        self.dbm = None
        OpenResourceNamespaceManager.__init__(self, namespace)

        self.file = util.encoded_path(root=self.dbm_dir,
                                      identifiers=[self.namespace],
                                      extension='.dbm',
                                      digest_filenames=self.digest_filenames)

        debug("data file %s", self.file)
        self._checkfile()

    def get_access_lock(self):
        return file_synchronizer(identifier=self.namespace,
                                 lock_dir=self.lock_dir)

    def get_creation_lock(self, key):
        return file_synchronizer(
            identifier="dbmcontainer/funclock/%s/%s" % (
                self.namespace, key
            ),
            lock_dir=self.lock_dir
        )

    def file_exists(self, file):
        if os.access(file, os.F_OK):
            return True
        else:
            for ext in ('db', 'dat', 'pag', 'dir'):
                if os.access(file + os.extsep + ext, os.F_OK):
                    return True

        return False

    def _ensuredir(self, filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            util.verify_directory(dirname)

    def _checkfile(self):
        if not self.file_exists(self.file):
            self._ensuredir(self.file)
            g = self.dbmmodule.open(self.file, 'c')
            g.close()

    def get_filenames(self):
        list = []
        if os.access(self.file, os.F_OK):
            list.append(self.file)

        for ext in ('pag', 'dir', 'db', 'dat'):
            if os.access(self.file + os.extsep + ext, os.F_OK):
                list.append(self.file + os.extsep + ext)
        return list

    def do_open(self, flags, replace):
        debug("opening dbm file %s", self.file)
        try:
            self.dbm = self.dbmmodule.open(self.file, flags)
        except:
            self._checkfile()
            self.dbm = self.dbmmodule.open(self.file, flags)

    def do_close(self):
        if self.dbm is not None:
            debug("closing dbm file %s", self.file)
            self.dbm.close()

    def do_remove(self):
        for f in self.get_filenames():
            os.remove(f)

    def __getitem__(self, key):
        return pickle.loads(self.dbm[key])

    def __contains__(self, key):
        if PYVER == (3, 2):
            # Looks like this is a bug that got solved in PY3.3 and PY3.4
            # http://bugs.python.org/issue19288
            if isinstance(key, unicode_text):
                key = key.encode('UTF-8')
        return key in self.dbm

    def __setitem__(self, key, value):
        self.dbm[key] = pickle.dumps(value)

    def __delitem__(self, key):
        del self.dbm[key]

    def keys(self):
        return self.dbm.keys()


class FileNamespaceManager(OpenResourceNamespaceManager):
    """:class:`.NamespaceManager` that uses binary files for storage.

    Each namespace is implemented as a single file storing a
    dictionary of key/value pairs, serialized using the Python
    ``pickle`` module.
    ：班级：`。NamespaceManager`使用二进制文件进行存储。
    每个名称空间都实现为一个单独的文件，存储键/值对字典，使用Python序列化
    ``pickle``模块。
    """

    def __init__(self, namespace, data_dir=None, file_dir=None, lock_dir=None,
                 digest_filenames=True, **kwargs):
        self.digest_filenames = digest_filenames#文件名摘要

        if not file_dir and not data_dir:
            raise MissingCacheParameter("data_dir or file_dir is required")
        elif file_dir:
            self.file_dir = file_dir
        else:
            self.file_dir = data_dir + "/container_file"
        util.verify_directory(self.file_dir)

        if not lock_dir and not data_dir:
            raise MissingCacheParameter("data_dir or lock_dir is required")
        elif lock_dir:
            self.lock_dir = lock_dir
        else:
            self.lock_dir = data_dir + "/container_file_lock"
        util.verify_directory(self.lock_dir)
        OpenResourceNamespaceManager.__init__(self, namespace)

        self.file = util.encoded_path(root=self.file_dir,
                                      identifiers=[self.namespace],
                                      extension='.cache',
                                      digest_filenames=self.digest_filenames)
        self.hash = {}

        debug("data file %s", self.file)

    def get_access_lock(self):
        return file_synchronizer(identifier=self.namespace,
                                 lock_dir=self.lock_dir)

    def get_creation_lock(self, key):
        return file_synchronizer(
            identifier="dbmcontainer/funclock/%s/%s" % (
                self.namespace, key
            ),
            lock_dir=self.lock_dir
        )

    def file_exists(self, file):
        return os.access(file, os.F_OK)

    def do_open(self, flags, replace):
        if not replace and self.file_exists(self.file):
            try:
                with open(self.file, 'rb') as fh:
                    self.hash = pickle.load(fh)
            except IOError as e:
                # Ignore EACCES and ENOENT as it just means we are no longer
                # able to access the file or that it no longer exists
                if e.errno not in [errno.EACCES, errno.ENOENT]:
                    raise

        self.flags = flags

    def do_close(self):
        if self.flags == 'c' or self.flags == 'w':
            pickled = pickle.dumps(self.hash)
            util.safe_write(self.file, pickled)

        self.hash = {}
        self.flags = None

    def do_remove(self):
        try:
            os.remove(self.file)
        except OSError:
            # for instance, because we haven't yet used this cache,
            # but client code has asked for a clear() operation...
            pass
        self.hash = {}

    def __getitem__(self, key):
        return self.hash[key]

    def __contains__(self, key):
        return key in self.hash

    def __setitem__(self, key, value):
        self.hash[key] = value

    def __delitem__(self, key):
        del self.hash[key]

    def keys(self):
        return self.hash.keys()


#### legacy stuff to support the old "Container" class interface

namespace_classes = {}

ContainerContext = dict


class ContainerMeta(type):
    def __init__(cls, classname, bases, dict_):
        namespace_classes[cls] = cls.namespace_class
        return type.__init__(cls, classname, bases, dict_)

    def __call__(self, key, context, namespace, createfunc=None,
                 expiretime=None, starttime=None, **kwargs):
        if namespace in context:
            ns = context[namespace]
        else:
            nscls = namespace_classes[self]
            context[namespace] = ns = nscls(namespace, **kwargs)
        return Value(key, ns, createfunc=createfunc,
                     expiretime=expiretime, starttime=starttime)


@add_metaclass(ContainerMeta)
class Container(object):
    """Implements synchronization and value-creation logic
    for a 'value' stored in a :class:`.NamespaceManager`.

    :class:`.Container` and its subclasses are deprecated.   The
    :class:`.Value` class is now used for this purpose.

    """
    namespace_class = NamespaceManager


class FileContainer(Container):
    namespace_class = FileNamespaceManager


class MemoryContainer(Container):
    namespace_class = MemoryNamespaceManager


class DBMContainer(Container):
    namespace_class = DBMNamespaceManager


DbmContainer = DBMContainer
