#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:49
# @Author  : Cojun  Mao
# @Site    : 
# @File    : orm0.0.1.py
# @Project : mysite_diy
# @Software: PyCharm
import operator
import re
import sqlite3
import threading
import warnings
from bisect import bisect_left, bisect_right
from copy import deepcopy


def __deprecated__(s):
    warnings.warn(s, DeprecationWarning)


class attrdict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        self[attr] = value

    def __iadd__(self, rhs):
        self.update(rhs);
        return self

    def __add__(self, rhs):
        d = attrdict(self);
        d.update(rhs);
        return d


SENTINEL = object()

#: Operations for use in SQL expressions.
OP = attrdict(
    AND='AND',
    OR='OR',
    ADD='+',
    SUB='-',
    MUL='*',
    DIV='/',
    BIN_AND='&',
    BIN_OR='|',
    XOR='#',
    MOD='%',
    EQ='=',
    LT='<',
    LTE='<=',
    GT='>',
    GTE='>=',
    NE='!=',
    IN='IN',
    NOT_IN='NOT IN',
    IS='IS',
    IS_NOT='IS NOT',
    LIKE='LIKE',
    ILIKE='ILIKE',
    BETWEEN='BETWEEN',
    REGEXP='REGEXP',
    IREGEXP='IREGEXP',
    CONCAT='||',
    BITWISE_NEGATION='~')


# To support "django-style" double-underscore filters, create a mapping between
# operation name and operation code, e.g. "__eq" == OP.EQ.
class Expression(object):
    pass


DJANGO_MAP = attrdict({
    'eq': operator.eq,
    'lt': operator.lt,
    'lte': operator.le,
    'gt': operator.gt,
    'gte': operator.ge,
    'ne': operator.ne,
    'in': operator.lshift,
    'is': lambda l, r: Expression(l, OP.IS, r),
    'like': lambda l, r: Expression(l, OP.LIKE, r),
    'ilike': lambda l, r: Expression(l, OP.ILIKE, r),
    'regexp': lambda l, r: Expression(l, OP.REGEXP, r),
})

#: Mapping of field type to the data-type supported by the database. Databases
#: may override or add to this list.
FIELD = attrdict(
    AUTO='INTEGER',
    BIGAUTO='BIGINT',
    BIGINT='BIGINT',
    BLOB='BLOB',
    BOOL='SMALLINT',
    CHAR='CHAR',
    DATE='DATE',
    DATETIME='DATETIME',
    DECIMAL='DECIMAL',
    DEFAULT='',
    DOUBLE='REAL',
    FLOAT='REAL',
    INT='INTEGER',
    SMALLINT='SMALLINT',
    TEXT='TEXT',
    TIME='TIME',
    UUID='TEXT',
    UUIDB='BLOB',
    VARCHAR='VARCHAR')

#: Join helpers (for convenience) -- all join types are supported, this object
#: is just to help avoid introducing errors by using strings everywhere.
JOIN = attrdict(
    INNER='INNER JOIN',
    LEFT_OUTER='LEFT OUTER JOIN',
    RIGHT_OUTER='RIGHT OUTER JOIN',
    FULL='FULL JOIN',
    FULL_OUTER='FULL OUTER JOIN',
    CROSS='CROSS JOIN',
    NATURAL='NATURAL JOIN',
    LATERAL='LATERAL',
    LEFT_LATERAL='LEFT JOIN LATERAL')

# Row representations.
ROW = attrdict(
    TUPLE=1,
    DICT=2,
    NAMED_TUPLE=3,
    CONSTRUCTOR=4,
    MODEL=5)

SCOPE_NORMAL = 1
SCOPE_SOURCE = 2
SCOPE_VALUES = 4
SCOPE_CTE = 8
SCOPE_COLUMN = 16

# Rules for parentheses around subqueries in compound select.
CSQ_PARENTHESES_NEVER = 0
CSQ_PARENTHESES_ALWAYS = 1
CSQ_PARENTHESES_UNNESTED = 2

# Regular expressions used to convert class names to snake-case table names.
# First regex handles acronym followed by word or initial lower-word followed
# by a capitalized word. e.g. APIResponse -> API_Response / fooBar -> foo_Bar.
# Second regex handles the normal case of two title-cased words.
SNAKE_CASE_STEP1 = re.compile('(.)_*([A-Z][a-z]+)')
SNAKE_CASE_STEP2 = re.compile('([a-z0-9])_*([A-Z])')

basestring = str


class SQL():
    """一个无范围的SQL字符串，带有可选参数"""
    _node_type = 'sql'

    def __init__(self, value, *params):
        self.value = value
        self.params = params
        # super(SQL, self).__init__()

    def clone_base(self):
        return SQL(self.value, *self.params)


R = SQL  # backwards-compat.


#
#
# class Entity():
#     """A quoted-name or entity, e.g. "table"."column"
#     引用的名称或实体，如“表”、“列”."""
#     _node_type = 'entity'
#
#     def __init__(self, *path):
#         # super(Entity, self).__init__()
#         self.path = path
#
#     def clone_base(self):
#         return Entity(*self.path)
#
#     def __getattr__(self, attr):
#         return Entity(*filter(None, self.path + (attr,)))
#

class FieldDescriptor(object):
    # Fields are exposed as descriptors in order to control access to the
    # underlying "raw" data.
    def __init__(self, field):
        self.field = field
        self.att_name = self.field.name

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return instance._data.get(self.att_name)
        return self.field

    def __set__(self, instance, value):
        instance._data[self.att_name] = value
        instance._dirty.add(self.att_name)


class Entity(object):
    """A quoted-name or entity, e.g. "table"."column".
    引用的名称或实体，如“表”、“列”"""
    _node_type = 'entity'

    def __init__(self, *path):
        # super(Entity, self).__init__()
        self.path = path

    def clone_base(self):
        return Entity(*self.path)

    def __getattr__(self, attr):
        return Entity(*filter(None, self.path + (attr,)))


class Field():
    """A column on a table."""
    _field_counter = 0  # 计数器
    _order = 0
    _node_type = 'field'
    db_field = 'unknown'

    def __init__(self, null=False, index=False, unique=False,
                 verbose_name=None, help_text=None, db_column=None,
                 default=None, choices=None, primary_key=False, sequence=None,
                 constraints=None, schema=None, undeclared=False):
        self.null = null
        self.index = index
        self.unique = unique
        self.verbose_name = verbose_name
        self.help_text = help_text
        self.db_column = db_column
        self.default = default
        self.choices = choices  # Used for metadata purposes, not enforced.
        self.primary_key = primary_key
        self.sequence = sequence  # Name of sequence, e.g. foo_id_seq.
        self.constraints = constraints  # List of column constraints.
        self.schema = schema  # Name of schema, e.g. 'public'.
        self.undeclared = undeclared  # Whether this field is part of schema.

        # Used internally for recovering the order in which Fields were defined
        # on the Model class.
        Field._field_counter += 1
        self._order = Field._field_counter
        self._sort_key = (self.primary_key and 1 or 2), self._order

        self._is_bound = False  # Whether the Field is "bound" to a Model.
        super(Field, self).__init__()

    def clone_base(self, **kwargs):
        inst = type(self)(
            null=self.null,
            index=self.index,
            unique=self.unique,
            verbose_name=self.verbose_name,
            help_text=self.help_text,
            db_column=self.db_column,
            default=self.default,
            choices=self.choices,
            primary_key=self.primary_key,
            sequence=self.sequence,
            constraints=self.constraints,
            schema=self.schema,
            undeclared=self.undeclared,
            **kwargs)
        if self._is_bound:
            inst.name = self.name
            inst.model_class = self.model_class
        inst._is_bound = self._is_bound
        return inst

    def add_to_class(self, model_class, name):
        """
        Hook that replaces the `Field` attribute on a class with a named
        `FieldDescriptor`. Called by the metaclass during construction of the
        `Model`.
        """
        self.name = name
        self.model_class = model_class
        self.db_column = self.db_column or self.name
        if not self.verbose_name:
            self.verbose_name = re.sub('_+', ' ', name).title()

        model_class._meta.add_field(self)
        setattr(model_class, name, FieldDescriptor(self))
        self._is_bound = True

    def get_database(self):
        return self.model_class._meta.database

    @property
    def column(self):
        return self.db_column

    def get_column_type(self):
        field_type = self.get_db_field()
        return self.get_database().compiler().get_column_type(field_type)

    def get_db_field(self):
        return self.db_field

    def get_modifiers(self):
        return None

    def coerce(self, value):
        return value

    def db_value(self, value):
        """Convert the python value for storage in the database."""
        return value if value is None else self.coerce(value)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        return value if value is None else self.coerce(value)

    def as_entity(self, with_table=False):
        if with_table:
            return Entity(self.model_class._meta.db_table, self.db_column)
        return Entity(self.db_column)

    def __ddl_column__(self, column_type):
        """Return the column type, e.g. VARCHAR(255) or REAL."""
        modifiers = self.get_modifiers()  # 修饰语
        if modifiers:
            return '%s(%s)' % (column_type, ', '.join(map(str, modifiers)))
        return column_type

    def __ddl__(self, column_type):
        """Return a list of Node instances that defines the column."""
        ddl = [self.column, self.__ddl_column__(column_type)]
        if not self.null:
            ddl.append('NOT NULL')
        if self.primary_key:
            ddl.append('PRIMARY KEY')
        if self.sequence:
            ddl.append("DEFAULT NEXTVAL('%s')" % self.sequence)
        if self.constraints:
            ddl.extend(self.constraints)
        return ddl

    def __hash__(self):
        return hash(self.name + '.' + self.model_class.__name__)


class _StringField(Field):
    def coerce(self, value):
        return coerce_to_unicode(value or '')

    def __add__(self, other):
        return self.concat(other)

    def __radd__(self, other):
        return other.concat(self)


class CharField(_StringField):
    db_field = 'string'

    def __init__(self, max_length=255, *args, **kwargs):
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def clone_base(self, **kwargs):
        return super(CharField, self).clone_base(
            max_length=self.max_length,
            **kwargs)

    def get_modifiers(self):
        return self.max_length and [self.max_length] or None


class FixedCharField(CharField):
    db_field = 'fixed_char'

    def python_value(self, value):
        value = super(FixedCharField, self).python_value(value)
        if value:
            value = value.strip()
        return value


class TextField(_StringField):
    db_field = 'text'


class IntegerField(Field):
    db_field = 'int'
    coerce = int


class PrimaryKeyField(IntegerField):
    db_field = 'primary_key'

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(PrimaryKeyField, self).__init__(*args, **kwargs)


class ForeignKeyField(IntegerField):
    def __init__(self, rel_model, related_name=None, on_delete=None,
                 on_update=None, extra=None, to_field=None,
                 object_id_name=None, *args, **kwargs):
        # if rel_model != 'self' and not \
        #         isinstance(rel_model, (Proxy, DeferredRelation)) and not \
        #         issubclass(rel_model, Model):
        #     raise TypeError('Unexpected value for `rel_model`.  Expected '
        #                     '`Model`, `Proxy`, `DeferredRelation`, or "self"')
        self.rel_model = rel_model
        self._related_name = related_name
        # self.deferred = isinstance(rel_model, (Proxy, DeferredRelation))
        self.on_delete = on_delete
        self.on_update = on_update
        self.extra = extra
        self.to_field = to_field
        self.object_id_name = object_id_name
        super(ForeignKeyField, self).__init__(*args, **kwargs)

    def clone_base(self, **kwargs):
        return super(ForeignKeyField, self).clone_base(
            rel_model=self.rel_model,
            related_name=self._get_related_name(),
            on_delete=self.on_delete,
            on_update=self.on_update,
            extra=self.extra,
            to_field=self.to_field,
            object_id_name=self.object_id_name,
            **kwargs)

    def _get_descriptor(self):
        return RelationDescriptor(self, self.rel_model)

    def _get_id_descriptor(self):
        return ObjectIdDescriptor(self)

    def _get_backref_descriptor(self):
        return ReverseRelationDescriptor(self)

    def _get_related_name(self):
        if self._related_name and callable(self._related_name):
            return self._related_name(self)
        return self._related_name or ('%s_set' % self.model_class._meta.name)

    def add_to_class(self, model_class, name):
        # self.name = name
        # self.model_class = model_class
        # self.db_column = self.db_column or '%s_id' % self.name
        # self.verbose_name = self.verbose_name or re.sub('_+', ' ', name).title()
        #
        # model_class._meta.fields[self.name] = self
        # model_class._meta.columns[self.db_column] = self
        #
        # self.related_name = self._related_name or '%s_set' % (model_class._meta.name)
        #
        # if self.rel_model == 'self':
        #     self.rel_model = self.model_class
        # if self.related_name in self.rel_model._meta.fields:
        #     raise AttributeError('Foreign key: %s.%s related name "%s" collision with field of same name' % (
        #         self.model_class._meta.name, self.name, self.related_name))
        #
        # setattr(model_class, name, RelationDescriptor(self, self.rel_model))
        # setattr(self.rel_model, self.related_name, ReverseRelationDescriptor(self))
        #
        # model_class._meta.rel[self.name] = self
        # self.rel_model._meta.reverse_rel[self.related_name] = self
        # if isinstance(self.rel_model, Proxy):
        #     def callback(rel_model):
        #         self.rel_model = rel_model
        #         self.add_to_class(model_class, name)
        #
        #     self.rel_model.attach_callback(callback)
        #     return
        # elif isinstance(self.rel_model, DeferredRelation):
        #     self.rel_model.set_field(model_class, self, name)
        #     return

        self.name = name
        self.model_class = model_class
        self.db_column = self.db_column or '%s_id' % self.name
        obj_id_name = self.object_id_name

        if not obj_id_name:
            obj_id_name = self.db_column
            if obj_id_name == self.name:
                obj_id_name += '_id'
        elif obj_id_name == self.name:
            raise ValueError('Cannot set a foreign key object_id_name to '
                             'the same name as the field itself.')

        if not self.verbose_name:
            self.verbose_name = re.sub('_+', ' ', name).title()

        model_class._meta.add_field(self)

        self.related_name = self._get_related_name()
        if self.rel_model == 'self':
            self.rel_model = self.model_class

        if self.to_field is not None:
            if not isinstance(self.to_field, Field):
                self.to_field = getattr(self.rel_model, self.to_field)
        else:
            self.to_field = self.rel_model._meta.primary_key

        # TODO: factor into separate method.
        if model_class._meta.validate_backrefs:
            def invalid(msg, **context):
                context.update(
                    field='%s.%s' % (model_class._meta.name, name),
                    backref=self.related_name,
                    obj_id_name=obj_id_name)
                raise AttributeError(msg % context)

            if self.related_name in self.rel_model._meta.fields:
                invalid('The related_name of %(field)s ("%(backref)s") '
                        'conflicts with a field of the same name.')
            elif self.related_name in self.rel_model._meta.reverse_rel:
                invalid('The related_name of %(field)s ("%(backref)s") '
                        'is already in use by another foreign key.')

            if obj_id_name in model_class._meta.fields:
                invalid('The object id descriptor of %(field)s conflicts '
                        'with a field named %(obj_id_name)s')
            elif obj_id_name in model_class.__dict__:
                invalid('Model attribute "%(obj_id_name)s" would be shadowed '
                        'by the object id descriptor of %(field)s.')

        setattr(model_class, name, self._get_descriptor())
        setattr(model_class, obj_id_name, self._get_id_descriptor())
        setattr(self.rel_model,
                self.related_name,
                self._get_backref_descriptor())
        self._is_bound = True

        model_class._meta.rel[self.name] = self
        self.rel_model._meta.reverse_rel[self.related_name] = self

    def get_db_field(self):
        """
       重写以确保外键使用与主键相同的列类型他们指出的关键。
        """
        if not isinstance(self.to_field, PrimaryKeyField):
            return self.to_field.get_db_field()
        return super(ForeignKeyField, self).get_db_field()

    def get_modifiers(self):
        if not isinstance(self.to_field, PrimaryKeyField):
            return self.to_field.get_modifiers()
        return super(ForeignKeyField, self).get_modifiers()

    def coerce(self, value):
        return self.to_field.coerce(value)

    def db_value(self, value):
        if isinstance(value, self.rel_model):
            value = value._get_pk_value()
        return self.to_field.db_value(value)

    def python_value(self, value):
        if isinstance(value, self.rel_model):
            return value
        return self.to_field.python_value(value)


class CompositeKey(object):
    """由多列组成的主键。与其他字段不同，
    复合键是在模型的 Meta 定义字段后初始化。
    它将用作主键的字段的字符串名称作为参数"""
    pass


class DoesNotExist(object):
    pass


class DeferredRelation(object):
    _unresolved = set()

    def __init__(self, rel_model_name=None):
        self.fields = []
        if rel_model_name is not None:
            self._rel_model_name = rel_model_name.lower()
            self._unresolved.add(self)

    def set_field(self, model_class, field, name):
        self.fields.append((model_class, field, name))

    def set_model(self, rel_model):
        for model, field, name in self.fields:
            field.rel_model = rel_model
            field.add_to_class(model, name)

    @staticmethod
    def resolve(model_cls):
        unresolved = list(DeferredRelation._unresolved)
        for dr in unresolved:
            if dr._rel_model_name == model_cls.__name__.lower():
                dr.set_model(model_cls)
                DeferredRelation._unresolved.discard(dr)


class DeferredForeignKey(object):
    """表示延迟的外键的字段类。用于循环外键引用"""
    _unresolved = set()

    def __init__(self, rel_model_name=None):
        self.fields = []
        if rel_model_name is not None:
            self._rel_model_name = rel_model_name.lower()
            self._unresolved.add(self)

    def set_field(self, model_class, field, name):
        self.fields.append((model_class, field, name))

    def set_model(self, rel_model):
        for model, field, name in self.fields:
            field.rel_model = rel_model
            field.add_to_class(model, name)

    @staticmethod
    def resolve(model_cls):
        unresolved = list(DeferredRelation._unresolved)
        for dr in unresolved:
            if dr._rel_model_name == model_cls.__name__.lower():
                dr.set_model(model_cls)
                DeferredRelation._unresolved.discard(dr)


class _BaseConnectionLocal(object):
    def __init__(self, **kwargs):
        super(_BaseConnectionLocal, self).__init__(**kwargs)
        self.autocommit = None
        self.closed = True
        self.conn = None
        self.context_stack = []
        self.transactions = []


class _ConnectionState(object):
    def __init__(self, **kwargs):
        super(_ConnectionState, self).__init__(**kwargs)
        self.reset()

    def reset(self):
        self.closed = True
        self.conn = None
        self.ctx = []
        self.transactions = []

    def set_connection(self, conn):
        self.conn = conn
        self.closed = False
        self.ctx = []
        self.transactions = []


class _ConnectionLocal(_BaseConnectionLocal, threading.local): pass


class _NoopLock(object):
    __slots__ = ()
    """__enter__():在使用with语句时调用，会话管理器在代码块开始前调用，返回值与as后的参数绑定
    __exit__():会话管理器在代码块执行完成好后调用，在with语句完成时，对象销毁之前调用"""

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb): pass


def merge_dict(source, overrides):
    merged = source.copy()
    if overrides:
        merged.update(overrides)
    return merged


class ConnectionContext:
    __slots__ = ('db',)

    def __init__(self, db): self.db = db

    def __enter__(self):
        if self.db.is_closed():
            self.db.connect()

    def __exit__(self, exc_type, exc_val, exc_tb): self.db.close()


# Exception
class PeeweeException(Exception): pass


class ImproperlyConfigured(PeeweeException): pass


class DatabaseError(PeeweeException): pass


class DataError(DatabaseError): pass


class IntegrityError(DatabaseError): pass


class InterfaceError(PeeweeException): pass


class InternalError(DatabaseError): pass


class NotSupportedError(DatabaseError): pass


class OperationalError(DatabaseError): pass


class ProgrammingError(DatabaseError): pass


class Clause():
    """A SQL clause, one or more Node objects joined by spaces.
    一个SQL子句，一个或多个由空格连接的节点对象"""
    _node_type = 'clause'

    glue = ' '
    parens = False

    def __init__(self, *nodes, **kwargs):
        if 'glue' in kwargs:
            self.glue = kwargs['glue']
        if 'parens' in kwargs:
            self.parens = kwargs['parens']
        # super(Clause, self).__init__()
        self.nodes = list(nodes)

    def clone_base(self):
        clone = Clause(*self.nodes)
        clone.glue = self.glue
        clone.parens = self.parens
        return clone


class CommaClause(Clause):
    """One or more Node objects joined by commas, no parens.
    一个或多个节点对象由逗号连接，无paren。"""
    glue = ', '


class EnclosedClause(CommaClause):
    """One or more Node objects joined by commas and enclosed in parens.
    一个或多个节点对象，用逗号连接并用括号括起来。"""
    parens = True


class AliasMap(object):
    prefix = 't'

    def __init__(self, start=0):
        self._alias_map = {}
        self._counter = start

    def __repr__(self):
        return '<AliasMap: %s>' % self._alias_map

    def add(self, obj, alias=None):
        if obj in self._alias_map:
            return
        self._counter += 1
        self._alias_map[obj] = alias or '%s%s' % (self.prefix, self._counter)

    def __getitem__(self, obj):
        if obj not in self._alias_map:
            self.add(obj)
        return self._alias_map[obj]

    def __contains__(self, obj):
        return obj in self._alias_map

    def update(self, alias_map):
        if alias_map:
            for obj, alias in alias_map._alias_map.items():
                if obj not in self:
                    self._alias_map[obj] = alias
        return self


class QueryCompiler(object):
    # Mapping of `db_type` to actual column type used by database driver.
    # Database classes may provide additional column types or overrides.
    field_map = {
        'bare': '',
        'bigint': 'BIGINT',
        'blob': 'BLOB',
        'bool': 'SMALLINT',
        'date': 'DATE',
        'datetime': 'DATETIME',
        'decimal': 'DECIMAL',
        'double': 'REAL',
        'fixed_char': 'CHAR',
        'float': 'REAL',
        'int': 'INTEGER',
        'primary_key': 'INTEGER',
        'smallint': 'SMALLINT',
        'string': 'VARCHAR',
        'text': 'TEXT',
        'time': 'TIME',
    }

    # Mapping of OP. to actual SQL operation.  For most databases this will be
    # the same, but some column types or databases may support additional ops.
    # Like `field_map`, Database classes may extend or override these.
    op_map = {
        OP.EQ: '=',
        OP.LT: '<',
        OP.LTE: '<=',
        OP.GT: '>',
        OP.GTE: '>=',
        OP.NE: '!=',
        OP.IN: 'IN',
        OP.NOT_IN: 'NOT IN',
        OP.IS: 'IS',
        OP.IS_NOT: 'IS NOT',
        OP.BIN_AND: '&',
        OP.BIN_OR: '|',
        OP.LIKE: 'LIKE',
        OP.ILIKE: 'ILIKE',
        OP.BETWEEN: 'BETWEEN',
        OP.ADD: '+',
        OP.SUB: '-',
        OP.MUL: '*',
        OP.DIV: '/',
        OP.XOR: '#',
        OP.AND: 'AND',
        OP.OR: 'OR',
        OP.MOD: '%',
        OP.REGEXP: 'REGEXP',
        OP.CONCAT: '||',
    }

    join_map = {
        JOIN.INNER: 'INNER JOIN',
        JOIN.LEFT_OUTER: 'LEFT OUTER JOIN',
        JOIN.RIGHT_OUTER: 'RIGHT OUTER JOIN',
        JOIN.FULL: 'FULL JOIN',
        JOIN.CROSS: 'CROSS JOIN',
    }
    alias_map_class = AliasMap

    def __init__(self, quote_char='"', interpolation='?', field_overrides=None,
                 op_overrides=None):
        self.quote_char = quote_char
        self.interpolation = interpolation
        self._field_map = merge_dict(self.field_map, field_overrides or {})
        self._op_map = merge_dict(self.op_map, op_overrides or {})
        # self._parse_map = self.get_parse_map()
        self._unknown_types = set(['param'])

    def _sql_splicer(self, node, params=None, glue=', '):
        sql = []
        params = []
        unknown = False
        if:
        elif isinstance(node, (list, tuple, set)):
            # If you're wondering how to pass a list into your query, simply
            # wrap it in Param().
            sql.append(glue.join(node))
            params.extend(node_params)
            sql = '(%s)' % sql
    def get_parse_map(self):
        # To avoid O(n) lookups when parsing nodes, use a lookup table for
        # common node types O(1).
        return {
            'expression': self._parse_expression,
            'param': self._parse_param,
            'passthrough': self._parse_passthrough,
            'func': self._parse_func,
            'clause': self._parse_clause,
            'entity': self._parse_entity,
            'field': self._parse_field,
            'sql': self._parse_sql,
            'select_query': self._parse_select_query,
            'compound_select_query': self._parse_compound_select_query,
            'strip_parens': self._parse_strip_parens,
            'composite_key': self._parse_composite_key,
        }

    def quote(self, s):
        return '%s%s%s' % (self.quote_char, s, self.quote_char)

    def get_column_type(self, f):
        return self._field_map[f] if f in self._field_map else f.upper()

    # def get_op(self, q):
    #     return self._op_map[q]
    #
    # def _sorted_fields(self, field_dict):
    #     return sorted(field_dict.items(), key=lambda i: i[0]._sort_key)
    #
    # def _parse_default(self, node, alias_map, conv):
    #     return self.interpolation, [node]
    #
    # def _parse_expression(self, node, alias_map, conv):
    #     if isinstance(node.lhs, Field):
    #         conv = node.lhs
    #     lhs, lparams = self.parse_node(node.lhs, alias_map, conv)
    #     rhs, rparams = self.parse_node(node.rhs, alias_map, conv)
    #     if node.op == OP.IN and rhs == '()' and not rparams:
    #         return ('0 = 1' if node.flat else '(0 = 1)'), []
    #     template = '%s %s %s' if node.flat else '(%s %s %s)'
    #     sql = template % (lhs, self.get_op(node.op), rhs)
    #     return sql, lparams + rparams
    #
    # def _parse_passthrough(self, node, alias_map, conv):
    #     if node.adapt:
    #         return self.parse_node(node.adapt(node.value), alias_map, None)
    #     return self.interpolation, [node.value]
    #
    # def _parse_param(self, node, alias_map, conv):
    #     if node.adapt:
    #         if conv and conv.db_value is node.adapt:
    #             conv = None
    #         return self.parse_node(node.adapt(node.value), alias_map, conv)
    #     elif conv is not None:
    #         return self.parse_node(conv.db_value(node.value), alias_map)
    #     else:
    #         return self.interpolation, [node.value]
    #
    # def _parse_func(self, node, alias_map, conv):
    #     conv = node._coerce and conv or None
    #     sql, params = self.parse_node_list(node.arguments, alias_map, conv)
    #     return '%s(%s)' % (node.name, strip_parens(sql)), params
    #
    def _parse_clause(self, node, alias_map, conv):
        sql, params = self.parse_node_list(
            node.nodes, alias_map, conv, node.glue)
        if node.parens:
            sql = '(%s)' % strip_parens(sql)
        return sql, params

    #
    # def _parse_entity(self, node, alias_map, conv):
    #     return '.'.join(map(self.quote, node.path)), []
    #
    def _parse_sql(self, sql, params):
        return sql, list(params)

    # def _parse_field(self, node, alias_map, conv):
    #     if alias_map:
    #         sql = '.'.join((
    #             self.quote(alias_map[node.model_class]),
    #             self.quote(node.db_column)))
    #     else:
    #         sql = self.quote(node.db_column)
    #     return sql, []
    #
    # def _parse_composite_key(self, node, alias_map, conv):
    #     fields = []
    #     for field_name in node.field_names:
    #         fields.append(node.model_class._meta.fields[field_name])
    #     return self._parse_clause(CommaClause(*fields), alias_map, conv)
    #
    # def _parse_compound_select_query(self, node, alias_map, conv):
    #     csq = 'compound_select_query'
    #     lhs, rhs = node.lhs, node.rhs
    #     inv = rhs._node_type == csq and lhs._node_type != csq
    #     if inv:
    #         lhs, rhs = rhs, lhs
    #
    #     new_map = self.alias_map_class()
    #     if lhs._node_type == csq:
    #         new_map._counter = alias_map._counter
    #
    #     sql1, p1 = self.generate_select(lhs, new_map)
    #     sql2, p2 = self.generate_select(rhs, self.calculate_alias_map(rhs,
    #                                                                   new_map))
    #
    #     # We add outer parentheses in the event the compound query is used in
    #     # the `from_()` clause, in which case we'll need them.
    #     if node.database.compound_select_parentheses:
    #         if lhs._node_type != csq:
    #             sql1 = '(%s)' % sql1
    #         if rhs._node_type != csq:
    #             sql2 = '(%s)' % sql2
    #
    #     if inv:
    #         sql1, p1, sql2, p2 = sql2, p2, sql1, p1
    #
    #     return '(%s %s %s)' % (sql1, node.operator, sql2), (p1 + p2)
    #
    # def _parse_select_query(self, node, alias_map, conv):
    #     clone = node.clone()
    #     if not node._explicit_selection:
    #         if conv and isinstance(conv, ForeignKeyField):
    #             clone._select = (conv.to_field,)
    #         else:
    #             clone._select = clone.model_class._meta.get_primary_key_fields()
    #     sub, params = self.generate_select(clone, alias_map)
    #     return '(%s)' % strip_parens(sub), params
    #
    # def _parse_strip_parens(self, node, alias_map, conv):
    #     sql, params = self.parse_node(node.node, alias_map, conv)
    #     return strip_parens(sql), params
    #
    # def _parse(self, node, alias_map, conv):
    #     # By default treat the incoming node as a raw value that should be
    #     # parameterized.
    #     node_type = getattr(node, '_node_type', None)
    #     unknown = False
    #     if node_type in self._parse_map:
    #         sql, params = self._parse_map[node_type](node, alias_map, conv)
    #         unknown = (node_type in self._unknown_types and
    #                    node.adapt is None and
    #                    conv is None)
    #     elif isinstance(node, (list, tuple, set)):
    #         # If you're wondering how to pass a list into your query, simply
    #         # wrap it in Param().
    #         sql, params = self.parse_node_list(node, alias_map, conv)
    #         sql = '(%s)' % sql
    #     elif isinstance(node, Model):
    #         sql = self.interpolation
    #         if conv and isinstance(conv, ForeignKeyField):
    #             to_field = conv.to_field
    #             if isinstance(to_field, ForeignKeyField):
    #                 value = conv.db_value(node)
    #             else:
    #                 value = to_field.db_value(getattr(node, to_field.name))
    #         else:
    #             value = node._get_pk_value()
    #         params = [value]
    #     elif (isclass(node) and issubclass(node, Model)) or \
    #             isinstance(node, ModelAlias):
    #         entity = node.as_entity().alias(alias_map[node])
    #         sql, params = self.parse_node(entity, alias_map, conv)
    #     elif conv is not None:
    #         value = conv.db_value(node)
    #         sql, params, _ = self._parse(value, alias_map, None)
    #     else:
    #         sql, params = self._parse_default(node, alias_map, None)
    #         unknown = True
    #
    #     return sql, params, unknown
    #
    # def parse_node(self, node, alias_map=None, conv=None):
    #     sql, params, unknown = self._parse(node, alias_map, conv)
    #     if unknown and (conv is not None) and params:
    #         params = [conv.db_value(i) for i in params]
    #
    #     if isinstance(node, Node):
    #         if node._negated:
    #             sql = 'NOT %s' % sql
    #         if node._alias:
    #             sql = ' '.join((sql, 'AS', node._alias))
    #         if node._ordering:
    #             sql = ' '.join((sql, node._ordering))
    #
    #     if params and any(isinstance(p, Node) for p in params):
    #         clean_params = []
    #         clean_sql = []
    #         for idx, param in enumerate(params):
    #             if isinstance(param, Node):
    #                 csql, cparams = self.parse_node(param)
    #
    #     return sql, params
    #
    def parse_node_list(self, nodes, glue=', '):
        sql = []
        params = []
        for node in nodes:
            node_sql, node_params = self.parse_node(node, alias_map, conv)
            sql.append(node_sql)
            params.extend(node_params)
        return glue.join(sql), params

    #
    # def calculate_alias_map(self, query, alias_map=None):
    #     new_map = self.alias_map_class()
    #     if alias_map is not None:
    #         new_map._counter = alias_map._counter
    #
    #     new_map.add(query.model_class, query.model_class._meta.table_alias)
    #     for src_model, joined_models in query._joins.items():
    #         new_map.add(src_model, src_model._meta.table_alias)
    #         for join_obj in joined_models:
    #             if isinstance(join_obj.dest, Node):
    #                 new_map.add(join_obj.dest, join_obj.dest.alias)
    #             else:
    #                 new_map.add(join_obj.dest, join_obj.dest._meta.table_alias)
    #
    #     return new_map.update(alias_map)
    #
    # def build_query(self, clauses, alias_map=None):
    #     return self.parse_node(Clause(*clauses), alias_map)
    #
    # def generate_joins(self, joins, model_class, alias_map):
    #     # Joins are implemented as an adjancency-list graph. Perform a
    #     # depth-first search of the graph to generate all the necessary JOINs.
    #     clauses = []
    #     seen = set()
    #     q = [model_class]
    #     while q:
    #         curr = q.pop()
    #         if curr not in joins or curr in seen:
    #             continue
    #         seen.add(curr)
    #         for join in joins[curr]:
    #             src = curr
    #             dest = join.dest
    #             join_type = join.get_join_type()
    #             if isinstance(join.on, (Expression, Func, Clause, Entity)):
    #                 # Clear any alias on the join expression.
    #                 constraint = join.on.clone().alias()
    #             elif join_type != JOIN.CROSS:
    #                 metadata = join.metadata
    #                 if metadata.is_backref:
    #                     fk_model = join.dest
    #                     pk_model = join.src
    #                 else:
    #                     fk_model = join.src
    #                     pk_model = join.dest
    #
    #                 fk = metadata.foreign_key
    #                 if fk:
    #                     lhs = getattr(fk_model, fk.name)
    #                     rhs = getattr(pk_model, fk.to_field.name)
    #                     if metadata.is_backref:
    #                         lhs, rhs = rhs, lhs
    #                     constraint = (lhs == rhs)
    #                 else:
    #                     raise ValueError('Missing required join predicate.')
    #
    #             if isinstance(dest, Node):
    #                 # TODO: ensure alias?
    #                 dest_n = dest
    #             else:
    #                 q.append(dest)
    #                 dest_n = dest.as_entity().alias(alias_map[dest])
    #
    #             join_sql = SQL(self.join_map.get(join_type) or join_type)
    #             if join_type == JOIN.CROSS:
    #                 clauses.append(Clause(join_sql, dest_n))
    #             else:
    #                 clauses.append(Clause(join_sql, dest_n, SQL('ON'),
    #                                       constraint))
    #
    #     return clauses
    #
    # def generate_select(self, query, alias_map=None):
    #     model = query.model_class
    #     db = model._meta.database
    #
    #     alias_map = self.calculate_alias_map(query, alias_map)
    #
    #     if isinstance(query, CompoundSelect):
    #         clauses = [_StripParens(query)]
    #     else:
    #         if not query._distinct:
    #             clauses = [SQL('SELECT')]
    #         else:
    #             clauses = [SQL('SELECT DISTINCT')]
    #             if query._distinct not in (True, False):
    #                 clauses += [SQL('ON'), EnclosedClause(*query._distinct)]
    #
    #         select_clause = Clause(*query._select)
    #         select_clause.glue = ', '
    #
    #         clauses.extend((select_clause, SQL('FROM')))
    #         if query._from is None:
    #             clauses.append(model.as_entity().alias(alias_map[model]))
    #         else:
    #             clauses.append(CommaClause(*query._from))
    #
    #     join_clauses = self.generate_joins(query._joins, model, alias_map)
    #     if join_clauses:
    #         clauses.extend(join_clauses)
    #
    #     if query._where is not None:
    #         clauses.extend([SQL('WHERE'), query._where])
    #
    #     if query._group_by:
    #         clauses.extend([SQL('GROUP BY'), CommaClause(*query._group_by)])
    #
    #     if query._having:
    #         clauses.extend([SQL('HAVING'), query._having])
    #
    #     if query._windows is not None:
    #         clauses.append(SQL('WINDOW'))
    #         clauses.append(CommaClause(*[
    #             Clause(
    #                 SQL(window._alias),
    #                 SQL('AS'),
    #                 window.__sql__())
    #             for window in query._windows]))
    #
    #     if query._order_by:
    #         clauses.extend([SQL('ORDER BY'), CommaClause(*query._order_by)])
    #
    #     if query._limit is not None or (query._offset and db.limit_max):
    #         limit = query._limit if query._limit is not None else db.limit_max
    #         clauses.append(SQL('LIMIT %d' % limit))
    #     if query._offset is not None:
    #         clauses.append(SQL('OFFSET %d' % query._offset))
    #
    #     if query._for_update:
    #         clauses.append(SQL(query._for_update))
    #
    #     return self.build_query(clauses, alias_map)
    #
    # def generate_update(self, query):
    #     model = query.model_class
    #     alias_map = self.alias_map_class()
    #     alias_map.add(model, model._meta.db_table)
    #     if query._on_conflict:
    #         statement = 'UPDATE OR %s' % query._on_conflict
    #     else:
    #         statement = 'UPDATE'
    #     clauses = [SQL(statement), model.as_entity(), SQL('SET')]
    #
    #     update = []
    #     for field, value in self._sorted_fields(query._update):
    #         if not isinstance(value, (Node, Model)):
    #             value = Param(value, adapt=field.db_value)
    #         update.append(Expression(
    #             field.as_entity(with_table=False),
    #             OP.EQ,
    #             value,
    #             flat=True))  # No outer parens, no table alias.
    #     clauses.append(CommaClause(*update))
    #
    #     if query._where:
    #         clauses.extend([SQL('WHERE'), query._where])
    #
    #     if query._returning is not None:
    #         returning_clause = Clause(*query._returning)
    #         returning_clause.glue = ', '
    #         clauses.extend([SQL('RETURNING'), returning_clause])
    #
    #     return self.build_query(clauses, alias_map)
    #
    # def _get_field_clause(self, fields, clause_type=EnclosedClause):
    #     return clause_type(*[
    #         field.as_entity(with_table=False) for field in fields])
    #
    # def generate_insert(self, query):
    #     model = query.model_class
    #     meta = model._meta
    #     alias_map = self.alias_map_class()
    #     alias_map.add(model, model._meta.db_table)
    #     if query._upsert:
    #         statement = meta.database.upsert_sql
    #     elif query._on_conflict:
    #         statement = 'INSERT OR %s INTO' % query._on_conflict
    #     else:
    #         statement = 'INSERT INTO'
    #     clauses = [SQL(statement), model.as_entity()]
    #
    #     if query._query is not None:
    #         # This INSERT query is of the form INSERT INTO ... SELECT FROM.
    #         if query._fields:
    #             clauses.append(self._get_field_clause(query._fields))
    #         clauses.append(_StripParens(query._query))
    #
    #     elif query._rows is not None:
    #         fields, value_clauses = [], []
    #         have_fields = False
    #
    #         for row_dict in query._iter_rows():
    #             if not have_fields:
    #                 fields = sorted(
    #                     row_dict.keys(), key=operator.attrgetter('_sort_key'))
    #                 have_fields = True
    #
    #             values = []
    #             for field in fields:
    #                 value = row_dict[field]
    #                 if not isinstance(value, (Node, Model)):
    #                     value = Param(value, adapt=field.db_value)
    #                 values.append(value)
    #
    #             value_clauses.append(EnclosedClause(*values))
    #
    #         if fields:
    #             clauses.extend([
    #                 self._get_field_clause(fields),
    #                 SQL('VALUES'),
    #                 CommaClause(*value_clauses)])
    #         elif query.model_class._meta.auto_increment:
    #             # Bare insert, use default value for primary key.
    #             clauses.append(query.database.default_insert_clause(
    #                 query.model_class))
    #
    #     if query.is_insert_returning:
    #         clauses.extend([
    #             SQL('RETURNING'),
    #             self._get_field_clause(
    #                 meta.get_primary_key_fields(),
    #                 clause_type=CommaClause)])
    #     elif query._returning is not None:
    #         returning_clause = Clause(*query._returning)
    #         returning_clause.glue = ', '
    #         clauses.extend([SQL('RETURNING'), returning_clause])
    #
    #     return self.build_query(clauses, alias_map)
    #
    # def generate_delete(self, query):
    #     model = query.model_class
    #     clauses = [SQL('DELETE FROM'), model.as_entity()]
    #     if query._where:
    #         clauses.extend([SQL('WHERE'), query._where])
    #     if query._returning is not None:
    #         returning_clause = Clause(*query._returning)
    #         returning_clause.glue = ', '
    #         clauses.extend([SQL('RETURNING'), returning_clause])
    #     return self.build_query(clauses)
    #
    def field_definition(self, field):
        """field定义"""
        column_type = self.get_column_type(field.get_db_field())
        ddl = field.__ddl__(column_type)
        return ' '.join(ddl)

    # def return_parsed_node(function_name):
    #     # TODO: treat all `generate_` functions as returning clauses, instead
    #     # of SQL/params.
    #     def inner(self, *args, **kwargs):
    #         fn = getattr(self, function_name)
    #         return self.parse_node(fn(*args, **kwargs))
    #
    #     return inner
    #
    # def _create_foreign_key(self, model_class, field, constraint=None):
    #     constraint = constraint or 'fk_%s_%s_refs_%s' % (
    #         model_class._meta.db_table,
    #         field.db_column,
    #         field.rel_model._meta.db_table)
    #     fk_clause = self.foreign_key_constraint(field)
    #     return Clause(
    #         SQL('ALTER TABLE'),
    #         model_class.as_entity(),
    #         SQL('ADD CONSTRAINT'),
    #         Entity(constraint),
    #         *fk_clause.nodes)
    #
    # create_foreign_key = return_parsed_node('_create_foreign_key')

    def foreign_key_constraint(self, field):
        """外键约束"""
        ddl = [
            'FOREIGN KEY',
            '.'.join(field.column),
            'REFERENCES',
            field.rel_model.column,
            ', '.join(field.to_field.column)]
        if field.on_delete:
            ddl.append('ON DELETE %s' % field.on_delete)
        if field.on_update:
            ddl.append('ON UPDATE %s' % field.on_update)
        return ' '.join(ddl)

    def create_table(self, model_class, safe=True, **options):
        is_temp = options.pop('temporary', False)
        statement = 'CREATE TABLE IF NOT EXISTS' if safe else 'CREATE TABLE'
        meta = model_class._meta
        # 列，约束
        columns, constraints = [], []
        if meta.composite_key:
            # as_entity引用的名称或实体，如“表”、“列”
            # pk_cols = [meta.fields[f].as_entity()
            #            for f in meta.primary_key.field_names]
            # # Clause一个SQL子句，一个或多个由空格连接的节点对象
            # constraints.append(Clause(
            #     SQL('PRIMARY KEY'), EnclosedClause(*pk_cols)))
            pk_columns = [meta.fields[field_name].column
                          for field_name in meta.primary_key.field_names]
            constraints.append('PRIMARY KEY "%s" ' % ', '.join(pk_columns))

        for field in meta.declared_fields:
            print("meta.declared_fields: ", field)
            columns.append(self.field_definition(field))
            if isinstance(field, ForeignKeyField) and not field.deferred:
                constraints.append(self.foreign_key_constraint(field))
        if model_class._meta.constraints:
            for constraint in model_class._meta.constraints:
                # if not isinstance(constraint, Node):
                #     constraint = SQL(constraint)
                constraints.extend(constraint)
        # print("SQL(statement) ", SQL(statement))
        return Clause(
            SQL(statement),
            model_class.as_entity(),
            EnclosedClause(*(columns + constraints)))
        # if model_class._meta.constraints:
        #     for constraint in model_class._meta.constraints:
        #         constraints.append(constraint)
        # p = ' '.join((statement, ''.join(('"', model_class._meta.db_table, '"')),
        #               ' '.join(('(',' ,'.join(columns + constraints), ')'))))
        # p = ' '.join((statement, model_class._meta.db_table,
        #               ' '.join(('(',' ,'.join(columns + constraints), ')'))))
        # return p

    def drop_table(self, model_class, fail_silently=False, cascade=False):
        statement = 'DROP TABLE IF EXISTS' if fail_silently else 'DROP TABLE'
        ddl = [SQL(statement), model_class.as_entity()]
        if cascade:
            ddl.append(SQL('CASCADE'))
        return Clause(*ddl)

    # drop_table = return_parsed_node('_drop_table')

    def truncate_table(self, model_class, restart_identity=False,
                       cascade=False):
        ddl = [SQL('TRUNCATE TABLE'), model_class.as_entity()]
        if restart_identity:
            ddl.append(SQL('RESTART IDENTITY'))
        if cascade:
            ddl.append(SQL('CASCADE'))
        return Clause(*ddl)

    # truncate_table = return_parsed_node('_truncate_table')

    def index_name(self, table, columns):
        index = '%s_%s' % (table, '_'.join(columns))
        if len(index) > 64:
            index_hash = hashlib.md5(index.encode('utf-8')).hexdigest()
            index = '%s_%s' % (table[:55], index_hash[:8])  # 55 + 1 + 8 = 64
        return index

    def create_index(self, model_class, fields, unique, *extra):
        tbl_name = model_class._meta.db_table
        statement = 'CREATE UNIQUE INDEX' if unique else 'CREATE INDEX'
        index_name = self.index_name(tbl_name, [f.db_column for f in fields])
        return Clause(
            SQL(statement),
            Entity(index_name),
            SQL('ON'),
            model_class.as_entity(),
            EnclosedClause(*[field.as_entity() for field in fields]),
            *extra)

    # create_index = return_parsed_node('_create_index')

    def _drop_index(self, model_class, fields, fail_silently=False):
        tbl_name = model_class._meta.db_table
        statement = 'DROP INDEX IF EXISTS' if fail_silently else 'DROP INDEX'
        index_name = self.index_name(tbl_name, [f.db_column for f in fields])
        return Clause(SQL(statement), Entity(index_name))

    # drop_index = return_parsed_node('_drop_index')

    def _create_sequence(self, sequence_name):
        return Clause(SQL('CREATE SEQUENCE'), Entity(sequence_name))

    # create_sequence = return_parsed_node('_create_sequence')

    def _drop_sequence(self, sequence_name):
        return Clause(SQL('DROP SEQUENCE'), Entity(sequence_name))

    # drop_sequence = return_parsed_node('_drop_sequence')


class SqliteQueryCompiler(QueryCompiler):
    def truncate_table(self, model_class, restart_identity=False,
                       cascade=False):
        return model_class.delete().sql()


def reraise(tp, value, tb=None):
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


class ExceptionWrapper(object):
    __slots__ = ['exceptions']

    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return
        if exc_type.__name__ in self.exceptions:
            new_type = self.exceptions[exc_type.__name__]
            exc_args = exc_value.args
            reraise(new_type, new_type(*exc_args), traceback)


class Database:
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
    sequences = False  # 序列
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

    def initialize_connection(self, conn):
        pass

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

    def _create_connection(self):
        with self.exception_wrapper:
            return self._connect(self.database, **self.connect_kwargs)

    def get_conn(self):
        if self._local.context_stack:
            conn = self._local.context_stack[-1].connection
            if conn is not None:
                return conn
        if self._local.closed:
            self.connect()
        return self._local.conn

    def get_cursor(self):
        return self.get_conn().cursor()

    def set_autocommit(self, autocommit):
        self._local.autocommit = autocommit

    def get_autocommit(self):
        if self._local.autocommit is None:
            self.set_autocommit(self.autocommit)
        return self._local.autocommit

    def is_closed(self):
        return self._local.closed

    def compiler(self):
        # print("quote_char",self.quote_char, "interpolation",self.interpolation, self.field_overrides,
        #     self.op_overrides)
        return self.compiler_class(
            self.quote_char, self.interpolation, self.field_overrides,
            self.op_overrides)

    def create_table(self, model_class, safe=False):
        qc = self.compiler()
        q = qc.create_table(model_class, safe)
        print("qc.create_table:  ", q)
        # return self.execute_sql(qc.create_table(model_class, safe))
        return self.execute_sql(q)

    def execute_sql(self, sql, params=None, require_commit=True):
        # logger.debug((sql, params))
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

    def get_tables(self, schema=None):
        raise NotImplementedError


def __pragma__(name):
    def __get__(self):
        return self.pragma(name)

    def __set__(self, value):
        return self.pragma(name, value)

    return property(__get__, __set__)


def _sqlite_regexp(regex, value, case_sensitive=False):
    flags = 0 if case_sensitive else re.I
    return re.search(regex, value, flags) is not None


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
        schema = schema or 'main'
        cursor = self.execute_sql('SELECT name FROM "%s". sqlite_master WHERE '
                                  'type = ? ORDER BY name;' % schema, ('table',))
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


# Sqlite does not support the `date_part` SQL function, so we will define an
# implementation in python.
# Sqlite不支持“date_part”SQL函数，因此我们将定义一个
# 用python实现。
__sqlite_datetime_formats__ = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d',
    '%H:%M:%S',
    '%H:%M:%S.%f',
    '%H:%M')

__sqlite_date_trunc__ = {
    'year': '%Y-01-01 00:00:00',
    'month': '%Y-%m-01 00:00:00',
    'day': '%Y-%m-%d 00:00:00',
    'hour': '%Y-%m-%d %H:00:00',
    'minute': '%Y-%m-%d %H:%M:00',
    'second': '%Y-%m-%d %H:%M:%S'}

__date_parts__ = set(('year', 'month', 'day', 'hour', 'minute', 'second'))


def _sqlite_date_part(lookup_type, datetime_string):
    assert lookup_type in __date_parts__
    if not datetime_string:
        return
    dt = format_date_time(datetime_string, __sqlite_datetime_formats__)
    return getattr(dt, lookup_type)


def _sqlite_date_trunc(lookup_type, datetime_string):
    assert lookup_type in __sqlite_date_trunc__
    if not datetime_string:
        return
    dt = format_date_time(datetime_string, __sqlite_datetime_formats__)
    return dt.strftime(__sqlite_date_trunc__[lookup_type])


def _date_part(date_part):
    def dec(self):
        return self.model._meta.database.extract_date(date_part, self)

    return dec


def format_date_time(value, formats, post_process=None):
    post_process = post_process or (lambda x: x)
    for fmt in formats:
        try:
            return post_process(datetime.datetime.strptime(value, fmt))
        except ValueError:
            pass
    return value


if sqlite3:
    default_database = SqliteDatabase('pewe.db')
else:
    default_database = None


class _SortedFieldList(object):
    __slots__ = ('_keys', '_items')

    def __init__(self):
        self._keys = []
        self._items = []

    def __getitem__(self, i):
        return self._items[i]

    # 实现了__iter__方法的对象是可迭代的
    def __iter__(self):
        return iter(self._items)

    # __contains__(self, x) 函数,
    # 可判断我们输入的数据是否在Class里.参数x就是我们传入的数据.
    def __contains__(self, item):
        k = item._sort_key
        # bisect.bisect_left（a，x，lo = 0，hi = len（a））
        # 在a中找到x的插入点以维护排序顺序。参数lo和hi可用于指定应考虑的列表的子集;
        # 默认情况下，使用整个列表。如果x已经存在于a中，则插入点将位于任何现有条目之前（左侧）。
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, field):
        return self._keys.index(field._sort_key)

    def insert(self, item):
        k = item._sort_key
        i = bisect_left(self._keys, k)
        # insert() 函数用于将指定对象插入列表的指定位置。
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        idx = self.index(item)
        del self._items[idx]
        del self._keys[idx]


class Metadata(object):
    def __init__(self, cls, database=None, db_table=None, db_table_func=None,
                 indexes=None, order_by=None, primary_key=None,
                 table_alias=None, constraints=None, schema=None,
                 validate_backrefs=True, only_save_dirty=False,
                 depends_on=None, **kwargs):
        self.model_class = cls
        self.name = cls.__name__.lower()
        self.fields = {}
        self.columns = {}
        self.defaults = {}
        self._default_by_name = {}
        self._default_dict = {}
        self._default_callables = {}
        self._default_callable_list = []
        self._sorted_field_list = _SortedFieldList()
        self.sorted_fields = []
        self.sorted_field_names = []
        self.valid_fields = set()
        self.declared_fields = []

        self.database = database if database is not None else default_database
        self.db_table = db_table
        self.db_table_func = db_table_func
        self.indexes = list(indexes or [])
        self.order_by = order_by
        self.primary_key = primary_key
        self.table_alias = table_alias
        self.constraints = constraints
        self.schema = schema
        self.validate_backrefs = validate_backrefs
        self.only_save_dirty = only_save_dirty
        self.depends_on = depends_on

        self.auto_increment = None
        self.composite_key = False
        self.rel = {}
        self.reverse_rel = {}

        for key, value in kwargs.items():
            setattr(self, key, value)
        self._additional_keys = set(kwargs.keys())

        if self.db_table_func and not self.db_table:
            self.db_table = self.db_table_func(cls)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    def prepared(self):
        if self.order_by:
            norm_order_by = []
            for item in self.order_by:
                if isinstance(item, Field):
                    prefix = '-' if item._ordering == 'DESC' else ''
                    item = prefix + item.name
                field = self.fields[item.lstrip('-')]
                if item.startswith('-'):
                    norm_order_by.append(field.desc())
                else:
                    norm_order_by.append(field.asc())
            self.order_by = norm_order_by

    def _update_field_lists(self):
        self.sorted_fields = list(self._sorted_field_list)
        self.sorted_field_names = [f.name for f in self.sorted_fields]
        #  a | b 集合a或b中包含的所有元素
        self.valid_fields = (set(self.fields.keys()) |
                             set(self.fields.values()) |
                             set((self.primary_key,)))
        self.declared_fields = [field for field in self.sorted_fields
                                if not field.undeclared]

    def add_field(self, field):
        self.remove_field(field.name)
        self.fields[field.name] = field
        self.columns[field.db_column] = field
        # 如果由关键字字段把他插入到第一列。
        self._sorted_field_list.insert(field)
        self._update_field_lists()

        if field.default is not None:
            self.defaults[field] = field.default
            if callable(field.default):
                self._default_callables[field] = field.default
                self._default_callable_list.append((field.name, field.default))
            else:
                self._default_dict[field] = field.default
                self._default_by_name[field.name] = field.default

    def remove_field(self, field_name):
        if field_name not in self.fields:
            return
        original = self.fields.pop(field_name)
        del self.columns[original.db_column]
        self._sorted_field_list.remove(original)
        self._update_field_lists()

        if original.default is not None:
            del self.defaults[original]
            if self._default_callables.pop(original, None):
                for i, (name, _) in enumerate(self._default_callable_list):
                    if name == field_name:
                        self._default_callable_list.pop(i)
                        break
            else:
                self._default_dict.pop(original, None)
                self._default_by_name.pop(original.name, None)

    def get_default_dict(self):
        dd = self._default_by_name.copy()
        for field_name, default in self._default_callable_list:
            dd[field_name] = default()
        return dd

    def get_field_index(self, field):
        try:
            return self._sorted_field_list.index(field)
        except ValueError:
            return -1

    def get_primary_key_fields(self):
        if self.composite_key:
            return [
                self.fields[field_name]
                for field_name in self.primary_key.field_names]
        return [self.primary_key]

    def rel_for_model(self, model, field_obj=None, multi=False):
        is_field = isinstance(field_obj, Field)
        is_node = not is_field and isinstance(field_obj, Node)
        if multi:
            accum = []
        for field in self.sorted_fields:
            if isinstance(field, ForeignKeyField) and field.rel_model == model:
                is_match = (
                        (field_obj is None) or
                        (is_field and field_obj.name == field.name) or
                        (is_node and field_obj._alias == field.name))
                if is_match:
                    if not multi:
                        return field
                    accum.append(field)
        if multi:
            return accum

    def reverse_rel_for_model(self, model, field_obj=None, multi=False):
        return model._meta.rel_for_model(self.model_class, field_obj, multi)

    def rel_exists(self, model):
        return self.rel_for_model(model) or self.reverse_rel_for_model(model)

    def related_models(self, backrefs=False):
        models = []
        stack = [self.model_class]
        while stack:
            model = stack.pop()
            if model in models:
                continue
            models.append(model)
            for fk in model._meta.rel.values():
                stack.append(fk.rel_model)
            if backrefs:
                for fk in model._meta.reverse_rel.values():
                    stack.append(fk.model_class)
        return models


class ModelMetaclass(type):
    # 定义可以继承的属性
    inheritable = set(['constraints', 'database', 'indexes', 'primary_key',
                       'options', 'schema', 'table_function', 'temporary',
                       'only_save_dirty', 'legacy_table_names',
                       'table_settings'])

    def __new__(mcs, name, bases, attrs):
        # if name == "Model" or bases[0].__name__ == "ModelMetaclass":
        # 假定用户创建的类是父类Model,不进行任何操作，因为需要修改的是用户自定义类
        print("name:", name)
        # print("bases[0]name:", bases[0].__name__)
        if name == "Mod el":
            # if bases:
            #     print("bases[0]", bases[0])
            # print("name:", name)
            return super().__new__(mcs, name, bases, attrs)
        # Meta类的属性通过meta_options存储在类中
        meta_options = {}
        meta = attrs.pop('Meta', None)
        if meta:
            for k, v in meta.__dict__.items():
                if not k.startswith('_'):  # 将Meta从属性中移除，将Meta中的非私有属性加入meta_options中
                    meta_options[k] = v
        # 从meta中获取主键信息
        model_pk = getattr(meta, 'primary_key', None)
        parent_pk = None
        ############################################################
        # 开始考虑从父类中继承的情况
        #############################################################
        # 通过深度复制基础字段来继承任何字段描述符
        # 在新模型的属性中，另外看看基是否定义了
        # 可继承的模型选项并滑动它们。
        # Inherit any field descriptors by deep copying the underlying field
        # into the attrs of the new model, additionally see if the bases define
        # inheritable model options and swipe them.
        for b in bases:
            # print("bases[0]", bases[0])
            if not hasattr(b, '_meta'):
                continue
            # 获取父类中Meta类的属性
            base_meta = b._meta
            if parent_pk is None:
                parent_pk = deepcopy(base_meta.primary_key)
            #  a | b 集合a或b中包含的所有元素
            all_inheritable = mcs.inheritable | base_meta._additional_keys
            # 获取父类中的Meta内部类字段，只考虑all_inheritable中的字段
            for k in base_meta.__dict__:
                if k in all_inheritable and k not in meta_options:
                    meta_options[k] = base_meta.__dict__[k]
            # meta_options.setdefault('schema', base_meta.schema)
            # 获取父类中的Fields, 即表的字段
            for (k, v) in b.__dict__.items():
                # print("k", k, "v", v)
                if k in attrs: continue

                if isinstance(v, FieldDescriptor) and not v.field.primary_key:
                    attrs[k] = deepcopy(v.field)

        # sopts = meta_options.pop('schema_options', None) or {}
        Meta = meta_options.get('model_metadata_class', Metadata)
        # Schema = meta_options.get('schema_manager_class', SchemaManager)

        # Construct the new class.and set the magic attributes
        mcs = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)
        mcs.__data__ = mcs.__rel__ = None

        mcs._meta = Meta(mcs, **meta_options)
        mcs._meta.indexes = list(mcs._meta.indexes)
        # mcs._schema = Schema(mcs, **sopts)
        # 获取类中的Fields, 即表的字段
        # replace fields with field descriptors, calling the add_to_class hook
        fields = []
        # 一个k, v 类似于 id : IntegerField('id')
        # 其中k是id，v是IntegerField的一个实例
        for name, attr in mcs.__dict__.items():
            if isinstance(attr, Field):
                if attr.primary_key and model_pk:
                    raise ValueError('primary key is overdetermined.')
                elif attr.primary_key:
                    model_pk, pk_name = attr, name
                else:
                    fields.append((attr, name))
        print("fields: ", fields)
        # 默认表名的设定，Model名的小写，然后将非数字和英文字符换成'_'
        if not mcs._meta.db_table:
            mcs._meta.db_table = re.sub('[^\w]+', '_', mcs.__name__.lower())
        # 默认主键的设置，如果无法从父类继承，，则使用'id'为key, 也就是行号
        # if pk is None:
        #     if parent_pk is not False:
        #         pk, pk_name = ((parent_pk, parent_pk.name)
        #                        if parent_pk is not None else
        #                        (AutoField(), 'id'))
        #     else:
        #         pk = False
        # elif isinstance(pk, CompositeKey):  # 由多列组成的主键
        #     pk_name = '__composite_key__'
        #     mcs._meta.composite_key = True
        #
        # if pk is not False:
        #     mcs._meta.set_primary_key(pk_name, pk)
        #
        # for name, field in fields:
        #     mcs._meta.add_field(name, field)
        composite_key = False
        if model_pk is None:
            if parent_pk:
                model_pk, pk_name = parent_pk, parent_pk.name
            else:
                model_pk, pk_name = PrimaryKeyField(primary_key=True), 'id'
        if isinstance(model_pk, CompositeKey):
            pk_name = '_composite_key'
            composite_key = True

        if model_pk is not False:
            model_pk.add_to_class(mcs, pk_name)
            mcs._meta.primary_key = model_pk
            mcs._meta.auto_increment = (
                    isinstance(model_pk, PrimaryKeyField) or
                    bool(model_pk.sequence))
            mcs._meta.composite_key = composite_key

        for field, name in fields:
            field.add_to_class(mcs, name)

        # 在完成之前创建repr和error类。
        # Create a repr and error class before finalizing.
        if hasattr(mcs, '__str__') and '__repr__' not in attrs:
            setattr(mcs, '__repr__', lambda self: '<%s: %s>' % (
                mcs.__name__, self.__str__()))

        exc_name = '%sDoesNotExist' % mcs.__name__
        exc_attrs = {'__module__': mcs.__module__}
        exception_class = type(exc_name, (DoesNotExist,), exc_attrs)
        mcs.DoesNotExist = exception_class
        mcs._meta.prepared()
        # 调用验证钩子，允许额外的模型验证。
        # Call validation hook, allowing additional model validation.
        if hasattr(mcs, 'validate_model'):
            mcs.validate_model()
        DeferredForeignKey.resolve(mcs)
        return mcs


class ModelDelete(object):
    pass


class ModelAlias(object):
    pass


class ModelSelect(object):
    pass


class ModelUpdate(object):
    pass


class ModelInsert(object):
    pass


class ModelRaw(object):
    pass


class NoopModelSelect(object):
    pass


class Value(object):
    pass


class _BoundModelsContext:
    """边界模型上下文"""

    def __init__(self, models, database, bind_refs, bind_backrefs):
        self.models = models
        self.database = database
        self.bind_refs = bind_refs
        self.bind_backrefs = bind_backrefs

    def __enter__(self):
        self._orig_database = []
        for model in self.models:
            self._orig_database.append(model._meta.database)
            model.bind(self.database, self.bind_refs, self.bind_backrefs,
                       _exclude=set(self.models))
        return self.models

    def __exit__(self, exc_type, exc_val, exc_tb):
        for model, db in zip(self.models, self._orig_database):
            model.bind(db, self.bind_refs, self.bind_backrefs,
                       _exclude=set(self.models))


class Model(metaclass=ModelMetaclass):
    def __init__(self, *args, **kwargs):
        # if kwargs.pop('__no_default__', None):
        #     self.__data__ = {}
        # else:
        #     self.__data__ = self._meta.get_default_dict()
        self._data = self._meta.get_default_dict()
        self._dirty = set(self._data)
        # self.__rel__ = {}
        self._obj_cache = {}

        for k in kwargs:
            setattr(self, k, kwargs[k])

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.save(force_insert=True)
        inst._prepare_instance()
        return inst

    def _prepare_instance(self):
        self._dirty.clear()
        self.prepared()

    def prepared(self):
        pass

    @classmethod
    def table_exists(cls):
        kwargs = {}
        if cls._meta.schema:
            kwargs['schema'] = cls._meta.schema
        return cls._meta.db_table in cls._meta.database.get_tables(**kwargs)

    @classmethod
    def create_table(cls, fail_silently=False):
        if fail_silently and cls.table_exists():
            return

        db = cls._meta.database
        pk = cls._meta.primary_key
        if db.sequences and pk is not False and pk.sequence:
            if not db.sequence_exists(pk.sequence):
                db.create_sequence(pk.sequence)

        db.create_table(cls)
        cls._create_indexes()


# 测试


sqlite_db = SqliteDatabase('app12.db')


class BaseModel(Model):
    """A base model that will use our Sqlite database."""

    class Meta:
        database = sqlite_db


class User(BaseModel):
    name = TextField()


new_user = User(name='LiMing')
if __name__ == "__main__":
    new_user.create_table()
    # new_user.save()
    # new_user.s
