#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:16
# @Author  : CJ  Mao
# @Site    : 
# @File    : dicthelper.py
# @Project : mysite_diy
# @Software: PyCharm
import functools
from collections import MutableMapping
from configparser import ConfigParser
# https://www.jianshu.com/p/755807cf2cdf\
# Python 的 collections.abc 模块内拥有 Mapping 和 MutableMapping
# 这两个抽象基类，它们为 dict 和其他类似的类型提供了接口定义。
from collections.abc import MutableMapping as DictMixin

class ConfigDict(dict):
    """ A dict-like configuration storage with additional support for
        namespaces, validators, meta-data, on_change listeners and more.

        This storage is optimized for fast read access. Retrieving a key
        or using non-altering dict methods (e.g. `dict.get()`) has no overhead
        compared to a native dict.
    """
    __slots__ = ('_meta', '_on_change')

    class Namespace(MutableMapping):
        def __init__(self, config, namespace):
            self._config = config
            self._prefix = namespace

        def __getitem__(self, key):
            # depr('Accessing namespaces as dicts is discouraged. '
            #      'Only use flat item access: '
            # 'cfg["names"]["pace"]["key"] -> cfg["name.space.key"]')  # 0.12
            return self._config[self._prefix + '.' + key]

        def __setitem__(self, key, value):
            self._config[self._prefix + '.' + key] = value

        def __delitem__(self, key):
            del self._config[self._prefix + '.' + key]

        def __iter__(self):
            ns_prefix = self._prefix + '.'
            for key in self._config:
                ns, dot, name = key.rpartition('.')
                if ns == self._prefix and name:
                    yield name

        def keys(self):
            return [x for x in self]

        def __len__(self):
            return len(self.keys())

        def __contains__(self, key):
            return self._prefix + '.' + key in self._config

        def __repr__(self):
            return '<Config.Namespace %s.*>' % self._prefix

        def __str__(self):
            return '<Config.Namespace %s.*>' % self._prefix

        # Deprecated ConfigDict features
        def __getattr__(self, key):
            # depr('Attribute access is deprecated.')  # 0.12
            if key not in self and key[0].isupper():
                self[key] = ConfigDict.Namespace(self._config, self._prefix + '.' + key)
            if key not in self and key.startswith('__'):
                raise AttributeError(key)
            return self.get(key)

        def __setattr__(self, key, value):
            if key in ('_config', '_prefix'):
                self.__dict__[key] = value
                return
            # depr('Attribute assignment is deprecated.')  # 0.12
            if hasattr(DictMixin, key):
                raise AttributeError('Read-only attribute.')
            if key in self and self[key] and isinstance(self[key], self.__class__):
                raise AttributeError('Non-empty namespace attribute.')
            self[key] = value

        def __delattr__(self, key):
            if key in self:
                val = self.pop(key)
                if isinstance(val, self.__class__):
                    prefix = key + '.'
                    for key in self:
                        if key.startswith(prefix):
                            del self[prefix + key]

        def __call__(self, *a, **ka):
            self.update(*a, **ka)
            return self

    def __init__(self, *a, **ka):
        self._meta = {}
        self._on_change = lambda name, value: None
        if a or ka:
            # depr('Constructor does no longer accept parameters.')  # 0.12
            self.update(*a, **ka)

    def load_config(self, filename):
        ''' Load values from an *.ini style config file.

            If the config file contains sections, their names are used as
            namespaces for the values within. The two special sections
            ``DEFAULT`` and ``bottle`` refer to the root namespace (no prefix).
        '''
        conf = ConfigParser()
        conf.read(filename)
        for section in conf.sections():
            for key, value in conf.items(section):
                if section not in ('DEFAULT', 'bottle'):
                    key = section + '.' + key
                self[key] = value
        return self

    def load_dict(self, source, namespace='', make_namespaces=False):
        ''' Import values from a dictionary structure. Nesting can be used to
            represent namespaces.

            >>> ConfigDict().load_dict({'name': {'space': {'key': 'value'}}})
            {'name.space.key': 'value'}
        '''
        stack = [(namespace, source)]
        while stack:
            prefix, source = stack.pop()
            if not isinstance(source, dict):
                raise TypeError('Source is not a dict (r)' % type(key))
            for key, value in source.items():
                if not isinstance(key, basestring):
                    raise TypeError('Key is not a string (%r)' % type(key))
                full_key = prefix + '.' + key if prefix else key
                if isinstance(value, dict):
                    stack.append((full_key, value))
                    if make_namespaces:
                        self[full_key] = self.Namespace(self, full_key)
                else:
                    self[full_key] = value
        return self

    def update(self, *a, **ka):
        ''' If the first parameter is a string, all keys are prefixed with this
            namespace. Apart from that it works just as the usual dict.update().
            Example: ``update('some.namespace', key='value')`` '''
        prefix = ''
        if a and isinstance(a[0], str):
            prefix = a[0].strip('.') + '.'
            a = a[1:]
        for key, value in dict(*a, **ka).items():
            self[prefix + key] = value

    def setdefault(self, key, value):
        if key not in self:
            self[key] = value
        return self[key]

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError('Key has type %r (not a string)' % type(key))

        value = self.meta_get(key, 'filter', lambda x: x)(value)
        if key in self and self[key] is value:
            return
        self._on_change(key, value)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def clear(self):
        for key in self:
            del self[key]

    def meta_get(self, key, metafield, default=None):
        ''' Return the value of a meta field for a key. '''
        return self._meta.get(key, {}).get(metafield, default)

    def meta_set(self, key, metafield, value):
        ''' Set the meta field for a key to a new value. This triggers the
            on-change handler for existing keys. '''
        self._meta.setdefault(key, {})[metafield] = value
        if key in self:
            self[key] = self[key]

    def meta_list(self, key):
        ''' Return an iterable of meta field names defined for a key. '''
        return self._meta.get(key, {}).keys()

    # Python中__get__, __getattr__, __getattribute__的区别及延迟初始化
    # https://www.cnblogs.com/wuzdandz/p/9682328.html
    # Deprecated ConfigDict features
    def __getattr__(self, key):
        # depr('Attribute access is deprecated.')  # 0.12
        if key not in self and key[0].isupper():
            self[key] = self.Namespace(self, key)
        if key not in self and key.startswith('__'):
            raise AttributeError(key)
        return self.get(key)

    def __setattr__(self, key, value):
        if key in self.__slots__:
            return dict.__setattr__(self, key, value)
        depr('Attribute assignment is deprecated.')  # 0.12
        if hasattr(dict, key):
            raise AttributeError('Read-only attribute.')
        if key in self and self[key] and isinstance(self[key], self.Namespace):
            raise AttributeError('Non-empty namespace attribute.')
        self[key] = value

    def __delattr__(self, key):
        if key in self:
            val = self.pop(key)
            if isinstance(val, self.Namespace):
                prefix = key + '.'
                for key in self:
                    if key.startswith(prefix):
                        del self[prefix + key]

    def __call__(self, *a, **ka):
        # depr('Calling ConfDict is deprecated. Use the update() method.')  # 0.12
        self.update(*a, **ka)
        return self


class DictProperty(object):
    """ 属性，该属性映射到本地dict-like属性中的键。
        映射修饰后的property到owner class中的某个类似字典的attribute
        (后文也用property和attribute，而不用属性，以表示区别) """
    def __init__(self, attr, key=None, read_only=False):
        self.attr, self.key, self.read_only = attr, key, read_only

    # 以调用的方法使用装饰器，则被装饰的函数在__call__方法里作为参数传入
    def __call__(self, func):
        # 用update_wrapper的方法把func的__module__，__name__，__doc__赋给装饰后的attribute
        functools.update_wrapper(self, func, updated=[])
        self.getter, self.key = func, self.key or func.__name__
        return self          # 这个attribute是DictProperty的实例

    # 当访问request.GET的时候，就会调用该方法, obj为当前对象，cls为当前类
    # 参数依次为被装饰后的实例，owner class的实例，owner class
    def __get__(self, obj, cls):  # obj则对应将某个属性托管给描述的实例对象的引用，对应的应该为request对象；而cls则为Request类的引用。
        if obj is None: return self  # obj为None说明被装饰的方法作为类变量来访问(Bottle.query)，返回描述符自身
        # getattr() 函数用于返回一个对象属性值
        key, storage = self.key, getattr(obj, self.attr)  # self.attr是owner class的一个attribute
        # key='bottle.get.query'
        # storage = environ 即包含HTTP请求的信息的environ

        # 判断envrion中是否包含key来决定是否需要解析
        # 如果bottle.request.query不在storage也就是不在request.environ中的时候，
        # 在request.environ中添加'bottle.request.query':request.query(self)， 即reqeuest.query(self)的返回值：GET参数的字典.
        # self.getter(obj)就是调用了原来的query方法，不过要传入一个Request实例，也就是obj
        if key not in storage: storage[key] = self.getter(obj)

        return storage[key]

    def __set__(self, obj, value):
        if self.read_only: raise AttributeError("Read-Only property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only: raise AttributeError("Read-Only property.")
        del getattr(obj, self.attr)[self.key]
