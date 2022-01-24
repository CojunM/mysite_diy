#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:41
# @Author  : Cojun  Mao
# @Site    : 
# @File    : orm0.0.0.py
# @Project : mysite_diy
# @Software: PyCharm
import operator
import re
import sqlite3
import threading
from copy import deepcopy
from functools import reduce

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

DJANGO_MAP = {
    'eq': OP_EQ,
    'lt': OP_LT,
    'lte': OP_LTE,
    'gt': OP_GT,
    'gte': OP_GTE,
    'ne': OP_NE,
    'in': OP_IN,
    'is': OP_IS,
    'like': OP_LIKE,
    'ilike': OP_ILIKE,
}

JOIN_INNER = 1
JOIN_LEFT_OUTER = 2
JOIN_FULL = 3
basestring = bytes

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
        return '%s%s%s' % (self.quote_char, s, self.quote_char)

    def get_field(self, f):
        return self._field_map[f]

    def field_sql(self, field):
        attrs = field.attributes
        attrs['column_type'] = self.get_field(field.get_db_field())
        template = field.template

        if isinstance(field, ForeignKeyField):
            to_pk = field.rel_model._meta.primary_key
            if not isinstance(to_pk, PrimaryKeyField):
                template = to_pk.template
                attrs.update(to_pk.attributes)

        parts = [self.quote(field.db_column), template]
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
        for p in parts:
            print(p)
        return ' '.join(p % attrs for p in parts)

    def parse_create_table(self, model_class, safe=False):
        parts = ['CREATE TABLE']
        if safe:
            parts.append('IF NOT EXISTS')
        parts.append(self.quote(model_class._meta.db_table))
        columns = ', '.join(self.field_sql(f) for f in model_class._meta.get_fields())
        parts.append('(%s)' % columns)
        return parts

    def create_table(self, model_class, safe=False):
        return ' '.join(self.parse_create_table(model_class, safe))

    def parse_create_index(self, model_class, fields, unique):
        tbl_name = model_class._meta.db_table
        colnames = [f.db_column for f in fields]
        # 唯一索引（unique   index）的创建
        parts = ['CREATE %s' % ('UNIQUE INDEX' if unique else 'INDEX')]
        parts.append(self.quote('%s_%s' % (tbl_name, '_'.join(colnames))))
        parts.append('ON %s' % self.quote(tbl_name))
        parts.append('(%s)' % ', '.join(map(self.quote, colnames)))
        return parts

    def create_index(self, model_class, fields, unique):
        return ' '.join(self.parse_create_index(model_class, fields, unique))

    def create_sequence(self, sequence_name):
        return 'CREATE SEQUENCE %s;' % self.quote(sequence_name)


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
        # self.init(database, **connect_kwargs)
        self.database = database
        self.connect_kwargs = connect_kwargs

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


default_database = SqliteDatabase('pe.db')


class ModelOptions(object):
    def __init__(self, cls, database=None, db_table=None, indexes=None,
                 order_by=None, primary_key=None):
        self.model_class = cls
        self.name = cls.__name__.lower()
        self.fields = {}
        self.columns = {}
        self.defaults = {}

        self.database = database or default_database
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
        return sorted(self.fields.items(), key=lambda kv: (kv[1] is self.primary_key and 1 or 2, kv[1]._order))

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

    # 避免 'Field' TypeError: unhashable type:
    def __hash__(self):
        return hash(self.name + '.' + self.model_class.__name__)


class Field:
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


class TextField(Field):
    db_field = 'text'

    def coerce(self, value):
        return format_unicode(value or '')


class BigIntegerField(IntegerField):
    db_field = 'bigint'


class PrimaryKeyField(IntegerField):
    db_field = 'primary_key'

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(PrimaryKeyField, self).__init__(*args, **kwargs)


class ForeignKeyField(IntegerField):
    def __init__(self, rel_model, null=False, related_name=None, cascade=False, extra=None, *args, **kwargs):
        self.rel_model = rel_model
        self._related_name = related_name
        self.cascade = cascade
        self.extra = extra

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
        if not isinstance(to_pk, PrimaryKeyField):
            return to_pk.get_db_field()
        return super(ForeignKeyField, self).get_db_field()

    def coerce(self, value):
        return self.rel_model._meta.primary_key.coerce(value)

    def db_value(self, value):
        if isinstance(value, self.rel_model):
            value = value.get_id()
        return self.rel_model._meta.primary_key.db_value(value)


class DoesNotExist(Exception):
    pass


def returns_clone(func):
    """
    Method decorator that will "clone" the object before applying the given
    method.  This ensures that state is mutated in a more predictable fashion,
    and promotes the use of method-chaining.
    方法修饰符，它将在应用给定的方法。这确保了状态以更可预测的方式发生突变，
    推广方法链的使用。
    """

    def inner(self, *args, **kwargs):
        clone = self.clone()  # Assumes object implements `clone`.假定对象实现`clone`
        func(clone, *args, **kwargs)
        return clone

    inner.call_local = func  # Provide a way to call without cloning.提供一种无需克隆的呼叫方式
    return inner


class Query(object):
    require_commit = True  # 需要提交

    def __init__(self, model_class):
        self.model_class = model_class
        self.database = model_class._meta.database

        self._dirty = True
        self._query_ctx = model_class
        self._joins = {self.model_class: []}  # adjacency graph
        self._where = None

    def clone(self):
        # type(self)新样式类实例的类型为其类
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

    def where(self, *q_or_node):
        if self._where is None:
            # reduce()函数会对参数序列中元素进行累积。
            self._where = reduce(operator.and_, q_or_node)
            self._where = reduce(lambda x, y: x & y, q_or_node)
        else:
            for piece in q_or_node:
                # a &= b是a = a & b的简写
                self._where &= piece

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


def not_allowed(fn):
    def inner(self, *args, **kwargs):
        raise NotImplementedError('%s is not allowed on %s instances' % (
            fn, type(self).__name__,
        ))

    return inner


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


class ModelMetaclass(type):
    # 定义可以继承的属性
    inheritable_options = ['database', 'indexes', 'order_by', 'primary_key']

    def __new__(mcs, name, bases, attrs):
        # 假定用户创建的类是父类Model,不进行任何操作，因为需要修改的是用户自定义类
        if name == "Model":
            return super().__new__(mcs, name, bases, attrs)
        # Meta类的属性通过meta_options存储在类中
        meta_options = {}
        meta = attrs.pop('Meta', None)
        if meta:
            for k, v in meta.__dict__.items():
                # 将Meta从属性中移除，将Meta中的非私有属性加入meta_options中
                if not k.startswith('_'):
                    meta_options[k] = v
            # inherit any field descriptors by deep copying the underlying field obj
            # into the attrs of the new model, additionally see if the bases define
            # inheritable model options and swipe them
        for b in bases:
            if not hasattr(b, '_meta'):
                continue
            # 获取父类中Meta类的属性
            base_meta = getattr(b, '_meta')
            for (k, v) in base_meta.__dict__.items():
                if k in mcs.inheritable_options and k not in meta_options:
                    meta_options[k] = v
            # 获取父类中的Fields, 即表的字段
            for (k, v) in b.__dict__.items():
                if isinstance(v, FieldDescriptor) and k not in attrs:
                    if not v.field.primary_key:
                        attrs[k] = deepcopy(v.field)

        # initialize the new class and set the magic attributes
        cls = super().__new__(mcs, name, bases, attrs)
        cls._meta = ModelOptions(cls, **meta_options)
        cls._data = None

        primary_key = None

        # replace the fields with field descriptors, calling the add_to_class hook
        # 一个k, v 类似于 id : IntegerField('id')
        # 其中k是id，v是IntegerField的一个实例
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

    def __init__(self, **kwargs):
        self._data = self._meta.get_default_dict()
        self._obj_cache = {}  # cache of related objects

        for k, v in kwargs.items():
            setattr(self, k, v)

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
    def update(cls, **update):
        fdict = dict((cls._meta.fields[f], v) for f, v in update.items())
        return UpdateQuery(cls, fdict)

    @classmethod
    def insert(cls, **insert):
        fdict = dict((cls._meta.fields[f], v) for f, v in insert.items())
        return InsertQuery(cls, fdict)

    def get_id(self):
        return getattr(self, self._meta.primary_key.name)

    def set_id(self, id):
        setattr(self, self._meta.primary_key.name, id)

    def save(self, force_insert=False, only=None):
        field_dict = dict(self._data)
        pk = self._meta.primary_key
        # get_id()获取主键值
        if self.get_id() is not None and not force_insert:
            field_dict.pop(pk.name)
            update = self.update(**field_dict).where(pk == self.get_id())
            update.execute()
        else:
            if self._meta.auto_increment:  # 自增量存在，删除该字段
                field_dict.pop(pk.name, None)
            insert = self.insert(**field_dict)
            new_pk = insert.execute()
            if self._meta.auto_increment:
                self.set_id(new_pk)


# 测试


sqlite_db = SqliteDatabase('apptest.db')


class BaseModel(Model):
    """A base model that will use our Sqlite database."""

    class Meta:
        database = sqlite_db


class User(BaseModel):
    name = TextField()


new_user = User(name='LiMing1')
if __name__ == "__main__":
    # new_user.create_table()
    new_user.save()
    # new_user.s
