#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/4/24 23:14
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : db_logic.py
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
import operator
from functools import reduce

from bottle import request

from brick.contrib import cache_helper, encrypt_helper
# from brick.httphandles import request
from brick.orm.felds import fn


class db_logic:
    """数据库类"""

    def __init__(self, model, is_output_sql=False, pk_name='id'):
        # def __init__(self, model, is_output_sql, column_name_list='*', pk_name='id'):
        """类初始化"""
        # 数据库参数
        self.__model = model
        # 是否输出执行的Sql语句到日志中
        self.__is_output_sql = is_output_sql
        # 表名称
        self.__table_name = str(model._meta.db_table).lower()
        # 查询的列字段名称，*表示查询全部字段，多于1个字段时用逗号进行分隔，除了字段名外，也可以是表达式
        # self.__column_name_list = str(column_name_list).lower()
        # 主健名称
        self.__pk_name = str(pk_name).lower()
        # 缓存列表
        self.__cache_list = self.__table_name + '_cache_list'

        print('self.__table_name: ', self.__table_name)
    #####################################################################

    def get_one(self, wheres):
        """通过条件获取一条记录"""
        result = self.__model.get(wheres)
        # print('pathnfo:12: ',result.id)
        if result:
            return result
        return {}

    def get_for_pk(self, pk):
        """通过主键值获取数据库记录实体"""

        return self.get_one(getattr(self.__model,self.__pk_name) == str(pk))

    def get_value(self, column_name, wheres=''):
        """
        获取指定条件的字段值————多于条记录时，只取第一条记录
        :param column_name: 单个字段名，如：id
        :param wheres: 查询条件
        :return: 7 （指定的字段值）
        """
        result = self.__model.select(column_name).where(wheres).execute()
        # print('pathnfo:12345')
        if result:
            return result
        return {}

    def add(self, fields, wheres=''):
        """新增数据库记录"""
        # print(fields)
        # print('pathnfo:aa12')
        # print(wheres)
        if wheres:
            # print('pathnfo:bb12')
            nub = self.__model.update(**fields).where(wheres).execute()

        else:
            # print('pathnfo:cc12')
            nub = self.__model.updata(**fields).execute()
        return nub

    def edit(self, fields, wheres=''):
        """
        批量编辑数据库记录
        :param fields: 要更新的字段（字段名与值存储在字典中）
        :param wheres: 更新条件
        :param returning: 更新成功后，返回的字段名
        :param is_update_cache: 是否同步更新缓存
        :return:
        """
        ### 拼接sql语句 ###
        # 拼接字段与值
        # field_list = [key + ' = %(' + key + ')s' for key in fields.keys()]
        # # 设置sql拼接字典
        # parameter = {
        #     'table_name': self.__table_name,
        #     'pk_name': self.__pk_name,
        #     'field_list': ','.join(field_list)
        # }
        # 如果存在更新条件，则将条件添加到sql拼接更换字典中
        if wheres:
            nub = self.__model.update(**fields).where(wheres).execute()
        else:
            nub = self.__model.update(**fields).execute()
        return nub
        # 如果有指定返回参数，则添加
        # if returning:
        #     parameter['returning'] = ', ' + returning
        # else:
        #     parameter['returning'] = ''
        #
        # # 生成sql语句
        # sql = "update %(table_name)s set %(field_list)s %(wheres)s returning %(pk_name)s %(returning)s" % parameter
        # return sql % fields

    def edit_pk(self, pk, fields, wheres='', returning=''):
        """编辑单条数据库记录"""
        if wheres:
            wheres = self.__pk_name == str(pk) and wheres
        else:
            wheres = self.__pk_name == str(pk)

        return self.edit(fields, wheres)

    def delete(self, wheres=''):
        """
        批量删除数据库记录
        :param wheres: 删除条件
        :param returning: 删除成功后，返回的字段名
        :param is_update_cache: 是否同步更新缓存
        :return:
        """
        # 如果存在条件
        if wheres:
            nub = self.__model.delete().where(wheres).execute()
        else:
            nub = self.__model.delete().execute()

        return nub
        # 如果有指定返回参数，则添加
        # if returning:
        #     returning = ', ' + returning
        #
        # # 生成sql语句
        # sql = "delete from %(table_name)s %(wheres)s returning %(pk_name)s %(returning)s" % \
        #       {'table_name': self.__table_name, 'wheres': wheres, 'pk_name': self.__pk_name, 'returning': returning}
        # return sql

    def delete_pk(self, pk, wheres='', returning=''):
        """删除单条数据库记录"""
        if wheres:
            wheres = self.__pk_name == str(pk) and wheres
        else:
            wheres = self.__pk_name == str(pk)

        return self.delete(wheres)

    def get_list(self, column_name_list='', wheres='', page_number=None, page_size=None,  orderby=None,table_name=None):
        """
        获取指定条件的数据库记录集
        :param column_name_list:      查询字段
        :param wheres:      查询条件
        :param page_number:   分页索引值
        :param page_size:    分页大小， 存在值时才会执行分页
        :param orderby:     排序规则
        :param table_name:     查询数据表，多表查询时需要设置
        :return: 返回记录集总数量与分页记录集
            {'records': 0, 'total': 0, 'page': 0, 'rows': []}
        """
        # 初始化输出参数：总记录数量与列表集
        data = {
            'records': 0,  # 总记录数
            'total': 0,  # 总页数
            'page': 1,  # 当前页面索引
            'rows': [],  # 查询结果（记录列表）
        }
        print('wheres0', wheres)
        # 初始化查询字段名
        if column_name_list:
            print('column_name_list ',column_name_list)
            result = self.__model.select(*column_name_list)
        else:
            result = self.__model.select()
        # print('012')
        # 初始化查询条件
        if wheres:
                # 如果是字符串，表示该查询条件已组装好了，直接可以使用
                # 如果是list，则表示查询条件有多个，可以使用join将它们用and方式组合起来使用
                # print('wheres1', wheres)
                if isinstance(wheres,( list,tuple)):
                    wheres =reduce(operator.and_, wheres) #join('%s' %id for id in wheres)
                #     print('wheres2', wheres)
                result = result.where(wheres)

        # 初始化排序
        if not orderby:
            # print('self.__pk_name',getattr(self.__model,self.__pk_name))
            # print('self.__model', self.__model.__name__)
            # n=self.__model.__name__+'.'+self.__pk_name

            # print('012', n)
            orderby = getattr(self.__model,self.__pk_name).desc()
            # print('012', orderby)
        result = result.order_by(orderby)
            # result = result.order_by(self.__model.id.desc)
        # 初始化分页查询的记录区间

        # print('0123')
        # paging = ''

        # 判断是否需要进行分页
        if not page_size is None:
            # ### 执行sql，获取指定条件的记录总数量
            # sql = 'select count(1) as records from %(table_name)s %(wheres)s ' % \
            #       {'table_name': table_name, 'wheres': wheres}
            # result = db.execute(sql)

            # 如果查询失败或不存在指定条件记录，则直接返回初始值
            if not result or result.count() == 0:
                return data

            # 设置记录总数量
            data['records'] = result.count()

            #########################################################
            ### 设置分页索引与页面大小 ###
            if page_size <= 0:
                page_size = 10
            # 计算总分页数量：通过总记录数除于每页显示数量来计算总分页数量
            if data['records'] % page_size == 0:
                page_total = data['records'] // page_size
            else:
                page_total = data['records'] // page_size + 1
            # 判断页码是否超出限制，超出限制查询时会出现异常，所以将页面索引设置为最后一页
            if page_number < 1 or page_number > page_total:
                page_number = page_total
            # 记录总页面数量
            data['total'] = page_total
            # 记录当前页面值
            data['page'] = page_number
            # 计算当前页面要显示的记录起始位置（limit指定的位置）
            record_number = (page_number - 1) * page_size
            #############################################################
            ### 按条件查询数据库记录
            result = result.paginate(page_size, record_number)
            # results=[r for r in result]#[r.name,r.icon,r.sort,r.is_show,r.is_enabled]
        # else:
        #     result = result.execute()
        if result:
            data['rows'] =result#[r for r in result]
            # 不需要分页查询时，直接在这里设置总记录数
            if page_size is None:
                data['records'] = result.count()
        # print(' result.count()', result.count()),print(' result()', result)
        return data

    # @app.route("/tiles/failed", defaults={"page": 1}, methods=["POST", "GET"])
    # @app.route("/tiles/failed/page/<int:page>", methods=["POST", "GET"])
    # def tiles_failed(page):
    #     if request.method == "POST":
    #         process_id, tile_name = request.form["tile_name"].split("/")
    #         select_status = request.form["select_status"]
    #         if not select_status == "False":
    #             process = models.Process.select().where(models.Process.id == process_id).get()
    #             tile = models.Tile.select().where(
    #                 models.Tile.name == tile_name and models.Tile.process == process).get()
    #             tile.message = "Manual state change from '{from_state}' to '{to_state}'".format(from_state=tile.success,
    #                                                                                             to_state=select_status)
    #             tile.success = select_status
    #             tile.error_count = 0
    #             tile.save()
    #     all_tiles = models.Tile.select().where(models.Tile.success == "False").order_by(models.Tile.name,
    #                                                                                     models.Tile.process)
    #     count = all_tiles.count()
    #     tiles = get_tiles_per_page(all_tiles, page, TILES_PER_PAGE, count)
    #     if not tiles and page != 1:
    #         abort(404)
    #     pagination = Pagination(page, TILES_PER_PAGE, count)
    #     t = app.jinja2_env.get_template("tiles.html")
    #     return t.render(tiles=tiles, pagination=pagination, count=count, request=request)
    # def kf_list():
    #     # 数据查询之分页返回
    #     start = request.values.get('start')
    #     length = request.values.get('length')
    #     try:
    #         find = model.py_user_kf.select().order_by(model.py_user_kf.create_time).paginate(int(start), int(length))
    #         index = 0
    #         list = []
    #         while index < len(find):
    #             print(find[index].name)
    #             list.append(
    #                 {'id': find[index].id, 'num': find[index].num, 'name': find[index].name, 'type': find[index].type,
    #                  'user': find[index].user,
    #                  'login_time': find[index].login_time, 'create_time': find[index].create_time})
    #             index += 1
    #         return json({
    #             'code': 200,
    #             'message': '查询成功',
    #             'data': list
    #         })
    #     except:
    #         return json({
    #             'code': 401,
    #             'message': '查询失败'
    #         })

    def get_count(self, wheres=''):
        """获取指定条件记录数量"""
        if wheres:
            result = self.__model.select().where(wheres).count()
        else:
            result = self.__model.select().count()

        return result

    def get_sum(self, fields, wheres):
        """获取指定条件记录数量"""
        # sql = 'select sum(%(fields)s) as total from %(table_name)s where %(wheres)s ' % \
        #       {'table_name': self.__table_name, 'wheres': wheres, 'fields': fields}
        result = self.__model.select(fn.sum(fields).alias('total'))
        if result:
            return result[0].get('total')
        return 0

    def get_min(self, fields, wheres):
        """获取该列记录最小值"""

        result = self.__model.select(fn.sum(fields).alias('min'))
        # 如果查询存在记录，则返回true
        if result and result[0].get('min'):
            return result[0].get('min')
        return 0

    def get_max(self, fields, wheres):
        """获取该列记录最大值"""
        result = self.__model.select(fn.sum(fields).alias('max'))
        if result and result[0].get('max'):
            return result[0].get('max')
        return 0

    #####################################################################

    #####################################################################

    def exists(self, wheres):
        """检查指定条件的记录是否存在"""
        return self.get_count(wheres) > 0

    #####################################################################
    ### 缓存操作方法 ###

    def get_cache_key(self, pk):
        """获取缓存key值"""
        return ''.join((self.__table_name, '_', str(pk)))

    def set_model_for_cache(self, pk, value, time=43200):
        """更新存储在缓存中的数据库记录，缓存过期时间为12小时"""
        # 生成缓存key
        key = self.get_cache_key(pk)
        # 存储到nosql缓存中
        cache_helper.set(key, value, time)

    def get_model_for_cache(self, pk):
        """从缓存中读取数据库记录"""
        # 生成缓存key
        key = self.get_cache_key(pk)
        # 从缓存中读取数据库记录
        result = cache_helper.get(key)
        # 缓存中不存在记录，则从数据库获取
        if not result:
            result = self.get_for_pk(pk)
            self.set_model_for_cache(pk, result)
        if result:
            return result
        else:
            return {}

    def get_model_for_cache_of_where(self, where):
        """
        通过条件获取记录实体——条件必须是额外的主键，也就是说记录是唯一的（我们经常需要使用key、编码或指定条件来获取记录，这时可以通过当前方法来获取）
        :param where: 查询条件
        :return: 记录实体
        """
        # 生成实体缓存key
        model_cache_key = self.__table_name + encrypt_helper.md5(str(where))
        # 通过条件从缓存中获取记录id
        pk = cache_helper.get(model_cache_key)
        # 如果主键id存在，则直接从缓存中读取记录

        if pk:
            return self.get_model_for_cache(pk)

        # 否则从数据库中获取
        result = self.get_one(where)
        # print('result: ',result)
        if result:
            # 存储条件对应的主键id值到缓存中
            # pk_name = result.__getattribute__(self.__pk_name)
            pk_name =getattr( result,self.__pk_name)
            # print('12345678:  ',pk_name)
            # print('12345678:  ',result.__getattribute__(self.__pk_name))
            cache_helper.set(model_cache_key, pk_name)
            # # 存储记录实体到缓存中
            self.set_model_for_cache(pk_name, result)
            # print('1234567')
        return result

    def get_value_for_cache(self, pk, column_name):
        """获取指定记录的字段值"""
        return getattr(self.get_model_for_cache(pk),column_name)

    def del_model_for_cache(self, pk):
        """删除缓存中指定数据"""
        # 生成缓存key
        key = self.get_cache_key(pk)
        # log_helper.info(key)
        # 存储到nosql缓存中
        cache_helper.delete(key)

    def get_model_for_url(self, key):
        """通过当前页面路由url，获取菜单对应的记录"""
        # 使用md5生成对应的缓存key值
        key_md5 = encrypt_helper.md5(key)
        # print('key_md5:  ', key_md5)
        # 从缓存中提取菜单记录
        model = cache_helper.get(key_md5)
        # 记录不存在时，运行记录载入缓存程序
        if not model:
            # print('not model123')
            self._load_cache()
            model = cache_helper.get(key_md5)
            # print(' model1234567')
        return model

    def add_relevance_cache_in_list(self, key):
        """将缓存名称存储到列表里————主要存储与记录变更关联的"""
        # 从nosql中读取全局缓存列表
        cache_list = cache_helper.get(self.__cache_list)
        # print('cache_list:  ',cache_list)
        # 判断缓存列表是否有值，有则进行添加操作
        if cache_list:
            # 判断是否已存储列表中，不存在则执行添加操作
            if not key in cache_list:
                cache_list.append(key)
                cache_helper.set(self.__cache_list, cache_list)
        # 无则直接创建全局缓存列表，并存储到nosql中
        else:
            cache_list = [key]
            cache_helper.set(self.__cache_list, cache_list)

    def del_relevance_cache(self):
        """删除关联缓存————将和数据表记录关联的，个性化缓存全部删除"""
        # 从nosql中读取全局缓存列表
        cache_list = cache_helper.get(self.__cache_list)
        # 清除已删除缓存列表
        cache_helper.delete(self.__cache_list)
        if cache_list:
            # 执行删除操作
            for cache in cache_list:
                cache_helper.delete(cache)

    def _load_cache(self):
        """全表记录载入缓存"""
        # 生成缓存载入状态key，主要用于检查是否已执行了菜单表载入缓存判断
        cache_key = self.__table_name + '_is_load'
        # 将自定义的key存储到全局缓存队列中（关于全局缓存队列请查看前面ORM对应章节说明）

        self.add_relevance_cache_in_list(cache_key)

        # 获取缓存载入状态，检查记录是否已载入缓存，是的话则不再执行
        if cache_helper.get(cache_key):
            return
        # 从数据库中读取全部记录
        result = self.get_list()

        # 标记记录已载入缓存
        cache_helper.set(cache_key, True)
        # 如果菜单表没有记录，则直接退出
        if not result:
            # print('not result')
            return
        # print('result.get(rows, {}): ', result.get('rows', {}))
        # 循环遍历所有记录，组合处理后，存储到nosql缓存中
        for model in result.get('rows', {}):
            # 提取菜单页面对应的接口（后台菜单管理中的接口值，同一个菜单操作时，经常需要访问多个接口，所以这个值有中存储多们接口值）
            # interface_url = model.get('interface_url', '')
            interface_url =getattr(model,'interface_url', '')
            # print(' interfacemodel: ', model)
            # print(' interface_url: ',interface_url)
            if not interface_url:
                continue
            # 获取前端html页面地址
            page_url =getattr( model,'page_url', '')
            # print(' page_url: ',page_url)
            # 同一页面接口可能有多个，所以需要进行分割
            interface_url_arr = interface_url.replace('\n', '').replace(' ', '').split(',')
            # print(' interface_url_arr: ', interface_url_arr)
            # 逐个接口处理
            for interface in interface_url_arr:
                # html+接口组合生成key
                url_md5 = encrypt_helper.md5(page_url + interface)
                # 存储到全局缓存队列中，方便菜单记录更改时，自动清除这些自定义缓存
                # print('  url_md5: ',  url_md5)
                self.add_relevance_cache_in_list(url_md5)
                # 存储到nosql缓存
                cache_helper.set(url_md5, model)

    def get_page_power(self, positions_id):
        """获取当前用户权限"""
        # print('page_power: ')
        page_power = self.get_value_for_cache(positions_id, 'page_power')
        # print('page_power: ', page_power)
        if page_power:
            return ',' + page_power + ','
        else:
            return ','
