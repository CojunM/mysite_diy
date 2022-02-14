#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/10/22 17:40
# @Author  : Cojun
# @Site    : 
# @File    : pools.py
# @Software: PyCharm
"""
import queue


class PooledDatabase:
    def __init__(self, **kwargs):
        """
import heapq
import logging
import random
import time
from collections import namedtuple

from brick.orm.databases import SqliteDatabase, PostgresqlDatabase, MySQLDatabase

try:
    from psycopg2.extensions import TRANSACTION_STATUS_IDLE
    from psycopg2.extensions import TRANSACTION_STATUS_INERROR
    from psycopg2.extensions import TRANSACTION_STATUS_UNKNOWN
except ImportError:
    TRANSACTION_STATUS_IDLE = \
        TRANSACTION_STATUS_INERROR = \
        TRANSACTION_STATUS_UNKNOWN = None
logger = logging.getLogger('orm.pools')


def make_int(val):
    if val is not None and not isinstance(val, (int, float)):
        return int(val)
    return val


# 超过最大连接数
class MaxConnectionsExceeded(ValueError): pass


PoolConnection = namedtuple('PoolConnection', ('timestamp', 'connection',
                                               'checked_out'))


class PooledDatabase:
    def __init__(self, database, max_connections=20, stale_timeout=None,
                 timeout=None, **kwargs):
        self._max_connections = make_int(max_connections)
        self._stale_timeout = make_int(stale_timeout)
        self._wait_timeout = make_int(timeout)
        if self._wait_timeout == 0:
            # 求最小值，所以初始化为正无穷
            self._wait_timeout = float('inf')

        # Available / idle connections stored in a heap, sorted oldest first.
        # 可用/空闲连接存储在堆中，首先排序。
        self._connections = []

        # Mapping of connection id to PoolConnection. Ordinarily we would want
        # to use something like a WeakKeyDictionary, but Python typically won't
        # allow us to create weak references to connection objects.
        # 连接id到池连接的映射。通常我们想要
        # 使用类似于weakkeydirectionary的东西，但Python通常不会
        # 允许我们创建对连接对象的弱引用。
        self._in_use = {}

        # Use the memory address of the connection as the key in the event the
        # connection object is not hashable. Connections will not get
        # garbage-collected, however, because a reference to them will persist
        # in "_in_use" as long as the conn has not been closed.
        # 使用连接的内存地址作为事件中的键
        # 连接对象不可散列。连接将无法连接
        # 但是，垃圾会被收集，因为对它们的引用将持续存在
        # 在“\u in\u use”中，只要连接尚未关闭。
        self.conn_key = id

        super(PooledDatabase, self).__init__(database, **kwargs)

    def init(self, database, max_connections=None, stale_timeout=None,
             timeout=None, **connect_kwargs):
        super(PooledDatabase, self).init(database, **connect_kwargs)
        if max_connections is not None:
            self._max_connections = make_int(max_connections)
        if stale_timeout is not None:
            self._stale_timeout = make_int(stale_timeout)
        if timeout is not None:
            self._wait_timeout = make_int(timeout)
            if self._wait_timeout == 0:
                self._wait_timeout = float('inf')

    def connect(self, reuse_if_open=False):
        if not self._wait_timeout:
            return super(PooledDatabase, self).connect(reuse_if_open)

        expires = time.time() + self._wait_timeout
        while expires > time.time():
            try:
                ret = super(PooledDatabase, self).connect(reuse_if_open)
            except MaxConnectionsExceeded:
                time.sleep(0.1)
            else:
                return ret
        raise MaxConnectionsExceeded('Max connections exceeded, timed out '
                                     'attempting to connect.')

    def _connect(self):
        while True:
            try:
                # Remove the oldest connection from the heap.
                # 从堆中删除最旧的连接。
                ts, conn = heapq.heappop(self._connections)
                key = self.conn_key(conn)
            except IndexError:
                ts = conn = None
                logger.debug('No connection available in pool.')
                break
            else:
                if self._is_closed(conn):
                    # This connecton was closed, but since it was not stale
                    # it got added back to the queue of available conns. We
                    # then closed it and marked it as explicitly closed, so
                    # it's safe to throw it away now.
                    # (Because Database.close() calls Database._close()).
                    # 此connecton已关闭，但由于未过时
                    # 它被重新添加到可用连接的队列中。我们
                    # 然后关闭它并将其标记为显式关闭，因此
                    # 现在把它扔掉是安全的。
                    # （因为Database.close（）调用Database.\u close（）。
                    logger.debug('Connection %s was closed.', key)
                    ts = conn = None
                elif self._stale_timeout and self._is_stale(ts):
                    # If we are attempting to check out a stale connection,
                    # then close it. We don't need to mark it in the "closed"
                    # set, because it is not in the list of available conns
                    # anymore.
                    # 如果我们试图检查过时的连接，
                    # 然后关上它。我们不需要在“关闭”中标记它
                    # 设置，因为它不在可用连接列表中
                    # 再也没有了。
                    logger.debug('Connection %s was stale, closing.', key)
                    self._close(conn, True)
                    ts = conn = None
                else:
                    break

        if conn is None:
            if self._max_connections and (
                    len(self._in_use) >= self._max_connections):
                raise MaxConnectionsExceeded('Exceeded maximum connections.')
            conn = super(PooledDatabase, self)._connect()
            ts = time.time() - random.random() / 1000
            key = self.conn_key(conn)
            logger.debug('Created new connection %s.', key)

        self._in_use[key] = PoolConnection(ts, conn, time.time())
        return conn

    def _is_stale(self, timestamp):
        # Called on check-out and check-in to ensure the connection has
        # not outlived the stale timeout.
        # 在签出和签入时调用，以确保连接已完成
        # 没有超过过时的超时时间。
        return (time.time() - timestamp) > self._stale_timeout

    def _is_closed(self, conn):
        return False

    def _can_reuse(self, conn):
        # Called on check-in to make sure the connection can be re-used.
        # 在签入时调用以确保连接可以重复使用。
        return True

    def _close(self, conn, close_conn=False):
        key = self.conn_key(conn)
        if close_conn:
            super(PooledDatabase, self)._close(conn)
        elif key in self._in_use:
            pool_conn = self._in_use.pop(key)
            if self._stale_timeout and self._is_stale(pool_conn.timestamp):
                logger.debug('Closing stale connection %s.', key)
                super(PooledDatabase, self)._close(conn)
            elif self._can_reuse(conn):
                logger.debug('Returning %s to pool.', key)
                heapq.heappush(self._connections, (pool_conn.timestamp, conn))
            else:
                logger.debug('Closed %s.', key)

    def manual_close(self):
        """
        Close the underlying connection without returning it to the pool.
        关闭基础连接而不将其返回池。
        """
        if self.is_closed():
            return False

        # Obtain reference to the connection in-use by the calling thread.
        # 获取调用线程正在使用的连接的引用。
        conn = self.connection()

        # A connection will only be re-added to the available list if it is
        # marked as "in use" at the time it is closed. We will explicitly
        # remove it from the "in use" list, call "close()" for the
        # side-effects, and then explicitly close the connection.
        # 只有在连接可用时，才会将其重新添加到可用列表中
        # 关闭时标记为“正在使用”。我们将明确
        # 将其从“正在使用”列表中删除，为
        # 然后显式关闭连接。
        self._in_use.pop(self.conn_key(conn), None)
        self.close()
        self._close(conn, close_conn=True)

    def close_idle(self):
        # Close any open connections that are not currently in-use.
        # 关闭当前未使用的所有打开的连接。
        with self._lock:
            for _, conn in self._connections:
                self._close(conn, close_conn=True)
            self._connections = []

    def close_stale(self, age=600):
        # Close any connections that are in-use but were checked out quite some
        # time ago and can be considered stale.
        # 关闭所有正在使用但已签出的连接
        # 时间早了，可以认为已经过时了。
        with self._lock:
            in_use = {}
            cutoff = time.time() - age
            n = 0
            for key, pool_conn in self._in_use.items():
                if pool_conn.checked_out < cutoff:
                    self._close(pool_conn.connection, close_conn=True)
                    n += 1
                else:
                    in_use[key] = pool_conn
            self._in_use = in_use
        return n

    def close_all(self):
        # Close all connections -- available and in-use. Warning: may break any
        # active connections used by other threads.
        # 关闭所有可用和正在使用的连接。警告：可能会损坏任何
        # 其他线程使用的活动连接。
        self.close()
        with self._lock:
            for _, conn in self._connections:
                self._close(conn, close_conn=True)
            for pool_conn in self._in_use.values():
                self._close(pool_conn.connection, close_conn=True)
            self._connections = []
            self._in_use = {}


class PooledMySQLDatabase(PooledDatabase, MySQLDatabase):
    def _is_closed(self, conn):
        try:
            conn.ping(False)
        except:
            return True
        else:
            return False


class _PooledPostgresqlDatabase(PooledDatabase):
    def _is_closed(self, conn):
        if conn.closed:
            return True

        txn_status = conn.get_transaction_status()
        if txn_status == TRANSACTION_STATUS_UNKNOWN:
            return True
        elif txn_status != TRANSACTION_STATUS_IDLE:
            conn.rollback()
        return False

    def _can_reuse(self, conn):
        txn_status = conn.get_transaction_status()
        # Do not return connection in an error state, as subsequent queries
        # will all fail. If the status is unknown then we lost the connection
        # to the server and the connection should not be re-used.
        # 不要像后续查询那样返回处于错误状态的连接
        # 一切都将失败。如果状态未知，则我们失去了连接
        # 连接到服务器，不应重复使用该连接。
        if txn_status == TRANSACTION_STATUS_UNKNOWN:
            return False
        elif txn_status == TRANSACTION_STATUS_INERROR:
            conn.reset()
        elif txn_status != TRANSACTION_STATUS_IDLE:
            conn.rollback()
        return True


class PooledPostgresqlDatabase(_PooledPostgresqlDatabase, PostgresqlDatabase):
    pass


class _PooledSqliteDatabase(PooledDatabase):
    def _is_closed(self, conn):
        try:
            conn.total_changes
        except:
            return True
        else:
            return False


class PooledSqliteDatabase(_PooledSqliteDatabase, SqliteDatabase):
    pass
