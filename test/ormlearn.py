#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:29
# @Author  : Cojun  Mao
# @Site    : 
# @File    : ormlearn.py
# @Project : mysite_diy
# @Software: PyCharm
import operator
import re
import sqlite3
import threading

from collections import namedtuple
from copy import deepcopy
from functools import reduce

basestring = unicode = str

OP_AND = 0
OP_OR = 1

OP_ADD = 10
OP_SUB = 11
OP_MUL = 12
OP_DIV = 13
OP_AND = 14
OP_OR = 15
OP_XOR = 16
OP_USER = 19

OP_EQ = 20
OP_LT = 21
OP_LTE = 22
OP_GT = 23
OP_GTE = 24
OP_NE = 25
OP_IN = 26
OP_IS = 27
OP_LIKE = 28
OP_ILIKE = 29
JOIN_INNER = 1
JOIN_LEFT_OUTER = 2
JOIN_FULL = 3

Ordering = namedtuple('Ordering', ('param', 'asc'))
R = namedtuple('R', ('value',))


class Leaf(object):
    def __init__(self):
        self.negated = False
        self._alias = None

    def __invert__(self):
        self.negated = not self.negated
        return self

    def alias(self, a):
        self._alias = a
        return self

    def asc(self):
        return Ordering(self, True)

    def desc(self):
        return Ordering(self, False)

    def _e(op, inv=False):
        def inner(self, rhs):
            if inv:
                return Expr(rhs, op, self)
            return Expr(self, op, rhs)

        return inner

    __and__ = _e(OP_AND)
    __or__ = _e(OP_OR)

    __add__ = _e(OP_ADD)
    __sub__ = _e(OP_SUB)
    __mul__ = _e(OP_MUL)
    __div__ = _e(OP_DIV)
    __xor__ = _e(OP_XOR)
    __radd__ = _e(OP_ADD, inv=True)
    __rsub__ = _e(OP_SUB, inv=True)
    __rmul__ = _e(OP_MUL, inv=True)
    __rdiv__ = _e(OP_DIV, inv=True)
    __rand__ = _e(OP_AND, inv=True)
    __ror__ = _e(OP_OR, inv=True)
    __rxor__ = _e(OP_XOR, inv=True)

    __eq__ = _e(OP_EQ)
    __lt__ = _e(OP_LT)
    __le__ = _e(OP_LTE)
    __gt__ = _e(OP_GT)
    __ge__ = _e(OP_GTE)
    __ne__ = _e(OP_NE)
    __lshift__ = _e(OP_IN)
    __rshift__ = _e(OP_IS)
    __mod__ = _e(OP_LIKE)
    __pow__ = _e(OP_ILIKE)


class Expr(Leaf):
    def __init__(self, lhs, op, rhs, negated=False):
        super(Expr, self).__init__()
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.negated = negated

    def clone(self):
        return Expr(self.lhs, self.op, self.rhs, self.negated)


class DQ(Leaf):
    def __init__(self, **query):
        super(DQ, self).__init__()
        self.query = query

    def clone(self):
        return DQ(**self.query)


class Param(Leaf):
    def __init__(self, data):
        self.data = data
        super(Param, self).__init__()


class Func(Leaf):
    def __init__(self, name, *params):
        self.name = name
        self.params = params
        super(Func, self).__init__()

    def clone(self):
        return Func(self.name, *self.params)

    def __getattr__(self, attr):
        def dec(*args, **kwargs):
            return Func(attr, *args, **kwargs)

        return dec


class Field(Leaf):
    _field_counter = 0
    _order = 0
    db_field = 'unknown'
    template = '%(column_type)s'

    def __init__(self, null=False, index=False, unique=False, verbose_name=None,
                 help_text=None, db_column=None, default=None, choices=None,
                 primary_key=False, sequence=None, *args, **kwargs):
        self.null = null
        self.index = index
        self.unique = unique
        self.verbose_name = verbose_name
        self.help_text = help_text
        self.db_column = db_column
        self.default = default
        self.choices = choices
        self.primary_key = primary_key
        self.sequence = sequence

        self.attributes = self.field_attributes()
        self.attributes.update(kwargs)

        Field._field_counter += 1
        self._order = Field._field_counter

        super(Field, self).__init__()

    def add_to_class(self, model_class, name):
        self.name = name
        self.model_class = model_class
        self.db_column = self.db_column or self.name
        self.verbose_name = self.verbose_name or re.sub('_+', ' ', name).title()

        model_class._meta.fields[self.name] = self
        model_class._meta.columns[self.db_column] = self
        setattr(model_class, name, FieldDescriptor(self))

    def field_attributes(self):
        return {}

    def get_db_field(self):
        return self.db_field

    def coerce(self, value):
        return value

    def db_value(self, value):
        return value if value is None else self.coerce(value)

    def python_value(self, value):
        return value if value is None else self.coerce(value)


class IntegerField(Field):
    db_field = 'int'

    def coerce(self, value):
        return int(value)


class BigIntegerField(IntegerField):
    field_type = 'BigIntegerField'


class SmallIntegerField(IntegerField):
    field_type = 'SMALLIntegerField'


class AutoField(IntegerField):
    field_type = "AutoField"
    auto_increment = True  # 是否自增


def format_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s
    elif isinstance(s, basestring):
        return s.decode(encoding)
    elif hasattr(s, '__unicode__'):
        return s.__unicode__()
    else:
        return unicode(bytes(s), encoding)


class TextField(Field):
    db_field = 'text'

    def coerce(self, value):
        return format_unicode(value or '')


class ReverseRelationDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.rel_model = field.model_class

    def __get__(self, instance, instance_type=None):
        if instance:
            return self.rel_model.select().where(self.field == instance.get_id())
        return self


class PrimaryKeyField(IntegerField):
    db_field = 'primary_key'

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(PrimaryKeyField, self).__init__(*args, **kwargs)


class ForeignKeyField(IntegerField):
    """外键"""

    def __init__(self, rel_model, null=False, related_name=None, cascade=False, extra=None, *args, **kwargs):
        """

        :param rel_model:
        :param null:
        :param related_name:关联名称
        :param cascade:级联
        :param extra:额外的
        :param args:
        :param kwargs:
        """
        self.rel_model = rel_model
        self._related_name = related_name
        self.cascade = cascade
        self.extra = extra
        # 'ON DELETE CASCADE'主外键关系中，级联删除，即删除主表数据会自动删除从表数据
        kwargs.update(dict(
            cascade='ON DELETE CASCADE' if self.cascade else '',
            extra=extra or '',
        ))

        super(ForeignKeyField, self).__init__(null=null, *args, **kwargs)

    def add_to_class(self, model_class, name):
        self.name = name
        self.model_class = model_class
        self.db_column = self.db_column or '%s_id' % self.name
        self.verbose_name = self.verbose_name or re.sub('_+', ' ', name).title()

        model_class._meta.fields[self.name] = self
        model_class._meta.columns[self.db_column] = self

        self.related_name = self._related_name or '%s_set' % (model_class._meta.name)

        if self.rel_model == 'self':
            self.rel_model = self.model_class
        if self.related_name in self.rel_model._meta.fields:
            raise AttributeError('Foreign key: %s.%s related name "%s" collision with field of same name' % (
                self.model_class._meta.name, self.name, self.related_name))

        setattr(model_class, name, RelationDescriptor(self, self.rel_model))
        setattr(self.rel_model, self.related_name, ReverseRelationDescriptor(self))

        model_class._meta.rel[self.name] = self
        self.rel_model._meta.reverse_rel[self.related_name] = self

    def get_db_field(self):
        to_pk = self.rel_model._meta.primary_key
        # if not isinstance(to_pk, PrimaryKeyField):
        #     return to_pk.get_db_field()
        return super(ForeignKeyField, self).get_db_field()

    def coerce(self, value):
        return self.rel_model._meta.primary_key.coerce(value)

    def db_value(self, value):
        if isinstance(value, self.rel_model):
            value = value.get_id()
        return self.rel_model._meta.primary_key.db_value(value)


class CharField(Field):
    db_field = 'string'
    template = '%(column_type)s(%(max_length)s)'

    def field_attributes(self):
        return {'max_length': 255}

    def coerce(self, value):
        value = format_unicode(value or '')
        return value[:self.attributes['max_length']]


class FieldDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.att_name = self.field.name

    def __get__(self, instance, instance_type=None):
        if instance:
            return instance._data.get(self.att_name)
        return self.field

    def __set__(self, instance, value):
        instance._data[self.att_name] = value


class RelationDescriptor(FieldDescriptor):
    def __init__(self, field, rel_model):
        self.rel_model = rel_model
        super(RelationDescriptor, self).__init__(field)

    def get_object_or_id(self, instance):
        rel_id = instance._data.get(self.att_name)
        if rel_id is not None or self.att_name in instance._obj_cache:
            if self.att_name not in instance._obj_cache:
                obj = self.rel_model.get(self.rel_model._meta.primary_key == rel_id)
                instance._obj_cache[self.att_name] = obj
            return instance._obj_cache[self.att_name]
        elif not self.field.null:
            raise self.rel_model.DoesNotExist
        return rel_id

    def __get__(self, instance, instance_type=None):
        if instance:
            return self.get_object_or_id(instance)
        return self.field

    def __set__(self, instance, value):
        if isinstance(value, self.rel_model):
            instance._data[self.att_name] = value.get_id()
            instance._obj_cache[self.att_name] = value
        else:
            instance._data[self.att_name] = value


def dict_update(orig, extra):
    new = {}
    new.update(orig)
    new.update(extra)
    return new


class QueryCompiler(object):
    field_map = {
        'int': 'INTEGER',
        'bigint': 'INTEGER',
        'float': 'REAL',
        'double': 'REAL',
        'decimal': 'DECIMAL',
        'string': 'VARCHAR',
        'text': 'TEXT',
        'datetime': 'DATETIME',
        'date': 'DATE',
        'time': 'TIME',
        'bool': 'SMALLINT',
        'primary_key': 'INTEGER',
    }

    op_map = {
        OP_EQ: '=',
        OP_LT: '<',
        OP_LTE: '<=',
        OP_GT: '>',
        OP_GTE: '>=',
        OP_NE: '!=',
        OP_IN: 'IN',
        OP_IS: 'IS',
        OP_LIKE: 'LIKE',
        OP_ILIKE: 'ILIKE',
        OP_ADD: '+',
        OP_SUB: '-',
        OP_MUL: '*',
        OP_DIV: '/',
        OP_XOR: '^',
        OP_AND: 'AND',
        OP_OR: 'OR',
    }

    join_map = {
        JOIN_INNER: 'INNER',
        JOIN_LEFT_OUTER: 'LEFT OUTER',
        JOIN_FULL: 'FULL',
    }

    def __init__(self, quote_char='"', interpolation='?', field_overrides=None,
                 op_overrides=None):
        self.quote_char = quote_char
        self.interpolation = interpolation
        self._field_map = dict_update(self.field_map, field_overrides or {})
        self._op_map = dict_update(self.op_map, op_overrides or {})

    def quote(self, s):
        return ''.join((self.quote_char, s, self.quote_char))

    def get_field(self, f):
        return self._field_map[f]

    def get_op(self, q):
        return self._op_map[q]

    def _max_alias(self, am):
        max_alias = 0
        if am:
            for a in am.values():
                i = int(a.lstrip('t'))
                if i > max_alias:
                    max_alias = i
        return max_alias + 1

    def parse_expr(self, expr, alias_map=None, conv=None):
        s = self.interpolation
        p = [expr]
        if isinstance(expr, Expr):
            if isinstance(expr.lhs, Field):
                conv = expr.lhs
            lhs, lparams = self.parse_expr(expr.lhs, alias_map, conv)
            rhs, rparams = self.parse_expr(expr.rhs, alias_map, conv)
            s = '(%s %s %s)' % (lhs, self.get_op(expr.op), rhs)
            p = lparams + rparams
        elif isinstance(expr, Field):
            s = self.quote(expr.db_column)
            if alias_map and expr.model_class in alias_map:
                s = '.'.join((alias_map[expr.model_class], s))
            p = []
        elif isinstance(expr, Func):
            p = []
            exprs = []
            for param in expr.params:
                parsed, params = self.parse_expr(param, alias_map, conv)
                exprs.append(parsed)
                p.extend(params)
            s = '%s(%s)' % (expr.name, ', '.join(exprs))
        elif isinstance(expr, Param):
            s = self.interpolation
            p = [expr.data]
        elif isinstance(expr, Ordering):
            s, p = self.parse_expr(expr.param, alias_map, conv)
            s += ' ASC' if expr.asc else ' DESC'
        elif isinstance(expr, R):
            s = expr.value
            p = []
        elif isinstance(expr, SelectQuery):
            max_alias = self._max_alias(alias_map)
            clone = expr.clone()
            if not expr._explicit_selection:
                clone._select = (clone.model_class._meta.primary_key,)
            subselect, p = self.parse_select_query(clone, max_alias, alias_map)
            s = '(%s)' % subselect
        elif isinstance(expr, (list, tuple)):
            exprs = []
            p = []
            for i in expr:
                e, v = self.parse_expr(i, alias_map, conv)
                exprs.append(e)
                p.extend(v)
            s = '(%s)' % ','.join(exprs)
        elif isinstance(expr, Model):
            s = self.interpolation
            p = [expr.get_id()]
        elif conv and p:
            p = [conv.db_value(i) for i in p]

        if isinstance(expr, Leaf):
            if expr.negated:
                s = 'NOT %s' % s
            if expr._alias:
                s = ' '.join((s, 'AS', expr._alias))

        return s, p

    def parse_query_node(self, qnode, alias_map):
        if qnode is not None:
            return self.parse_expr(qnode, alias_map)
        return '', []

    def parse_joins(self, joins, model_class, alias_map):
        parsed = []
        seen = set()

        def _traverse(curr):
            if curr not in joins or curr in seen:
                return
            seen.add(curr)
            for join in joins[curr]:
                from_model = curr
                to_model = join.model_class

                field = from_model._meta.rel_for_model(to_model, join.on)
                if field:
                    left_field = field.db_column
                    right_field = to_model._meta.primary_key.db_column
                else:
                    field = to_model._meta.rel_for_model(from_model, join.on)
                    left_field = from_model._meta.primary_key.db_column
                    right_field = field.db_column

                join_type = join.join_type or JOIN_INNER
                lhs = '%s.%s' % (alias_map[from_model], self.quote(left_field))
                rhs = '%s.%s' % (alias_map[to_model], self.quote(right_field))

                parsed.append('%s JOIN %s AS %s ON %s = %s' % (
                    self.join_map[join_type],
                    self.quote(to_model._meta.db_table),
                    alias_map[to_model],
                    lhs,
                    rhs,
                ))

                _traverse(to_model)

        _traverse(model_class)
        return parsed

    def parse_expr_list(self, s, alias_map):
        parsed = []
        data = []
        for expr in s:
            expr_str, vars = self.parse_expr(expr, alias_map)
            parsed.append(expr_str)
            data.extend(vars)
        return ', '.join(parsed), data

    def calculate_alias_map(self, query, start=1):
        alias_map = {query.model_class: 't%s' % start}
        for model, joins in query._joins.items():
            if model not in alias_map:
                start += 1
                alias_map[model] = 't%s' % start
            for join in joins:
                if join.model_class not in alias_map:
                    start += 1
                    alias_map[join.model_class] = 't%s' % start
        return alias_map

    def parse_select_query(self, query, start=1, alias_map=None):
        model = query.model_class
        db = model._meta.database

        alias_map = alias_map or {}
        alias_map.update(self.calculate_alias_map(query, start))

        parts = ['SELECT']
        params = []

        if query._distinct:
            parts.append('DISTINCT')  # DISTINCT 关键字与 SELECT 语句一起使用，来消除所有重复的记录，并只获取唯一一次记录。

        selection = query._select
        select, s_params = self.parse_expr_list(selection, alias_map)

        parts.append(select)
        params.extend(s_params)

        parts.append('FROM %s AS %s' % (self.quote(model._meta.db_table), alias_map[model]))

        joins = self.parse_joins(query._joins, query.model_class, alias_map)
        if joins:
            parts.append(' '.join(joins))

        where, w_params = self.parse_query_node(query._where, alias_map)
        if where:
            parts.append('WHERE %s' % where)
            params.extend(w_params)

        if query._group_by:
            group_by, g_params = self.parse_expr_list(query._group_by, alias_map)
            parts.append('GROUP BY %s' % group_by)
            params.extend(g_params)

        if query._having:
            having, h_params = self.parse_query_node(query._having, alias_map)
            parts.append('HAVING %s' % having)
            params.extend(h_params)

        if query._order_by:
            order_by, _ = self.parse_expr_list(query._order_by, alias_map)
            parts.append('ORDER BY %s' % order_by)

        if query._limit or (query._offset and not db.empty_limit):
            limit = query._limit or -1
            parts.append('LIMIT %s' % limit)
        if query._offset:
            parts.append('OFFSET %s' % query._offset)
        if query._for_update:
            parts.append('FOR UPDATE')

        return ' '.join(parts), params

    def _parse_field_dictionary(self, d):
        sets, params = [], []
        for field, expr in d.items():
            field_str, _ = self.parse_expr(field)
            val_str, val_params = self.parse_expr(expr)
            val_params = [field.db_value(vp) for vp in val_params]
            sets.append((field_str, val_str))
            params.extend(val_params)
        return sets, params

    def parse_update_query(self, query):
        model = query.model_class

        parts = ['UPDATE %s SET' % self.quote(model._meta.db_table)]
        sets, params = self._parse_field_dictionary(query._update)

        parts.append(', '.join('%s=%s' % (f, v) for f, v in sets))

        where, w_params = self.parse_query_node(query._where, None)
        if where:
            parts.append('WHERE %s' % where)
            params.extend(w_params)
        return ' '.join(parts), params

    def parse_insert_query(self, query):
        model = query.model_class

        parts = ['INSERT INTO %s' % self.quote(model._meta.db_table)]
        sets, params = self._parse_field_dictionary(query._insert)

        parts.append('(%s)' % ', '.join(s[0] for s in sets))
        parts.append('VALUES (%s)' % ', '.join(s[1] for s in sets))

        return ' '.join(parts), params

    def parse_delete_query(self, query):
        model = query.model_class

        parts = ['DELETE FROM %s' % self.quote(model._meta.db_table)]
        params = []

        where, w_params = self.parse_query_node(query._where, None)
        if where:
            parts.append('WHERE %s' % where)
            params.extend(w_params)

        return ' '.join(parts), params

    def field_sql(self, field):
        attrs = field.attributes
        attrs['column_type'] = self.get_field(field.get_db_field())
        template = field.template
        print('column_type： %s' % attrs['column_type'])

        if isinstance(field, ForeignKeyField):
            to_pk = field.rel_model._meta.primary_key
            if not isinstance(to_pk, PrimaryKeyField):
                template = to_pk.template
                attrs.update(to_pk.attributes)
        print('template： %s' % template)
        parts = [self.quote(field.db_column), template]
        print('field_sql parts： %s' % parts)
        if not field.null:
            parts.append('NOT NULL')
        if field.primary_key:
            parts.append('PRIMARY KEY')
        if isinstance(field, ForeignKeyField):
            ref_mc = (
                self.quote(field.rel_model._meta.db_table),
                self.quote(field.rel_model._meta.primary_key.db_column),
            )
            parts.append('REFERENCES %s (%s)' % ref_mc)
            parts.append('%(cascade)s%(extra)s')
        elif field.sequence:
            parts.append("DEFAULT NEXTVAL('%s')" % self.quote(field.sequence))
        return ' '.join(p % attrs for p in parts)

    def parse_create_table(self, model_class, safe=False):
        parts = ['CREATE TABLE']
        if safe:
            parts.append('IF NOT EXISTS')
        parts.append(self.quote(model_class._meta.db_table))
        columns = ', '.join(self.field_sql(f) for f in model_class._meta.get_fields())
        parts.append('(%s)' % columns)
        # print(' parts: %s' % parts)
        return parts

    def create_table(self, model_class, safe=False):
        return ' '.join(self.parse_create_table(model_class, safe))

    def drop_table(self, model_class, fail_silently=False, cascade=False):
        parts = ['DROP TABLE']
        if fail_silently:
            parts.append('IF EXISTS')
        parts.append(self.quote(model_class._meta.db_table))
        if cascade:
            parts.append('CASCADE')
        return ' '.join(parts)

    def parse_create_index(self, model_class, fields, unique):
        tbl_name = model_class._meta.db_table
        colnames = [f.db_column for f in fields]
        parts = ['CREATE %s' % ('UNIQUE INDEX' if unique else 'INDEX')]
        parts.append(self.quote('%s_%s' % (tbl_name, '_'.join(colnames))))
        parts.append('ON %s' % self.quote(tbl_name))
        parts.append('(%s)' % ', '.join(map(self.quote, colnames)))
        return parts

    def create_index(self, model_class, fields, unique):
        return ' '.join(self.parse_create_index(model_class, fields, unique))

    def create_sequence(self, sequence_name):
        return 'CREATE SEQUENCE %s;' % self.quote(sequence_name)

    def drop_sequence(self, sequence_name):
        return 'DROP SEQUENCE %s;' % self.quote(sequence_name)


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
                 fields=None, ops=None, **connect_kwargs):
        self.init(database, **connect_kwargs)

        if threadlocals:
            self.__local = threading.local()
        else:
            self.__local = type('DummyLocal', (object,), {})

        self._conn_lock = threading.Lock()
        self.autocommit = autocommit

    def init(self, database, **connect_kwargs):
        self.deferred = database is None
        self.database = database
        self.connect_kwargs = connect_kwargs

    def connect(self):
        with self._conn_lock:
            if self.deferred:
                raise Exception('Error, database not properly initialized before opening connection')
            self.__local.conn = self._connect(self.database, **self.connect_kwargs)
            self.__local.closed = False

    def close(self):
        with self._conn_lock:
            if self.deferred:
                raise Exception('Error, database not properly initialized before closing connection')
            self._close(self.__local.conn)
            self.__local.closed = True

    def get_conn(self):
        if not hasattr(self.__local, 'closed') or self.__local.closed:
            self.connect()
        return self.__local.conn

    def is_closed(self):
        return getattr(self.__local, 'closed', True)

    def get_cursor(self):
        return self.get_conn().cursor()

    def _close(self, conn):
        conn.close()

    def _connect(self, database, **kwargs):
        raise NotImplementedError

    # @classmethod
    # def register_fields(cls, fields):
    #     cls.field_overrides = dict_update(cls.field_overrides, fields)
    #
    # @classmethod
    # def register_ops(cls, ops):
    #     cls.op_overrides = dict_update(cls.op_overrides, ops)

    def last_insert_id(self, cursor, model):
        if model._meta.auto_increment:
            return cursor.lastrowid

    def rows_affected(self, cursor):
        return cursor.rowcount

    def get_compiler(self):
        return self.compiler_class(
            self.quote_char, self.interpolation, self.field_overrides,
            self.op_overrides)

    def execute_sql(self, sql, params=None, require_commit=True):
        cursor = self.get_cursor()
        # sq = "%s" % sql
        # print(' sq: %s' % sq)
        cursor.execute(sql, params or ())
        if require_commit and self.get_autocommit():
            self.commit()
            return cursor

    def begin(self):
        pass

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

    def get_tables(self):
        raise NotImplementedError

    def get_indexes_for_table(self, table):
        raise NotImplementedError

    def sequence_exists(self, seq):
        raise NotImplementedError

    def create_table(self, model_class):
        qc = self.get_compiler()
        print(' qc: %s' % qc.create_table(model_class))
        return self.execute_sql(qc.create_table(model_class))

    def create_index(self, model_class, fields, unique=False, ):
        qc = self.get_compiler()
        if not isinstance(fields, (list, tuple)):
            raise ValueError('fields passed to "create_index" must be a list or tuple: "%s"' % fields)
        field_objs = [model_class._meta.fields[f] if isinstance(f, basestring) else f for f in fields]
        return self.execute_sql(qc.create_index(model_class, field_objs, unique))

    def create_foreign_key(self, model_class, field):
        if not field.primary_key:
            return self.create_index(model_class, [field], field.unique)

    def create_sequence(self, seq):
        if self.sequences:
            qc = self.get_compiler()
            return self.execute_sql(qc.create_sequence(seq))

    def drop_table(self, model_class, fail_silently=False):
        qc = self.get_compiler()
        return self.execute_sql(qc.drop_table(model_class, fail_silently))

    def drop_sequence(self, seq):
        if self.sequences:
            qc = self.get_compiler()
            return self.execute_sql(qc.drop_sequence(seq))

    def transaction(self):
        return transaction(self)

    def commit_on_success(self, func):
        def inner(*args, **kwargs):
            orig = self.get_autocommit()
            self.set_autocommit(False)
            self.begin()
            try:
                res = func(*args, **kwargs)
                self.commit()
            except:
                self.rollback()
                raise
            else:
                return res
            finally:
                self.set_autocommit(orig)

        return inner


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

    def get_indexes_for_table(self, table):
        res = self.execute_sql('PRAGMA index_list(%s);' % self.quote(table))
        rows = sorted([(r[1], r[2] == 1) for r in res.fetchall()])
        return rows

    def get_tables(self):
        res = self.execute_sql('select name  from sqlite_master where type="table" order by name')
        # print(' res: %s' % list(res))#res: [('u',), ('ur',), ('user',)]
        return [r[0] for r in res.fetchall()]


default_database = SqliteDatabase('peewee.db')


class ModelOptions(object):
    def __init__(self, cls, database=None, db_table=None, indexes=None,
                 order_by=None, primary_key=None):
        self.model_class = cls
        self.name = cls.__name__.lower()
        self.fields = {}
        self.columns = {}
        self.defaults = {}
        self.database = database
        # self.database = database or default_database
        self.db_table = db_table
        self.indexes = indexes or []
        self.order_by = order_by
        self.primary_key = primary_key

        self.auto_increment = None
        self.rel = {}
        self.reverse_rel = {}

    def prepared(self):
        for field in self.fields.values():
            if field.default is not None:
                self.defaults[field] = field.default

        if self.order_by:
            norm_order_by = []
            for clause in self.order_by:
                field = self.fields[clause.lstrip('-')]
                if clause.startswith('-'):
                    norm_order_by.append(field.desc())
                else:
                    norm_order_by.append(field.asc())
            self.order_by = norm_order_by

    def get_default_dict(self):
        dd = {}
        for field, default in self.defaults.items():
            if callable(default):
                dd[field.name] = default()
            else:
                dd[field.name] = default
        return dd

    def get_sorted_fields(self):
        # lambda (k,v)python3不支持  httphelper: // www.voidcn.com / article / p - hzlltdtw - bd.html
        # return sorted(self.fields.items(), key=lambda (k,v): (v is self.primary_key and 1 or 2, v._order))
        return sorted(self.fields.items(), key=lambda k_v: (k_v[1] is self.primary_key and 1 or 2, k_v[1]._order))

    def get_field_names(self):
        return [f[0] for f in self.get_sorted_fields()]

    def get_fields(self):
        return [f[1] for f in self.get_sorted_fields()]

    def rel_for_model(self, model, field_obj=None):
        for field in self.get_fields():
            if isinstance(field, ForeignKeyField) and field.rel_model == model:
                if field_obj is None or field_obj.name == field.name:
                    return field

    def reverse_rel_for_model(self, model):
        return model._meta.rel_for_model(self.model_class)

    def rel_exists(self, model):
        return self.rel_for_model(model) or self.reverse_rel_for_model(model)


class FieldDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.att_name = self.field.name

    def __get__(self, instance, instance_type=None):
        if instance:
            return instance._data.get(self.att_name)
        return self.field

    def __set__(self, instance, value):
        instance._data[self.att_name] = value


class DoesNotExist(Exception):
    pass


def not_allowed(fn):
    def inner(self, *args, **kwargs):
        raise NotImplementedError('%s is not allowed on %s instances' % (
            fn, type(self).__name__,
        ))

    return inner


def returns_clone(func):
    def inner(self, *args, **kwargs):
        clone = self.clone()
        func(clone, *args, **kwargs)
        return clone

    inner.call_local = func
    return inner


class Query(object):
    require_commit = True

    def __init__(self, model_class):
        self.model_class = model_class
        self.database = model_class._meta.database

        self._dirty = True
        self._query_ctx = model_class
        self._joins = {self.model_class: []}  # adjacency graph邻接图
        self._where = None

    def clone(self):
        query = type(self)(self.model_class)
        if self._where is not None:
            query._where = self._where.clone()
        query._joins = self.clone_joins()
        query._query_ctx = self._query_ctx
        return query

    def clone_joins(self):
        return dict(
            (mc, list(j)) for mc, j in self._joins.items()
        )

    @returns_clone
    def where(self, *q_or_node):
        if self._where is None:
            self._where = reduce(operator.and_, q_or_node)
        else:
            for piece in q_or_node:
                self._where &= piece

    @returns_clone
    def join(self, model_class, join_type=None, on=None):
        if not self._query_ctx._meta.rel_exists(model_class):
            raise ValueError('No foreign key between %s and %s' % (
                self._query_ctx, model_class,
            ))
        if on and isinstance(on, basestring):
            on = self._query_ctx._meta.fields[on]
        self._joins.setdefault(self._query_ctx, [])
        self._joins[self._query_ctx].append(Join(model_class, join_type, on))
        self._query_ctx = model_class

    @returns_clone
    def switch(self, model_class=None):
        self._query_ctx = model_class or self.model_class

    def ensure_join(self, lm, rm, on=None):
        ctx = self._query_ctx
        for join in self._joins.get(lm, []):
            if join.model_class == rm:
                return self
        query = self.switch(lm).join(rm, on=on).switch(ctx)
        return query

    def convert_dict_to_node(self, qdict):
        accum = []
        joins = []
        for key, value in sorted(qdict.items()):
            curr = self.model_class
            if '__' in key and key.rsplit('__', 1)[1] in DJANGO_MAP:
                key, op = key.rsplit('__', 1)
                op = DJANGO_MAP[op]
            else:
                op = OP_EQ
            for piece in key.split('__'):
                model_attr = getattr(curr, piece)
                if isinstance(model_attr, (ForeignKeyField, ReverseRelationDescriptor)):
                    curr = model_attr.rel_model
                    joins.append(model_attr)
            accum.append(Expr(model_attr, op, value))
        return accum, joins

    def filter(self, *args, **kwargs):
        # normalize args and kwargs into a new expression
        dq_node = Leaf()
        if args:
            dq_node &= reduce(operator.and_, [a.clone() for a in args])
        if kwargs:
            dq_node &= DQ(**kwargs)

        # dq_node should now be an Expr, lhs = Leaf(), rhs = ...
        q = deque([dq_node])
        dq_joins = set()
        while q:
            curr = q.popleft()
            if not isinstance(curr, Expr):
                continue
            for side, piece in (('lhs', curr.lhs), ('rhs', curr.rhs)):
                if isinstance(piece, DQ):
                    query, joins = self.convert_dict_to_node(piece.query)
                    dq_joins.update(joins)
                    setattr(curr, side, reduce(operator.and_, query))
                else:
                    q.append(piece)

        dq_node = dq_node.rhs

        query = self.clone()
        for field in dq_joins:
            if isinstance(field, ForeignKeyField):
                lm, rm = field.model_class, field.rel_model
                field_obj = field
            elif isinstance(field, ReverseRelationDescriptor):
                lm, rm = field.field.rel_model, field.rel_model
                field_obj = field.field
            query = query.ensure_join(lm, rm, field_obj)
        return query.where(dq_node)

    def get_compiler(self):
        return self.database.get_compiler()

    def sql(self):
        raise NotImplementedError

    def _execute(self):
        sql, params = self.sql()
        return self.database.execute_sql(sql, params, self.require_commit)

    def execute(self):
        raise NotImplementedError

    def scalar(self, as_tuple=False):
        row = self._execute().fetchone()
        if row and not as_tuple:
            return row[0]
        else:
            return row


class SelectQuery(Query):
    def __init__(self, model_class, *selection):
        super(SelectQuery, self).__init__(model_class)
        self.require_commit = self.database.commit_select
        self._explicit_selection = len(selection) > 0
        self._select = self._model_shorthand(selection or model_class._meta.get_fields())
        self._group_by = None
        self._having = None
        self._order_by = None
        self._limit = None
        self._offset = None
        self._distinct = False
        self._for_update = False
        self._naive = False
        self._qr = None

    def clone(self):
        query = super(SelectQuery, self).clone()
        query._explicit_selection = self._explicit_selection
        query._select = list(self._select)
        if self._group_by is not None:
            query._group_by = list(self._group_by)
        if self._having:
            query._having = self._having.clone()
        if self._order_by is not None:
            query._order_by = list(self._order_by)
        query._limit = self._limit
        query._offset = self._offset
        query._distinct = self._distinct
        query._for_update = self._for_update
        query._naive = self._naive
        return query

    def _model_shorthand(self, args):
        accum = []
        for arg in args:
            if isinstance(arg, Leaf):
                accum.append(arg)
            elif issubclass(arg, Model):
                accum.extend(arg._meta.get_fields())
        return accum

    @returns_clone
    def group_by(self, *args):
        self._group_by = self._model_shorthand(args)

    @returns_clone
    def having(self, *q_or_node):
        if self._having is None:
            self._having = reduce(operator.and_, q_or_node)
        else:
            for piece in q_or_node:
                self._having &= piece

    @returns_clone
    def order_by(self, *args):
        self._order_by = list(args)

    @returns_clone
    def limit(self, lim):
        self._limit = lim

    @returns_clone
    def offset(self, off):
        self._offset = off

    @returns_clone
    def paginate(self, page, paginate_by=20):
        if page > 0:
            page -= 1
        self._limit = paginate_by
        self._offset = page * paginate_by

    @returns_clone
    def distinct(self, is_distinct=True):
        self._distinct = is_distinct

    @returns_clone
    def for_update(self, for_update=True):
        self._for_update = for_update

    @returns_clone
    def naive(self, naive=True):
        self._naive = naive

    def annotate(self, rel_model, annotation=None):
        annotation = annotation or fn.Count(rel_model._meta.primary_key).alias('count')
        query = self.clone()
        query = query.ensure_join(query._query_ctx, rel_model)
        if not query._group_by:
            query._group_by = list(query._select)
        query._select = tuple(query._select) + (annotation,)
        return query

    def _aggregate(self, aggregation=None):
        aggregation = aggregation or fn.Count(self.model_class._meta.primary_key)
        query = self.order_by()
        query._select = [aggregation]
        return query

    def aggregate(self, aggregation=None):
        return self._aggregate(aggregation).scalar()

    def count(self):
        if self._distinct or self._group_by:
            return self.wrapped_count()

        # defaults to a count() of the primary key
        return self.aggregate() or 0

    def wrapped_count(self):
        clone = self.order_by()
        clone._limit = clone._offset = None

        sql, params = clone.sql()
        wrapped = 'SELECT COUNT(1) FROM (%s) AS wrapped_select' % sql
        rq = RawQuery(self.model_class, wrapped, *params)
        return rq.scalar() or 0

    def exists(self):
        clone = self.paginate(1, 1)
        clone._select = [self.model_class._meta.primary_key]
        return bool(clone.scalar())

    def get(self):
        clone = self.paginate(1, 1)
        try:
            return clone.execute().next()
        except StopIteration:
            raise self.model_class.DoesNotExist('instance matching query does not exist:\nSQL: %s\nPARAMS: %s' % (
                self.sql()
            ))

    def sql(self):
        return self.get_compiler().parse_select_query(self)

    def verify_naive(self):
        for expr in self._select:
            if isinstance(expr, Field) and expr.model_class != self.model_class:
                return False
        return True

    def execute(self):
        if self._dirty or not self._qr:
            if self._naive or not self._joins or self.verify_naive():
                query_meta = None
            else:
                query_meta = [self._select, self._joins]
            self._qr = QueryResultWrapper(self.model_class, self._execute(), query_meta)
            self._dirty = False
            return self._qr
        else:
            return self._qr

    def __iter__(self):
        return iter(self.execute())

    def __getitem__(self, value):
        offset = limit = None
        if isinstance(value, slice):
            if value.start:
                offset = value.start
            if value.stop:
                limit = value.stop - (value.start or 0)
        else:
            if value < 0:
                raise ValueError('Negative indexes are not supported, try ordering in reverse')
            offset = value
            limit = 1
        if self._limit != limit or self._offset != offset:
            self._qr = None
        self._limit = limit
        self._offset = offset
        res = list(self)
        return limit == 1 and res[0] or res


class InsertQuery(Query):
    def __init__(self, model_class, insert=None):
        mm = model_class._meta
        query = dict((mm.fields[f], v) for f, v in mm.get_default_dict().items())
        query.update(insert)
        self._insert = query
        super(InsertQuery, self).__init__(model_class)

    def clone(self):
        query = super(InsertQuery, self).clone()
        query._insert = dict(self._insert)
        return query

    join = not_allowed('joining')
    where = not_allowed('where clause')

    def sql(self):
        return self.get_compiler().parse_insert_query(self)

    def execute(self):
        return self.database.last_insert_id(self._execute(), self.model_class)


class UpdateQuery(Query):
    def __init__(self, model_class, update=None):
        self._update = update
        super(UpdateQuery, self).__init__(model_class)

    def clone(self):
        query = super(UpdateQuery, self).clone()
        query._update = dict(self._update)
        return query

    join = not_allowed('joining')

    def sql(self):
        return self.get_compiler().parse_update_query(self)

    def execute(self):
        return self.database.rows_affected(self._execute())


class ModelMetaclass(type):
    # inheritable_options = ['database', 'indexes', 'order_by', 'primary_key']
    #
    # def __new__(mcs, name, bases, attrs):
    #
    #     # 假定用户创建的类的父类是Model,不进行任何操作，因为需要修改的是用户自定义类
    #     if name == 'Model':
    #         return type.__new__(mcs, name, bases, attrs)
    #     meta_options = {}
    #     meta = attrs.pop('Meta', None)
    #     if meta:
    #         meta_options.update((k, v) for k, v in meta.__dict__.items() if not k.startswith('_'))
    #     for b in bases:
    #         if not hasattr(b, '_meta'):
    #             continue
    #
    #         base_meta = getattr(b, '_meta')
    #         for (k, v) in base_meta.__dict__.items():
    #             if k in mcs.inheritable_options and k not in meta_options:
    #                 meta_options[k] = v
    #
    #         for (k, v) in b.__dict__.items():
    #             if isinstance(v, Field) and k not in attrs:
    #                 if not v.field.primary_key:
    #                     attrs[k] = deepcopy(v.field)
    #
    #     _meta = ModelOptions(mcs, **meta_options)
    #     # 因为用户创建的类应当与一个数据库中的表挂钩，也就是关系映射
    #     # 用户对这个类的操作会影响数据库中对应表的操作，无需使用SQL语句直接与数据库打交道，方便使用
    #     # 因为这一切都交给ORM框架了，所以对于编写者来说，需要从用户定义的类中获取需要的信息，然后代替用户实现数据库的操作
    #     # 需要获取的数据有：表名，主键，其他字段，用户类中的映射关系
    #
    #     # 尝试从类的__table__属性中获取表名，没找到就使用用户定义的类名作为表名
    #     # table_name = attrs.get('__table__', None) or name
    #     if not _meta.db_table:
    #         # mcs._meta.db_table = re.sub('[^\w]+', '_', mcs.__name__.lower())
    #         _meta.db_table = attrs.get('table', None) or name
    #     # 稍后获取
    #     primaryKey = None
    #     fields = []
    #     mappings = dict()  # 用户类中的映射关系
    #
    #     # 一个k, v 类似于 id : IntegerField('id')
    #     # 其中k是id，v是IntegerField的一个实例
    #     # 可以使用print(attrs)查看有哪些属性，帮助理解
    #     for k, v in attrs.items():  # 查找定义的类的所有属性，
    #         if isinstance(v, Field):  # 如果找到一个Field属性，
    #             mappings[k] = v  # 保存映射关系，把它保存到一个__mappings__的dict中
    #             # 如果是主键，判断是否只有一个主键
    #             if v.primary_key:
    #                 # 如果定义了多个主键，报错
    #                 if primaryKey:
    #                     raise Exception('Duplicate primary key for field: %s' % k)
    #                 primaryKey = k
    #             # 不是主键则添加到fields里
    #             else:
    #                 fields.append(k)
    #
    #     # 如果所有属性里都没有主键，报错
    #     if primaryKey is None:
    #         raise BaseException('Primary key not found.')
    #     # 从类属性中删除该Field属性，否则容易造成运行时错误（实例的属性会遮盖类的同名属性）
    #     for k in mappings.keys():
    #         attrs.pop(k)  # 同时从类属性中删除该Field属性，否则，容易造成运行时错误（实例的属性会遮盖类的同名属性）
    #
    #     # 数据库操作中有时候会遇到特殊的字段名或者表名，比如table name，存在空格。这时可以使用``，比如`table name`
    #     # escaped_fields = list(map(lambda f: '`%s`' % f, fields))  # 关于map函数不再赘述，有问题可网上查找相关资料
    #
    #     # 将获取到的数据作为类属性
    #     attrs['__mappings__'] = mappings  # 映射关系
    #     # attrs['__table__'] = table_name  # 表名
    #     attrs['__primary_key__'] = primaryKey  # 主键
    #     attrs['__fields__'] = fields  # 除了主键外的字段
    #     attrs['_meta'] = _meta
    #     # 提前设置好SQL语句的模板
    #     # attrs['__select__'] = 'select `%s` , %s from `%s` ' % (primary_key, ', '.join(escaped_fields), table_name)
    #     # attrs['__insert__'] = 'insert into `%s` (`%s`,%s) values (%s)' % (
    #     #     table_name, primary_key, ', '.join(escaped_fields), create_args_string(len(escaped_fields) + 1))
    #     # attrs['__update__'] = 'update `%s` set %s where `%s`=? ' % (
    #     #     table_name, ', '.join(map(lambda f: '`%s` = ?' % (mappings.get(f).name or f), fields)), primary_key)
    #     # attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (table_name, primary_key)
    #
    #     # 将拦截的类修改之后，返回新的类
    #     return type.__new__(mcs, name, bases, attrs)

    # 定义Model类，当用户如果需要与数据库交互，应当继承自该类
    # 定义一些方法，用于某些数据库操作
    # 父类是dict，方便操作，因为基本上都是字典数据
    inheritable_options = ['database', 'indexes', 'order_by', 'primary_key']

    def __new__(cls, name, bases, attrs):
        if not bases:
            return super().__new__(cls, name, bases, attrs)

        meta_options = {}
        meta = attrs.pop('Meta', None)
        if meta:
            meta_options.update((k, v) for k, v in meta.__dict__.items() if not k.startswith('_'))

        # inherit any field descriptors by deep copying the underlying field obj
        # into the attrs of the new model, additionally see if the bases define
        # inheritable model options and swipe them
        for b in bases:
            print('b: %s' % b)
            if not hasattr(b, '_meta'):
                continue

            base_meta = getattr(b, '_meta')
            for (k, v) in base_meta.__dict__.items():
                if k in cls.inheritable_options and k not in meta_options:
                    meta_options[k] = v

            for (k, v) in b.__dict__.items():
                if isinstance(v, FieldDescriptor) and k not in attrs:
                    if not v.field.primary_key:
                        attrs[k] = deepcopy(v.field)

        # initialize the new class and set the magic attributes
        cls = super().__new__(cls, name, bases, attrs)
        cls._meta = ModelOptions(cls, **meta_options)
        cls._data = None
        if cls._meta.database is None:
            raise ImproperlyConfigured('database attribute does not appear to '
                                       'be set on the model: %s' % cls)
        primary_key = None

        # replace the fields with field descriptors, calling the add_to_class hook
        for name, attr in cls.__dict__.items():
            cls._meta.indexes = list(cls._meta.indexes)
            if isinstance(attr, Field):
                attr.add_to_class(cls, name)
                if attr.primary_key:
                    primary_key = attr

        if not primary_key:
            primary_key = PrimaryKeyField(primary_key=True)
            primary_key.add_to_class(cls, 'id')

        cls._meta.primary_key = primary_key
        cls._meta.auto_increment = isinstance(primary_key, PrimaryKeyField) or primary_key.sequence
        if not cls._meta.db_table:
            cls._meta.db_table = re.sub('[^\w]+', '_', cls.__name__.lower())

        # create a repr and error class before finalizing
        if hasattr(cls, '__unicode__'):
            setattr(cls, '__repr__', lambda self: '<%s: %r>' % (
                cls.__name__, self.__unicode__()))

        exception_class = type('%sDoesNotExist' % cls.__name__, (DoesNotExist,), {})
        cls.DoesNotExist = exception_class
        cls._meta.prepared()

        return cls


class Model(metaclass=ModelMetaclass):

    # # 如果子类没有实现__init__方法，会调用父类的__init__方法
    # # 所以这里的kw实际上是子类在实例化的时候传入的参数
    # # 比如定义一个User子类，对应数据库中的User表 User(id=123, name='Michael')
    # # 那么父类Model的 **kw 接收的参数为 {'id':123,'name':'Michael'}
    # def __init__(self, **kwargs):
    #     for k, v in kwargs.items():
    #         setattr(self, k, v)
    #
    # # 访问对象的key属性时，如果对象并没有这个相应的属性，那么将会调用__getattr__（）方法来处理
    # def __getattr__(self, key):  # 没有找到的属性，就在这里找
    #     try:
    #         return self[key]  # Model类也是一个dict，具有dict的功能
    #     except KeyError:
    #         raise AttributeError(r"'Model' object has no attribute '%s'" % key)
    #
    # # 当试图对对象的key赋值的时候将会被调用
    # def __setattr__(self, key, value):
    #     self[key] = value
    #
    # # 返回key对应的值，没找到则返回None
    # def getValue(self, key):
    #     return getattr(self, key, None)
    #
    # # 获取key对应的value，没找到则返回之前在字段中定义的默认值
    # def getValueOrDefault(self, key):
    #     value = getattr(self, key, None)
    #     if value is None:
    #         field = self.__mappings__[key]  # 这里之前保存的映射关系就用上了，value是Field类的某一个子类的实例
    #         if field.default is not None:
    #             value = field.default() if callable(field.default) else field.default
    #             print('using default value for %s: %s' % (key, str(value)))
    #             setattr(self, key, value)
    #     return value
    #
    # @classmethod
    # def drop_table(cls, fail_silently=False):
    #     """删除表格"""
    #     cls._meta.database.drop_table(cls, fail_silently)
    #
    # @classmethod
    # def table_exists(cls):
    #     return cls._meta.db_table in cls._meta.database.get_tables()
    #
    # # 创建表格
    # @classmethod
    # def create_table(cls, fail_silently=False):
    #     """ 创建表格    """
    #
    #     if fail_silently and cls.table_exists():
    #         return
    #
    #     db = cls._meta.database
    #     pk = cls._meta.primary_key
    #     if db.sequences and pk.sequence and not db.sequence_exists(pk.sequence):
    #         db.create_sequence(pk.sequence)
    #
    #     db.create_table(cls)
    #
    #     for field_name, field_obj in cls._meta.fields.items():
    #         if isinstance(field_obj, ForeignKeyField):
    #             db.create_foreign_key(cls, field_obj)
    #         elif field_obj.index or field_obj.unique:
    #             db.create_index(cls, [field_obj], field_obj.unique)
    #
    #     if cls._meta.indexes:
    #         for fields, unique in cls._meta.indexes:
    #             db.create_index(cls, fields, unique)
    #
    # # classmethod装饰器表示该类为类方法，无需创建实例即可调用，如Model.findAll()
    #
    # # 后面基本上就是实现关于数据库的方法，save, update, delete等。构造SQL语句，利用aiomysql实现异步执行操作。
    # # 因为篇幅以及涉及到异步io的知识，所以不再详细分析，知道大致原理，可以尝试自己去编写后面部分
    # @classmethod
    # def select(cls, *selection):
    #     query = SelectQuery(cls, *selection)
    #     if cls._meta.order_by:
    #         query = query.order_by(*cls._meta.order_by)
    #     return query
    #
    # @classmethod
    # def findAll(cls, where=None, args=None, **kw):
    #     ' find objects by where clause. '
    #     sql = [cls.__select__]
    #     if where:
    #         sql.append('where')
    #         sql.append(where)
    #     if args is None:
    #         args = []
    #     orderBy = kw.get('orderBy', None)
    #     if orderBy:
    #         sql.append('order by')
    #         sql.append(orderBy)
    #     limit = kw.get('limit', None)
    #     if limit is not None:
    #         sql.append('limit')
    #         if isinstance(limit, int):
    #             sql.append('?')
    #             args.append(limit)
    #         elif isinstance(limit, tuple) and len(limit) == 2:
    #             sql.append('?, ?')
    #             args.extend(limit)
    #         else:
    #             raise ValueError('Invalid limit value: %s' % str(limit))
    #     rs = select(' '.join(sql), args)  # 执行sql语句，该select()方法在代码最后实现，涉及异步的知识
    #     return [cls(**r) for r in rs]
    #
    # @classmethod
    # def findNumber(cls, selectField, where=None, args=None):
    #     sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
    #     if where:
    #         sql.append('where')
    #         sql.append(where)
    #     rs = select(' '.join(sql), args, 1)
    #     if len(rs) == 0:
    #         return None
    #     return rs[0]['_num_']
    #
    # @classmethod
    # def find(cls, pk):
    #     rs = select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
    #     if len(rs) == 0:
    #         return None
    #     return cls(**rs[0])
    #
    # def save(self):
    #     args = list(map(self.getValueOrDefault, self.__fields__))
    #     args.append(self.getValueOrDefault(self.__primary_key__))
    #     rows = execute(self.__insert__, args)  # 执行sql语句，该execute()方法在代码最后实现，涉及异步的知识
    #     if rows != 1:
    #         print('failed to insert record: affected rows: %s' % rows)
    #
    # def update(self):
    #     args = list(map(self.getValue, self.__fields__))
    #     args.append(self.getValue(self.__primary_key__))
    #     rows = execute(self.__update__, args)
    #     if rows != 1:
    #         print('failed to update by primary key: affected rows: %s' % rows)
    #
    # def remove(self):
    #     args = [self.getValue(self.__primary_key__)]
    #     rows = execute(self.__delete__, args)
    #     if rows != 1:
    #         print('failed to remove by primary key: affected rows: %s' % rows)
    #
    # @classmethod
    # def bind(cls, database):
    #     cls._meta.set_database(database)

    # SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
    # 注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。
    def __init__(self, **kwargs):
        self._data = self._meta.get_default_dict()
        self._obj_cache = {}  # cache of related objects

        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def select(cls, *selection):
        query = SelectQuery(cls, *selection)
        if cls._meta.order_by:
            query = query.order_by(*cls._meta.order_by)
        return query

    @classmethod
    def update(cls, **update):
        for f, v in update.items():
            print("f, v:", f, v)
            print("cls._meta.fields[f]:", cls._meta.fields[f])
        # fdict = dict((cls._meta.fields[f], v) for f, v in update.items())
        fdict = dict((f, v) for f, v in update.items())
        return UpdateQuery(cls, fdict)

    @classmethod
    def insert(cls, **insert):
        fdict = dict((cls._meta.fields[f], v) for f, v in insert.items())
        return InsertQuery(cls, fdict)

    @classmethod
    def delete(cls):
        return DeleteQuery(cls)

    @classmethod
    def raw(cls, sql, *params):
        return RawQuery(cls, sql, *params)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.save(force_insert=True)
        return inst

    @classmethod
    def get(cls, *query, **kwargs):
        sq = cls.select().naive()
        if query:
            sq = sq.where(*query)
        if kwargs:
            sq = sq.filter(**kwargs)
        return sq.get()

    @classmethod
    def get_or_create(cls, **kwargs):
        sq = cls.select().filter(**kwargs)
        try:
            return sq.get()
        except cls.DoesNotExist:
            return cls.create(**kwargs)

    @classmethod
    def filter(cls, *dq, **query):
        return cls.select().filter(*dq, **query)

    @classmethod
    def table_exists(cls):
        return cls._meta.db_table in cls._meta.database.get_tables()

    @classmethod
    def create_table(cls, fail_silently=False):
        if fail_silently and cls.table_exists():
            return

        db = cls._meta.database
        pk = cls._meta.primary_key
        if db.sequences and pk.sequence and not db.sequence_exists(pk.sequence):
            db.create_sequence(pk.sequence)

        db.create_table(cls)

        for field_name, field_obj in cls._meta.fields.items():
            if isinstance(field_obj, ForeignKeyField):
                db.create_foreign_key(cls, field_obj)
            elif field_obj.index or field_obj.unique:
                db.create_index(cls, [field_obj], field_obj.unique)

        if cls._meta.indexes:
            for fields, unique in cls._meta.indexes:
                db.create_index(cls, fields, unique)

    @classmethod
    def drop_table(cls, fail_silently=False):
        cls._meta.database.drop_table(cls, fail_silently)

    def get_id(self):
        return getattr(self, self._meta.primary_key.name)

    def set_id(self, id):
        setattr(self, self._meta.primary_key.name, id)

    def prepared(self):
        pass

    def save(self, force_insert=False):
        field_dict = dict(self._data)
        pk = self._meta.primary_key
        if self.get_id() is not None and not force_insert:
            field_dict.pop(pk.name)
            update = self.update(
                **field_dict
            ).where(pk == self.get_id())
            update.execute()
        else:
            if self._meta.auto_increment:
                field_dict.pop(pk.name, None)
            insert = self.insert(**field_dict)
            new_pk = insert.execute()
            if self._meta.auto_increment:
                self.set_id(new_pk)

    def dependencies(self, search_nullable=False):
        stack = [(type(self), self.select().where(self._meta.primary_key == self.get_id()))]
        seen = set()

        while stack:
            klass, query = stack.pop()
            if klass in seen:
                continue
            seen.add(klass)
            for rel_name, fk in klass._meta.reverse_rel.items():
                rel_model = fk.model_class
                expr = fk << query
                if not fk.null or search_nullable:
                    stack.append((rel_model, rel_model.select().where(expr)))
                yield (expr, fk)

    def delete_instance(self, recursive=False, delete_nullable=False):
        if recursive:
            for query, fk in reversed(list(self.dependencies(delete_nullable))):
                if fk.null and not delete_nullable:
                    fk.model_class.update(**{fk.name: None}).where(query).execute()
                else:
                    fk.model_class.delete().where(query).execute()
        return self.delete().where(self._meta.primary_key == self.get_id()).execute()

    def __eq__(self, other):
        return other.__class__ == self.__class__ and \
               self.get_id() is not None and \
               other.get_id() == self.get_id()

    def __ne__(self, other):
        return not self == other


# 测试
db = SqliteDatabase('test.db')


class User(Model):
    id = IntegerField(primary_key=True)
    name = CharField()

    class Meta:
        database = db


new_user = User(id='123456', name='LiMing')
# new_user = User()
# new_user.id = '123456'
# new_user.name='LiMing'
if __name__ == "__main__":
    # new_user.create_table()
    # new_user.insert( )
    # db.connect()
    # new_user.save()
    new_user.create(id='123456', name='LiMing')