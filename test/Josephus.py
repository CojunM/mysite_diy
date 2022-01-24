#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/9 15:51
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : Josephus.py
# @Project : mysite_diy
# @Software: PyCharm
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""

# 约瑟夫环问题
# 用户输入n，n代表人数，围成一圈，顺序排号
# 从第一个开始报数，1，2，数到1的人，退出圈子
# 报数逻辑，数到3的把对应的位置置为0，直到剩下最后一个人
def num_report(list_create):
    n = 0
    list_size = len(list_create)
    number_stay = list_size  # 剩下的人数（值为1的个数）
    result = []
    while not number_stay == 1:
        for i in range(list_size):
            if list_create[i] == 1:
                n = n + 1
                if n == 1:
                    list_create[i] = 0
                    n = 1
                    number_stay = number_stay - 1
                elif n == 2:
                    n = 0
                    result.append(i + 1)

            if i == list_size:
                i = 0
        print('经过报数逻辑得到的列表是：' + str(result))
        # print('经过报数逻辑得到的列表是：' + str(list_create))
        result.clear()


# 通过报数函数最后生成的新的列表，遍历，找到唯一一个值不是0的人
def remove_num_3(list_create):
    num_report(list_create)
    # print('经过报数逻辑最后得到的列表是：' + str(list_create))
    i = 0
    while i < len(list_create):
        if list_create[i] == 1:
            print('最后剩下的编号是：' + str(i + 1))
            return True
        i = i + 1


# 根据用户输入的人数n，生成列表，同时执行移除动作
def list_create_rm(n):
    try:
        if not n.isdigit():
            return False
    except ValueError as e:
        pass

    nn = int(n)
    i = 0
    # list_create = []
    # while i < nn:
    #     list_create.append(1)
    #     i = i + 1
    list_create = [1,]*nn
    # print('生成的列表是：' + str(list_create))
    remove_num_3(list_create)





if __name__ == '__main__':
   while True:
        n = input('请输入人数：')
        list_create_rm(n)
        # josephus(5, 1)
        # solution_list2(5, 1)
