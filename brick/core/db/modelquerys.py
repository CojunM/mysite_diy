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
from inspect import isclass

from brick.core.db.constants import RESULTS_DICTS, RESULTS_NAIVE, RESULTS_NAMEDTUPLES, RESULTS_AGGREGATE_MODELS, \
    RESULTS_MODELS, RESULTS_TUPLES, basestring

from brick.core.db.felds import EnclosedClause, SQL, Value, Field, FieldProxy, Node, ForeignKeyField, Expression, DQ, \
    fn, Func
from brick.core.db.utils import returns_clone, OP, JOIN, DJANGO_MAP


def not_allowed(fn):
    """
    方法修饰符，用于指示不允许调用方法。将
    引发“NotImplementedError”。
    """
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


# basestring = bytes

# class QueryResultWrapper(object):
#     """
#     Provides an iterator over the results of a raw Query, additionally doing
#     two things:
#     - converts rows from the database into model instances
#     - ensures that multiple iterations do not result in multiple queries
#     对原始查询的结果提供迭代器两件事：
#         -将数据库中的行转换为模型实例
#         -确保多次迭代不会导致多次查询
#     """
#
#     def __init__(self, model, cursor, meta=None):
#         self.model = model
#         self.cursor = cursor
#         self.naive = not meta
#
#         if self.naive:
#             cols = []
#             non_cols = []
#             for i in range(len(self.cursor.description)):
#                 col = self.cursor.description[i][0]
#                 if col in model._meta.columns:
#                     cols.append((i, model._meta.columns[col]))
#                 else:
#                     non_cols.append((i, col))
#             self._cols = cols
#             self._non_cols = non_cols
#         else:
#             self.column_meta, self.join_meta = meta
#
#         self.__ct = 0
#         self.__idx = 0
#
#         self._result_cache = []
#         self._populated = False
#
#     def simple_iter(self, row):
#         instance = self.model()
#         for i, f in self._cols:
#             setattr(instance, f.name, f.python_value(row[i]))
#         for i, f in self._non_cols:
#             setattr(instance, f, row[i])
#         return instance
#
#     def construct_instance(self, row):
#         # we have columns, model, and a graph of joins to reconstruct
#         collected_models = {}
#         cols = [c[0] for c in self.cursor.description]
#         for i, expr in enumerate(self.column_meta):
#             value = row[i]
#             if isinstance(expr, Field):
#                 model = expr.model_class
#             else:
#                 model = self.model
#
#             if model not in collected_models:
#                 collected_models[model] = model()
#             instance = collected_models[model]
#
#             if isinstance(expr, Field):
#                 setattr(instance, expr.name, expr.python_value(value))
#             elif isinstance(expr, Expr) and expr._alias:
#                 setattr(instance, expr._alias, value)
#             else:
#                 setattr(instance, cols[i], value)
#
#         return self.follow_joins(self.join_meta, collected_models, self.model)
#
#     def follow_joins(self, joins, collected_models, current):
#         inst = collected_models[current]
#
#         if current not in joins:
#             return inst
#
#         for joined_model, _, _ in joins[current]:
#             if joined_model in collected_models:
#                 joined_inst = self.follow_joins(joins, collected_models, joined_model)
#                 fk_field = current._meta.rel_for_model(joined_model)
#
#                 if not fk_field:
#                     continue
#
#                 if joined_inst.get_id() is None and fk_field.name in inst._data:
#                     rel_inst_id = inst._data[fk_field.name]
#                     joined_inst.set_id(rel_inst_id)
#
#                 setattr(inst, fk_field.name, joined_inst)
#
#         return inst
#
#     def __iter__(self):
#         self.__idx = 0
#
#         if not self._populated:
#             return self
#         else:
#             return iter(self._result_cache)
#
#     def iterate(self):
#         row = self.cursor.fetchone()
#         if not row:
#             self._populated = True
#             raise StopIteration
#
#         if self.naive:
#             return self.simple_iter(row)
#         else:
#             return self.construct_instance(row)
#
#     def iterator(self):
#         while 1:
#             yield self.iterate()
#
#     # def __next__(self):
#     #     self.next()
#
#     def next(self):
#         if self.__idx < self.__ct:
#             inst = self._result_cache[self.__idx]
#             self.__idx += 1
#             return inst
#
#         instance = self.iterate()
#         instance.prepared()  # <-- model prepared hook
#         self._result_cache.append(instance)
#         self.__ct += 1
#         self.__idx += 1
#         return instance
#
#     __next__ = next
#
#     def fill_cache(self, n=None):
#         n = n or float('Inf')
#         self.__idx = self.__ct
#         while not self._populated and (n > self.__ct):
#             try:
#                 self.next()
#             except StopIteration:
#                 break

#
# class QueryResultWrapper(object):
#     """
#     Provides an iterator over the results of a raw Query, additionally doing
#     two things:
#     - converts rows from the database into python representations
#     - ensures that multiple iterations do not result in multiple queries
#     """
#
#     def __init__(self, model, cursor, meta=None):
#         self.model = model
#         self.cursor = cursor
#
#         self._ct = 0
#         self._idx = 0
#
#         self._result_cache = []
#         self._populated = False
#         self._initialized = False
#
#         if meta is not None:
#             self.column_meta, self.join_meta = meta
#         else:
#             self.column_meta = self.join_meta = None
#
#     def __iter__(self):
#         if self._populated:
#             return iter(self._result_cache)
#         else:
#             return ResultIterator(self)
#
#     @property
#     def count(self):
#         self.fill_cache()
#         return self._ct
#
#     def __len__(self):
#         return self.count
#
#     def process_row(self, row):
#         return row
#
#     def iterate(self):
#         row = self.cursor.fetchone()
#         if not row:
#             self._populated = True
#             if not getattr(self.cursor, 'name', None):
#                 self.cursor.close()
#             raise StopIteration
#         elif not self._initialized:
#             self.initialize(self.cursor.description)
#             self._initialized = True
#         return self.process_row(row)
#
#     def iterator(self):
#         while True:
#             yield self.iterate()
#
#     def next(self):
#         if self._idx < self._ct:
#             inst = self._result_cache[self._idx]
#             self._idx += 1
#             return inst
#         elif self._populated:
#             raise StopIteration
#
#         obj = self.iterate()
#         self._result_cache.append(obj)
#         self._ct += 1
#         self._idx += 1
#         return obj
#
#     __next__ = next
#
#     def fill_cache(self, n=None):
#         n = n or float('Inf')
#         if n < 0:
#             raise ValueError('Negative values are not supported.')
#         self._idx = self._ct
#         while not self._populated and (n > self._ct):
#             try:
#                 next(self)
#             except StopIteration:
#                 break
#
# class ExtQueryResultWrapper(QueryResultWrapper):
#     def initialize(self, description):
#         n_cols = len(description)
#         self.conv = conv = []
#         if self.column_meta is not None:
#             n_meta = len(self.column_meta)
#             for i, node in enumerate(self.column_meta):
#                 if not self._initialize_node(node, i):
#                     self._initialize_by_name(description[i][0], i)
#             if n_cols == n_meta:
#                 return
#         else:
#             i = 0
#
#         for i in range(i, n_cols):
#             self._initialize_by_name(description[i][0], i)
#
#     def _initialize_by_name(self, name, i):
#         model_cols = self.model._meta.columns
#         if name in model_cols:
#             field = model_cols[name]
#             self.conv.append((i, field.name, field.python_value))
#         else:
#             self.conv.append((i, name, None))
#
#     def _initialize_node(self, node, i):
#         if isinstance(node, Field):
#             self.conv.append((i, node._alias or node.name, node.python_value))
#             return True
#         elif isinstance(node, Func) and len(node.arguments):
#             arg = node.arguments[0]
#             if isinstance(arg, Field):
#                 name = node._alias or arg._alias or arg.name
#                 func = node._coerce and arg.python_value or None
#                 self.conv.append((i, name, func))
#                 return True
#         return False
#
#
# class DictQueryResultWrapper(ExtQueryResultWrapper):
#     def process_row(self, row):
#         res = {}
#         for i, column, f in self.conv:
#             res[column] = f(row[i]) if f is not None else row[i]
#         return res
# class TuplesQueryResultWrapper(ExtQueryResultWrapper):
#     def process_row(self, row):
#         return tuple([col if self.conv[i][2] is None else self.conv[i][2](col)
#                       for i, col in enumerate(row)])

# if _TuplesQueryResultWrapper is None:
#     _TuplesQueryResultWrapper = TuplesQueryResultWrapper
#
#
# if _DictQueryResultWrapper is None:
#     _DictQueryResultWrapper = DictQueryResultWrapper
#
# Join = namedtuple('Join', ('model_class', 'join_type', 'on'))
#
# class Query(object):
#     require_commit = True  # 需要提交
#
#     def __init__(self, model_class):
#         self.model_class = model_class
#         self.database = model_class._meta.database
#
#         self._dirty = True
#         self._query_ctx = model_class
#         self._joins = {self.model_class: []}  # adjacency graph邻接图
#         self._where = None
#
#     def clone(self):
#         """
#         原型模式（Prototype Pattern）是用于创建重复的对象，
#         同时又能保证性能。这种类型的设计模式属于创建型模式，
#         它提供了一种创建对象的最佳方式。这种模式是实现了一个原型接口，
#         该接口用于创建当前对象的克隆。当直接创建对象的代价比较大时，
#         则采用这种模式。例如，一个对象需要在一个高代价的数据库操作之后被创建。
#         我们可以缓存该对象，在下一个请求时返回它的克隆，在需要的时候更新数据库，以此来减少数据库调用。
#         :return:
#         """
#         # type(self)新样式类实例的类型为其类
#         query = type(self)(self.model_class)  # 创建查询副本
#         if self._where is not None:
#             query._where = self._where.clone()
#             # print('query._where',query._where)
#         query._joins = self.clone_joins()
#         query._query_ctx = self._query_ctx
#         return query
#         # if self._where is not None:
#         #     self._where = self._where.clone()
#         # self._joins = self.clone_joins()
#         # self._query_ctx = self._query_ctx
#         # return self
#
#     # def clone(self):
#     #     obj = self.__class__.__new__(self.__class__)
#     #     obj.__dict__ = self.__dict__.copy()
#     #     return obj
#
#     def clone_joins(self):
#         return dict(
#             (mc, list(j)) for mc, j in self._joins.items()
#         )
#
#     @returns_clone
#     def where(self, *q_or_node):
#         # print('where*q_or_node ',  q_or_node)
#         if self._where is None:
#             # reduce()函数会对参数序列中元素进行累积。
#             self._where = reduce(operator.and_, q_or_node)
#             # self._where = reduce(lambda x, y: x & y, q_or_node)
#             # print('self._where is none')
#             # print('self._where None ',self._where)
#         else:
#             for piece in q_or_node:
#                 # print('self._where is not none')
#                 # a &= b是a = a & b的简写
#                 self._where &= piece
#                 # print('self._where ', self._where)
#
#         return self
#
#     def join(self, model_class, join_type=None, on=None):
#         if not self._query_ctx._meta.rel_exists(model_class):
#             raise ValueError('No foreign key between %s and %s' % (
#                 self._query_ctx, model_class,
#             ))
#         if on and isinstance(on, basestring):
#             on = self._query_ctx._meta.fields[on]
#         self._joins.setdefault(self._query_ctx, [])
#         self._joins[self._query_ctx].append(Join(model_class, join_type, on))
#         self._query_ctx = model_class
#
#     def switch(self, model_class=None):
#         self._query_ctx = model_class or self.model_class
#
#     def ensure_join(self, lm, rm, on=None):
#         ctx = self._query_ctx
#         for join in self._joins.get(lm, []):
#             if join.model_class == rm:
#                 return self
#         query = self.switch(lm).join(rm, on=on).switch(ctx)
#         return query
#
#     def convert_dict_to_node(self, qdict):
#         accum = []
#         joins = []
#         for key, value in sorted(qdict.items()):
#             curr = self.model_class
#             if '__' in key and key.rsplit('__', 1)[1] in DJANGO_MAP:
#                 key, op = key.rsplit('__', 1)
#                 op = DJANGO_MAP[op]
#             else:
#                 op = OP_EQ
#             for piece in key.split('__'):
#                 model_attr = getattr(curr, piece)
#                 if isinstance(model_attr, (ForeignKeyField, ReverseRelationDescriptor)):
#                     curr = model_attr.rel_model
#                     joins.append(model_attr)
#             accum.append(Expr(model_attr, op, value))
#         return accum, joins
#
#     def filter(self, *args, **kwargs):
#         # normalize args and kwargs into a new expression
#         # 将 args 和 kwargs 规范化为新的表达式
#         dq_node = Leaf()
#         if args:
#             # a &= b 等价于  a = a & b、
#             # &=就是做完位与运算再赋值
#             dq_node &= reduce(operator.and_, [a.clone() for a in args])
#         if kwargs:
#             dq_node &= DQ(**kwargs)
#
#         # dq_node should now be an Expr, lhs = Leaf(), rhs = ...
#         # dq_node 现在应该是一个 Expr, lhs = Leaf(), rhs = ...
#         q = deque([dq_node])
#         dq_joins = set()
#         while q:
#             curr = q.popleft()
#             if not isinstance(curr, Expr):
#                 continue
#             for side, piece in (('lhs', curr.lhs), ('rhs', curr.rhs)):
#                 if isinstance(piece, DQ):
#                     query, joins = self.convert_dict_to_node(piece.query)
#                     dq_joins.update(joins)
#                     # operator.add(x, y) 等同于x + y。
#                     setattr(curr, side, reduce(operator.and_, query))
#                 else:
#                     q.append(piece)
#
#         dq_node = dq_node.rhs
#
#         query = self.clone()
#         for field in dq_joins:
#             if isinstance(field, ForeignKeyField):
#                 lm, rm = field.model_class, field.rel_model
#                 field_obj = field
#             elif isinstance(field, ReverseRelationDescriptor):
#                 lm, rm = field.field.rel_model, field.rel_model
#                 field_obj = field.field
#             query = query.ensure_join(lm, rm, field_obj)
#         return query.where(dq_node)
#
#     def get_compiler(self):
#         return self.database.get_compiler()
#
#     def sql(self):
#         raise NotImplementedError
#
#     def _execute(self):
#         sql, params = self.sql()
#         print('sql: ',sql)
#         print('params: ',params)
#         return self.database.execute_sql(sql, params, self.require_commit)
#
#     def execute(self):
#         raise NotImplementedError
#
#     def scalar(self, as_tuple=False):
#         row = self._execute().fetchone()
#         if row and not as_tuple:
#             return row[0]
#         else:
#             return row
# class RawQuery(Query):
#     def __init__(self, model, query, *params):
#         self._sql = query
#         self._params = list(params)
#         self._qr = None
#         super(RawQuery, self).__init__(model)
#
#     def clone(self):
#         return RawQuery(self.model_class, self._sql, *self._params)
#
#     join = not_allowed('joining')
#     where = not_allowed('where')
#     switch = not_allowed('switch')
#
#     def sql(self):
#         return self._sql, self._params
#
#     def execute(self):
#         if self._qr is None:
#             self._qr = QueryResultWrapper(self.model_class, self._execute(), None)
#         return self._qr
#
#     def __iter__(self):
#         return iter(self.execute())
#
#
# class SelectQuery(Query):
#     def __init__(self, model_class, *selection):
#         super(SelectQuery, self).__init__(model_class)
#         self.require_commit = self.database.commit_select
#         self._explicit_selection = len(selection) > 0
#         self._select = self._model_shorthand(selection or model_class._meta.get_fields())
#         self._group_by = None
#         self._having = None
#         self._order_by = None
#         self._limit = None
#         self._offset = None
#         self._distinct = False
#         self._tuples = False
#         self._dicts = False
#         self._namedtuples = False
#         self._for_update = False
#         self._naive = False
#         self._qr = None
#
#     def clone(self):
#         query = super(SelectQuery, self).clone()
#         query._explicit_selection = self._explicit_selection
#         query._select = list(self._select)
#         if self._group_by is not None:
#             query._group_by = list(self._group_by)
#         if self._having:
#             query._having = self._having.clone()
#         if self._order_by is not None:
#             query._order_by = list(self._order_by)
#         query._limit = self._limit
#         query._offset = self._offset
#         query._distinct = self._distinct
#         query._for_update = self._for_update
#         query._naive = self._naive
#         query._tuples = self._tuples
#         query._dicts = self._dicts
#         # print('SelectQuery clone query:  ', query)
#         return query
#
#     def _model_shorthand(self, args):
#         accum = []
#         from brick.core.db.models import Model
#         for arg in args:
#             if isinstance(arg, Leaf):
#                 accum.append(arg)
#             elif issubclass(arg, Model):
#                 accum.extend(arg._meta.get_fields())
#         return accum
#
#     @returns_clone
#     def group_by(self, *args):
#         self._group_by = self._model_shorthand(args)
#
#     @returns_clone
#     def having(self, *q_or_node):
#         if self._having is None:
#             self._having = reduce(operator.and_, q_or_node)
#         else:
#             for piece in q_or_node:
#                 self._having &= piece
#
#
#     @returns_clone
#     def order_by(self, *args):
#         # print('order_by:  ',args)
#         self._order_by = list(args)
#
#     @returns_clone
#     def limit(self, lim):
#         self._limit = lim
#
#     @returns_clone
#     def offset(self, off):
#         self._offset = off
#
#     @returns_clone
#     def paginate(self, page, paginate_by=20):
#         # print('paginate,self: ', self)
#         if page > 0:
#             page -= 1
#         self._limit = paginate_by
#         self._offset = page * paginate_by
#
#     @returns_clone
#     def distinct(self, is_distinct=True):
#         self._distinct = is_distinct
#
#     @returns_clone
#     def for_update(self, for_update=True):
#         self._for_update = for_update
#
#     @returns_clone
#     def tuples(self, tuples=True):
#         self._tuples = tuples
#         if tuples:
#             self._dicts = self._namedtuples = False
#
#     @returns_clone
#     def dicts(self, dicts=True):
#         self._dicts = dicts
#         if dicts:
#             self._tuples = self._namedtuples = False
#
#     @returns_clone
#     def naive(self, naive=True):
#         self._naive = naive
#
#
#     def annotate(self, rel_model, annotation=None):
#         annotation = annotation or fn.Count(rel_model._meta.primary_key).alias('count')
#         query = self.clone()
#         query = query.ensure_join(query._query_ctx, rel_model)
#         if not query._group_by:
#             query._group_by = list(query._select)
#         query._select = tuple(query._select) + (annotation,)
#         return query
#
#     def _aggregate(self, aggregation=None):
#         aggregation = aggregation or fn.Count(self.model_class._meta.primary_key)
#         query = self.order_by()
#         query._select = [aggregation]
#         return query
#
#     def aggregate(self, aggregation=None):
#         return self._aggregate(aggregation).scalar()
#
#     def count(self):
#         if self._distinct or self._group_by:
#             return self.wrapped_count()
#
#         # defaults to a count() of the primary key
#         return self.aggregate() or 0
#
#     def wrapped_count(self):
#         clone = self.order_by()
#         clone._limit = clone._offset = None
#
#         sql, params = clone.sql()
#         wrapped = 'SELECT COUNT(1) FROM (%s) AS wrapped_select' % sql
#         rq = RawQuery(self.model_class, wrapped, *params)
#         return rq.scalar() or 0
#
#     def exists(self):
#         clone = self.paginate(1, 1)
#         clone._select = [self.model_class._meta.primary_key]
#         return bool(clone.scalar())
#
#     def get(self):
#         clone = self.paginate(1, 1)
#         try:
#             return clone.execute().next()
#         except StopIteration:
#             raise self.model_class.DoesNotExist('instance matching query does not exist:\nSQL: %s\nPARAMS: %s' % (
#                 self.sql()
#             ))
#
#     def sql(self):
#         return self.get_compiler().parse_select_query(self)
#
#     def verify_naive(self):
#         for expr in self._select:
#             if isinstance(expr, Field) and expr.model_class != self.model_class:
#                 return False
#         return True
#
#     def execute(self):
#         # print('2588')
#         if self._dirty or not self._qr:
#             if self._naive or not self._joins or self.verify_naive():
#                 query_meta = None
#             else:
#                 query_meta = [self._select, self._joins]
#             self._qr = QueryResultWrapper(self.model_class, self._execute(), query_meta)
#             self._dirty = False
#             return self._qr
#         else:
#             return self._qr
#         # if self._tuples:
#         #     QRW = self.database.get_result_wrapper(RESULTS_TUPLES)
#         # elif self._dicts:
#         #     QRW = self.database.get_result_wrapper(RESULTS_DICTS)
#         # else:
#         #     QRW = self.database.get_result_wrapper(RESULTS_NAIVE)
#
#     def __iter__(self):
#         return iter(self.execute())
#         # print('123')
#         # return self.execute()
#
#     def __getitem__(self, value):
#         offset = limit = None
#         if isinstance(value, slice):
#             if value.start:
#                 offset = value.start
#             if value.stop:
#                 limit = value.stop - (value.start or 0)
#         else:
#             if value < 0:
#                 raise ValueError('Negative indexes are not supported, try ordering in reverse')
#             offset = value
#             limit = 1
#         if self._limit != limit or self._offset != offset:
#             self._qr = None
#         self._limit = limit
#         self._offset = offset
#         res = list(self)
#         return limit == 1 and res[0] or res
#
# class ManyToManyQuery(SelectQuery):
#     def __init__(self, instance, accessor, rel, *args, **kwargs):
#         self._instance = instance
#         self._accessor = accessor
#         self._src_attr = accessor.src_fk.rel_field.name
#         self._dest_attr = accessor.dest_fk.rel_field.name
#         super(ManyToManyQuery, self).__init__(rel, (rel,), *args, **kwargs)
#
#     def _id_list(self, model_or_id_list):
#         if isinstance(model_or_id_list[0], Model):
#             return [getattr(obj, self._dest_attr) for obj in model_or_id_list]
#         return model_or_id_list
#
#     def add(self, value, clear_existing=False):
#         if clear_existing:
#             self.clear()
#
#         accessor = self._accessor
#         src_id = getattr(self._instance, self._src_attr)
#         if isinstance(value, SelectQuery):
#             query = value.columns(
#                 Value(src_id),
#                 accessor.dest_fk.rel_field)
#             accessor.through_model.insert_from(
#                 fields=[accessor.src_fk, accessor.dest_fk],
#                 query=query).execute()
#         else:
#             value = ensure_tuple(value)
#             if not value: return
#
#             inserts = [{
#                 accessor.src_fk.name: src_id,
#                 accessor.dest_fk.name: rel_id}
#                 for rel_id in self._id_list(value)]
#             accessor.through_model.insert_many(inserts).execute()
#
#     def remove(self, value):
#         src_id = getattr(self._instance, self._src_attr)
#         if isinstance(value, SelectQuery):
#             column = getattr(value.model, self._dest_attr)
#             subquery = value.columns(column)
#             return (self._accessor.through_model
#                     .delete()
#                     .where(
#                 (self._accessor.dest_fk << subquery) &
#                 (self._accessor.src_fk == src_id))
#                     .execute())
#         else:
#             value = ensure_tuple(value)
#             if not value:
#                 return
#             return (self._accessor.through_model
#                     .delete()
#                     .where(
#                 (self._accessor.dest_fk << self._id_list(value)) &
#                 (self._accessor.src_fk == src_id))
#                     .execute())
#
#     def clear(self):
#         src_id = getattr(self._instance, self._src_attr)
#         return (self._accessor.through_model
#                 .delete()
#                 .where(self._accessor.src_fk == src_id)
#                 .execute())
#
# class UpdateQuery(Query):
#     def __init__(self, model_class, update=None):
#         self._update = update
#         self._on_conflict = None
#         self._windows = None
#         super(UpdateQuery, self).__init__(model_class)
#
#     def clone(self):
#         query = super(UpdateQuery, self).clone()
#         query._update = dict(self._update)
#         query._on_conflict = self._on_conflict
#         if self._windows is not None:
#             query._windows = list(self._windows)
#         return query
#
#     join = not_allowed('joining')
#
#     def on_conflict(self, action=None):
#         self._on_conflict = action
#
#     def sql(self):
#         return self.get_compiler().parse_update_query(self)
#
#     def execute(self):
#         return self.database.rows_affected(self._execute())
#
#
# class InsertQuery(Query):
#     def __init__(self, model_class, insert=None):
#         mm = model_class._meta
#         query = dict((mm.fields[f], v) for f, v in mm.get_default_dict().items())
#         query.update(insert)
#         self._insert = query
#         super(InsertQuery, self).__init__(model_class)
#
#     def clone(self):
#         query = super(InsertQuery, self).clone()
#         query._insert = dict(self._insert)
#         return query
#
#     join = not_allowed('joining')
#     where = not_allowed('where clause')
#
#     def sql(self):
#         return self.get_compiler().parse_insert_query(self)
#
#     def execute(self):
#         return self.database.last_insert_id(self._execute(), self.model_class)
#
# class DeleteQuery(Query):
#     join = not_allowed('joining')
#
#     def sql(self):
#         return self.get_compiler().parse_delete_query(self)
#
#     def execute(self):
#         return self.database.rows_affected(self._execute())


class ModelAlias(object):
    def __init__(self, model_class):
        self.__dict__['model_class'] = model_class

    def __getattr__(self, attr):
        model_attr = getattr(self.model_class, attr)
        if isinstance(model_attr, Field):
            return FieldProxy(self, model_attr)
        return model_attr

    def __setattr__(self, attr, value):
        raise AttributeError('Cannot set attributes on ModelAlias instances')

    def get_proxy_fields(self, declared_fields=False):
        mm = self.model_class._meta
        fields = mm.declared_fields if declared_fields else mm.sorted_fields
        return [FieldProxy(self, f) for f in fields]

    def select(self, *selection):
        if not selection:
            selection = self.get_proxy_fields()
        query = SelectQuery(self, *selection)
        if self._meta.order_by:
            query = query.order_by(*self._meta.order_by)
        return query

    def __call__(self, **kwargs):
        return self.model_class(**kwargs)


class Query(Node):
    """Base class representing a database query on one or more tables."""
    require_commit = True

    def __init__(self, model_class):
        super(Query, self).__init__()

        self.model_class = model_class
        self.database = model_class._meta.database

        self._dirty = True
        self._query_ctx = model_class
        self._joins = {self.model_class: []}  # Join graph as adjacency list.
        self._where = None

    def __repr__(self):
        sql, params = self.sql()
        return '%s %s %s' % (self.model_class, sql, params)

    def clone(self):
        query = type(self)(self.model_class)
        query.database = self.database
        return self._clone_attributes(query)

    def _clone_attributes(self, query):
        if self._where is not None:
            query._where = self._where.clone()
        query._joins = self._clone_joins()
        query._query_ctx = self._query_ctx
        return query

    def _clone_joins(self):
        return dict(
            (mc, list(j)) for mc, j in self._joins.items())

    def _add_query_clauses(self, initial, expressions, conjunction=None):
        reduced = reduce(operator.and_, expressions)
        if initial is None:
            return reduced
        conjunction = conjunction or operator.and_
        return conjunction(initial, reduced)

    def _model_shorthand(self, args):
        accum = []
        for arg in args:
            from brick.core.db.models import Model
            if isinstance(arg, Node):
                accum.append(arg)
            elif isinstance(arg, Query):
                accum.append(arg)
            elif isinstance(arg, ModelAlias):
                accum.extend(arg.get_proxy_fields())
            elif isclass(arg) and issubclass(arg, Model):
                accum.extend(arg._meta.declared_fields)
        return accum

    @returns_clone
    def where(self, *expressions):
        self._where = self._add_query_clauses(self._where, expressions)

    @returns_clone
    def orwhere(self, *expressions):
        self._where = self._add_query_clauses(
            self._where, expressions, operator.or_)

    @returns_clone
    def join(self, dest, join_type=None, on=None):
        src = self._query_ctx
        if on is None:
            require_join_condition = join_type != JOIN.CROSS and (
                    isinstance(dest, SelectQuery) or
                    (isclass(dest) and not src._meta.rel_exists(dest)))
            if require_join_condition:
                raise ValueError('A join condition must be specified.')
        elif join_type == JOIN.CROSS:
            raise ValueError('A CROSS join cannot have a constraint.')
        elif isinstance(on, basestring):
            on = src._meta.fields[on]
        self._joins.setdefault(src, [])
        self._joins[src].append(Join(src, dest, join_type, on))
        if not isinstance(dest, SelectQuery):
            self._query_ctx = dest

    @returns_clone
    def switch(self, model_class=None):
        """Change or reset the query context."""
        self._query_ctx = model_class or self.model_class

    def ensure_join(self, lm, rm, on=None, **join_kwargs):
        ctx = self._query_ctx
        for join in self._joins.get(lm, []):
            if join.dest == rm:
                return self
        return self.switch(lm).join(rm, on=on, **join_kwargs).switch(ctx)

    def convert_dict_to_node(self, qdict):
        accum = []
        joins = []
        relationship = (ForeignKeyField, ReverseRelationDescriptor)
        for key, value in sorted(qdict.items()):
            curr = self.model_class
            if '__' in key and key.rsplit('__', 1)[1] in DJANGO_MAP:
                key, op = key.rsplit('__', 1)
                op = DJANGO_MAP[op]
            elif value is None:
                op = OP.IS
            else:
                op = OP.EQ
            for piece in key.split('__'):
                model_attr = getattr(curr, piece)
                if value is not None and isinstance(model_attr, relationship):
                    curr = model_attr.rel_model
                    joins.append(model_attr)
            accum.append(Expression(model_attr, op, value))
        return accum, joins

    def filter(self, *args, **kwargs):
        # normalize args and kwargs into a new expression
        dq_node = Node()
        if args:
            dq_node &= reduce(operator.and_, [a.clone() for a in args])
        if kwargs:
            dq_node &= DQ(**kwargs)

        # dq_node should now be an Expression, lhs = Node(), rhs = ...
        q = deque([dq_node])
        dq_joins = set()
        while q:
            curr = q.popleft()
            if not isinstance(curr, Expression):
                continue
            for side, piece in (('lhs', curr.lhs), ('rhs', curr.rhs)):
                if isinstance(piece, DQ):
                    query, joins = self.convert_dict_to_node(piece.query)
                    dq_joins.update(joins)
                    expression = reduce(operator.and_, query)
                    # Apply values from the DQ object.
                    expression._negated = piece._negated
                    expression._alias = piece._alias
                    setattr(curr, side, expression)
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

    def compiler(self):
        return self.database.compiler()

    def sql(self):
        raise NotImplementedError

    def _execute(self):
        sql, params = self.sql()
        return self.database.execute_sql(sql, params, self.require_commit)

    def execute(self):
        raise NotImplementedError

    def scalar(self, as_tuple=False, convert=False):
        if convert:
            row = self.tuples().first()
        else:
            row = self._execute().fetchone()
        if row and not as_tuple:
            return row[0]
        else:
            return row


class RawQuery(Query):
    """
    Execute a SQL query, returning a standard iterable interface that returns
    model instances.
    """

    def __init__(self, model, query, *params):
        self._sql = query
        self._params = list(params)
        self._qr = None
        self._tuples = False
        self._dicts = False
        super(RawQuery, self).__init__(model)

    def clone(self):
        query = RawQuery(self.model_class, self._sql, *self._params)
        query._tuples = self._tuples
        query._dicts = self._dicts
        return query

    join = not_allowed('joining')
    where = not_allowed('where')
    switch = not_allowed('switch')

    @returns_clone
    def tuples(self, tuples=True):
        self._tuples = tuples

    @returns_clone
    def dicts(self, dicts=True):
        self._dicts = dicts

    def sql(self):
        return self._sql, self._params

    def execute(self):
        if self._qr is None:
            if self._tuples:
                QRW = self.database.get_result_wrapper(RESULTS_TUPLES)
            elif self._dicts:
                QRW = self.database.get_result_wrapper(RESULTS_DICTS)
            else:
                QRW = self.database.get_result_wrapper(RESULTS_NAIVE)
            self._qr = QRW(self.model_class, self._execute(), None)
        return self._qr

    def __iter__(self):
        return iter(self.execute())




def allow_extend(orig, new_val, **kwargs):
    extend = kwargs.pop('extend', False)
    if kwargs:
        raise ValueError('"extend" is the only valid keyword argument.')
    if extend:
        return ((orig or []) + new_val) or None
    elif new_val:
        return new_val



class SelectQuery(Query):
    _node_type = 'select_query'

    def __init__(self, model_class, *selection):
        super(SelectQuery, self).__init__(model_class)
        self.require_commit = self.database.commit_select
        self.__select(*selection)
        self._from = None
        self._group_by = None
        self._having = None
        self._order_by = None
        self._windows = None
        self._limit = None
        self._offset = None
        self._distinct = False
        self._for_update = None
        self._naive = False
        self._tuples = False
        self._dicts = False
        self._namedtuples = False
        self._aggregate_rows = False
        self._alias = None
        self._qr = None

    def _clone_attributes(self, query):
        query = super(SelectQuery, self)._clone_attributes(query)
        query._explicit_selection = self._explicit_selection
        query._select = list(self._select)
        if self._from is not None:
            query._from = []
            for f in self._from:
                if isinstance(f, Node):
                    query._from.append(f.clone())
                else:
                    query._from.append(f)
        if self._group_by is not None:
            query._group_by = list(self._group_by)
        if self._having:
            query._having = self._having.clone()
        if self._order_by is not None:
            query._order_by = list(self._order_by)
        if self._windows is not None:
            query._windows = list(self._windows)
        query._limit = self._limit
        query._offset = self._offset
        query._distinct = self._distinct
        query._for_update = self._for_update
        query._naive = self._naive
        query._tuples = self._tuples
        query._dicts = self._dicts
        query._namedtuples = self._namedtuples
        query._aggregate_rows = self._aggregate_rows
        query._alias = self._alias
        return query

    def compound_op(operator):
        def inner(self, other):
            supported_ops = self.model_class._meta.database.compound_operations
            if operator not in supported_ops:
                raise ValueError(
                    'Your database does not support %s' % operator)
            return CompoundSelect(self.model_class, self, operator, other)

        return inner

    _compound_op_static = staticmethod(compound_op)
    __or__ = compound_op('UNION')
    __and__ = compound_op('INTERSECT')
    __sub__ = compound_op('EXCEPT')

    def __xor__(self, rhs):
        # Symmetric difference, should just be (self | rhs) - (self & rhs)...
        wrapped_rhs = self.model_class.select(SQL('*')).from_(
            EnclosedClause((self & rhs)).alias('_')).order_by()
        return (self | rhs) - wrapped_rhs

    def union_all(self, rhs):
        return SelectQuery._compound_op_static('UNION ALL')(self, rhs)

    def __select(self, *selection):
        self._explicit_selection = len(selection) > 0
        selection = selection or self.model_class._meta.declared_fields
        self._select = self._model_shorthand(selection)

    select = returns_clone(__select)

    @returns_clone
    def from_(self, *args):
        self._from = list(args) if args else None

    @returns_clone
    def group_by(self, *args, **kwargs):
        self._group_by = self._model_shorthand(args) if args else None

    @returns_clone
    def having(self, *expressions):
        self._having = self._add_query_clauses(self._having, expressions)

    @returns_clone
    def order_by(self, *args, **kwargs):
        self._order_by = allow_extend(self._order_by, list(args), **kwargs)

    @returns_clone
    def window(self, *windows, **kwargs):
        self._windows = allow_extend(self._windows, list(windows), **kwargs)

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
    def for_update(self, for_update=True, nowait=False):
        self._for_update = 'FOR UPDATE NOWAIT' if for_update and nowait else \
            'FOR UPDATE' if for_update else None

    @returns_clone
    def with_lock(self, lock_type='UPDATE'):
        self._for_update = ('FOR %s' % lock_type) if lock_type else None

    @returns_clone
    def naive(self, naive=True):
        self._naive = naive

    @returns_clone
    def tuples(self, as_tuples=True):
        self._tuples = as_tuples
        if as_tuples:
            self._dicts = self._namedtuples = False

    @returns_clone
    def dicts(self,as_dicts=True):
        self._dicts = as_dicts
        if as_dicts:
            self._tuples = self._namedtuples = False

    @returns_clone
    def namedtuples(self, as_namedtuples=True):
        self._namedtuples = as_namedtuples
        if as_namedtuples:
            self._dicts = self._tuples = False

    @returns_clone
    def aggregate_rows(self, aggregate_rows=True):
        self._aggregate_rows = aggregate_rows

    @returns_clone
    def alias(self, alias=None):
        self._alias = alias

    def annotate(self, rel_model, annotation=None):
        if annotation is None:
            annotation = fn.Count(rel_model._meta.primary_key).alias('count')
        if self._query_ctx == rel_model:
            query = self.switch(self.model_class)
        else:
            query = self.clone()
        query = query.ensure_join(query._query_ctx, rel_model)
        if not query._group_by:
            query._group_by = [x.alias() for x in query._select]
        query._select = tuple(query._select) + (annotation,)
        return query

    def _aggregate(self, aggregation=None):
        if aggregation is None:
            aggregation = fn.Count(SQL('*'))
        query = self.order_by()
        query._select = [aggregation]
        return query

    def aggregate(self, aggregation=None, convert=True):
        return self._aggregate(aggregation).scalar(convert=convert)

    def count(self, clear_limit=False):
        if self._distinct or self._group_by or self._limit or self._offset:
            return self.wrapped_count(clear_limit=clear_limit)

        # defaults to a count() of the primary key
        return self.aggregate(convert=False) or 0

    def wrapped_count(self, clear_limit=False):
        clone = self.order_by()
        if clear_limit:
            clone._limit = clone._offset = None

        sql, params = clone.sql()
        wrapped = 'SELECT COUNT(1) FROM (%s) AS wrapped_select' % sql
        rq = self.model_class.raw(wrapped, *params)
        return rq.scalar() or 0

    def exists(self):
        clone = self.paginate(1, 1)
        clone._select = [SQL('1')]
        return bool(clone.scalar())

    def get(self):
        clone = self.paginate(1, 1)
        try:
            return next(clone.execute())
        except StopIteration:
            raise self.model_class.DoesNotExist(
                'Instance matching query does not exist:\nSQL: %s\nPARAMS: %s'
                % self.sql())

    def peek(self, n=1):
        res = self.execute()
        res.fill_cache(n)
        models = res._result_cache[:n]
        if models:
            return models[0] if n == 1 else models

    def first(self, n=1):
        if self._limit != n:
            self._limit = n
            self._dirty = True
        return self.peek(n=n)

    def sql(self):
        return self.compiler().generate_select(self)

    def verify_naive(self):
        model_class = self.model_class
        for node in self._select:
            if isinstance(node, Field) and node.model_class != model_class:
                return False
            elif isinstance(node, Node) and node._bind_to is not None:
                if node._bind_to != model_class:
                    return False
        return True

    def get_query_meta(self):
        return (self._select, self._joins)

    def _get_result_wrapper(self):
        if self._tuples:
            return self.database.get_result_wrapper(RESULTS_TUPLES)
        elif self._dicts:
            return self.database.get_result_wrapper(RESULTS_DICTS)
        elif self._namedtuples:
            return self.database.get_result_wrapper(RESULTS_NAMEDTUPLES)
        elif self._naive or not self._joins or self.verify_naive():
            return self.database.get_result_wrapper(RESULTS_NAIVE)
        elif self._aggregate_rows:
            return self.database.get_result_wrapper(RESULTS_AGGREGATE_MODELS)
        else:
            return self.database.get_result_wrapper(RESULTS_MODELS)

    def execute(self):
        if self._dirty or self._qr is None:
            model_class = self.model_class
            query_meta = self.get_query_meta()
            ResultWrapper = self._get_result_wrapper()
            self._qr = ResultWrapper(model_class, self._execute(), query_meta)
            self._dirty = False
            return self._qr
        else:
            return self._qr

    def __iter__(self):
        return iter(self.execute())

    def iterator(self):
        return iter(self.execute().iterator())

    def __getitem__(self, value):
        res = self.execute()
        if isinstance(value, slice):
            index = value.stop
        else:
            index = value
        if index is not None:
            index = index + 1 if index >= 0 else None
        res.fill_cache(index)
        return res._result_cache[value]

    def __len__(self):
        return len(self.execute())

    def __hash__(self):
            return id(self)




def ensure_tuple(value):
    '''确保元组'''
    if value is not None:
        return value if isinstance(value, (list, tuple)) else (value,)

class ManyToManyQuery(SelectQuery):
    def __init__(self, instance, accessor, rel, *args, **kwargs):
        self._instance = instance
        self._accessor = accessor
        self._src_attr = accessor.src_fk.rel_field.name
        self._dest_attr = accessor.dest_fk.rel_field.name
        super(ManyToManyQuery, self).__init__(rel, (rel,), *args, **kwargs)

    def _id_list(self, model_or_id_list):
        from brick.core.db.models import Model
        if isinstance(model_or_id_list[0], Model):
            return [getattr(obj, self._dest_attr) for obj in model_or_id_list]
        return model_or_id_list

    def add(self, value, clear_existing=False):
        if clear_existing:
            self.clear()

        accessor = self._accessor
        src_id = getattr(self._instance, self._src_attr)
        if isinstance(value, SelectQuery):
            query = value.columns(
                Value(src_id),
                accessor.dest_fk.rel_field)
            accessor.through_model.insert_from(
                fields=[accessor.src_fk, accessor.dest_fk],
                query=query).execute()
        else:
            value = ensure_tuple(value)
            if not value: return

            inserts = [{
                accessor.src_fk.name: src_id,
                accessor.dest_fk.name: rel_id}
                for rel_id in self._id_list(value)]
            accessor.through_model.insert_many(inserts).execute()

    def remove(self, value):
        src_id = getattr(self._instance, self._src_attr)
        if isinstance(value, SelectQuery):
            column = getattr(value.model, self._dest_attr)
            subquery = value.columns(column)
            return (self._accessor.through_model
                    .delete()
                    .where(
                (self._accessor.dest_fk << subquery) &
                (self._accessor.src_fk == src_id))
                    .execute())
        else:
            value = ensure_tuple(value)
            if not value:
                return
            return (self._accessor.through_model
                    .delete()
                    .where(
                (self._accessor.dest_fk << self._id_list(value)) &
                (self._accessor.src_fk == src_id))
                    .execute())

    def clear(self):
        src_id = getattr(self._instance, self._src_attr)
        return (self._accessor.through_model
                .delete()
                .where(self._accessor.src_fk == src_id)
                .execute())



JoinMetadata = namedtuple('JoinMetadata', (
    'src_model',  # Source Model class.
    'dest_model',  # Dest Model class.
    'src',  # Source, may be Model, ModelAlias
    'dest',  # Dest, may be Model, ModelAlias, or SelectQuery.
    'attr',  # Attribute name joined instance(s) should be assigned to.
    'primary_key',  # Primary key being joined on.
    'foreign_key',  # Foreign key being joined from.
    'is_backref',  # Is this a backref, i.e. 1 -> N.
    'alias',  # Explicit alias given to join expression.
    'is_self_join',  # Is this a self-join?
    'is_expression',  # Is the join ON clause an Expression?
))

class Join(namedtuple('_Join', ('src', 'dest', 'join_type', 'on'))):
    def get_foreign_key(self, source, dest, field=None):
        if isinstance(source, SelectQuery) or isinstance(dest, SelectQuery):
            return None, None
        fk_field = source._meta.rel_for_model(dest, field)
        if fk_field is not None:
            return fk_field, False
        reverse_rel = source._meta.reverse_rel_for_model(dest, field)
        if reverse_rel is not None:
            return reverse_rel, True
        return None, None

    def get_join_type(self):
        return self.join_type or JOIN.INNER

    def model_from_alias(self, model_or_alias):
        if isinstance(model_or_alias, ModelAlias):
            return model_or_alias.model_class
        elif isinstance(model_or_alias, SelectQuery):
            return model_or_alias.model_class
        return model_or_alias

    def _join_metadata(self):
        # Get the actual tables being joined.
        src = self.model_from_alias(self.src)
        dest = self.model_from_alias(self.dest)

        join_alias = isinstance(self.on, Node) and self.on._alias or None
        is_expression = isinstance(self.on, (Expression, Func, SQL))

        on_field = isinstance(self.on, (Field, FieldProxy)) and self.on or None
        if on_field:
            fk_field = on_field
            is_backref = on_field.name not in src._meta.fields
        else:
            fk_field, is_backref = self.get_foreign_key(src, dest, self.on)
            if fk_field is None and self.on is not None:
                fk_field, is_backref = self.get_foreign_key(src, dest)

        if fk_field is not None:
            primary_key = fk_field.to_field
        else:
            primary_key = None

        if not join_alias:
            if fk_field is not None:
                if is_backref:
                    target_attr = dest._meta.db_table
                else:
                    target_attr = fk_field.name
            else:
                try:
                    target_attr = self.on.lhs.name
                except AttributeError:
                    target_attr = dest._meta.db_table
        else:
            target_attr = None

        return JoinMetadata(
            src_model=src,
            dest_model=dest,
            src=self.src,
            dest=self.dest,
            attr=join_alias or target_attr,
            primary_key=primary_key,
            foreign_key=fk_field,
            is_backref=is_backref,
            alias=join_alias,
            is_self_join=src is dest,
            is_expression=is_expression)

    @property
    def metadata(self):
        if not hasattr(self, '_cached_metadata'):
            self._cached_metadata = self._join_metadata()
        return self._cached_metadata


class NoopSelectQuery(SelectQuery):
    def sql(self):
        return (self.database.get_noop_sql(), ())

    def get_query_meta(self):
        return None, None

    def _get_result_wrapper(self):
        return self.database.get_result_wrapper(RESULTS_TUPLES)


class CompoundSelect(SelectQuery):
    _node_type = 'compound_select_query'

    def __init__(self, model_class, lhs=None, operator=None, rhs=None):
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs
        super(CompoundSelect, self).__init__(model_class, [])

    def _clone_attributes(self, query):
        query = super(CompoundSelect, self)._clone_attributes(query)
        query.lhs = self.lhs
        query.operator = self.operator
        query.rhs = self.rhs
        return query

    def count(self, clear_limit=False):
        return self.wrapped_count(clear_limit=clear_limit)

    def get_query_meta(self):
        return self.lhs.get_query_meta()

    def verify_naive(self):
        return self.lhs.verify_naive() and self.rhs.verify_naive()

    def _get_result_wrapper(self):
        if self._tuples:
            return self.database.get_result_wrapper(RESULTS_TUPLES)
        elif self._dicts:
            return self.database.get_result_wrapper(RESULTS_DICTS)
        elif self._namedtuples:
            return self.database.get_result_wrapper(RESULTS_NAMEDTUPLES)
        elif self._aggregate_rows:
            return self.database.get_result_wrapper(RESULTS_AGGREGATE_MODELS)

        has_joins = self.lhs._joins or self.rhs._joins
        is_naive = self.lhs._naive or self.rhs._naive or self._naive
        if is_naive or not has_joins or self.verify_naive():
            return self.database.get_result_wrapper(RESULTS_NAIVE)
        else:
            return self.database.get_result_wrapper(RESULTS_MODELS)


class _WriteQuery(Query):
    def __init__(self, model_class):
        self._returning = None
        self._tuples = False
        self._dicts = False
        self._namedtuples = False
        self._qr = None
        super(_WriteQuery, self).__init__(model_class)

    def _clone_attributes(self, query):
        query = super(_WriteQuery, self)._clone_attributes(query)
        if self._returning:
            query._returning = list(self._returning)
            query._tuples = self._tuples
            query._dicts = self._dicts
            query._namedtuples = self._namedtuples
        return query

    def requires_returning(method):
        def inner(self, *args, **kwargs):
            db = self.model_class._meta.database
            if not db.returning_clause:
                raise ValueError('RETURNING is not supported by your '
                                 'database: %s' % type(db))
            return method(self, *args, **kwargs)

        return inner

    @requires_returning
    @returns_clone
    def returning(self, *selection):
        if len(selection) == 1 and selection[0] is None:
            self._returning = None
        else:
            if not selection:
                selection = self.model_class._meta.declared_fields
            self._returning = self._model_shorthand(selection)

    @requires_returning
    @returns_clone
    def tuples(self, tuples=True):
        self._tuples = tuples
        if tuples:
            self._dicts = self._namedtuples = False

    @requires_returning
    @returns_clone
    def dicts(self, dicts=True):
        self._dicts = dicts
        if dicts:
            self._tuples = self._namedtuples = False

    @requires_returning
    @returns_clone
    def namedtuples(self, namedtuples=True):
        self._namedtuples = namedtuples
        if namedtuples:
            self._dicts = self._tuples = False

    def get_result_wrapper(self):
        if self._returning is not None:
            if self._tuples:
                return self.database.get_result_wrapper(RESULTS_TUPLES)
            elif self._dicts:
                return self.database.get_result_wrapper(RESULTS_DICTS)
            elif self._namedtuples:
                return self.database.get_result_wrapper(RESULTS_NAMEDTUPLES)
        return self.database.get_result_wrapper(RESULTS_NAIVE)

    def _execute_with_result_wrapper(self):
        ResultWrapper = self.get_result_wrapper()
        meta = (self._returning, {self.model_class: []})
        self._qr = ResultWrapper(self.model_class, self._execute(), meta)
        return self._qr


class UpdateQuery(_WriteQuery):
    def __init__(self, model_class, update=None):
        self._update = update
        self._on_conflict = None
        super(UpdateQuery, self).__init__(model_class)

    def _clone_attributes(self, query):
        query = super(UpdateQuery, self)._clone_attributes(query)
        query._update = dict(self._update)
        query._on_conflict = self._on_conflict
        return query

    @returns_clone
    def on_conflict(self, action=None):
        self._on_conflict = action

    join = not_allowed('joining')

    def sql(self):
        return self.compiler().generate_update(self)

    def execute(self):
        if self._returning is not None and self._qr is None:
            return self._execute_with_result_wrapper()
        elif self._qr is not None:
            return self._qr
        else:
            return self.database.rows_affected(self._execute())

    def __iter__(self):
        if not self.model_class._meta.database.returning_clause:
            raise ValueError('UPDATE queries cannot be iterated over unless '
                             'they specify a RETURNING clause, which is not '
                             'supported by your database.')
        return iter(self.execute())

    def iterator(self):
        return iter(self.execute().iterator())


class InsertQuery(_WriteQuery):
    def __init__(self, model_class, field_dict=None, rows=None,
                 fields=None, query=None, validate_fields=False):
        super(InsertQuery, self).__init__(model_class)

        self._upsert = False
        self._is_multi_row_insert = rows is not None or query is not None
        self._return_id_list = False
        if rows is not None:
            self._rows = rows
        else:
            self._rows = [field_dict or {}]

        self._fields = fields
        self._query = query
        self._validate_fields = validate_fields
        self._on_conflict = None

    def _iter_rows(self):
        model_meta = self.model_class._meta
        if self._validate_fields:
            valid_fields = model_meta.valid_fields

            def validate_field(field):
                if field not in valid_fields:
                    raise KeyError('"%s" is not a recognized field.' % field)

        defaults = model_meta._default_dict
        callables = model_meta._default_callables

        for row_dict in self._rows:
            field_row = defaults.copy()
            seen = set()
            for key in row_dict:
                if self._validate_fields:
                    validate_field(key)
                if key in model_meta.fields:
                    field = model_meta.fields[key]
                else:
                    field = key
                field_row[field] = row_dict[key]
                seen.add(field)
            if callables:
                for field in callables:
                    if field not in seen:
                        field_row[field] = callables[field]()
            yield field_row

    def _clone_attributes(self, query):
        query = super(InsertQuery, self)._clone_attributes(query)
        query._rows = self._rows
        query._upsert = self._upsert
        query._is_multi_row_insert = self._is_multi_row_insert
        query._fields = self._fields
        query._query = self._query
        query._return_id_list = self._return_id_list
        query._validate_fields = self._validate_fields
        query._on_conflict = self._on_conflict
        return query

    join = not_allowed('joining')
    where = not_allowed('where clause')

    @returns_clone
    def upsert(self, upsert=True):
        self._upsert = upsert

    @returns_clone
    def on_conflict(self, action=None):
        self._on_conflict = action

    @returns_clone
    def return_id_list(self, return_id_list=True):
        self._return_id_list = return_id_list

    @property
    def is_insert_returning(self):
        if self.database.insert_returning:
            if not self._is_multi_row_insert or self._return_id_list:
                return True
        return False

    def sql(self):
        return self.compiler().generate_insert(self)

    def _insert_with_loop(self):
        id_list = []
        last_id = None
        return_id_list = self._return_id_list
        for row in self._rows:
            last_id = (InsertQuery(self.model_class, row)
                       .upsert(self._upsert)
                       .execute())
            if return_id_list:
                id_list.append(last_id)

        if return_id_list:
            return id_list
        else:
            return last_id

    def execute(self):
        insert_with_loop = (
                self._is_multi_row_insert and
                self._query is None and
                self._returning is None and
                not self.database.insert_many)
        if insert_with_loop:
            return self._insert_with_loop()

        if self._returning is not None and self._qr is None:
            return self._execute_with_result_wrapper()
        elif self._qr is not None:
            return self._qr
        else:
            cursor = self._execute()
            if not self._is_multi_row_insert:
                if self.database.insert_returning:
                    pk_row = cursor.fetchone()
                    meta = self.model_class._meta
                    clean_data = [
                        field.python_value(column)
                        for field, column
                        in zip(meta.get_primary_key_fields(), pk_row)]
                    if self.model_class._meta.composite_key:
                        return clean_data
                    return clean_data[0]
                return self.database.last_insert_id(cursor, self.model_class)
            elif self._return_id_list:
                return map(operator.itemgetter(0), cursor.fetchall())
            else:
                return True


class DeleteQuery(_WriteQuery):
    join = not_allowed('joining')

    def sql(self):
        return self.compiler().generate_delete(self)

    def execute(self):
        if self._returning is not None and self._qr is None:
            return self._execute_with_result_wrapper()
        elif self._qr is not None:
            return self._qr
        else:
            return self.database.rows_affected(self._execute())

