

(function (global, factory) {
    // alert(global)
    // 检查上下文环境是否为Nodejs环境'
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        // 检测上下文环境是否为AMD或CMD
        typeof define === 'function' && define.amd ? define(factory) :

            (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.BootstrapTable = factory());
})(this, (function () {
    'use strict';
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


    function each(object, callback, args) {

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



    //  data的原生实现
    Element.prototype.data = function (key, value) {
        var _this = this,
            _dataName = 'testData',  // 存储至DOM上的对象标记, 这里只是测试用名
            _data = {};
        // 未指定参数,返回全部
        if (typeof key === 'undefined' && typeof value === 'undefined') {
            return _this[_dataName];
        }
        // setter
        if (typeof (value) !== 'undefined') {
            // 存储值类型为字符或数字时, 使用attr执行
            var _type = typeof (value);
            if (_type === 'string' || _type === 'number') {
                _this.setAttribute(key, value);
            }
            _data = _this[_dataName] || {};
            _data[key] = value;
            _this[_dataName] = _data;
            return this;
        }
        // getter
        else {
            _data = _this[_dataName] || {};
            return _data[key] || _this.getAttribute(key);
        }
    };
    NodeList.prototype.data = function (key, value) {
        // setter
        if (typeof (value) !== 'undefined') {
            [].forEach.call(this, function (element, index) {
                element.data(key, value);
            });
            return this;
        }
        // getter
        else {
            return this[0].data(key, value); // getter 将返回第一个
        }
    };
    function isObject(obj) {
        return typeof (obj) === 'object' && obj !== null && !Array.isArray(obj);
    };

    function extend() {
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

    function inArray(elem, array, i) {
        var len, indexOf = Array.indexOf;
        if (Array.isArray(array)) {
            if (indexOf) {
                return indexOf.call(arr, elem, i);
            }
            len = arr.length;
            //alert($.inArray(5,[1,2,3,5,4],-1))这里获取到的i就是4，len就是5，返回值为-1
            i = i ? i < 0 ? Math.max(0, len + i) : i : 0;
            for (; i < len; i++) {
                // Skip accessing in sparse arrays
                //这里直接跳过稀疏数组中的空白部分，进而节约时间 
                if (i in arr && arr[i] === elem) {
                    return i;
                }
            }
        }
        return -1;




    }


    var fn = Element.prototype.bootstrapTable = Element.prototype.bt = function (option) {
        var value,
            args = Array.prototype.slice.call(arguments, 1);
        // console.log(arguments);
        // console.log(this);
        var data = this.data('bootstrap.table'),
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
                delete this.data('bootstrap.table');
            }
        }
        if (!data) {
            this.data('bootstrap.table', (data = new BootstrapTable(this, options)));
        };
        return typeof value === 'undefined' ? this : value;
    };

    var BootstrapTable = function (el, options) {
        this.options = options;
        this.$el = el;
        this.$el_ = this.$el.cloneNode(true);// 记录触发元素的初始值，destroy销毁重置的时候使用

        this.init();
    };
    BootstrapTable.DEFAULTS = {
        classes: 'table table-hover',
        height: undefined,
        undefinedText: '-',
        sortName: undefined,
        sortOrder: 'asc',
        striped: false,
        columns: [],
        data: [],
        method: 'get',
        url: undefined,
        queryParams: {},
        pagination: false,
        sidePagination: 'client', // client or server
        totalRows: 0, // server side need to set
        pageNumber: 1,
        pageSize: 10,
        pageList: [10, 20, 30, 40, 50],
        onClickRow: function (item) { return false; },
        onSort: function (name, order) { return false; },
        onCheck: function (row) { return false; },
        onUncheck: function (row) { return false; },
        onCheckAll: function (rows) { return false; },
        onUncheckAll: function (rows) { return false; }
    };
    BootstrapTable.prototype.init = function () {
        this.initContainer();
        this.initHeader();
        // this.initData();
        // this.initPagination();
        // this.initBody();
        // this.initServer();
    };

    BootstrapTable.prototype.initContainer = function () {
        // range = document.createRange();
        // parse = range.createContextualFragment.bind(range);
        // this.$cont= parse ( [
        // '<div class="fixed-table-container">',
        // '<div class="fixed-table-header"></div>',
        // '<div class="fixed-table-body"></div>',
        // '<div class="fixed-table-pagination"></div>', '</div > '
        // ].join(''));
        this.$container = document.createElement('div');
        this.$container.insertAdjacentHTML('afterbegin', [
            '<div class="fixed-table-container">',
            '<div class="fixed-table-header"></div>',
            '<div class="fixed-table-body"></div>',
            '<div class="fixed-table-pagination"></div>', '</div > '
        ].join(''))

        // this.$container.innerHTML = [
        // '<div class="fixed-table-container">',
        // '<div class="fixed-table-header"></div>',
        // '<div class="fixed-table-body"></div>',
        // '<div class="fixed-table-pagination"></div>', '</div > '
        // ].join('');

        // console.log(this.$el.className);

        this.$el.className = this.options.classes;

        if (this.options.striped) {
            this.$el.classList.add('table-striped');
        }

        // this.$container.querySelector('.fixed-table-body').appendChild(this.$el);


        alert(this.$container.innerHTML)

        this.$container.querySelector('.fixed-table-container').insertAdjacentHTML('afterend', '<div class="clearfix"></div>');
        if (this.options.height) {
            this.$container.style.height = this.options.height + 'px';
        }




        this.$el.insertAdjacentHTML('afterend', this.$container);
        // this.$el.parentNode.replaceChild(this.$container, this.$el);
        console.log(this.$container.innerHTML);
    };


    BootstrapTable.prototype.initHeader = function () {
        var that = this,
            columns = [],
            html = [];
        this.$header = this.$el.querySelector('thead');
        if (this.$header === null) {
            this.$header = document.createEvent('thead')
            this.$el.appendchild(this.$header);
        }
        if (this.$header.querySelector('tr') === null) {
            this.$header.append(document.createElement('tr'));
        }
        this.$header.querySelectorall('th').forEach(element => {
            var column = extend({}, {
                title: this.innertext
            }, this.data());
            columns.push(column);

        });
        this.options.columns = extend(columns, this.options.columns);
        this.header = {
            fields: [],
            styles: [],
            formatters: [],
            sorters: []
        };
        each(this.options.columns, function (i, column) {
            var text = '',
                style = sprintf('text-align: %s; ', column.align) + sprintf('vertical-align: %s; ', column.valign),
                order = that.options.sortOrder || column.order || 'asc';
            that.header.fields.push(column.field);
            that.header.styles.push(style);
            that.header.formatters.push(column.formatter);
            that.header.sorters.push(column.sorter);
            style = sprintf('width: %spx; ', column.checkbox || column.radio ? 36 : column.width);
            style += column.sortable ? 'cursor: pointer; ' : '';
            html.push('<th' + sprintf(' style="%s"', style) + '>');
            html.push('<div class="th-inner">');
            text = column.title;
            if (that.options.sortName === column.field && column.sortable) {
                text += that.getCaretHtml();
            }
            if (column.checkbox) {
                text = '<input name="btSelectAll" type="checkbox" class="checkbox" />';
                that.header.stateField = column.field;
            }
            if (column.radio) {
                text = '';
                that.header.stateField = column.field;
            }
            html.push(text);
            html.push('</div>');
            html.push('</th>');
        });
        this.$header.querySelectorall('tr').forEach(function (i) { i.innerHTML = html.join('') });
        this.$header.querySelectorall('th').forEach(function (i) {
            this.data(columns[i]);
            if (columns[i].sortable) {
                // this.onclick = function () { new proxy(that, {}).onSort };
                this.onclick = function () { that.onSort.bind(that) };
            }
        });
        this.$selectAll = this.$header.find('[name="btSelectAll"]');
        this.$selectAll.onclick = null;
        this.$selectAll.addEventListener('click', function () {
            var checked = this['checked'];
            that[checked ? 'checkAll' : 'uncheckAll']();
        });
    };

    BootstrapTable.prototype.initData = function (data, append) {
        if (append) {
            this.data = this.data.concat(data);
        } else {
            this.data = data || this.options.data;
        }
        this.initSort();
    };

    BootstrapTable.prototype.initSort = function () {
        var name = this.options.sortName,
            order = this.options.sortOrder === 'desc' ? -1 : 1,
            index = inArray(this.options.sortName, this.header.fields);
        if (index !== -1) {
            var sorter = this.header.sorters[index];
            this.data.sort(function (a, b) {
                if (typeof sorter === 'function') {
                    return order * sorter(a[name], b[name]);
                }
                if (a[name] === b[name]) {
                    return 0;
                }
                if (a[name] < b[name]) {
                    return order * -1;
                }
                return order;
            });
        }
    };

    BootstrapTable.prototype.onSort = function (event) {
        var $this = event.currentTarget;
        this.$header.querySelector('span.order').remove();
        this.options.sortName = $this.data('field');
        this.options.sortOrder = $this.data('order') === 'asc' ? 'desc' : 'asc';
        this.options.onSort(this.options.sortName, this.options.sortOrder);
        $this.data('order', this.options.sortOrder);
        $this.querySelector('.th-inner').append(this.getCaretHtml());
        this.initSort();
        this.initBody();
    };

    BootstrapTable.prototype.initPagination = function () {
        if (!this.options.pagination) {
            return;
        }
        this.$pagination = this.$container.querySelector('.fixed-table-pagination');
        if (this.options.sidePagination === 'client') {
            this.options.totalRows = this.data.length;
        }
        this.updatePagination();
    };

    BootstrapTable.prototype.updatePagination = function () {
        var that = this,
            html = [],
            i, from, to,
            $pageList,
            $first, $pre,
            $next, $last,
            $number;
        this.totalPages = 0;
        if (this.options.totalRows) {
            this.totalPages = ~~((this.options.totalRows - 1) / this.options.pageSize) + 1;
        }
        if (this.totalPages > 0 && this.options.pageNumber > this.totalPages) {
            this.options.pageNumber = this.totalPages;
        }
        this.pageFrom = (this.options.pageNumber - 1) * this.options.pageSize + 1;
        this.pageTo = this.options.pageNumber * this.options.pageSize;
        if (this.pageTo > this.options.totalRows) {
            this.pageTo = this.options.totalRows;
        }
        html.push(
            '<div class="pull-left pagination">',
            '<div class="pagination-info">',
            sprintf('Showing %s to %s of %s rows', this.pageFrom, this.pageTo, this.options.totalRows),
            '</div>',
            '</div>',
            '<div class="pull-right">',
            '<ul class="pagination">',
            '<li class="page-first"><a href="javascript:void(0)">&lt;&lt;</a></li>',
            '<li class="page-pre"><a href="javascript:void(0)">&lt;</a></li>');
        if (this.totalPages < 5) {
            from = 1;
            to = this.totalPages;
        } else {
            from = this.options.pageNumber - 2;
            to = from + 4;
            if (from < 1) {
                from = 1;
                to = 5;
            }
            if (to > this.totalPages) {
                to = this.totalPages;
                from = to - 4;
            }
        }
        for (i = from; i <= to; i++) {
            html.push('<li class="page-number' + (i === this.options.pageNumber ? ' active' : '') + '">',
                '<a href="javascript:void(0)">', i, '</a>',
                '</li>');
        }
        html.push(
            '<li class="page-next"><a href="javascript:void(0)">&gt;</a></li>',
            '<li class="page-last"><a href="javascript:void(0)">&gt;&gt;</a></li>',
            '</ul>',
            '</div>');
        html.push(
            '<div class="pagination btn-group dropup page-list">',
            '<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">',
            this.options.pageSize,
            ' <span class="caret"></span>',
            '</button>',
            '<ul class="dropdown-menu" role="menu">');
        $.each(this.options.pageList, function (i, page) {
            var active = page === that.options.pageSize ? ' class="active"' : '';
            html.push(sprintf('<li%s><a href="javascript:void(0)">%s</a></li>', active, page));
        });
        html.push(
            '</ul>',
            '</div>');
        this.$pagination.innerHTML = html.join('');
        $pageList = this.$pagination.querySelector('.page-list a');
        $first = this.$pagination.querySelector('.page-first');
        $pre = this.$pagination.querySelector('.page-pre');
        $next = this.$pagination.querySelector('.page-next');
        $last = this.$pagination.querySelector('.page-last');
        $number = this.$pagination.querySelector('.page-number');
        if (this.options.pageNumber <= 1) {
            $first.classList.add('disabled');
            $pre.classList.add('disabled');
        }
        if (this.options.pageNumber >= this.totalPages) {
            $next.classList.add('disabled');
            $last.classList.add('disabled');
        }
        $pageList.removeEventListener('click').addEventListener('click', this.onPageListChange.bind(this));
        $first.removeEventListener('click').addEventListener('click', this.onPageFirst.bind(this));
        $pre.removeEventListener('click').addEventListener('click', this.onPagePre.bind(this));
        $next.removeEventListener('click').addEventListener('click', this.onPageNext.bind(this));
        $last.removeEventListener('click').addEventListener('click', this.onPageLast.bind(this));
        $number.removeEventListener('click').addEventListener('click', this.onPageNumber.bind(this));
    };

    BootstrapTable.prototype.onPageListChange = function (event) {
        this.options.pageSize = +$(event.currentTarget).text();
        this.updatePagination();
        this.initBody();
    };

    BootstrapTable.prototype.onPageFirst = function () {
        this.options.pageNumber = 1;
        this.updatePagination();
        this.initBody();
    };

    BootstrapTable.prototype.onPagePre = function () {
        this.options.pageNumber--;
        this.updatePagination();
        this.initBody();
    };

    BootstrapTable.prototype.onPageNext = function () {
        this.options.pageNumber++;
        this.updatePagination();
        this.initBody();
    };


    BootstrapTable.prototype.onPageLast = function () {
        this.options.pageNumber = this.totalPages;
        this.updatePagination();
        this.initBody();
    };

    BootstrapTable.prototype.onPageNumber = function (event) {
        this.options.pageNumber = +$(event.currentTarget).text();
        this.updatePagination();
        this.initBody();
    };

    BootstrapTable.prototype.initBody = function () {
        var that = this,
            html = [];
        this.$body = this.$el.find('tbody');
        if (!this.$body.length) {
            this.$body = $('<tbody></tbody>').appendTo(this.$el);
        }
        if (!this.options.pagination) {
            this.pageFrom = 1;
            this.pageTo = this.data.length;
        }
        for (var i = this.pageFrom - 1; i < this.pageTo; i++) {
            var item = this.data[i];
            html.push('<tr' + ' data-index="' + i + '">');
            $.each(that.header.fields, function (j, field) {
                var text = '',
                    value = item[field],
                    type = '';
                if (typeof that.header.formatters[j] === 'function') {
                    value = that.header.formatters[j](value, item);
                }
                text = ['<td' + sprintf(' style="%s"', that.header.styles[j]) + '>',
                typeof value === 'undefined' ? that.options.undefinedText : value,
                    '</td>'].join('');
                if (that.options.columns[j].checkbox || that.options.columns[j].radio) {
                    type = that.options.columns[j].checkbox ? 'checkbox' : type;
                    type = that.options.columns[j].radio ? 'radio' : type;
                    text = ['<td>',
                        '<input name="btSelectItem" class="checkbox" data-index="' + i + '"' +
                        sprintf(' type="%s"', type) +
                        sprintf(' checked="%s"', value ? 'checked' : undefined) + ' />',
                        '</td>'].join('');
                }
                html.push(text);
            });
            html.push('</tr>');
        }
        this.$body.html(html.join(''));
        this.$body.find('tr').off('click').on('click', function () {
            that.options.onClickRow(that.data[$(this).data('index')]);
        });
        this.$selectItem = this.$body.find('[name="btSelectItem"]');
        this.$selectItem.off('click').on('click', function () {
            var checkAll = that.data.length === that.$selectItem.filter(':checked').length;
            that.$selectAll.prop('checked', checkAll);
            that.data[$(this).data('index')][that.header.stateField] = $(this).prop('checked');
        });
        this.resetView();
    };

    BootstrapTable.prototype.initServer = function () {
        var that = this;
        if (!this.options.url) {
            return;
        }
        $.ajax({
            type: this.options.method,
            url: this.options.url,
            data: this.options.queryParams,
            contentType: 'application/json',
            dataType: 'json',
            success: function (data) {
                that.load(data);
            }
        });
    };

    BootstrapTable.prototype.getCaretHtml = function () {
        return ['<span class="order' + (this.options.sortOrder === 'desc' ? '' : ' dropup') + '">',
            '<span class="caret" style="margin: 10px 5px;"></span>',
            '</span>'].join('');
    };

    BootstrapTable.prototype.resetView = function () {
        var header = this.header;

        this.$header.find('.th-inner').each(function (i) {
            $(this).attr('style', header.styles[i])
                .css('width', ($(this).parent().width()) + 'px'); // padding: 8px
        });
    };

    BootstrapTable.prototype.updateRows = function (checked) {
        var that = this;
        $.each(this.data, function (i, row) {
            row[that.header.stateField] = checked;
        });
    };

    // PUBLIC FUNCTION DEFINITION
    // =======================
    BootstrapTable.prototype.load = function (data) {
        this.initData(data);
        this.initPagination();
        this.initBody();
    };

    BootstrapTable.prototype.append = function (data) {
        this.initData(data, true);
        this.initBody();
    };

    BootstrapTable.prototype.mergeCells = function (options) {
        var row = options.index,
            col = $.inArray(options.field, this.header.fields),
            rowspan = options.rowspan || 1,
            colspan = options.colspan || 1,
            i, j,
            $tr = this.$body.find('tr'),
            $td = $tr.eq(row).find('td').eq(col);
        if (row < 0 || col < 0 || row >= this.data.length) {
            return;
        }
        for (i = row; i < row + rowspan; i++) {
            for (j = col; j < col + colspan; j++) {
                $tr.eq(i).find('td').eq(j).hide();
            }
        }
        $td.attr('rowspan', rowspan).attr('colspan', colspan).show();
    };
    BootstrapTable.prototype.getSelections = function () {
        var that = this;
        return $.grep(this.data, function (row) {
            return row[that.header.stateField];
        });

    };
    BootstrapTable.prototype.checkAll = function () {
        this.$selectAll.prop('checked', true);
        this.$selectItem.prop('checked', true);
        this.updateRows(true);
    };
    BootstrapTable.prototype.uncheckAll = function () {
        this.$selectAll.prop('checked', false);
        this.$selectItem.prop('checked', false);
        this.updateRows(false);
    };
    BootstrapTable.prototype.destroy = function () {
        this.$container.replaceWith(this.$el_);
        return this.$el_;
    };


    $.fn.bootstrapTable.Constructor = BootstrapTable;

    // BOOTSTRAP TABLE INIT
    // =======================

    $(function () {
        $('[data-toggle="table"]').bootstrapTable();
    });

}))