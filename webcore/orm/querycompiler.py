#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:26
# @Author  : Cojun  Mao
# @Site    : 
# @File    : querycompiler.py
# @Project : mysite_diy
# @Software: PyCharm
from webcore.orm.felds import ForeignKeyField, PrimaryKeyField, Field, op_map, Expr, Leaf, Func, Param, Ordering, R
from webcore.orm.modelquerys import SelectQuery
from webcore.orm.models import Model
from webcore.orm.utils import dict_update


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

    def __init__(self, quote_char='"', interpolation='?', field_overrides=None,
                 op_overrides=None):
        self.quote_char = quote_char
        self.interpolation = interpolation
        self._field_map = dict_update(self.field_map, field_overrides or {})
        self._op_map = dict_update(op_map, op_overrides or {})

    def quote(self, s):
        return '%s%s%s' % (self.quote_char, s, self.quote_char)

    def get_op(self, q):
        print(q)
        print(self._op_map[q])
        return self._op_map[q]

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
    #创建序列
    def create_sequence(self, sequence_name):
        return 'CREATE SEQUENCE %s;' % self.quote(sequence_name)

    def parse_insert_query(self, query):
        model = query.model_class

        parts = ['INSERT INTO %s' % self.quote(model._meta.db_table)]
        sets, params = self._parse_field_dictionary(query._insert)

        parts.append('(%s)' % ', '.join(s[0] for s in sets))
        parts.append('VALUES (%s)' % ', '.join(s[1] for s in sets))

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

    def parse_expr(self, expr, alias_map=None, conv=None):
        """解析表达式"""
        s = self.interpolation
        p = [expr]
        if isinstance(expr, Expr):
            # 解析表达式
            if isinstance(expr.lhs, Field):
                conv = expr.lhs
            lhs, lparams = self.parse_expr(expr.lhs, alias_map, conv)
            rhs, rparams = self.parse_expr(expr.rhs, alias_map, conv)
            s = '(%s %s %s)' % (lhs, self.get_op(expr.op), rhs)
            p = lparams + rparams
        elif isinstance(expr, Field):
            # 解析字段
            s = self.quote(expr.db_column)
            if alias_map and expr.model_class in alias_map:
                s = '.'.join((alias_map[expr.model_class], s))
            p = []
        elif isinstance(expr, Func):
            # 解析
            p = []
            exprs = []
            for param in expr.params:
                parsed, params = self.parse_expr(param, alias_map, conv)
                exprs.append(parsed)
                p.extend(params)
            s = '%s(%s)' % (expr.name, ', '.join(exprs))
        elif isinstance(expr, Param):
            # 解析参数
            s = self.interpolation
            p = [expr.data]
        elif isinstance(expr, Ordering):
            # 解析排序
            s, p = self.parse_expr(expr.param, alias_map, conv)
            s += ' ASC' if expr.asc else ' DESC'
        elif isinstance(expr, R):
            # 解析
            s = expr.value
            p = []
        elif isinstance(expr, SelectQuery):
            # 解析查询
            max_alias = self._max_alias(alias_map)
            clone = expr.clone()
            if not expr._explicit_selection:
                clone._select = (clone.model_class._meta.primary_key,)
            subselect, p = self.parse_select_query(clone, max_alias, alias_map)
            s = '(%s)' % subselect
        elif isinstance(expr, (list, tuple)):
            # 解析
            # print('--list, tuple--')
            exprs = []
            p = []
            for i in expr:
                e, v = self.parse_expr(i, alias_map, conv)
                exprs.append(e)
                p.extend(v)
            s = '(%s)' % ','.join(exprs)
        elif isinstance(expr, Model):
            # 解析
            print('--Model--')
            s = self.interpolation
            p = [expr.get_id()]
        elif conv and p:
            # 解析
            # print('--conv and p--')
            p = [conv.db_value(i) for i in p]

        if isinstance(expr, Leaf):
            # 解析
            if expr.negated:
                s = 'NOT %s' % s
            if expr._alias:
                s = ' '.join((s, 'AS', expr._alias))

        return s, p

    def parse_query_node(self, qnode, alias_map):
        if qnode is not None:
            print(qnode)
            return self.parse_expr(qnode, alias_map)
        return '', []

    def parse_delete_query(self, query):
        model = query.model_class
        print(model)
        parts = ['DELETE FROM %s' % self.quote(model._meta.db_table)]
        params = []
        print(query._where)
        where, w_params = self.parse_query_node(query._where, None)
        print('where:  ', where)
        if where:
            print('w_params: ', w_params)
            parts.append('WHERE %s' % where)
            params.extend(w_params)

        return ' '.join(parts), params
