#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:27
# @Author  : Cojun  Mao
# @Site    : 
# @File    : databases.py
# @Project : mysite_diy
# @Software: PyCharm
import logging
import re
import threading
from collections import namedtuple


# By default, peewee supports Sqlite, MySQL and Postgresql.
from brick.core.db.felds import TuplesQueryResultWrapper, transaction_sqlite, savepoint_sqlite, fn, Clause, SQL, \
    EnclosedClause, R, NaiveQueryResultWrapper, DictQueryResultWrapper, NamedTupleQueryResultWrapper, \
    AggregateQueryResultWrapper, ModelQueryResultWrapper, transaction

try:
    from pysqlite2 import dbapi2 as pysq3
except ImportError:
    pysq3 = None
try:
    import sqlite3
except ImportError:
    sqlite3 = pysq3
else:
    if pysq3 and pysq3.sqlite_version_info >= sqlite3.sqlite_version_info:
        sqlite3 = pysq3

try:
    from psycopg2cffi import compat

    compat.register()
except ImportError:
    pass
try:
    import psycopg2
    from psycopg2 import extensions as pg_extensions
except ImportError:
    psycopg2 = None
try:
    import MySQLdb as mysql  # prefer the C module.
except ImportError:
    try:
        import pymysql as mysql
    except ImportError:
        mysql = None


from brick.core.db.constants import DATETIME_LOOKUPS, SQLITE_DATETIME_FORMATS, RESULTS_NAIVE, RESULTS_MODELS, \
    RESULTS_TUPLES, RESULTS_DICTS, RESULTS_NAMEDTUPLES, RESULTS_AGGREGATE_MODELS, SQLITE_DATE_TRUNC_MAPPING, basestring, \
    MYSQL_DATE_TRUNC_MAPPING
from brick.core.db.exceptions import IntegrityError, DatabaseError, DataError, InterfaceError, InternalError, \
    NotSupportedError, OperationalError, ProgrammingError, ExceptionWrapper, ImproperlyConfigured

from brick.core.db.querycompiler import QueryCompiler, SqliteQueryCompiler
from brick.core.db.utils import merge_dict, format_date_time, OP, binary_construct

# NullHandler是出于某种原因方便使用日志处理程序的情况，但实际上并不想执行任何日志记录。
from logging import NullHandler
logger = logging.getLogger('peewee')
logger.addHandler(NullHandler())
def _sqlite_date_part(lookup_type, datetime_string):
    assert lookup_type in DATETIME_LOOKUPS
    if not datetime_string:
        return
    dt = format_date_time(datetime_string, SQLITE_DATETIME_FORMATS)
    return getattr(dt, lookup_type)

def _sqlite_date_trunc(lookup_type, datetime_string):
    assert lookup_type in SQLITE_DATE_TRUNC_MAPPING
    if not datetime_string:
        return
    dt = format_date_time(datetime_string, SQLITE_DATETIME_FORMATS)
    return dt.strftime(SQLITE_DATE_TRUNC_MAPPING[lookup_type])


def _sqlite_regexp(regex, value, case_sensitive=False):
    flags = 0 if case_sensitive else re.I
    return re.search(regex, value, flags) is not None

#
# OP_LIKE = 28
# OP_ILIKE = 29
#
# RESULTS_NAIVE = 1
# RESULTS_MODELS = 2
# RESULTS_TUPLES = 3
# RESULTS_DICTS = 4
# RESULTS_AGGREGATE_MODELS = 5
# RESULTS_NAMEDTUPLES = 6

#
# class Proxy(object):
#     """
#     Create a proxy or placeholder for another object.
#     为另一个对象创建代理或占位符。
#     """
#     __slots__ = ('obj', '_callbacks')
#
#     def __init__(self):
#         self._callbacks = []
#         self.initialize(None)
#
#     def initialize(self, obj):
#         self.obj = obj
#         for callback in self._callbacks:
#             callback(obj)
#
#     def attach_callback(self, callback):
#         self._callbacks.append(callback)
#         return callback
#
#     def passthrough(method):
#         def inner(self, *args, **kwargs):
#             if self.obj is None:
#                 raise AttributeError('Cannot use uninitialized Proxy.')
#             return getattr(self.obj, method)(*args, **kwargs)
#         return inner
#
#     # Allow proxy to be used as a context-manager.
#     __enter__ = passthrough('__enter__')
#     __exit__ = passthrough('__exit__')
#
#     def __getattr__(self, attr):
#         if self.obj is None:
#             raise AttributeError('Cannot use uninitialized Proxy.')
#         return getattr(self.obj, attr)
#
#     def __setattr__(self, attr, value):
#         if attr not in self.__slots__:
#             raise AttributeError('Cannot set attribute on proxy.')
#         return super(Proxy, self).__setattr__(attr, value)
#
# class DatabaseProxy(Proxy):
#     """
#     Proxy implementation specifically for proxying `Database` objects.
#     """
#     def connection_context(self):
#         return ConnectionContext(self)
#     def atomic(self, *args, **kwargs):
#         return _atomic(self, *args, **kwargs)
#     def manual_commit(self):
#         return _manual(self)
#     def transaction(self, *args, **kwargs):
#         return _transaction(self, *args, **kwargs)
#     def savepoint(self):
#         return _savepoint(self)
#
# class Database(object):
#     commit_select = False
#     compiler_class = QueryCompiler
#     empty_limit = False
#     field_overrides = {}
#     for_update = False
#     interpolation = '?'
#     op_overrides = {}
#     quote_char = '"'
#     reserved_tables = []
#     sequences = False
#     subquery_delete_same_table = True
#
#     def __init__(self, database, threadlocals=False, autocommit=True,
#                  fields=None, use_speedups=True, ops=None, **connect_kwargs):
#         # self.init(database, **connect_kwargs)
#         self.database = database
#         self.connect_kwargs = connect_kwargs
#         self.use_speedups = use_speedups
#         if threadlocals:
#             self.__local = threading.local()
#         else:
#             self.__local = type('DummyLocal', (object,), {})
#
#         self._conn_lock = threading.Lock()
#         self.autocommit = autocommit
#
#         self.field_overrides = dict_update(self.field_overrides, fields or {})
#         self.op_overrides = dict_update(self.op_overrides, ops or {})
#
#     def init(self, database, **connect_kwargs):
#         self.deferred = database is None
#         self.database = database
#         self.connect_kwargs = connect_kwargs
#
#     def connect(self):
#         with self._conn_lock:
#             if self.database is None:
#                 raise Exception('Error, database not properly initialized before opening connection')
#             self.__local.conn = self._connect(self.database, **self.connect_kwargs)
#             self.__local.closed = False
#
#     def _connect(self, database, **kwargs):
#         raise NotImplementedError
#
#     def get_conn(self):
#         if not hasattr(self.__local, 'closed') or self.__local.closed:
#             self.connect()
#         return self.__local.conn
#
#     def _close(self, conn):
#         conn.close()
#
#     def create_table(self, model_class):
#         qc = self.get_compiler()
#         return self.execute_sql(qc.create_table(model_class))
#
#     def get_compiler(self):
#         return self.compiler_class(
#             self.quote_char, self.interpolation, self.field_overrides,
#             self.op_overrides)
#
#     def execute_sql(self, sql, params=None, require_commit=True):
#         cursor = self.get_cursor()
#         res = cursor.execute(sql, params or ())
#         if require_commit and self.get_autocommit():
#             self.commit()
#         # logger.debug((sql, params))
#         return cursor
#
#     def get_cursor(self):
#         return self.get_conn().cursor()
#
#     def commit(self):
#         self.get_conn().commit()
#
#     def rollback(self):
#         self.get_conn().rollback()
#
#     def set_autocommit(self, autocommit):
#         self.__local.autocommit = autocommit
#
#     def get_autocommit(self):
#         if not hasattr(self.__local, 'autocommit'):
#             self.set_autocommit(self.autocommit)
#         return self.__local.autocommit
#
#     def last_insert_id(self, cursor, model):
#         if model._meta.auto_increment:
#             return cursor.lastrowid
#
#     def rows_affected(self, cursor):
#         return cursor.rowcount
#
# class ImproperlyConfigured(Exception):
#     pass
#
# class SqliteDatabase(Database):
#     op_overrides = {
#         OP_LIKE: 'GLOB',
#         OP_ILIKE: 'LIKE',
#     }
#
#     def _connect(self, database, **kwargs):
#         if not sqlite3:
#             raise ImproperlyConfigured('sqlite3 must be installed on the system')
#         return sqlite3.connect(database, **kwargs)
#
# class PostgresqlDatabase(Database):
#     commit_select = True
#     empty_limit = True
#     field_overrides = {
#         'bigint': 'BIGINT',
#         'bool': 'BOOLEAN',
#         'datetime': 'TIMESTAMP',
#         'decimal': 'NUMERIC',
#         'double': 'DOUBLE PRECISION',
#         'primary_key': 'SERIAL',
#     }
#     for_update = True
#     interpolation = '%s'
#     reserved_tables = ['user']
#     sequences = True
#
#     def _connect(self, database, **kwargs):
#         if not psycopg2:
#             raise ImproperlyConfigured('psycopg2 must be installed on the system')
#         return psycopg2.connect(database=database, **kwargs)
#
#     def last_insert_id(self, cursor, model):
#         seq = model._meta.primary_key.sequence
#         if seq:
#             cursor.execute("SELECT CURRVAL('\"%s\"')" % (seq))
#             return cursor.fetchone()[0]
#         elif model._meta.auto_increment:
#             cursor.execute("SELECT CURRVAL('\"%s_%s_seq\"')" % (
#                 model._meta.db_table, model._meta.primary_key.db_column))
#             return cursor.fetchone()[0]
#
#     def get_indexes_for_table(self, table):
#         res = self.execute_sql("""
#             SELECT c2.relname, i.indisprimary, i.indisunique
#             FROM pg_catalog.pg_class c, pg_catalog.pg_class c2, pg_catalog.pg_index i
#             WHERE c.relname = %s AND c.oid = i.indrelid AND i.indexrelid = c2.oid
#             ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname""", (table,))
#         return sorted([(r[0], r[1]) for r in res.fetchall()])
#
#     def get_tables(self):
#         res = self.execute_sql("""
#             SELECT c.relname
#             FROM pg_catalog.pg_class c
#             LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
#             WHERE c.relkind IN ('r', 'v', '')
#                 AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
#                 AND pg_catalog.pg_table_is_visible(c.oid)
#             ORDER BY c.relname""")
#         return [row[0] for row in res.fetchall()]
#
#     def sequence_exists(self, sequence):
#         res = self.execute_sql("""
#             SELECT COUNT(*)
#             FROM pg_class, pg_namespace
#             WHERE relkind='S'
#                 AND pg_class.relnamespace = pg_namespace.oid
#                 AND relname=%s""", (sequence,))
#         return bool(res.fetchone()[0])
#
#     def set_search_path(self, *search_path):
#         path_params = ','.join(['%s'] * len(search_path))
#         self.execute_sql('SET search_path TO %s' % path_params, search_path)
#
# class MySQLDatabase(Database):
#     commit_select = True
#     field_overrides = {
#         'bigint': 'BIGINT',
#         'boolean': 'BOOL',
#         'decimal': 'NUMERIC',
#         'double': 'DOUBLE PRECISION',
#         'float': 'FLOAT',
#         'primary_key': 'INTEGER AUTO_INCREMENT',
#         'text': 'LONGTEXT',
#     }
#     for_update = True
#     interpolation = '%s'
#     op_overrides = {OP_LIKE: 'LIKE BINARY', OP_ILIKE: 'LIKE'}
#     quote_char = '`'
#     subquery_delete_same_table = False
#
#     def _connect(self, database, **kwargs):
#         if not mysql:
#             raise ImproperlyConfigured('MySQLdb must be installed on the system')
#         conn_kwargs = {
#             'charset': 'utf8',
#             'use_unicode': True,
#         }
#         conn_kwargs.update(kwargs)
#         return mysql.connect(db=database, **conn_kwargs)
#
#     def create_foreign_key(self, model_class, field):
#         compiler = self.get_compiler()
#         framing = """
#             ALTER TABLE %(table)s ADD CONSTRAINT %(constraint)s
#             FOREIGN KEY (%(field)s) REFERENCES %(to)s(%(to_field)s)%(cascade)s;
#         """
#         db_table = model_class._meta.db_table
#         constraint = 'fk_%s_%s_%s' % (
#             db_table,
#             field.rel_model._meta.db_table,
#             field.db_column,
#         )
#
#         query = framing % {
#             'table': compiler.quote(db_table),
#             'constraint': compiler.quote(constraint),
#             'field': compiler.quote(field.db_column),
#             'to': compiler.quote(field.rel_model._meta.db_table),
#             'to_field': compiler.quote(field.rel_model._meta.primary_key.db_column),
#             'cascade': ' ON DELETE CASCADE' if field.cascade else '',
#         }
#
#         self.execute_sql(query)
#         return super(MySQLDatabase, self).create_foreign_key(model_class, field)
#
#     def get_indexes_for_table(self, table):
#         res = self.execute_sql('SHOW INDEXES IN `%s`;' % table)
#         rows = sorted([(r[2], r[1] == 0) for r in res.fetchall()])
#         return rows
#
#     def get_tables(self):
#         res = self.execute_sql('SHOW TABLES;')
#         return [r[0] for r in res.fetchall()]


class _BaseConnectionLocal(object):
    def __init__(self, **kwargs):
        super(_BaseConnectionLocal, self).__init__(**kwargs)
        self.autocommit = None
        self.closed = True
        self.conn = None
        self.context_stack = []
        self.transactions = []


class _ConnectionLocal(_BaseConnectionLocal, threading.local):
    pass


def sort_models_topologically(models):
        """Sort model topologically so that parents will precede children."""
        models = set(models)
        seen = set()
        ordering = []

        def dfs(model):
            # Omit model which are already sorted
            # or should not be in the list at all
            if model in models and model not in seen:
                seen.add(model)

                # First create model on which current model depends
                # (either through foreign keys or through depends_on),
                # then create current model itself
                for foreign_key in model._meta.rel.values():
                    dfs(foreign_key.rel_model)
                if model._meta.depends_on:
                    for dependency in model._meta.depends_on:
                        dfs(dependency)
                ordering.append(model)

        # Order model by name and table initially to guarantee total ordering.
        names = lambda m: (m._meta.name, m._meta.db_table)
        for m in sorted(models, key=names):
            dfs(m)
        return ordering


def create_model_tables(models, **create_table_kwargs):
    """Create tables for all given model (in the right order)."""
    for m in sort_models_topologically(models):
        m.create_table(**create_table_kwargs)


def drop_model_tables(models, **drop_table_kwargs):
    """Drop tables for all given model (in the right order)."""
    for m in reversed(sort_models_topologically(models)):
        m.drop_table(**drop_table_kwargs)

class Database(object):
    commit_select = False
    compiler_class = QueryCompiler
    compound_operations = ['UNION', 'INTERSECT', 'EXCEPT', 'UNION ALL']
    compound_select_parentheses = False
    distinct_on = False
    drop_cascade = False
    field_overrides = {}
    foreign_keys = True
    for_update = False
    for_update_nowait = False
    insert_many = True
    insert_returning = False
    interpolation = '?'
    limit_max = None
    op_overrides = {}
    quote_char = '"'
    reserved_tables = []
    returning_clause = False
    savepoints = True
    sequences = False
    subquery_delete_same_table = True
    upsert_sql = None
    window_functions = False

    exceptions = {
        'ConstraintError': IntegrityError,
        'DatabaseError': DatabaseError,
        'DataError': DataError,
        'IntegrityError': IntegrityError,
        'InterfaceError': InterfaceError,
        'InternalError': InternalError,
        'NotSupportedError': NotSupportedError,
        'OperationalError': OperationalError,
        'ProgrammingError': ProgrammingError}

    def __init__(self, database, threadlocals=True, autocommit=True,
                 fields=None, ops=None, autorollback=False, use_speedups=True,
                 **connect_kwargs):
        self.connect_kwargs = {}
        if threadlocals:
            self._local = _ConnectionLocal()
        else:
            self._local = _BaseConnectionLocal()
        self.init(database, **connect_kwargs)

        self._conn_lock = threading.Lock()
        self.autocommit = autocommit
        self.autorollback = autorollback
        self.use_speedups = use_speedups

        self.field_overrides = merge_dict(self.field_overrides, fields or {})
        self.op_overrides = merge_dict(self.op_overrides, ops or {})
        self.exception_wrapper = ExceptionWrapper(self.exceptions)

    def init(self, database, **connect_kwargs):
        if not self.is_closed():
            self.close()
        self.deferred = database is None
        self.database = database
        self.connect_kwargs.update(connect_kwargs)

    def connect(self):
        with self._conn_lock:
            if self.deferred:
                raise OperationalError('Database has not been initialized')
            if not self._local.closed:
                raise OperationalError('Connection already open')
            self._local.conn = self._create_connection()
            self._local.closed = False
            with self.exception_wrapper:
                self.initialize_connection(self._local.conn)

    def initialize_connection(self, conn):
        pass

    def close(self):
        with self._conn_lock:
            if self.deferred:
                raise Exception('Error, database not properly initialized '
                                'before closing connection')
            try:
                with self.exception_wrapper:
                    self._close(self._local.conn)
            finally:
                self._local.closed = True

    def get_conn(self):
        if self._local.context_stack:
            conn = self._local.context_stack[-1].connection
            if conn is not None:
                return conn
        if self._local.closed:
            self.connect()
        return self._local.conn

    def _create_connection(self):
        with self.exception_wrapper:
            return self._connect(self.database, **self.connect_kwargs)

    def is_closed(self):
        return self._local.closed

    def get_cursor(self):
        return self.get_conn().cursor()

    def _close(self, conn):
        conn.close()

    def _connect(self, database, **kwargs):
        raise NotImplementedError

    @classmethod
    def register_fields(cls, fields):
        cls.field_overrides = merge_dict(cls.field_overrides, fields)

    @classmethod
    def register_ops(cls, ops):
        cls.op_overrides = merge_dict(cls.op_overrides, ops)

    def get_result_wrapper(self, wrapper_type):
        if wrapper_type == RESULTS_NAIVE:
            # return (_ModelQueryResultWrapper if self.use_speedups
            #         else NaiveQueryResultWrapper)
            return (NaiveQueryResultWrapper)
        elif wrapper_type == RESULTS_MODELS:
            return ModelQueryResultWrapper
        elif wrapper_type == RESULTS_TUPLES:
            # return (_TuplesQueryResultWrapper if self.use_speedups
        #         #             #         else TuplesQueryResultWrapper)
            return (TuplesQueryResultWrapper)
        elif wrapper_type == RESULTS_DICTS:
            # return (_DictQueryResultWrapper if self.use_speedups
            #         else DictQueryResultWrapper)
            return (DictQueryResultWrapper)
        elif wrapper_type == RESULTS_NAMEDTUPLES:
            return NamedTupleQueryResultWrapper
        elif wrapper_type == RESULTS_AGGREGATE_MODELS:
            return AggregateQueryResultWrapper
        else:
            return ( NaiveQueryResultWrapper)

    def last_insert_id(self, cursor, model):
        if model._meta.auto_increment:
            return cursor.lastrowid

    def rows_affected(self, cursor):
        return cursor.rowcount

    def compiler(self):
        return self.compiler_class(
            self.quote_char, self.interpolation, self.field_overrides,
            self.op_overrides)

    def execute(self, clause):
        return self.execute_sql(*self.compiler().parse_node(clause))

    def execute_sql(self, sql, params=None, require_commit=True):
        logger.debug((sql, params))
        with self.exception_wrapper:
            cursor = self.get_cursor()
            try:
                cursor.execute(sql, params or ())
            except Exception:
                if self.autorollback and self.get_autocommit():
                    self.rollback()
                raise
            else:
                if require_commit and self.get_autocommit():
                    self.commit()
        return cursor

    def begin(self):
        pass

    def commit(self):
        with self.exception_wrapper:
            self.get_conn().commit()

    def rollback(self):
        with self.exception_wrapper:
            self.get_conn().rollback()

    def set_autocommit(self, autocommit):
        self._local.autocommit = autocommit

    def get_autocommit(self):
        if self._local.autocommit is None:
            self.set_autocommit(self.autocommit)
        return self._local.autocommit

    def push_execution_context(self, transaction):
        self._local.context_stack.append(transaction)

    def pop_execution_context(self):
        self._local.context_stack.pop()

    def execution_context_depth(self):
        return len(self._local.context_stack)

    def execution_context(self, with_transaction=True, transaction_type=None):
        return ExecutionContext(self, with_transaction, transaction_type)

    __call__ = execution_context

    def push_transaction(self, transaction):
        self._local.transactions.append(transaction)

    def pop_transaction(self):
        self._local.transactions.pop()

    def transaction_depth(self):
        return len(self._local.transactions)

    def transaction(self, transaction_type=None):
        return transaction(self, transaction_type)

    commit_on_success = property(transaction)

    def savepoint(self, sid=None):
        if not self.savepoints:
            raise NotImplementedError
        return savepoint(self, sid)

    def atomic(self, transaction_type=None):
        return _atomic(self, transaction_type)

    def get_tables(self, schema=None):
        raise NotImplementedError

    def get_indexes(self, table, schema=None):
        raise NotImplementedError

    def get_columns(self, table, schema=None):
        raise NotImplementedError

    def get_primary_keys(self, table, schema=None):
        raise NotImplementedError

    def get_foreign_keys(self, table, schema=None):
        raise NotImplementedError

    def sequence_exists(self, seq):
        raise NotImplementedError

    def create_table(self, model_class, safe=False):
        qc = self.compiler()
        return self.execute_sql(*qc.create_table(model_class, safe))

    def create_tables(self, models, safe=False):
        create_model_tables(models, fail_silently=safe)

    def create_index(self, model_class, fields, unique=False):
        qc = self.compiler()
        if not isinstance(fields, (list, tuple)):
            raise ValueError('Fields passed to "create_index" must be a list '
                             'or tuple: "%s"' % fields)
        fobjs = [
            model_class._meta.fields[f] if isinstance(f, basestring) else f
            for f in fields]
        return self.execute_sql(*qc.create_index(model_class, fobjs, unique))

    def drop_index(self, model_class, fields, safe=False):
        qc = self.compiler()
        if not isinstance(fields, (list, tuple)):
            raise ValueError('Fields passed to "drop_index" must be a list '
                             'or tuple: "%s"' % fields)
        fobjs = [
            model_class._meta.fields[f] if isinstance(f, basestring) else f
            for f in fields]
        return self.execute_sql(*qc.drop_index(model_class, fobjs, safe))

    def create_foreign_key(self, model_class, field, constraint=None):
        qc = self.compiler()
        return self.execute_sql(*qc.create_foreign_key(
            model_class, field, constraint))

    def create_sequence(self, seq):
        if self.sequences:
            qc = self.compiler()
            return self.execute_sql(*qc.create_sequence(seq))

    def drop_table(self, model_class, fail_silently=False, cascade=False):
        qc = self.compiler()
        if cascade and not self.drop_cascade:
            raise ValueError('Database does not support DROP TABLE..CASCADE.')
        return self.execute_sql(*qc.drop_table(
            model_class, fail_silently, cascade))

    def drop_tables(self, models, safe=False, cascade=False):
        drop_model_tables(models, fail_silently=safe, cascade=cascade)

    def truncate_table(self, model_class, restart_identity=False,
                       cascade=False):
        qc = self.compiler()
        return self.execute_sql(*qc.truncate_table(
            model_class, restart_identity, cascade))

    def truncate_tables(self, models, restart_identity=False, cascade=False):
        for model in reversed(sort_models_topologically(models)):
            model.truncate_table(restart_identity, cascade)

    def drop_sequence(self, seq):
        if self.sequences:
            qc = self.compiler()
            return self.execute_sql(*qc.drop_sequence(seq))

    def extract_date(self, date_part, date_field):
        return fn.EXTRACT(Clause(date_part, R('FROM'), date_field))

    def truncate_date(self, date_part, date_field):
        return fn.DATE_TRUNC(date_part, date_field)

    def default_insert_clause(self, model_class):
        return SQL('DEFAULT VALUES')

    def get_noop_sql(self):
        return 'SELECT 0 WHERE 0'

    def get_binary_type(self):
        return binary_construct

SENTINEL = object()
def __pragma__(name):
    def __get__(self):
        return self.pragma(name)

    def __set__(self, value):
        return self.pragma(name, value)

    return property(__get__, __set__)
ColumnMetadata = namedtuple(
    'ColumnMetadata',
    ('name', 'data_type', 'null', 'primary_key', 'table'))
ForeignKeyMetadata = namedtuple(
    'ForeignKeyMetadata',
    ('column', 'dest_table', 'dest_column', 'table'))
IndexMetadata = namedtuple(
    'IndexMetadata',
    ('name', 'sql', 'columns', 'unique', 'table'))

class SqliteDatabase(Database):
    compiler_class = SqliteQueryCompiler
    field_overrides = {
        'bool': 'INTEGER',
        'smallint': 'INTEGER',
        'uuid': 'TEXT',
    }
    foreign_keys = False
    insert_many = sqlite3 and sqlite3.sqlite_version_info >= (3, 7, 11, 0)
    limit_max = -1
    op_overrides = {
        OP.LIKE: 'GLOB',
        OP.ILIKE: 'LIKE',
    }
    upsert_sql = 'INSERT OR REPLACE INTO'

    def __init__(self, database, pragmas=None, *args, **kwargs):
        self._pragmas = pragmas or []
        journal_mode = kwargs.pop('journal_mode', None)  # Backwards-compat.
        if journal_mode:
            self._pragmas.append(('journal_mode', journal_mode))

        super(SqliteDatabase, self).__init__(database, *args, **kwargs)

    def _connect(self, database, **kwargs):
        if not sqlite3:
            raise ImproperlyConfigured('pysqlite or sqlite3 must be installed.')
        conn = sqlite3.connect(database, **kwargs)
        conn.isolation_level = None
        try:
            self._add_conn_hooks(conn)
        except:
            conn.close()
            raise
        return conn

    def _add_conn_hooks(self, conn):
        self._set_pragmas(conn)
        conn.create_function('date_part', 2, _sqlite_date_part)
        conn.create_function('date_trunc', 2, _sqlite_date_trunc)
        conn.create_function('regexp', -1, _sqlite_regexp)

    def _set_pragmas(self, conn):
        if self._pragmas:
            cursor = conn.cursor()
            for pragma, value in self._pragmas:
                cursor.execute('PRAGMA %s = %s;' % (pragma, value))
            cursor.close()

    def pragma(self, key, value=SENTINEL):
        sql = 'PRAGMA %s' % key
        if value is not SENTINEL:
            sql += ' = %s' % value
        return self.execute_sql(sql).fetchone()

    cache_size = __pragma__('cache_size')
    foreign_keys = __pragma__('foreign_keys')
    journal_mode = __pragma__('journal_mode')
    journal_size_limit = __pragma__('journal_size_limit')
    mmap_size = __pragma__('mmap_size')
    page_size = __pragma__('page_size')
    read_uncommitted = __pragma__('read_uncommitted')
    synchronous = __pragma__('synchronous')
    wal_autocheckpoint = __pragma__('wal_autocheckpoint')

    def begin(self, lock_type=None):
        statement = 'BEGIN %s' % lock_type if lock_type else 'BEGIN'
        self.execute_sql(statement, require_commit=False)

    def transaction(self, transaction_type=None):
        return transaction_sqlite(self, transaction_type)

    def create_foreign_key(self, model_class, field, constraint=None):
        raise OperationalError('SQLite does not support ALTER TABLE '
                               'statements to add constraints.')

    def get_tables(self, schema=None):
        cursor = self.execute_sql('SELECT name FROM sqlite_master WHERE '
                                  'type = ? ORDER BY name;', ('table',))
        return [row[0] for row in cursor.fetchall()]

    def get_indexes(self, table, schema=None):
        query = ('SELECT name, sql FROM sqlite_master '
                 'WHERE tbl_name = ? AND type = ? ORDER BY name')
        cursor = self.execute_sql(query, (table, 'index'))
        index_to_sql = dict(cursor.fetchall())

        # Determine which indexes have a unique constraint.
        unique_indexes = set()
        cursor = self.execute_sql('PRAGMA index_list("%s")' % table)
        for row in cursor.fetchall():
            name = row[1]
            is_unique = int(row[2]) == 1
            if is_unique:
                unique_indexes.add(name)

        # Retrieve the indexed columns.
        index_columns = {}
        for index_name in sorted(index_to_sql):
            cursor = self.execute_sql('PRAGMA index_info("%s")' % index_name)
            index_columns[index_name] = [row[2] for row in cursor.fetchall()]

        return [
            IndexMetadata(
                name,
                index_to_sql[name],
                index_columns[name],
                name in unique_indexes,
                table)
            for name in sorted(index_to_sql)]

    def get_columns(self, table, schema=None):
        cursor = self.execute_sql('PRAGMA table_info("%s")' % table)
        return [ColumnMetadata(row[1], row[2], not row[3], bool(row[5]), table)
                for row in cursor.fetchall()]

    def get_primary_keys(self, table, schema=None):
        cursor = self.execute_sql('PRAGMA table_info("%s")' % table)
        return [row[1] for row in cursor.fetchall() if row[-1]]

    def get_foreign_keys(self, table, schema=None):
        cursor = self.execute_sql('PRAGMA foreign_key_list("%s")' % table)
        return [ForeignKeyMetadata(row[3], row[2], row[4], table)
                for row in cursor.fetchall()]

    def savepoint(self, sid=None):
        return savepoint_sqlite(self, sid)

    def extract_date(self, date_part, date_field):
        return fn.date_part(date_part, date_field)

    def truncate_date(self, date_part, date_field):
        return fn.strftime(SQLITE_DATE_TRUNC_MAPPING[date_part], date_field)

    def get_binary_type(self):
        return sqlite3.Binary


class PostgresqlDatabase(Database):
    commit_select = True
    compound_select_parentheses = True
    distinct_on = True
    drop_cascade = True
    field_overrides = {
        'blob': 'BYTEA',
        'bool': 'BOOLEAN',
        'datetime': 'TIMESTAMP',
        'decimal': 'NUMERIC',
        'double': 'DOUBLE PRECISION',
        'primary_key': 'SERIAL',
        'uuid': 'UUID',
    }
    for_update = True
    for_update_nowait = True
    insert_returning = True
    interpolation = '%s'
    op_overrides = {
        OP.REGEXP: '~',
    }
    reserved_tables = ['user']
    returning_clause = True
    sequences = True
    window_functions = True

    register_unicode = True

    def _connect(self, database, encoding=None, **kwargs):
        if not psycopg2:
            raise ImproperlyConfigured('psycopg2 must be installed.')
        conn = psycopg2.connect(database=database, **kwargs)
        if self.register_unicode:
            pg_extensions.register_type(pg_extensions.UNICODE, conn)
            pg_extensions.register_type(pg_extensions.UNICODEARRAY, conn)
        if encoding:
            conn.set_client_encoding(encoding)
        return conn

    def _get_pk_sequence(self, model):
        meta = model._meta
        if meta.primary_key is not False and meta.primary_key.sequence:
            return meta.primary_key.sequence
        elif meta.auto_increment:
            return '%s_%s_seq' % (meta.db_table, meta.primary_key.db_column)

    def last_insert_id(self, cursor, model):
        sequence = self._get_pk_sequence(model)
        if not sequence:
            return

        meta = model._meta
        if meta.schema:
            schema = '%s.' % meta.schema
        else:
            schema = ''

        cursor.execute("SELECT CURRVAL('%s\"%s\"')" % (schema, sequence))
        result = cursor.fetchone()[0]
        if self.get_autocommit():
            self.commit()
        return result

    def get_tables(self, schema='public'):
        query = ('SELECT tablename FROM pg_catalog.pg_tables '
                 'WHERE schemaname = %s ORDER BY tablename')
        return [r for r, in self.execute_sql(query, (schema,)).fetchall()]

    def get_indexes(self, table, schema='public'):
        query = """
            SELECT
                i.relname, idxs.indexdef, idx.indisunique,
                array_to_string(array_agg(cols.attname), ',')
            FROM pg_catalog.pg_class AS t
            INNER JOIN pg_catalog.pg_index AS idx ON t.oid = idx.indrelid
            INNER JOIN pg_catalog.pg_class AS i ON idx.indexrelid = i.oid
            INNER JOIN pg_catalog.pg_indexes AS idxs ON
                (idxs.tablename = t.relname AND idxs.indexname = i.relname)
            LEFT OUTER JOIN pg_catalog.pg_attribute AS cols ON
                (cols.attrelid = t.oid AND cols.attnum = ANY(idx.indkey))
            WHERE t.relname = %s AND t.relkind = %s AND idxs.schemaname = %s
            GROUP BY i.relname, idxs.indexdef, idx.indisunique
            ORDER BY idx.indisunique DESC, i.relname;"""
        cursor = self.execute_sql(query, (table, 'r', schema))
        return [IndexMetadata(row[0], row[1], row[3].split(','), row[2], table)
                for row in cursor.fetchall()]

    def get_columns(self, table, schema='public'):
        query = """
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position"""
        cursor = self.execute_sql(query, (table, schema))
        pks = set(self.get_primary_keys(table, schema))
        return [ColumnMetadata(name, dt, null == 'YES', name in pks, table)
                for name, null, dt in cursor.fetchall()]

    def get_primary_keys(self, table, schema='public'):
        query = """
            SELECT kc.column_name
            FROM information_schema.table_constraints AS tc
            INNER JOIN information_schema.key_column_usage AS kc ON (
                tc.table_name = kc.table_name AND
                tc.table_schema = kc.table_schema AND
                tc.constraint_name = kc.constraint_name)
            WHERE
                tc.constraint_type = %s AND
                tc.table_name = %s AND
                tc.table_schema = %s"""
        cursor = self.execute_sql(query, ('PRIMARY KEY', table, schema))
        return [row for row, in cursor.fetchall()]

    def get_foreign_keys(self, table, schema='public'):
        sql = """
            SELECT
                kcu.column_name, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON (tc.constraint_name = kcu.constraint_name AND
                    tc.constraint_schema = kcu.constraint_schema)
            JOIN information_schema.constraint_column_usage AS ccu
                ON (ccu.constraint_name = tc.constraint_name AND
                    ccu.constraint_schema = tc.constraint_schema)
            WHERE
                tc.constraint_type = 'FOREIGN KEY' AND
                tc.table_name = %s AND
                tc.table_schema = %s"""
        cursor = self.execute_sql(sql, (table, schema))
        return [ForeignKeyMetadata(row[0], row[1], row[2], table)
                for row in cursor.fetchall()]

    def sequence_exists(self, sequence):
        res = self.execute_sql("""
            SELECT COUNT(*) FROM pg_class, pg_namespace
            WHERE relkind='S'
                AND pg_class.relnamespace = pg_namespace.oid
                AND relname=%s""", (sequence,))
        return bool(res.fetchone()[0])

    def set_search_path(self, *search_path):
        path_params = ','.join(['%s'] * len(search_path))
        self.execute_sql('SET search_path TO %s' % path_params, search_path)

    def get_noop_sql(self):
        return 'SELECT 0 WHERE false'

    def get_binary_type(self):
        return psycopg2.Binary


class MySQLDatabase(Database):
    commit_select = True
    compound_select_parentheses = True
    compound_operations = ['UNION', 'UNION ALL']
    field_overrides = {
        'bool': 'BOOL',
        'decimal': 'NUMERIC',
        'double': 'DOUBLE PRECISION',
        'float': 'FLOAT',
        'primary_key': 'INTEGER AUTO_INCREMENT',
        'text': 'LONGTEXT',
        'uuid': 'VARCHAR(40)',
    }
    for_update = True
    interpolation = '%s'
    limit_max = 2 ** 64 - 1  # MySQL quirk
    op_overrides = {
        OP.LIKE: 'LIKE BINARY',
        OP.ILIKE: 'LIKE',
        OP.XOR: 'XOR',
    }
    quote_char = '`'
    subquery_delete_same_table = False
    upsert_sql = 'REPLACE INTO'

    def _connect(self, database, **kwargs):
        if not mysql:
            raise ImproperlyConfigured('MySQLdb or PyMySQL must be installed.')
        conn_kwargs = {
            'charset': 'utf8',
            'use_unicode': True,
        }
        conn_kwargs.update(kwargs)
        if 'password' in conn_kwargs:
            conn_kwargs['passwd'] = conn_kwargs.pop('password')
        return mysql.connect(db=database, **conn_kwargs)

    def get_tables(self, schema=None):
        return [row for row, in self.execute_sql('SHOW TABLES')]

    def get_indexes(self, table, schema=None):
        cursor = self.execute_sql('SHOW INDEX FROM `%s`' % table)
        unique = set()
        indexes = {}
        for row in cursor.fetchall():
            if not row[1]:
                unique.add(row[2])
            indexes.setdefault(row[2], [])
            indexes[row[2]].append(row[4])
        return [IndexMetadata(name, None, indexes[name], name in unique, table)
                for name in indexes]

    def get_columns(self, table, schema=None):
        sql = """
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = DATABASE()"""
        cursor = self.execute_sql(sql, (table,))
        pks = set(self.get_primary_keys(table))
        return [ColumnMetadata(name, dt, null == 'YES', name in pks, table)
                for name, null, dt in cursor.fetchall()]

    def get_primary_keys(self, table, schema=None):
        cursor = self.execute_sql('SHOW INDEX FROM `%s`' % table)
        return [row[4] for row in cursor.fetchall() if row[2] == 'PRIMARY']

    def get_foreign_keys(self, table, schema=None):
        query = """
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s
                AND table_schema = DATABASE()
                AND referenced_table_name IS NOT NULL
                AND referenced_column_name IS NOT NULL"""
        cursor = self.execute_sql(query, (table,))
        return [
            ForeignKeyMetadata(column, dest_table, dest_column, table)
            for column, dest_table, dest_column in cursor.fetchall()]

    def extract_date(self, date_part, date_field):
        return fn.EXTRACT(Clause(R(date_part), R('FROM'), date_field))

    def truncate_date(self, date_part, date_field):
        return fn.DATE_FORMAT(date_field, MYSQL_DATE_TRUNC_MAPPING[date_part])

    def default_insert_clause(self, model_class):
        return Clause(
            EnclosedClause(model_class._meta.primary_key),
            SQL('VALUES (DEFAULT)'))

    def get_noop_sql(self):
        return 'DO 0'

    def get_binary_type(self):
        return mysql.Binary
