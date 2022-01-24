#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:29
# @Author  : Cojun  Mao
# @Site    : 
# @File    : test_iter.py
# @Project : mysite_diy
# @Software: PyCharm
from bisect import bisect_left, bisect_right


class MyRange(object):
    def __init__(self, end):
        self.start = 0
        self.end = end

    def __iter__(self):
        return self

    def __getitem__(self, i):
        return self.end[i]
    # def __next__(self):
    #     if self.start < self.end:
    #         ret = self.start
    #         self.start += 1
    #         return ret
    #     else:
    #         raise StopIteration


class Field:
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
        self._sort_key = (self.primary_key and 1 or 2), self._order


class _SortedFieldList(object):
    __slots__ = ('_keys', '_items')

    def __init__(self):
        self._keys = []
        self._items = []

    # def __getitem__(self, i):
    #     return self._items[i]

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


from collections.abc import *

if __name__ == "__main__":
    # a = MyRange(5)
    i = 0
    f = Field()
    a = _SortedFieldList()
    while i < 5:
        a.insert(f)
        i+=1
    print(isinstance(a, Iterable))
    print(isinstance(a, Iterator))
    for i in a:
    # for i in list(a):
        print(i)
