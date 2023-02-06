"""Synchronization functions.

File- and mutex-based mutual exclusion synchronizers are provided,
as well as a name-based mutex which locks within an application
based on a string name.

"""
import os
import sys
import tempfile

from brick.contrib.sessions.exceptions import LockError
from brick.contrib.sessions.util import WeakValuedRegistry, ThreadLocal, encoded_path, verify_directory

try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

# check for fcntl module
try:
    sys.getwindowsversion()
    has_flock = False
except:
    try:
        # https: // www.cnblogs.com / Zzbj / p / 11068131. html
        import fcntl  # 文件锁

        has_flock = True
    except ImportError:
        has_flock = False
#
# from beaker import util
# from beaker.exceptions import LockError

__all__ = ["file_synchronizer", "mutex_synchronizer", "null_synchronizer",
           "NameLock", "_threading"]


class NameLock(object):
    """a proxy for an RLock object that is stored in a name based
    registry.

    Multiple threads can get a reference to the same RLock based on the
    name alone, and synchronize operations related to that name.
    基于名称存储的RLock对象的代理注册表。
    多个线程可以基于并同步与该名称相关的操作。
    """
    locks = WeakValuedRegistry()

    class NLContainer(object):
        def __init__(self, reentrant):
            if reentrant:
                self.lock = _threading.RLock()
            else:
                self.lock = _threading.Lock()

        def __call__(self):
            return self.lock

    def __init__(self, identifier=None, reentrant=False):
        if identifier is None:
            self._lock = NameLock.NLContainer(reentrant)
        else:
            self._lock = NameLock.locks.get(identifier, NameLock.NLContainer,
                                            reentrant)

    def acquire(self, wait=True):
        return self._lock().acquire(wait)

    def release(self):
        self._lock().release()


_synchronizers = WeakValuedRegistry()


def _synchronizer(identifier, cls, **kwargs):
    """
    同步器
    :param identifier:
    :param cls:
    :param kwargs:
    :return:
    """
    # print('_synchronizer identifier:',identifier)
    return _synchronizers.sync_get((identifier, cls), cls, identifier, **kwargs)


def file_synchronizer(identifier, **kwargs):
    """
    文件同步 标识符
    @param identifier:标识符
    @param kwargs:
    @return:
    """
    if not has_flock or 'lock_dir' not in kwargs:
        # print('mutex')
        # print('file_synchronizer identifier:', identifier)
        # print('**kwargs:',kwargs)
        return mutex_synchronizer(identifier)
    else:
        # print('_synchronizer')
        return _synchronizer(identifier, FileSynchronizer, **kwargs)


def mutex_synchronizer(identifier, **kwargs):
    """
    互斥同步器
    :param identifier:
    :param kwargs:
    :return:
    """
    return _synchronizer(identifier, ConditionSynchronizer, **kwargs)


class null_synchronizer(object):
    """A 'null' synchronizer, which provides the :class:`.SynchronizerImpl` interface
    without any locking.
    一个‘null’同步器，它提供：class:`.SynchronizerImpl`接口
    没有任何锁定。
    """

    def acquire_write_lock(self, wait=True):
        return True

    def acquire_read_lock(self):
        pass

    def release_write_lock(self):
        pass

    def release_read_lock(self):
        pass

    acquire = acquire_write_lock
    release = release_write_lock


class SynchronizerImpl(object):
    """Base class for a synchronization object that allows
    multiple readers, single writers.
    同步对象的基类允许多个读者，一个作者。
    """

    def __init__(self):
        self._state = ThreadLocal()

    class SyncState(object):
        __slots__ = 'reentrantcount', 'writing', 'reading'

        def __init__(self):
            self.reentrantcount = 0  # 重入计数
            self.writing = False
            self.reading = False

    def state(self):
        if not self._state.has():
            state = SynchronizerImpl.SyncState()
            self._state.put(state)
            return state
        else:
            # print('self._state.get：',self._state.get())
            return self._state.get()

    state = property(state)

    def release_read_lock(self):
        state = self.state

        if state.writing:
            raise LockError("lock is in writing state")
        if not state.reading:
            raise LockError("lock is not in reading state")

        if state.reentrantcount == 1:
            self.do_release_read_lock()
            state.reading = False

        state.reentrantcount -= 1

    def acquire_read_lock(self, wait=True):
        state = self.state

        if state.writing:
            raise LockError("lock is in writing state")

        if state.reentrantcount == 0:
            x = self.do_acquire_read_lock(wait)
            if (wait or x):
                state.reentrantcount += 1
                state.reading = True
            return x
        elif state.reading:
            state.reentrantcount += 1
            return True

    def release_write_lock(self):
        state = self.state

        if state.reading:
            raise LockError("lock is in reading state")
        if not state.writing:
            raise LockError("lock is not in writing state")

        if state.reentrantcount == 1:
            self.do_release_write_lock()
            state.writing = False

        state.reentrantcount -= 1

    release = release_write_lock

    def acquire_write_lock(self, wait=True):
        state = self.state

        if state.reading:
            raise LockError("lock is in reading state")

        if state.reentrantcount == 0:
            x = self.do_acquire_write_lock(wait)
            if wait or x:
                state.reentrantcount += 1
                state.writing = True
            return x
        elif state.writing:
            state.reentrantcount += 1
            return True

    acquire = acquire_write_lock

    def do_release_read_lock(self):
        raise NotImplementedError()

    def do_acquire_read_lock(self, wait):
        raise NotImplementedError()

    def do_release_write_lock(self):
        raise NotImplementedError()

    def do_acquire_write_lock(self, wait):
        raise NotImplementedError()


class FileSynchronizer(SynchronizerImpl):
    """A synchronizer which locks using flock().
    使用flock（）锁定的同步器。
    """

    def __init__(self, identifier, lock_dir):
        super(FileSynchronizer, self).__init__()
        self._filedescriptor = ThreadLocal()

        if lock_dir is None:
            lock_dir = tempfile.gettempdir()  # 返回保存临时文件的文件夹路径
        else:
            lock_dir = lock_dir

        self.filename = encoded_path(
            lock_dir,
            [identifier],
            extension='.lock'
        )
        self.lock_dir = os.path.dirname(self.filename)
        print(' self.lock_dir', self.lock_dir)

    # 语法：os.path.dirname(path)  功能：去掉文件名，返回目录

    def _filedesc(self):
        return self._filedescriptor.get()

    _filedesc = property(_filedesc)

    def _ensuredir(self):
        if not os.path.exists(self.lock_dir):
            verify_directory(self.lock_dir)

    def _open(self, mode):
        filedescriptor = self._filedesc
        if filedescriptor is None:
            self._ensuredir()
            filedescriptor = os.open(self.filename, mode)
            self._filedescriptor.put(filedescriptor)
        return filedescriptor

    def do_acquire_read_lock(self, wait):
        filedescriptor = self._open(os.O_RDONLY)  # os.O_CREAT: 创建并打开一个新文件os.O_CREAT |
        print('filedescriptor ',filedescriptor)
        if not wait:
            try:
                # 文件只可以读
                fcntl.flock(filedescriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
                return True
            except IOError:
                os.close(filedescriptor)
                self._filedescriptor.remove()
                return False
        else:
            fcntl.flock(filedescriptor, fcntl.LOCK_SH)
            return True

    def do_acquire_write_lock(self, wait):
        filedescriptor = self._open(os.O_CREAT | os.O_WRONLY)
        print('filedescriptor ', filedescriptor)
        if not wait:
            try:
                fcntl.flock(filedescriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except IOError:
                os.close(filedescriptor)
                self._filedescriptor.remove()
                return False
        else:
            fcntl.flock(filedescriptor, fcntl.LOCK_EX)
            return True

    def do_release_read_lock(self):
        self._release_all_locks()

    def do_release_write_lock(self):
        self._release_all_locks()

    def _release_all_locks(self):
        filedescriptor = self._filedesc
        if filedescriptor is not None:
            fcntl.flock(filedescriptor, fcntl.LOCK_UN)
            os.close(filedescriptor)
            self._filedescriptor.remove()


class ConditionSynchronizer(SynchronizerImpl):
    """a synchronizer using a Condition.使用条件的同步器"""

    def __init__(self, identifier):
        super(ConditionSynchronizer, self).__init__()

        # counts how many asynchronous methods are executing
        # 统计正在执行的异步方法数
        self.asynch = 0

        # pointer to thread that is the current sync operation
        # 指向当前同步操作线程的指针
        self.current_sync_operation = None

        # condition object to lock on要锁定的条件对象
        # 有一类线程需要满足条件之后才能够继续执行，
        # Python提供了threading.Condition 对象用于条件变量线程的支持，
        # 此类实现条件变量对象。条件变量允许一个或多个线程等待，直到它们收到另一个线程的通知。
        # 如果给出了 lock 参数，则它必须是 Lock 或 RLock 对象，并且它被用作基础锁。
        # 否则，将创建一个新的 RLock 对象并将其用作基础锁。None
        self.condition = _threading.Condition(_threading.Lock())
        # Condition的底层实现了__enter__和 __exit__协议.所以可以使用with上下文管理器
        # 由Condition的__init__方法可知, 它的底层也是维护了一个RLock锁

    def do_acquire_read_lock(self, wait=True):
        self.condition.acquire()  # 获取底层锁。此方法调用底层锁上的相应方法;返回值是该方法返回的任何值。
        try:
            # see if a synchronous operation is waiting to start
            # or is already running, in which case we wait (or just
            # give up and return)
            if wait:
                while self.current_sync_operation is not None:
                    self.condition.wait()
            else:
                if self.current_sync_operation is not None:
                    return False

            self.asynch += 1
        finally:
            self.condition.release()

        if not wait:
            return True

    def do_release_read_lock(self):
        self.condition.acquire()
        try:
            self.asynch -= 1

            # check if we are the last asynchronous reader thread
            # out the door.
            if self.asynch == 0:
                # yes. so if a sync operation is waiting, notifyAll to wake
                # it up
                if self.current_sync_operation is not None:
                    self.condition.notifyAll()
            elif self.asynch < 0:
                raise LockError("Synchronizer error - too many "
                                "release_read_locks called")
        finally:
            self.condition.release()

    def do_acquire_write_lock(self, wait=True):
        self.condition.acquire()
        try:
            # here, we are not a synchronous reader, and after returning,
            # assuming waiting or immediate availability, we will be.

            if wait:
                # if another sync is working, wait
                while self.current_sync_operation is not None:
                    self.condition.wait()
            else:
                # if another sync is working,
                # we dont want to wait, so forget it
                if self.current_sync_operation is not None:
                    return False

            # establish ourselves as the current sync
            # this indicates to other read/write operations
            # that they should wait until this is None again
            self.current_sync_operation = _threading.currentThread()

            # now wait again for asyncs to finish
            if self.asynch > 0:
                if wait:
                    # wait
                    self.condition.wait()
                else:
                    # we dont want to wait, so forget it
                    self.current_sync_operation = None
                    return False
        finally:
            self.condition.release()

        if not wait:
            return True

    def do_release_write_lock(self):
        self.condition.acquire()
        try:
            if self.current_sync_operation is not _threading.currentThread():
                raise LockError("Synchronizer error - current thread doesnt "
                                "have the write lock")

            # reset the current sync operation so
            # another can get it
            self.current_sync_operation = None

            # tell everyone to get ready
            self.condition.notifyAll()
        finally:
            # everyone go !!
            self.condition.release()
