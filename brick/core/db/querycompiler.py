#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:26
# @Author  : Cojun  Mao
# @Site    : 
# @File    : querycompiler.py
# @Project : mysite_diy
# @Software: PyCharm
import hashlib
import operator
from inspect import isclass

from brick.core.db.felds import ForeignKeyField, Field, CommaClause, Node, Clause, Expression, Func, \
    Entity, _StripParens, SQL, EnclosedClause, Param
from brick.core.db.modelquerys import ModelAlias, CompoundSelect
from brick.core.db.models import Model
from brick.core.db.utils import OP, merge_dict, strip_parens, JOIN



class AliasMap(object):
    '''别名'''
    prefix = 't'  # 前缀

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
        self._parse_map = self.get_parse_map()
        self._unknown_types = set(['param'])

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

    def get_op(self, q):
        return self._op_map[q]

    def _sorted_fields(self, field_dict):
        return sorted(field_dict.items(), key=lambda i: i[0]._sort_key)

    def _parse_default(self, node, alias_map, conv):
        return self.interpolation, [node]

    def _parse_expression(self, node, alias_map, conv):
        if isinstance(node.lhs, Field):
            conv = node.lhs
        lhs, lparams = self.parse_node(node.lhs, alias_map, conv)
        rhs, rparams = self.parse_node(node.rhs, alias_map, conv)
        if node.op == OP.IN and rhs == '()' and not rparams:
            return ('0 = 1' if node.flat else '(0 = 1)'), []
        template = '%s %s %s' if node.flat else '(%s %s %s)'
        sql = template % (lhs, self.get_op(node.op), rhs)
        return sql, lparams + rparams

    def _parse_passthrough(self, node, alias_map, conv):
        if node.adapt:
            return self.parse_node(node.adapt(node.value), alias_map, None)
        return self.interpolation, [node.value]

    def _parse_param(self, node, alias_map, conv):
        if node.adapt:
            if conv and conv.db_value is node.adapt:
                conv = None
            return self.parse_node(node.adapt(node.value), alias_map, conv)
        elif conv is not None:
            return self.parse_node(conv.db_value(node.value), alias_map)
        else:
            return self.interpolation, [node.value]

    def _parse_func(self, node, alias_map, conv):
        conv = node._coerce and conv or None
        sql, params = self.parse_node_list(node.arguments, alias_map, conv)
        return '%s(%s)' % (node.name, strip_parens(sql)), params

    def _parse_clause(self, node, alias_map, conv):
        sql, params = self.parse_node_list(
            node.nodes, alias_map, conv, node.glue)
        if node.parens:
            sql = '(%s)' % strip_parens(sql)
        return sql, params

    def _parse_entity(self, node, alias_map, conv):
        return '.'.join(map(self.quote, node.path)), []  # map() 会根据提供的函数对指定序列做映射。

    def _parse_sql(self, node, alias_map, conv):
        return node.value, list(node.params)

    def _parse_field(self, node, alias_map, conv):
        if alias_map:
            sql = '.'.join((
                self.quote(alias_map[node.model_class]),
                self.quote(node.db_column)))
        else:
            sql = self.quote(node.db_column)
        return sql, []

    def _parse_composite_key(self, node, alias_map, conv):
        fields = []
        for field_name in node.field_names:
            fields.append(node.model_class._meta.fields[field_name])
        return self._parse_clause(CommaClause(*fields), alias_map, conv)

    def _parse_compound_select_query(self, node, alias_map, conv):
        csq = 'compound_select_query'
        lhs, rhs = node.lhs, node.rhs
        inv = rhs._node_type == csq and lhs._node_type != csq
        if inv:
            lhs, rhs = rhs, lhs

        new_map = self.alias_map_class()
        if lhs._node_type == csq:
            new_map._counter = alias_map._counter

        sql1, p1 = self.generate_select(lhs, new_map)
        sql2, p2 = self.generate_select(rhs, self.calculate_alias_map(rhs,
                                                                      new_map))

        # We add outer parentheses in the event the compound query is used in
        # the `from_()` clause, in which case we'll need them.
        if node.database.compound_select_parentheses:
            if lhs._node_type != csq:
                sql1 = '(%s)' % sql1
            if rhs._node_type != csq:
                sql2 = '(%s)' % sql2

        if inv:
            sql1, p1, sql2, p2 = sql2, p2, sql1, p1

        return '(%s %s %s)' % (sql1, node.operator, sql2), (p1 + p2)

    def _parse_select_query(self, node, alias_map, conv):
        clone = node.clone()
        if not node._explicit_selection:
            if conv and isinstance(conv, ForeignKeyField):
                clone._select = (conv.to_field,)
            else:
                clone._select = clone.model_class._meta.get_primary_key_fields()
        sub, params = self.generate_select(clone, alias_map)
        return '(%s)' % strip_parens(sub), params

    def _parse_strip_parens(self, node, alias_map, conv):
        sql, params = self.parse_node(node.node, alias_map, conv)
        return strip_parens(sql), params

    def _parse(self, node, alias_map, conv):
        # By default treat the incoming node as a raw value that should be
        # parameterized.
        # 默认情况下，将传入节点视为原始值
        # 参数化。

        node_type = getattr(node, '_node_type', None)
        unknown = False
        if node_type in self._parse_map:
            sql, params = self._parse_map[node_type](node, alias_map, conv)
            unknown = (node_type in self._unknown_types and
                       node.adapt is None and
                       conv is None)
        elif isinstance(node, (list, tuple, set)):
            # If you're wondering how to pass a list into your query, simply
            # wrap it in Param().
            # 如果您想知道如何将列表传递到查询中，只需
            # 将其包装在Param（）中。
            sql, params = self.parse_node_list(node, alias_map, conv)
            sql = '(%s)' % sql
        elif isinstance(node, Model):
            sql = self.interpolation
            if conv and isinstance(conv, ForeignKeyField):
                to_field = conv.to_field
                if isinstance(to_field, ForeignKeyField):
                    value = conv.db_value(node)
                else:
                    value = to_field.db_value(getattr(node, to_field.name))
            else:
                value = node._get_pk_value()
            params = [value]
        elif (isclass(node) and issubclass(node, Model)) or \
                isinstance(node, ModelAlias):
            entity = node.as_entity().alias(alias_map[node])
            sql, params = self.parse_node(entity, alias_map, conv)
        elif conv is not None:
            value = conv.db_value(node)
            sql, params, _ = self._parse(value, alias_map, None)
        else:
            sql, params = self._parse_default(node, alias_map, None)
            unknown = True

        return sql, params, unknown

    def parse_node(self, node, alias_map=None, conv=None):
        sql, params, unknown = self._parse(node, alias_map, conv)
        if unknown and (conv is not None) and params:
            params = [conv.db_value(i) for i in params]

        if isinstance(node, Node):
            if node._negated:
                sql = 'NOT %s' % sql
            if node._alias:
                sql = ' '.join((sql, 'AS', node._alias))
            if node._ordering:
                sql = ' '.join((sql, node._ordering))

        if params and any(isinstance(p, Node) for p in params):
            clean_params = []
            clean_sql = []
            for idx, param in enumerate(params):
                if isinstance(param, Node):
                    csql, cparams = self.parse_node(param)

        return sql, params

    def parse_node_list(self, nodes, alias_map, conv=None, glue=', '):
        sql = []
        params = []
        for node in nodes:
            node_sql, node_params = self.parse_node(node, alias_map, conv)
            sql.append(node_sql)
            params.extend(node_params)
        return glue.join(sql), params

    def calculate_alias_map(self, query, alias_map=None):
        new_map = self.alias_map_class()
        if alias_map is not None:
            new_map._counter = alias_map._counter

        new_map.add(query.model_class, query.model_class._meta.table_alias)
        for src_model, joined_models in query._joins.items():
            new_map.add(src_model, src_model._meta.table_alias)
            for join_obj in joined_models:
                if isinstance(join_obj.dest, Node):
                    new_map.add(join_obj.dest, join_obj.dest.alias)
                else:
                    new_map.add(join_obj.dest, join_obj.dest._meta.table_alias)

        return new_map.update(alias_map)

    def build_query(self, clauses, alias_map=None):
        return self.parse_node(Clause(*clauses), alias_map)

    def generate_joins(self, joins, model_class, alias_map):
        # Joins are implemented as an adjancency-list graph. Perform a
        # depth-first search of the graph to generate all the necessary JOINs.
        # 连接被实现为邻接列表图。执行
        # 深度优先搜索图形以生成所有必要的JOIN。
        clauses = []
        seen = set()
        q = [model_class]
        while q:
            curr = q.pop()
            if curr not in joins or curr in seen:
                continue
            seen.add(curr)
            for join in joins[curr]:
                src = curr
                dest = join.dest
                join_type = join.get_join_type()
                if isinstance(join.on, (Expression, Func, Clause, Entity)):
                    # Clear any alias on the join expression.
                    constraint = join.on.clone().alias()
                elif join_type != JOIN.CROSS:
                    metadata = join.metadata
                    if metadata.is_backref:
                        fk_model = join.dest
                        pk_model = join.src
                    else:
                        fk_model = join.src
                        pk_model = join.dest

                    fk = metadata.foreign_key
                    if fk:
                        lhs = getattr(fk_model, fk.name)
                        rhs = getattr(pk_model, fk.to_field.name)
                        if metadata.is_backref:
                            lhs, rhs = rhs, lhs
                        constraint = (lhs == rhs)
                    else:
                        raise ValueError('Missing required join predicate.')

                if isinstance(dest, Node):
                    # TODO: ensure alias?
                    dest_n = dest
                else:
                    q.append(dest)
                    dest_n = dest.as_entity().alias(alias_map[dest])

                join_sql = SQL(self.join_map.get(join_type) or join_type)
                if join_type == JOIN.CROSS:
                    clauses.append(Clause(join_sql, dest_n))
                else:
                    clauses.append(Clause(join_sql, dest_n, SQL('ON'),
                                          constraint))

        return clauses

    def generate_select(self, query, alias_map=None):
        model = query.model_class
        db = model._meta.database

        alias_map = self.calculate_alias_map(query, alias_map)

        if isinstance(query, CompoundSelect):
            clauses = [_StripParens(query)]
        else:
            if not query._distinct:
                clauses = [SQL('SELECT')]
            else:
                clauses = [SQL('SELECT DISTINCT')]
                if query._distinct not in (True, False):
                    clauses += [SQL('ON'), EnclosedClause(*query._distinct)]

            select_clause = Clause(*query._select)
            select_clause.glue = ', '

            clauses.extend((select_clause, SQL('FROM')))
            if query._from is None:
                clauses.append(model.as_entity().alias(alias_map[model]))
            else:
                clauses.append(CommaClause(*query._from))

        join_clauses = self.generate_joins(query._joins, model, alias_map)
        if join_clauses:
            clauses.extend(join_clauses)

        if query._where is not None:
            clauses.extend([SQL('WHERE'), query._where])

        if query._group_by:
            clauses.extend([SQL('GROUP BY'), CommaClause(*query._group_by)])

        if query._having:
            clauses.extend([SQL('HAVING'), query._having])
        # https: // zhuanlan.zhihu.com / p / 455084260
        if query._windows is not None:
            clauses.append(SQL('WINDOW'))
            clauses.append(CommaClause(*[
                Clause(
                    SQL(window._alias),
                    SQL('AS'),
                    window.__sql__())
                for window in query._windows]))

        if query._order_by:
            clauses.extend([SQL('ORDER BY'), CommaClause(*query._order_by)])

        if query._limit is not None or (query._offset and db.limit_max):
            limit = query._limit if query._limit is not None else db.limit_max
            # print('limit ', limit,db.limit_max)
            clauses.append(SQL('LIMIT %d' % limit))
        if query._offset is not None:
            clauses.append(SQL('OFFSET %d' % query._offset))

        if query._for_update:
            clauses.append(SQL(query._for_update))

        return self.build_query(clauses, alias_map)

    def generate_update(self, query):
        model = query.model_class
        alias_map = self.alias_map_class()
        alias_map.add(model, model._meta.db_table)
        if query._on_conflict:
            statement = 'UPDATE OR %s' % query._on_conflict
        else:
            statement = 'UPDATE'
        clauses = [SQL(statement), model.as_entity(), SQL('SET')]

        update = []
        for field, value in self._sorted_fields(query._update):
            if not isinstance(value, (Node, Model)):
                value = Param(value, adapt=field.db_value)
            update.append(Expression(
                field.as_entity(with_table=False),
                OP.EQ,
                value,
                flat=True))  # No outer parens, no table alias.
        clauses.append(CommaClause(*update))

        if query._where:
            clauses.extend([SQL('WHERE'), query._where])

        if query._returning is not None:
            returning_clause = Clause(*query._returning)
            returning_clause.glue = ', '
            clauses.extend([SQL('RETURNING'), returning_clause])

        return self.build_query(clauses, alias_map)

    def _get_field_clause(self, fields, clause_type=EnclosedClause):
        return clause_type(*[
            field.as_entity(with_table=False) for field in fields])

    def generate_insert(self, query):
        model = query.model_class
        meta = model._meta
        alias_map = self.alias_map_class()
        alias_map.add(model, model._meta.db_table)
        if query._upsert:
            statement = meta.database.upsert_sql
        elif query._on_conflict:
            statement = 'INSERT OR %s INTO' % query._on_conflict
        else:
            statement = 'INSERT INTO'
        clauses = [SQL(statement), model.as_entity()]

        if query._query is not None:
            # This INSERT query is of the form INSERT INTO ... SELECT FROM.
            if query._fields:
                clauses.append(self._get_field_clause(query._fields))
            clauses.append(_StripParens(query._query))

        elif query._rows is not None:
            fields, value_clauses = [], []
            have_fields = False

            for row_dict in query._iter_rows():
                if not have_fields:
                    fields = sorted(
                        row_dict.keys(), key=operator.attrgetter('_sort_key'))
                    have_fields = True

                values = []
                for field in fields:
                    value = row_dict[field]
                    if not isinstance(value, (Node, Model)):
                        value = Param(value, adapt=field.db_value)
                    values.append(value)

                value_clauses.append(EnclosedClause(*values))

            if fields:
                clauses.extend([
                    self._get_field_clause(fields),
                    SQL('VALUES'),
                    CommaClause(*value_clauses)])
            elif query.model_class._meta.auto_increment:
                # Bare insert, use default value for primary key.
                clauses.append(query.database.default_insert_clause(
                    query.model_class))

        if query.is_insert_returning:
            clauses.extend([
                SQL('RETURNING'),
                self._get_field_clause(
                    meta.get_primary_key_fields(),
                    clause_type=CommaClause)])
        elif query._returning is not None:
            returning_clause = Clause(*query._returning)
            returning_clause.glue = ', '
            clauses.extend([SQL('RETURNING'), returning_clause])

        return self.build_query(clauses, alias_map)

    def generate_delete(self, query):
        model = query.model_class
        clauses = [SQL('DELETE FROM'), model.as_entity()]
        if query._where:
            clauses.extend([SQL('WHERE'), query._where])
        if query._returning is not None:
            returning_clause = Clause(*query._returning)
            returning_clause.glue = ', '
            clauses.extend([SQL('RETURNING'), returning_clause])
        return self.build_query(clauses)

    def field_definition(self, field):
        column_type = self.get_column_type(field.get_db_field())
        ddl = field.__ddl__(column_type)
        return Clause(*ddl)

    def foreign_key_constraint(self, field):
        ddl = [
            SQL('FOREIGN KEY'),
            EnclosedClause(field.as_entity()),
            SQL('REFERENCES'),
            field.rel_model.as_entity(),
            EnclosedClause(field.to_field.as_entity())]
        if field.on_delete:
            ddl.append(SQL('ON DELETE %s' % field.on_delete))
        if field.on_update:
            ddl.append(SQL('ON UPDATE %s' % field.on_update))
        return Clause(*ddl)

    def return_parsed_node(function_name):
        # TODO: treat all `generate_` functions as returning clauses, instead
        # of SQL/params.
        def inner(self, *args, **kwargs):
            fn = getattr(self, function_name)
            return self.parse_node(fn(*args, **kwargs))

        return inner

    def _create_foreign_key(self, model_class, field, constraint=None):
        constraint = constraint or 'fk_%s_%s_refs_%s' % (
            model_class._meta.db_table,
            field.db_column,
            field.rel_model._meta.db_table)
        fk_clause = self.foreign_key_constraint(field)
        return Clause(
            SQL('ALTER TABLE'),
            model_class.as_entity(),
            SQL('ADD CONSTRAINT'),
            Entity(constraint),
            *fk_clause.nodes)

    create_foreign_key = return_parsed_node('_create_foreign_key')

    def _create_table(self, model_class, safe=False):
        statement = 'CREATE TABLE IF NOT EXISTS' if safe else 'CREATE TABLE'
        meta = model_class._meta

        columns, constraints = [], []
        if meta.composite_key:
            pk_cols = [meta.fields[f].as_entity()
                       for f in meta.primary_key.field_names]
            constraints.append(Clause(
                SQL('PRIMARY KEY'), EnclosedClause(*pk_cols)))
        for field in meta.declared_fields:
            columns.append(self.field_definition(field))
            if isinstance(field, ForeignKeyField) and not field.deferred:
                constraints.append(self.foreign_key_constraint(field))

        if model_class._meta.constraints:
            for constraint in model_class._meta.constraints:
                if not isinstance(constraint, Node):
                    constraint = SQL(constraint)
                constraints.append(constraint)

        return Clause(
            SQL(statement),
            model_class.as_entity(),
            EnclosedClause(*(columns + constraints)))

    create_table = return_parsed_node('_create_table')

    def _drop_table(self, model_class, fail_silently=False, cascade=False):
        statement = 'DROP TABLE IF EXISTS' if fail_silently else 'DROP TABLE'
        ddl = [SQL(statement), model_class.as_entity()]
        if cascade:
            ddl.append(SQL('CASCADE'))
        return Clause(*ddl)

    drop_table = return_parsed_node('_drop_table')

    def _truncate_table(self, model_class, restart_identity=False,
                        cascade=False):
        ddl = [SQL('TRUNCATE TABLE'), model_class.as_entity()]
        if restart_identity:
            ddl.append(SQL('RESTART IDENTITY'))
        if cascade:
            ddl.append(SQL('CASCADE'))
        return Clause(*ddl)

    truncate_table = return_parsed_node('_truncate_table')

    def index_name(self, table, columns):
        index = '%s_%s' % (table, '_'.join(columns))
        if len(index) > 64:
            index_hash = hashlib.md5(index.encode('utf-8')).hexdigest()
            index = '%s_%s' % (table[:55], index_hash[:8])  # 55 + 1 + 8 = 64
        return index

    def _create_index(self, model_class, fields, unique, *extra):
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

    create_index = return_parsed_node('_create_index')

    def _drop_index(self, model_class, fields, fail_silently=False):
        tbl_name = model_class._meta.db_table
        statement = 'DROP INDEX IF EXISTS' if fail_silently else 'DROP INDEX'
        index_name = self.index_name(tbl_name, [f.db_column for f in fields])
        return Clause(SQL(statement), Entity(index_name))

    drop_index = return_parsed_node('_drop_index')

    def _create_sequence(self, sequence_name):
        return Clause(SQL('CREATE SEQUENCE'), Entity(sequence_name))

    create_sequence = return_parsed_node('_create_sequence')

    def _drop_sequence(self, sequence_name):
        return Clause(SQL('DROP SEQUENCE'), Entity(sequence_name))

    drop_sequence = return_parsed_node('_drop_sequence')


class SqliteQueryCompiler(QueryCompiler):
    def truncate_table(self, model_class, restart_identity=False,
                       cascade=False):
        return model_class.delete().sql()
