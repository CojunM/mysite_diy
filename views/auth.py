#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2023/4/4 14:05
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : auth.py
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
from brick.contrib import web_helper
from brick.core.wsgiapp import get
from views.db_logic import db_logic
from views.models import Group, Menu, Role


def get_all_roles(session):
    """user_id
    获取当前用户的角色的子类角色id
    :param
    :return:
    """
    # print('ls')
    roles_list = []
    # 初始化管理员逻辑类
    _Group_logic = db_logic(Group)

    # print("roles:", userroles)

    # 对用户当前的角色遍历
    for group in session.get('groups'):
        # print("role1:", userrole)
        # 获取当前用户组的角色集合
        gp = _Group_logic.get_model_for_cache_of_where(Group.id == group.id)
        # 将当前角色id添加到列表
        if gp:
            roles_list.extend([role.id for role in gp.roles])
            if group.parent_id:
                gp_parent = _Group_logic.get_model_for_cache_of_where(Group.id == group.parent_id)
                if gp_parent:
                    roles_list.extend([role.id for role in gp_parent.roles])

        # # 获取当前角色的第一层子角色id
        # roles_id = Role.query.filter_by(prole_id=userrole.role_id).all()
        # for role_id in roles_id:
        #     get_son_roles(role_id, roles_list)
    roles_list.extend(session.get('roles'))

    return set(roles_list)


def get_roles_menus(roles):
    menus_list = []
    _role_logic = db_logic(Role)
    for id in roles:
        result = _role_logic.get_model_for_cache_of_where(Role.id == id)
        if result:
            # print('result', result)
            menus_list.extend([m.id for m in result.menus])
            # print(menus_list)
    return set(menus_list)


@get('/api/login2/menu/')
def get_menus():
    """
    主页面获取菜单列表数据
    """
    _menu_logic = db_logic(Menu)
    # mu = Menu.alias()
    # 读取记录
    # result = _menu_logic.get_list(wheres=(mu.is_show == True, mu.is_enabled == True), join=mu,
    #                               orderby=mu.sort)
    result = _menu_logic.get_list(wheres=(Menu.is_show == True, Menu.is_enabled == True),
                                  orderby=Menu.sort)
    # result = _menu_logic.get_list(wheres=(Menu.is_show == True, Menu.is_enabled == True), join=mu,
    #                               orderby=Menu.sort)
    if result:
        # 获取当前用户角色
        session = web_helper.get_session()
        if session:
            roles = get_all_roles(session)
        else:
            return web_helper.return_msg(-404, '您的登录已超时，请重新登录')
        page_power = get_roles_menus(roles)
        print('page_power', page_power)
        # 定义最终输出的html存储变量
        html = ''
        lst = [m for m in result.get('rows')]
        print('提取出result', [m.id for m in result.get('rows')])
        for model in lst:
            # print('提取出model', model.name)
            # 检查是否有权限
            # 检查是否有权限
            if model.id in page_power:
                print('提取出modelname', getattr(model, 'name'))
                if model.parent_id == 0:  # getattr(model, 'parent_id')
                    # print('提取出第一级菜单model', getattr(model, 'name'))
                    temp = """ 
                          <li class="nav-item">
                             <a class="nav-link collapsed" data-href="%(page_url)s" data-title="%(name)s" 
                             data-bs-target="#components-nav-%(id)s"  data-bs-toggle="collapse" href="#">
                          %(icon)s  <span class="menu-title">%(name)s</span> %(chevron)s
                                </a>    
                                 <ul id="components-nav-%(id)s"  class="nav-content collapse "  data-bs-parent="#sidebar-nav"> """ \
                           % {
                               'id': model.id,
                               'icon': "<i class=\"bi " + model.icon + "\"></i>" if model.icon else "",
                               # "<i class=\"bi " + model.icon + "\"></i>" if model.icon else "",
                               'page_url': model.page_url,
                               'name': model.name,
                               'chevron': '%(chevron)s'}
                    html = html + temp  # id': getattr(model, 'id'),
                    flg = False
                    # lst.remove(model)
                    for sub_model in lst:

                        # 检查是否有权限
                        # 如果父id等于当前一级菜单id，则为当前菜单的子菜单
                        if sub_model.parent_id == model.id:
                            # print('提取出 sub_model', getattr(sub_model, 'name'))
                            # lst.remove(sub_model)
                            flg = True
                            temp = """
                                <li>
                                 <a data-href="%(page_url)s" data-title="%(name)s" href="javascript:void(0)" >
                                    <i class="bi bi-circle"></i><span  >%(name)s</span>
                                </a>
                                </li>
                          
                              """ % {'page_url': sub_model.page_url,
                                     'name': sub_model.name}
                            html = html + temp
                    if flg:
                        html = html % {'chevron': '<i  class="bi bi-chevron-down ms-auto"></i>'}
                        # print('html33')
                    else:
                        html = html % {'chevron': ''}
                        # print('html12')
                    # 闭合菜单html
                    temp = """ </ul>   </li> """
                    html = html + temp
                    print('html', html)
        return web_helper.return_msg(0, '成功', {'menu_html': html})
    else:
        return web_helper.return_msg(-1, "查询失败")
