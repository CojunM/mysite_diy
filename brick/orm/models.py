#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:23
# @Author  : Cojun  Mao
# @Site    : 
# @File    : model.py
# @Project : mysite_diy
# @Software: PyCharm
import re
from copy import deepcopy
from brick.orm.modelquerys import InsertQuery, UpdateQuery, DeleteQuery, SelectQuery
from brick.orm.felds import Field, PrimaryKeyField, FieldDescriptor, ForeignKeyField



class ModelOptions(object):
    def __init__(self, cls, database=None, db_table=None, indexes=None,
                 order_by=None, primary_key=None):
        self.model_class = cls
        self.name = cls.__name__.lower()
        self.fields = {}
        self.columns = {}
        self.defaults = {}

        self.database = database
        self.db_table = db_table
        self.indexes = indexes or []
        self.order_by = order_by
        self.primary_key = primary_key

        self.auto_increment = None
        self.rel = {}
        self.reverse_rel = {}

    def prepared(self):
        """
        准备数据
        :return:
        """
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


class DoesNotExist(Exception):
    pass


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
        # 这里筛选attr中的Field类型字段，设置Model中的数据类型
        # 也许可以测试一下类里面的函数是怎么继承的
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
            # 默认表名的设定，Model名的小写，然后将非数字和英文字符换成'_'
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
        # print('11111')
        fdict = dict((cls._meta.fields[f], v) for f, v in update.items())
        return UpdateQuery(cls, fdict)

    @classmethod
    def insert(cls, **insert):
        fdict = dict((cls._meta.fields[f], v) for f, v in insert.items())
        return InsertQuery(cls, fdict)

    @classmethod
    def delete(cls):
        return DeleteQuery(cls)

    @classmethod
    def select(cls, *selection):
        query = SelectQuery(cls, *selection)
        if cls._meta.order_by:
            query = query.order_by(*cls._meta.order_by)
        return query

    @classmethod
    def get(cls, *query, **kwargs):
        sq = cls.select().naive()
        if query:
            sq = sq.where(*query)
        if kwargs:
            sq = sq.filter(**kwargs)
        return sq.get()
    def get_id(self):
        """
        获取主键值
        :return:
        """
        return getattr(self, self._meta.primary_key.name)

    def set_id(self, id):
        setattr(self, self._meta.primary_key.name, id)

    def save(self, force_insert=False, only=None):
        """
        保存
        :param force_insert: 强制插入
        :param only:
        :return:
        """
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
    def prepared(self):
        pass