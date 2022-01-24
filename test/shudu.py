#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/10/28 13:25
# @Author  : Cojun
# @Site    : 
# @File    : shudu.py
# @Software: PyCharm
import copy
import time

# 求每一行单元格行值域
def valueRange(row):
    temp = copy.deepcopy(row)
    row_value_range = list(range(1,10))
    for i in row:
        if i == '':
            continue
        else:
            if row_value_range.count(i) > 0:
                row_value_range.remove(i)
            else:
                continue
    for j in range(9):
        if temp[j] == '':
            temp[j] = row_value_range
        else:
            temp[j] = [temp[j]]
    return temp

# 求数独每个单元格行值域
def rowValueRange(soduku):
    row_value_range = []
    for row in soduku:
        row_value_range.append(valueRange(row))
    return row_value_range

# 求数独每个单元格列值域
def colValueRange(soduku):
    soduku_invert = [list(i) for i in list(zip(*soduku))]
    temp = rowValueRange(soduku_invert)
    s_column_vrange = [list(i) for i in list(zip(*temp))]
    return s_column_vrange

# 将一个数独数组转化为数独九宫格数组
def matrix_invert(lista):
    listb = [[] for i in range(9)]
    for i in range(9):
        for j in range(9):
            k = i//3
            l = j//3
            m = k*3 + l
            listb[m].append(lista[i][j])
    return listb

# 求数独每个单元格九宫格值域
def matrixValueRange(soduku):
    matrix = matrix_invert(soduku)
    temp = rowValueRange(matrix)
    matrix_vrange = matrix_invert(temp)
    return matrix_vrange

# 三个列表求交集函数
def inersection(lista,listb,listc):
    tempa = []
    tempb = []
    for i in lista:
        for j in listb:
            if i == j:
                tempa.append(i)
    for k in listc:
        for l in tempa:
            if k == l:
                tempb.append(k)
    return tempb

#  求数独每个单元格总值域
def totalValueRange(soduku):
    row_value_range = rowValueRange(soduku)
    col_value_range = colValueRange(soduku)
    matrix_value_range = matrixValueRange(soduku)
    total_value_range = [[] for i in range(9)]
    for i in range(9):
        for j in range(9):
            total_value_range[i].append(inersection(row_value_range[i][j],col_value_range[i][j],matrix_value_range[i][j]))
    return total_value_range

# 寻找一行中唯一的值，若该值仅在行值域列表中出现了一次，则其所在单元格取值为该值
def checkUnique(list):
    listb = copy.deepcopy(list)
    templist = []
    for i in listb:
        templist.extend(i)
    for i in range(len(list)):
        for j in list[i]:
            if templist.count(j) == 1:
                listb[i] = [j]
    list = listb
    return list

# 寻找每一行的唯一值，更新值域列表
def row_checkUnique(s_row_vrange):
    temp = []
    for list in s_row_vrange:
        temp.append(checkUnique(list))
    s_row_vrange = temp
    return s_row_vrange

# 检查值域列表每一行、每一列、每一个九宫格的值域，并寻找唯一值，更新值域列表
def soduku_checkUnique(s_row_vrange):
    temp = []
    temp_b = []
    s_row_vrange = row_checkUnique(s_row_vrange)
    for i in list(zip(*s_row_vrange)):# 将数独进行行列转换，然后对每一列进行唯一值检测
        temp.append(list(i))
    temp = row_checkUnique(temp)
    for i in list(zip(*temp)):
        temp_b.append(list(i))
    temp_c = matrix_invert(temp_b)# 将数独进行九宫格转换，然后对每一九宫格进行唯一值检测
    temp_c = row_checkUnique(temp_c)
    temp_d = matrix_invert(temp_c)
    return temp_d

# 将获得的值域列表转化为一个新的数独题目
def generator_soduku(total_value_range):
    soduku = [[] for i in range(9)]
    for i in range(9):
        for j in range(9):
            if len(total_value_range[i][j]) == 1:
                soduku[i].append(total_value_range[i][j][0])
            else:
                soduku[i].append('')
    return soduku

# 值域列表缩减函数：将值域列表转化为数独题目，求新的数独题目的值域列表，如此反复
def reduce_totalValueRange(soduku):
    for n in range(100):
        total_value_range = totalValueRange(soduku)
        total_value_range = soduku_checkUnique(total_value_range)
        soduku = generator_soduku(total_value_range)
        if total_value_range == totalValueRange(generator_soduku(total_value_range)):
            break
    return total_value_range

# 检查行值域列表是否合法
def row_checkRepeat(s_value_range):
    for i in s_value_range:
        temp = []
        for j in i:
            if len(j) == 1:
                temp.append(j[0])
        len_temp = len(temp)
        if len_temp != len(list(set(temp))):
            return False
    return True

# 检查值域列表是否合法：行检测，列检测，九宫格检测
def soduku_checkRepeat(s_value_range):
    temp_col = list(zip(*s_value_range))
    temp_matrix = matrix_invert(s_value_range)
    return row_checkRepeat(s_value_range) and row_checkRepeat(temp_col) and row_checkRepeat(temp_matrix)

# 计算值域列表取值总的组合数（各单元格值域长度相乘）
def sodukuRate(s_row_vrange):
    rate = 1
    for i in s_row_vrange:
        for j in i:
            rate *= len(j)
    return rate

# 主函数，输入值域列表，如遇到多个取值的单元格，依次尝试值域里的每个值，通过递归的方法检测值是否正确
def trial(total_value_range):
    for i in range(9):
        for j in range(9):
            if len(total_value_range[i][j]) > 1:
                for k in total_value_range[i][j]:
                    test_value = copy.deepcopy(total_value_range)
                    test_value[i][j] = [k]
                    test_value = reduce_totalValueRange(generator_soduku(test_value))
                    if soduku_checkRepeat(test_value):
                        if sodukuRate(test_value) == 1:
                            return test_value
                        else:
                            if trial(test_value):
                                return trial(test_value)
                    else:
                        continue
                return False

if __name__ == '__main__':
    t1 = time.time()

    soduku = [[] for i in range(9)]

    # soduku[0] = ['',1,4,'',9,'','',2,'']
    # soduku[1] = ['','','','',3,'','','',5]
    # soduku[2] = [3,8,'','','',2,'',6,'']
    # soduku[3] = [8,4,'',6,'','','','',2]
    # soduku[4] = [1,'',5,2,'','',7,'','']
    # soduku[5] = ['','','','','',7,8,'','']
    # soduku[6] = [2,'','',4,'','','','',9]
    # soduku[7] = ['',6,'','','',9,'',5,'']
    # soduku[8] = ['','','','','','','','','']

    soduku[0] = ['','','',8,'','','','','']
    soduku[1] = ['',9,7,2,4,'','','','']
    soduku[2] = ['',4,6,'',3,'','',2,'']
    soduku[3] = [9,'','','','','',1,'','']
    soduku[4] = ['',3,5,1,2,8,9,7,'']
    soduku[5] = ['','',1,'','','','','',6]
    soduku[6] = ['',6,'','',9,'',3,8,'']
    soduku[7] = ['','','','',8,1,5,6,'']
    soduku[8] = ['','','','','','','','','']

    a = reduce_totalValueRange(soduku)
    for i in trial(a):
        print(i)

    print("代码执行完毕，用时{}秒".format(round(time.time() - t1,2)))
# import time
#
#
# def print_board(bo):
#     for i in range(len(bo)):
#         if i % 3 == 0 and i != 0:
#             print("- - - - - - - - - - - - - ")
#
#         for j in range(len(bo[0])):
#             if j % 3 == 0 and j != 0:
#                 print(" | ", end="")
#
#             if j == 8:
#                 print(bo[i][j])
#             else:
#                 print(str(bo[i][j]) + " ", end="")
#
#
# def find_possible_valid(bo, pos):
#     num_list = list(range(1, 10))
#     for i in range(9):
#         if bo[pos[0]][i] != 0 and bo[pos[0]][i] in num_list:
#             num_list.remove(bo[pos[0]][i])
#         if bo[i][pos[1]] != 0 and bo[i][pos[1]] in num_list:
#             num_list.remove(bo[i][pos[1]])
#     x, y = pos[0] // 3, pos[1] // 3
#     for i in range(3 * x, 3 * x + 3):
#         for j in range(3 * y, 3 * y + 3):
#             if bo[i][j] != 0 and bo[i][j] in num_list:
#                 num_list.remove(bo[i][j])
#
#     return num_list
#
#
# def find_empty(bo):
#     for i in range(len(bo)):
#         for j in range(len(bo[0])):
#             if bo[i][j] == 0:
#                 return (i, j)  # row, col
#
#     return None
#
#
# def solve_suduko(bo):
#     find = find_empty(bo)
#     if not find:
#         return True
#     else:
#         row, col = find
#
#     for i in find_possible_valid(bo, [row, col]):
#         if valid(bo, i, (row, col)):
#             bo[row][col] = i
#
#             if solve_suduko(bo):
#                 return True
#
#             bo[row][col] = 0
#
#     return False
#
#
# def valid(bo, num, pos):
#     # Check row
#     for i in range(len(bo[0])):
#         if bo[pos[0]][i] == num and pos[1] != i:
#             return False
#
#     # Check column
#     for i in range(len(bo)):
#         if bo[i][pos[1]] == num and pos[0] != i:
#             return False
#
#     # Check box
#     box_x = pos[1] // 3
#     box_y = pos[0] // 3
#
#     for i in range(box_y * 3, box_y * 3 + 3):
#         for j in range(box_x * 3, box_x * 3 + 3):
#             if bo[i][j] == num and (i, j) != pos:
#                 return False
#
#     return True
#
#
# if __name__ == "__main__":
#     board = [
#         [0, 0, 0, 8, 0, 0, 0, 0, 0],
#         [0, 9, 7, 2, 4, 0, 0, 0, 0],
#         [0, 4, 6, 0, 3, 0, 0, 2, 0],
#         [9, 0, 0, 0, 0, 0, 1, 0, 0],
#         [0, 3, 5, 1, 2, 8, 9, 7, 0],
#         [0, 0, 1, 0, 0, 0, 0, 0, 6],
#         [0, 6, 0, 0, 9, 0, 3, 8, 0],
#         [0, 0, 0, 0, 8, 0, 5, 6, 0],
#         [0, 0, 0, 0, 0, 0, 0, 0, 0]
#     ]
#
#     print_board(board)
#     start_time = time.time()
#     solve_suduko(board)
#     end_time = time.time()
#     print("_____________________________\n")
#     print_board(board)
#     print("time used:{}s".format(end_time - start_time))