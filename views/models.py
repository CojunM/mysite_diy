#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/3/8 11:23
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : models.py
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
from brick.orm.models import Model
from brick.orm.databases import PostgresqlDatabase
from brick.orm.felds import TextField, IntegerField, DateTimeField, BooleanField, DateField, PrimaryKeyField


ps_db = PostgresqlDatabase('simple_db', host='localhost', port=5432, user='postgres', password='test')


class BaseModel(Model):
    """A base model that will use our Postgresql database."""

    class Meta:
        database = ps_db


class Manager(BaseModel):
    login_name = TextField( help_text='登陆账号')
    login_password = TextField(help_text= '登陆密码')
    login_key = TextField(help_text= '登录密钥')
    last_login_time = DateTimeField(help_text='最后登陆时间')
    last_login_ip = TextField(help_text='最后登陆IP')
    login_count = IntegerField(default=0,help_text= '登陆次数')
    create_time = DateTimeField(help_text='注册时间')
    department_id = IntegerField(default=0,help_text= '部门自编号Id，用户只能归属于一个部门')
    department_code = TextField(help_text= '部门编号')
    department_name = TextField(help_text='部门名称')
    positions_id = IntegerField(default=0,help_text= '用户职位Id')
    positions_name = TextField(help_text= '职位名称')
    is_work = BooleanField(default=False,help_text= '0=离职，1=就职')
    is_enabled = BooleanField(default=False,help_text= '账号是否启用，true=启用，false=禁用')
    name = TextField(help_text= '用户中文名称')
    sex = TextField(help_text='性别（未知，男，女）')
    birthday = DateField(help_text= '出生日期')
    mobile = TextField(help_text='手机号码')
    email = TextField(help_text= '个人--联系邮箱')
    remark = TextField(help_text= '备注')
    manager_id = IntegerField(default=0,help_text='操作人员id')
    manager_name = TextField(help_text='操作人员姓名')



class Menu_info(BaseModel):
    id = PrimaryKeyField(help_text='主键Id')
    name = TextField(help_text='菜单名称或各个页面功能名称')
    icon = TextField(help_text= '菜单小图标（一级菜单需要设置，二级菜单不用）')
    page_url = TextField(help_text='各页面URL（主菜单与分类菜单没有URL）')
    interface_url = TextField(help_text= '各接口url')
    parent_id = IntegerField(default=0,help_text='父ID')
    sort = IntegerField(default=0,help_text= '排序')
    level = IntegerField(default=0,help_text='树列表深度级别，即当前数据在哪一级')
    is_leaf = BooleanField(default=False,help_text='是否最终节点')
    expanded = BooleanField(default=False,help_text= '此节点是否展开，后台菜单列表js要用到，不用进行编辑')
    is_show = BooleanField(default=False,help_text= '该菜单是否在菜单栏显示，false=不显示，true=显示')
    is_enabled = BooleanField(default=False,help_text= '是否启用，true=启用，false=禁用')
# class positions(BaseModel):
#     name= TextField(help_text=' 职位名称')
#     department_id=IntegerField(default=0,help_text='部门自编号ID')
#     department_code=TextField(help_text=' 部门编号')
#     department_name= TextField(help_text=' 部门名称')
#     page_power= TextField(help_text=' 菜单操作权限，有操作权限的菜单ID列表：,1,2,3,4,5')
class Positions(BaseModel):
    id=IntegerField(null=False, default=0,help_text='主键Id')
    name= TextField(help_text=' 职位名称')
    department_id=IntegerField(null=False, default=0,help_text='部门自编号ID')
    department_code= TextField(null=False, default='::',help_text=' 部门编号')
    department_name= TextField(default='::',help_text=' 部门名称')
    page_power= TextField(default='::',help_text='菜单操作权限，有操作权限的菜单ID列表：,1,2,3,4,5,')
if __name__ == "__main__":

    # r = Manager.select().where(Manager.login_name == 'admin')
#     # for row in r:
#     #     print('row', row.name, row.login_password)
#     r = Manager.get(Manager.login_name == 'admin1')
#     print(r.login_name, r.login_password)
    fields = {
       'last_login_time':'now()',
        'login_count': Manager.login_count + 1
            }
    w=Manager.login_name == 'admin' and Manager.login_password =='e10adc3949ba59abbe56e057f20f883e'
    # result =Manager.update(**fields).where(Manager.login_name == 'admin').execute()
    result = Manager.update(**fields).where(w).execute()
    print(result)