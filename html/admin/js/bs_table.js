(function (global, factory) {

      // 检查上下文环境是否为Node
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        // 检测上下文环境是否为AMD或CMD
  typeof define === 'function' && define.amd ? define(factory) :

  (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.BootstrapTable = factory());
})(this, (function () { 'use strict';
     // 顺序替换文本，无替换文本返回空;
    let sprintf = function (str) {
            var args = arguments,
                flag = true,
                i = 1;

            str = str.replace(/%s/g, function () {
                var arg = args[i++];// 对每个匹配值应用函数，i自加1，直到无匹配值;

                if (typeof arg === 'undefined') {
                    flag = false;
                    return '';
                }
                return arg;
            });
            return flag ? str : '';
        };

         /**
         * Easy selector helper function*简易选择器辅助功能
         */
        const select = (el, all = false) => {
            el = el.trim();
            if (all) {
                return [...document.querySelectorAll(el)]
            } else {
                return document.querySelector(el)
            }
        };

        //**BootstrapTable构造函数
    let  BootstrapTable = function (el, options) {
            this.options = options;
            this.$el = select(el);
            this.$el_ = this.$el.clone();// 记录触发元素的初始值，destroy销毁重置的时候使用
            this.timeoutId_ = 0;// 超时计时器，有滚动条的情况下调整表头的水平偏移量
            this.timeoutFooter_ = 0;// 超时计时器，有滚动条的情况下调整表尾的水平偏移量

            this.init();
        };

    BootstrapTable.DEFAULTS = {
        classes: 'table table-hover',// 触发元素table加入的样式;
        locale: undefined,// 设置语言包;
        height: undefined,// 包括分页和工具栏的高度;
        undefinedText: '-',// 无显示文本时默认显示内容;
        sortName: undefined,
        // 初始化排序字段名，须是column.filed主键名;
        // 点击排序后更新options.sortName为被排序列的主键名columns[i].field;
        // 通过主键名在this.header.fields中的序号获取sortName，比较后排序;
        sortOrder: 'asc',// 升序或降序，并且上传
        striped: false,// 触发元素table是否显示间行色
        columns: [[]],
        data: [],
        dataField: 'rows',// 后台传回data数据的字段名
        method: 'get',// ajax发送类型
        url: undefined,// ajax发送地址
        ajax: undefined,
        // 用户自定义ajax，或通过字符串调用window下的方法，对插件内配置有较多使用，调用其实不便
        cache: true,// ajax设置
        contentType: 'application/json',
        dataType: 'json',
        ajaxOptions: {},
        queryParams: function (params) {
            return params;
        },
        queryParamsType: 'limit', // undefined
        responseHandler: function (res) {
            return res;
        },// ajax处理相应的函数
        pagination: false,// 分页是否显示
        onlyInfoPagination: false,// 分页文案提示只显示有多少条数据
        sidePagination: 'client', // client or server 前台分页或后台分页
        totalRows: 0, // server side need to set
        pageNumber: 1,// 初始化显示第几页
        pageSize: 10,// 初始化页面多少条数据
        pageList: [10, 25, 50, 100],// 每页显示数据量切换配置项
        paginationHAlign: 'right', //right, left 分页浮动设置
        paginationVAlign: 'bottom', //bottom, top, both
        // 分页显示位置，上、下或上下均显示，默认底部显示
        // 设置一页显示多少条数据按钮向上下拉，还是向下下拉，默认向上下拉
        // 设置为both时，分页在上下位置均显示，设置一页显示多少条数据按钮向上下拉
        paginationDetailHAlign: 'left', //right, left 每页几行数据显示区浮动情况
        paginationPreText: '&lsaquo;',// 分页上一页按钮
        paginationNextText: '&rsaquo;',// 分页下一页按钮
        search: false,// 是否支持搜索
        searchOnEnterKey: false,// enter键开启搜索
        strictSearch: false,// 搜索框输入内容是否须和条目显示数据严格匹配，false时只要键入部分值就可获得结果
        searchAlign: 'right',// 搜索框对齐方式
        selectItemName: 'btSelectItem',// 复选框默认上传name值
        showHeader: true,// 显示表头，包含标题栏内容
        showFooter: false,// 默认隐藏表尾
        showColumns: false,// 显示筛选条目按钮
        showPaginationSwitch: false,// 显示分页隐藏展示按钮
        showRefresh: false,// 显示刷新按钮
        showToggle: false,// 显示切换表格显示或卡片式详情显示按钮
        buttonsAlign: 'right',// 显示隐藏分页、刷新、切换表格或卡片显示模式、筛选显示条目、下载按钮浮动设置
        smartDisplay: true,
        // smartDisplay为真，当总页数为1时，屏蔽分页，以及下拉列表仅有一条时，屏蔽切换条目数按钮下拉功能
        escape: false,// 是否转义
        minimumCountColumns: 1,// 最小显示条目数
        idField: undefined,// data中存储复选框value的键值
        uniqueId: undefined,// 从data中获取每行数据唯一标识的属性名
        cardView: false,// 是否显示卡片式详情（移动端），直接罗列每行信息，不以表格形式显现
        detailView: false,// 表格显示数据时，每行数据前是否有点击按钮，显示这行数据的卡片式详情
        detailFormatter: function (index, row) {
            return '';
        },// 折叠式卡片详情渲染文本，包含html标签、Dom元素
        trimOnSearch: true,// 搜索框键入值执行搜索时，清除两端空格填入该搜索框
        clickToSelect: false,
        singleSelect: false,// 复选框只能单选，需设置column.radio属性为真
        toolbar: undefined,// 用户自定义按钮组，区别于搜索框、分页切换按钮等
        toolbarAlign: 'left',// 用户自定义按钮组浮动情况
        checkboxHeader: true,// 为否隐藏全选按钮
        sortable: true,// 可排序全局设置
        silentSort: true,// ajax交互的时候是否显示loadding加载信息
        maintainSelected: false,// 为真且翻页时，保持前一页各条row[that.header.stateField]为翻页前的值
        searchTimeOut: 500,
        // 搜索框键入值敲enter后隔多少时间执行搜索，使用clearTimeout避免间隔时间内多次键入反复搜索
        searchText: '',// 初始化搜索内容
        iconSize: undefined,// 按钮、搜索输入框通用大小，使用bootstrap的sm、md、lg等
        iconsPrefix: 'glyphicon', // 按钮通用样式
        icons: {
            paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down',// 显示分页按钮
            paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up',// 隐藏分页按钮
            refresh: 'glyphicon-refresh icon-refresh',// 刷新按钮
            toggle: 'glyphicon-list-alt icon-list-alt',// 切换表格详情显示、卡片式显示按钮
            columns: 'glyphicon-th icon-th',// 筛选条目按钮
            detailOpen: 'glyphicon-plus icon-plus',// 卡片式详情展开按钮
            detailClose: 'glyphicon-minus icon-minus'// 卡片式详情折叠按钮
        },// 工具栏按钮具体样式

        rowStyle: function (row, index) {
            return {};
        },// 传递给每一行的css设置，row为这一行的data数据

        rowAttributes: function (row, index) {
            return {};
        },// 传递给每一行的属性设置

        onAll: function (name, args) {
            return false;
        },
        onClickCell: function (field, value, row, $element) {
            return false;
        },
        onDblClickCell: function (field, value, row, $element) {
            return false;
        },
        onClickRow: function (item, $element) {
            return false;
        },
        onDblClickRow: function (item, $element) {
            return false;
        },
        onSort: function (name, order) {
            return false;
        },
        onCheck: function (row) {
            return false;
        },
        onUncheck: function (row) {
            return false;
        },
        onCheckAll: function (rows) {
            return false;
        },
        onUncheckAll: function (rows) {
            return false;
        },
        onCheckSome: function (rows) {
            return false;
        },
        onUncheckSome: function (rows) {
            return false;
        },
        onLoadSuccess: function (data) {
            return false;
        },
        onLoadError: function (status) {
            return false;
        },
        onColumnSwitch: function (field, checked) {
            return false;
        },
        onPageChange: function (number, size) {
            return false;
        },
        onSearch: function (text) {
            return false;
        },
        onToggle: function (cardView) {
            return false;
        },
        onPreBody: function (data) {
            return false;
        },
        onPostBody: function () {
            return false;
        },
        onPostHeader: function () {
            return false;
        },
        onExpandRow: function (index, row, $detail) {
            return false;
        },
        onCollapseRow: function (index, row) {
            return false;
        },
        onRefreshOptions: function (options) {
            return false;
        },
        onResetView: function () {
            return false;
        }
    };

    BootstrapTable.LOCALES = [];

    BootstrapTable.LOCALES['en-US'] = BootstrapTable.LOCALES['en'] = {
        formatLoadingMessage: function () {
            return 'Loading, please wait...';
        },
        formatRecordsPerPage: function (pageNumber) {
            return sprintf('%s records per page', pageNumber);
        },// 每页显示条目数提示文案
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return sprintf('Showing %s to %s of %s rows', pageFrom, pageTo, totalRows);
        },// 分页提示当前页从第pageFrom到pageTo，总totalRows条
        formatDetailPagination: function (totalRows) {
            return sprintf('Showing %s rows', totalRows);// 分页提示供多少条数据
        },
        formatSearch: function () {
            return 'Search';
        },// 设置搜索框placeholder属性
        formatNoMatches: function () {
            return 'No matching records found';
        },// 没有数据时提示文案
        formatPaginationSwitch: function () {
            return 'Hide/Show pagination';
        },// 显示隐藏分页按钮title属性提示文案
        formatRefresh: function () {
            return 'Refresh';
        },// 刷新按钮title属性提示文案
        formatToggle: function () {
            return 'Toggle';
        },// 切换表格、卡片显示模式按钮title属性提示文案
        formatColumns: function () {
            return 'Columns';
        },// 筛选显示条目按钮title属性提示文案
        formatAllRows: function () {
            return 'All';
        }
    };

    Object.assign(BootstrapTable.DEFAULTS, BootstrapTable.LOCALES['en-US']);

    BootstrapTable.COLUMN_DEFAULTS = {
        radio: false,// 有否radio，有则options.singleSelect设为真
        checkbox: false,// 有否checkbox，options.singleSelect设为真，checkbox单选
        checkboxEnabled: true,// 复选框是否可选
        field: undefined,// 后台数据的id号
        title: undefined,// 内容文案
        titleTooltip: undefined,// title属性文案
        'class': undefined,// 样式
        align: undefined, // tbody、thead、tfoot文本对齐情况
        halign: undefined, // thead文本对齐情况
        falign: undefined, // tfoot文本对齐情况
        valign: undefined, // 垂直对齐情况
        width: undefined, // 宽度，字符串或数值输入，均转化为"36px"或"10%"形式
        sortable: false,// 是否可排序，options.sortable设置为真的时候可用
        order: 'asc', // asc, desc
        visible: true,// 可见性
        switchable: true,// 该条目可以通过筛选条目按钮切换显示状态
        clickToSelect: true,
        formatter: undefined,
        // 以function(field,row,index){}格式化数据，field后台字段，row行数据，index对应row的序号值
        // 无配置时以title显示，有配置时以返回值显示
        footerFormatter: undefined,// 填充表尾内容
        events: undefined,// 数据格式为[{"click element":functionName}],回调中传入（value,row,index）
        sorter: undefined,// 调用sorter函数或window[sorter]函数进行排序，高优先级
        sortName: undefined,// 进行排序的字段名，用以获取options.data中的数据
        cellStyle: undefined,
        // 调用cellStyle函数或window[cellStyle]函数添加样式以及类;
        // 以function(field,row,index){}设置单元格样式以及样式类，返回数据格式为{classes:"class1 class2",css:{key:value}}
        searchable: true,// 设置哪一列的数据元素可搜索
        searchFormatter: true,
        cardVisible: true// 设为否时，卡片式显示时该列数据不显示
    };

    BootstrapTable.EVENTS = {
        'all.bs.table': 'onAll',
        'click-cell.bs.table': 'onClickCell',
        'dbl-click-cell.bs.table': 'onDblClickCell',
        'click-row.bs.table': 'onClickRow',
        'dbl-click-row.bs.table': 'onDblClickRow',
        'sort.bs.table': 'onSort',
        'check.bs.table': 'onCheck',
        'uncheck.bs.table': 'onUncheck',
        'check-all.bs.table': 'onCheckAll',
        'uncheck-all.bs.table': 'onUncheckAll',
        'check-some.bs.table': 'onCheckSome',
        'uncheck-some.bs.table': 'onUncheckSome',
        'load-success.bs.table': 'onLoadSuccess',
        'load-error.bs.table': 'onLoadError',
        'column-switch.bs.table': 'onColumnSwitch',
        'page-change.bs.table': 'onPageChange',
        'search.bs.table': 'onSearch',
        'toggle.bs.table': 'onToggle',
        'pre-body.bs.table': 'onPreBody',
        'post-body.bs.table': 'onPostBody',
        'post-header.bs.table': 'onPostHeader',
        'expand-row.bs.table': 'onExpandRow',
        'collapse-row.bs.table': 'onCollapseRow',
        'refresh-options.bs.table': 'onRefreshOptions',
        'reset-view.bs.table': 'onResetView'
    };

    BootstrapTable.prototype.init = function () {
        this.initLocale();
        // 将语言包添加进配置项this.options中，数据格式是{formatLoadingMessage:fn};
        this.initContainer();
        // 创建包裹元素this.container及其子元素this.$toolbar、this.$pagination等，为表格添加样式;
        this.initTable();
        // 获取页面配置更新options.columns、options.data，this.columns记录表体对应标题栏的数据;
        this.initHeader();
        // 渲染表头，设置this.header数据记录主键等，绑定表头事件，卡片式显示时隐藏表头;
        this.initData();
        // 页面初始化、后台传值、表头表尾插入数据，更新this.data、options.data，前台分页则排序;
        this.initFooter();
        // 显示隐藏表尾;
        this.initToolbar();
        // 创建工具栏按钮组，并绑定事件;
        this.initPagination();
        // 创建分页相关内容，并绑定事件;
        this.initBody();
        // 渲染表体，区分卡片显示和表格显示两类，绑定相关事件;
        this.initSearchText();
        // 初始化若设置搜索文本，开启搜索，不支持本地数据搜索;
        this.initServer();
        // 上传数据，成功时调用load方法渲染表格;
    };

    // 将语言包添加进配置项this.options中，数据格式是{formatLoadingMessage:fn};
    BootstrapTable.prototype.initLocale = function () {
        if (this.options.locale) {
            var parts = this.options.locale.split(/-|_/);
            parts[0].toLowerCase();
            parts[1] && parts[1].toUpperCase();
            if ($.fn.bootstrapTable.locales[this.options.locale]) {
                $.extend(this.options, $.fn.bootstrapTable.locales[this.options.locale]);
            } else if ($.fn.bootstrapTable.locales[parts.join('-')]) {
                $.extend(this.options, $.fn.bootstrapTable.locales[parts.join('-')]);
            } else if ($.fn.bootstrapTable.locales[parts[0]]) {
                $.extend(this.options, $.fn.bootstrapTable.locales[parts[0]]);
            }
        }
    };

    // 创建包裹元素this.container及其子元素this.$toolbar、this.$pagination等，为表格添加样式;
    BootstrapTable.prototype.initContainer = function () {
        this.$container =  document.createElement([
            '<div class="bootstrap-table">',
            '<div class="fixed-table-toolbar"></div>',
            this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ?
                '<div class="fixed-table-pagination" style="clear: both;"></div>' :
                '',
            '<div class="fixed-table-container">',
            '<div class="fixed-table-header"><table></table></div>',
            '<div class="fixed-table-body">',
            '<div class="fixed-table-loading">',
            this.options.formatLoadingMessage(),
            '</div>',
            '</div>',
            '<div class="fixed-table-footer"><table><tr></tr></table></div>',
            this.options.paginationVAlign === 'bottom' || this.options.paginationVAlign === 'both' ?
                '<div class="fixed-table-pagination"></div>' :
                '',
            '</div>',
            '</div>'
        ].join(''));

        this.$container.insertAfter(this.$el);
        this.$tableContainer = this.$container.querySelectorAll('.fixed-table-container');
        this.$tableHeader = this.$container.querySelectorAll('.fixed-table-header');
        this.$tableBody = this.$container.querySelectorAll('.fixed-table-body');
        this.$tableLoading = this.$container.querySelectorAll('.fixed-table-loading');
        this.$tableFooter = this.$container.querySelectorAll('.fixed-table-footer');
        this.$toolbar = this.$container.querySelectorAll('.fixed-table-toolbar');
        this.$pagination = this.$container.querySelectorAll('.fixed-table-pagination');

        this.$tableBody.append(this.$el);
        this.$container.after('<div class="clearfix"></div>');

        this.$el.addClass(this.options.classes);
        if (this.options.striped) {
            this.$el.addClass('table-striped');
        }
        if ($.inArray('table-no-bordered', this.options.classes.split(' ')) !== -1) {
            this.$tableContainer.addClass('table-no-bordered');
        }
    };




    }
);