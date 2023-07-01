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
from brick.core.db.felds import TextField, IntegerField, DateTimeField, BooleanField, DateField, CharField, \
    ForeignKeyField, ManyToManyField
from brick.core.db.models import Model

ps_db = PostgresqlDatabase('simple_db', host='localhost', port=5432, user='postgres', password='test')


class BaseModel(Model):
    """A base model that will use our Postgresql database."""

    class Meta:
        database = ps_db


class Menu(BaseModel):
    """
    菜单
    """
    code = CharField(max_length=50, primary_key=True, unique=True, null=True, verbose_name="编码")
    name = CharField(max_length=30, verbose_name="菜单名",
                     help_text='菜单名称或各个页面功能名称')  # unique=True, 这个字段在表中必须有唯一值.
    icon = CharField(max_length=50, null=True, verbose_name="图标", help_text='菜单小图标（一级菜单需要设置，二级菜单不用）')
    page_url = TextField(null=True, help_text='各页面URL（主菜单与分类菜单没有URL）',
                         verbose_name="页面URL")
    interface_url = TextField(null=True, help_text='各接口url', verbose_name="页面接口URL")
    parent_id = ForeignKeyField('self', to_field=code, null=True, on_delete="SET NULL", verbose_name="父菜ID")
    sort = IntegerField(default=0, help_text='排序')
    level = IntegerField(default=0, help_text='树列表深度级别，即当前数据在哪一级')
    is_leaf = BooleanField(default=False, help_text='是否最终节点')
    expanded = BooleanField(default=False, help_text='此节点是否展开，后台菜单列表js要用到，不用进行编辑')
    is_show = BooleanField(default=False, help_text='该菜单是否在菜单栏显示，false=不显示，true=显示')
    is_enabled = BooleanField(default=False, help_text='是否启用，true=启用，false=禁用')

    # priority = IntegerField(verbose_name=u'显示优先级', null=True, help_text=u'菜单的显示顺序，优先级越小显示越靠前'                            )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '菜单'
        # verbose_name_plural = verbose_name

        ordering = ["sort", "id"]  # 根据优先级和id来排序

    @classmethod
    def get_menu_by_request_url(cls, url):
        return dict(menu=Menu.get(url=url))


# 身份分类
role_choices = (
    ("1", "董事"),
    ("2", "超管"),
    ("3", "总监"),
    ("4", "科长"),
    ("5", "部长"),
    ("6", "职员"),
)


class Permission(BaseModel):
    name = CharField(max_length=32)
    url = CharField(max_length=32)
    menus = ManyToManyField(Menu, verbose_name=u'对应菜单')

    # 指定属于哪个父级权限
    parent = ForeignKeyField('self', verbose_name=u'父级权限', null=True, on_delete='SET NULL',
                             help_text='如果添加的是子权限，请选择父权限'
                             )

    # 指定属于哪个menu
    # menu = ForeignKeyField(Menu, verbose_name=u'对应菜单', null=True)

    class Meta:
        verbose_name_plural = '权限表'
        permissions = (
            ('edit', u'编辑权限'),
            ('add', u'添加权限'),
            ('DEL', u'删除权限'),
            ('list', u'查看权限'),
        )

    def __str__(self):
        # return '%s-%s' % (self.caption, self.url)
        return "{parent}{name}".format(name=self.name, parent="%s-->" % self.parent.name if self.parent else '')


class Role(BaseModel):
    """
    角色：用于权限绑定
    """
    name = CharField(max_length=32, unique=True, choices=role_choices, verbose_name="角色")
    menus = ManyToManyField(Menu)
    permissions = ManyToManyField(Permission)
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
    parent = ForeignKeyField('self', null=True, on_delete='SET NULL', verbose_name="父组织")
    menus = ManyToManyField(Menu)
    roles = ManyToManyField(Role, verbose_name="角色")
    permissions = ManyToManyField(Permission)

    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(BaseModel):
    login_name = CharField(max_length=64, unique=True, help_text='登陆账号')
    login_password = CharField(max_length=64, help_text='登陆密码')
    mobile = CharField(max_length=11, default="", verbose_name="手机号码")
    login_key = TextField(help_text='登录密钥', null=True)
    last_login_time = DateTimeField(help_text='最后登陆时间')
    last_login_ip = TextField(help_text='最后登陆IP')
    login_count = IntegerField(default=0, help_text='登陆次数')
    is_work = BooleanField(default=False, help_text='0=离职，1=就职')
    is_enabled = BooleanField(default=False, help_text='账号是否启用，true=启用，false=禁用')
    lockrelease_time = DateTimeField(null=True, verbose_name="用户账户锁定到期时间")
    create_time = DateTimeField(help_text='注册时间')
    roles = ManyToManyField(Role, verbose_name="角色")
    permissions = ManyToManyField(Permission, verbose_name="权限")
    groups = ManyToManyField(Group, verbose_name="组")

    # USERNAME_FIELD='login_name'
    class Meta:
        verbose_name_plural = '用户表'

    def __str__(self):
        return self.username


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


def insert_datas():
    ps_db.drop_tables([User, Permission, Menu, Group, Role, User.permissions.get_through_model(),
                       User.roles.get_through_model(), Group.roles.get_through_model(),
                       Group.menus.get_through_model(),
                       User.groups.get_through_model(),
                       Role.permissions.get_through_model(), Role.menus.get_through_model(),
                       Group.permissions.get_through_model(), ],safe=True)

    ps_db.create_tables([User, Permission, Menu, Group, Role, User.permissions.get_through_model(),
                         User.roles.get_through_model(), Group.roles.get_through_model(),
                         Group.menus.get_through_model(),
                         User.groups.get_through_model(),
                         Role.permissions.get_through_model(), Role.menus.get_through_model(),
                         Group.permissions.get_through_model()])

    # user
    for k in range(6):
        usr = User()
        usr.login_name = f'Alex_{k}'
        usr.login_password = 'e10adc3949ba59abbe56e057f20f883e'
        usr.create_time = datetime.now()
        usr.last_login_ip = '1,2,2122'
        usr.last_login_time = datetime.now()
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

    groupData = {("1", "董事会"),
                 ("2", "销售一部"),
                 ("3", "销售"),
                 ("4", "销售二部"),
                 ("5", "后勤"),
                 ("6", "网管"), }
    # group
    for k in range(6):
        g = Group()
        g.name = groupData[k][1]
        # if g.name == "销售":
        #     g.parent = 2

        try:
            g.save()
        except:
            pass

    # menu
    data_source = [
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (12, '销售部', '&#xe6b5;', '', '', None, 10, 0, False, False, True, True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (
        #              9, '添加', '', 'department_edit', 'get(/api/system/department/tree/),post(/api/system/department/)',
        #              7, 2, 2, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (1, '系统管理', '&#xe62e;', '', '', None, 2, 0, False, False, True, True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (10, '编辑', '', 'department_edit',
        #                           'get(/api/system/department/tree/),get(/api/system/department/<id:int>/),put(/api/system/department/<id:int>/)',
        #                           7, 3, 2, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (39, '管理员操作日志', '', 'manager_operation_log', '', 1, 5, 1, False, False, True, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (38, '主界面', '', 'main', 'get(/api/main/menu_info/)', None, 1, 0, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     15, '添加', '', 'product_class_edit', 'post(/api/product_class/)', 13, 2, 2, True, False, False,
                     True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     35, '删除', '', 'manager', 'delete(/api/system/manager/<id:int>/)', 31, 4, 2, True, False, False,
                     True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (16, '编辑', '', 'product_class_edit',
                                  'get(/api/product_class/<id:int>/),put(/api/product_class/<id:int>/)',
                                  13, 3, 2, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'),
                 (3, '列表', '', 'menu_info', 'get(/api/system/menu_info/)', 2, 1, 2, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (2, '菜单管理', '', 'menu_info', '', 1, 1, 1, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (5, '编辑', '', 'menu_info_edit',
                                  'get(/api/system/menu_info/tree/),get(/api/system/menu_info/<id:int>/),put(/api/system/menu_info/<id:int>/)',
                                  2, 3, 2, True, False, False, True))),

        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     6, '删除', '', 'menu_info', 'delete(/api/system/menu_info/<id:int>/)', 2, 4, 2, True, False, False,
                     True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (25, '联系我们', '', 'contact_us_edit', '', 23, 2, 1, False, False, True, True))),

        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (13, '销售一部', '', 'products_class', '', 12, 1, 1, False, False, True, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     22, '删除', '', 'products_list', 'delete(/api/product/<id:int>/)', 18, 4, 2, True, False, False,
                     True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     37, '复职', '', 'manager', 'put(/api/system/manager/<id:int>/reinstated/)', 31, 6, 2, True, False,
                     False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (18, '销售二部', '', 'products_list', '', 12, 2, 1, False, False, True, True))),
        # dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
        #           'expanded', 'is_show',
        #           'is_enabled'), (18, '产品列表', '', 'products_list', '', 12, 2, 1, False, False, True, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (
                     20, '添加', '', 'products_edit', 'get(/api/product_class/),post(/api/product/)', 18, 2, 2, True,
                     False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (31, '管理员管理', '', 'manager', '', 1, 4, 1, False, False, True, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (33, '添加', '', 'manager_edit',
                                  'post(/api/system/manager/),get(/api/system/department/tree/),get(/api/system/positions/)',
                                  31, 2, 2, True, False, False, True))),
        dict(zip(('code', 'name', 'icon', 'page_url', 'interface_url', 'parent_id', 'sort', 'level', 'is_leaf',
                  'expanded', 'is_show',
                  'is_enabled'), (34, '编辑', '', 'manager_edit',
                                  'get(/api/system/manager/<id:int>/),put(/api/system/manager/<id:int>/),get(/api/system/department/tree/),get(/api/system/positions/)',
                                  31, 3, 2, True, False, False, True))), ]
    with ps_db.atomic():
        Menu.insert_many(data_source).execute()
    for k in range(6):
        u = User.get(login_name=f'Alex_{k}')
        u.roles.add(Role.get(name=role_choices[k][1]))
        u.groups.add(Group.get(name=groupData[k][1]))
        # u.permissions.add(Permission.get())
    Role.get(name="部长").menus.add(Menu.select())
    Role.get(name="总监").menus.add(Menu.select())
    Group.get(name='group_0').menus.add(Menu.select())


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
    insert_datas()
