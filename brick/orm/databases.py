#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:27
# @Author  : Cojun  Mao
# @Site    : 
# @File    : databases.py
# @Project : mysite_diy
# @Software: PyCharm
import sqlite3
import threading
import  mysql as mysql
import psycopg2 as psycopg2

from brick.orm.querycompiler import QueryCompiler
from brick.orm.utils import dict_update

OP_LIKE = 28
OP_ILIKE = 29


class Database(object):
    commit_select = False
    compiler_class = QueryCompiler
    empty_limit = False
    field_overrides = {}
    for_update = False
    interpolation = '?'
    op_overrides = {}
    quote_char = '"'
    reserved_tables = []
    sequences = False
    subquery_delete_same_table = True

    def __init__(self, database, threadlocals=False, autocommit=True,
                 fields=None, use_speedups=True, ops=None, **connect_kwargs):
        # self.init(database, **connect_kwargs)
        self.database = database
        self.connect_kwargs = connect_kwargs
        self.use_speedups = use_speedups
        if threadlocals:
            self.__local = threading.local()
        else:
            self.__local = type('DummyLocal', (object,), {})

        self._conn_lock = threading.Lock()
        self.autocommit = autocommit

        self.field_overrides = dict_update(self.field_overrides, fields or {})
        self.op_overrides = dict_update(self.op_overrides, ops or {})

    def init(self, database, **connect_kwargs):
        self.deferred = database is None
        self.database = database
        self.connect_kwargs = connect_kwargs

    def connect(self):
        with self._conn_lock:
            if self.database is None:
                raise Exception('Error, database not properly initialized before opening connection')
            self.__local.conn = self._connect(self.database, **self.connect_kwargs)
            self.__local.closed = False

    def _connect(self, database, **kwargs):
        raise NotImplementedError

    def get_conn(self):
        if not hasattr(self.__local, 'closed') or self.__local.closed:
            self.connect()
        return self.__local.conn

    def _close(self, conn):
        conn.close()

    def create_table(self, model_class):
        qc = self.get_compiler()
        return self.execute_sql(qc.create_table(model_class))

    def get_compiler(self):
        return self.compiler_class(
            self.quote_char, self.interpolation, self.field_overrides,
            self.op_overrides)

    def execute_sql(self, sql, params=None, require_commit=True):
        cursor = self.get_cursor()
        res = cursor.execute(sql, params or ())
        if require_commit and self.get_autocommit():
            self.commit()
        # logger.debug((sql, params))
        return cursor

    def get_cursor(self):
        return self.get_conn().cursor()

    def commit(self):
        self.get_conn().commit()

    def rollback(self):
        self.get_conn().rollback()

    def set_autocommit(self, autocommit):
        self.__local.autocommit = autocommit

    def get_autocommit(self):
        if not hasattr(self.__local, 'autocommit'):
            self.set_autocommit(self.autocommit)
        return self.__local.autocommit

    def last_insert_id(self, cursor, model):
        if model._meta.auto_increment:
            return cursor.lastrowid

    def rows_affected(self, cursor):
        return cursor.rowcount


class ImproperlyConfigured(Exception):
    pass


class SqliteDatabase(Database):
    op_overrides = {
        OP_LIKE: 'GLOB',
        OP_ILIKE: 'LIKE',
    }

    def _connect(self, database, **kwargs):
        if not sqlite3:
            raise ImproperlyConfigured('sqlite3 must be installed on the system')
        return sqlite3.connect(database, **kwargs)


class PostgresqlDatabase(Database):
    commit_select = True
    empty_limit = True
    field_overrides = {
        'bigint': 'BIGINT',
        'bool': 'BOOLEAN',
        'datetime': 'TIMESTAMP',
        'decimal': 'NUMERIC',
        'double': 'DOUBLE PRECISION',
        'primary_key': 'SERIAL',
    }
    for_update = True
    interpolation = '%s'
    reserved_tables = ['user']
    sequences = True

    def _connect(self, database, **kwargs):
        if not psycopg2:
            raise ImproperlyConfigured('psycopg2 must be installed on the system')
        return psycopg2.connect(database=database, **kwargs)

    def last_insert_id(self, cursor, model):
        seq = model._meta.primary_key.sequence
        if seq:
            cursor.execute("SELECT CURRVAL('\"%s\"')" % (seq))
            return cursor.fetchone()[0]
        elif model._meta.auto_increment:
            cursor.execute("SELECT CURRVAL('\"%s_%s_seq\"')" % (
                model._meta.db_table, model._meta.primary_key.db_column))
            return cursor.fetchone()[0]

    def get_indexes_for_table(self, table):
        res = self.execute_sql("""
            SELECT c2.relname, i.indisprimary, i.indisunique
            FROM pg_catalog.pg_class c, pg_catalog.pg_class c2, pg_catalog.pg_index i
            WHERE c.relname = %s AND c.oid = i.indrelid AND i.indexrelid = c2.oid
            ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname""", (table,))
        return sorted([(r[0], r[1]) for r in res.fetchall()])

    def get_tables(self):
        res = self.execute_sql("""
            SELECT c.relname
            FROM pg_catalog.pg_class c
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'v', '')
                AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
                AND pg_catalog.pg_table_is_visible(c.oid)
            ORDER BY c.relname""")
        return [row[0] for row in res.fetchall()]

    def sequence_exists(self, sequence):
        res = self.execute_sql("""
            SELECT COUNT(*)
            FROM pg_class, pg_namespace
            WHERE relkind='S'
                AND pg_class.relnamespace = pg_namespace.oid
                AND relname=%s""", (sequence,))
        return bool(res.fetchone()[0])

    def set_search_path(self, *search_path):
        path_params = ','.join(['%s'] * len(search_path))
        self.execute_sql('SET search_path TO %s' % path_params, search_path)


class MySQLDatabase(Database):
    commit_select = True
    field_overrides = {
        'bigint': 'BIGINT',
        'boolean': 'BOOL',
        'decimal': 'NUMERIC',
        'double': 'DOUBLE PRECISION',
        'float': 'FLOAT',
        'primary_key': 'INTEGER AUTO_INCREMENT',
        'text': 'LONGTEXT',
    }
    for_update = True
    interpolation = '%s'
    op_overrides = {OP_LIKE: 'LIKE BINARY', OP_ILIKE: 'LIKE'}
    quote_char = '`'
    subquery_delete_same_table = False

    def _connect(self, database, **kwargs):
        if not mysql:
            raise ImproperlyConfigured('MySQLdb must be installed on the system')
        conn_kwargs = {
            'charset': 'utf8',
            'use_unicode': True,
        }
        conn_kwargs.update(kwargs)
        return mysql.connect(db=database, **conn_kwargs)

    def create_foreign_key(self, model_class, field):
        compiler = self.get_compiler()
        framing = """
            ALTER TABLE %(table)s ADD CONSTRAINT %(constraint)s
            FOREIGN KEY (%(field)s) REFERENCES %(to)s(%(to_field)s)%(cascade)s;
        """
        db_table = model_class._meta.db_table
        constraint = 'fk_%s_%s_%s' % (
            db_table,
            field.rel_model._meta.db_table,
            field.db_column,
        )

        query = framing % {
            'table': compiler.quote(db_table),
            'constraint': compiler.quote(constraint),
            'field': compiler.quote(field.db_column),
            'to': compiler.quote(field.rel_model._meta.db_table),
            'to_field': compiler.quote(field.rel_model._meta.primary_key.db_column),
            'cascade': ' ON DELETE CASCADE' if field.cascade else '',
        }

        self.execute_sql(query)
        return super(MySQLDatabase, self).create_foreign_key(model_class, field)

    def get_indexes_for_table(self, table):
        res = self.execute_sql('SHOW INDEXES IN `%s`;' % table)
        rows = sorted([(r[2], r[1] == 0) for r in res.fetchall()])
        return rows

    def get_tables(self):
        res = self.execute_sql('SHOW TABLES;')
        return [r[0] for r in res.fetchall()]
