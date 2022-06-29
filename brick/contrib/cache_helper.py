#!/usr/bin/env python
# coding=utf-8

# import redis
import datetime

# from common import log_helper
# from config import redis_config
#
# # 设置redis配置参数
# _redis = redis_config.REDIS
# # 初始化Redis缓存链接

# try:
#     if not r:
#         r = redis.Redis(host=_redis.get('server', ''),
#                         port=_redis.get('post', ''),
#                         db=_redis.get('db', ''),
#                         password=_redis.get('pwd', ''),
#                         socket_timeout=1,
#                         socket_connect_timeout=1)
# except Exception as e:
#     log_helper.info('连接redis出错:(' + str(_redis) + ')' + str(e.args))
#     pass
from brick.contrib import log_helper


import time


class Value:
    def __init__(self, value, put_time, expired):
        """
        缓存值对象

        :param value: 具体的值
        :param put_time: 放入缓存的时间
        :param expired: 缓存失效时间
        """
        self.value = value
        self.put_time = put_time
        self.expired = expired

    def __str__(self):
        return f"value: {self.value}  put_time: {self.put_time}  expired: {self.expired}"


"""
基于内存缓存
使用 memory_cache 实例即可
"""
class MemoryCache:

    def __init__(self):
        self.__cache = {}

    def set_value(self, k, v, expired):
        """
        将值放入缓存中

        :param k: 缓存的 key
        :param v: 缓存值
        :param expired: 缓存失效时间，单位秒(s)
        """
        current_timestamp = int(time.time())  # 获取当前时间戳 10 位 秒级
        value = Value(v, current_timestamp, expired)
        # print('set_value')
        self.__cache[k] = value
        log_helper.info("已放入缓存, key: {  % s} {%s}"%( k, value))


    def check_key(self, k):
        """
        检查缓存是否可用

        :param k: 缓存 key
        :return: True or False
        """
        current_timestamp = int(time.time())
        value = self.__cache.get(k, None)
        # print('check_key')
        # 考虑k不存在的情况
        if value is None:
            return False
        differ = current_timestamp - value.put_time
        if differ > value.expired:
            del self.__cache[k]  # 证明缓存失效了，删除键值对
            log_helper.info("缓存已失效, key: {%s}"% k)
            return False
        return True

    def get_value(self, k):
        """
        通过缓存key获取值
        :param k: key
        :return: value
        """
        if self.check_key(k):
            return self.__cache[k].value
            # print('get_value')
        return None
    def delete(self,k):
        del self.__cache[k]

    def clear(self):
        self.__cache.clear()

memory_cache = MemoryCache()
def set(key, value, time=86400):
    """
    写缓存
    :param key: 缓存key，字符串，不区分大小写
    :param value: 要存储的值
    :param time: 缓存过期时间（单位：秒），0=永不过期
    :return:
    """
    # 将key转换为小写字母
    key = str(key).lower()
    try:
        # r.set(key, value, time)
        memory_cache.set_value(key,value,time)
    except Exception as e:
        log_helper.info('写缓存失败:key(' + key + '), ' + str(e.args))
        pass


def get(key):
    """
    读缓存
    :param key: 缓存key，字符串，不区分大小写
    :return:
    """
    # 将key转换为小写字母
    key = str(key).lower()
    try:
        value = memory_cache.get_value(key)
    except Exception as e:
        log_helper.error('读缓存失败:key(' + key + '), ' + str(e.args) )
        value = None

    return _str_to_json(value)


def delete(key):
    """
    删除缓存
    :param key:缓存key，字符串，不区分大小写
    :return:
    """
    # 将key转换为小写字母
    key = str(key).lower()
    try:
        memory_cache.delete(key)
        log_helper.info('删除缓存:' +str(key))
    except Exception as e:
        log_helper.info('Exception:' + str(e.args))
        pass


def clear():
    """
    清空所有缓存
    """
    try:
        memory_cache.clear()
    except:
        pass
# def push(key, value):
#     """
#     添加数据到队列头部
#     :param key: 缓存key，字符串，不区分大小写
#     :param value: 要存储的值
#     """
#     # 将key转换为小写字母
#     key = str(key).lower()
#     try:
#         r.lpush(key, value)
#     except Exception as e:
#         log_helper.info('写缓存失败:key(' + key + ')' + str(e.args))
#         pass
#
#
# def pop(key):
#     """
#     从缓存队列的后尾读取一条数据
#     :param key: 缓存key，字符串，不区分大小写
#     :return: 缓存数据
#     """
#     # 将key转换为小写字母
#     key = str(key).lower()
#     try:
#         value = r.pop(key)
#     except Exception as e:
#         log_helper.info('读取缓存队列失败:key(' + key + ')' + str(e.args))
#         value = None
#
#     return _str_to_json(value)


def _str_to_json(value):
    """
    将缓存中读取出来的字符串转换成对应的数据、元组、列表或字典
    """
    if not value:
        return value
    # 否则直接转换
    try:
        value = value.decode()
        return eval(value)
    except Exception as e:
        print(e.args)
        pass
    # 否则直接输出字符串
    return value



