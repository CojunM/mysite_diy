
(function (global, factory) {
    // alert(global)
    // 检查上下文环境是否为Nodejs环境'
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        // 检测上下文环境是否为AMD或CMD
        typeof define === 'function' && define.amd ? define(factory) :

            (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.BootstrapTable = factory());
})(this, (function () {
    'use strict';

    /*
 *  GridManager: 挂载至Element、window
 *  #001: 如果已经存在，则清除之前的实例，重新进行实例化。原因：如果不清除而直接返回错误，会让使用者存在不便。
 * */


    //    工具函数 


    // 顺序替换文本，无替换文本返回空;  
    var sprintf = function (str) {
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
      * 是否为 string
      * @param o
      * @returns {boolean}
      */
    const isString = (o) => {
        return typeof (o) === 'string';
    };
    // /*
    // *  捆绑至选择器对象
    // * */
    // (() => {
    //     Element.prototype.bootstrapTable = Element.prototype.bt = function () {
    // 		// 方法名
    // 		let name,
    // 		// 参数
    // 		arg,

    // 		// 回调函数
    // 		callback,

    // 		// 条件
    // 		condition;

    // 		const _ = arguments;
    // 		// 格式化参数
    // 		if (!isString(_[0])) {
    // 			// ex: document.querySelector('table').GridManager({arg}, callback)
    // 			name = 'init';
    // 			arg = _[0];
    // 			callback = _[1];
    // 		} else {
    // 			// ex: document.querySelector('table').GridManager('get')
    // 			// ex: document.querySelector('table').GM('showTh', $th);
    // 			// ex: document.querySelector('table').GM('setSort',sortJson,callback, refresh);
    // 			name = _[0];
    // 			arg = _[1];
    // 			callback = _[2];
    // 			condition = _[3];
    // 		}
    //         console.log(this)
    // 		// no init: 执行
    // 	// 	if (name !== 'init') {
    //     //         return GridManager[name](this, arg, callback, condition) || this;
    //     //     }

    //     //     // init
    //     //     new GridManager(this, arg, callback);
    // 	// };
    // // window只存储第一次加载的GM对像, 后续加载的对像将不再向window上挂载
    // if (!Window.BootstrapTable && !Window.bt) {
    //     Window.BootstrapTable = Window.bt = BootstrapTable;
    // }}
    // })();

    function jQueryEach(object, callback, args) {

        var name,

            i = 0,

            length = object.length;

        if (args) {

            if (length == undefined) {

                for (name in object) {

                    if (callback.apply(object[name], args) === false) {

                        break

                    }

                }

            } else {

                for (; i < length;) {

                    if (callback.apply(object[i++], args) === false) {

                        break

                    }

                }

            }

        } else {

            if (length == undefined) {

                for (name in object) {

                    if (callback.call(object[name], name, object[name]) === false) {

                        break

                    }

                }

            } else {

                for (var value = object[0]; i < length && callback.call(value, i, value) !== false; value = object[++i]) { }

            }

        }

        return object

    };




    function isObject(obj) {
        return typeof (obj) === 'object' && obj !== null && !Array.isArray(obj);
    };
    function extend() {
        // var length = arguments.length;
        // var target = arguments[0] || {};
        // if (typeof target != "object" && typeof target != "function") {
        // target = {};
        // }
        // if (length == 1) {
        // target = this;
        // i--;
        // }
        // for (var i = 1; i < length; i++) {
        // var source = arguments[i];
        // for (var key in source) {
        // 使用for in会遍历数组所有的可枚举属性，包括原型。
        // if (Object.prototype.hasOwnProperty.call(source, key)) {
        // target[key] = source[key];
        // }
        // }
        // }
        // return target;

        for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
            args[_key] = arguments[_key];
        }
        var target = args[0] || {};
        var i = 1;
        var deep = false;
        var clone;
        // Handle a deep copy situation
        if (typeof target === 'boolean') {
            deep = target;
            // Skip the boolean and the target
            target = args[i] || {};
            i++;
        }
        // Handle case when target is a string or something (possible in deep copy)
        if (typeof (target) !== 'object' && typeof target !== 'function') {
            target = {};
        }
        for (; i < args.length; i++) {
            var options = args[i];
            // Ignore undefined/null values
            if (typeof options === 'undefined' || options === null) {
                continue;
            }
            // Extend the base object
            // eslint-disable-next-line guard-for-in
            for (var name in options) {
                var copy = options[name];
                // Prevent Object.prototype pollution
                // Prevent never-ending loop
                if (name === '__proto__' || target === copy) {
                    continue;
                }
                var copyIsArray = Array.isArray(copy);
                // Recurse if we're merging plain objects or arrays
                if (deep && copy && (isObject(copy) || copyIsArray)) {
                    var src = target[name];
                    if (copyIsArray && Array.isArray(src)) {
                        if (src.every(function (it) {
                            return !isObject(it) && !Array.isArray(it);
                        })) {
                            target[name] = copy;
                            continue;
                        }
                    }
                    if (copyIsArray && !Array.isArray(src)) {
                        clone = [];
                    } else if (!copyIsArray && !isObject(src)) {
                        clone = {};
                    } else {
                        clone = src;
                    }
                    // Never move original objects, clone them
                    target[name] = extend(deep, clone, copy);
                    // Don't bring in undefined values
                } else if (copy !== undefined) {
                    target[name] = copy;
                }
            }
        }
        return target;


    }

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
    // var MyPlugin = function (el) {
    //     // return new MyPlugin.prototype.init(el)
    //     // $.el = typeof el === "string" ? document.querySelector(el) : el;
    //     // var el = typeof el === "string" ? document.querySelector(el) : el;
    //     console.log(this.el)
    // }
    // var fn = MyPlugin.prototype

    var BootstrapTable = function (el, options) {
        this.options = options;
        // alert(el)
        this.$el = el;
        this.$el_ = this.$el.cloneNode(true);// 记录触发元素的初始值，destroy销毁重置的时候使用  
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
    extend(BootstrapTable.DEFAULTS, BootstrapTable.LOCALES['en-US']);

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
        // // 渲染表头，设置this.header数据记录主键等，绑定表头事件，卡片式显示时隐藏表头;  
        // this.initData();
        // // 页面初始化、后台传值、表头表尾插入数据，更新this.data、options.data，前台分页则排序;  
        // this.initFooter();
        // // 显示隐藏表尾;  
        // this.initToolbar();
        // // 创建工具栏按钮组，并绑定事件;  
        // this.initPagination();
        // // 创建分页相关内容，并绑定事件;  
        // this.initBody();
        // // 渲染表体，区分卡片显示和表格显示两类，绑定相关事件;  
        // this.initSearchText();
        // // 初始化若设置搜索文本，开启搜索，不支持本地数据搜索;  
        // this.initServer();
        // 上传数据，成功时调用load方法渲染表格; 
    };
    // 将语言包添加进配置项this.options中，数据格式是{formatLoadingMessage:fn};  
    BootstrapTable.prototype.initLocale = function () {
        if (this.options.locale) {
            var parts = this.options.locale.split(/-|_/);
            parts[0].toLowerCase();
            parts[1] && parts[1].toUpperCase();
            if (fn.bootstrapTable.locales[this.options.locale]) {
                extend(this.options, fn.bootstrapTable.locales[this.options.locale]);
            } else if (fn.bootstrapTable.locales[parts.join('-')]) {
                extend(this.options, fn.bootstrapTable.locales[parts.join('-')]);
            } else if (fn.bootstrapTable.locales[parts[0]]) {
                extend(this.options, fn.bootstrapTable.locales[parts[0]]);
            };
            console.log(parts)
        }

    };


    // 创建包裹元素this.container及其子元素this.$toolbar、this.$pagination等，为表格添加样式;  
    BootstrapTable.prototype.initContainer = function () {
        this.$el.innerHTML = 'this.options';

        this.$container = [
            '<div class="bootstrap-table">',
            '<div class="fixed-table-toolbar"></div>',
            // this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ?
            //     '<div class="fixed-table-pagination" style="clear: both;"></div>' :
            //     '',
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
            '</div>',
            '<div class="clearfix"></div>'
        ].join('');
        // alert(this.$container)
        this.$el.insertAdjacentHTML('afterend', this.$container);
        // this.$container.insertAfter(this.$el);  
        this.$tableContainer = select('.fixed-table-container');
        this.$tableHeader = select('.fixed-table-header');
        this.$tableBody = select('.fixed-table-body');
        this.$tableLoading = select('.fixed-table-loading');
        this.$tableFooter = select('.fixed-table-footer');
        this.$toolbar = select('.fixed-table-toolbar');
        this.$pagination = select('.fixed-table-pagination');

        this.$tableBody.append(this.$el);
        // this.$container.insertAdjacentHTML('afterEnd', '<div class="clearfix"></div>');

        this.$el.classList.add(this.options.classes.split(' '));
        if (this.options.striped) {
            this.$el.classList.add('table-striped');
        }
        if (inArray('table-no-bordered', this.options.classes.split(' ')) !== -1) {
            this.$tableContainer.classList.add('table-no-bordered');
        }
        // alert(232434)
    };



    // 将paramName的data属性转换成param-name修改完成后输出;  
    var getRealDataAttr = function (dataAttr) {
        for (var attr in dataAttr) {
            // "paramName".split(/(?=[A-Z])/) 返回结果为["param","Name"];  
            var auxAttr = attr.split(/(?=[A-Z])/).join('-').toLowerCase();
            if (auxAttr !== attr) {
                dataAttr[auxAttr] = dataAttr[attr];
                delete dataAttr[attr];
            }
        }
        return dataAttr;
    };
    // 为每条标题栏数据设置filedIndex:所在列/列坐标;  
    /** 
     * 策略： 
     * 表头分割成columns.length（总行数）* totalCol（总列数）的矩阵，以flag矩阵标记为false; 
     * 各标题栏为columns[i][j].rowspan（行数）* columns[i][j].colspan（列数）的小矩阵; 
     * 从左自右、从上而下遍历标题栏小矩阵，将标题栏对应的flag首行、首列标记为true; 
     * 因标题栏只能跨列或跨行，不能既跨行又跨列，函数的实现依赖用户输入正确的options.columns格式， 
     */
    var setFieldIndex = function (columns) {
        var i, j, k,
            totalCol = 0,
            flag = [];
        // console.log(columns[0])
        // console.log(columns)
        for (i = 0; i < columns[0].length; i++) {
            totalCol += columns[0][i].colspan || 1;// 表格总列数;  
        }
        // alert('totalCol'+totalCol)
        for (i = 0; i < columns.length; i++) {// columns.length表格总行数;  
            flag[i] = [];
            for (j = 0; j < totalCol; j++) {
                flag[i][j] = false;
            }
        }
        alert(flag)
        for (i = 0; i < columns.length; i++) {
            for (j = 0; j < columns[i].length; j++) {// columns[i].length某行共有多少元素;  
                var r = columns[i][j],
                    rowspan = r.rowspan || 1,
                    colspan = r.colspan || 1,
                    // i为标题栏小矩阵在flag大矩阵的行位置;  
                    // index记录标题栏小矩阵在flag大矩阵的列位置;  
                    index = flag[i].indexOf(false);

                if (colspan === 1) {
                    // fieldIndex记录每个标题栏的列坐标信息;  
                    r.fieldIndex = index;
                    if (typeof r.field === 'undefined') {
                        r.field = index;
                    }
                }

                // 目的是让$.inArray(false, flag[i])正确获取标题栏的列坐标;  
                for (k = 0; k < rowspan; k++) {
                    flag[i + k][index] = true;
                }
                for (k = 0; k < colspan; k++) {
                    flag[i][index + k] = true;
                }
            }
        }
    };

    // 当html中包含thead>tr>th以及tbody>tr>td时，获取页面的配置项更新options.columns、options.data;  
    // js配置的优先级高于html页面配置;  
    // this.columns以this.columns[fieldIndex]的数组形式[columns]记录表体相应标题栏的数据内容;  
    BootstrapTable.prototype.initTable = function () {
        var that = this,
            columns = [],
            data = [];

        // 触发元素table中有thead子标签等则使用（查询排序的时候），无则创建  
        this.$header = this.$el.querySelector('thead');
        if (!this.$header.length) {
            this.$el.insertAdjacentHTML('beforeend', '<thead></thead>');
            this.$header = this.$el.querySelector('thead');
        }
        else {
            this.$tr = this.$header.querySelectorAll('tr')
            if (this.$tr.length) {
                this.$tr.forEach(function () {
                    var column = []; this.querySelectorAll('th').forEach(function () {
                        column.push(extend({}, {
                            title: this.innerHTM(),
                            'class': this.getAttribute('class'),
                            titleTooltip: this.getAttribute('title'),
                            rowspan: this.getAttribute('rowspan') ? +this.getAttribute('rowspan') : undefined,
                            colspan: this.getAttribute('colspan') ? +this.getAttribute('colspan') : undefined
                        }, this.data()));
                    });
                    columns.push(column);
                })
            }
        };
        if (!Array.isArray(this.options.columns[0])) {
            this.options.columns = [this.options.columns];// 都处理成两维数组的形式  
        }
        this.options.columns = extend(true, [], columns, this.options.columns);

        // 借用this.columns[fieldIndex]=column构建this.columns;  
        // this.column的数据格式为{[column]}，列坐标相同的标题栏取靠后的子标题;  
        // 意义：填充表体内容时，this.column提供每列数据的相关信息;  
        this.columns = [];

        // setFieldIndex将标题栏的fieldIndex属性赋值为标题栏所在列坐标;  
        setFieldIndex(this.options.columns);

        each(this.options.columns, function (i, columns) {
            each(columns, function (j, column) {
                column = extend({}, BootstrapTable.COLUMN_DEFAULTS, column);

                if (typeof column.fieldIndex !== 'undefined') {
                    that.columns[column.fieldIndex] = column;
                }

                that.options.columns[i][j] = column;
            });
        });

        if (this.options.data.length) {
            return;
        }

        this.$el.getElementsByTagName('tbody').forEach(function (tb) {

            tb.getElementsByTagName('tr').forEach(function () {
                var row = {};

                // 获取每一行tr的id、class、data属性，以数组形式赋值给data  
                row._id = this.getAttribute('id');
                row._class = this.getAttribute('class');
                // row._data = getRealDataAttr(this.data());

                // 获取某一行每个子元素的内容、id、class、rowspan、title、data属性  
                var $tds = this.querySelectorAll('td');
                [].forEach.call($tds, function (i) {
                    // field通常是后台数据的id号，没有该值的时候赋值为column列坐标信息，写入本地数据的时候  
                    var field = that.columns[i].field;

                    row[field] = this.innerHTML;
                    // save td's id, class and data-* attributes  
                    row['_' + field + '_id'] = this.attr('id');
                    row['_' + field + '_class'] = this.getAttribute('class');
                    row['_' + field + '_rowspan'] = this.getAttribute('rowspan');
                    row['_' + field + '_title'] = this.getAttribute('title');
                    // row['_' + field + '_data'] = getRealDataAttr(this.data());
                });
                data.push(row);
            })
        });

        this.options.data = data;
    };

    // 由options.columns渲染表头,th的data-field记为column[field],data数据记为column;  
    // 更新this.header记录主键、样式、事件、格式化函数等，以及stateField复选框上传字段;  
    // 绑定事件，包括点击排序、确认键排序、全选，更新上传数据、页面状态等；  
    BootstrapTable.prototype.initHeader = function () {
        var that = this,
            visibleColumns = {},
            html = [];

        this.header = {
            fields: [],
            styles: [],
            classes: [],
            formatters: [],
            events: [],
            sorters: [],
            sortNames: [],
            cellStyles: [],
            searchables: []
        };

        each(this.options.columns, function (i, columns) {
            html.push('<tr>');

            // 页面以表格显示且有卡片式详情点击按钮的时候，表头首列为该按钮开辟一个空白的单元格  
            if (i == 0 && !that.options.cardView && that.options.detailView) {
                html.push(sprintf('<th class="detail" rowspan="%s"><div class="fht-cell"></div></th>',
                    that.options.columns.length));
            }

            each(columns, function (j, column) {
                var text = '',
                    halign = '',
                    align = '',
                    style = '',
                    class_ = sprintf(' class="%s"', column['class']),
                    order = that.options.sortOrder || column.order,
                    unitWidth = 'px',
                    width = column.width;

                // width输入宽度有%或px时，分割%或px到unitWidth中，width保留数字字符串  
                // width输入数值时，unitWidth默认取px  
                if (column.width !== undefined && (!that.options.cardView)) {
                    if (typeof column.width === 'string') {
                        if (column.width.indexOf('%') !== -1) {
                            unitWidth = '%';
                        }
                    }
                }
                if (column.width && typeof column.width === 'string') {
                    width = column.width.replace('%', '').replace('px', '');
                }

                halign = sprintf('text-align: %s; ', column.halign ? column.halign : column.align);
                align = sprintf('text-align: %s; ', column.align);
                style = sprintf('vertical-align: %s; ', column.valign);
                style += sprintf('width: %s; ', (column.checkbox || column.radio) && !width ?
                    '36px' : (width ? width + unitWidth : undefined));

                /**  
                 * this.header.styles、this.header.classes: 
                 *     数组形式存储经过处理的每列数据的样式、类; 
                 * this.header.formatters、this.header.cellStyles、this.header.sorters: 
                 *     数组形式存储格式化函数、设置单元格样式函数、排序函数，或者window方法名; 
                 * this.header.events、this.header.sortNames、this.header.searchables: 
                 *     数组形式存储表体相应标题栏配置的事件events、上传排序的字段名sortName、可搜索searchable; 
                 */
                // 填充触发元素的tbody内容块时使用  
                if (typeof column.fieldIndex !== 'undefined') {
                    that.header.fields[column.fieldIndex] = column.field;
                    that.header.styles[column.fieldIndex] = align + style;
                    that.header.classes[column.fieldIndex] = class_;
                    that.header.formatters[column.fieldIndex] = column.formatter;
                    that.header.events[column.fieldIndex] = column.events;
                    that.header.sorters[column.fieldIndex] = column.sorter;
                    that.header.sortNames[column.fieldIndex] = column.sortName;
                    that.header.cellStyles[column.fieldIndex] = column.cellStyle;
                    that.header.searchables[column.fieldIndex] = column.searchable;

                    if (!column.visible) {
                        return;
                    }

                    if (that.options.cardView && (!column.cardVisible)) {
                        return;
                    }

                    visibleColumns[column.field] = column;
                }

                // options.columns数据回显和渲染页面  
                html.push('<th' + sprintf(' title="%s"', column.titleTooltip),
                    column.checkbox || column.radio ?
                        sprintf(' class="bs-checkbox %s"', column['class'] || '') :
                        class_,
                    sprintf(' style="%s"', halign + style),
                    sprintf(' rowspan="%s"', column.rowspan),
                    sprintf(' colspan="%s"', column.colspan),
                    sprintf(' data-field="%s"', column.field),
                    "tabindex='0'",
                    '>');

                html.push(sprintf('<div class="th-inner %s">', that.options.sortable && column.sortable ?
                    'sortable both' : ''));

                text = column.title;

                if (column.checkbox) {
                    if (!that.options.singleSelect && that.options.checkboxHeader) {
                        text = '<input name="btSelectAll" type="checkbox" />';
                    }
                    that.header.stateField = column.field;// 复选框内容上传时的字段名  
                }
                if (column.radio) {
                    text = '';
                    that.header.stateField = column.field;
                    that.options.singleSelect = true;
                }

                html.push(text);
                html.push('</div>');
                html.push('<div class="fht-cell"></div>');
                html.push('</div>');
                html.push('</th>');
            });
            html.push('</tr>');
        });

        this.$header.innerHTML = html.join('');
        console.log(this.$header);
        this.$header.getElementsByTagName(th).forEach(function (i) {
            // 标题栏data属性写入各自的column数据，展开卡片式详情时使用  
            this.getAttribute(visibleColumns[this.getAttribute('field')]);
        });

        // 绑定点击排序事件  
        this.$container.off('click', '.th-inner').on('click', '.th-inner', function (event) {
            var target = $(this);
            if (target.closest('.bootstrap-table')[0] !== that.$container[0])
                return false;

            if (that.options.sortable && target.parent().data().sortable) {
                that.onSort(event);
            }
        });

        // 确认键排序  
        this.$header.children().children().off('keypress').on('keypress', function (event) {
            if (that.options.sortable && $(this).data().sortable) {
                var code = event.keyCode || event.which;
                if (code == 13) { //Enter keycode  
                    that.onSort(event);
                }
            }
        });

        // 显示隐藏表头，调整this.$tableLoading位置;options.cardView为真时卡片式显示隐藏表头  
        if (!this.options.showHeader || this.options.cardView) {
            this.$header.hide();
            this.$tableHeader.hide();
            this.$tableLoading.css('top', 0);
        } else {
            this.$header.show();
            this.$tableHeader.show();
            this.$tableLoading.css('top', this.$header.outerHeight() + 1);

            this.getCaret();// 更新排序箭头显示情况  
        }

        // 全选  
        this.$selectAll = this.$header.find('[name="btSelectAll"]');
        this.$selectAll.off('click').on('click', function () {
            var checked = $(this).prop('checked');
            that[checked ? 'checkAll' : 'uncheckAll']();// 改变复选框勾选状态，更新上传数据  
            that.updateSelected();// tr添加selected类  
        });
    };

    var allowedMethods = [
        'getOptions',
        'getSelections', 'getAllSelections', 'getData',
        'load', 'append', 'prepend', 'remove', 'removeAll',
        'insertRow', 'updateRow', 'updateCell', 'updateByUniqueId', 'removeByUniqueId',
        'getRowByUniqueId', 'showRow', 'hideRow', 'getRowsHidden',
        'mergeCells',
        'checkAll', 'uncheckAll', 'checkInvert',
        'check', 'uncheck',
        'checkBy', 'uncheckBy',
        'refresh',
        'resetView',
        'resetWidth',
        'destroy',
        'showLoading', 'hideLoading',
        'showColumn', 'hideColumn', 'getHiddenColumns',
        'filterBy',
        'scrollTo',
        'getScrollPosition',
        'selectPage', 'prevPage', 'nextPage',
        'togglePagination',
        'toggleView',
        'refreshOptions',
        'resetSearch',
        'expandRow', 'collapseRow', 'expandAllRows', 'collapseAllRows',
        'updateFormatText'
    ];
    function parseHTML(string) {
        const context = document.implementation.createHTMLDocument();

        // Set the base href for the created document so any parsed elements with URLs
        // are based on the document's URL
        const base = context.createElement('base');
        base.href = document.location.href;
        context.head.appendChild(base);

        context.body.innerHTML = string;
        return context.body.children;
    }
    function inArray(elem, array) {
        if (Array.isArray(array)) {

            return array.includes(elem);

        }
        return false;
    }


    // function inArray(elem, arr, i) {
    //     return arr == null ? -1 : indexOf.call(arr, elem, i);
    // };
    // 通过字面量方式实现的函数each
    var each = function (object, callback) {
        var type = (function () {
            switch (object.constructor) {
                case Object:
                    return 'Object';
                    break;
                case Array:
                    return 'Array';
                    break;
                case NodeList:
                    return 'NodeList';
                    break;
                default:
                    return 'null';
                    break;
            }
        })();
        // alert("type:"+type+object)
        // 为数组或类数组时, 返回: index, value
        if (type === 'Array' || type === 'NodeList') {
            // 由于存在类数组NodeList, 所以不能直接调用every方法
            [].every.call(object, function (v, i) {
                return callback.call(v, i, v) === false ? false : true;
            });
        }
        // 为对象格式时,返回:key, value if (type === 'Object') 
        else {
            for (var i in object) {
                if (callback.call(object[i], i, object[i]) === false) {
                    break;
                }
            }
        }
    };
    // (() => {

    var fn = Element.prototype.bootstrapTable = Element.prototype.bt = function (option) {

        var value,
            args = Array.prototype.slice.call(arguments, 1);
        console.log(arguments);

        console.log(this);
        var data = this["bootstrap.table"],
            // 配置项在触发元素的data数据中，或在js的option传参中  
            options = extend({}, BootstrapTable.DEFAULTS,
                typeof option === 'object' && option);

        // console.log(options);
        // console.log(data);
        if (typeof option === 'string') {
            if (!inArray(option, allowedMethods)) {
                throw new Error("Unknown method: " + option);
            }

            if (!data) {
                return;
            }

            value = data[option].apply(data, args);

            if (option === 'destroy') {
                delete this['bootstrap.table'];
            }
        }

        if (!data) {
            this['bootstrap.table', (data = new BootstrapTable(this, options))];
        };

        return typeof value === 'undefined' ? this : value;
    };
    // })()

    // fn.bootstrapTable.Constructor = BootstrapTable;
    // fn.bootstrapTable.defaults = BootstrapTable.DEFAULTS;
    // fn.bootstrapTable.columnDefaults = BootstrapTable.COLUMN_DEFAULTS;
    // fn.bootstrapTable.locales = BootstrapTable.LOCALES;
    // fn.bootstrapTable.methods = allowedMethods;
    // fn.bootstrapTable.utils = {
    //     sprintf: sprintf,
    //     getFieldIndex: getFieldIndex,
    //     compareObjects: compareObjects,
    //     calculateObjectValue: calculateObjectValue
    // };

    // fn.bootstrapTable.prototype = MyPlugin.prototype
    // script标签引入插件后全局下挂载一个_$的方法
    // window.$ = function (el) { return new MyPlugin(el) };
    // return MyPlugin;

}))
