#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:36
# @Author  : Cojun  Mao
# @Site    : 
# @File    : modelquerys.py
# @Project : mysite_diy
# @Software: PyCharm
import operator
from collections import deque, namedtuple
from functools import reduce

from webcore.orm.felds import ForeignKeyField, Leaf, Expr, Field, DJANGO_MAP, OP_EQ, fn, DQ
from webcore.orm.models import Model


def not_allowed(fn):
    def inner(self, *args, **kwargs):
        raise NotImplementedError('%s is not allowed on %s instances' % (
            fn, type(self).__name__,
        ))

    return inner


class ReverseRelationDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.rel_model = field.model_class

    def __get__(self, instance, instance_type=None):
        if instance:
            return self.rel_model.select().where(self.field == instance.get_id())
        return self


basestring = bytes


def returns_clone(func):
    '''
    创建副本
    :param func:
    :return:
    '''

    def inner(self, *args, **kwargs):
        clone = self.clone()  # 生成新类
        func(clone, *args, **kwargs)
        return clone

    inner.call_local = func
    return inner


class QueryResultWrapper(object):
    """
    Provides an iterator over the results of a raw Query, additionally doing
    two things:
    - converts rows from the database into model instances
    - ensures that multiple iterations do not result in multiple queries
    对原始查询的结果提供迭代器两件事：
        -将数据库中的行转换为模型实例
        -确保多次迭代不会导致多次查询
    """

    def __init__(self, model, cursor, meta=None):
        self.model = model
        self.cursor = cursor
        self.naive = not meta

        if self.naive:
            cols = []
            non_cols = []
            for i in range(len(self.cursor.description)):
                col = self.cursor.description[i][0]
                if col in model._meta.columns:
                    cols.append((i, model._meta.columns[col]))
                else:
                    non_cols.append((i, col))
            self._cols = cols
            self._non_cols = non_cols
        else:
            self.column_meta, self.join_meta = meta

        self.__ct = 0
        self.__idx = 0

        self._result_cache = []
        self._populated = False

    def simple_iter(self, row):
        instance = self.model()
        for i, f in self._cols:
            setattr(instance, f.name, f.python_value(row[i]))
        for i, f in self._non_cols:
            setattr(instance, f, row[i])
        return instance

    def construct_instance(self, row):
        # we have columns, model, and a graph of joins to reconstruct
        collected_models = {}
        cols = [c[0] for c in self.cursor.description]
        for i, expr in enumerate(self.column_meta):
            value = row[i]
            if isinstance(expr, Field):
                model = expr.model_class
            else:
                model = self.model

            if model not in collected_models:
                collected_models[model] = model()
            instance = collected_models[model]

            if isinstance(expr, Field):
                setattr(instance, expr.name, expr.python_value(value))
            elif isinstance(expr, Expr) and expr._alias:
                setattr(instance, expr._alias, value)
            else:
                setattr(instance, cols[i], value)

        return self.follow_joins(self.join_meta, collected_models, self.model)

    def follow_joins(self, joins, collected_models, current):
        inst = collected_models[current]

        if current not in joins:
            return inst

        for joined_model, _, _ in joins[current]:
            if joined_model in collected_models:
                joined_inst = self.follow_joins(joins, collected_models, joined_model)
                fk_field = current._meta.rel_for_model(joined_model)

                if not fk_field:
                    continue

                if joined_inst.get_id() is None and fk_field.name in inst._data:
                    rel_inst_id = inst._data[fk_field.name]
                    joined_inst.set_id(rel_inst_id)

                setattr(inst, fk_field.name, joined_inst)

        return inst

    def __iter__(self):
        self.__idx = 0

        if not self._populated:
            return self
        else:
            return iter(self._result_cache)

    def iterate(self):
        row = self.cursor.fetchone()
        if not row:
            self._populated = True
            raise StopIteration

        if self.naive:
            return self.simple_iter(row)
        else:
            return self.construct_instance(row)

    def iterator(self):
        while 1:
            yield self.iterate()

    # def __next__(self):
    #     self.next()

    def next(self):
        if self.__idx < self.__ct:
            inst = self._result_cache[self.__idx]
            self.__idx += 1
            return inst

        instance = self.iterate()
        instance.prepared()  # <-- model prepared hook
        self._result_cache.append(instance)
        self.__ct += 1
        self.__idx += 1
        return instance

    __next__ = next

    def fill_cache(self, n=None):
        n = n or float('Inf')
        self.__idx = self.__ct
        while not self._populated and (n > self.__ct):
            try:
                self.next()
            except StopIteration:
                break
Join = namedtuple('Join', ('model_class', 'join_type', 'on'))

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
        """
        原型模式（Prototype Pattern）是用于创建重复的对象，
        同时又能保证性能。这种类型的设计模式属于创建型模式，
        它提供了一种创建对象的最佳方式。这种模式是实现了一个原型接口，
        该接口用于创建当前对象的克隆。当直接创建对象的代价比较大时，
        则采用这种模式。例如，一个对象需要在一个高代价的数据库操作之后被创建。
        我们可以缓存该对象，在下一个请求时返回它的克隆，在需要的时候更新数据库，以此来减少数据库调用。
        :return:
        """
        # type(self)新样式类实例的类型为其类
        query = type(self)(self.model_class)  # 创建查询副本
        if self._where is not None:
            query._where = self._where.clone()
            # print('query._where',query._where)
        query._joins = self.clone_joins()
        query._query_ctx = self._query_ctx
        return query
        # if self._where is not None:
        #     self._where = self._where.clone()
        # self._joins = self.clone_joins()
        # self._query_ctx = self._query_ctx
        # return self

    def clone_joins(self):
        return dict(
            (mc, list(j)) for mc, j in self._joins.items()
        )

    @returns_clone
    def where(self, *q_or_node):
        print('*q_or_node ',  q_or_node)
        if self._where is None:
            # reduce()函数会对参数序列中元素进行累积。
            self._where = reduce(operator.and_, q_or_node)
            # self._where = reduce(lambda x, y: x & y, q_or_node)
            print('self._where is none')
            print('self._where ',self._where)
        else:
            for piece in q_or_node:
                print('self._where is not none')
                # a &= b是a = a & b的简写
                self._where &= piece
                print('self._where ', self._where)

        return self

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
        # 将 args 和 kwargs 规范化为新的表达式
        dq_node = Leaf()
        if args:
            # a &= b 等价于  a = a & b、
            # &=就是做完位与运算再赋值
            dq_node &= reduce(operator.and_, [a.clone() for a in args])
        if kwargs:
            dq_node &= DQ(**kwargs)

        # dq_node should now be an Expr, lhs = Leaf(), rhs = ...
        # dq_node 现在应该是一个 Expr, lhs = Leaf(), rhs = ...
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
                    # operator.add(x, y) 等同于x + y。
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
        print('sql: ',sql)
        print('params: ',params)
        return self.database.execute_sql(sql, params, self.require_commit)

    def execute(self):
        raise NotImplementedError

    def scalar(self, as_tuple=False):
        row = self._execute().fetchone()
        if row and not as_tuple:
            return row[0]
        else:
            return row
class RawQuery(Query):
    def __init__(self, model, query, *params):
        self._sql = query
        self._params = list(params)
        self._qr = None
        super(RawQuery, self).__init__(model)

    def clone(self):
        return RawQuery(self.model_class, self._sql, *self._params)

    join = not_allowed('joining')
    where = not_allowed('where')
    switch = not_allowed('switch')

    def sql(self):
        return self._sql, self._params

    def execute(self):
        if self._qr is None:
            self._qr = QueryResultWrapper(self.model_class, self._execute(), None)
        return self._qr

    def __iter__(self):
        return iter(self.execute())


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
        print('SelectQuery clone query:  ', query)
        return query

    def _model_shorthand(self, args):
        accum = []
        for arg in args:
            if isinstance(arg, Leaf):
                accum.append(arg)
            elif issubclass(arg, Model):
                accum.extend(arg._meta.get_fields())
        return accum

    def group_by(self, *args):
        self._group_by = self._model_shorthand(args)
        return self

    def having(self, *q_or_node):
        if self._having is None:
            self._having = reduce(operator.and_, q_or_node)
        else:
            for piece in q_or_node:
                self._having &= piece
        return self

    def order_by(self, *args):
        self._order_by = list(args)
        return self

    def limit(self, lim):
        self._limit = lim
        return self

    def offset(self, off):
        self._offset = off
        return self

    def paginate(self, page, paginate_by=20):
        print('self: ', self)
        if page > 0:
            page -= 1
        self._limit = paginate_by
        self._offset = page * paginate_by
        return self

    def distinct(self, is_distinct=True):
        self._distinct = is_distinct
        return self

    def for_update(self, for_update=True):
        self._for_update = for_update
        return self

    def naive(self, naive=True):
        self._naive = naive
        return self

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
        # print('2588')
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
        # print('123')
        # return self.execute()

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


class DeleteQuery(Query):
    join = not_allowed('joining')

    def sql(self):
        return self.get_compiler().parse_delete_query(self)

    def execute(self):
        return self.database.rows_affected(self._execute())
