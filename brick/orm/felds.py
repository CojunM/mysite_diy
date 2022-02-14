#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:24
# @Author  : Cojun  Mao
# @Site    : 
# @File    : felds.py
# @Project : mysite_diy
# @Software: PyCharm

import re
# from brick.orm.map import op_map
from collections import namedtuple

from brick.orm.utils import format_unicode, basestring, format_date_time, datetime

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


class Leaf(object):
    """查询的任何部分的基类，该部分应是可组合的"""

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
        """轻型工厂，它返回一个构建表达式的方法
        由左操作数和右操作数组成，使用'op'。
        以实现类似 WHERE ("name" = ?)
        """

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
    __rxor__ = _e(OP_XOR)
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
        # print('op', op)
        super(Expr, self).__init__()
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.negated = negated
        # print('--Expr--')

    def clone(self):
        return Expr(self.lhs, self.op, self.rhs, self.negated)


class DQ(Leaf):
    """A "django-style" filter expression, e.g. {'foo__eq': 'x'}."""
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


fn = Func(None)
# Python元组的升级版本 -- namedtuple(具名元组)
# collections.namedtuple(typename, field_names, verbose=False, rename=False)
# 返回一个具名元组子类 typename，其中参数的意义如下：
# typename：元组名称
# field_names: 元组中元素的名称
# rename: 如果元素名称中含有 python 的关键字，则必须设置为 rename=True
# verbose: 默认就好
Ordering = namedtuple('Ordering', ('param', 'asc'))
R = namedtuple('R', ('value',))


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
    def __hash__(self):
        return hash(self.name + '.' + self.model_class.__name__)

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


class ReverseRelationDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.rel_model = field.model_class

    def __get__(self, instance, instance_type=None):
        if instance:
            return self.rel_model.select().where(self.field == instance.get_id())
        return self


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


class TimeField(Field):
    db_field = 'time'

    def field_attributes(self):
        return {
            'formats': [
                '%H:%M:%S.%f',
                '%H:%M:%S',
                '%H:%M',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
            ]
        }

    def python_value(self, value):
        if value and isinstance(value, basestring):
            pp = lambda x: x.time()
            return format_date_time(value, self.attributes['formats'], pp)
        elif value and isinstance(value, datetime):
            return value.time()
        return value


class DateTimeField(Field):
    db_field = 'datetime'

    def field_attributes(self):
        return {
            'formats': [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]
        }

    def python_value(self, value):
        if value and isinstance(value, basestring):
            return format_date_time(value, self.attributes['formats'])
        return value

class DateField(Field):
    db_field = 'date'

    def field_attributes(self):
        return {
            'formats': [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
            ]
        }

    def python_value(self, value):
        if value and isinstance(value, basestring):
            pp = lambda x: x.date()
            return format_date_time(value, self.attributes['formats'], pp)
        elif value and isinstance(value, datetime.datetime):
            return value.date()
        return value

class BooleanField(Field):
    db_field = 'bool'

    def coerce(self, value):
        return bool(value)