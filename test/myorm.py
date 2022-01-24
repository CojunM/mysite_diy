#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:16
# @Author  : Cojun  Mao
# @Site    : 
# @File    : myorm.py
# @Project : mysite_diy
# @Software: PyCharm
import builtins
import collections
import datetime
import operator
import re
import sqlite3
import threading
from copy import deepcopy
from collections.abc import Callable

# callable_ = callable
from functools import wraps

callable_ = lambda c: isinstance(c, Callable)
text_type = str
bytes_type = bytes
buffer_type = memoryview
basestring = str
long = int
multi_types = (list, tuple, frozenset, set, range)
print_ = getattr(builtins, 'print')


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


def query_to_string(query):
    # NOTE: this function is not exported by default as it might be misused --
    # and this misuse could lead to sql injection vulnerabilities. This
    # function is intended for debugging or logging purposes ONLY.
    db = getattr(query, '_database', None)
    if db is not None:
        ctx = db.get_sql_context()
    else:
        ctx = Context()

    sql, params = ctx.sql(query).query()
    if not params:
        return sql

    param = ctx.state.param or '?'
    if param == '?':
        sql = sql.replace('?', '%s')

    return sql % tuple(map(_query_val_transform, params))


def _query_val_transform(v):
    # Interpolate parameters.
    if isinstance(v, (text_type, datetime.datetime, datetime.date,
                      datetime.time)):
        v = "'%s'" % v
    elif isinstance(v, bytes_type):
        try:
            v = v.decode('utf8')
        except UnicodeDecodeError:
            v = v.decode('raw_unicode_escape')
        v = "'%s'" % v
    elif isinstance(v, int):
        v = '%s' % int(v)  # Also handles booleans -> 1 or 0.
    elif v is None:
        v = 'NULL'
    else:
        v = str(v)
    return v


class Node(object):
    _coerce = True

    def clone(self):
        obj = self.__class__.__new__(self.__class__)
        obj.__dict__ = self.__dict__.copy()
        print("obj  ", obj)
        return obj

    def __sql__(self, ctx):
        raise NotImplementedError

    @staticmethod
    def copy(method):
        def inner(self, *args, **kwargs):
            clone = self.clone()
            method(clone, *args, **kwargs)
            return clone

        return inner

    def coerce(self, _coerce=True):
        if _coerce != self._coerce:
            clone = self.clone()
            clone._coerce = _coerce
            return clone
        return self

    def is_alias(self):
        return False

    def unwrap(self):
        return self


class Expression():
    def __init__(self, lhs, op, rhs, flat=False):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.flat = flat

    def __sql__(self, ctx):
        overrides = {'parentheses': not self.flat, 'in_expr': True}

        # First attempt to unwrap the node on the left-hand-side, so that we
        # can get at the underlying Field if one is present.
        node = raw_node = self.lhs
        # if isinstance(raw_node, WrappedNode):
        #     node = raw_node.unwrap()

        # Set up the appropriate converter if we have a field on the left side.
        if isinstance(node, Field) and raw_node._coerce:
            overrides['converter'] = node.db_value
            overrides['is_fk_expr'] = isinstance(node, ForeignKeyField)
        else:
            overrides['converter'] = None

        if ctx.state.operations:
            op_sql = ctx.state.operations.get(self.op, self.op)
        else:
            op_sql = self.op

        with ctx(**overrides):
            # Postgresql reports an error for IN/NOT IN (), so convert to
            # the equivalent boolean expression.
            op_in = self.op == OP.IN or self.op == OP.NOT_IN
            if op_in and ctx.as_new().parse(self.rhs)[0] == '()':
                return ctx.literal('0 = 1' if self.op == OP.IN else '1 = 1')

            return (ctx
                    .sql(self.lhs)
                    .literal(' %s ' % op_sql)
                    .sql(self.rhs))


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

SNAKE_CASE_STEP1 = re.compile('(.)_*([A-Z][a-z]+)')
SNAKE_CASE_STEP2 = re.compile('([a-z0-9])_*([A-Z])')


def merge_dict(source, overrides):
    merged = source.copy()
    if overrides:
        merged.update(overrides)
    return merged


def quote(path, quote_chars):
    if len(path) == 1:
        return path[0].join(quote_chars)
    return '.'.join([part.join(quote_chars) for part in path])


def make_snake_case(s):
    first = SNAKE_CASE_STEP1.sub(r'\1_\2', s)
    return SNAKE_CASE_STEP2.sub(r'\1_\2', first).lower()


class _callable_context_manager(object):
    def __call__(self, fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            with self:
                return fn(*args, **kwargs)

        return inner



class ColumnBase(Node):
    _converter = None

    @Node.copy
    def converter(self, converter=None):
        self._converter = converter

    def alias(self, alias):
        if alias:
            return Alias(self, alias)
        return self

    def unalias(self):
        return self

    def cast(self, as_type):
        return Cast(self, as_type)

    def asc(self, collation=None, nulls=None):
        return Asc(self, collation=collation, nulls=nulls)

    __pos__ = asc

    def desc(self, collation=None, nulls=None):
        return Desc(self, collation=collation, nulls=nulls)

    __neg__ = desc

    def __invert__(self):
        return Negated(self)

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

    def __eq__(self, rhs):
        op = OP.IS if rhs is None else OP.EQ
        return Expression(self, op, rhs)

    def __ne__(self, rhs):
        op = OP.IS_NOT if rhs is None else OP.NE
        return Expression(self, op, rhs)

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
    in_ = _e(OP.IN)
    not_in = _e(OP.NOT_IN)
    regexp = _e(OP.REGEXP)

    # Special expressions.
    def is_null(self, is_null=True):
        op = OP.IS if is_null else OP.IS_NOT
        return Expression(self, op, None)

    def _escape_like_expr(self, s, template):
        if s.find('_') >= 0 or s.find('%') >= 0 or s.find('\\') >= 0:
            s = s.replace('\\', '\\\\').replace('_', '\\_').replace('%', '\\%')
            return NodeList((template % s, SQL('ESCAPE'), '\\'))
        return template % s

    def contains(self, rhs):
        if isinstance(rhs, Node):
            rhs = Expression('%', OP.CONCAT,
                             Expression(rhs, OP.CONCAT, '%'))
        else:
            rhs = self._escape_like_expr(rhs, '%%%s%%')
        return Expression(self, OP.ILIKE, rhs)

    def startswith(self, rhs):
        if isinstance(rhs, Node):
            rhs = Expression(rhs, OP.CONCAT, '%')
        else:
            rhs = self._escape_like_expr(rhs, '%s%%')
        return Expression(self, OP.ILIKE, rhs)

    def endswith(self, rhs):
        if isinstance(rhs, Node):
            rhs = Expression('%', OP.CONCAT, rhs)
        else:
            rhs = self._escape_like_expr(rhs, '%%%s')
        return Expression(self, OP.ILIKE, rhs)

    def between(self, lo, hi):
        return Expression(self, OP.BETWEEN, NodeList((lo, SQL('AND'), hi)))

    def concat(self, rhs):
        return StringExpression(self, OP.CONCAT, rhs)

    def regexp(self, rhs):
        return Expression(self, OP.REGEXP, rhs)

    def iregexp(self, rhs):
        return Expression(self, OP.IREGEXP, rhs)

    def __getitem__(self, item):
        if isinstance(item, slice):
            if item.start is None or item.stop is None:
                raise ValueError('BETWEEN range must have both a start- and '
                                 'end-point.')
            return self.between(item.start, item.stop)
        return self == item

    def distinct(self):
        return NodeList((SQL('DISTINCT'), self))

    def collate(self, collation):
        return NodeList((self, SQL('COLLATE %s' % collation)))

    def get_sort_key(self, ctx):
        return ()

class WrappedNode(ColumnBase):
    def __init__(self, node):
        self.node = node
        self._coerce = getattr(node, '_coerce', True)
        self._converter = getattr(node, '_converter', None)

    def is_alias(self):
        return self.node.is_alias()

    def unwrap(self):
        return self.node.unwrap()


class Negated(WrappedNode):
    def __invert__(self):
        return self.node

    def __sql__(self, ctx):
        return ctx.literal('NOT ').sql(self.node)



class Cast(WrappedNode):
    def __init__(self, node, cast):
        super(Cast, self).__init__(node)
        self._cast = cast
        self._coerce = False

    def __sql__(self, ctx):
        return (ctx
                .literal('CAST(')
                .sql(self.node)
                .literal(' AS %s)' % self._cast))


class Ordering(WrappedNode):
    def __init__(self, node, direction, collation=None, nulls=None):
        super(Ordering, self).__init__(node)
        self.direction = direction
        self.collation = collation
        self.nulls = nulls
        if nulls and nulls.lower() not in ('first', 'last'):
            raise ValueError('Ordering nulls= parameter must be "first" or '
                             '"last", got: %s' % nulls)

    def collate(self, collation=None):
        return Ordering(self.node, self.direction, collation)

    def _null_ordering_case(self, nulls):
        if nulls.lower() == 'last':
            ifnull, notnull = 1, 0
        elif nulls.lower() == 'first':
            ifnull, notnull = 0, 1
        else:
            raise ValueError('unsupported value for nulls= ordering.')
        return Case(None, ((self.node.is_null(), ifnull),), notnull)

    def __sql__(self, ctx):
        if self.nulls and not ctx.state.nulls_ordering:
            ctx.sql(self._null_ordering_case(self.nulls)).literal(', ')

        ctx.sql(self.node).literal(' %s' % self.direction)
        if self.collation:
            ctx.literal(' COLLATE %s' % self.collation)
        if self.nulls and ctx.state.nulls_ordering:
            ctx.literal(' NULLS %s' % self.nulls)
        return ctx


def Asc(node, collation=None, nulls=None):
    return Ordering(node, 'ASC', collation, nulls)


def Desc(node, collation=None, nulls=None):
    return Ordering(node, 'DESC', collation, nulls)

class Value(ColumnBase):
    def __init__(self, value, converter=None, unpack=True):
        self.value = value
        self.converter = converter
        self.multi = unpack and isinstance(self.value, multi_types)
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


is_model = lambda o: isclass(o) and issubclass(o, Model)


class Context(object):
    __slots__ = ('stack', '_sql', '_values', 'alias_manager', 'state')

    def __init__(self, **settings):
        self.stack = []
        self._sql = []
        self._values = []
        # self.alias_manager = AliasManager()
        # self.state = State(**settings)

    def as_new(self):
        return Context(**self.state.settings)

    def column_sort_key(self, item):
        return item[0].get_sort_key(self)

    @property
    def scope(self):
        return self.state.scope

    @property
    def parentheses(self):
        return self.state.parentheses

    @property
    def subquery(self):
        return self.state.subquery

    def __call__(self, **overrides):
        if overrides and overrides.get('scope') == self.scope:
            del overrides['scope']

        self.stack.append(self.state)
        self.state = self.state(**overrides)
        return self

    #
    # scope_normal = __scope_context__(SCOPE_NORMAL)
    # scope_source = __scope_context__(SCOPE_SOURCE)
    # scope_values = __scope_context__(SCOPE_VALUES)
    # scope_cte = __scope_context__(SCOPE_CTE)
    # scope_column = __scope_context__(SCOPE_COLUMN)

    def __enter__(self):
        if self.parentheses:
            self.literal('(')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.parentheses:
            self.literal(')')
        self.state = self.stack.pop()

    #
    # @contextmanager
    # def push_alias(self):
    #     self.alias_manager.push()
    #     yield
    #     self.alias_manager.pop()
    #
    def sql(self, obj):
        if isinstance(obj, (Node, Context)):
            return obj.__sql__(self)
        elif is_model(obj):
            return obj._meta.table.__sql__(self)
        else:
            return self.sql(Value(obj))

    def literal(self, keyword):
        self._sql.append(keyword)
        return self

    def value(self, value, converter=None, add_param=True):
        if converter:
            value = converter(value)
        elif converter is None and self.state.converter:
            # Explicitly check for None so that "False" can be used to signify
            # that no conversion should be applied.
            value = self.state.converter(value)

        if isinstance(value, Node):
            with self(converter=None):
                return self.sql(value)
        # elif is_model(value):
        # Under certain circumstances, we could end-up treating a model-
        # class itself as a value. This check ensures that we drop the
        # table alias into the query instead of trying to parameterize a
        # model (for instance, passing a model as a function argument).
        # with self.scope_column():
        #     return self.sql(value)

        self._values.append(value)
        return self.literal(self.state.param or '?') if add_param else self

    def __sql__(self, ctx):
        ctx._sql.extend(self._sql)
        ctx._values.extend(self._values)
        return ctx

    def parse(self, node):
        return self.sql(node).query()

    def query(self):
        return ''.join(self._sql), self._values


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


class _ConnectionLocal(_ConnectionState, threading.local): pass


class _NoopLock(object):
    __slots__ = ()

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb): pass


class ConnectionContext(_callable_context_manager):
    __slots__ = ('db',)

    def __init__(self, db): self.db = db

    def __enter__(self):
        if self.db.is_closed():
            self.db.connect()

    def __exit__(self, exc_type, exc_val, exc_tb): self.db.close()


# DB-API 2.0 EXCEPTIONS.


class PeeweeException(Exception):
    def __init__(self, *args):
        if args and isinstance(args[0], Exception):
            self.orig, args = args[0], args[1:]
        super(PeeweeException, self).__init__(*args)


class ImproperlyConfigured(PeeweeException): pass


class DatabaseError(PeeweeException): pass


class DataError(DatabaseError): pass


class IntegrityError(DatabaseError): pass


class InterfaceError(PeeweeException): pass


class InternalError(DatabaseError): pass


class NotSupportedError(DatabaseError): pass


class OperationalError(DatabaseError): pass


class ProgrammingError(DatabaseError): pass


class ExceptionWrapper(object):
    __slots__ = ('exceptions',)

    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return
        # psycopg2.8 shits out a million cute error types. Try to catch em all.
        if pg_errors is not None and exc_type.__name__ not in self.exceptions \
                and issubclass(exc_type, pg_errors.Error):
            exc_type = exc_type.__bases__[0]
        if exc_type.__name__ in self.exceptions:
            new_type = self.exceptions[exc_type.__name__]
            exc_args = exc_value.args
            reraise(new_type, new_type(exc_value, *exc_args), traceback)


EXCEPTIONS = {
    'ConstraintError': IntegrityError,
    'DatabaseError': DatabaseError,
    'DataError': DataError,
    'IntegrityError': IntegrityError,
    'InterfaceError': InterfaceError,
    'InternalError': InternalError,
    'NotSupportedError': NotSupportedError,
    'OperationalError': OperationalError,
    'ProgrammingError': ProgrammingError,
    'TransactionRollbackError': OperationalError}

__exception_wrapper__ = ExceptionWrapper(EXCEPTIONS)


class Database(_callable_context_manager):
    context_class = Context
    field_types = {}
    operations = {}
    param = '?'
    quote = '""'
    server_version = None

    # Feature toggles.
    commit_select = False
    compound_select_parentheses = CSQ_PARENTHESES_NEVER
    for_update = False
    index_schema_prefix = False
    index_using_precedes_table = False
    limit_max = None
    nulls_ordering = False
    returning_clause = False
    safe_create_index = True
    safe_drop_index = True
    sequences = False
    truncate_table = True

    def __init__(self, database, thread_safe=True, autorollback=False,
                 field_types=None, operations=None,
                 autoconnect=True, **kwargs):
        self._field_types = merge_dict(FIELD, self.field_types)
        self._operations = merge_dict(OP, self.operations)
        if field_types:
            self._field_types.update(field_types)
        if operations:
            self._operations.update(operations)

        self.autoconnect = autoconnect
        self.autorollback = autorollback
        self.thread_safe = thread_safe
        if thread_safe:
            self._state = _ConnectionLocal()
            self._lock = threading.RLock()
        else:
            self._state = _ConnectionState()
            self._lock = _NoopLock()

        self.connect_params = {}
        self.init(database, **kwargs)

    def init(self, database, **kwargs):
        if not self.is_closed():
            self.close()
        self.database = database
        self.connect_params.update(kwargs)
        self.deferred = not bool(database)

    def __enter__(self):
        if self.is_closed():
            self.connect()
        ctx = self.atomic()
        self._state.ctx.append(ctx)
        ctx.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx = self._state.ctx.pop()
        try:
            ctx.__exit__(exc_type, exc_val, exc_tb)
        finally:
            if not self._state.ctx:
                self.close()

    def connection_context(self):
        return ConnectionContext(self)

    def _connect(self):
        raise NotImplementedError

    def connect(self, reuse_if_open=False):
        with self._lock:
            if self.deferred:
                raise InterfaceError('Error, database must be initialized '
                                     'before opening a connection.')
            if not self._state.closed:
                if reuse_if_open:
                    return False
                raise OperationalError('Connection already opened.')

            self._state.reset()
            with __exception_wrapper__:
                self._state.set_connection(self._connect())
                if self.server_version is None:
                    self._set_server_version(self._state.conn)
                self._initialize_connection(self._state.conn)
        return True

    def _initialize_connection(self, conn):
        pass

    def _set_server_version(self, conn):
        self.server_version = 0

    def close(self):
        with self._lock:
            if self.deferred:
                raise InterfaceError('Error, database must be initialized '
                                     'before opening a connection.')
            if self.in_transaction():
                raise OperationalError('Attempting to close database while '
                                       'transaction is open.')
            is_open = not self._state.closed
            try:
                if is_open:
                    with __exception_wrapper__:
                        self._close(self._state.conn)
            finally:
                self._state.reset()
            return is_open

    def _close(self, conn):
        conn.close()

    def is_closed(self):
        return self._state.closed

    def is_connection_usable(self):
        return not self._state.closed

    def connection(self):
        if self.is_closed():
            self.connect()
        return self._state.conn

    def cursor(self, commit=None):
        if self.is_closed():
            if self.autoconnect:
                self.connect()
            else:
                raise InterfaceError('Error, database connection not opened.')
        return self._state.conn.cursor()

    def execute_sql(self, sql, params=None, commit=SENTINEL):
        logger.debug((sql, params))
        if commit is SENTINEL:
            if self.in_transaction():
                commit = False
            elif self.commit_select:
                commit = True
            else:
                commit = not sql[:6].lower().startswith('select')

        with __exception_wrapper__:
            cursor = self.cursor(commit)
            try:
                cursor.execute(sql, params or ())
            except Exception:
                if self.autorollback and not self.in_transaction():
                    self.rollback()
                raise
            else:
                if commit and not self.in_transaction():
                    self.commit()
        return cursor

    def execute(self, query, commit=SENTINEL, **context_options):
        ctx = self.get_sql_context(**context_options)
        sql, params = ctx.sql(query).query()
        return self.execute_sql(sql, params, commit=commit)

    def get_context_options(self):
        return {
            'field_types': self._field_types,
            'operations': self._operations,
            'param': self.param,
            'quote': self.quote,
            'compound_select_parentheses': self.compound_select_parentheses,
            'conflict_statement': self.conflict_statement,
            'conflict_update': self.conflict_update,
            'for_update': self.for_update,
            'index_schema_prefix': self.index_schema_prefix,
            'index_using_precedes_table': self.index_using_precedes_table,
            'limit_max': self.limit_max,
            'nulls_ordering': self.nulls_ordering,
        }

    def get_sql_context(self, **context_options):
        context = self.get_context_options()
        if context_options:
            context.update(context_options)
        return self.context_class(**context)

    def conflict_statement(self, on_conflict, query):
        raise NotImplementedError

    def conflict_update(self, on_conflict, query):
        raise NotImplementedError

    def _build_on_conflict_update(self, on_conflict, query):
        if on_conflict._conflict_target:
            stmt = SQL('ON CONFLICT')
            target = EnclosedNodeList([
                Entity(col) if isinstance(col, basestring) else col
                for col in on_conflict._conflict_target])
            if on_conflict._conflict_where is not None:
                target = NodeList([target, SQL('WHERE'),
                                   on_conflict._conflict_where])
        else:
            stmt = SQL('ON CONFLICT ON CONSTRAINT')
            target = on_conflict._conflict_constraint
            if isinstance(target, basestring):
                target = Entity(target)

        updates = []
        if on_conflict._preserve:
            for column in on_conflict._preserve:
                excluded = NodeList((SQL('EXCLUDED'), ensure_entity(column)),
                                    glue='.')
                expression = NodeList((ensure_entity(column), SQL('='),
                                       excluded))
                updates.append(expression)

        if on_conflict._update:
            for k, v in on_conflict._update.items():
                if not isinstance(v, Node):
                    # Attempt to resolve string field-names to their respective
                    # field object, to apply data-type conversions.
                    if isinstance(k, basestring):
                        k = getattr(query.table, k)
                    if isinstance(k, Field):
                        v = k.to_value(v)
                    else:
                        v = Value(v, unpack=False)
                else:
                    v = QualifiedNames(v)
                updates.append(NodeList((ensure_entity(k), SQL('='), v)))

        parts = [stmt, target, SQL('DO UPDATE SET'), CommaNodeList(updates)]
        if on_conflict._where:
            parts.extend((SQL('WHERE'), QualifiedNames(on_conflict._where)))

        return NodeList(parts)

    def last_insert_id(self, cursor, query_type=None):
        return cursor.lastrowid

    def rows_affected(self, cursor):
        return cursor.rowcount

    def default_values_insert(self, ctx):
        return ctx.literal('DEFAULT VALUES')

    def session_start(self):
        with self._lock:
            return self.transaction().__enter__()

    def session_commit(self):
        with self._lock:
            try:
                txn = self.pop_transaction()
            except IndexError:
                return False
            txn.commit(begin=self.in_transaction())
            return True

    def session_rollback(self):
        with self._lock:
            try:
                txn = self.pop_transaction()
            except IndexError:
                return False
            txn.rollback(begin=self.in_transaction())
            return True

    def in_transaction(self):
        return bool(self._state.transactions)

    def push_transaction(self, transaction):
        self._state.transactions.append(transaction)

    def pop_transaction(self):
        return self._state.transactions.pop()

    def transaction_depth(self):
        return len(self._state.transactions)

    def top_transaction(self):
        if self._state.transactions:
            return self._state.transactions[-1]

    def atomic(self, *args, **kwargs):
        return _atomic(self, *args, **kwargs)

    def manual_commit(self):
        return _manual(self)

    def transaction(self, *args, **kwargs):
        return _transaction(self, *args, **kwargs)

    def savepoint(self):
        return _savepoint(self)

    def begin(self):
        if self.is_closed():
            self.connect()

    def commit(self):
        with __exception_wrapper__:
            return self._state.conn.commit()

    def rollback(self):
        with __exception_wrapper__:
            return self._state.conn.rollback()

    def batch_commit(self, it, n):
        for group in chunked(it, n):
            with self.atomic():
                for obj in group:
                    yield obj

    def table_exists(self, table_name, schema=None):
        return table_name in self.get_tables(schema=schema)

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

    def create_tables(self, models, **options):
        for model in sort_models(models):
            model.create_table(**options)

    def drop_tables(self, models, **kwargs):
        for model in reversed(sort_models(models)):
            model.drop_table(**kwargs)

    def extract_date(self, date_part, date_field):
        raise NotImplementedError

    def truncate_date(self, date_part, date_field):
        raise NotImplementedError

    def to_timestamp(self, date_field):
        raise NotImplementedError

    def from_timestamp(self, date_field):
        raise NotImplementedError

    def random(self):
        return fn.random()

    def bind(self, models, bind_refs=True, bind_backrefs=True):
        for model in models:
            model.bind(self, bind_refs=bind_refs, bind_backrefs=bind_backrefs)

    def bind_ctx(self, models, bind_refs=True, bind_backrefs=True):
        return _BoundModelsContext(models, self, bind_refs, bind_backrefs)

    def get_noop_select(self, ctx):
        return ctx.sql(Select().columns(SQL('0')).where(SQL('0')))


# Sqlite does not support the `date_part` SQL function, so we will define an
# implementation in python.
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


def format_date_time(value, formats, post_process=None):
    post_process = post_process or (lambda x: x)
    for fmt in formats:
        try:
            return post_process(datetime.datetime.strptime(value, fmt))
        except ValueError:
            pass
    return value


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


def __pragma__(name):
    def __get__(self):
        return self.pragma(name)

    def __set__(self, value):
        return self.pragma(name, value)

    return property(__get__, __set__)


class SqliteDatabase(Database):
    field_types = {
        'BIGAUTO': FIELD.AUTO,
        'BIGINT': FIELD.INT,
        'BOOL': FIELD.INT,
        'DOUBLE': FIELD.FLOAT,
        'SMALLINT': FIELD.INT,
        'UUID': FIELD.TEXT}
    operations = {
        'LIKE': 'GLOB',
        'ILIKE': 'LIKE'}
    index_schema_prefix = True
    limit_max = -1
    # server_version = __sqlite_version__
    truncate_table = False

    def __init__(self, database, *args, **kwargs):
        self._pragmas = kwargs.pop('pragmas', ())
        super(SqliteDatabase, self).__init__(database, *args, **kwargs)
        self._aggregates = {}
        self._collations = {}
        self._functions = {}
        self._window_functions = {}
        self._table_functions = []
        self._extensions = set()
        self._attached = {}
        self.register_function(_sqlite_date_part, 'date_part', 2)
        self.register_function(_sqlite_date_trunc, 'date_trunc', 2)
        # self.nulls_ordering = self.server_version >= (3, 30, 0)

    def init(self, database, pragmas=None, timeout=5, **kwargs):
        if pragmas is not None:
            self._pragmas = pragmas
        if isinstance(self._pragmas, dict):
            self._pragmas = list(self._pragmas.items())
        self._timeout = timeout
        super(SqliteDatabase, self).init(database, **kwargs)

    def _set_server_version(self, conn):
        pass

    def _connect(self):
        if sqlite3 is None:
            raise ImproperlyConfigured('SQLite driver not installed!')
        conn = sqlite3.connect(self.database, timeout=self._timeout,
                               isolation_level=None, **self.connect_params)
        try:
            self._add_conn_hooks(conn)
        except:
            conn.close()
            raise
        return conn

    def _add_conn_hooks(self, conn):
        if self._attached:
            self._attach_databases(conn)
        if self._pragmas:
            self._set_pragmas(conn)
        self._load_aggregates(conn)
        self._load_collations(conn)
        self._load_functions(conn)
        if self.server_version >= (3, 25, 0):
            self._load_window_functions(conn)
        if self._table_functions:
            for table_function in self._table_functions:
                table_function.register(conn)
        if self._extensions:
            self._load_extensions(conn)

    def _set_pragmas(self, conn):
        cursor = conn.cursor()
        for pragma, value in self._pragmas:
            cursor.execute('PRAGMA %s = %s;' % (pragma, value))
        cursor.close()

    def _attach_databases(self, conn):
        cursor = conn.cursor()
        for name, db in self._attached.items():
            cursor.execute('ATTACH DATABASE "%s" AS "%s"' % (db, name))
        cursor.close()

    def pragma(self, key, value=SENTINEL, permanent=False, schema=None):
        if schema is not None:
            key = '"%s".%s' % (schema, key)
        sql = 'PRAGMA %s' % key
        if value is not SENTINEL:
            sql += ' = %s' % (value or 0)
            if permanent:
                pragmas = dict(self._pragmas or ())
                pragmas[key] = value
                self._pragmas = list(pragmas.items())
        elif permanent:
            raise ValueError('Cannot specify a permanent pragma without value')
        row = self.execute_sql(sql).fetchone()
        if row:
            return row[0]

    cache_size = __pragma__('cache_size')
    foreign_keys = __pragma__('foreign_keys')
    journal_mode = __pragma__('journal_mode')
    journal_size_limit = __pragma__('journal_size_limit')
    mmap_size = __pragma__('mmap_size')
    page_size = __pragma__('page_size')
    read_uncommitted = __pragma__('read_uncommitted')
    synchronous = __pragma__('synchronous')
    wal_autocheckpoint = __pragma__('wal_autocheckpoint')

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, seconds):
        if self._timeout == seconds:
            return

        self._timeout = seconds
        if not self.is_closed():
            # PySQLite multiplies user timeout by 1000, but the unit of the
            # timeout PRAGMA is actually milliseconds.
            self.execute_sql('PRAGMA busy_timeout=%d;' % (seconds * 1000))

    def _load_aggregates(self, conn):
        for name, (klass, num_params) in self._aggregates.items():
            conn.create_aggregate(name, num_params, klass)

    def _load_collations(self, conn):
        for name, fn in self._collations.items():
            conn.create_collation(name, fn)

    def _load_functions(self, conn):
        for name, (fn, num_params) in self._functions.items():
            conn.create_function(name, num_params, fn)

    def _load_window_functions(self, conn):
        for name, (klass, num_params) in self._window_functions.items():
            conn.create_window_function(name, num_params, klass)

    def register_aggregate(self, klass, name=None, num_params=-1):
        self._aggregates[name or klass.__name__.lower()] = (klass, num_params)
        if not self.is_closed():
            self._load_aggregates(self.connection())

    def aggregate(self, name=None, num_params=-1):
        def decorator(klass):
            self.register_aggregate(klass, name, num_params)
            return klass

        return decorator

    def register_collation(self, fn, name=None):
        name = name or fn.__name__

        def _collation(*args):
            expressions = args + (SQL('collate %s' % name),)
            return NodeList(expressions)

        fn.collation = _collation
        self._collations[name] = fn
        if not self.is_closed():
            self._load_collations(self.connection())

    def collation(self, name=None):
        def decorator(fn):
            self.register_collation(fn, name)
            return fn

        return decorator

    def register_function(self, fn, name=None, num_params=-1):
        self._functions[name or fn.__name__] = (fn, num_params)
        if not self.is_closed():
            self._load_functions(self.connection())

    def func(self, name=None, num_params=-1):
        def decorator(fn):
            self.register_function(fn, name, num_params)
            return fn

        return decorator

    def register_window_function(self, klass, name=None, num_params=-1):
        name = name or klass.__name__.lower()
        self._window_functions[name] = (klass, num_params)
        if not self.is_closed():
            self._load_window_functions(self.connection())

    def window_function(self, name=None, num_params=-1):
        def decorator(klass):
            self.register_window_function(klass, name, num_params)
            return klass

        return decorator

    def register_table_function(self, klass, name=None):
        if name is not None:
            klass.name = name
        self._table_functions.append(klass)
        if not self.is_closed():
            klass.register(self.connection())

    def table_function(self, name=None):
        def decorator(klass):
            self.register_table_function(klass, name)
            return klass

        return decorator

    def unregister_aggregate(self, name):
        del (self._aggregates[name])

    def unregister_collation(self, name):
        del (self._collations[name])

    def unregister_function(self, name):
        del (self._functions[name])

    def unregister_window_function(self, name):
        del (self._window_functions[name])

    def unregister_table_function(self, name):
        for idx, klass in enumerate(self._table_functions):
            if klass.name == name:
                break
        else:
            return False
        self._table_functions.pop(idx)
        return True

    def _load_extensions(self, conn):
        conn.enable_load_extension(True)
        for extension in self._extensions:
            conn.load_extension(extension)

    def load_extension(self, extension):
        self._extensions.add(extension)
        if not self.is_closed():
            conn = self.connection()
            conn.enable_load_extension(True)
            conn.load_extension(extension)

    def unload_extension(self, extension):
        self._extensions.remove(extension)

    def attach(self, filename, name):
        if name in self._attached:
            if self._attached[name] == filename:
                return False
            raise OperationalError('schema "%s" already attached.' % name)

        self._attached[name] = filename
        if not self.is_closed():
            self.execute_sql('ATTACH DATABASE "%s" AS "%s"' % (filename, name))
        return True

    def detach(self, name):
        if name not in self._attached:
            return False

        del self._attached[name]
        if not self.is_closed():
            self.execute_sql('DETACH DATABASE "%s"' % name)
        return True

    def begin(self, lock_type=None):
        statement = 'BEGIN %s' % lock_type if lock_type else 'BEGIN'
        self.execute_sql(statement, commit=False)

    def get_tables(self, schema=None):
        schema = schema or 'main'
        cursor = self.execute_sql('SELECT name FROM "%s".sqlite_master WHERE '
                                  'type=? ORDER BY name' % schema, ('table',))
        return [row for row, in cursor.fetchall()]

    def get_views(self, schema=None):
        sql = ('SELECT name, sql FROM "%s".sqlite_master WHERE type=? '
               'ORDER BY name') % (schema or 'main')
        return [ViewMetadata(*row) for row in self.execute_sql(sql, ('view',))]

    def get_indexes(self, table, schema=None):
        schema = schema or 'main'
        query = ('SELECT name, sql FROM "%s".sqlite_master '
                 'WHERE tbl_name = ? AND type = ? ORDER BY name') % schema
        cursor = self.execute_sql(query, (table, 'index'))
        index_to_sql = dict(cursor.fetchall())

        # Determine which indexes have a unique constraint.
        unique_indexes = set()
        cursor = self.execute_sql('PRAGMA "%s".index_list("%s")' %
                                  (schema, table))
        for row in cursor.fetchall():
            name = row[1]
            is_unique = int(row[2]) == 1
            if is_unique:
                unique_indexes.add(name)

        # Retrieve the indexed columns.
        index_columns = {}
        for index_name in sorted(index_to_sql):
            cursor = self.execute_sql('PRAGMA "%s".index_info("%s")' %
                                      (schema, index_name))
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
        cursor = self.execute_sql('PRAGMA "%s".table_info("%s")' %
                                  (schema or 'main', table))
        return [ColumnMetadata(r[1], r[2], not r[3], bool(r[5]), table, r[4])
                for r in cursor.fetchall()]

    def get_primary_keys(self, table, schema=None):
        cursor = self.execute_sql('PRAGMA "%s".table_info("%s")' %
                                  (schema or 'main', table))
        return [row[1] for row in filter(lambda r: r[-1], cursor.fetchall())]

    def get_foreign_keys(self, table, schema=None):
        cursor = self.execute_sql('PRAGMA "%s".foreign_key_list("%s")' %
                                  (schema or 'main', table))
        return [ForeignKeyMetadata(row[3], row[2], row[4], table)
                for row in cursor.fetchall()]

    def get_binary_type(self):
        return sqlite3.Binary

    def conflict_statement(self, on_conflict, query):
        action = on_conflict._action.lower() if on_conflict._action else ''
        if action and action not in ('nothing', 'update'):
            return SQL('INSERT OR %s' % on_conflict._action.upper())

    def conflict_update(self, oc, query):
        # Sqlite prior to 3.24.0 does not support Postgres-style upsert.
        if self.server_version < (3, 24, 0) and \
                any((oc._preserve, oc._update, oc._where, oc._conflict_target,
                     oc._conflict_constraint)):
            raise ValueError('SQLite does not support specifying which values '
                             'to preserve or update.')

        action = oc._action.lower() if oc._action else ''
        if action and action not in ('nothing', 'update', ''):
            return

        if action == 'nothing':
            return SQL('ON CONFLICT DO NOTHING')
        elif not oc._update and not oc._preserve:
            raise ValueError('If you are not performing any updates (or '
                             'preserving any INSERTed values), then the '
                             'conflict resolution action should be set to '
                             '"NOTHING".')
        elif oc._conflict_constraint:
            raise ValueError('SQLite does not support specifying named '
                             'constraints for conflict resolution.')
        elif not oc._conflict_target:
            raise ValueError('SQLite requires that a conflict target be '
                             'specified when doing an upsert.')

        return self._build_on_conflict_update(oc, query)

    def extract_date(self, date_part, date_field):
        return fn.date_part(date_part, date_field, python_value=int)

    def truncate_date(self, date_part, date_field):
        return fn.date_trunc(date_part, date_field,
                             python_value=simple_date_time)

    def to_timestamp(self, date_field):
        return fn.strftime('%s', date_field).cast('integer')

    def from_timestamp(self, date_field):
        return fn.datetime(date_field, 'unixepoch')


class MetaField(object):
    pass


class ForeignKeyField(object):
    pass


class ManyToManyField(object):
    pass


class Metadata(object):
    def __init__(self, model, database=None, table_name=None, indexes=None,
                 primary_key=None, constraints=None, schema=None,
                 only_save_dirty=False, depends_on=None, options=None,
                 table_function=None, table_settings=None,
                 without_rowid=False, temporary=False, legacy_table_names=True,
                 **kwargs):
        self.model = model
        self.database = database

        self.fields = {}
        self.columns = {}
        self.combined = {}

        # self._sorted_field_list = _SortedFieldList()
        self.sorted_fields = []
        self.sorted_field_names = []

        self.defaults = {}
        self._default_by_name = {}
        self._default_dict = {}
        self._default_callables = {}
        self._default_callable_list = []

        self.name = model.__name__.lower()
        self.table_function = table_function
        self.legacy_table_names = legacy_table_names
        if not table_name:
            table_name = (self.table_function(model)
                          if self.table_function
                          else self.make_table_name())
        self.table_name = table_name
        self._table = None

        self.indexes = list(indexes) if indexes else []
        self.constraints = constraints
        self._schema = schema
        self.primary_key = primary_key
        self.composite_key = self.auto_increment = None
        self.only_save_dirty = only_save_dirty
        self.depends_on = depends_on
        self.table_settings = table_settings
        self.without_rowid = without_rowid
        self.temporary = temporary

        self.refs = {}
        self.backrefs = {}
        # Python中通过Key访问字典，当Key不存在时，会引发‘KeyError’异常。为了避免这种情况的发生，可以使用collections类中的defaultdict()
        # 方法来为字典提供默认值。
        # https://www.baidu.com/link?url=cWaziMn8RlIUyWenAE_79P2PBO6xB4KJEdtrGICHbcBiNGfIJKG1VlRStIY_VUTwE8CKm1LZ-9EmC65KRLov0qowHwClywzTJWFtROXkwL7&wd=&eqid=b432620e000eed290000000660a21faf
        self.model_refs = collections.defaultdict(list)
        self.model_backrefs = collections.defaultdict(list)
        self.manytomany = {}

        self.options = options or {}
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._additional_keys = set(kwargs.keys())
        # 允许对象注册在绑定模型时调用的钩子到另一个数据库。例如，BlobField使用不同的
        # Python数据类型取决于db driver/Python版本。什么时候？
        # 数据库发生变化，我们需要更新任何BlobField以便他们可以使用适当的数据类型。
        # Allow objects to register hooks that are called if the model is bound
        # to a different database. For example, BlobField uses a different
        # Python data-type depending on the db driver / python version. When
        # the database changes, we need to update any BlobField so they can use
        # the appropriate data-type.
        self._db_hooks = []

    def make_table_name(self):
        if self.legacy_table_names:
            return re.sub(r'[^\w]+', '_', self.name)
        return make_snake_case(self.model.__name__)

    def model_graph(self, refs=True, backrefs=True, depth_first=True):
        if not refs and not backrefs:
            raise ValueError('One of `refs` or `backrefs` must be True.')

        accum = [(None, self.model, None)]
        seen = set()
        queue = collections.deque((self,))
        method = queue.pop if depth_first else queue.popleft

        while queue:
            curr = method()
            if curr in seen: continue
            seen.add(curr)

            if refs:
                for fk, model in curr.refs.items():
                    accum.append((fk, model, False))
                    queue.append(model._meta)
            if backrefs:
                for fk, model in curr.backrefs.items():
                    accum.append((fk, model, True))
                    queue.append(model._meta)

        return accum

    def add_ref(self, field):
        rel = field.rel_model
        self.refs[field] = rel
        self.model_refs[rel].append(field)
        rel._meta.backrefs[field] = self.model
        rel._meta.model_backrefs[self.model].append(field)

    def remove_ref(self, field):
        rel = field.rel_model
        del self.refs[field]
        self.model_refs[rel].remove(field)
        del rel._meta.backrefs[field]
        rel._meta.model_backrefs[self.model].remove(field)

    def add_manytomany(self, field):
        self.manytomany[field.name] = field

    def remove_manytomany(self, field):
        del self.manytomany[field.name]

    @property
    def table(self):
        # if self._table is None:
        # self._table = Table(
        #     self.table_name,
        #     [field.column_name for field in self.sorted_fields],
        #     schema=self.schema,
        #     _model=self.model,
        #     _database=self.database)
        return self._table

    @table.setter
    def table(self, value):
        raise AttributeError('Cannot set the "table".')

    @table.deleter
    def table(self):
        self._table = None

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, value):
        self._schema = value
        del self.table

    # @property
    # def entity(self):
    #     if self._schema:
    #         return Entity(self._schema, self.table_name)
    #     else:
    #         return Entity(self.table_name)

    def _update_sorted_fields(self):
        # self.sorted_fields = list(self._sorted_field_list)
        self.sorted_field_names = [f.name for f in self.sorted_fields]

    def get_rel_for_model(self, model):
        # if isinstance(model, ModelAlias):
        #     model = model.model
        forwardrefs = self.model_refs.get(model, [])
        backrefs = self.model_backrefs.get(model, [])
        return (forwardrefs, backrefs)

    def add_field(self, field_name, field, set_attribute=True):
        if field_name in self.fields:
            self.remove_field(field_name)
        elif field_name in self.manytomany:
            self.remove_manytomany(self.manytomany[field_name])

        if not isinstance(field, MetaField):
            del self.table
            field.bind(self.model, field_name, set_attribute)
            self.fields[field.name] = field
            self.columns[field.column_name] = field
            self.combined[field.name] = field
            self.combined[field.column_name] = field

            # self._sorted_field_list.insert(field)
            self._update_sorted_fields()

            if field.default is not None:
                # This optimization helps speed up model instance construction.
                self.defaults[field] = field.default
                # if callable_(field.default):
                #     self._default_callables[field] = field.default
                #     self._default_callable_list.append((field.name,
                #                                         field.default))
                # else:
                #     self._default_dict[field] = field.default
                #     self._default_by_name[field.name] = field.default
        else:
            field.bind(self.model, field_name, set_attribute)

        if isinstance(field, ForeignKeyField):
            self.add_ref(field)
        elif isinstance(field, ManyToManyField) and field.name:
            self.add_manytomany(field)

    def remove_field(self, field_name):
        if field_name not in self.fields:
            return

        del self.table
        original = self.fields.pop(field_name)
        del self.columns[original.column_name]
        del self.combined[field_name]
        try:
            del self.combined[original.column_name]
        except KeyError:
            pass
        self._sorted_field_list.remove(original)
        self._update_sorted_fields()

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

        if isinstance(original, ForeignKeyField):
            self.remove_ref(original)

    def set_primary_key(self, name, field):
        self.composite_key = isinstance(field, CompositeKey)
        self.add_field(name, field)
        self.primary_key = field
        self.auto_increment = (
                field.auto_increment or
                bool(field.sequence))

    def get_primary_keys(self):
        if self.composite_key:
            return tuple([self.fields[field_name]
                          for field_name in self.primary_key.field_names])
        else:
            return (self.primary_key,) if self.primary_key is not False else ()

    def get_default_dict(self):
        dd = self._default_by_name.copy()
        for field_name, default in self._default_callable_list:
            dd[field_name] = default()
        return dd

    def fields_to_index(self):
        indexes = []
        # for f in self.sorted_fields:
        # if f.primary_key:
        #     continue
        # if f.index or f.unique:
        #     indexes.append(ModelIndex(self.model, (f,), unique=f.unique,
        #                               using=f.index_type))

        # for index_obj in self.indexes:
        #     if isinstance(index_obj, Node):
        #         indexes.append(index_obj)
        #     elif isinstance(index_obj, (list, tuple)):
        #         index_parts, unique = index_obj
        #         fields = []
        #         for part in index_parts:
        #             if isinstance(part, basestring):
        #                 fields.append(self.combined[part])
        #             elif isinstance(part, Node):
        #                 fields.append(part)
        #             else:
        #                 raise ValueError('Expected either a field name or a '
        #                                  'subclass of Node. Got: %s' % part)
        #         indexes.append(ModelIndex(self.model, fields, unique=unique))

        return indexes

    def set_database(self, database):
        self.database = database
        self.model._schema._database = database
        del self.table

        # Apply any hooks that have been registered.
        for hook in self._db_hooks:
            hook(database)

    def set_table_name(self, table_name):
        self.table_name = table_name
        del self.table


class FieldAccessor(object):
    def __init__(self, model, field, name):
        self.model = model
        self.field = field
        self.name = name

    def __get__(self, instance, instance_type=None):
        if instance is not None:
            return instance.__data__.get(self.name)
        return self.field

    def __set__(self, instance, value):
        instance.__data__[self.name] = value
        instance._dirty.add(self.name)


class SQL():
    def __init__(self, sql, params=None):
        self.sql = sql
        self.params = params

    def __sql__(self, ctx):
        ctx.literal(self.sql)
        if self.params:
            for param in self.params:
                ctx.value(param, False, add_param=False)
        return ctx


class Field(object):
    _field_counter = 0
    _order = 0
    accessor_class = FieldAccessor
    auto_increment = False
    default_index_type = None
    field_type = 'DEFAULT'
    unpack = True

    def __init__(self, null=False, index=False, unique=False, column_name=None,
                 default=None, primary_key=False, constraints=None,
                 sequence=None, collation=None, unindexed=False, choices=None,
                 help_text=None, verbose_name=None, index_type=None,
                 _hidden=False):

        self.null = null
        self.index = index
        self.unique = unique
        self.column_name = column_name
        self.default = default
        self.primary_key = primary_key
        self.constraints = constraints  # List of column constraints.
        self.sequence = sequence  # Name of sequence, e.g. foo_id_seq.
        self.collation = collation
        self.unindexed = unindexed
        self.choices = choices
        self.help_text = help_text
        self.verbose_name = verbose_name
        self.index_type = index_type or self.default_index_type
        self._hidden = _hidden

        # Used internally for recovering the order in which Fields were defined
        # on the Model class.
        Field._field_counter += 1
        self._order = Field._field_counter
        self._sort_key = (self.primary_key and 1 or 2), self._order

    def __hash__(self):
        return hash(self.name + '.' + self.model.__name__)

    def __repr__(self):
        if hasattr(self, 'model') and getattr(self, 'name', None):
            return '<%s: %s.%s>' % (type(self).__name__,
                                    self.model.__name__,
                                    self.name)
        return '<%s: (unbound)>' % type(self).__name__

    def bind(self, model, name, set_attribute=True):
        self.model = model
        self.name = self.safe_name = name
        self.column_name = self.column_name or name
        if set_attribute:
            setattr(model, name, self.accessor_class(model, self, name))

    # @property
    # def column(self):
    #     return Column(self.model._meta.table, self.column_name)

    def adapt(self, value):
        return value

    def db_value(self, value):
        return value if value is None else self.adapt(value)

    def python_value(self, value):
        return value if value is None else self.adapt(value)

    # def to_value(self, value):
    #     return Value(value, self.db_value, unpack=False)

    def get_sort_key(self, ctx):
        return self._sort_key

    def __sql__(self, ctx):
        return ctx.sql(self.column)

    def get_modifiers(self):
        pass

    def ddl_datatype(self, ctx):
        if ctx and ctx.state.field_types:
            column_type = ctx.state.field_types.get(self.field_type,
                                                    self.field_type)
        else:
            column_type = self.field_type

        modifiers = self.get_modifiers()
        if column_type and modifiers:
            modifier_literal = ', '.join([str(m) for m in modifiers])
            return SQL('%s(%s)' % (column_type, modifier_literal))
        else:
            return SQL(column_type)

    def ddl(self, ctx):
        # accum = [Entity(self.column_name)]
        data_type = self.ddl_datatype(ctx)
        # if data_type:
        #     accum.append(data_type)
        # if self.unindexed:
        #     accum.append(SQL('UNINDEXED'))
        # if not self.null:
        #     accum.append(SQL('NOT NULL'))
        # if self.primary_key:
        #     accum.append(SQL('PRIMARY KEY'))
        # if self.sequence:
        #     accum.append(SQL("DEFAULT NEXTVAL('%s')" % self.sequence))
        # if self.constraints:
        #     accum.extend(self.constraints)
        # if self.collation:
        #     accum.append(SQL('COLLATE %s' % self.collation))
        # return NodeList(accum)


class IntegerField(Field):
    field_type = 'INT'

    def adapt(self, value):
        try:
            return int(value)
        except ValueError:
            return value


class BigIntegerField(IntegerField):
    field_type = 'BIGINT'


class SmallIntegerField(IntegerField):
    field_type = 'SMALLINT'


class AutoField(IntegerField):
    auto_increment = True
    field_type = 'AUTO'

    def __init__(self, *args, **kwargs):
        if kwargs.get('primary_key') is False:
            raise ValueError('%s must always be a primary key.' % type(self))
        kwargs['primary_key'] = True
        super(AutoField, self).__init__(*args, **kwargs)


class BigAutoField(AutoField):
    field_type = 'BIGAUTO'


class PrimaryKeyField(AutoField):
    def __init__(self, *args, **kwargs):
        __deprecated__('"PrimaryKeyField" has been renamed to "AutoField". '
                       'Please update your code accordingly as this will be '
                       'completely removed in a subsequent release.')
        super(PrimaryKeyField, self).__init__(*args, **kwargs)


class StringExpression(object):
    pass


class _StringField(Field):
    def adapt(self, value):
        if isinstance(value, text_type):
            return value
        elif isinstance(value, bytes_type):
            return value.decode('utf-8')
        return text_type(value)

    def __add__(self, other):
        return StringExpression(self, OP.CONCAT, other)

    def __radd__(self, other):
        return StringExpression(other, OP.CONCAT, self)


class CharField(_StringField):
    field_type = 'VARCHAR'

    def __init__(self, max_length=255, *args, **kwargs):
        self.max_length = max_length
        super(CharField, self).__init__(*args, **kwargs)

    def get_modifiers(self):
        return self.max_length and [self.max_length] or None


class FixedCharField(CharField):
    field_type = 'CHAR'

    def python_value(self, value):
        value = super(FixedCharField, self).python_value(value)
        if value:
            value = value.strip()
        return value


class TextField(_StringField):
    field_type = 'TEXT'


class ForeignKeyField(Field):
    # accessor_class = ForeignKeyAccessor

    def __init__(self, model, field=None, backref=None, on_delete=None,
                 on_update=None, deferrable=None, _deferred=None,
                 object_id_name=None, lazy_load=True, constraint_name=None,
                 *args, **kwargs):
        kwargs.setdefault('index', True)

        super(ForeignKeyField, self).__init__(*args, **kwargs)

        # if rel_model is not None:
        #     __deprecated__('"rel_model" has been deprecated in favor of '
        #                    '"model" for ForeignKeyField objects.')
        #     model = rel_model
        # if to_field is not None:
        #     __deprecated__('"to_field" has been deprecated in favor of '
        #                    '"field" for ForeignKeyField objects.')
        #     field = to_field
        # if related_name is not None:
        #     __deprecated__('"related_name" has been deprecated in favor of '
        #                    '"backref" for Field objects.')
        #     backref = related_name

        self._is_self_reference = model == 'self'
        self.rel_model = model
        self.rel_field = field
        self.declared_backref = backref
        self.backref = None
        self.on_delete = on_delete
        self.on_update = on_update
        self.deferrable = deferrable
        self.deferred = _deferred
        self.object_id_name = object_id_name
        self.lazy_load = lazy_load
        self.constraint_name = constraint_name

    @property
    def field_type(self):
        if not isinstance(self.rel_field, AutoField):
            return self.rel_field.field_type
        elif isinstance(self.rel_field, BigAutoField):
            return BigIntegerField.field_type
        return IntegerField.field_type

    def get_modifiers(self):
        if not isinstance(self.rel_field, AutoField):
            return self.rel_field.get_modifiers()
        return super(ForeignKeyField, self).get_modifiers()

    def adapt(self, value):
        return self.rel_field.adapt(value)

    def db_value(self, value):
        if isinstance(value, self.rel_model):
            value = getattr(value, self.rel_field.name)
        return self.rel_field.db_value(value)

    def python_value(self, value):
        if isinstance(value, self.rel_model):
            return value
        return self.rel_field.python_value(value)

    def bind(self, model, name, set_attribute=True):
        if not self.column_name:
            self.column_name = name if name.endswith('_id') else name + '_id'
        if not self.object_id_name:
            self.object_id_name = self.column_name
            if self.object_id_name == name:
                self.object_id_name += '_id'
        elif self.object_id_name == name:
            raise ValueError('ForeignKeyField "%s"."%s" specifies an '
                             'object_id_name that conflicts with its field '
                             'name.' % (model._meta.name, name))
        if self._is_self_reference:
            self.rel_model = model
        if isinstance(self.rel_field, basestring):
            self.rel_field = getattr(self.rel_model, self.rel_field)
        elif self.rel_field is None:
            self.rel_field = self.rel_model._meta.primary_key

        # Bind field before assigning backref, so field is bound when
        # calling declared_backref() (if callable).
        super(ForeignKeyField, self).bind(model, name, set_attribute)
        self.safe_name = self.object_id_name

        if callable_(self.declared_backref):
            self.backref = self.declared_backref(self)
        else:
            self.backref, self.declared_backref = self.declared_backref, None
        if not self.backref:
            self.backref = '%s_set' % model._meta.name

        if set_attribute:
            setattr(model, self.object_id_name, ObjectIdAccessor(self))
            if self.backref not in '!+':
                setattr(self.rel_model, self.backref, BackrefAccessor(self))

    def foreign_key_constraint(self):
        parts = []
        if self.constraint_name:
            parts.extend((SQL('CONSTRAINT'), Entity(self.constraint_name)))
        parts.extend([
            SQL('FOREIGN KEY'),
            EnclosedNodeList((self,)),
            SQL('REFERENCES'),
            self.rel_model,
            EnclosedNodeList((self.rel_field,))])
        if self.on_delete:
            parts.append(SQL('ON DELETE %s' % self.on_delete))
        if self.on_update:
            parts.append(SQL('ON UPDATE %s' % self.on_update))
        if self.deferrable:
            parts.append(SQL('DEFERRABLE %s' % self.deferrable))
        return NodeList(parts)

    def __getattr__(self, attr):
        if attr.startswith('__'):
            # Prevent recursion error when deep-copying.
            raise AttributeError('Cannot look-up non-existant "__" methods.')
        if attr in self.rel_model._meta.fields:
            return self.rel_model._meta.fields[attr]
        raise AttributeError('Foreign-key has no attribute %s, nor is it a '
                             'valid field on the related model.' % attr)


class DeferredForeignKey(Field):
    _unresolved = set()

    def __init__(self, rel_model_name, **kwargs):
        self.field_kwargs = kwargs
        self.rel_model_name = rel_model_name.lower()
        DeferredForeignKey._unresolved.add(self)
        super(DeferredForeignKey, self).__init__(
            column_name=kwargs.get('column_name'),
            null=kwargs.get('null'))

    __hash__ = object.__hash__

    def __deepcopy__(self, memo=None):
        return DeferredForeignKey(self.rel_model_name, **self.field_kwargs)

    def set_model(self, rel_model):
        field = ForeignKeyField(rel_model, _deferred=True, **self.field_kwargs)
        self.model._meta.add_field(self.name, field)

    @staticmethod
    def resolve(model_cls):
        unresolved = sorted(DeferredForeignKey._unresolved,
                            key=operator.attrgetter('_order'))
        for dr in unresolved:
            if dr.rel_model_name == model_cls.__name__.lower():
                dr.set_model(model_cls)
                DeferredForeignKey._unresolved.discard(dr)


class DoesNotExist(object):
    pass


class DeferredForeignKey(object):
    pass


class CompositeKey(object):
    pass


class AutoField(Field):
    pass


class SchemaManager(object):
    """数据库结构管理器"""

    def __init__(self, model, database=None, **context_options):
        self.model = model
        self._database = database
        context_options.setdefault('scope', SCOPE_VALUES)
        self.context_options = context_options

    @property
    def database(self):
        db = self._database or self.model._meta.database
        if db is None:
            raise ImproperlyConfigured('database attribute does not appear to '
                                       'be set on the model: %s' % self.model)
        return db

    @database.setter
    def database(self, value):
        self._database = value

    def _create_context(self):
        return self.database.get_sql_context(**self.context_options)

    def _create_table(self, safe=True, **options):
        is_temp = options.pop('temporary', False)
        ctx = self._create_context()
        ctx.literal('CREATE TEMPORARY TABLE ' if is_temp else 'CREATE TABLE ')
        if safe:
            ctx.literal('IF NOT EXISTS ')
        ctx.sql(self.model).literal(' ')

        columns = []
        constraints = []
        meta = self.model._meta
        if meta.composite_key:
            pk_columns = [meta.fields[field_name].column
                          for field_name in meta.primary_key.field_names]
            constraints.append(NodeList((SQL('PRIMARY KEY'),
                                         EnclosedNodeList(pk_columns))))

        for field in meta.sorted_fields:
            columns.append(field.ddl(ctx))
            if isinstance(field, ForeignKeyField) and not field.deferred:
                constraints.append(field.foreign_key_constraint())

        if meta.constraints:
            constraints.extend(meta.constraints)

        constraints.extend(self._create_table_option_sql(options))
        ctx.sql(EnclosedNodeList(columns + constraints))

        if meta.table_settings is not None:
            table_settings = ensure_tuple(meta.table_settings)
            for setting in table_settings:
                if not isinstance(setting, basestring):
                    raise ValueError('table_settings must be strings')
                ctx.literal(' ').literal(setting)

        if meta.without_rowid:
            ctx.literal(' WITHOUT ROWID')
        return ctx

    def _create_table_option_sql(self, options):
        accum = []
        options = merge_dict(self.model._meta.options or {}, options)
        if not options:
            return accum

        for key, value in sorted(options.items()):
            if not isinstance(value, Node):
                if is_model(value):
                    value = value._meta.table
                else:
                    value = SQL(str(value))
            accum.append(NodeList((SQL(key), value), glue='='))
        return accum

    def create_table(self, safe=True, **options):
        self.database.execute(self._create_table(safe=safe, **options))

    def _create_table_as(self, table_name, query, safe=True, **meta):
        ctx = (self._create_context()
               .literal('CREATE TEMPORARY TABLE '
                        if meta.get('temporary') else 'CREATE TABLE '))
        if safe:
            ctx.literal('IF NOT EXISTS ')
        return (ctx
                .sql(Entity(table_name))
                .literal(' AS ')
                .sql(query))

    def create_table_as(self, table_name, query, safe=True, **meta):
        ctx = self._create_table_as(table_name, query, safe=safe, **meta)
        self.database.execute(ctx)

    def _drop_table(self, safe=True, **options):
        ctx = (self._create_context()
               .literal('DROP TABLE IF EXISTS ' if safe else 'DROP TABLE ')
               .sql(self.model))
        if options.get('cascade'):
            ctx = ctx.literal(' CASCADE')
        elif options.get('restrict'):
            ctx = ctx.literal(' RESTRICT')
        return ctx

    def drop_table(self, safe=True, **options):
        self.database.execute(self._drop_table(safe=safe, **options))

    def _truncate_table(self, restart_identity=False, cascade=False):
        db = self.database
        if not db.truncate_table:
            return (self._create_context()
                    .literal('DELETE FROM ').sql(self.model))

        ctx = self._create_context().literal('TRUNCATE TABLE ').sql(self.model)
        if restart_identity:
            ctx = ctx.literal(' RESTART IDENTITY')
        if cascade:
            ctx = ctx.literal(' CASCADE')
        return ctx

    def truncate_table(self, restart_identity=False, cascade=False):
        self.database.execute(self._truncate_table(restart_identity, cascade))

    def _create_indexes(self, safe=True):
        return [self._create_index(index, safe)
                for index in self.model._meta.fields_to_index()]

    def _create_index(self, index, safe=True):
        if isinstance(index, Index):
            if not self.database.safe_create_index:
                index = index.safe(False)
            elif index._safe != safe:
                index = index.safe(safe)
        return self._create_context().sql(index)

    def create_indexes(self, safe=True):
        for query in self._create_indexes(safe=safe):
            self.database.execute(query)

    def _drop_indexes(self, safe=True):
        return [self._drop_index(index, safe)
                for index in self.model._meta.fields_to_index()
                if isinstance(index, Index)]

    def _drop_index(self, index, safe):
        statement = 'DROP INDEX '
        if safe and self.database.safe_drop_index:
            statement += 'IF EXISTS '
        if isinstance(index._table, Table) and index._table._schema:
            index_name = Entity(index._table._schema, index._name)
        else:
            index_name = Entity(index._name)
        return (self
                ._create_context()
                .literal(statement)
                .sql(index_name))

    def drop_indexes(self, safe=True):
        for query in self._drop_indexes(safe=safe):
            self.database.execute(query)

    def _check_sequences(self, field):
        if not field.sequence or not self.database.sequences:
            raise ValueError('Sequences are either not supported, or are not '
                             'defined for "%s".' % field.name)

    def _sequence_for_field(self, field):
        if field.model._meta.schema:
            return Entity(field.model._meta.schema, field.sequence)
        else:
            return Entity(field.sequence)

    def _create_sequence(self, field):
        self._check_sequences(field)
        if not self.database.sequence_exists(field.sequence):
            return (self
                    ._create_context()
                    .literal('CREATE SEQUENCE ')
                    .sql(self._sequence_for_field(field)))

    def create_sequence(self, field):
        seq_ctx = self._create_sequence(field)
        if seq_ctx is not None:
            self.database.execute(seq_ctx)

    def _drop_sequence(self, field):
        self._check_sequences(field)
        if self.database.sequence_exists(field.sequence):
            return (self
                    ._create_context()
                    .literal('DROP SEQUENCE ')
                    .sql(self._sequence_for_field(field)))

    def drop_sequence(self, field):
        seq_ctx = self._drop_sequence(field)
        if seq_ctx is not None:
            self.database.execute(seq_ctx)

    def _create_foreign_key(self, field):
        name = 'fk_%s_%s_refs_%s' % (field.model._meta.table_name,
                                     field.column_name,
                                     field.rel_model._meta.table_name)
        return (self
                ._create_context()
                .literal('ALTER TABLE ')
                .sql(field.model)
                .literal(' ADD CONSTRAINT ')
                .sql(Entity(_truncate_constraint_name(name)))
                .literal(' ')
                .sql(field.foreign_key_constraint()))

    def create_foreign_key(self, field):
        self.database.execute(self._create_foreign_key(field))

    def create_sequences(self):
        if self.database.sequences:
            for field in self.model._meta.sorted_fields:
                if field.sequence:
                    self.create_sequence(field)

    def create_all(self, safe=True, **table_options):
        self.create_sequences()
        self.create_table(safe, **table_options)
        self.create_indexes(safe=safe)

    def drop_sequences(self):
        if self.database.sequences:
            for field in self.model._meta.sorted_fields:
                if field.sequence:
                    self.drop_sequence(field)

    def drop_all(self, safe=True, drop_sequences=True, **options):
        self.drop_table(safe, **options)
        if drop_sequences:
            self.drop_sequences()


class ModelMetaclass(type):
    inheritable = set(['constraints', 'database', 'indexes', 'primary_key',
                       'options', 'schema', 'table_function', 'temporary',
                       'only_save_dirty', 'legacy_table_names',
                       'table_settings'])

    def __new__(cls, name, bases, attrs):
        # if name == "Model" or bases[0].__name__ == "ModelMetaclass":
        if name == "Model":
            if bases:
                print("bases[0]", bases[0])
            return super().__new__(cls, name, bases, attrs)
        # Meta类的属性通过meta_options存储在类中
        meta_options = {}
        meta = attrs.pop('Meta', None)
        if meta:
            for k, v in meta.__dict__.items():
                if not k.startswith('_'):  # 将Meta从属性中移除，将Meta中的非私有属性加入meta_options中
                    meta_options[k] = v
        # 从meta中获取主键信息
        pk = getattr(meta, 'primary_key', None)
        pk_name = parent_pk = None
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
            print("bases[0]", bases[0])
            if not hasattr(b, '_meta'):
                continue

            base_meta = b._meta
            if parent_pk is None:
                parent_pk = deepcopy(base_meta.primary_key)
            all_inheritable = cls.inheritable | base_meta._additional_keys
            # 获取父类中的Meta内部类字段，只考虑all_inheritable中的字段
            for k in base_meta.__dict__:
                if k in all_inheritable and k not in meta_options:
                    meta_options[k] = base_meta.__dict__[k]
            meta_options.setdefault('schema', base_meta.schema)
            # 获取父类中的Fields, 即表的字段
            for (k, v) in b.__dict__.items():
                print("k", k, "v", v)
                if k in attrs: continue

                if isinstance(v, Field) and not v.field.primary_key:
                    attrs[k] = deepcopy(v.field)

        sopts = meta_options.pop('schema_options', None) or {}
        Meta = meta_options.get('model_metadata_class', Metadata)
        Schema = meta_options.get('schema_manager_class', SchemaManager)

        # Construct the new class.
        cls = super().__new__(cls, name, bases, attrs)
        cls.__data__ = cls.__rel__ = None

        cls._meta = Meta(cls, **meta_options)
        cls._schema = Schema(cls, **sopts)

        fields = []
        for key, value in cls.__dict__.items():
            if isinstance(value, Field):
                if value.primary_key and pk:
                    raise ValueError('over-determined primary key %s.' % name)
                elif value.primary_key:
                    pk, pk_name = value, key
                else:
                    fields.append((key, value))
        # 默认表名的设定，Model名的小写，然后将非数字和英文字符换成'_'
        if pk is None:
            if parent_pk is not False:
                pk, pk_name = ((parent_pk, parent_pk.name)
                               if parent_pk is not None else
                               (AutoField(), 'id'))
            else:
                pk = False
        elif isinstance(pk, CompositeKey):
            pk_name = '__composite_key__'
            cls._meta.composite_key = True

        if pk is not False:
            cls._meta.set_primary_key(pk_name, pk)

        for name, field in fields:
            cls._meta.add_field(name, field)
        # 在完成之前创建repr和error类。
        # Create a repr and error class before finalizing.
        if hasattr(cls, '__str__') and '__repr__' not in attrs:
            setattr(cls, '__repr__', lambda self: '<%s: %s>' % (
                cls.__name__, self.__str__()))

        exc_name = '%sDoesNotExist' % cls.__name__
        exc_attrs = {'__module__': cls.__module__}
        exception_class = type(exc_name, (DoesNotExist,), exc_attrs)
        cls.DoesNotExist = exception_class
        # 调用验证钩子，允许额外的模型验证。
        # Call validation hook, allowing additional model validation.
        cls.validate_model()
        # DeferredForeignKey.resolve(cls)
        return cls

    def __repr__(self):
        return '<Model: %s>' % self.__name__

    def __iter__(self):
        return iter(self.select())

    def __getitem__(self, key):
        return self.get_by_id(key)

    def __setitem__(self, key, value):
        self.set_by_id(key, value)

    def __delitem__(self, key):
        self.delete_by_id(key)

    def __contains__(self, key):
        try:
            self.get_by_id(key)
        except self.DoesNotExist:
            return False
        else:
            return True

    def __len__(self):
        return self.select().count()

    def __bool__(self):
        return True

    __nonzero__ = __bool__  # Python 2.

    def __sql__(self, ctx):
        return ctx.sql(self._meta.table)


class IntegrityError(object):
    pass


def database_required(method):
    @wraps(method)
    def inner(self, database=None, *args, **kwargs):
        database = self._database if database is None else database
        if not database:
            raise InterfaceError('Query must be bound to a database in order '
                                 'to call "%s".' % method.__name__)
        return method(self, database, *args, **kwargs)

    return inner


class ResultIterator(object):
    def __init__(self, cursor_wrapper):
        self.cursor_wrapper = cursor_wrapper
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index < self.cursor_wrapper.count:
            obj = self.cursor_wrapper.row_cache[self.index]
        elif not self.cursor_wrapper.populated:
            self.cursor_wrapper.iterate()
            obj = self.cursor_wrapper.row_cache[self.index]
        else:
            raise StopIteration
        self.index += 1
        return obj

    __next__ = next


class CursorWrapper(object):
    def __init__(self, cursor):
        self.cursor = cursor
        self.count = 0
        self.index = 0
        self.initialized = False
        self.populated = False
        self.row_cache = []

    def __iter__(self):
        if self.populated:
            return iter(self.row_cache)
        return ResultIterator(self)

    def __getitem__(self, item):
        if isinstance(item, slice):
            stop = item.stop
            if stop is None or stop < 0:
                self.fill_cache()
            else:
                self.fill_cache(stop)
            return self.row_cache[item]
        elif isinstance(item, int):
            self.fill_cache(item if item > 0 else 0)
            return self.row_cache[item]
        else:
            raise ValueError('CursorWrapper only supports integer and slice '
                             'indexes.')

    def __len__(self):
        self.fill_cache()
        return self.count

    def initialize(self):
        pass

    def iterate(self, cache=True):
        row = self.cursor.fetchone()
        if row is None:
            self.populated = True
            self.cursor.close()
            raise StopIteration
        elif not self.initialized:
            self.initialize()  # Lazy initialization.
            self.initialized = True
        self.count += 1
        result = self.process_row(row)
        if cache:
            self.row_cache.append(result)
        return result

    def process_row(self, row):
        return row

    def iterator(self):
        """Efficient one-pass iteration over the result set."""
        while True:
            try:
                yield self.iterate(False)
            except StopIteration:
                return

    def fill_cache(self, n=0):
        n = n or float('Inf')
        if n < 0:
            raise ValueError('Negative values are not supported.')

        iterator = ResultIterator(self)
        iterator.index = self.count
        while not self.populated and (n > self.count):
            try:
                iterator.next()
            except StopIteration:
                break


class DictCursorWrapper(CursorWrapper):
    def _initialize_columns(self):
        description = self.cursor.description
        self.columns = [t[0][t[0].find('.') + 1:].strip('")')
                        for t in description]
        self.ncols = len(description)

    initialize = _initialize_columns

    def _row_to_dict(self, row):
        result = {}
        for i in range(self.ncols):
            result.setdefault(self.columns[i], row[i])  # Do not overwrite.
        return result

    process_row = _row_to_dict


class BaseQuery(Node):
    default_row_type = ROW.DICT

    def __init__(self, _database=None, **kwargs):
        self._database = _database
        self._cursor_wrapper = None
        self._row_type = None
        self._constructor = None
        super(BaseQuery, self).__init__(**kwargs)

    def bind(self, database=None):
        self._database = database
        return self

    def clone(self):
        query = super(BaseQuery, self).clone()
        query._cursor_wrapper = None
        return query

    @Node.copy
    def dicts(self, as_dict=True):
        self._row_type = ROW.DICT if as_dict else None
        return self

    @Node.copy
    def tuples(self, as_tuple=True):
        self._row_type = ROW.TUPLE if as_tuple else None
        return self

    @Node.copy
    def namedtuples(self, as_namedtuple=True):
        self._row_type = ROW.NAMED_TUPLE if as_namedtuple else None
        return self

    @Node.copy
    def objects(self, constructor=None):
        self._row_type = ROW.CONSTRUCTOR if constructor else None
        self._constructor = constructor
        return self

    def _get_cursor_wrapper(self, cursor):
        row_type = self._row_type or self.default_row_type

        if row_type == ROW.DICT:
            return DictCursorWrapper(cursor)
        elif row_type == ROW.TUPLE:
            return CursorWrapper(cursor)
        elif row_type == ROW.NAMED_TUPLE:
            return NamedTupleCursorWrapper(cursor)
        elif row_type == ROW.CONSTRUCTOR:
            return ObjectCursorWrapper(cursor, self._constructor)
        else:
            raise ValueError('Unrecognized row type: "%s".' % row_type)

    def __sql__(self, ctx):
        raise NotImplementedError

    def sql(self):
        if self._database:
            context = self._database.get_sql_context()
        else:
            context = Context()
        return context.parse(self)

    @database_required
    def execute(self, database):
        return self._execute(database)

    def _execute(self, database):
        raise NotImplementedError

    def iterator(self, database=None):
        return iter(self.execute(database).iterator())

    def _ensure_execution(self):
        if not self._cursor_wrapper:
            if not self._database:
                raise ValueError('Query has not been executed.')
            self.execute()

    def __iter__(self):
        self._ensure_execution()
        return iter(self._cursor_wrapper)

    def __getitem__(self, value):
        self._ensure_execution()
        if isinstance(value, slice):
            index = value.stop
        else:
            index = value
        if index is not None:
            index = index + 1 if index >= 0 else 0
        self._cursor_wrapper.fill_cache(index)
        return self._cursor_wrapper.row_cache[value]

    def __len__(self):
        self._ensure_execution()
        return len(self._cursor_wrapper)

    def __str__(self):
        return query_to_string(self)


class Query(BaseQuery):
    def __init__(self, where=None, order_by=None, limit=None, offset=None,
                 **kwargs):
        super(Query, self).__init__(**kwargs)
        self._where = where
        self._order_by = order_by
        self._limit = limit
        self._offset = offset

        self._cte_list = None

    @Node.copy
    def with_cte(self, *cte_list):
        self._cte_list = cte_list

    @Node.copy
    def where(self, *expressions):
        if self._where is not None:
            expressions = (self._where,) + expressions
        self._where = reduce(operator.and_, expressions)

    @Node.copy
    def orwhere(self, *expressions):
        if self._where is not None:
            expressions = (self._where,) + expressions
        self._where = reduce(operator.or_, expressions)

    @Node.copy
    def order_by(self, *values):
        self._order_by = values

    @Node.copy
    def order_by_extend(self, *values):
        self._order_by = ((self._order_by or ()) + values) or None

    @Node.copy
    def limit(self, value=None):
        self._limit = value

    @Node.copy
    def offset(self, value=None):
        self._offset = value

    @Node.copy
    def paginate(self, page, paginate_by=20):
        if page > 0:
            page -= 1
        self._limit = paginate_by
        self._offset = page * paginate_by

    def _apply_ordering(self, ctx):
        if self._order_by:
            (ctx
             .literal(' ORDER BY ')
             .sql(CommaNodeList(self._order_by)))
        if self._limit is not None or (self._offset is not None and
                                       ctx.state.limit_max):
            limit = ctx.state.limit_max if self._limit is None else self._limit
            ctx.literal(' LIMIT ').sql(limit)
        if self._offset is not None:
            ctx.literal(' OFFSET ').sql(self._offset)
        return ctx

    def __sql__(self, ctx):
        if self._cte_list:
            # The CTE scope is only used at the very beginning of the query,
            # when we are describing the various CTEs we will be using.
            recursive = any(cte._recursive for cte in self._cte_list)

            # Explicitly disable the "subquery" flag here, so as to avoid
            # unnecessary parentheses around subsequent selects.
            with ctx.scope_cte(subquery=False):
                (ctx
                 .literal('WITH RECURSIVE ' if recursive else 'WITH ')
                 .sql(CommaNodeList(self._cte_list))
                 .literal(' '))
        return ctx


class _WriteQuery(Query):
    def __init__(self, table, returning=None, **kwargs):
        self.table = table
        self._returning = returning
        self._return_cursor = True if returning else False
        super(_WriteQuery, self).__init__(**kwargs)

    @Node.copy
    def returning(self, *returning):
        self._returning = returning
        self._return_cursor = True if returning else False

    def apply_returning(self, ctx):
        if self._returning:
            with ctx.scope_source():
                ctx.literal(' RETURNING ').sql(CommaNodeList(self._returning))
        return ctx

    def _execute(self, database):
        if self._returning:
            cursor = self.execute_returning(database)
        else:
            cursor = database.execute(self)
        return self.handle_result(database, cursor)

    def execute_returning(self, database):
        if self._cursor_wrapper is None:
            cursor = database.execute(self)
            self._cursor_wrapper = self._get_cursor_wrapper(cursor)
        return self._cursor_wrapper

    def handle_result(self, database, cursor):
        if self._return_cursor:
            return cursor
        return database.rows_affected(cursor)

    def _set_table_alias(self, ctx):
        ctx.alias_manager[self.table] = self.table.__name__

    def __sql__(self, ctx):
        super(_WriteQuery, self).__sql__(ctx)
        # We explicitly set the table alias to the table's name, which ensures
        # that if a sub-select references a column on the outer table, we won't
        # assign it a new alias (e.g. t2) but will refer to it as table.column.
        self._set_table_alias(ctx)
        return ctx


class Update(_WriteQuery):
    def __init__(self, table, update=None, **kwargs):
        super(Update, self).__init__(table, **kwargs)
        self._update = update
        self._from = None

    @Node.copy
    def from_(self, *sources):
        self._from = sources

    def __sql__(self, ctx):
        super(Update, self).__sql__(ctx)

        with ctx.scope_values(subquery=True):
            ctx.literal('UPDATE ')

            expressions = []
            for k, v in sorted(self._update.items(), key=ctx.column_sort_key):
                if not isinstance(v, Node):
                    if isinstance(k, Field):
                        v = k.to_value(v)
                    else:
                        v = Value(v, unpack=False)
                if not isinstance(v, Value):
                    v = qualify_names(v)
                expressions.append(NodeList((k, SQL('='), v)))

            (ctx
             .sql(self.table)
             .literal(' SET ')
             .sql(CommaNodeList(expressions)))

            if self._from:
                with ctx.scope_source(parentheses=False):
                    ctx.literal(' FROM ').sql(CommaNodeList(self._from))

            if self._where:
                with ctx.scope_normal():
                    ctx.literal(' WHERE ').sql(self._where)
            self._apply_ordering(ctx)
            return self.apply_returning(ctx)


class _ModelQueryHelper(object):
    default_row_type = ROW.MODEL

    def __init__(self, *args, **kwargs):
        super(_ModelQueryHelper, self).__init__(*args, **kwargs)
        if not self._database:
            self._database = self.model._meta.database

    @Node.copy
    def objects(self, constructor=None):
        self._row_type = ROW.CONSTRUCTOR
        self._constructor = self.model if constructor is None else constructor

    def _get_cursor_wrapper(self, cursor):
        row_type = self._row_type or self.default_row_type
        if row_type == ROW.MODEL:
            return self._get_model_cursor_wrapper(cursor)
        elif row_type == ROW.DICT:
            return ModelDictCursorWrapper(cursor, self.model, self._returning)
        elif row_type == ROW.TUPLE:
            return ModelTupleCursorWrapper(cursor, self.model, self._returning)
        elif row_type == ROW.NAMED_TUPLE:
            return ModelNamedTupleCursorWrapper(cursor, self.model,
                                                self._returning)
        elif row_type == ROW.CONSTRUCTOR:
            return ModelObjectCursorWrapper(cursor, self.model,
                                            self._returning, self._constructor)
        else:
            raise ValueError('Unrecognized row type: "%s".' % row_type)

    def _get_model_cursor_wrapper(self, cursor):
        return ModelObjectCursorWrapper(cursor, self.model, [], self.model)


class _ModelWriteQueryHelper(_ModelQueryHelper):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(_ModelWriteQueryHelper, self).__init__(model, *args, **kwargs)

    def returning(self, *returning):
        accum = []
        for item in returning:
            if is_model(item):
                accum.extend(item._meta.sorted_fields)
            else:
                accum.append(item)
        return super(_ModelWriteQueryHelper, self).returning(*accum)

    def _set_table_alias(self, ctx):
        table = self.model._meta.table
        ctx.alias_manager[table] = table.__name__


class ModelUpdate(_ModelWriteQueryHelper, Update):
    pass


class Model(metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        if kwargs.pop('__no_default__', None):
            self.__data__ = {}
        else:
            self.__data__ = self._meta.get_default_dict()
        self._dirty = set(self.__data__)
        self.__rel__ = {}

        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __str__(self):
        return str(self._pk) if self._meta.primary_key is not False else 'n/a'

    @classmethod
    def validate_model(cls):
        pass

    # @classmethod
    # def alias(cls, alias=None):
    #     return ModelAlias(cls, alias)

    #     @classmethod
    # def select(cls, *fields):
    #     is_default = not fields
    #     if not fields:
    #         fields = cls._meta.sorted_fields
    #     return ModelSelect(cls, fields, is_default=is_default)

    @classmethod
    def _normalize_data(cls, data, kwargs):
        normalized = {}
        if data:
            if not isinstance(data, dict):
                if kwargs:
                    raise ValueError('Data cannot be mixed with keyword '
                                     'arguments: %s' % data)
                return data
            for key in data:
                try:
                    field = (key if isinstance(key, Field)
                             else cls._meta.combined[key])
                except KeyError:
                    # if not isinstance(key, Node):
                    #     raise ValueError('Unrecognized field name: "%s" in %s.'
                    #                      % (key, data))
                    field = key
                normalized[field] = data[key]
        if kwargs:
            for key in kwargs:
                try:
                    normalized[cls._meta.combined[key]] = kwargs[key]
                except KeyError:
                    normalized[getattr(cls, key)] = kwargs[key]
        return normalized

    @classmethod
    def update(cls, __data=None, **update):
        return ModelUpdate(cls, cls._normalize_data(__data, update))

    # @classmethod
    # def insert(cls, __data=None, **insert):
    #     return ModelInsert(cls, cls._normalize_data(__data, insert))
    #
    # @classmethod
    # def insert_many(cls, rows, fields=None):
    #     return ModelInsert(cls, insert=rows, columns=fields)
    #
    # @classmethod
    # def insert_from(cls, query, fields):
    #     columns = [getattr(cls, field) if isinstance(field, basestring)
    #                else field for field in fields]
    #     return ModelInsert(cls, insert=query, columns=columns)

    @classmethod
    def replace(cls, __data=None, **insert):
        return cls.insert(__data, **insert).on_conflict('REPLACE')

    @classmethod
    def replace_many(cls, rows, fields=None):
        return (cls
                .insert_many(rows=rows, fields=fields)
                .on_conflict('REPLACE'))

    #
    # @classmethod
    # def raw(cls, sql, *params):
    #     return ModelRaw(cls, sql, params)
    #
    # @classmethod
    # def delete(cls):
    #     return ModelDelete(cls)

    @classmethod
    def create(cls, **query):
        inst = cls(**query)
        inst.save(force_insert=True)
        return inst

    # @classmethod
    # def bulk_create(cls, model_list, batch_size=None):
    #     if batch_size is not None:
    #         batches = chunked(model_list, batch_size)
    #     else:
    #         batches = [model_list]
    #
    #     field_names = list(cls._meta.sorted_field_names)
    #     if cls._meta.auto_increment:
    #         pk_name = cls._meta.primary_key.name
    #         field_names.remove(pk_name)
    #
    #     if cls._meta.database.returning_clause and \
    #             cls._meta.primary_key is not False:
    #         pk_fields = cls._meta.get_primary_keys()
    #     else:
    #         pk_fields = None
    #
    #     fields = [cls._meta.fields[field_name] for field_name in field_names]
    #     attrs = []
    #     for field in fields:
    #         if isinstance(field, ForeignKeyField):
    #             attrs.append(field.object_id_name)
    #         else:
    #             attrs.append(field.name)
    #
    #     for batch in batches:
    #         accum = ([getattr(model, f) for f in attrs]
    #                  for model in batch)
    #         res = cls.insert_many(accum, fields=fields).execute()
    #         if pk_fields and res is not None:
    #             for row, model in zip(res, batch):
    #                 for (pk_field, obj_id) in zip(pk_fields, row):
    #                     setattr(model, pk_field.name, obj_id)
    #
    # @classmethod
    # def bulk_update(cls, model_list, fields, batch_size=None):
    #     if isinstance(cls._meta.primary_key, CompositeKey):
    #         raise ValueError('bulk_update() is not supported for model with '
    #                          'a composite primary key.')
    #
    #     # First normalize list of fields so all are field instances.
    #     fields = [cls._meta.fields[f] if isinstance(f, basestring) else f
    #               for f in fields]
    #     # Now collect list of attribute names to use for values.
    #     attrs = [field.object_id_name if isinstance(field, ForeignKeyField)
    #              else field.name for field in fields]
    #
    #     if batch_size is not None:
    #         batches = chunked(model_list, batch_size)
    #     else:
    #         batches = [model_list]
    #
    #     n = 0
    #     pk = cls._meta.primary_key
    #
    #     for batch in batches:
    #         id_list = [model._pk for model in batch]
    #         update = {}
    #         for field, attr in zip(fields, attrs):
    #             accum = []
    #             for model in batch:
    #                 value = getattr(model, attr)
    #                 if not isinstance(value, Node):
    #                     value = field.to_value(value)
    #                 accum.append((pk.to_value(model._pk), value))
    #             case = Case(pk, accum)
    #             update[field] = case
    #
    #         n += (cls.update(update)
    #               .where(cls._meta.primary_key.in_(id_list))
    #               .execute())
    #     return n
    #
    # @classmethod
    # def noop(cls):
    #     return NoopModelSelect(cls, ())

    @classmethod
    def get(cls, *query, **filters):
        sq = cls.select()
        if query:
            # Handle simple lookup using just the primary key.
            if len(query) == 1 and isinstance(query[0], int):
                sq = sq.where(cls._meta.primary_key == query[0])
            else:
                sq = sq.where(*query)
        if filters:
            sq = sq.filter(**filters)
        return sq.get()

    @classmethod
    def get_or_none(cls, *query, **filters):
        try:
            return cls.get(*query, **filters)
        except DoesNotExist:
            pass

    @classmethod
    def get_by_id(cls, pk):
        return cls.get(cls._meta.primary_key == pk)

    @classmethod
    def set_by_id(cls, key, value):
        if key is None:
            return cls.insert(value).execute()
        else:
            return (cls.update(value)
                    .where(cls._meta.primary_key == key).execute())

    @classmethod
    def delete_by_id(cls, pk):
        return cls.delete().where(cls._meta.primary_key == pk).execute()

    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = kwargs.pop('defaults', {})
        query = cls.select()
        for field, value in kwargs.items():
            query = query.where(getattr(cls, field) == value)

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                if defaults:
                    kwargs.update(defaults)
                with cls._meta.database.atomic():
                    return cls.create(**kwargs), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    @classmethod
    def filter(cls, *dq_nodes, **filters):
        return cls.select().filter(*dq_nodes, **filters)

    def get_id(self):
        # Using getattr(self, pk-name) could accidentally trigger a query if
        # the primary-key is a foreign-key. So we use the safe_name attribute,
        # which defaults to the field-name, but will be the object_id_name for
        # foreign-key fields.
        if self._meta.primary_key is not False:
            return getattr(self, self._meta.primary_key.safe_name)

    _pk = property(get_id)

    @_pk.setter
    def _pk(self, value):
        setattr(self, self._meta.primary_key.name, value)

    def _pk_expr(self):
        return self._meta.primary_key == self._pk

    def _prune_fields(self, field_dict, only):
        new_data = {}
        for field in only:
            if isinstance(field, basestring):
                field = self._meta.combined[field]
            if field.name in field_dict:
                new_data[field.name] = field_dict[field.name]
        return new_data

    def _populate_unsaved_relations(self, field_dict):
        for foreign_key_field in self._meta.refs:
            foreign_key = foreign_key_field.name
            conditions = (
                    foreign_key in field_dict and
                    field_dict[foreign_key] is None and
                    self.__rel__.get(foreign_key) is not None)
            if conditions:
                setattr(self, foreign_key, getattr(self, foreign_key))
                field_dict[foreign_key] = self.__data__[foreign_key]

    def save(self, force_insert=False, only=None):
        field_dict = self.__data__.copy()
        if self._meta.primary_key is not False:
            pk_field = self._meta.primary_key
            pk_value = self._pk
        else:
            pk_field = pk_value = None
        if only is not None:
            field_dict = self._prune_fields(field_dict, only)
        elif self._meta.only_save_dirty and not force_insert:
            field_dict = self._prune_fields(field_dict, self.dirty_fields)
            if not field_dict:
                self._dirty.clear()
                return False

        self._populate_unsaved_relations(field_dict)
        rows = 1

        if self._meta.auto_increment and pk_value is None:
            field_dict.pop(pk_field.name, None)

        if pk_value is not None and not force_insert:
            if self._meta.composite_key:
                for pk_part_name in pk_field.field_names:
                    field_dict.pop(pk_part_name, None)
            else:
                field_dict.pop(pk_field.name, None)
            if not field_dict:
                raise ValueError('no data to save!')
            rows = self.update(**field_dict).where(self._pk_expr()).execute()
        elif pk_field is not None:
            pk = self.insert(**field_dict).execute()
            if pk is not None and (self._meta.auto_increment or
                                   pk_value is None):
                self._pk = pk
        else:
            self.insert(**field_dict).execute()

        self._dirty.clear()
        return rows

    def is_dirty(self):
        return bool(self._dirty)

    @property
    def dirty_fields(self):
        return [f for f in self._meta.sorted_fields if f.name in self._dirty]

    def dependencies(self, search_nullable=False):
        model_class = type(self)
        stack = [(type(self), None)]
        seen = set()

        while stack:
            klass, query = stack.pop()
            if klass in seen:
                continue
            seen.add(klass)
            for fk, rel_model in klass._meta.backrefs.items():
                if rel_model is model_class or query is None:
                    node = (fk == self.__data__[fk.rel_field.name])
                else:
                    node = fk << query
                subquery = (rel_model.select(rel_model._meta.primary_key)
                            .where(node))
                if not fk.null or search_nullable:
                    stack.append((rel_model, subquery))
                yield (node, fk)

    def delete_instance(self, recursive=False, delete_nullable=False):
        if recursive:
            dependencies = self.dependencies(delete_nullable)
            for query, fk in reversed(list(dependencies)):
                model = fk.model
                if fk.null and not delete_nullable:
                    model.update(**{fk.name: None}).where(query).execute()
                else:
                    model.delete().where(query).execute()
        return type(self).delete().where(self._pk_expr()).execute()

    def __hash__(self):
        return hash((self.__class__, self._pk))

    def __eq__(self, other):
        return (
                other.__class__ == self.__class__ and
                self._pk is not None and
                self._pk == other._pk)

    def __ne__(self, other):
        return not self == other

    # def __sql__(self, ctx):
    #     # NOTE: when comparing a foreign-key field whose related-field is not a
    #     # primary-key, then doing an equality test for the foreign-key with a
    #     # model instance will return the wrong value; since we would return
    #     # the primary key for a given model instance.
    #     #
    #     # This checks to see if we have a converter in the scope, and that we
    #     # are converting a foreign-key expression. If so, we hand the model
    #     # instance to the converter rather than blindly grabbing the primary-
    #     # key. In the event the provided converter fails to handle the model
    #     # instance, then we will return the primary-key.
    #     if ctx.state.converter is not None and ctx.state.is_fk_expr:
    #         try:
    #             return ctx.sql(Value(self, converter=ctx.state.converter))
    #         except (TypeError, ValueError):
    #             pass
    #
    #     return ctx.sql(Value(getattr(self, self._meta.primary_key.name),
    #                          converter=self._meta.primary_key.db_value))

    @classmethod
    def bind(cls, database, bind_refs=True, bind_backrefs=True, _exclude=None):
        is_different = cls._meta.database is not database
        cls._meta.set_database(database)
        if bind_refs or bind_backrefs:
            if _exclude is None:
                _exclude = set()
            G = cls._meta.model_graph(refs=bind_refs, backrefs=bind_backrefs)
            for _, model, is_backref in G:
                if model not in _exclude:
                    model._meta.set_database(database)
                    _exclude.add(model)
        return is_different

    # @classmethod
    # def bind_ctx(cls, database, bind_refs=True, bind_backrefs=True):
    #     return _BoundModelsContext((cls,), database, bind_refs, bind_backrefs)

    @classmethod
    def table_exists(cls):
        M = cls._meta
        return cls._schema.database.table_exists(M.table.__name__, M.schema)

    @classmethod
    def create_table(cls, safe=True, **options):
        # if 'fail_silently' in options:
        #     __deprecated__('"fail_silently" has been deprecated in favor of '
        #                    '"safe" for the create_table() method.')
        #     safe = options.pop('fail_silently')

        if safe and not cls._schema.database.safe_create_index \
                and cls.table_exists():
            return
        if cls._meta.temporary:
            options.setdefault('temporary', cls._meta.temporary)
        # cls._schema.create_all(safe, **options)

    @classmethod
    def drop_table(cls, safe=True, drop_sequences=True, **options):
        if safe and not cls._schema.database.safe_drop_index \
                and not cls.table_exists():
            return
        if cls._meta.temporary:
            options.setdefault('temporary', cls._meta.temporary)
        cls._schema.drop_all(safe, drop_sequences, **options)

    @classmethod
    def truncate_table(cls, **options):
        cls._schema.truncate_table(**options)

    # @classmethod
    # def index(cls, *fields, **kwargs):
    #     return ModelIndex(cls, fields, **kwargs)

    # @classmethod
    # def add_index(cls, *fields, **kwargs):
    #     if len(fields) == 1 and isinstance(fields[0], (SQL, Index)):
    #         cls._meta.indexes.append(fields[0])
    #     else:
    #         cls._meta.indexes.append(ModelIndex(cls, fields, **kwargs))


# 测试
db = SqliteDatabase('testorm.db')


class User(Model):
    id = IntegerField(primary_key=True)
    name = CharField()

    class Meta:
        database = db


new_user = User(id='123456', name='LiMing')

if __name__ == "__main__":
    # new_user.create_table()
    # new_user.insert( )
    # db.connect()
    new_user.save()
#
