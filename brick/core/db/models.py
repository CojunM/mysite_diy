#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:23
# @Author  : Cojun  Mao
# @Site    : 
# @File    : model.py
# @Project : mysite_diy
# @Software: PyCharm
import collections
import itertools

import re
from bisect import bisect_right, bisect_left  # Python3二分查找库函数
from copy import deepcopy

from brick.core.db.exceptions import IntegrityError
from brick.core.db.modelquerys import InsertQuery, UpdateQuery, DeleteQuery, SelectQuery, ModelAlias, RawQuery, \
    NoopSelectQuery
from brick.core.db.felds import Field, PrimaryKeyField, FieldDescriptor, ForeignKeyField, CompositeKey, Entity, Node, \
    ManyToManyField
from brick.core.db.utils import DeferredRelation

_DictQueryResultWrapper = _ModelQueryResultWrapper = _SortedFieldList = \
    _TuplesQueryResultWrapper = None


class DoesNotExist(Exception):
    pass


class _SortedFieldList(object):
    __slots__ = ('_keys', '_items')

    def __init__(self):
        self._keys = []
        self._items = []

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, item):
        k = item._sort_key
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, field):
        return self._keys.index(field._sort_key)

    def insert(self, item):
        k = item._sort_key
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        idx = self.index(item)
        del self._items[idx]
        del self._keys[idx]



class ModelOptions(object):
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

        self.database = database #if database is not None else default_database
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
        self.valid_fields = (set(self.fields.keys()) |
                             set(self.fields.values()) |
                             set((self.primary_key,)))
        self.declared_fields = [field for field in self.sorted_fields
                                if not field.undeclared]

    def add_field(self, field):
        self.remove_field(field.name)
        self.fields[field.name] = field
        self.columns[field.db_column] = field

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
    inheritable = set(['constraints', 'database', 'db_table_func', 'indexes', 'order_by',
                       'primary_key', 'schema', 'validate_backrefs', 'only_save_dirty'])

    def __new__(cls, name, bases, attrs):
        # 假定用户创建的类是父类Model,不进行任何操作，因为需要修改的是用户自定义类
        if name == "Model":
            return super().__new__(cls, name, bases, attrs)
        # Meta类的属性通过meta_options存储在类中
        meta_options = {}
        meta = attrs.pop('Meta', None)
        if meta:
            for k, v in meta.__dict__.items():
                # 将Meta从属性中移除，将Meta中的非私有属性加入meta_options中
                if not k.startswith('_'):
                    meta_options[k] = v

        model_pk = getattr(meta, 'primary_key', None)
        pk_name = parent_pk = None

        # inherit any field descriptors by deep copying the underlying field obj
        # into the attrs of the new model, additionally see if the bases define
        # inheritable model options and swipe them
        for b in bases:
            if not hasattr(b, '_meta'):
                continue
            # 获取父类中Meta类的属性
            base_meta = getattr(b, '_meta')
            if parent_pk is None:
                parent_pk = deepcopy(base_meta.primary_key)
            all_inheritable = cls.inheritable | base_meta._additional_keys
            # 一个k, v 类似于 id : IntegerField('id')
            # 其中k是id，v是IntegerField的一个实例
            for (k, v) in base_meta.__dict__.items():
                if k in all_inheritable and k not in meta_options:
                    meta_options[k] = v

            # 获取父类中的Fields, 即表的字段
            for (k, v) in b.__dict__.items():
                if isinstance(v, FieldDescriptor) and k not in attrs:
                    if not v.field.primary_key:
                        attrs[k] = deepcopy(v.field)

        # initialize the new class and set the magic attributes
        cls = super().__new__(cls, name, bases, attrs)
        ModelOptionsBase = meta_options.get('model_options_base', ModelOptions)
        cls._meta = ModelOptionsBase(cls, **meta_options)
        cls._data = None
        cls._meta.indexes = list(cls._meta.indexes)
        # primary_key = None
        if not cls._meta.db_table:
            # 默认表名的设定，Model名的小写，然后将非数字和英文字符换成'_'
            cls._meta.db_table = re.sub('[^\w]+', '_', cls.__name__.lower())
        # replace the fields with field descriptors, calling the add_to_class hook
        # 这里筛选attr中的Field类型字段，设置Model中的数据类型
        # 也许可以测试一下类里面的函数是怎么继承的
        # fields = []
        for name, attr in list(cls.__dict__.items()):
            # for name, attr in cls.__dict__.items():
            if isinstance(attr, Field):
                if attr.primary_key and model_pk:
                    raise ValueError('primary key is overdetermined.')
                elif attr.primary_key:
                    model_pk, pk_name = attr, name
                else:
                    attr.add_to_class(cls, name)
                    # fields.append((attr, name))
                # if attr.primary_key:
                #     primary_key = attr

        if model_pk is None:
            if parent_pk:
                model_pk, pk_name = parent_pk, parent_pk.name
            else:
                model_pk, pk_name = PrimaryKeyField(primary_key=True), 'id'
        # if not primary_key:
        #     primary_key = PrimaryKeyField(primary_key=True)
        #     primary_key.add_to_class(cls, 'id')
        composite_key = False  # 复合键
        if isinstance(model_pk, CompositeKey):
            pk_name = '_composite_key'
            composite_key = True

        if model_pk is not False:
            model_pk.add_to_class(cls, pk_name)
            cls._meta.primary_key = model_pk
            cls._meta.auto_increment = (
                    isinstance(model_pk, PrimaryKeyField) or
                    bool(model_pk.sequence))
            cls._meta.composite_key = composite_key
        # cls._meta.primary_key = primary_key
        # cls._meta.auto_increment = isinstance(primary_key, PrimaryKeyField) or primary_key.sequence
        # for field, name in fields:
        #     field.add_to_class(cls, name)
        # create a repr and error class before finalizing
        if hasattr(cls, '__unicode__'):
            setattr(cls, '__repr__', lambda self: '<%s: %r>' % (
                cls.__name__, self.__unicode__()))

        exception_class = type('%sDoesNotExist' % cls.__name__, (DoesNotExist,), {'__module__': cls.__module__})
        cls.DoesNotExist = exception_class
        cls._meta.prepared()
        if hasattr(cls, 'validate_model'):
            cls.validate_model()

        DeferredRelation.resolve(cls)
        return cls

    def __iter__(self):
        return iter(self.select())


class Model(metaclass=ModelMetaclass):

    def __init__(self, **kwargs):
        self._data = self._meta.get_default_dict()
        self._obj_cache = {}  # cache of related objects
        self._dirty = set(self._data)  # j加的

        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def alias(cls):
        return ModelAlias(cls)

    @classmethod
    def select(cls, *selection):
        query = SelectQuery(cls, *selection)
        if cls._meta.order_by:
            query = query.order_by(*cls._meta.order_by)
        return query

    @classmethod
    def update(cls, __data=None, **update):
        fdict = __data or {}
        fdict.update([(cls._meta.fields[f], update[f]) for f in update])
        return UpdateQuery(cls, fdict)

    @classmethod
    def insert(cls, __data=None, **insert):
        fdict = __data or {}
        fdict.update([(cls._meta.fields[f], insert[f]) for f in insert])
        return InsertQuery(cls, fdict)

    @classmethod
    def insert_many(cls, rows, validate_fields=True):
        return InsertQuery(cls, rows=rows, validate_fields=validate_fields)

    @classmethod
    def insert_from(cls, fields, query):
        return InsertQuery(cls, fields=fields, query=query)

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
        inst._prepare_instance()
        return inst

    @classmethod
    def get(cls, *query, **filters):
        # sq = cls.select()
        sq = cls.select().naive()
        if query:
            sq = sq.where(*query)
        if filters:
            sq = sq.filter(**filters)
        return sq.get()

    @classmethod
    def get_or_create(cls, **kwargs):
        defaults = kwargs.pop('defaults', {})
        query = cls.select()
        for field, value in kwargs.items():
            if '__' in field:
                query = query.filter(**{field: value})
            else:
                query = query.where(getattr(cls, field) == value)

        try:
            return query.get(), False
        except cls.DoesNotExist:
            try:
                params = dict((k, v) for k, v in kwargs.items()
                              if '__' not in k)
                params.update(defaults)
                with cls._meta.database.atomic():
                    return cls.create(**params), True
            except IntegrityError as exc:
                try:
                    return query.get(), False
                except cls.DoesNotExist:
                    raise exc

    @classmethod
    def filter(cls, *dq, **query):
        return cls.select().filter(*dq, **query)

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

    @classmethod
    def _fields_to_index(cls):
        fields = []
        for field in cls._meta.sorted_fields:
            if field.primary_key:
                continue
            requires_index = any((
                field.index,
                field.unique,
                isinstance(field, ForeignKeyField)))
            if requires_index:
                fields.append(field)
        return fields

    @classmethod
    def _index_data(cls):
        return itertools.chain(
            [((field,), field.unique) for field in cls._fields_to_index()],
            cls._meta.indexes or ())

    @classmethod
    def _create_indexes(cls):
        for field_list, is_unique in cls._index_data():
            cls._meta.database.create_index(cls, field_list, is_unique)

    @classmethod
    def _drop_indexes(cls, safe=False):
        for field_list, is_unique in cls._index_data():
            cls._meta.database.drop_index(cls, field_list, safe)

    @classmethod
    def sqlall(cls):
        queries = []
        compiler = cls._meta.database.compiler()
        pk = cls._meta.primary_key
        if cls._meta.database.sequences and pk.sequence:
            queries.append(compiler.create_sequence(pk.sequence))
        queries.append(compiler.create_table(cls))
        for field in cls._fields_to_index():
            queries.append(compiler.create_index(cls, [field], field.unique))
        if cls._meta.indexes:
            for field_names, unique in cls._meta.indexes:
                fields = [cls._meta.fields[f] for f in field_names]
                queries.append(compiler.create_index(cls, fields, unique))
        return [sql for sql, _ in queries]

    @classmethod
    def drop_table(cls, fail_silently=False, cascade=False):
        cls._meta.database.drop_table(cls, fail_silently, cascade)

    @classmethod
    def truncate_table(cls, restart_identity=False, cascade=False):
        cls._meta.database.truncate_table(cls, restart_identity, cascade)

    @classmethod
    def as_entity(cls):
        if cls._meta.schema:
            return Entity(cls._meta.schema, cls._meta.db_table)
        return Entity(cls._meta.db_table)

    @classmethod
    def noop(cls, *args, **kwargs):
        return NoopSelectQuery(cls, *args, **kwargs)

    def _get_pk_value(self):
        return getattr(self, self._meta.primary_key.name)

    get_id = _get_pk_value  # Backwards-compatibility.

    def _set_pk_value(self, value):
        if not self._meta.composite_key:
            setattr(self, self._meta.primary_key.name, value)

    set_id = _set_pk_value  # Backwards-compatibility.

    def _pk_expr(self):
        return self._meta.primary_key == self._get_pk_value()

    def _prepare_instance(self):
        self._dirty.clear()
        self.prepared()

    def prepared(self):
        pass

    def _prune_fields(self, field_dict, only):
        new_data = {}
        for field in only:
            if field.name in field_dict:
                new_data[field.name] = field_dict[field.name]
        return new_data

    def _populate_unsaved_relations(self, field_dict):
        for key in self._meta.rel:
            conditions = (
                    key in self._dirty and
                    key in field_dict and
                    field_dict[key] is None and
                    self._obj_cache.get(key) is not None)
            if conditions:
                setattr(self, key, getattr(self, key))
                field_dict[key] = self._data[key]

    def save(self, force_insert=False, only=None):
        field_dict = dict(self._data)
        if self._meta.primary_key is not False:
            pk_field = self._meta.primary_key
            pk_value = self._get_pk_value()
        else:
            pk_field = pk_value = None
        if only:
            field_dict = self._prune_fields(field_dict, only)
        elif self._meta.only_save_dirty and not force_insert:
            field_dict = self._prune_fields(
                field_dict,
                self.dirty_fields)
            if not field_dict:
                self._dirty.clear()
                return False

        self._populate_unsaved_relations(field_dict)
        if pk_value is not None and not force_insert:
            if self._meta.composite_key:
                for pk_part_name in pk_field.field_names:
                    field_dict.pop(pk_part_name, None)
            else:
                field_dict.pop(pk_field.name, None)
            rows = self.update(**field_dict).where(self._pk_expr()).execute()
        elif pk_field is None:
            self.insert(**field_dict).execute()
            rows = 1
        else:
            pk_from_cursor = self.insert(**field_dict).execute()
            if pk_from_cursor is not None:
                pk_value = pk_from_cursor
            self._set_pk_value(pk_value)
            rows = 1
        self._dirty.clear()
        return rows

    def is_dirty(self):
        '''返回布尔值，指示是否手动设置了任何字段。'''
        return bool(self._dirty)

    # 模型实例上的脏字段。 脏表示内存中的字段和数据库值不同
    @property
    def dirty_fields(self):
        '''返回已修改的字段列表。'''
        return [f for f in self._meta.sorted_fields if f.name in self._dirty]

    def dependencies(self, search_nullable=False):
        '''依赖关系'''
        model_class = type(self)
        query = self.select().where(self._pk_expr())
        stack = [(type(self), query)]
        seen = set()

        while stack:
            klass, query = stack.pop()
            if klass in seen:
                continue
            seen.add(klass)
            for rel_name, fk in klass._meta.reverse_rel.items():
                rel_model = fk.model_class
                if fk.rel_model is model_class:
                    node = (fk == self._data[fk.to_field.name])
                    subquery = rel_model.select().where(node)
                else:
                    node = fk << query
                    subquery = rel_model.select().where(node)
                if not fk.null or search_nullable:
                    stack.append((rel_model, subquery))
                yield (node, fk)

    def delete_instance(self, recursive=False, delete_nullable=False):
        if recursive:
            dependencies = self.dependencies(delete_nullable)
            for query, fk in reversed(list(dependencies)):
                model = fk.model_class
                if fk.null and not delete_nullable:
                    model.update(**{fk.name: None}).where(query).execute()
                else:
                    model.delete().where(query).execute()
        return self.delete().where(self._pk_expr()).execute()

    def __hash__(self):
        return hash((self.__class__, self._get_pk_value()))

    def __eq__(self, other):
        return (
                other.__class__ == self.__class__ and
                self._get_pk_value() is not None and
                other._get_pk_value() == self._get_pk_value())

    def __ne__(self, other):
        return not self == other
