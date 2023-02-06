#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 19:29
# @Author  : Cojun  Mao
# @Site    : 
# @File    : util.py
# @Project : mysite_diy
# @Software: PyCharm
import datetime

from brick.core.db.constants import basestring


def returns_clone(func):
    '''
    创建副本,方法修饰符，在应用给定的
    方法这确保以更可预测的方式改变状态，
    并促进方法链的使用。
    :param func:
    :return:
    '''

    def inner(self, *args, **kwargs):
        clone = self.clone()  # 生成新类,假定对象实现“克隆”。
        func(clone, *args, **kwargs)
        return clone

    inner.call_local = func#提供一种无需克隆的呼叫方式。
    return inner

def dict_update(orig, extra):
    new = {}
    new.update(orig)
    new.update(extra)
    return new
def merge_dict(source, overrides):
    merged = source.copy()
    merged.update(overrides)
    return merged

class attrdict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

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
    BITWISE_NEGATION='~'
)

JOIN = attrdict(
    INNER='INNER',
    LEFT_OUTER='LEFT OUTER',
    RIGHT_OUTER='RIGHT OUTER',
    FULL='FULL',
    CROSS='CROSS',
)
DJANGO_MAP = {
    'eq': OP.EQ,
    'lt': OP.LT,
    'lte': OP.LTE,
    'gt': OP.GT,
    'gte': OP.GTE,
    'ne': OP.NE,
    'in': OP.IN,
    'is': OP.IS,
    'like': OP.LIKE,
    'ilike': OP.ILIKE,
    'regexp': OP.REGEXP,
}
unicode = str
# string_type = bytes
# basestring = bytes
datetime=datetime.datetime
def format_unicode(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s
    elif isinstance(s, basestring):
        return s.decode(encoding)
    # Python3的话就只能用__str__方法，如果是Python2的话就使用__unicode__方法。
    elif hasattr(s, '__unicode__'):
        return s.__unicode__()
    else:
        return unicode(bytes(s), encoding)
def format_date_time(value, formats, post_process=None):
    post_process = post_process or (lambda x: x)
    for fmt in formats:
        try:
            return post_process(datetime.strptime(value, fmt))
        except ValueError:
            pass
    return value


def strip_parens(s):
        # Quick sanity check 快速健全性检查.去括号
        if not s or s[0] != '(':
            return s

        ct = i = 0
        l = len(s)
        while i < l:
            if s[i] == '(' and s[l - 1] == ')':
                ct += 1
                i += 1
                l -= 1
            else:
                break
        if ct:
            # If we ever end up with negatively-balanced parentheses, then we
            # know that one of the outer parentheses was required.
            # 如果我们最终使用负平衡括号，那么我们
            # 知道需要一个外括号。
            unbalanced_ct = 0
            required = 0
            for i in range(ct, l - ct):
                if s[i] == '(':
                    unbalanced_ct += 1
                elif s[i] == ')':
                    unbalanced_ct -= 1
                if unbalanced_ct < 0:
                    required += 1
                    unbalanced_ct = 0
                if required == ct:
                    break
            ct -= required
        if ct > 0:
            return s[ct:-ct]
        return s
binary_construct = lambda s: bytes(s.encode('raw_unicode_escape'))


class DeferredRelation(object):
    _unresolved = set()

    def __init__(self, rel_model_name=None):
        self.fields = []
        if rel_model_name is not None:
            self._rel_model_name = rel_model_name.lower()
            self._unresolved.add(self)

    def set_field(self, model_class, field, name):
        self.fields.append((model_class, field, name))

    def set_model(self, rel_model):
        for model, field, name in self.fields:
            field.rel_model = rel_model
            field.add_to_class(model, name)

    @staticmethod
    def resolve(model_cls):
        unresolved = list(DeferredRelation._unresolved)
        for dr in unresolved:
            if dr._rel_model_name == model_cls.__name__.lower():
                dr.set_model(model_cls)
                DeferredRelation._unresolved.discard(dr)

if __name__ == "__main__":
    s= '((new_user.(create)_table))'
    print(strip_parens(s))#new_user.(create)_table