#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:24
# @Author  : Cojun  Mao
# @Site    : 
# @File    : felds.py
# @Project : mysite_diy
# @Software: PyCharm
import calendar
import decimal
import operator
import re
import time
import uuid
import weakref
from collections import namedtuple
from functools import wraps, reduce

from brick.core.db.constants import unicode_type, string_type, long
from brick.core.db.utils import basestring, format_date_time, datetime, returns_clone, OP, binary_construct, \
    DeferredRelation

# from inspect import isclass

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict


class _CDescriptor(object):
    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return Entity(instance._alias)
        return self


class Node(object):
    """Base-class for any part of a query which shall be composable."""
    c = _CDescriptor()
    _node_type = 'node'

    def __init__(self):
        self._negated = False
        self._alias = None
        self._bind_to = None
        self._ordering = None  # ASC or DESC.

    @classmethod
    def extend(cls, name=None, clone=False):
        def decorator(method):
            method_name = name or method.__name__
            if clone:
                method = returns_clone(method)
            setattr(cls, method_name, method)
            return method

        return decorator

    def clone_base(self):
        return type(self)()

    def clone(self):
        inst = self.clone_base()
        inst._negated = self._negated
        inst._alias = self._alias
        inst._ordering = self._ordering
        inst._bind_to = self._bind_to
        return inst

    @returns_clone
    def __invert__(self):
        self._negated = not self._negated

    @returns_clone
    def alias(self, a=None):
        '''别名'''
        self._alias = a

    @returns_clone
    def bind_to(self, bt):
        """
        Bind the results of an expression to a specific model type. Useful
        when adding expressions to a select, where the result of the expression
        should be placed on a joined instance.
        """
        self._bind_to = bt

    @returns_clone
    def asc(self):
        self._ordering = 'ASC'

    @returns_clone
    def desc(self):
        self._ordering = 'DESC'

    def __pos__(self):
        return self.asc()

    def __neg__(self):
        return self.desc()

    def _e(op, inv=False):
        """
        Lightweight factory which returns a method that builds an Expression
        consisting of the left-hand and right-hand operands, using `op`.
        """

        def inner(self, rhs):
            if inv:
                return Expression(rhs, op, self)
            return Expression(self, op, rhs)

        return inner

    __and__ = _e(OP.AND)
    __or__ = _e(OP.OR)

    __add__ = _e(OP.ADD)
    __sub__ = _e(OP.SUB)
    __mul__ = _e(OP.MUL)
    __div__ = __truediv__ = _e(OP.DIV)
    __xor__ = _e(OP.XOR)
    __radd__ = _e(OP.ADD, inv=True)
    __rsub__ = _e(OP.SUB, inv=True)
    __rmul__ = _e(OP.MUL, inv=True)
    __rdiv__ = __rtruediv__ = _e(OP.DIV, inv=True)
    __rand__ = _e(OP.AND, inv=True)
    __ror__ = _e(OP.OR, inv=True)
    __rxor__ = _e(OP.XOR, inv=True)

    like = _e(OP.LIKE)
    ilike = _e(OP.ILIKE)

    bin_and = _e(OP.BIN_AND)
    bin_or = _e(OP.BIN_OR)
    in_ = _e(OP.IN)
    not_in = _e(OP.NOT_IN)
    regexp = _e(OP.REGEXP)

    def __eq__(self, rhs):
        if rhs is None:
            return Expression(self, OP.IS, None)
        return Expression(self, OP.EQ, rhs)

    def __ne__(self, rhs):
        if rhs is None:
            return Expression(self, OP.IS_NOT, None)
        return Expression(self, OP.NE, rhs)

    __lt__ = _e(OP.LT)
    __le__ = _e(OP.LTE)
    __gt__ = _e(OP.GT)
    __ge__ = _e(OP.GTE)
    __lshift__ = _e(OP.IN)
    __rshift__ = _e(OP.IS)
    __mod__ = _e(OP.LIKE)
    __pow__ = _e(OP.ILIKE)

    bin_and = _e(OP.BIN_AND)
    bin_or = _e(OP.BIN_OR)

    # Special expressions.
    def in_(self, rhs):
        return Expression(self, OP.IN, rhs)

    def not_in(self, rhs):
        return Expression(self, OP.NOT_IN, rhs)

    def is_null(self, is_null=True):
        if is_null:
            return Expression(self, OP.IS, None)
        return Expression(self, OP.IS_NOT, None)

    def contains(self, rhs):
        return Expression(self, OP.ILIKE, '%%%s%%' % rhs)

    def startswith(self, rhs):
        return Expression(self, OP.ILIKE, '%s%%' % rhs)

    def endswith(self, rhs):
        return Expression(self, OP.ILIKE, '%%%s' % rhs)

    def between(self, low, high):
        return Expression(self, OP.BETWEEN, Clause(low, R('AND'), high))

    def regexp(self, expression):
        return Expression(self, OP.REGEXP, expression)

    def concat(self, rhs):
        return StringExpression(self, OP.CONCAT, rhs)


class SQL(Node):
    """An unescaped SQL string, with optional parameters.
    带可选参数的未转义SQL字符串。"""
    _node_type = 'sql'

    def __init__(self, value, *params):
        self.value = value
        self.params = params
        super(SQL, self).__init__()

    def clone_base(self):
        return SQL(self.value, *self.params)


R = SQL  # backwards-compat.


class Entity(Node):
    """A quoted-name or entity, e.g. "table"."column"."""
    _node_type = 'entity'

    def __init__(self, *path):
        super(Entity, self).__init__()
        self.path = path

    def clone_base(self):
        return Entity(*self.path)

    def __getattr__(self, attr):
        return Entity(*filter(None, self.path + (attr,)))  # filter过滤掉列表中的None


class Func(Node):
    """An arbitrary SQL function call."""
    _node_type = 'func'
    _no_coerce = set(('count', 'sum'))

    def __init__(self, name, *arguments):
        self.name = name
        self.arguments = arguments
        self._coerce = (name.lower() not in self._no_coerce) if name else False
        super(Func, self).__init__()

    @returns_clone
    def coerce(self, coerce=True):
        self._coerce = coerce

    def clone_base(self):
        res = Func(self.name, *self.arguments)
        res._coerce = self._coerce
        return res

    def over(self, partition_by=None, order_by=None, start=None, end=None,
             window=None):
        if isinstance(partition_by, Window) and window is None:
            window = partition_by
        if start is not None and not isinstance(start, SQL):
            start = SQL(*start)
        if end is not None and not isinstance(end, SQL):
            end = SQL(*end)

        if window is None:
            sql = Window(partition_by=partition_by, order_by=order_by,
                         start=start, end=end).__sql__()
        else:
            sql = SQL(window._alias)
        return Clause(self, SQL('OVER'), sql)

    def __getattr__(self, attr):
        def dec(*args, **kwargs):
            return Func(attr, *args, **kwargs)

        return dec


# fn is a factory for creating `Func` objects and supports a more friendly
# API.  So instead of `Func("LOWER", param)`, `fn.LOWER(param)`.
fn = Func(None)


class Expression(Node):
    """A binary expression, e.g `foo + 1` or `bar < 7`
    二进制表达式，例如“foo+1”或“bar<7”。."""
    _node_type = 'expression'

    def __init__(self, lhs, op, rhs, flat=False):
        super(Expression, self).__init__()
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.flat = flat

    def clone_base(self):
        return Expression(self.lhs, self.op, self.rhs, self.flat)


class StringExpression(Expression):
    def __add__(self, other):
        return self.concat(other)

    def __radd__(self, other):
        return other.concat(self)


class Param(Node):
    """
    Arbitrary parameter passed into a query. Instructs the query compiler to
    specifically treat this value as a parameter, useful for `list` which is
    special-cased for `IN` lookups.
    """
    _node_type = 'param'

    def __init__(self, value, adapt=None):
        self.value = value
        self.adapt = adapt
        super(Param, self).__init__()

    def clone_base(self):
        return Param(self.value, self.adapt)


class Passthrough(Param):
    _node_type = 'passthrough'


class Clause(Node):
    """A SQL clause, one or more Node objects joined by spaces."""
    _node_type = 'clause'

    glue = ' '
    parens = False

    def __init__(self, *nodes, **kwargs):
        if 'glue' in kwargs:
            self.glue = kwargs['glue']
        if 'parens' in kwargs:
            self.parens = kwargs['parens']
        super(Clause, self).__init__()
        self.nodes = list(nodes)

    def clone_base(self):
        clone = Clause(*self.nodes)
        clone.glue = self.glue
        clone.parens = self.parens
        return clone


class CommaClause(Clause):
    """One or more Node objects joined by commas, no parens."""
    glue = ', '


class EnclosedClause(CommaClause):
    """One or more Node objects joined by commas and enclosed in parens."""
    parens = True


Tuple = EnclosedClause


def EnclosedNodeList(nodes):
    return Clause(nodes, ', ', True)


class _StripParens(Node):
    _node_type = 'strip_parens'

    def __init__(self, node):
        super(_StripParens, self).__init__()
        self.node = node


class CompositeKey(object):
    """A primary key composed of multiple columns."""
    _node_type = 'composite_key'
    sequence = None

    def __init__(self, *field_names):
        self.field_names = field_names

    def add_to_class(self, model_class, name):
        self.name = name
        self.model_class = model_class
        setattr(model_class, name, self)

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return tuple([getattr(instance, field_name)
                          for field_name in self.field_names])
        return self

    def __set__(self, instance, value):
        pass

    def __eq__(self, other):
        expressions = [(self.model_class._meta.fields[field] == value)
                       for field, value in zip(self.field_names, other)]
        return reduce(operator.and_, expressions)

    def __ne__(self, other):
        return ~(self == other)

    def __hash__(self):
        return hash((self.model_class.__name__, self.field_names))


class Window(Node):
    CURRENT_ROW = 'CURRENT ROW'

    def __init__(self, partition_by=None, order_by=None, start=None, end=None):
        super(Window, self).__init__()
        self.partition_by = partition_by
        self.order_by = order_by
        self.start = start
        self.end = end
        if self.start is None and self.end is not None:
            raise ValueError('Cannot specify WINDOW end without start.')
        self._alias = self._alias or 'w'

    @staticmethod
    def following(value=None):
        if value is None:
            return SQL('UNBOUNDED FOLLOWING')
        return SQL('%d FOLLOWING' % value)

    @staticmethod
    def preceding(value=None):
        if value is None:
            return SQL('UNBOUNDED PRECEDING')
        return SQL('%d PRECEDING' % value)

    def __sql__(self):
        over_clauses = []
        if self.partition_by:
            over_clauses.append(Clause(
                SQL('PARTITION BY'),
                CommaClause(*self.partition_by)))
        if self.order_by:
            over_clauses.append(Clause(
                SQL('ORDER BY'),
                CommaClause(*self.order_by)))
        if self.start is not None and self.end is not None:
            over_clauses.append(Clause(
                SQL('RANGE BETWEEN'),
                self.start,
                SQL('AND'),
                self.end))
        elif self.start is not None:
            over_clauses.append(Clause(SQL('RANGE'), self.start))
        return EnclosedClause(Clause(*over_clauses))

    def clone_base(self):
        return Window(self.partition_by, self.order_by)


def Check(value):
    return SQL('CHECK (%s)' % value)


class DQ(Node):
    """A "django-style" filter expression, e.g. {'foo__eq': 'x'}."""

    def __init__(self, **query):
        super(DQ, self).__init__()
        self.query = query

    def clone_base(self):
        return DQ(**self.query)


class ResultIterator(object):
    def __init__(self, qrw):
        self.qrw = qrw
        self._idx = 0

    def next(self):
        if self._idx < self.qrw._ct:
            obj = self.qrw._result_cache[self._idx]
        elif not self.qrw._populated:
            obj = self.qrw.iterate()
            self.qrw._result_cache.append(obj)
            self.qrw._ct += 1
        else:
            raise StopIteration
        self._idx += 1
        return obj

    __next__ = next


class QueryResultWrapper(object):
    """
    Provides an iterator over the results of a raw Query, additionally doing
    two things:
    - converts rows from the database into python representations
    - ensures that multiple iterations do not result in multiple queries
    """

    def __init__(self, model, cursor, meta=None):
        self.model = model
        self.cursor = cursor

        self._ct = 0
        self._idx = 0

        self._result_cache = []
        self._populated = False
        self._initialized = False

        if meta is not None:
            self.column_meta, self.join_meta = meta
        else:
            self.column_meta = self.join_meta = None

    def __iter__(self):
        if self._populated:
            return iter(self._result_cache)
        else:
            return ResultIterator(self)

    @property
    def count(self):
        self.fill_cache()
        return self._ct

    def __len__(self):
        return self.count

    def process_row(self, row):
        return row

    def iterate(self):
        row = self.cursor.fetchone()
        if not row:
            self._populated = True
            if not getattr(self.cursor, 'name', None):
                self.cursor.close()
            raise StopIteration
        elif not self._initialized:
            self.initialize(self.cursor.description)
            self._initialized = True
        return self.process_row(row)

    def iterator(self):
        while True:
            yield self.iterate()

    def next(self):
        if self._idx < self._ct:
            inst = self._result_cache[self._idx]
            self._idx += 1
            return inst
        elif self._populated:
            raise StopIteration

        obj = self.iterate()
        self._result_cache.append(obj)
        self._ct += 1
        self._idx += 1
        return obj

    __next__ = next

    def fill_cache(self, n=None):
        n = n or float('Inf')
        if n < 0:
            raise ValueError('Negative values are not supported.')
        self._idx = self._ct
        while not self._populated and (n > self._ct):
            try:
                next(self)
            except StopIteration:
                break


class ExtQueryResultWrapper(QueryResultWrapper):
    def initialize(self, description):
        n_cols = len(description)
        self.conv = conv = []
        if self.column_meta is not None:
            n_meta = len(self.column_meta)
            for i, node in enumerate(self.column_meta):
                if not self._initialize_node(node, i):
                    self._initialize_by_name(description[i][0], i)
            if n_cols == n_meta:
                return
        else:
            i = 0

        for i in range(i, n_cols):
            self._initialize_by_name(description[i][0], i)

    def _initialize_by_name(self, name, i):
        model_cols = self.model._meta.columns
        if name in model_cols:
            field = model_cols[name]
            self.conv.append((i, field.name, field.python_value))
        else:
            self.conv.append((i, name, None))

    def _initialize_node(self, node, i):
        if isinstance(node, Field):
            self.conv.append((i, node._alias or node.name, node.python_value))
            return True
        elif isinstance(node, Func) and len(node.arguments):
            arg = node.arguments[0]
            if isinstance(arg, Field):
                name = node._alias or arg._alias or arg.name
                func = node._coerce and arg.python_value or None
                self.conv.append((i, name, func))
                return True
        return False


class TuplesQueryResultWrapper(ExtQueryResultWrapper):
    def process_row(self, row):
        return tuple([col if self.conv[i][2] is None else self.conv[i][2](col)
                      for i, col in enumerate(row)])


class NaiveQueryResultWrapper(ExtQueryResultWrapper):
    def process_row(self, row):
        instance = self.model()
        for i, column, f in self.conv:
            setattr(instance, column, f(row[i]) if f is not None else row[i])
        instance._prepare_instance()
        return instance


class ModelQueryResultWrapper(QueryResultWrapper):
    def initialize(self, description):
        self.column_map, model_set = self.generate_column_map()
        self._col_set = set(col for col in self.column_meta
                            if isinstance(col, Field))
        self.join_list = self.generate_join_list(model_set)

    def generate_column_map(self):
        column_map = []
        models = set([self.model])
        for i, node in enumerate(self.column_meta):
            attr = conv = None
            if isinstance(node, Field):
                if isinstance(node, FieldProxy):
                    key = node._model_alias
                    constructor = node.model
                    conv = node.field_instance.python_value
                else:
                    key = constructor = node.model_class
                    conv = node.python_value
                attr = node._alias or node.name
            else:
                if node._bind_to is None:
                    key = constructor = self.model
                else:
                    key = constructor = node._bind_to
                if isinstance(node, Node) and node._alias:
                    attr = node._alias
                elif isinstance(node, Entity):
                    attr = node.path[-1]
            column_map.append((key, constructor, attr, conv))
            models.add(key)

        return column_map, models

    def generate_join_list(self, models):
        join_list = []
        joins = self.join_meta
        stack = [self.model]
        while stack:
            current = stack.pop()
            if current not in joins:
                continue

            for join in joins[current]:
                metadata = join.metadata
                if metadata.dest in models or metadata.dest_model in models:
                    if metadata.foreign_key is not None:
                        fk_present = metadata.foreign_key in self._col_set
                        pk_present = metadata.primary_key in self._col_set
                        check = metadata.foreign_key.null and (fk_present or
                                                               pk_present)
                    else:
                        check = fk_present = pk_present = False

                    join_list.append((
                        metadata,
                        check,
                        fk_present,
                        pk_present))
                    stack.append(join.dest)

        return join_list

    def process_row(self, row):
        collected = self.construct_instances(row)
        instances = self.follow_joins(collected)
        for i in instances:
            i._prepare_instance()
        return instances[0]

    def construct_instances(self, row, keys=None):
        collected_models = {}
        for i, (key, constructor, attr, conv) in enumerate(self.column_map):
            if keys is not None and key not in keys:
                continue
            value = row[i]
            if key not in collected_models:
                collected_models[key] = constructor()
            instance = collected_models[key]
            if attr is None:
                attr = self.cursor.description[i][0]
            setattr(instance, attr, value if conv is None else conv(value))

        return collected_models

    def follow_joins(self, collected):
        prepared = [collected[self.model]]
        for (metadata, check_null, fk_present, pk_present) in self.join_list:
            inst = collected[metadata.src]
            try:
                joined_inst = collected[metadata.dest]
            except KeyError:
                joined_inst = collected[metadata.dest_model]

            has_fk = True
            if check_null:
                if fk_present:
                    has_fk = inst._data.get(metadata.foreign_key.name)
                elif pk_present:
                    has_fk = joined_inst._data.get(metadata.primary_key.name)

            if not has_fk:
                continue

            # Can we populate a value on the joined instance using the current?
            mpk = metadata.primary_key is not None
            can_populate_joined_pk = (
                    mpk and
                    (metadata.attr in inst._data) and
                    (getattr(joined_inst, metadata.primary_key.name) is None))
            if can_populate_joined_pk:
                setattr(
                    joined_inst,
                    metadata.primary_key.name,
                    inst._data[metadata.attr])

            if metadata.is_backref:
                can_populate_joined_fk = (
                        mpk and
                        (metadata.foreign_key is not None) and
                        (getattr(inst, metadata.primary_key.name) is not None) and
                        (joined_inst._data.get(metadata.foreign_key.name) is None))
                if can_populate_joined_fk:
                    setattr(
                        joined_inst,
                        metadata.foreign_key.name,
                        inst)

            setattr(inst, metadata.attr, joined_inst)
            prepared.append(joined_inst)

        return prepared


class DictQueryResultWrapper(ExtQueryResultWrapper):
    def process_row(self, row):
        res = {}
        for i, column, f in self.conv:
            res[column] = f(row[i]) if f is not None else row[i]
        return res


class NamedTupleQueryResultWrapper(ExtQueryResultWrapper):
    def initialize(self, description):
        super(NamedTupleQueryResultWrapper, self).initialize(description)
        columns = [column for _, column, _ in self.conv]
        self.constructor = namedtuple('Row', columns)

    def process_row(self, row):
        return self.constructor(*[f(row[i]) if f is not None else row[i]
                                  for i, _, f in self.conv])


class ModelQueryResultWrapper(QueryResultWrapper):
    def initialize(self, description):
        self.column_map, model_set = self.generate_column_map()
        self._col_set = set(col for col in self.column_meta
                            if isinstance(col, Field))
        self.join_list = self.generate_join_list(model_set)

    def generate_column_map(self):
        column_map = []
        models = set([self.model])
        for i, node in enumerate(self.column_meta):
            attr = conv = None
            if isinstance(node, Field):
                if isinstance(node, FieldProxy):
                    key = node._model_alias
                    constructor = node.model
                    conv = node.field_instance.python_value
                else:
                    key = constructor = node.model_class
                    conv = node.python_value
                attr = node._alias or node.name
            else:
                if node._bind_to is None:
                    key = constructor = self.model
                else:
                    key = constructor = node._bind_to
                if isinstance(node, Node) and node._alias:
                    attr = node._alias
                elif isinstance(node, Entity):
                    attr = node.path[-1]
            column_map.append((key, constructor, attr, conv))
            models.add(key)

        return column_map, models

    def generate_join_list(self, models):
        join_list = []
        joins = self.join_meta
        stack = [self.model]
        while stack:
            current = stack.pop()
            if current not in joins:
                continue

            for join in joins[current]:
                metadata = join.metadata
                if metadata.dest in models or metadata.dest_model in models:
                    if metadata.foreign_key is not None:
                        fk_present = metadata.foreign_key in self._col_set
                        pk_present = metadata.primary_key in self._col_set
                        check = metadata.foreign_key.null and (fk_present or
                                                               pk_present)
                    else:
                        check = fk_present = pk_present = False

                    join_list.append((
                        metadata,
                        check,
                        fk_present,
                        pk_present))
                    stack.append(join.dest)

        return join_list

    def process_row(self, row):
        collected = self.construct_instances(row)
        instances = self.follow_joins(collected)
        for i in instances:
            i._prepare_instance()
        return instances[0]

    def construct_instances(self, row, keys=None):
        collected_models = {}
        for i, (key, constructor, attr, conv) in enumerate(self.column_map):
            if keys is not None and key not in keys:
                continue
            value = row[i]
            if key not in collected_models:
                collected_models[key] = constructor()
            instance = collected_models[key]
            if attr is None:
                attr = self.cursor.description[i][0]
            setattr(instance, attr, value if conv is None else conv(value))

        return collected_models

    def follow_joins(self, collected):
        prepared = [collected[self.model]]
        for (metadata, check_null, fk_present, pk_present) in self.join_list:
            inst = collected[metadata.src]
            try:
                joined_inst = collected[metadata.dest]
            except KeyError:
                joined_inst = collected[metadata.dest_model]

            has_fk = True
            if check_null:
                if fk_present:
                    has_fk = inst._data.get(metadata.foreign_key.name)
                elif pk_present:
                    has_fk = joined_inst._data.get(metadata.primary_key.name)

            if not has_fk:
                continue

            # Can we populate a value on the joined instance using the current?
            mpk = metadata.primary_key is not None
            can_populate_joined_pk = (
                    mpk and
                    (metadata.attr in inst._data) and
                    (getattr(joined_inst, metadata.primary_key.name) is None))
            if can_populate_joined_pk:
                setattr(
                    joined_inst,
                    metadata.primary_key.name,
                    inst._data[metadata.attr])

            if metadata.is_backref:
                can_populate_joined_fk = (
                        mpk and
                        (metadata.foreign_key is not None) and
                        (getattr(inst, metadata.primary_key.name) is not None) and
                        (joined_inst._data.get(metadata.foreign_key.name) is None))
                if can_populate_joined_fk:
                    setattr(
                        joined_inst,
                        metadata.foreign_key.name,
                        inst)

            setattr(inst, metadata.attr, joined_inst)
            prepared.append(joined_inst)

        return prepared


JoinCache = namedtuple('JoinCache', ('metadata', 'attr'))


class AggregateQueryResultWrapper(ModelQueryResultWrapper):
    def __init__(self, *args, **kwargs):
        self._row = []
        super(AggregateQueryResultWrapper, self).__init__(*args, **kwargs)

    def initialize(self, description):
        super(AggregateQueryResultWrapper, self).initialize(description)

        # Collect the set of all model (and ModelAlias objects) queried.
        self.all_models = set()
        for key, _, _, _ in self.column_map:
            self.all_models.add(key)

        # Prepare data structures for analyzing unique rows. Also cache
        # foreign key and attribute names for joined model.
        self.models_with_aggregate = set()
        self.back_references = {}
        self.source_to_dest = {}
        self.dest_to_source = {}

        for (metadata, _, _, _) in self.join_list:
            if metadata.is_backref:
                att_name = metadata.foreign_key.related_name
            else:
                att_name = metadata.attr

            is_backref = metadata.is_backref or metadata.is_self_join
            if is_backref:
                self.models_with_aggregate.add(metadata.src)
            else:
                self.dest_to_source.setdefault(metadata.dest, set())
                self.dest_to_source[metadata.dest].add(metadata.src)

            self.source_to_dest.setdefault(metadata.src, {})
            self.source_to_dest[metadata.src][metadata.dest] = JoinCache(
                metadata=metadata,
                attr=metadata.alias or att_name)

        # Determine which columns could contain "duplicate" data, e.g. if
        # getting Users and their Tweets, this would be the User columns.
        self.columns_to_compare = {}
        key_to_columns = {}
        for idx, (key, model_class, col_name, _) in enumerate(self.column_map):
            if key in self.models_with_aggregate:
                self.columns_to_compare.setdefault(key, [])
                self.columns_to_compare[key].append((idx, col_name))

            key_to_columns.setdefault(key, [])
            key_to_columns[key].append((idx, col_name))

        # Also compare columns for joins -> many-related model.
        for model_or_alias in self.models_with_aggregate:
            if model_or_alias not in self.columns_to_compare:
                continue
            sources = self.dest_to_source.get(model_or_alias, ())
            for joined_model in sources:
                self.columns_to_compare[model_or_alias].extend(
                    key_to_columns[joined_model])

    def read_model_data(self, row):
        models = {}
        for model_class, column_data in self.columns_to_compare.items():
            models[model_class] = []
            for idx, col_name in column_data:
                models[model_class].append(row[idx])
        return models

    def iterate(self):
        if self._row:
            row = self._row.pop()
        else:
            row = self.cursor.fetchone()

        if not row:
            self._populated = True
            if not getattr(self.cursor, 'name', None):
                self.cursor.close()
            raise StopIteration
        elif not self._initialized:
            self.initialize(self.cursor.description)
            self._initialized = True

        def _get_pk(instance):
            if instance._meta.composite_key:
                return tuple([
                    instance._data[field_name]
                    for field_name in instance._meta.primary_key.field_names])
            return instance._get_pk_value()

        identity_map = {}
        _constructed = self.construct_instances(row)
        primary_instance = _constructed[self.model]
        for model_or_alias, instance in _constructed.items():
            identity_map[model_or_alias] = OrderedDict()
            identity_map[model_or_alias][_get_pk(instance)] = instance

        model_data = self.read_model_data(row)
        while True:
            cur_row = self.cursor.fetchone()
            if cur_row is None:
                break

            duplicate_models = set()
            cur_row_data = self.read_model_data(cur_row)
            for model_class, data in cur_row_data.items():
                if model_data[model_class] == data:
                    duplicate_models.add(model_class)

            if not duplicate_models:
                self._row.append(cur_row)
                break

            different_models = self.all_models - duplicate_models

            new_instances = self.construct_instances(cur_row, different_models)
            for model_or_alias, instance in new_instances.items():
                # Do not include any instances which are comprised solely of
                # NULL values.
                all_none = True
                for value in instance._data.values():
                    if value is not None:
                        all_none = False
                if not all_none:
                    identity_map[model_or_alias][_get_pk(instance)] = instance

        stack = [self.model]
        instances = [primary_instance]
        while stack:
            current = stack.pop()
            if current not in self.join_meta:
                continue

            for join in self.join_meta[current]:
                try:
                    metadata, attr = self.source_to_dest[current][join.dest]
                except KeyError:
                    continue

                if metadata.is_backref or metadata.is_self_join:
                    for instance in identity_map[current].values():
                        setattr(instance, attr, [])

                    if join.dest not in identity_map:
                        continue

                    for pk, inst in identity_map[join.dest].items():
                        if pk is None:
                            continue
                        try:
                            # XXX: if no FK exists, unable to join.
                            joined_inst = identity_map[current][
                                inst._data[metadata.foreign_key.name]]
                        except KeyError:
                            continue

                        getattr(joined_inst, attr).append(inst)
                        instances.append(inst)
                elif attr:
                    if join.dest not in identity_map:
                        continue

                    for pk, instance in identity_map[current].items():
                        # XXX: if no FK exists, unable to join.
                        joined_inst = identity_map[join.dest][
                            instance._data[metadata.foreign_key.name]]
                        setattr(
                            instance,
                            metadata.foreign_key.name,
                            joined_inst)
                        instances.append(joined_inst)

                stack.append(join.dest)

        for instance in instances:
            instance._prepare_instance()

        return primary_instance


class _callable_context_manager(object):
    __slots__ = ()

    def __call__(self, fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            with self:
                return fn(*args, **kwargs)

        return inner


class ExecutionContext(_callable_context_manager):
    def __init__(self, database, with_transaction=True, transaction_type=None):
        self.database = database
        self.with_transaction = with_transaction
        self.transaction_type = transaction_type
        self.connection = None

    def __enter__(self):
        with self.database._conn_lock:
            self.database.push_execution_context(self)
            self.connection = self.database._connect(
                self.database.database,
                **self.database.connect_kwargs)
            if self.with_transaction:
                self.txn = self.database.transaction()
                self.txn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.database._conn_lock:
            if self.connection is None:
                self.database.pop_execution_context()
            else:
                try:
                    if self.with_transaction:
                        if not exc_type:
                            self.txn.commit(False)
                        self.txn.__exit__(exc_type, exc_val, exc_tb)
                finally:
                    self.database.pop_execution_context()
                    self.database._close(self.connection)


class Using(ExecutionContext):
    def __init__(self, database, models, with_transaction=True):
        super(Using, self).__init__(database, with_transaction)
        self.models = models

    def __enter__(self):
        self._orig = []
        for model in self.models:
            self._orig.append(model._meta.database)
            model._meta.database = self.database
        return super(Using, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Using, self).__exit__(exc_type, exc_val, exc_tb)
        for i, model in enumerate(self.models):
            model._meta.database = self._orig[i]


class _atomic(_callable_context_manager):
    __slots__ = ('db', 'transaction_type', 'context_manager')

    def __init__(self, db, transaction_type=None):
        self.db = db
        self.transaction_type = transaction_type

    def __enter__(self):
        if self.db.transaction_depth() == 0:
            self.context_manager = self.db.transaction(self.transaction_type)
        else:
            self.context_manager = self.db.savepoint()
        return self.context_manager.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.context_manager.__exit__(exc_type, exc_val, exc_tb)


class transaction(_callable_context_manager):
    __slots__ = ('db', 'autocommit', 'transaction_type')

    def __init__(self, db, transaction_type=None):
        self.db = db
        self.transaction_type = transaction_type

    def _begin(self):
        if self.transaction_type:
            self.db.begin(self.transaction_type)
        else:
            self.db.begin()

    def commit(self, begin=True):
        self.db.commit()
        if begin: self._begin()

    def rollback(self, begin=True):
        self.db.rollback()
        if begin: self._begin()

    def __enter__(self):
        self.autocommit = self.db.get_autocommit()
        self.db.set_autocommit(False)
        if self.db.transaction_depth() == 0: self._begin()
        self.db.push_transaction(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.rollback(False)
            elif self.db.transaction_depth() == 1:
                try:
                    self.commit(False)
                except:
                    self.rollback(False)
                    raise
        finally:
            self.db.set_autocommit(self.autocommit)
            self.db.pop_transaction()


class savepoint(_callable_context_manager):
    __slots__ = ('db', 'sid', 'quoted_sid', 'autocommit')

    def __init__(self, db, sid=None):
        self.db = db
        _compiler = db.compiler()
        self.sid = sid or 's' + uuid.uuid4().hex
        self.quoted_sid = _compiler.quote(self.sid)

    def _execute(self, query):
        self.db.execute_sql(query, require_commit=False)

    def _begin(self):
        self._execute('SAVEPOINT %s;' % self.quoted_sid)

    def commit(self, begin=True):
        self._execute('RELEASE SAVEPOINT %s;' % self.quoted_sid)
        if begin: self._begin()

    def rollback(self):
        self._execute('ROLLBACK TO SAVEPOINT %s;' % self.quoted_sid)

    def __enter__(self):
        self.autocommit = self.db.get_autocommit()
        self.db.set_autocommit(False)
        self._begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.rollback()
            else:
                try:
                    self.commit(begin=False)
                except:
                    self.rollback()
                    raise
        finally:
            self.db.set_autocommit(self.autocommit)


class transaction_sqlite(transaction):
    __slots__ = ()

    def _begin(self):
        self.db.begin(lock_type=self.transaction_type)


class savepoint_sqlite(savepoint):
    __slots__ = ('isolation_level',)

    def __enter__(self):
        conn = self.db.get_conn()
        # For sqlite, the connection's isolation_level *must* be set to None.
        # The act of setting it, though, will break any existing savepoints,
        # so only write to it if necessary.
        if conn.isolation_level is not None:
            self.isolation_level = conn.isolation_level
            conn.isolation_level = None
        else:
            self.isolation_level = None
        return super(savepoint_sqlite, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return super(savepoint_sqlite, self).__exit__(
                exc_type, exc_val, exc_tb)
        finally:
            if self.isolation_level is not None:
                self.db.get_conn().isolation_level = self.isolation_level


class Value(Node):
    def __init__(self, value, converter=None, unpack=True):
        self.value = value
        self.converter = converter
        self.multi = unpack and isinstance(self.value, (list, tuple, frozenset, set, range))
        if self.multi:
            self.values = []
            for item in self.value:
                if isinstance(item, Node):
                    self.values.append(item)
                else:
                    self.values.append(Value(item, self.converter))

    def __sql__(self, ctx):
        if self.multi:
            # For multi-part values (e.g. lists of IDs).
            return ctx.sql(EnclosedNodeList(self.values))

        return ctx.value(self.value, self.converter)


class FieldDescriptor(object):
    # Fields are exposed as descriptors in order to control access to the
    #     # underlying "raw" data.
    # 字段作为描述符公开，以便控制对
    # 底层“原始”数据。
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


#
class Field(Node):
    """A column on a table."""
    _field_counter = 0
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
        self._sort_key = (self.primary_key and 1 or 2), self._order  # 创建元组
        # print('self._sort_key',self._sort_key)
        self._is_bound = False  # Whether the Field is "bound" to a Model.字段是否“绑定”到模型。
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

    def get_column_type(self):
        field_type = self.get_db_field()
        return self.get_database().compiler().get_column_type(field_type)

    def get_db_field(self):
        return self.db_field

    def get_modifiers(self):
        return None

    def coerce(self, value):
        '''强迫'''
        return value

    # def bind(self, model, name, set_attribute=True):
    #     self.model_class = model
    #     self.name = self.safe_name = name
    #     self.db_column = self.db_column or name
    #     if set_attribute:
    #         setattr(model, name, FieldDescriptor(self))

    def db_value(self, value):
        """Convert the python value for storage in the database.
        转换python值以存储在数据库中"""
        return value if value is None else self.coerce(value)

    def python_value(self, value):
        """Convert the database value to a pythonic value.
        将数据库值转换为pythonic值。"""
        return value if value is None else self.coerce(value)

    def as_entity(self, with_table=False):
        if with_table:
            return Entity(self.model_class._meta.db_table, self.db_column)
        return Entity(self.db_column)

    def __ddl_column__(self, column_type):
        """Return the column type, e.g. VARCHAR(255) or REAL.
        返回列类型，例如VARCHAR（255）或REAL。"""
        modifiers = self.get_modifiers()
        if modifiers:
            return SQL(
                '%s(%s)' % (column_type, ', '.join(map(str, modifiers))))
        return SQL(column_type)

    def __ddl__(self, column_type):
        """Return a list of Node instances that defines the column
        返回定义列的节点实例列表。."""
        ddl = [self.as_entity(), self.__ddl_column__(column_type)]
        if not self.null:
            ddl.append(SQL('NOT NULL'))
        if self.primary_key:
            ddl.append(SQL('PRIMARY KEY'))
        if self.sequence:
            ddl.append(SQL("DEFAULT NEXTVAL('%s')" % self.sequence))
        if self.constraints:
            ddl.extend(self.constraints)
        return ddl

    def __hash__(self):
        return hash(self.name + '.' + self.model_class.__name__)


class FieldProxy(Field):
    def __init__(self, alias, field_instance):
        self._model_alias = alias
        self.model = self._model_alias.model_class
        self.field_instance = field_instance

    def clone_base(self):
        return FieldProxy(self._model_alias, self.field_instance)

    def coerce(self, value):
        return self.field_instance.coerce(value)

    def python_value(self, value):
        return self.field_instance.python_value(value)

    def db_value(self, value):
        return self.field_instance.db_value(value)

    def __getattr__(self, attr):
        if attr == 'model_class':
            return self._model_alias
        return getattr(self.field_instance, attr)


class BareField(Field):
    db_field = 'bare'

    def __init__(self, coerce=None, *args, **kwargs):
        super(BareField, self).__init__(*args, **kwargs)
        if coerce is not None:
            self.coerce = coerce

    def clone_base(self, **kwargs):
        return super(BareField, self).clone_base(coerce=self.coerce, **kwargs)


class IntegerField(Field):
    db_field = 'int'
    coerce = int


class BigIntegerField(IntegerField):
    db_field = 'bigint'


class SmallIntegerField(IntegerField):
    db_field = 'smallint'


class PrimaryKeyField(IntegerField):
    db_field = 'primary_key'

    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(PrimaryKeyField, self).__init__(*args, **kwargs)


class _AutoPrimaryKeyField(PrimaryKeyField):
    _column_name = None

    def __init__(self, *args, **kwargs):
        if 'undeclared' in kwargs and not kwargs['undeclared']:
            raise ValueError('%r must be created with undeclared=True.' % self)
        kwargs['undeclared'] = True
        super(_AutoPrimaryKeyField, self).__init__(*args, **kwargs)

    def add_to_class(self, model_class, name):
        if name != self._column_name:
            raise ValueError('%s must be named `%s`.' % (type(self), name))
        super(_AutoPrimaryKeyField, self).add_to_class(model_class, name)


class FloatField(Field):
    db_field = 'float'
    coerce = float


class DoubleField(FloatField):
    db_field = 'double'


class DecimalField(Field):
    db_field = 'decimal'

    def __init__(self, max_digits=10, decimal_places=5, auto_round=False,
                 rounding=None, *args, **kwargs):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.auto_round = auto_round
        self.rounding = rounding or decimal.DefaultContext.rounding
        self._exp = decimal.Decimal(10) ** (-self.decimal_places)
        super(DecimalField, self).__init__(*args, **kwargs)

    def clone_base(self, **kwargs):
        return super(DecimalField, self).clone_base(
            max_digits=self.max_digits,
            decimal_places=self.decimal_places,
            auto_round=self.auto_round,
            rounding=self.rounding,
            **kwargs)

    def get_modifiers(self):
        return [self.max_digits, self.decimal_places]

    def db_value(self, value):
        D = decimal.Decimal
        if not value:
            return value if value is None else D(0)
        elif self.auto_round or not isinstance(value, D):
            value = D(str(value))
            if value.is_normal() and self.auto_round:
                value = value.quantize(self._exp, rounding=self.rounding)
        return value

    def python_value(self, value):
        if value is not None:
            if isinstance(value, decimal.Decimal):
                return value
            return decimal.Decimal(str(value))


def coerce_to_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode_type):
        return s
    elif isinstance(s, string_type):
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            return s
    return unicode_type(s)


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


class Proxy(object):
    """
    Proxy class useful for situations when you wish to defer the initialization
    of an object.
    """
    __slots__ = ('obj', '_callbacks')

    def __init__(self):
        self._callbacks = []
        self.initialize(None)

    def initialize(self, obj):
        self.obj = obj
        for callback in self._callbacks:
            callback(obj)

    def attach_callback(self, callback):
        self._callbacks.append(callback)
        return callback

    def __getattr__(self, attr):
        if self.obj is None:
            raise AttributeError('Cannot use uninitialized Proxy.')
        return getattr(self.obj, attr)

    def __setattr__(self, attr, value):
        if attr not in self.__slots__:
            raise AttributeError('Cannot set attribute on proxy.')
        return super(Proxy, self).__setattr__(attr, value)


class BlobField(Field):
    db_field = 'blob'
    _constructor = binary_construct

    def add_to_class(self, model_class, name):
        if isinstance(model_class._meta.database, Proxy):
            model_class._meta.database.attach_callback(self._set_constructor)
        return super(BlobField, self).add_to_class(model_class, name)

    def _set_constructor(self, database):
        self._constructor = database.get_binary_type()

    def db_value(self, value):
        if isinstance(value, unicode_type):
            value = value.encode('raw_unicode_escape')
        if isinstance(value, basestring):
            return self._constructor(value)
        return value


class UUIDField(Field):
    db_field = 'uuid'

    def db_value(self, value):
        if isinstance(value, uuid.UUID):
            return value.hex
        try:
            return uuid.UUID(value).hex
        except:
            return value

    def python_value(self, value):
        if isinstance(value, uuid.UUID):
            return value
        return None if value is None else uuid.UUID(value)


def _date_part(date_part):
    def dec(self):
        return self.model_class._meta.database.extract_date(date_part, self)

    return dec


class _BaseFormattedField(Field):
    formats = None

    def __init__(self, formats=None, *args, **kwargs):
        if formats is not None:
            self.formats = formats
        super(_BaseFormattedField, self).__init__(*args, **kwargs)

    def clone_base(self, **kwargs):
        return super(_BaseFormattedField, self).clone_base(
            formats=self.formats,
            **kwargs)


class DateTimeField(_BaseFormattedField):
    db_field = 'datetime'
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]

    def python_value(self, value):
        if value and isinstance(value, basestring):
            return format_date_time(value, self.formats)
        return value

    year = property(_date_part('year'))
    month = property(_date_part('month'))
    day = property(_date_part('day'))
    hour = property(_date_part('hour'))
    minute = property(_date_part('minute'))
    second = property(_date_part('second'))


class DateField(_BaseFormattedField):
    db_field = 'date'
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
    ]

    def python_value(self, value):
        if value and isinstance(value, basestring):
            pp = lambda x: x.date()
            return format_date_time(value, self.formats, pp)
        elif value and isinstance(value, datetime.datetime):
            return value.date()
        return value

    year = property(_date_part('year'))
    month = property(_date_part('month'))
    day = property(_date_part('day'))


class TimeField(_BaseFormattedField):
    db_field = 'time'
    formats = [
        '%H:%M:%S.%f',
        '%H:%M:%S',
        '%H:%M',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
    ]

    def python_value(self, value):
        if value:
            if isinstance(value, basestring):
                pp = lambda x: x.time()
                return format_date_time(value, self.formats, pp)
            elif isinstance(value, datetime.datetime):
                return value.time()
        if value is not None and isinstance(value, datetime.timedelta):
            return (datetime.datetime.min + value).time()
        return value

    hour = property(_date_part('hour'))
    minute = property(_date_part('minute'))
    second = property(_date_part('second'))


class TimestampField(IntegerField):
    # Support second -> microsecond resolution.
    valid_resolutions = [10 ** i for i in range(7)]
    zero_value = None

    def __init__(self, *args, **kwargs):
        self.resolution = kwargs.pop('resolution', 1) or 1
        if self.resolution not in self.valid_resolutions:
            raise ValueError('TimestampField resolution must be one of: %s' %
                             ', '.join(str(i) for i in self.valid_resolutions))

        self.utc = kwargs.pop('utc', False) or False
        _dt = datetime.datetime
        self._conv = _dt.utcfromtimestamp if self.utc else _dt.fromtimestamp
        _default = _dt.utcnow if self.utc else _dt.now
        kwargs.setdefault('default', _default)
        self.zero_value = kwargs.pop('zero_value', None)
        super(TimestampField, self).__init__(*args, **kwargs)

    def get_db_field(self):
        # For second resolution we can get away (for a while) with using
        # 4 bytes to store the timestamp (as long as they're not > ~2038).
        # Otherwise we'll need to use a BigInteger type.
        return (self.db_field if self.resolution == 1
                else BigIntegerField.db_field)

    def db_value(self, value):
        if value is None:
            return

        if isinstance(value, datetime.datetime):
            pass
        elif isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
        else:
            return int(round(value * self.resolution))

        if self.utc:
            timestamp = calendar.timegm(value.utctimetuple())
        else:
            timestamp = time.mktime(value.timetuple())
        timestamp += (value.microsecond * .000001)
        if self.resolution > 1:
            timestamp *= self.resolution
        return int(round(timestamp))

    def python_value(self, value):
        if value is not None and isinstance(value, (int, float, long)):
            if value == 0:
                return self.zero_value
            elif self.resolution > 1:
                ticks_to_microsecond = 1000000 // self.resolution
                value, ticks = divmod(value, self.resolution)
                microseconds = ticks * ticks_to_microsecond
                return self._conv(value).replace(microsecond=microseconds)
            else:
                return self._conv(value)
        return value


class BooleanField(Field):
    db_field = 'bool'
    coerce = bool


class RelationDescriptor(FieldDescriptor):
    """Foreign-key abstraction to replace a related PK with a related model.
    用相关模型替换相关PK的外键抽象。"""

    def __init__(self, field, rel_model):
        self.rel_model = rel_model
        super(RelationDescriptor, self).__init__(field)

    def get_object_or_id(self, instance):
        rel_id = instance._data.get(self.att_name)
        if rel_id is not None or self.att_name in instance._obj_cache:
            if self.att_name not in instance._obj_cache:
                obj = self.rel_model.get(self.field.to_field == rel_id)
                instance._obj_cache[self.att_name] = obj
            return instance._obj_cache[self.att_name]
        elif not self.field.null:
            raise self.rel_model.DoesNotExist
        return rel_id

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return self.get_object_or_id(instance)
        return self.field

    def __set__(self, instance, value):
        if isinstance(value, self.rel_model):
            instance._data[self.att_name] = getattr(
                value, self.field.to_field.name)
            instance._obj_cache[self.att_name] = value
        else:
            orig_value = instance._data.get(self.att_name)
            instance._data[self.att_name] = value
            if orig_value != value and self.att_name in instance._obj_cache:
                del instance._obj_cache[self.att_name]
        instance._dirty.add(self.att_name)


class ReverseRelationDescriptor(object):
    """Back-reference to expose related objects as a `SelectQuery`
    反向引用以将相关对象公开为`selectquery`."""

    def __init__(self, field):
        self.field = field
        self.rel_model = field.model_class

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return self.rel_model.select().where(
                self.field == getattr(instance, self.field.to_field.name))
        return self


class ObjectIdDescriptor(object):
    """Gives direct access to the underlying id"
    提供对基础id的直接访问"""

    def __init__(self, field):
        self.attr_name = field.name
        #  返回对象object的弱引用。如果指示对象仍然存在，则可以通过调用引用对象来检索原始对象;
        #  如果指示对象不再存在，则调用引用对象将返回None。如果提供了callback且不返回None，并且返回的weakref对象仍然存活，则在对象即将销毁时将调用回调;
        #  弱引用对象将作为唯一参数传递给回调;
        #  指示对象将不再可用。
        # https: // blog.csdn.net / L_zzwwen / article / details / 100071136
        self.field = weakref.ref(field)

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return instance._data.get(self.attr_name)
        return self.field()

    def __set__(self, instance, value):
        setattr(instance, self.attr_name, value)


class ForeignKeyField(IntegerField):
    def __init__(self, rel_model, related_name=None, on_delete=None,
                 on_update=None, extra=None, to_field=None,
                 object_id_name=None, *args, **kwargs):
        from brick.core.db.models import Model
        if rel_model != 'self' and not \
                isinstance(rel_model, (Proxy, DeferredRelation)) and not \
                issubclass(rel_model, Model):
            raise TypeError('Unexpected value for `rel_model`.  Expected '
                            '`Model`, `Proxy`, `DeferredRelation`, or "self"')
        self.rel_model = rel_model
        self._related_name = related_name
        self.deferred = isinstance(rel_model, (Proxy, DeferredRelation))
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
        if isinstance(self.rel_model, Proxy):
            def callback(rel_model):
                self.rel_model = rel_model
                self.add_to_class(model_class, name)

            self.rel_model.attach_callback(callback)
            return
        elif isinstance(self.rel_model, DeferredRelation):
            self.rel_model.set_field(model_class, self, name)
            return

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
        Overridden to ensure Foreign Keys use same column type as the primary
        key they point to.
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


class DeferredThroughModel(object):
    '''延迟吞吐量模型'''

    def set_field(self, model_class, field, name):
        self.model_class = model_class
        self.field = field
        self.name = name

    def set_model(self, through_model):
        self.field._through_model = through_model
        self.field.add_to_class(self.model_class, self.name)


class ManyToManyField(Field):
    def __init__(self, rel_model, related_name=None, through_model=None,
                 _is_backref=False, on_delete=None,
                 on_update=None, verbose_name=None):
        from brick.core.db.models import Model
        if through_model is not None and not (
                isinstance(through_model, (Proxy, DeferredThroughModel)) or
                issubclass(through_model, Model)):
            raise TypeError('Unexpected value for `through_model`.  Expected '
                            '`Model`, `Proxy` or `DeferredThroughModel`.')
        self.rel_model = rel_model
        self._related_name = related_name
        self._through_model = through_model
        self._is_backref = _is_backref
        self.primary_key = False
        self.verbose_name = verbose_name
        self._on_delete = on_delete
        self._on_update = on_update

    def _get_descriptor(self):
        return ManyToManyFieldDescriptor(self)

    def add_to_class(self, model_class, name):
        if isinstance(self._through_model, Proxy):
            def callback(through_model):
                self._through_model = through_model
                self.add_to_class(model_class, name)

            self._through_model.attach_callback(callback)
            return
        elif isinstance(self._through_model, DeferredThroughModel):
            self._through_model.set_field(model_class, self, name)
            return

        self.name = name
        self.model_class = model_class
        if not self.verbose_name:
            self.verbose_name = re.sub('_+', ' ', name).title()
        setattr(model_class, name, self._get_descriptor())

        if not self._is_backref:
            backref = ManyToManyField(
                self.model_class,
                through_model=self._through_model, on_delete=self._on_delete,
                on_update=self._on_update,
                _is_backref=True, verbose_name=self.verbose_name)
            related_name = self._related_name or model_class._meta.name + 's'
            backref.add_to_class(self.rel_model, related_name)

    def get_models(self):
        return [model for _, model in sorted((
            (self._is_backref, self.model_class),
            (not self._is_backref, self.rel_model)))]

    def get_through_model(self):
        if not self._through_model:
            lhs, rhs = self.get_models()
            tables = [model._meta.db_table for model in (lhs, rhs)]

            class Meta:
                database = self.model_class._meta.database
                db_table = '%s_%s_through' % tuple(tables)
                indexes = (
                    ((lhs._meta.name, rhs._meta.name),
                     True),)
                validate_backrefs = False

            attrs = {lhs._meta.name: ForeignKeyField(rel_model=lhs),
                     rhs._meta.name: ForeignKeyField(rel_model=rhs)}
            attrs['Meta'] = Meta

            from brick.core.db.models import Model
            self._through_model = type(
                '%s%sThrough' % (lhs.__name__, rhs.__name__),
                (Model,),
                attrs)

        return self._through_model


class ManyToManyFieldDescriptor(FieldDescriptor):
    def __init__(self, field):
        super(ManyToManyFieldDescriptor, self).__init__(field)
        self.model_class = field.model_class
        self.rel_model = field.rel_model
        self.through_model = field.get_through_model()
        self.src_fk = self.through_model._meta.rel_for_model(self.model_class)
        self.dest_fk = self.through_model._meta.rel_for_model(self.rel_model)

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            from brick.core.db.modelquerys import ManyToManyQuery
            return (ManyToManyQuery(instance, self, self.rel_model)
                    .select()
                    .join(self.through_model)
                    .join(self.model_class)
                    .where(self.src_fk == instance))
        return self.field

    def __set__(self, instance, value):
        query = self.__get__(instance)
        query.add(value, clear_existing=True)
