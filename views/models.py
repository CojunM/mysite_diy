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
from datetime import datetime

from brick.core.db.databases import PostgresqlDatabase
from brick.core.db.felds import TextField, IntegerField, DateTimeField, BooleanField, DateField, PrimaryKeyField, \
    CharField, ForeignKeyField, ManyToManyField
from brick.core.db.models import Model

ps_db = PostgresqlDatabase('simple_db', host='localhost', port=5432, user='postgres', password='test')


class BaseModel(Model):
    """A base model that will use our Postgresql database."""

    class Meta:
        database = ps_db


class Manager(BaseModel):
    login_name = TextField(help_text='登陆账号')
    login_password = TextField(help_text='登陆密码')
    login_key = TextField(help_text='登录密钥')
    last_login_time = DateTimeField(help_text='最后登陆时间')
    last_login_ip = TextField(help_text='最后登陆IP')
    login_count = IntegerField(default=0, help_text='登陆次数')
    create_time = DateTimeField(help_text='注册时间')
    department_id = IntegerField(default=0, help_text='部门自编号Id，用户只能归属于一个部门')
    department_code = TextField(help_text='部门编号')
    department_name = TextField(help_text='部门名称')
    positions_id = IntegerField(default=0, help_text='用户职位Id')
    positions_name = TextField(help_text='职位名称')
    is_work = BooleanField(default=False, help_text='0=离职，1=就职')
    is_enabled = BooleanField(default=False, help_text='账号是否启用，true=启用，false=禁用')
    name = TextField(help_text='用户中文名称')
    sex = TextField(help_text='性别（未知，男，女）')
    birthday = DateField(help_text='出生日期')
    mobile = TextField(help_text='手机号码')
    email = TextField(help_text='个人--联系邮箱')
    remark = TextField(help_text='备注')
    manager_id = IntegerField(default=0, help_text='操作人员id')
    manager_name = TextField(help_text='操作人员姓名')


class Menu_info(BaseModel):
    id = PrimaryKeyField(help_text='主键Id')
    name = TextField(help_text='菜单名称或各个页面功能名称')
    icon = TextField(help_text='菜单小图标（一级菜单需要设置，二级菜单不用）')
    page_url = TextField(help_text='各页面URL（主菜单与分类菜单没有URL）')
    interface_url = TextField(help_text='各接口url')
    parent_id = IntegerField(default=0, help_text='父ID')
    sort = IntegerField(default=0, help_text='排序')
    level = IntegerField(default=0, help_text='树列表深度级别，即当前数据在哪一级')
    is_leaf = BooleanField(default=False, help_text='是否最终节点')
    expanded = BooleanField(default=False, help_text='此节点是否展开，后台菜单列表js要用到，不用进行编辑')
    is_show = BooleanField(default=False, help_text='该菜单是否在菜单栏显示，false=不显示，true=显示')
    is_enabled = BooleanField(default=False, help_text='是否启用，true=启用，false=禁用')


# class positions(BaseModel):
#     name= TextField(help_text=' 职位名称')
#     department_id=IntegerField(default=0,help_text='部门自编号ID')
#     department_code=TextField(help_text=' 部门编号')
#     department_name= TextField(help_text=' 部门名称')
#     page_power= TextField(help_text=' 菜单操作权限，有操作权限的菜单ID列表：,1,2,3,4,5')
class Positions(BaseModel):
    id = IntegerField(null=False, default=0, help_text='主键Id')
    name = TextField(help_text=' 职位名称')
    department_id = IntegerField(null=False, default=0, help_text='部门自编号ID')
    department_code = TextField(null=False, default='::', help_text=' 部门编号')
    department_name = TextField(default='::', help_text=' 部门名称')
    page_power = TextField(default='::', help_text='菜单操作权限，有操作权限的菜单ID列表：,1,2,3,4,5,')


class Menu(BaseModel):
    """
    菜单
    """
    # code = CharField(max_length=50, unique=True, null=True, verbose_name="编码")
    name = CharField(max_length=30, verbose_name="菜单名",
                     help_text='菜单名称或各个页面功能名称')  # unique=True, 这个字段在表中必须有唯一值.
    icon = CharField(max_length=50, null=True, verbose_name="图标", help_text='菜单小图标（一级菜单需要设置，二级菜单不用）')
    page_url = TextField(null=True, help_text='各页面URL（主菜单与分类菜单没有URL）',
                         verbose_name="页面URL")
    interface_url = TextField(null=True, help_text='各接口url', verbose_name="页面接口URL")
    # parent_id = ForeignKeyField('self', null=True, on_delete="SET NULL", verbose_name="父菜ID")  # to_field='parent_id',
    parent_id = IntegerField(default=0, help_text='父ID')
    sort = IntegerField(default=0, help_text='排序')
    level = IntegerField(default=0, help_text='树列表深度级别，即当前数据在哪一级')
    is_leaf = BooleanField(default=False, help_text='是否最终节点')
    expanded = BooleanField(default=False, help_text='此节点是否展开，后台菜单列表js要用到，不用进行编辑')
    is_show = BooleanField(default=False, help_text='该菜单是否在菜单栏显示，false=不显示，true=显示')
    is_enabled = BooleanField(default=False, help_text='是否启用，true=启用，false=禁用')

    # priority = IntegerField(verbose_name=u'显示优先级', null=True, help_text=u'菜单的显示顺序，优先级越小显示越靠前')


def __str__(self):
    return self.name


class Meta:
    verbose_name = '菜单'
    # verbose_name_plural = verbose_name

    ordering = ["sort", "id"]  # 根据优先级和id来排序


@classmethod
def get_menu_by_request_url(cls, url):
    return dict(menu=Menu.get(url=url))


class Power(BaseModel):
    name = CharField(max_length=32)
    url = TextField(null=True, help_text='各页面URL（主菜单与分类菜单没有URL）',
                    verbose_name="页面URL")
    menus = ForeignKeyField(Menu, on_delete='CASCADE', verbose_name=u'对应菜单')

    # 指定属于哪个父级权限
    parent = ForeignKeyField('self', verbose_name=u'父级权限', null=True, on_delete='SET NULL',
                             help_text='如果添加的是子权限，请选择父权限'
                             )

    # 指定属于哪个menu
    # menu = ForeignKeyField(Menu, verbose_name=u'对应菜单', null=True)

    class Meta:
        verbose_name_plural = '权限表'
        poeers = (
            ('edit', u'编辑权限'),
            ('add', u'添加权限'),
            ('DEL', u'删除权限'),
            ('list', u'查看权限'),
        )

    def __str__(self):
        # return '%s-%s' % (self.caption, self.url)
        return "{parent}{name}".format(name=self.name, parent="%s-->" % self.parent.name if self.parent else '')


# 身份分类
role_choices = (
    ("1", "董事"),
    ("2", "超管"),
    ("3", "总监"),
    ("4", "科长"),
    ("5", "部长"),
    ("6", "职员"),
)


class Role(BaseModel):
    """
    角色：用于权限绑定
    """

    name = CharField(max_length=32, unique=True, choices=role_choices, verbose_name="角色")
    menus = ManyToManyField(Menu)
    powers = ManyToManyField(Power, verbose_name="权限")
    desc = CharField(max_length=50, null=True, verbose_name="描述")
    flag = CharField(max_length=64, null=True, verbose_name="角色标识")
    parent = ForeignKeyField('self', null=True, on_delete='SET NULL', verbose_name="父角色")

    class Meta:
        verbose_name_plural = '角色表'

    def __str__(self):
        return self.name


class Group(BaseModel):
    """
    组织架构
    """
    type_choices = (("unit", "单位"), ("department", "部门"))
    name = CharField(max_length=60, verbose_name="组织名称")
    type = CharField(max_length=20, choices=type_choices, default="department", verbose_name="组织类型")
    code = CharField(max_length=50, unique=True, verbose_name="编码")

    parent = ForeignKeyField('self', null=True, on_delete='SET NULL', verbose_name="父组织")
    # menus = ManyToManyField(Menu)
    roles = ManyToManyField(Role, on_delete='CASCADE', verbose_name="角色")

    # permissions = ManyToManyField(Permission)

    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(BaseModel):
    # userid= CharField(max_length=64, help_text='用户ID')
    login_name = CharField(max_length=64, unique=True, help_text='登陆账号')
    login_password = CharField(max_length=64, help_text='登陆密码')
    mobile = CharField(max_length=11, default="", verbose_name="手机号码")
    login_key = TextField(help_text='登录密钥', null=True)
    last_login_time = DateTimeField(help_text='最后登陆时间')
    last_login_ip = TextField(help_text='最后登陆IP')
    login_count = IntegerField(default=0, help_text='登陆次数')

    is_work = BooleanField(default=False, help_text='0=离职，1=就职')
    is_enabled = BooleanField(default=False, help_text='账号是否启用，true=启用，false=禁用')
    lock_release_time = DateTimeField(null=True, verbose_name="用户账户锁定到期时间")
    create_time = DateTimeField(help_text='注册时间')
    roles = ManyToManyField(Role, verbose_name="角色")
    # permissions = ManyToManyField(Permission, verbose_name="权限")
    groups = ManyToManyField(Group, verbose_name="组")

    # USERNAME_FIELD='login_name'
    class Meta:
        verbose_name_plural = '用户表'

    def __str__(self):
        return self.login_name


class NotifyAnnounce(BaseModel):
    id = IntegerField(primary_key=True, help_text='公告编号')
    sender_id = IntegerField(help_text='发送者编号')
    title = CharField(max_length=164, unique=True, help_text='公告标题')
    content = TextField(help_text='公告内容')
    created_time = DateTimeField(help_text='发送时间')


class NotifyAnnounceUser(BaseModel):
    # id = IntegerField(primary_key=True, help_text='公告编号')
    announce_id = IntegerField(help_text='公告编号')
    recipient_id = IntegerField(help_text='接收用户编号,0是给全体人的消息')
    created_time = DateTimeField(help_text='拉取公告时间')
    read_time = DateTimeField(help_text='阅读时间')
    state = IntegerField(help_text='状态，1已读|0未读')


class UserProfile(BaseModel):
    user_id = ForeignKeyField(User, on_delete='CASCADE')
    name = CharField(max_length=20, default="", verbose_name="姓名")
    birthday = DateField(null=True, verbose_name="出生日期")
    gender = CharField(max_length=10, choices=(("male", "男"), ("female", "女")),
                       default="male", verbose_name="性别")
    email = CharField(max_length=50, verbose_name="邮箱")
    image = CharField(max_length=100, null=True, verbose_name="邮箱")
    department = ForeignKeyField(Group, null=True, on_delete='SET NULL', verbose_name="部门")
    post = CharField(max_length=50, null=True, verbose_name="职位")
    superior = ForeignKeyField("self", null=True, on_delete='SET NULL', verbose_name="上级主管")

    # roles = ManyToManyField(Role, verbose_name="角色")

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class BaseNotify(BaseModel):
    action = CharField(help_text=' 提醒信息的动作类型')
    target_type = CharField(help_text='目标的类型')
    target_id = IntegerField(help_text='目标的ID')
    created_at = DateTimeField(help_text='发送时间')


class Notify(BaseNotify):
    # id = IntegerField(primary_key=True, help_text='公告编号')
    content = TextField(help_text='消息内容')
    type = IntegerField(choices=[1, 2, 3], help_text='消息的类型，1: 公告 Announce，2: 提醒 Remind，3：信息 Message')
    # targetType = CharField(help_text='目标的类型')
    # targetId = IntegerField(help_text='目标的ID')
    sender_id = IntegerField(help_text='发送者编号')
    # action= CharField( help_text=' 提醒信息的动作类型')
    # createdAt = DateTimeField(help_text='发送时间')


class UserNotify(BaseNotify):
    # id = IntegerField(primary_key=True, help_text='公告编号')
    is_read = BooleanField()
    # userId  = IntegerField(help_text='用户消息所属者')
    notify = ForeignKeyField(Notify, null=True, on_delete='SET NULL', verbose_name="关联的Notify")

    # targetId = IntegerField(help_text='目标的ID')
    # targetType = CharField( help_text='目标的类型')
    # action = CharField(help_text=' 订阅动作,如: comment/like/post/update etc.')

    # createdAt = DateTimeField(help_text='发送时间')


class SubscriptionConfig(BaseModel):
    user_id = IntegerField(help_text='用户消息所属者')
    action = IntegerField(choices=[1, 2, 3, 4], help_text=' 订阅动作,如: comment/like/post/update etc.')


def drop_tables():
    ps_db.drop_tables([User, Power, Menu, Group, Role,
                       User.roles.get_through_model(), Group.roles.get_through_model(),

                       User.groups.get_through_model(),
                       Role.powers.get_through_model(), Role.menus.get_through_model(), ], safe=True)


def creare_tables():
    ps_db.create_tables([User, Power, Menu, Group, Role,
                         User.roles.get_through_model(), Group.roles.get_through_model(),

                         User.groups.get_through_model(),
                         Role.powers.get_through_model(), Role.menus.get_through_model(),
                         ])


def insert_datas():
    # user
    for k in range(6):
        usr = User()
        usr.login_name = f'Alex_{k}'
        usr.login_password = 'e10adc3949ba59abbe56e057f20f883e'
        usr.create_time = datetime.now()
        usr.last_login_ip = '1,2,2122'
        usr.last_login_time = datetime.now()
        usr.is_enabled = True
        # noinspection PyBroadException

        try:
            usr.save()
        except:
            pass

    # role
    for k in range(6):
        r = Role()
        r.name = role_choices[k][1]
        try:
            r.save()
        except:
            pass

    group_data = (("1", "董事会"),
                  ("2", "销售一部"),
                  ("3", "销售"),
                  ("4", "销售二部"),
                  ("5", "后勤"),
                  ("6", "网管"),)
    # group
    for k in range(6):
        g = Group()
        g.code = group_data[k][0]
        g.name = group_data[k][1]
        if g.name == "销售":
            g.parent = 2
        try:
            g.save()
            # if g.name == "销售":
            #     g.code = group_data[5][0]
            #     g.save()
        except:
            pass

    # menu
    data_source = [
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (12, '销售部', 'bi-journal-text', '', '', 0, 2, 0, False, False, True, True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (
        #              9, '添加', '', 'department_edit', 'get(/api/system/department/tree/),post(/api/system/department/)',
        #              7, 2, 2, True, False, False, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (1, '系统管理', '', '', '', 0, 1, 0, False, False, True, True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (10, '编辑', '', 'department_edit',
        #                           'get(/api/system/department/tree/),get(/api/system/department/<id:int>/),put(/api/system/department/<id:int>/)',
        #                           7, 3, 2, True, False, False, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (39, '管理员操作日志', '', 'manager_operation_log', '', 1, 5, 1, False, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (38, '主界面', '', 'main', 'get(/api/main/menu_info/)', 0, 1, 0, True, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     15, '添加', '', 'product_class_edit', 'post(/api/product_class/)', 13, 2, 2, True, False, True,
                     True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     35, '删除', '', 'manager', 'delete(/api/system/manager/<id:int>/)', 31, 4, 2, True, False, True,
                     True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (16, '编辑', '', 'product_class_edit',
                                  'get(/api/product_class/<id:int>/),put(/api/product_class/<id:int>/)',
                                  13, 3, 2, True, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (3, '列表', '', 'menu_info', 'get(/api/system/menu_info/)', 2, 1, 2, True, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (2, '菜单管理', '', 'menu_info', '', 1, 1, 1, True, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (5, '编辑', '', 'menu_info_edit',
                                  'get(/api/system/menu_info/tree/),get(/api/system/menu_info/<id:int>/),put(/api/system/menu_info/<id:int>/)',
                                  2, 3, 2, True, False, True, True))),

        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     6, '删除', '', 'menu_info', 'delete(/api/system/menu_info/<id:int>/)', 2, 4, 2, True, False, True,
                     True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (25, '联系我们', '', 'contact_us_edit', '', 23, 2, 1, False, False, True, True))),

        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (13, '销售一部', '', 'products_class', '', 12, 5, 1, False, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     22, '删除', '', 'products_list', 'delete(/api/product/<id:int>/)', 18, 4, 2, True, False, True,
                     True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     37, '复职', '', 'manager', 'put(/api/system/manager/<id:int>/reinstated/)', 31, 6, 2, True, False,
                     True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (28, '销售二部', '', 'products_list', '', 12, 6, 1, False, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (18, '产品列表', '', 'products_list', '', 12, 2, 1, False, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     20, '添加', '', 'products_edit', 'get(/api/product_class/),post(/api/product/)', 18, 2, 2, True,
                     False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (31, '管理员管理', '', 'manager', '', 1, 4, 1, False, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (33, '添加', '', 'manager_edit',
                                  'post(/api/system/manager/),get(/api/system/department/tree/),get(/api/system/positions/)',
                                  31, 2, 2, True, False, True, True))),
        dict(zip(('id', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (34, '编辑', '', 'manager_edit',
                                  'get(/api/system/manager/<id:int>/),put(/api/system/manager/<id:int>/),get(/api/system/department/tree/),get(/api/system/positions/)',
                                  31, 3, 2, True, False, True, True))), ]
    try:
        with ps_db.atomic():
            Menu.insert_many(data_source).execute()
    except Exception as e:
        pass
    # print(e)

    for k in range(6):
        u = User.get(login_name=f'Alex_{k}')
        #  ps.add(Group.get(name=group_data[k][1]))
        # u.permissions.add(Permission.get())
        if u.login_name == 'Alex_2':
            u.roles.add(Role.get(name=role_choices[1][1]))
            u.groups.add(Group.get(name=group_data[5][1]))
        else:
            u.roles.add(Role.get(name=role_choices[k][1]))
            u.groups.add(Group.get(name=group_data[k][1]))
    for g in Group.select().where(Group.name.startswith('网管')):
        g.roles.add(Role.get(name='超管'))
    # Role.get(name="总监").menus.add(Menu.select())
    Role.get(Role.name == '超管').menus.add(Menu.select())


if __name__ == "__main__":
    # r = Manager.select().where(Manager.login_name == 'admin')
    #     # for row in r:
    #     #     print('row', row.name, row.login_password)
    #     r = Manager.get(Manager.login_name == 'admin1')
    #     print(r.login_name, r.login_password)
    #     fields = {
    #        'last_login_time':'now()',
    #         'login_count': Manager.login_count + 1
    #             }
    #     w=Manager.login_name == 'admin' and Manager.login_password =='e10adc3949ba59abbe56e057f20f883e'
    #     # result =Manager.update(**fields).where(Manager.login_name == 'admin').execute()
    #     result = Manager.update(**fields).where(w).execute()
    #     print(result)
    #    Menu.create_table()
    #     Role.create_table()
    #     Structure.create_table()
    #     Role.create_table()
    #     Menu.create_table()
    # #     Role.permissions.get_through_model().create_table()
    #         permissions = (Role
    #                    .select()
    #                    .join(Role.permissions.get_through_model())
    #                    .join(Menu)
    #                    .where(Menu.name == 'menu2'))
    #         print(permissions)
    #         for course in  permissions:
    #             print(course.name)
    # m = Menu.get(name="menu1")
    #
    # r = Role.get(Role.name == "role3")
    # print(m.id, r.id)
    # print( r.id)
    #     r.permissions.add(m.id)

    drop_tables()
    creare_tables()

    insert_datas()
