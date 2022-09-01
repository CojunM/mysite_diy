create table department
(
  id        serial                   not null
    constraint department_pkey
      primary key,
  code      text    default ''::text not null,
  name      text    default ''::text not null,
  parent_id integer default 0,
  sort      integer default 0,
  level     integer default 0,
  is_leaf   boolean default false,
  expanded  boolean default false
);

comment on table department is '部门管理表';

comment on column department.id is '主键Id';

comment on column department.code is '部门ID，内容为010101，即每低一级部门，编码增加两位小数';

comment on column department.name is '部门名称';

comment on column department.parent_id is '父ID';

comment on column department.sort is '排序';

comment on column department.level is '树列表深度级别，即当前数据在哪一级';

comment on column department.is_leaf is '是否最终节点';

comment on column department.expanded is '此节点是否展开，后台菜单列表js要用到，不用进行编辑';

alter table department
  owner to postgres;

create unique index department_code_idx
  on department (code);

create index department_sort_idx
  on department (sort);

INSERT INTO public.department (id, code, name, parent_id, sort, level, is_leaf, expanded) VALUES (2, '0101', '软件开发部', 1, 1, 1, true, false);
INSERT INTO public.department (id, code, name, parent_id, sort, level, is_leaf, expanded) VALUES (3, '0102', '行政部', 1, 2, 1, true, false);
INSERT INTO public.department (id, code, name, parent_id, sort, level, is_leaf, expanded) VALUES (4, '0103', '财务部', 1, 2, 1, true, false);
INSERT INTO public.department (id, code, name, parent_id, sort, level, is_leaf, expanded) VALUES (1, '01', 'xx公司', 0, 1, 0, false, false);
create table infomation
(
  id              serial                     not null
    constraint infomation_pkey
      primary key,
  title           text         default ''::text,
  front_cover_img text         default ''::text,
  content         text         default ''::text,
  add_time        timestamp(0) default now() not null
);

comment on table infomation is '信息表';

comment on column infomation.id is '主键Id';

comment on column infomation.title is '标题';

comment on column infomation.front_cover_img is '封面图片地址（首页）';

comment on column infomation.content is '内容';

comment on column infomation.add_time is '添加时间';

alter table infomation
  owner to postgres;

INSERT INTO public.infomation (id, title, front_cover_img, content, add_time) VALUES (2, '联系我们', '', '<p><span>    地址：广州市天河区黄浦大道XX号</span><br><span>    邮编： 510000</span><br><span>    电话： 4008-0000-00 020-00000000</span><br><span>    Email：xxxx@xxx.com</span></p><p><span><img src="http://api.map.baidu.com/staticimage?center=113.271429,23.135336&amp;zoom=13&amp;width=530&amp;height=340&amp;markers=113.271429,23.135336" width="530" height="340"></span></p>', '2018-08-30 15:25:19');
INSERT INTO public.infomation (id, title, front_cover_img, content, add_time) VALUES (1, '公司介绍', 'http://localhost:81/upload/20180830/20180830162343CYK2U.gif', '<p>XXXX物科技有限公xxxx集团，成立于2011年3月，注册资本1000万元，是XXXX开发销售的公司，主要XXX产品的销售。 旗下的XXX品牌源自XXX先生创立XXX，经过一百多年的发展，现已成为最具规模化，现代化，专业化的XXXX生产企业之一。 公司特与XXXX超市股份有限公司、XXXX集团股份有限公司等合作，在XX省多个城市100多家门店进行销售。</p><p>    公司本着“客户至上，质量为本”的原则，建立健全了严苛的质量标准检验体系，除了通过国家食品认证体系之外，还委托国家轻工业食品质量监督检测XX站特别做了XXX检测，XXX检测，以远远低于国家标准的检测结果确保XX品质。</p>', '2018-08-30 15:25:10');
create table manager
(
  id              serial                        not null
    constraint manager_pkey
      primary key,
  login_name      text         default ''::text not null,
  login_password  text         default ''::text not null,
  login_key       text         default ''::text,
  last_login_time timestamp(0),
  last_login_ip   text         default ''::text,
  login_count     integer      default 0,
  create_time     timestamp(0) default now()    not null,
  department_id   integer      default 0,
  department_code text         default ''::text,
  department_name text         default ''::text,
  positions_id    integer      default 0,
  positions_name  text         default ''::text,
  is_work         boolean      default false,
  is_enabled      boolean      default false,
  name            text         default ''::text not null,
  sex             text         default ''::text,
  birthday        date,
  mobile          text         default ''::text,
  email           text         default ''::text,
  remark          text         default ''::text,
  manager_id      integer      default 0,
  manager_name    text         default ''::text
);

comment on table manager is '管理员管理表';

comment on column manager.id is '主键Id';

comment on column manager.login_name is '登陆账号';

comment on column manager.login_password is '登陆密码';

comment on column manager.login_key is '登录密钥';

comment on column manager.last_login_time is '最后登陆时间';

comment on column manager.last_login_ip is '最后登陆IP';

comment on column manager.login_count is '登陆次数';

comment on column manager.create_time is '注册时间';

comment on column manager.department_id is '部门自编号Id，用户只能归属于一个部门';

comment on column manager.department_code is '部门编号';

comment on column manager.department_name is '部门名称';

comment on column manager.positions_id is '用户职位Id';

comment on column manager.positions_name is '职位名称';

comment on column manager.is_work is '0=离职，1=就职';

comment on column manager.is_enabled is '账号是否启用，true=启用，false=禁用';

comment on column manager.name is '用户中文名称';

comment on column manager.sex is '性别（未知，男，女）';

comment on column manager.birthday is '出生日期';

comment on column manager.mobile is '手机号码';

comment on column manager.email is '个人--联系邮箱';

comment on column manager.remark is '备注';

comment on column manager.manager_id is '操作人员id';

comment on column manager.manager_name is '操作人员姓名';

alter table manager
  owner to postgres;

create index manager_department_code_idx
  on manager (department_code);

create index manager_department_id_idx
  on manager (department_id);

create index manager_is_enabled_idx
  on manager (is_enabled);

create index manager_is_work_idx
  on manager (is_work);

create index manager_last_login_time_idx
  on manager (last_login_time);

create unique index manager_login_name_idx1
  on manager (login_name);

create index manager_manager_id_idx
  on manager (manager_id);

create index manager_manager_name_idx
  on manager (manager_name);

create index manager_name_idx
  on manager (name);

create index manager_positions_id_idx
  on manager (positions_id);

INSERT INTO public.manager (id, login_name, login_password, login_key, last_login_time, last_login_ip, login_count, create_time, department_id, department_code, department_name, positions_id, positions_name, is_work, is_enabled, name, sex, birthday, mobile, email, remark, manager_id, manager_name) VALUES (1, 'admin', 'e10adc3949ba59abbe56e057f20f883e', '', '2022-05-20 18:38:39', '127.0.0.1', 24, '2018-08-23 15:58:52', 2, '0101', '软件开发部', 1, '软件开发人员', true, true, 'admin', '男', null, '13900000000', '', '', 0, '');
create table manager_operation_log
(
  id           serial                     not null
    constraint manager_operation_log_pkey
      primary key,
  ip           text         default ''::text,
  remark       text         default ''::text,
  manager_id   integer      default 0,
  manager_name text         default ''::text,
  add_time     timestamp(0) default now() not null
);

comment on table manager_operation_log is '管理员操作日志表';

comment on column manager_operation_log.id is '主键Id';

comment on column manager_operation_log.ip is '登陆IP';

comment on column manager_operation_log.remark is '操作内容';

comment on column manager_operation_log.manager_id is '操作人员id';

comment on column manager_operation_log.manager_name is '操作人员姓名';

comment on column manager_operation_log.add_time is '添加时间';

alter table manager_operation_log
  owner to postgres;

create index manager_operation_log_add_time_idx
  on manager_operation_log (add_time);

create index manager_operation_log_manager_id_idx
  on manager_operation_log (manager_id);

create index manager_operation_log_manager_name_idx
  on manager_operation_log (manager_name);

INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (1, '127.0.0.1', '用户进行访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:19:32');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (2, '127.0.0.1', '用户进行访问[菜单管理添加]操作', 1, 'admin', '2018-09-14 10:19:35');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (3, '127.0.0.1', '用户进行访问[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:19:35');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (4, '127.0.0.1', '用户进行[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:19:38');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (5, '127.0.0.1', '用户进行访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:19:40');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (6, '127.0.0.1', '用户进行访问[菜单管理添加]操作', 1, 'admin', '2018-09-14 10:22:06');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (7, '127.0.0.1', '用户进行访问[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:22:07');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (8, '127.0.0.1', '用户进行访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:22:12');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (9, '127.0.0.1', '用户进行访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:22:49');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (10, '127.0.0.1', '用户进行[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:22:53');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (11, '127.0.0.1', '用户进行访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:22:55');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (12, '127.0.0.1', '用户[信息管理公司介绍]操作', 1, 'admin', '2018-09-14 10:26:36');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (13, '127.0.0.1', '用户进行[信息管理公司介绍]操作', 1, 'admin', '2018-09-14 10:27:22');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (14, '127.0.0.1', '用户访问[http://localhost/api/product_class/]接口地址时，检测没有操作权限', 1, 'admin', '2018-09-14 10:28:15');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (15, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:30:00');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (16, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:30:03');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (17, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:30:05');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (18, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:30:07');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (19, '127.0.0.1', '用户访问[http://localhost/api/product_class/]接口地址时，检测没有操作权限', 1, 'admin', '2018-09-14 10:30:22');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (20, '127.0.0.1', '用户进行[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:31:48');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (21, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:31:50');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (22, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:31:52');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (23, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:31:54');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (24, '127.0.0.1', '用户进行[菜单管理编辑]操作', 1, 'admin', '2018-09-14 10:32:00');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (25, '127.0.0.1', '用户访问[菜单管理列表]操作', 1, 'admin', '2018-09-14 10:32:02');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (26, '127.0.0.1', '用户进行[产品分类管理添加]操作', 1, 'admin', '2018-09-14 10:32:05');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (27, '127.0.0.1', '用户进行[产品分类管理添加]操作', 1, 'admin', '2018-09-14 10:32:43');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (28, '127.0.0.1', '用户进行[产品分类管理删除]操作', 1, 'admin', '2018-09-14 10:32:48');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (29, '127.0.0.1', '用户进行[产品列表添加]操作', 1, 'admin', '2018-09-14 10:33:32');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (30, '127.0.0.1', '用户进行[产品列表编辑]操作', 1, 'admin', '2018-09-14 10:33:49');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (31, '127.0.0.1', '用户进行[产品列表编辑]操作', 1, 'admin', '2018-09-14 10:33:49');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (32, '127.0.0.1', '用户进行[产品列表删除]操作', 1, 'admin', '2018-09-14 10:34:00');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (33, '127.0.0.1', '用户进行[产品添加]操作', 1, 'admin', '2018-09-14 10:37:47');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (34, '127.0.0.1', '用户进行[产品删除]操作', 1, 'admin', '2018-09-14 10:37:53');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (35, '127.0.0.1', '【admin】退出登录', 1, 'admin', '2018-09-14 12:03:23');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (36, '127.0.0.1', '【admin】登陆成功', 1, 'admin', '2018-09-14 12:05:32');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (37, '127.0.0.1', '用户访问[主界面]操作', 1, 'admin', '2018-09-14 12:05:33');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (38, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:21:42');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (39, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:21:45');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (40, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:22:26');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (41, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:22:28');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (42, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:22:50');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (43, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:22:52');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (44, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:22:53');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (45, '127.0.0.1', '用户进行[菜单编辑]操作', 1, 'admin', '2018-09-14 14:22:58');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (46, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:23:01');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (47, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:23:04');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (48, '127.0.0.1', '用户进行[菜单编辑]操作', 1, 'admin', '2018-09-14 14:23:19');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (49, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:23:21');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (50, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:23:39');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (51, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:23:45');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (52, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:23:50');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (53, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:23:52');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (54, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:23:53');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (55, '127.0.0.1', '用户进行[菜单编辑]操作', 1, 'admin', '2018-09-14 14:24:10');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (56, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:24:12');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (57, '127.0.0.1', '用户进行[菜单添加]操作', 1, 'admin', '2018-09-14 14:24:35');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (58, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:24:37');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (59, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:24:39');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (60, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:24:41');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (61, '127.0.0.1', '用户访问[菜单列表]操作', 1, 'admin', '2018-09-14 14:24:43');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (62, '127.0.0.1', '用户访问[职位列表]操作', 1, 'admin', '2018-09-14 14:24:54');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (63, '127.0.0.1', '用户访问[职位列表]操作', 1, 'admin', '2018-09-14 14:24:54');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (64, '127.0.0.1', '用户访问[职位列表]操作', 1, 'admin', '2018-09-14 14:24:56');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (65, '127.0.0.1', '用户访问[职位列表]操作', 1, 'admin', '2018-09-14 14:24:57');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (66, '127.0.0.1', '用户进行[职位编辑]操作', 1, 'admin', '2018-09-14 14:25:09');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (67, '127.0.0.1', '用户访问[职位列表]操作', 1, 'admin', '2018-09-14 14:25:10');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (68, '127.0.0.1', '用户访问[主界面]操作', 1, 'admin', '2018-09-14 14:25:11');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (69, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:26:31');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (70, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:26:42');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (71, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:26:54');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (72, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:03');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (73, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:06');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (74, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:11');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (75, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:19');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (76, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:23');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (77, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:28');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (78, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:27:38');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (79, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:29:24');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (80, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:29:41');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (81, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:32:04');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (82, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:32:37');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (83, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:32:40');
INSERT INTO public.manager_operation_log (id, ip, remark, manager_id, manager_name, add_time) VALUES (84, '127.0.0.1', '用户访问[员操作日志列表]操作', 1, 'admin', '2018-09-14 14:32:42');
create table menu_info
(
  id            serial                   not null
    constraint menu_info_pkey
      primary key,
  name          text    default ''::text not null,
  icon          text    default ''::text,
  page_url      text    default ''::text,
  interface_url text    default ''::text,
  parent_id     integer default 0,
  sort          integer default 0,
  level         integer default 0,
  is_leaf       boolean default false,
  expanded      boolean default false,
  is_show       boolean default true,
  is_enabled    boolean default true
);

comment on table menu_info is '菜单表';

comment on column menu_info.id is '主键Id';

comment on column menu_info.name is '菜单名称或各个页面功能名称';

comment on column menu_info.icon is '菜单小图标（一级菜单需要设置，二级菜单不用）';

comment on column menu_info.page_url is '各页面URL（主菜单与分类菜单没有URL）';

comment on column menu_info.interface_url is '各接口url';

comment on column menu_info.parent_id is '父ID';

comment on column menu_info.sort is '排序';

comment on column menu_info.level is '树列表深度级别，即当前数据在哪一级';

comment on column menu_info.is_leaf is '是否最终节点';

comment on column menu_info.expanded is '此节点是否展开，后台菜单列表js要用到，不用进行编辑';

comment on column menu_info.is_show is '该菜单是否在菜单栏显示，false=不显示，true=显示';

comment on column menu_info.is_enabled is '是否启用，true=启用，false=禁用';

alter table menu_info
  owner to postgres;

create index menu_info_is_show_idx
  on menu_info (is_show);

create index menu_info_sort_idx
  on menu_info (sort);

INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (12, '产品管理', '&#xe6b5;', '', '', 0, 10, 0, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (1, '系统管理', '&#xe62e;', '', '', 0, 2, 0, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (9, '添加', '', 'department_edit', 'get(/api/system/department/tree/),post(/api/system/department/)', 7, 2, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (10, '编辑', '', 'department_edit', 'get(/api/system/department/tree/),get(/api/system/department/<id:int>/),put(/api/system/department/<id:int>/)', 7, 3, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (39, '管理员操作日志', '', 'manager_operation_log', '', 1, 5, 1, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (15, '添加', '', 'product_class_edit', 'post(/api/product_class/)', 13, 2, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (35, '删除', '', 'manager', 'delete(/api/system/manager/<id:int>/)', 31, 4, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (16, '编辑', '', 'product_class_edit', 'get(/api/product_class/<id:int>/),put(/api/product_class/<id:int>/)', 13, 3, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (3, '列表', '', 'menu_info', 'get(/api/system/menu_info/)', 2, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (38, '主界面', '', 'main', 'get(/api/main/menu_info/)', 0, 1, 0, true, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (2, '菜单管理', '', 'menu_info', '', 1, 1, 1, true, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (6, '删除', '', 'menu_info', 'delete(/api/system/menu_info/<id:int>/)', 2, 4, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (25, '联系我们', '', 'contact_us_edit', '', 23, 2, 1, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (27, '列表', '', 'positions', 'get(/api/system/positions/),get(/api/system/department/),', 26, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (32, '列表', '', 'manager', 'get(/api/system/manager/)', 31, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (40, '列表', '', 'manager_operation_log', 'get(/api/system/manager_operation_log/)', 39, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (28, '添加', '', 'positions_edit', 'get(/api/system/menu_info/positions/<id:int>/),post(/api/system/positions/)', 26, 2, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (17, '删除', '', 'products_class', 'delete(/api/product_class/<id:int>/)', 13, 4, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (29, '编辑', '', 'positions_edit', 'get(/api/system/menu_info/positions/<id:int>/),get(/api/system/positions/<id:int>/),put(/api/system/positions/<id:int>/)', 26, 3, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (21, '编辑', '', 'products_edit', 'get(/api/product_class/),get(/api/product/<id:int>/),put(/api/product/<id:int>/),post(/api/files/)', 18, 3, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (14, '列表', '', 'products_class', 'get(/api/product_class/)', 13, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (5, '编辑', '', 'menu_info_edit', 'get(/api/system/menu_info/tree/),get(/api/system/menu_info/<id:int>/),put(/api/system/menu_info/<id:int>/)', 2, 3, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (13, '产品分类管理', '', 'products_class', '', 12, 1, 1, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (22, '删除', '', 'products_list', 'delete(/api/product/<id:int>/)', 18, 4, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (37, '复职', '', 'manager', 'put(/api/system/manager/<id:int>/reinstated/)', 31, 6, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (36, '离职', '', 'manager', 'put(/api/system/manager/<id:int>/dimission/)', 31, 5, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (18, '产品列表', '', 'products_list', '', 12, 2, 1, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (19, '列表', '', 'products_list', 'get(/api/product_class/),get(/api/product/)', 18, 1, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (20, '添加', '', 'products_edit', 'get(/api/product_class/),post(/api/product/)', 18, 2, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (31, '管理员管理', '', 'manager', '', 1, 4, 1, false, false, true, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (33, '添加', '', 'manager_edit', 'post(/api/system/manager/),get(/api/system/department/tree/),get(/api/system/positions/)', 31, 2, 2, true, false, false, true);
INSERT INTO public.menu_info (id, name, icon, page_url, interface_url, parent_id, sort, level, is_leaf, expanded, is_show, is_enabled) VALUES (34, '编辑', '', 'manager_edit', 'get(/api/system/manager/<id:int>/),put(/api/system/manager/<id:int>/),get(/api/system/department/tree/),get(/api/system/positions/)', 31, 3, 2, true, false, false, true);
create table positions
(
  id              serial                   not null
    constraint positions_pkey
      primary key,
  name            text    default ''::text,
  department_id   integer default 0        not null,
  department_code text    default ''::text not null,
  department_name text    default ''::text,
  page_power      text    default ''::text
);

comment on table positions is '职位管理表';

comment on column positions.id is '主键Id';

comment on column positions.name is '职位名称';

comment on column positions.department_id is '部门自编号ID';

comment on column positions.department_code is '部门编号';

comment on column positions.department_name is '部门名称';

comment on column positions.page_power is '菜单操作权限，有操作权限的菜单ID列表：,1,2,3,4,5,';

alter table positions
  owner to postgres;

create index positions_department_code_idx
  on positions (department_code);

create index positions_department_id_idx
  on positions (department_id);

create index positions_name_idx
  on positions (name);

INSERT INTO public.positions (id, name, department_id, department_code, department_name, page_power) VALUES (1, '软件开发人员', 2, '0101', '软件开发部', ',38,23,25,42,24,41,12,18,22,21,20,19,13,17,16,15,14,1,39,40,31,37,36,35,34,33,32,26,30,29,28,27,7,11,10,9,8,2,6,5,4,3,');
create table product
(
  id                       serial                        not null
    constraint product_pkey
      primary key,
  name                     text         default ''::text not null,
  code                     text         default ''::text,
  product_class_id         integer      default 0,
  standard                 text         default ''::text,
  quality_guarantee_period text         default ''::text,
  place_of_origin          text         default ''::text,
  front_cover_img          text         default ''::text,
  content                  text         default ''::text,
  is_enable                integer      default 0,
  add_time                 timestamp(0) default now()    not null
);

comment on table product is '产品信息';

comment on column product.id is '主键Id';

comment on column product.name is '菜单名称或各个页面功能名称';

comment on column product.code is '产品编码';

comment on column product.product_class_id is '所属产品分类';

comment on column product.standard is '产品规格';

comment on column product.quality_guarantee_period is '保质期';

comment on column product.place_of_origin is '产地';

comment on column product.front_cover_img is '封面图片地址（展示图片）';

comment on column product.content is '产品描述';

comment on column product.is_enable is '是否启用，1=true(启用)，0=false（禁用）';

comment on column product.add_time is '添加时间';

alter table product
  owner to postgres;

INSERT INTO public.product (id, name, code, product_class_id, standard, quality_guarantee_period, place_of_origin, front_cover_img, content, is_enable, add_time) VALUES (15, '葱油饼', '201808031245678', 1, '200g', '1年', '广东深圳', '/upload/20180830/20180830162650s1Uzi.png', '<p>好吃</p>', 1, '2018-08-03 16:51:03');
INSERT INTO public.product (id, name, code, product_class_id, standard, quality_guarantee_period, place_of_origin, front_cover_img, content, is_enable, add_time) VALUES (14, '苏打饼', '201807251234568', 1, '100g', '1年', '广东深圳', '/upload/20180830/20180830162810cJQfu.png', '<p>味道不错</p>', 1, '2018-08-03 00:14:14');
INSERT INTO public.product (id, name, code, product_class_id, standard, quality_guarantee_period, place_of_origin, front_cover_img, content, is_enable, add_time) VALUES (7, '入口即化威化饼', '201807251234568', 2, '150g', '1年', '广东深圳', 'http://localhost:81/upload/20180830/20180830162856nPjF0.png', '<p>赞</p>', 1, '2018-07-25 23:16:25');
INSERT INTO public.product (id, name, code, product_class_id, standard, quality_guarantee_period, place_of_origin, front_cover_img, content, is_enable, add_time) VALUES (2, '香橙味威化饼', '20180212321211', 2, '500g', '1年', '广东广州', '/upload/20180830/20180830163135Dmh9e.png', '<p>产品详情</p>', 1, '2018-07-25 23:10:04');
create table product_class
(
  id        serial                        not null
    constraint product_class_pkey
      primary key,
  name      text         default ''::text not null,
  is_enable integer      default 0,
  add_time  timestamp(0) default now()    not null
);

comment on table product_class is '产品分类';

comment on column product_class.id is '主键Id';

comment on column product_class.name is '菜单名称或各个页面功能名称';

comment on column product_class.is_enable is '是否启用，1=true(启用)，0=false（禁用）';

comment on column product_class.add_time is '添加时间';

alter table product_class
  owner to postgres;

INSERT INTO public.product_class (id, name, is_enable, add_time) VALUES (2, '威化饼', 1, '2018-08-30 16:24:46');
INSERT INTO public.product_class (id, name, is_enable, add_time) VALUES (1, '饼干', 1, '2018-08-17 16:14:54');
INSERT INTO public.product_class (id, name, is_enable, add_time) VALUES (3, '果冻', 1, '2018-09-14 10:32:05');