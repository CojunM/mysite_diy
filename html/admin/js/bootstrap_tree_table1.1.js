;//防止多文件集成成一个文件后，高压缩出现语法错误。
(function (global, factory) {
    // alert(global)
    // 检查上下文环境是否为Nodejs环境'
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        // 检测上下文环境是否为AMD或CMD
        typeof define === 'function' && define.amd ? define(factory) :

            (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.bootstrapTable = factory());
})(this, (function () {
    'use strict';
    let $Event = {
        _events: new WeakMap(), // 使用WeakMap存储事件与元素的映射关系，利于垃圾回收
        /**
         * 绑定代理事件
         * ========================================================================
         * @param {HTMLElement} el - 绑定代理事件的 DOM 节点
         * @param {String} selector - 触发 el 代理事件的 DOM 节点的选择器
         * @param {String} types - 事件类型
         * @param {Function} callback - 绑定事件的回调函数
         * @param {Object} [context] - callback 回调函数的 this 上下文（默认值：el）
         * @param {Boolean} [capture] - 是否采用事件捕获（默认值：false - 事件冒泡）
         * @param {Boolean} [once] - 是否只触发一次（默认值：false - 事件冒泡）
         */
        on(el, types, selector, context, callback, capture, /* private */ once) {
            let type
            //如果第一个types的对象是object类型，见代码1
            if (typeof types === "object") {
                // ( types-Object, selector, data )
                //如果第二个参数不是string，那么调用方式就是$("p").on(typeObject,dataObject)
                //也就是第一个参数是type对象，第二个参数是数据对象
                if (typeof selector !== "string") {
                    context = context || selector;
                    selector = undefined;
                }
                //获取types封装的每一个type对象
                for (type in types) {
                    //继续逐个绑定到选择器选择的对象上面去。也就是虽然事件类型是一个object对象，但是还
                    //type是"mouseenter",但是types[type]就是function对象
                    let fn = types[type]
                    if (!fn._flag) fn._flag = selector + Math.random().toString(36).substring(2, 8);
                    $Event.on(el, type, selector, context, fn, capture, once);
                }
                return el;
            }
            //如果第一个参数不是object类型，同时第三个和第四个参数data和fn同时是null,因为undefined==nu
            // 这个if语句的调用逻辑是: $("p").on("click", function () { })也就是只有两个参数，这种调用方式第二个参数是f
            // 第一个是types，data和selector是undefined。on: function(types, selector, data, fn, /*INTERNAL*/ one
            if (context == null && callback == null) {
                // ( types, fn )
                //把selector赋值给fn,记住韦恩图的逻辑!
                callback = selector;
                context = selector = undefined;
            } else if (callback == null) {
                //仅仅fn为null，data不是null,function( types, selector, data, fn, /*INTERNAL*/ one )
                if (typeof selector === "string") {
                    // ( types, selector, fn )
                    callback = context;
                    context = undefined;
                } else {
                    // ( types, data, fn )
                    callback = context;
                    context = selector;
                    selector = undefined;
                }
            }
            //如果第四个参数是false,那么就把事件触发时候的回调函数设为returnFalse函数!
            if (callback === false) {
                callback = () => { return false; };
            } else if (!callback) {
                return el;
            }
            callback._flag = callback._flag = selector + Math.random().toString(36).substr(2, 8);
            // Ensure that invalid selectors throw exceptions at attach time
            // Evaluate against documentElement in case elem is a non-element node (e.g., document)
            if (selector) {
                let fn = callback;
                callback = function (e) {
                    //  验证子选择器所匹配的nodeList中是否包含当前事件源 或 事件源的父级
                    // 注意: 这个方法为包装函数,此处的this为触发事件的Elemen  t
                    var target = e.target;
                    while (target !== el) {
                        if ([].indexOf.call(el.querySelectorAll(selector), target) !== -1) {
                            fn.apply(target, arguments);
                            break;
                        }
                        target = target.parentNode;
                    };
                }
                callback._flag = fn._flag
            }
            //如果传入了最后一个参数，同时设置为1，在下面的one（）函数中会被调用
            if (once === true) {
                //保存原来的传递过来的事件函数
                //把one调用的函数作为局部变量保存下来
                let fn = callback;
                //对传进来的fn重新赋值，这个函数是一个全新的函数，这个函数首先移除相应的事件，移除以后
                //一次
                callback = function (event) {
                    // Can use an empty set, since event contains the info
                    $Event.off(el, types, selector, callback);
                    return fn.apply(context || el, arguments);
                };
                callback._flag = fn._flag
            }

            if (type === 'mouseenter' || type === 'mouseleave') {
                capture = true
            }


            // Only attach events to objects that accept data
            // if (!acceptData(el)) {
            // return;
            // }
            //jQuery.event.add传入参数，第一个参数是遍历出来的jQuery对象转化成的DOM对象，即$("p")[i]
            //第二个参数是类型，第三个参数回调函数，第四个参数是传递的额外数据，最后一个是选择器

            // if (typeof el === '') {
            // el.forEach(function (item) {
            // Delegate.addEvent(item, types, callback, context, selector, capture || false)
            // })}
            //    else  {
            $Event.addEvent(el, types, callback, context, selector, capture || false)
            return el
            //    }              ;
        },
        /**
         * 绑定只触发一次的事件
         * ========================================================================
         * @param {HTMLElement} el - 绑定代理事件的 DOM 节点
         * @param {String} selector - 触发 el 代理事件的 DOM 节点的选择器
         * @param {String} type - 事件类型
         * @param {Function} callback - 绑定事件的回调函数
         * @param {Object} [context] - callback 回调函数的 this 上下文（默认值：el）
         * @param {Boolean} [capture] - 是否采用事件捕获（默认值：false - 事件冒泡）
         */
        once(el, type, selector, context, callback, capture) {
            $Event.on(el, type, selector, context, callback, capture, true);
        },
        /**
         * 取消事件绑定
         * ========================================================================
         * @param {HTMLElement} el - 取消绑定（代理）事件的 DOM 节点
         * @param {String} type - 事件类型
         * @param {Function} callback - 绑定事件的回调函数
         * @param {Boolean} [capture] - 是否采用事件捕获（默认值：false - 事件冒泡）
         */
        off(el, types, selector, fn) {
            //如果types存在，同时types有preventDefault和handleObj对象
            //很显然这样的off方法是用于内部调用的!
            if (typeof types === "object") {
                // ( types-object [, selector] )
                for (let type in types) {
                    //那么对每一个调用对象单独移除事件!
                    $Event.off(el, type, selector, types[type]);
                }
                return el;
            }
            //如果selector是false或者是函数，那么调用就是off(types,fn)
            if (selector === false || typeof selector === "function") {
                // ( types [, fn] )
                fn = selector;
                selector = undefined;
            }
            //如果函数是fn===false那么移除的函数就是returnFalse函数!
            if (fn === false) {
                fn = false;
            }
            $Event.removeEvent(el, types, fn, selector);
            return el;
        },
        /**
         * 为一个元素添加一个或多个事件监听器。
         * 
         * @param {HTMLElement} el - 需要添加事件监听器的元素。
         * @param {String} types - 一个或多个以空格分隔的事件类型，例如 'click keydown'.
         * @param {Function} callback - 事件被触发时执行的回调函数。
         * @param {Object} [context=this] - 回调函数执行时的上下文对象，默认为当前函数作用域。
         * @param {String} [selector] - 一个CSS选择器，用于筛选出事件冒泡过程中的目标元素。
         * @param {Boolean} [capture=false] - 指定事件是否在捕获或冒泡阶段执行，默认为冒泡阶段。
         */
        addEvent(el, types, callback, context, selector, capture) {
            // Only attach events to objects that accept data
            if (!$Event.acceptData(el) || !types || !callback) return;
            // Define a cache object for the element's events if it doesn't exist
            let handlers = $Event._events.get(el) || {};
            // 处理多事件绑定
            types.split(' ').filter((item) => {
                return item !== null && item !== "";
            }).forEach(type => {
                handlers[type] = handlers[type] || [];
                // 添加事件处理信息到WeakMap
                handlers[type].push({
                    selector: selector,
                    callback: callback,
                    context: context,
                    capture: capture
                });

                $Event._events.set(el, handlers);
                el.addEventListener(type, callback, capture);
            });
        },
        /**
 * 移除指定元素的事件监听器。
 * 
 * @param {HTMLElement} el - 要移除事件监听器的元素。
 * @param {String} types - 以空格分隔的多个事件类型字符串。
 * @param {Function} callback - 事件被触发时执行的回调函数。
 * @param {String} [selector] - 一个CSS选择器，用于选择事件委托的目标。
 */
        removeEvent(el, types, callback, selector) {
            let handlers = $Event._events.get(el);
            if (!handlers) return;
            if (!types) {
                //type是空，那么直接移除所有的事件!
                Object.entries(handlers).forEach(([k, v]) => {
                    v.forEach((item) => {
                        el.removeEventListener(k, item.callback, item.capture)

                    })
                    $Event._events.delete(el);
                });
            }
            else {
                types.split(' ').filter((item) => {
                    return item !== null && item !== "";
                }).forEach(type => {
                    if (handlers[type]) {
                        let handleObj = handlers[type]
                        if (!callback) {
                            handleObj.forEach(item => {
                                el.removeEventListener(type, item.callback, item.capture)
                            })
                            delete handlers[type];
                        }
                        else {
                            //如果传入了handler，那么就移除对应的事件!
                            handleObj.forEach((item, index) => {
                                //判断当前遍历到的方法和传入的方法是否相同
                                if ((item.callback._flag === callback._flag) &&
                                    (!selector || selector === item.selector || selector === "**" && item.selector)) {
                                    //移除对应的事件
                                    el.removeEventListener(type, item.callback, item.capture)
                                    //删除对应的事件对象
                                    delete handlers[type].splice(index, 1);
                                }
                            })

                        }
                    }
                })
            }
        },
        /**
 * 触发指定DOM元素上的事件。
 * @param {Element} elem - 需要触发事件的DOM元素。
 * @param {string} eventName - 需要触发的事件名称。
 * @param {*} data - 与事件一起传递的数据。
 * @returns {boolean} - 如果事件被成功触发，则返回true；否则返回false。
 */
        trigger(elem, eventName, data) {
            let _event;
            if (data) { _event = new CustomEvent(eventName, { detail: data }); }
            else { _event = new Event(eventName); }
            // 触发事件
            return elem.dispatchEvent(_event);
        },
        /**
 * 停止事件（阻止默认行为和阻止事件的捕获或冒泡）
 * ========================================================================
 * @param {Event} evt - 事件对象
 */
        stop(evt) {
            $Event.stopPropagation(evt)
            $Event.preventDefault(evt)
        },
        /**
         * 终止事件在传播过程的捕获或冒泡
         * ========================================================================
         * @param {Event} evt - 事件对象
         */
        stopPropagation(evt) {
            let event = window.event
            if (evt.stopPropagation) {
                evt.stopPropagation()
            } else {
                event.cancelBubble = true
            }
        },
        /**
         * 阻止事件的默认行为
         * ========================================================================
         * @param {Event} evt - 事件对象
         */
        preventDefault(evt) {
            let event = window.event
            if (evt.preventDefault) {
                evt.preventDefault()
            } else {
                event.returnValue = false
            }
        },

        acceptData(owner) {
            // Accepts only:
            //  - Node
            //    - Node.ELEMENT_NODE
            //    - Node.DOCUMENT_NODE
            //  - Object
            //    - Any
            //!(+owner.nodeType)对于非 Node 类型的对象，
            //    通过逻辑表达式 !(+owner.nodeType) 进行判断。
            //    这里将 owner.nodeType 转换为数值（+owner.nodeType），
            //    然后取反。由于非 Node 类型的 owner 其 nodeType 
            //    属性通常不存在或非数值，转换后可能为 NaN 或非零数值，
            //    取反后结果为真（即接受此类对象）。
            return !!owner && (owner.nodeType === 1 || owner.nodeType === 9 || !(+owner.nodeType));
        },
    }

    //    工具函数
    var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {
        return typeof obj;
    } : function (obj) {
        return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
    };
    var _slicedToArray = function () {
        function sliceIterator(arr, i) {
            var _arr = [];
            var _n = true;
            var _d = false;
            var _e = undefined;

            try {
                for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) {
                    _arr.push(_s.value);

                    if (i && _arr.length === i) break;
                }
            } catch (err) {
                _d = true;
                _e = err;
            } finally {
                try {
                    if (!_n && _i["return"]) _i["return"]();
                } finally {
                    if (_d) throw _e;
                }
            }

            return _arr;
        }

        return function (arr, i) {
            if (Array.isArray(arr)) {
                return arr;
            } else if (Symbol.iterator in Object(arr)) {
                return sliceIterator(arr, i);
            } else {
                throw new TypeError("Invalid attempt to destructure non-iterable instance");
            }
        };
    }();
    // var bootstrapVersion = getBootstrapVersion();
    var CONSTANTS = {
        3: {
            classes: {
                buttonsPrefix: 'btn',
                buttons: 'default',
                buttonsGroup: 'btn-group',
                buttonsDropdown: 'btn-group',
                pull: 'pull',
                inputGroup: 'input-group',
                inputPrefix: 'input-',
                input: 'form-control',
                select: 'form-control',
                paginationDropdown: 'btn-group dropdown',
                dropup: 'dropup',
                dropdownActive: 'active',
                paginationActive: 'active',
                buttonActive: 'active'
            },
            html: {
                toolbarDropdown: ['<ul class="dropdown-menu" role="menu">', '</ul>'],
                toolbarDropdownItem: '<li class="dropdown-item-marker" role="menuitem"><label>%s</label></li>',
                toolbarDropdownSeparator: '<li class="divider"></li>',
                pageDropdown: ['<ul class="dropdown-menu" role="menu">', '</ul>'],
                pageDropdownItem: '<li role="menuitem" class="%s"><a href="#">%s</a></li>',
                dropdownCaret: '<span class="caret"></span>',
                pagination: ['<ul class="pagination%s">', '</ul>'],
                paginationItem: '<li class="page-item%s"><a class="page-link" aria-label="%s" href="javascript:void(0)">%s</a></li>',
                icon: '<i class="%s %s"></i>',
                inputGroup: '<div class="input-group">%s<span class="input-group-btn">%s</span></div>',
                searchInput: '<input class="%s%s" type="text" placeholder="%s">',
                searchButton: '<button class="%s" type="button" name="search" title="%s">%s %s</button>',
                searchClearButton: '<button class="%s" type="button" name="clearSearch" title="%s">%s %s</button>'
            }
        },
        4: {
            classes: {
                buttonsPrefix: 'btn',
                buttons: 'secondary',
                buttonsGroup: 'btn-group',
                buttonsDropdown: 'btn-group',
                pull: 'float',
                inputGroup: 'btn-group',
                inputPrefix: 'form-control-',
                input: 'form-control',
                select: 'form-control',
                paginationDropdown: 'btn-group dropdown',
                dropup: 'dropup',
                dropdownActive: 'active',
                paginationActive: 'active',
                buttonActive: 'active'
            },
            html: {
                toolbarDropdown: ['<div class="dropdown-menu dropdown-menu-right">', '</div>'],
                toolbarDropdownItem: '<label class="dropdown-item dropdown-item-marker">%s</label>',
                pageDropdown: ['<div class="dropdown-menu">', '</div>'],
                pageDropdownItem: '<a class="dropdown-item %s" href="#">%s</a>',
                toolbarDropdownSeparator: '<div class="dropdown-divider"></div>',
                dropdownCaret: '<span class="caret"></span>',
                pagination: ['<ul class="pagination%s">', '</ul>'],
                paginationItem: '<li class="page-item%s"><a class="page-link" aria-label="%s" href="javascript:void(0)">%s</a></li>',
                icon: '<i class="%s %s"></i>',
                inputGroup: '<div class="input-group">%s<div class="input-group-append">%s</div></div>',
                searchInput: '<input class="%s%s" type="text" placeholder="%s">',
                searchButton: '<button class="%s" type="button" name="search" title="%s">%s %s</button>',
                searchClearButton: '<button class="%s" type="button" name="clearSearch" title="%s">%s %s</button>'
            }
        },
        5: {
            classes: {
                buttonsPrefix: 'btn',
                buttons: 'secondary',
                buttonsGroup: 'btn-group',
                buttonsDropdown: 'btn-group',
                pull: 'float',
                inputGroup: 'btn-group',
                inputPrefix: 'form-control-',
                input: 'form-control',
                select: 'form-select',
                paginationDropdown: 'btn-group dropdown',
                dropup: 'dropup',
                dropdownActive: 'active',
                paginationActive: 'active',
                buttonActive: 'active'
            },
            icons: {
                paginationSwitchDown: 'fa-caret-square-down',
                paginationSwitchUp: 'fa-caret-square-up',
                refresh: 'fa-sync',
                toggleOff: 'fa-toggle-off',
                toggleOn: 'fa-toggle-on',
                columns: 'fa-th-list',
                detailOpen: 'fa-plus',
                detailClose: 'fa-minus',
                fullscreen: 'fa-arrows-alt'
            },
            html: {
                dataToggle: 'data-bs-toggle',
                toolbarDropdown: ['<div class="dropdown-menu dropdown-menu-end">', '</div>'],
                toolbarDropdownItem: '<label class="dropdown-item dropdown-item-marker">%s</label>',
                pageDropdown: ['<div class="dropdown-menu">', '</div>'],
                pageDropdownItem: '<a class="dropdown-item %s" href="#">%s</a>',
                toolbarDropdownSeparator: '<div class="dropdown-divider"></div>',
                dropdownCaret: '<span class="caret"></span>',
                pagination: ['<ul class="pagination%s">', '</ul>'],
                paginationItem: '<li class="page-item%s"><a class="page-link" aria-label="%s" href="javascript:void(0)">%s</a></li>',
                icon: '<i class="%s %s"></i>',
                inputGroup: '<div class="input-group">%s%s</div>',
                searchInput: '<input class="%s%s" type="text" placeholder="%s">',
                searchButton: '<button class="%s" type="button" name="search" title="%s">%s %s</button>',
                searchClearButton: '<button class="%s" type="button" name="clearSearch" title="%s">%s %s</button>'
            }
        }
    }[5];
    function _toConsumableArray(arr) {
        if (Array.isArray(arr)) {
            for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) {
                arr2[i] = arr[i];
            }

            return arr2;
        } else {
            return Array.from(arr);
        }
    }

    let Utils = {

        getIconsPrefix: function getIconsPrefix(theme) {
            return {
                bootstrap3: 'glyphicon',
                bootstrap4: 'fa',
                bootstrap5: 'bi',
                'bootstrap-table': 'icon',
                bulma: 'fa',
                foundation: 'fa',
                materialize: 'material-icons',
                semantic: 'fa'
            }[theme] || 'fa';
        },
        getIcons: function getIcons(prefix) {
            return {
                glyphicon: {
                    paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down',
                    paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up',
                    refresh: 'glyphicon-refresh icon-refresh',
                    toggleOff: 'glyphicon-list-alt icon-list-alt',
                    toggleOn: 'glyphicon-list-alt icon-list-alt',
                    columns: 'glyphicon-th icon-th',
                    detailOpen: 'glyphicon-plus icon-plus',
                    detailClose: 'glyphicon-minus icon-minus',
                    fullscreen: 'glyphicon-fullscreen',
                    search: 'glyphicon-search',
                    clearSearch: 'glyphicon-trash'
                },
                fa: {
                    paginationSwitchDown: 'fa-caret-square-down',
                    paginationSwitchUp: 'fa-caret-square-up',
                    refresh: 'fa-sync',
                    toggleOff: 'fa-toggle-off',
                    toggleOn: 'fa-toggle-on',
                    columns: 'fa-th-list',
                    detailOpen: 'fa-plus',
                    detailClose: 'fa-minus',
                    fullscreen: 'fa-arrows-alt',
                    search: 'fa-search',
                    clearSearch: 'fa-trash'
                },
                bi: {
                    paginationSwitchDown: 'bi-caret-down-square',
                    paginationSwitchUp: 'bi-caret-up-square',
                    refresh: 'bi-arrow-clockwise',
                    toggleOff: 'bi-toggle-off',
                    toggleOn: 'bi-toggle-on',
                    columns: 'bi-list-ul',
                    detailOpen: 'bi-plus',
                    detailClose: 'bi-dash',
                    fullscreen: 'bi-arrows-move',
                    search: 'bi-search',
                    clearSearch: 'bi-trash'
                },
                icon: {
                    paginationSwitchDown: 'icon-arrow-up-circle',
                    paginationSwitchUp: 'icon-arrow-down-circle',
                    refresh: 'icon-refresh-cw',
                    toggleOff: 'icon-toggle-right',
                    toggleOn: 'icon-toggle-right',
                    columns: 'icon-list',
                    detailOpen: 'icon-plus',
                    detailClose: 'icon-minus',
                    fullscreen: 'icon-maximize',
                    search: 'icon-search',
                    clearSearch: 'icon-trash-2'
                },
                'material-icons': {
                    paginationSwitchDown: 'grid_on',
                    paginationSwitchUp: 'grid_off',
                    refresh: 'refresh',
                    toggleOff: 'tablet',
                    toggleOn: 'tablet_android',
                    columns: 'view_list',
                    detailOpen: 'add',
                    detailClose: 'remove',
                    fullscreen: 'fullscreen',
                    sort: 'sort',
                    search: 'search',
                    clearSearch: 'delete'
                }
            }[prefix] || {};
        },

        //比较对象
        compareObjects: function compareObjects(objectA, objectB, compareLength) {
            var aKeys = Object.keys(objectA);
            var bKeys = Object.keys(objectB);

            if (compareLength && aKeys.length !== bKeys.length) {
                return false;
            }

            var _iteratorNormalCompletion5 = true;
            var _didIteratorError5 = false;
            var _iteratorError5 = undefined;

            try {
                for (var _iterator5 = aKeys[Symbol.iterator](), _step5; !(_iteratorNormalCompletion5 = (_step5 = _iterator5.next()).done); _iteratorNormalCompletion5 = true) {
                    var key = _step5.value;

                    if (bKeys.includes(key) && objectA[key] !== objectB[key]) {
                        return false;
                    }
                }
            } catch (err) {
                _didIteratorError5 = true;
                _iteratorError5 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion5 && _iterator5.return) {
                        _iterator5.return();
                    }
                } finally {
                    if (_didIteratorError5) {
                        throw _iteratorError5;
                    }
                }
            }

            return true;
        },
        trigger: function (elem, eventName, data) {
            let _event;
            if (data) { _event = new CustomEvent(eventName, data); }
            else { _event = new Event(eventName); }
            elem.dispatchEvent(_event);
        },
        $: {
            // 动态生成XHR对象的方法
            createXHR: function () {
                if (window.XMLHttpRequest) {
                    return new XMLHttpRequest()
                } else {
                    return new ActiveXObject()
                }
            },
            get: function (url, data, callback, dataType) {
                // 避免dataType大小写的问题
                var dataType = dataType.toLowerCase()
                // 如果有传入data，则在url后面跟上参数
                if (data) {
                    url += '?'
                    Object.keys(data).forEach(key => url += `${key}=${data[key]}&`)
                    url = url.slice(0, -1)
                }
                // 调用我们封装的方法生成XHR对象
                let xhr = this.createXHR()
                // 创建get请求
                xhr.open('get', url)
                // 发送请求
                xhr.send()
                xhr.onreadystatechange = function () {
                    if (xhr.readyState === 4) {
                        if (xhr.status >= 200 && xhr.status < 300 || xhr.status == 304) {
                            // 若dataType为json，则将返回的数据通过JSON.parse格式化
                            let res = dataType === 'json' ? JSON.parse(xhr.responseText) : xhr.responseText
                            // 调用回调函数，并把参数传进去
                            callback(res, xhr.status, xhr)
                        }
                    }
                }
            },
            post: function (url, data, callback, dataType) {
                // 避免dataType大小写的问题
                var dataType = dataType.toLowerCase()
                // 调用我们封装的方法动态生成XHR对象
                let xhr = this.createXHR()

                let str = ''
                // 若传入参数，则将参数序列化
                if (data) {
                    Object.keys(data).forEach(key => str += `${key}=${data[key]}&`)
                    str = str.slice(0, -1)
                }
                // 设置头部信息
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
                // 发送请求，并携带参数
                xhr.send(str)
                xhr.onreadystatechange = function () {
                    if (xhr.readyState === 4) {
                        if (xhr.status >= 200 && xhr.status < 300 || xhr.status == 304) {
                            // 若dataType为json，则将返回的数据通过JSON.parse格式化
                            let res = dataType === 'json' ? JSON.parse(xhr.responseText) : xhr.responseText
                            // 调用回调函数，把对应参数传进去
                            callback(res, xhr.status, xhr)
                        }
                    }
                }
            },
            ajax: function (params) {
                // 初始化参数
                let type = params.type ? params.type.toLowerCase() : 'get'
                let isAsync = params.isAsync ? params.isAsync : 'true'
                let url = params.url
                let data = params.data ? params.data : {}
                let dataType = params.dataType.toLowerCase()
                // 用我们封装的方法动态生成XHR对象
                let xhr = this.createXHR()

                let str = ''

                // 拼接字符串
                Object.keys(data).forEach(key => str += `${key}=${data[key]}&`)
                str = str.slice(0, -1)
                // 如果是get请求就把携带参数拼接到url后面
                if (type === 'get') url += `?${str}`;
                // 返回promise对象，便于外部then和catch函数调用
                return new Promise((resolve, reject) => {
                    // 创建请求
                    xhr.open(type, url, isAsync)

                    if (type === 'post') {
                        xhr.setRequestHeader('Content-Type', 'application/x-www-form-rulencoded')
                        xhr.send(str)
                    } else {
                        xhr.send()
                    }

                    xhr.onreadystatechange = function () {
                        if (xhr.readyState === 4) {
                            if (xhr.status >= 200 && xhr.status < 300 || xhr.status == 304) {
                                let res = dataType === 'json' ? JSON.parse(xhr.responseText) : xhr.responseText
                                resolve(res) // 请求成功，返回数据
                            } else {
                                reject(xhr.status) // 请求失败，返回状态码
                            }
                        }
                    }
                })
            }
        },

        isIEBrowser: function () {
            return navigator.userAgent.includes('MSIE ') || /Trident.*rv:11\./.test(navigator.userAgent);
            // return !!(navigator.userAgent.indexOf("MSIE ") > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./));
        },
        getScrollBarWidth: function getScrollBarWidth() {
            if (this.cachedWidth === null) {
                var $inner = document.createElement('div').classList.add('fixed-table-scroll-inner');
                var $outer = document.createElement('div').classList.add('fixed-table-scroll-outer');

                $outer.append($inner);
                document.querySelector('body').append($outer);

                var w1 = $inner.offsetWidth;
                $outer.style.overflow = 'scroll';
                var w2 = $inner.offsetWidth;

                if (w1 === w2) {
                    w2 = $outer.clientWidth;
                }

                $outer.parentNode.removeChild($outer);
                this.cachedWidth = w1 - w2;
            }
            return this.cachedWidth;
        },

        // 判断是否为空
        isEmpty: function (value) {
            return typeof value === 'undefined' || value === null ||
                (typeof value === 'string' && value.trim().length === 0);
        },
        // 判断是否为对象
        isObject: function (value) {
            return typeof value === 'object' && value !== null && !Array.isArray(obj);
        },
        // 判断是否为函数
        isFunction: function (value) {
            return typeof value === 'function';
        },

        //判断是否为数字
        // isNumber: function (value) {
        // return typeof value === 'number';
        // },
        isNumeric: function (n) {
            return !isNaN(parseFloat(n)) && isFinite(n);
        },
        // 判断是否为空对象 
        // isEmptyObject: function (value) {
        // return Object.keys(value).length === 0;
        // },
        isEmptyObject: function isEmptyObject() {
            var obj = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
            return Object.values(obj).length === 0 && obj.constructor === Object;
            // return Object.entries(obj).length === 0 && obj.constructor === Object;
        },
        // 判断是否为字符串 
        isString: function (value) {
            return typeof value === 'string';
        },
        // 判断是否为布尔值
        isBoolean: function (value) {
            return typeof value === 'boolean';
        },
        // 判断是否为undefined
        isUndefined: function (value) {
            return typeof value === 'undefined';
        },
        // 判断是否为null
        isNull: function (value) {
            return value === null;
        },
        // 判断是否为空数组
        isEmptyArray: function (value) {
            return Array.isArray(value) && value.length === 0;
        },
        // 判断是否为空值
        isEmptyValue: function (value) {
            return this.isUndefined(value) || this.isNull(value) || this.isEmptyObject(value) || this.isEmptyArray(value);
        },
        /* 合并多个对象的内容到第一个对象。
         第一个参数为合并的目标对象，后面的参数为合并的源对象。
         如果有重复的属性，则后面的属性会覆盖前面的属性。如果需要深度合并，请查看 extendDeep 方法。
         返回合并后的目标对象。
         注意：该方法不会修改原对象，而是返回一个新的对象。
        示例：
         var obj1 = {a: 1, b: 2};
         var obj2 = {b: 3, c: 4};
         var obj3 = {c: 5, d: 6};
        var mergedObj = utils.merge(obj1, obj2, obj3);
         console.log(mergedObj); // 输出: {a: 1, b: 3, c: 5, d:
         6}
         console.log(obj1); // 输出: {a: 1, b: 2}
         console.log(obj2); // 输出: {b: 3, c: 4}
         console.log(obj3); // 输出: {c: 5, d: 6}     */
        merge: function () {
            var target = arguments[0];
            for (var i = 1; i < arguments.length; i++) {
                var source = arguments[i];
                for (var key in source) {
                    if (source.hasOwnProperty(key)) {
                        target[key] = source[key];
                    }
                }
            }
            return target;
        },
        // 深度合并多个对象的内容到第一个对象。
        // 如果有重复的属性，则后面的属性会覆盖前面的属性。
        // 返回合并后的目标对象。
        // 注意：该方法会修改原对象，并将原对象作为合并后的目标对象返回。
        // 示例：
        // var obj1 = {a: 1, b: {c: 2}};
        // var obj2 = {b: {c: 3}, d: 4};
        // var mergedObj = utils.extendDeep(obj1, obj2);
        // console.log(mergedObj); // 输出: {a: 1, b: {c: 3}
        // , d: 4}
        // console.log(obj1); // 输出: {a: 1, b: {c: 3}
        // , d: 4}
        // console.log(obj2); // 输出: {b: {c: 3}, d: 4}
        extendDeep: function () {
            var target = arguments[0];
            for (var i = 1; i < arguments.length; i++) {
                var source = arguments[i];
                for (var key in source) {
                    if (source.hasOwnProperty(key)) {
                        if (typeof source[key] === 'object' && typeof target[key] === 'object') {
                            utils.extendDeep(target[key], source[key]);
                        }
                        else {
                            target[key] = source[key];
                        }
                    }
                }
            }
            return target;
        },
        // 复制一个对象。
        // 返回复制后的对象。
        // 注意：该方法会修改原对象，并将原对象作为复制后的对象返回。
        // 示例：
        // var obj = {a: 1, b: {c: 2}};
        // var copiedObj = utils.copy(obj);
        // console.log(copiedObj); // 输出: {a: 1, b: {c: 2}}
        // console.log(obj); // 输出: {a: 1, b: {c: 2}}
        copy: function copy(obj) {
            if (typeof obj !== 'object' || obj === null) {
                return obj;
            }
            var copiedObj = Array.isArray(obj) ? [] : {};
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                    copiedObj[key] = utils.copy(obj[key]);
                }
            }
            return copiedObj;
        },
        // 检查一个对象是否为空。
        // 返回一个布尔值，表示对象是否为空。
        // 示例：
        // var obj = {};
        // console.log(utils.isEmpty(obj)); // 输出: true
        isEmpty: function isEmpty(obj) {
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) { // hasOwnProperty检测属性是否为对象自有而不是继承的属性，如果是，返回true，否者false;
                    return false;
                };
            };
            return true;
        },

        // 合并多个对象的内容到第一个对象。
        // 如果有重复的属性，后面的对象属性值将覆盖前面的属性值，默认是浅拷贝如果需要深度合并，extend(true,obj,obj1)
        // 返回合并后的第一个对象
        // 示例：
        // var obj1 = {a: 1, b: {c: 2}};
        // var obj2 = {b: {d: 3}, e: 4};
        // var mergedObj = utils.extend(obj1, obj2);
        // console.log(mergedObj); // 输出: {a: 1, b: {c: 2, d: 3}, e: 4}
        extend: function extend() {
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
                    if (deep && copy && Utils.isObject(copy)) {
                        var src = target[name];
                        if (copyIsArray && Array.isArray(src)) {
                            if (src.every(function (it) {
                                return !isObject(it);
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
        },
        // 格式化字符串，类似c语言的printf函数;
        // 用法：Utils.sprintf(format, value1, value2, ...);
        // 返回格式化后的字符串;
        // 示例：Utils.sprintf("Age:%d, Height:%f", 29, 1.75);
        // 返回：Age:29, Height:1.75;
        sprintf: function sprintf(_str) {
            for (var _len = arguments.length, args = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
                args[_key - 1] = arguments[_key];
            }

            var flag = true;
            var i = 0;

            var str = _str.replace(/%s/g, function () {// 对每个匹配值应用函数，i自加1，直到无匹配值; 
                var arg = args[i++];

                if (typeof arg === 'undefined') {
                    flag = false;
                    return '';
                }
                return arg;
            });
            return flag ? str : '';
        },
        /* 这个函数的作用是对表格的列进行排序，并为每个列分配一个唯一的索引。这个索引是根据列的行跨度（rowspan）和列跨度（colspan）计算得出的。
函数的参数是一个数组（columns），其中每个元素都是一个包含列对象的一维数组。列对象可以包含以下属性：
- colspan：列的列跨度，默认为 1
- rowspan：列的行跨度，默认为 1
- field：列的数据字段，默认为索引
函数的实现首先计算总的列数（totalCol），然后为每个列的状态数组（flag）分配内存。接下来，遍历所有列，并为每个列分配一个唯一的索引。最后，为每个列分配一个唯一的索引，并根据其行跨度和列跨度更新状态数组。
这个函数的主要目的是为每个列分配一个唯一的索引，以便在后续处理中可以使用该索引来访问和操作列。 */
        setFieldIndex: function setFieldIndex(columns) {
            var totalCol = 0;
            var flag = [];

            var _iteratorNormalCompletion2 = true;
            var _didIteratorError2 = false;
            var _iteratorError2 = undefined;

            try {
                for (var _iterator2 = columns[0][Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
                    var column = _step2.value;

                    totalCol += column.colspan || 1;
                }
            } catch (err) {
                _didIteratorError2 = true;
                _iteratorError2 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion2 && _iterator2.return) {
                        _iterator2.return();
                    }
                } finally {
                    if (_didIteratorError2) {
                        throw _iteratorError2;
                    }
                }
            }

            for (var i = 0; i < columns.length; i++) {
                flag[i] = [];
                for (var j = 0; j < totalCol; j++) {
                    flag[i][j] = false;
                }
            }

            for (var _i = 0; _i < columns.length; _i++) {
                var _iteratorNormalCompletion3 = true;
                var _didIteratorError3 = false;
                var _iteratorError3 = undefined;

                try {
                    for (var _iterator3 = columns[_i][Symbol.iterator](), _step3; !(_iteratorNormalCompletion3 = (_step3 = _iterator3.next()).done); _iteratorNormalCompletion3 = true) {
                        var r = _step3.value;

                        var rowspan = r.rowspan || 1;
                        var colspan = r.colspan || 1;
                        var index = flag[_i].indexOf(false);

                        if (colspan === 1) {
                            r.fieldIndex = index;
                            // when field is undefined, use index instead
                            if (typeof r.field === 'undefined') {
                                r.field = index;
                            }
                        }

                        for (var k = 0; k < rowspan; k++) {
                            flag[_i + k][index] = true;
                        }
                        for (var _k = 0; _k < colspan; _k++) {
                            flag[_i][index + _k] = true;
                        }
                    }
                } catch (err) {
                    _didIteratorError3 = true;
                    _iteratorError3 = err;
                } finally {
                    try {
                        if (!_iteratorNormalCompletion3 && _iterator3.return) {
                            _iterator3.return();
                        }
                    } finally {
                        if (_didIteratorError3) {
                            throw _iteratorError3;
                        }
                    }
                }
            }
        },
        getFieldTitle: function getFieldTitle(list, value) {
            var _iteratorNormalCompletion = true;
            var _didIteratorError = false;
            var _iteratorError = undefined;

            try {
                for (var _iterator = list[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                    var item = _step.value;

                    if (item.field === value) {
                        return item.title;
                    }
                }
            } catch (err) {
                _didIteratorError = true;
                _iteratorError = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion && _iterator.return) {
                        _iterator.return();
                    }
                } finally {
                    if (_didIteratorError) {
                        throw _iteratorError;
                    }
                }
            }

            return '';
        },

        // 获取真实的data-attr属性值
        getRealDataAttr: function getRealDataAttr(dataAttr) {
            var _iteratorNormalCompletion6 = true;
            var _didIteratorError6 = false;
            var _iteratorError6 = undefined;

            try {
                for (var _iterator6 = Object.entries(dataAttr)[Symbol.iterator](), _step6; !(_iteratorNormalCompletion6 = (_step6 = _iterator6.next()).done); _iteratorNormalCompletion6 = true) {
                    var _ref = _step6.value;

                    var _ref2 = _slicedToArray(_ref, 2);

                    var attr = _ref2[0];
                    var value = _ref2[1];

                    var auxAttr = attr.split(/(?=[A-Z])/).join('-').toLowerCase();
                    if (auxAttr !== attr) {
                        dataAttr[auxAttr] = value;
                        delete dataAttr[attr];
                    }
                }
            } catch (err) {
                _didIteratorError6 = true;
                _iteratorError6 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion6 && _iterator6.return) {
                        _iterator6.return();
                    }
                } finally {
                    if (_didIteratorError6) {
                        throw _iteratorError6;
                    }
                }
            }

            return dataAttr;
        },
        // 计算对象值
        calculateObjectValue: function calculateObjectValue(self, name, args, defaultValue) {
            var func = name;

            if (typeof name === 'string') {
                // support obj.func1.func2
                var names = name.split('.');

                if (names.length > 1) {
                    func = window;
                    var _iteratorNormalCompletion4 = true;
                    var _didIteratorError4 = false;
                    var _iteratorError4 = undefined;

                    try {
                        for (var _iterator4 = names[Symbol.iterator](), _step4; !(_iteratorNormalCompletion4 = (_step4 = _iterator4.next()).done); _iteratorNormalCompletion4 = true) {
                            var f = _step4.value;

                            func = func[f];
                        }
                    } catch (err) {
                        _didIteratorError4 = true;
                        _iteratorError4 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion4 && _iterator4.return) {
                                _iterator4.return();
                            }
                        } finally {
                            if (_didIteratorError4) {
                                throw _iteratorError4;
                            }
                        }
                    }
                } else {
                    func = window[name];
                }
            }

            if (func !== null && (typeof func === 'undefined' ? 'undefined' : _typeof(func)) === 'object') {
                return func;
            }

            if (typeof func === 'function') {
                return func.apply(self, args || []);
            }

            if (!func && typeof name === 'string' && this.sprintf.apply(this, [name].concat(_toConsumableArray(args)))) {
                return this.sprintf.apply(this, [name].concat(_toConsumableArray(args)));
            }

            return defaultValue;
        },
        getItemField: function getItemField(item, field, escape) {
            var value = item;

            if (typeof field !== 'string' || item.hasOwnProperty(field)) {
                return escape ? this.escapeHTML(item[field]) : item[field];
            }

            var props = field.split('.');
            var _iteratorNormalCompletion7 = true;
            var _didIteratorError7 = false;
            var _iteratorError7 = undefined;

            try {
                for (var _iterator7 = props[Symbol.iterator](), _step7; !(_iteratorNormalCompletion7 = (_step7 = _iterator7.next()).done); _iteratorNormalCompletion7 = true) {
                    var p = _step7.value;

                    value = value && value[p];
                }
            } catch (err) {
                _didIteratorError7 = true;
                _iteratorError7 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion7 && _iterator7.return) {
                        _iterator7.return();
                    }
                } finally {
                    if (_didIteratorError7) {
                        throw _iteratorError7;
                    }
                }
            }

            return escape ? this.escapeHTML(value) : value;
        },

        escapeHTML: function (text) {
            if (typeof text === 'string') {
                return text
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#039;')
                    .replace(/`/g, '&#x60;');
            }
            return text;
        },
        inArray: function (elem, arr, i) {
            var len, indexOf = Array.indexOf;
            if (Array.isArray(arr)) {
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
        },
        parents: function getParents(el, selector, filter) {
            // console.log(el);
            // If no parentSelector defined will bubble up all the way to *document*
            const result = [];
            const matchesSelector = el.matches || el.webkitMatchesSelector || el.mozMatchesSelector || el.msMatchesSelector;

            // match start from parent
            el = el.parentElement;
            if (!selector) {
                while (el) {
                    result.push(el);
                    el = el.parentElement;
                }
                return result;
            }
            else {
                while (el && !matchesSelector.call(el, selector)) {

                    if (!filter) {
                        result.push(el);
                    } else {
                        if (matchesSelector.call(el, filter)) {
                            result.push(el);
                        }
                    }
                    el = el.parentElement;
                }
                return result;
            }
        },
        // Tree相关方法
        getParent: function (node, source, treefield, parentfield) {
            var data = [];
            var items = source.filter(function (item, index) {
                return node[parentfield] == item[treefield];
            });
            items.forEach(function (item, index) {
                data.splice(0, 0, item);
                var child = Utils.getParent(item, source, treefield, parentfield);
                child.forEach(function (n, i) {
                    data.splice(0, 0, n);
                });
            });
            return data;

        },
        getChild: function (node, source, treefield, parentfield) {
            var data = [];
            var items = source.filter(function (item, index) {
                return item[parentfield] == node[treefield];
            });
            items.forEach(function (item, index) {
                data.push(item);
                var child = Utils.getChild(item, source, treefield, parentfield);
                child.forEach(function (n, i) {
                    data.push(n);
                });
            });
            return data;
        },

    };

    var DEFAULTS = {
        classes: 'table table-hover',
        theadClasses: '',
        sortClass: undefined,
        locale: undefined,
        height: undefined,
        undefinedText: '-',
        sortName: undefined,
        sortOrder: 'asc',
        sortStable: false,
        rememberOrder: false,
        striped: false,
        columns: [[]],
        data: [],
        totalField: 'total',
        dataField: 'rows',
        method: 'get',
        url: undefined,
        ajax: undefined,
        cache: true,
        contentType: 'application/json',
        dataType: 'json',
        ajaxOptions: {},
        queryParams: function queryParams(params) {
            return params;
        },

        queryParamsType: 'limit', responseHandler: function responseHandler(res) {
            return res;
        },

        pagination: false,
        onlyInfoPagination: false,
        paginationLoop: true,
        sidePagination: 'client', // client or server
        totalRows: 0, // server side need to set
        pageNumber: 1,
        pageSize: 10,
        pageList: [10, 25, 50, 100],
        paginationHAlign: 'right', // right, left
        paginationVAlign: 'bottom', // bottom, top, both
        paginationDetailHAlign: 'left', // right, left
        paginationPreText: '&lsaquo;',
        paginationNextText: '&rsaquo;',
        search: false,
        searchOnEnterKey: false,
        strictSearch: false,
        searchAlign: 'right',
        selectItemName: 'btSelectItem',
        showHeader: true,
        showFooter: false,
        showColumns: false,
        showPaginationSwitch: false,
        showRefresh: false,
        showToggle: false,
        showFullscreen: false,
        smartDisplay: true,
        escape: false,
        minimumCountColumns: 1,
        idField: undefined,
        uniqueId: undefined,
        cardView: false,
        detailView: false,
        detailFormatter: function detailFormatter(index, row) {
            return '';
        },
        detailFilter: function detailFilter(index, row) {
            return true;
        },

        trimOnSearch: true,
        clickToSelect: false,
        singleSelect: false,
        toolbar: undefined,
        toolbarAlign: 'left',
        buttonsToolbar: undefined,
        buttonsAlign: 'right',
        checkboxHeader: true,
        sortable: true,
        silentSort: true,
        maintainSelected: false,
        searchTimeOut: 500,
        searchText: '',
        iconSize: undefined,
        buttonsClass: CONSTANTS.classes.buttons,
        iconsPrefix: CONSTANTS.iconsPrefix, // glyphicon or fa(font-awesome)
        icons: CONSTANTS.icons,
        customSearch: Function.prototype,
        customSort: Function.prototype,
        //tree begin
        treeShowField: null,
        idField: 'id',
        parentIdField: 'pid',
        rootParentId: null,
        onGetNodes: function onGetNodes(row, data) {
            var that = this;
            var nodes = [];
            data.forEach(function (item) {
                if (row[that.options.idField] === item[that.options.parentIdField]) {
                    nodes.push(item);
                }
            });
            return nodes;
        },
        onCheckRoot: function onCheckRoot(row, data) {
            var that = this;
            return that.options.rootParentId === row[that.options.parentIdField] || !row[that.options.parentIdField];
        },
        //end  
        ignoreClickToSelectOn: function ignoreClickToSelectOn(_ref3) {
            var tagName = _ref3.tagName;

            return ['A', 'BUTTON'].includes(tagName);
        },
        rowStyle: function rowStyle(row, index) {
            return {};
        },
        rowAttributes: function rowAttributes(row, index) {
            return {};
        },
        footerStyle: function footerStyle(row, index) {
            return {};
        },
        onAll: function onAll(name, args) {
            return false;
        },
        onClickCell: function onClickCell(field, value, row, $element) {
            return false;
        },
        onDblClickCell: function onDblClickCell(field, value, row, $element) {
            return false;
        },
        onClickRow: function onClickRow(item, $element) {
            return false;
        },
        onDblClickRow: function onDblClickRow(item, $element) {
            return false;
        },
        onSort: function onSort(name, order) {
            return false;
        },
        onCheck: function onCheck(row) {
            return false;
        },
        onUncheck: function onUncheck(row) {
            return false;
        },
        onCheckAll: function onCheckAll(rows) {
            return false;
        },
        onUncheckAll: function onUncheckAll(rows) {
            return false;
        },
        onCheckSome: function onCheckSome(rows) {
            return false;
        },
        onUncheckSome: function onUncheckSome(rows) {
            return false;
        },
        onLoadSuccess: function onLoadSuccess(data) {
            return false;
        },
        onLoadError: function onLoadError(status) {
            return false;
        },
        onColumnSwitch: function onColumnSwitch(field, checked) {
            return false;
        },
        onPageChange: function onPageChange(number, size) {
            return false;
        },
        onSearch: function onSearch(text) {
            return false;
        },
        onToggle: function onToggle(cardView) {
            return false;
        },
        onPreBody: function onPreBody(data) {
            return false;
        },
        onPostBody: function onPostBody() {
            return false;
        },
        onPostHeader: function onPostHeader() {
            return false;
        },
        onExpandRow: function onExpandRow(index, row, $detail) {
            return false;
        },
        onCollapseRow: function onCollapseRow(index, row) {
            return false;
        },
        onRefreshOptions: function onRefreshOptions(options) {
            return false;
        },
        onRefresh: function onRefresh(params) {
            return false;
        },
        onResetView: function onResetView() {
            return false;
        },
        onScrollBody: function onScrollBody() {
            return false;
        }
    };

    var LOCALES = {};
    LOCALES['en-US'] = LOCALES.en = {
        formatLoadingMessage: function formatLoadingMessage() {
            return 'Loading, please wait...';
        },
        formatRecordsPerPage: function formatRecordsPerPage(pageNumber) {
            return Utils.sprintf('%s rows per page', pageNumber);
        },
        formatShowingRows: function formatShowingRows(pageFrom, pageTo, totalRows) {
            return Utils.sprintf('Showing %s to %s of %s rows', pageFrom, pageTo, totalRows);
        },
        formatDetailPagination: function formatDetailPagination(totalRows) {
            return Utils.sprintf('Showing %s rows', totalRows);
        },
        formatSearch: function formatSearch() {
            return 'Search';
        },
        formatNoMatches: function formatNoMatches() {
            return 'No matching records found';
        },
        formatPaginationSwitch: function formatPaginationSwitch() {
            return 'Hide/Show pagination';
        },
        formatRefresh: function formatRefresh() {
            return 'Refresh';
        },
        formatToggle: function formatToggle() {
            return 'Toggle';
        },
        formatFullscreen: function formatFullscreen() {
            return 'Fullscreen';
        },
        formatColumns: function formatColumns() {
            return 'Columns';
        },
        formatAllRows: function formatAllRows() {
            return 'All';
        }
    };
    Object.assign(DEFAULTS, LOCALES['en-US']);
    var COLUMN_DEFAULTS = {
        radio: false,
        checkbox: false,
        checkboxEnabled: true,
        field: undefined,
        title: undefined,
        titleTooltip: undefined,
        'className': undefined,
        align: undefined, // left, right, center
        halign: undefined, // left, right, center
        falign: undefined, // left, right, center
        valign: undefined, // top, middle, bottom
        width: undefined,
        sortable: false,
        order: 'asc', // asc, desc
        visible: true,
        switchable: true,
        clickToSelect: true,
        formatter: undefined,
        footerFormatter: undefined,
        events: undefined,
        sorter: undefined,
        sortName: undefined,
        cellStyle: undefined,
        searchable: true,
        searchFormatter: true,
        cardVisible: true,
        escape: false,
        showSelectTitle: false
    };

    var EVENTS = {
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
        'reset-view.bs.table': 'onResetView',
        'refresh.bs.table': 'onRefresh',
        'scroll-body.bs.table': 'onScrollBody'
    };
    function _classCallCheck(instance, Constructor) {
        if (!(instance instanceof Constructor)) {
            throw new TypeError("Cannot call a class as a function");
        }
    };

    var _createClass = function () {
        function defineProperties(target, props) {
            for (var i = 0; i < props.length; i++) {
                var descriptor = props[i];
                descriptor.enumerable = descriptor.enumerable || false;
                descriptor.configurable = true;
                if ("value" in descriptor) descriptor.writable = true;
                Object.defineProperty(target, descriptor.key, descriptor);
            }
        }

        return function (Constructor, protoProps, staticProps) {
            if (protoProps) defineProperties(Constructor.prototype, protoProps);
            if (staticProps) defineProperties(Constructor, staticProps);
            return Constructor;
        };
    }();



    (function () {

        // 定义BootstrapTable函数，接收两个参数：el和options
        var BootstrapTable = function () {
            function BootstrapTable(el, options) {
                _classCallCheck(this, BootstrapTable);
                this.options = options;
                this.$el = el;
                this.$el_ = this.$el.cloneNode();
                this.timeoutId_ = 0;
                this.timeoutFooter_ = 0;
                this.init();
            };
            _createClass(BootstrapTable, [{
                key: 'init',
                value: function init() {
                    this.initLocale();
                    this.initContainer();
                    this.initTable();
                    this.initHeader();
                    this.initData();
                    this.initHiddenRows();
                    this.initFooter();
                    this.initToolbar();
                    this.initPagination();
                    this.initBody();
                    this.initSearchText();
                    this.initServer();
                }
            }, {
                key: 'initLocale',
                value: function initLocale() {
                    if (this.options.locale) {
                        var locales = fn.bootstrapTable.locales;
                        var parts = this.options.locale.split(/-|_/);
                        parts[0].toLowerCase();
                        if (parts[1]) {
                            parts[1].toUpperCase();
                        }
                        if (locales[this.options.locale]) {
                            // locale as requested
                            Object.assign(this.options, locales[this.options.locale]);
                        } else if (fn.bootstrapTable.locales[parts.join('-')]) {
                            // locale with sep set to - (in case original was specified with _)
                            Object.assign(this.options, locales[parts.join('-')]);
                        } else if (fn.bootstrapTable.locales[parts[0]]) {
                            // short locale language code (i.e. 'en')
                            Object.assign(this.options, locales[parts[0]]);
                        }
                    }
                }
            }, {
                key: 'initContainer',
                value: function initContainer() {
                    var topPagination = ['top', 'both'].includes(this.options.paginationVAlign) ? '<div class="fixed-table-pagination clearfix"></div>' : '';
                    var bottomPagination = ['bottom', 'both'].includes(this.options.paginationVAlign) ? '<div class="fixed-table-pagination"></div>' : '';

                    this.$container = document.createElement('div')
                    this.$container.classList.add('bootstrap-table');
                    console.log(this.$container)
                    this.$container.insertAdjacentHTML('afterbegin', ' <div class="fixed-table-toolbar"></div>\n        ' + topPagination + '\n        <div class="fixed-table-container">\n        <div class="fixed-table-header"><table></table></div>\n        <div class="fixed-table-body">\n        <div class="fixed-table-loading">\n        ' + this.options.formatLoadingMessage() + '\n        </div>\n        </div>\n        <div class="fixed-table-footer"><table><tr></tr></table></div>\n        </div>\n        ' + bottomPagination + '\n        </div>\n      ');
                    this.$el.after(this.$container)
                    this.$tableContainer = this.$container.querySelector('.fixed-table-container');
                    this.$tableHeader = this.$container.querySelector('.fixed-table-header');
                    this.$tableBody = this.$container.querySelector('.fixed-table-body');
                    this.$tableLoading = this.$container.querySelector('.fixed-table-loading');
                    this.$tableFooter = this.$container.querySelector('.fixed-table-footer');
                    // checking if custom table-toolbar exists or not
                    if (this.options.buttonsToolbar) {
                        this.$toolbar = document.querySelector('body').querySelector(this.options.buttonsToolbar);
                    } else {
                        this.$toolbar = this.$container.querySelector('.fixed-table-toolbar');
                    }
                    this.$pagination = this.$container.querySelector('.fixed-table-pagination');

                    this.$tableBody.append(this.$el);
                    // this.$container.insertAdjacentHTML('afterend', '<div class="clearfix"></div>');
                    this.$container.insertAdjacentHTML('afterend', '<div class="clearfix"></div>');
                    this.$el.className = this.options.classes;
                    if (this.options.striped) {
                        this.$el.classList.add('table-striped');
                    }
                    if (this.options.classes.split(' ').includes('table-no-bordered')) {
                        this.$tableContainer.classList.add('table-no-bordered');
                    }
                }
            }, {
                key: 'initTable',
                value: function initTable() {
                    var _this = this;

                    var columns = [];
                    var data = [];

                    this.$header = this.$el.querySelectorAll('thead');
                    if (!this.$header.length) {
                        this.$header = document.createElement('thead')
                        this.$header.className = this.options.theadClasses;
                        this.$el.appendChild(this.$header);
                    }
                    this.$header.querySelectorAll('tr').forEach(function (el, i) {
                        var column = [];
                        var $$el = document.querySelector(el);
                        $$el.querySelectorAll('th').forEach(function (el, i) {
                            // #2014: getFieldIndex and elsewhere assume this is string, causes issues if not
                            if (typeof $$el.dataset['field'] !== 'undefined') {
                                $$el.dataset['field'] = '' + $$el.dataset['field'];
                            }
                            column.push(Object.assign({}, {
                                title: $$el.innerHTML,
                                'className': $$el.getAttribute('className'),
                                titleTooltip: $$el.getAttribute('title'),
                                rowspan: $$el.getAttribute('rowspan') ? +$(el).attr('rowspan') : undefined,
                                colspan: $$el.getAttribute('colspan') ? +$(el).attr('colspan') : undefined
                            }, $$el.dataset));
                        });
                        columns.push(column);
                    });

                    if (!Array.isArray(this.options.columns[0])) {
                        this.options.columns = [this.options.columns];
                    }

                    this.options.columns = Object.assign([], columns, this.options.columns);
                    this.columns = [];
                    this.fieldsColumnsIndex = [];

                    Utils.setFieldIndex(this.options.columns);

                    this.options.columns.forEach(function (columns, i) {
                        columns.forEach(function (_column, j) {
                            var column = Object.assign({}, BootstrapTable.COLUMN_DEFAULTS, _column);

                            if (typeof column.fieldIndex !== 'undefined') {
                                _this.columns[column.fieldIndex] = column;
                                _this.fieldsColumnsIndex[column.field] = column.fieldIndex;
                            }

                            _this.options.columns[i][j] = column;
                        });
                    });

                    // if options.data is setting, do not process tbody data
                    if (this.options.data.length) {
                        return;
                    }

                    var m = [];
                    this.$el.querySelectorAll('tbody>tr').forEach(function (el, y) {
                        var row = {};
                        var $$el = document.querySelector(el);
                        // save tr's id, class and data-* attributes
                        row._id = $$el.getAttribute('id');
                        row._class = $$el.getAttribute('className');
                        row._data = Utils.getRealDataAttr($$el.getAttribute.dataset);

                        $$el.querySelectorAll('td').forEach(function (el, _x) {
                            var $$$el = document.querySelector(el);
                            var cspan = +$$$el.getAttribute('colspan') || 1;
                            var rspan = +$$$el.getAttribute('rowspan') || 1;
                            var x = _x;

                            // skip already occupied cells in current row
                            for (; m[y] && m[y][x]; x++) { }
                            // ignore


                            // mark matrix elements occupied by current cell with true
                            for (var tx = x; tx < x + cspan; tx++) {
                                for (var ty = y; ty < y + rspan; ty++) {
                                    if (!m[ty]) {
                                        // fill missing rows
                                        m[ty] = [];
                                    }
                                    m[ty][tx] = true;
                                }
                            }

                            var field = _this.columns[x].field;

                            row[field] = $$$el.innerHTML;
                            // save td's id, class and data-* attributes
                            row['_' + field + '_id'] = $$$el.getAttribute('id');
                            row['_' + field + '_class'] = $$$el.getAttribute('className');
                            row['_' + field + '_rowspan'] = $$$el.getAttribute('rowspan');
                            row['_' + field + '_colspan'] = $$$el.getAttribute('colspan');
                            row['_' + field + '_title'] = $$$el.getAttribute('title');
                            row['_' + field + '_data'] = Utils.getRealDataAttr($$$el.dataset);
                        });
                        data.push(row);
                    });
                    this.options.data = data;
                    if (data.length) {
                        this.fromHtml = true;
                    }
                }
            }, {
                key: 'initHeader',
                value: function initHeader() {
                    var _this2 = this;

                    var visibleColumns = {};
                    var html = [];

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

                    this.options.columns.forEach(function (columns, i) {
                        html.push('<tr>');

                        if (i === 0 && !_this2.options.cardView && _this2.options.detailView) {
                            html.push('<th class="detail" rowspan="' + _this2.options.columns.length + '">\n            <div class="fht-cell"></div>\n            </th>\n          ');
                        }

                        columns.forEach(function (column, j) {
                            var text = '';

                            var halign = ''; // header align style

                            var align = ''; // body align style

                            var style = '';
                            var class_ = Utils.sprintf(' class="%s"', column['className']);
                            var unitWidth = 'px';
                            var width = column.width;

                            if (column.width !== undefined && !_this2.options.cardView) {
                                if (typeof column.width === 'string') {
                                    if (column.width.includes('%')) {
                                        unitWidth = '%';
                                    }
                                }
                            }
                            if (column.width && typeof column.width === 'string') {
                                width = column.width.replace('%', '').replace('px', '');
                            }

                            halign = Utils.sprintf('text-align: %s; ', column.halign ? column.halign : column.align);
                            align = Utils.sprintf('text-align: %s; ', column.align);
                            style = Utils.sprintf('vertical-align: %s; ', column.valign);
                            style += Utils.sprintf('width: %s; ', (column.checkbox || column.radio) && !width ? !column.showSelectTitle ? '36px' : undefined : width ? width + unitWidth : undefined);

                            if (typeof column.fieldIndex !== 'undefined') {
                                _this2.header.fields[column.fieldIndex] = column.field;
                                _this2.header.styles[column.fieldIndex] = align + style;
                                _this2.header.classes[column.fieldIndex] = class_;
                                _this2.header.formatters[column.fieldIndex] = column.formatter;
                                _this2.header.events[column.fieldIndex] = column.events;
                                _this2.header.sorters[column.fieldIndex] = column.sorter;
                                _this2.header.sortNames[column.fieldIndex] = column.sortName;
                                _this2.header.cellStyles[column.fieldIndex] = column.cellStyle;
                                _this2.header.searchables[column.fieldIndex] = column.searchable;

                                if (!column.visible) {
                                    return;
                                }

                                if (_this2.options.cardView && !column.cardVisible) {
                                    return;
                                }

                                visibleColumns[column.field] = column;
                            }

                            html.push('<th' + Utils.sprintf(' title="%s"', column.titleTooltip), column.checkbox || column.radio ? Utils.sprintf(' class="bs-checkbox %s"', column['className'] || '') : class_, Utils.sprintf(' style="%s"', halign + style), Utils.sprintf(' rowspan="%s"', column.rowspan), Utils.sprintf(' colspan="%s"', column.colspan), Utils.sprintf(' data-field="%s"', column.field),
                                // If `column` is not the first element of `this.options.columns[0]`, then className 'data-not-first-th' should be added.
                                j === 0 && i > 0 ? ' data-not-first-th' : '', '>');

                            html.push(Utils.sprintf('<div class="th-inner %s">', _this2.options.sortable && column.sortable ? 'sortable both' : ''));

                            text = _this2.options.escape ? Utils.escapeHTML(column.title) : column.title;

                            var title = text;
                            if (column.checkbox) {
                                text = '';
                                if (!_this2.options.singleSelect && _this2.options.checkboxHeader) {
                                    text = '<input name="btSelectAll" type="checkbox" />';
                                }
                                _this2.header.stateField = column.field;
                            }
                            if (column.radio) {
                                text = '';
                                _this2.header.stateField = column.field;
                                _this2.options.singleSelect = true;
                            }
                            if (!text && column.showSelectTitle) {
                                text += title;
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

                    this.$header.querySelectorAll('th[data-field]').forEach(function (el) {
                        // 标题栏data属性写入各自的column数据，展开卡片式详情时使用


                        Object.entries(visibleColumns[el.dataset['field']]).forEach(([k, v]) => {
                            el.dataset[k] = v;
                        });
                    });
                    this.$container.querySelectorAll('.th-inner').forEach(el => {
                        $Event.on($Event.off(el, 'click'), 'click'
                            , function (e) {
                                var $this = e.currentTarget;

                                if (_this2.options.detailView && !$this.parentNode.classList.contains('bs-checkbox')) {
                                    if ($this.closest('.bootstrap-table') !== _this2.$container) {
                                        return false;
                                    }
                                }

                                if (_this2.options.sortable && $this.parentNode.dataset.sortable) {
                                    _this2.onSort(e);
                                }
                            });
                    });
                    let childrens = this.$header.children
                    for (let i = 0; i < childrens.length; i++) {
                        if (childrens[i].children.length > 0) {
                            let children = childrens[i].children
                            for (let j = 0; j < children.length; j++) {
                                $Event.off(children[j], 'keypress')
                                $Event.on(children[j], "keypress", function (e) {
                                    if (_this2.options.sortable && e.currentTarget.dataset.sortable) {
                                        var code = e.keyCode || e.which;
                                        if (code === 13) {
                                            // Enter keycode
                                            _this2.onSort(e);
                                        }
                                    }
                                })
                            }
                        }
                    };

                    $Event.off(window, 'resize.bootstrap-table');
                    if (!this.options.showHeader || this.options.cardView) {
                        this.$header.style.display = 'none';
                        this.$tableHeader.style.display = 'none';
                        this.$tableLoading.style.top = 0;
                    } else {
                        this.$header.style.display = '';
                        this.$tableHeader.style.display = '';
                        this.$tableLoading.style.top = this.$header.outerHeight + 1;
                        // Assign the correct sortable arrow
                        this.getCaret();// 更新排序箭头显示情况 
                        $Event.on(window, 'resize.bootstrap-table', this.resetWidth.bind(this));
                    }

                    this.$selectAll = this.$header.querySelectorAll('[name="btSelectAll"]');
                    this.$selectAll.forEach(item => {
                        // item.indeterminate = false,
                        $Event.on($Event.off(item, 'click'), 'click', function (_ref4) {
                            var currentTarget = _ref4.currentTarget;

                            var checked = currentTarget['checked'];
                            _this2[checked ? 'checkAll' : 'uncheckAll']();
                            _this2.updateSelected();
                        })
                    });
                    //tree
                    // var treeShowField = this.options.treeShowField;
                    // if (treeShowField) {
                    //     this.header.fields.forEach(function (field) {
                    //         if (treeShowField === field) {
                    //             _this2.treeEnable = true;
                    //             return false;
                    //         }
                    //     });
                    // }

                }
            }, {
                key: 'initFooter',
                value: function initFooter() {
                    if (!this.options.showFooter || this.options.cardView) {
                        this.$tableFooter.style.display = 'none';
                    } else {
                        this.$tableFooter.style.display = '';
                    }
                }
            }, {
                key: 'initData',
                value: function initData(data, type) {
                    if (type === 'append') {
                        this.options.data = this.options.data.concat(data);
                    } else if (type === 'prepend') {
                        this.options.data = [].concat(data).concat(this.options.data);
                    } else {
                        this.options.data = data || this.options.data;
                    }

                    this.data = this.options.data;

                    if (this.options.sidePagination === 'server') {
                        return;
                    }
                    this.initSort();
                }
            }, {
                key: 'initSort',
                value: function initSort() {
                    var _this3 = this;

                    var name = this.options.sortName;
                    var order = this.options.sortOrder === 'desc' ? -1 : 1;
                    var index = this.header.fields.indexOf(this.options.sortName);
                    var timeoutId = 0;

                    if (this.options.customSort !== Function.prototype) {
                        this.options.customSort.apply(this, [this.options.sortName, this.options.sortOrder]);
                        return;
                    }

                    if (index !== -1) {
                        if (this.options.sortStable) {
                            this.data.forEach(function (row, i) {
                                row._position = i;
                            });
                        }

                        this.data.sort(function (a, b) {
                            if (_this3.header.sortNames[index]) {
                                name = _this3.header.sortNames[index];
                            }
                            var aa = Utils.getItemField(a, name, _this3.options.escape);
                            var bb = Utils.getItemField(b, name, _this3.options.escape);
                            var value = Utils.calculateObjectValue(_this3.header, _this3.header.sorters[index], [aa, bb, a, b]);

                            if (value !== undefined) {
                                if (_this3.options.sortStable && value === 0) {
                                    return a._position - b._position;
                                }
                                return order * value;
                            }

                            // Fix #161: undefined or null string sort bug.
                            if (aa === undefined || aa === null) {
                                aa = '';
                            }
                            if (bb === undefined || bb === null) {
                                bb = '';
                            }

                            if (_this3.options.sortStable && aa === bb) {
                                aa = a._position;
                                bb = b._position;
                                return a._position - b._position;
                            }

                            // IF both values are numeric, do a numeric comparison
                            if (Utils.isNumeric(aa) && Utils.isNumeric(bb)) {
                                // Convert numerical values form string to float.
                                aa = parseFloat(aa);
                                bb = parseFloat(bb);
                                if (aa < bb) {
                                    return order * -1;
                                }
                                return order;
                            }

                            if (aa === bb) {
                                return 0;
                            }

                            // If value is not a string, convert to string
                            if (typeof aa !== 'string') {
                                aa = aa.toString();
                            }

                            if (aa.localeCompare(bb) === -1) {
                                return order * -1;
                            }

                            return order;
                        });

                        if (this.options.sortClass !== undefined) {
                            clearTimeout(timeoutId);
                            timeoutId = setTimeout(function () {
                                _this3.$el.removeClass(_this3.options.sortClass);
                                var index = _this3.$header.querySelector(Utils.sprintf('[data-field="%s"]', _this3.options.sortName).index() + 1);
                                _this3.$el.querySelector(Utils.sprintf('tr td:nth-child(%s)', index)).classList.add(_this3.options.sortClass);
                            }, 250);
                        }
                    }
                }
            }, {
                key: 'onSort',
                value: function onSort(_ref5) {
                    var type = _ref5.type, that = this,
                        currentTarget = _ref5.currentTarget;

                    var $this = type === 'keypress' ? currentTarget : currentTarget.parentNode;
                    var $this_ = this.$header.querySelectorAll('th')[$this.index];// 记录this.$header下相同元素  

                    this.$header_?.querySelectorAll('span.order').forEach(item => item.remove());
                    this.$header.querySelectorAll('span.order').forEach(item => item.remove());

                    if (this.options.sortName === $this.dataset['field']) {
                        this.options.sortOrder = this.options.sortOrder === 'asc' ? 'desc' : 'asc';
                    } else {
                        this.options.sortName = $this.dataset['field'];
                        if (this.options.rememberOrder) {
                            this.options.sortOrder = $this.dataset['order'] === 'asc' ? 'desc' : 'asc';
                        } else {
                            this.options.sortOrder = this.columns[this.fieldsColumnsIndex[$this.dataset['field']]].order;
                        }
                    }
                    this.trigger('sort', this.options.sortName, this.options.sortOrder);

                    $this.dataset['order'] = this.options.sortOrder;
                    ($this_ || []).forEach(t => t.dataset['order'] = that.options.sortOrder);

                    // Assign the correct sortable arrow
                    this.getCaret();

                    if (this.options.sidePagination === 'server') {
                        this.initServer(this.options.silentSort);
                        return;
                    }

                    this.initSort();
                    this.initBody();
                }
            }, {
                key: 'initToolbar',
                value: function initToolbar() {
                    var _this4 = this;

                    var html = [];
                    var timeoutId = 0;
                    var $keepOpen = void 0;
                    var $search = void 0;
                    var switchableCount = 0;

                    if (this.$toolbar.querySelector('.bs-bars')?.children().length) {
                        document.querySelector('body').append(this.options.toolbar);
                    }
                    this.$toolbar.innerHTML = '';

                    if (typeof this.options.toolbar === 'string' || _typeof(this.options.toolbar) === 'object') {
                        this.$toolbar.append(Utils.sprintf('<div class="bars pull-%s"></div>', this.options.toolbarAlign))
                        this.$toolbar.append(this.options.toolbar);
                    }

                    // showColumns, showToggle, showRefresh
                    html = [Utils.sprintf('<div class="columns columns-%s btn-group %s-%s">', this.options.buttonsAlign, CONSTANTS.classes.pull, this.options.buttonsAlign)];

                    if (typeof this.options.icons === 'string') {
                        this.options.icons = Utils.calculateObjectValue(null, this.options.icons);
                    }

                    if (this.options.showPaginationSwitch) {
                        html.push(Utils.sprintf('<button class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + '" type="button" name="paginationSwitch" aria-label="pagination Switch" title="%s">', this.options.formatPaginationSwitch()), Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.paginationSwitchDown), '</button>');
                    }

                    if (this.options.showFullscreen) {
                        $Event.on($Event.off(this.$toolbar.querySelector('button[name="fullscreen"]'), 'click'), 'click',
                            this.toggleFullscreen.bind(this));
                    }

                    if (this.options.showRefresh) {
                        html.push(Utils.sprintf('<button class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + '" type="button" name="refresh" aria-label="refresh" title="%s">', this.options.formatRefresh()), Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.refresh), '</button>');
                    }

                    if (this.options.showToggle) {
                        html.push(Utils.sprintf('<button class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + '" type="button" name="toggle" aria-label="toggle" title="%s">', this.options.formatToggle()), Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.toggleOff), '</button>');
                    }

                    if (this.options.showFullscreen) {
                        html.push(Utils.sprintf('<button class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + '" type="button" name="fullscreen" aria-label="fullscreen" title="%s">', this.options.formatFullscreen()), Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.fullscreen), '</button>');
                    }


                    if (this.options.showColumns) {
                        html.push(Utils.sprintf('<div class="keep-open btn-group" title="%s">', this.options.formatColumns()), '<button type="button" aria-label="columns" class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + ' dropdown-toggle" data-toggle="dropdown">', Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.columns), ' <span class="caret"></span>', '</button>', CONSTANTS.html.toolbarDropdown[0]);

                        this.columns.forEach(function (column, i) {
                            if (column.radio || column.checkbox) {
                                return;
                            }

                            if (_this4.options.cardView && !column.cardVisible) {
                                return;
                            }

                            var checked = column.visible ? ' checked="checked"' : '';

                            if (column.switchable) {
                                html.push(Utils.sprintf(CONSTANTS.html.toolbarDropdownItem, Utils.sprintf('<input type="checkbox" data-field="%s" value="%s"%s> %s', column.field, i, checked, column.title)));
                                switchableCount++;
                            }
                        });
                        html.push(CONSTANTS.html.toolbarDropdown[1], '</div>');
                    }

                    html.push('</div>');

                    // Fix #188: this.showToolbar is for extensions
                    if (this.showToolbar || html.length > 2) {
                        this.$toolbar.insertAdjacentHTML('beforeend', html.join(''));
                    }

                    if (this.options.showPaginationSwitch) {
                        $Event.on($Event.off(this.$toolbar.querySelector('button[name="paginationSwitch"]'), 'click'), 'click',
                            this.togglePagination.bind(this));

                    }

                    if (this.options.showRefresh) {
                        $Event.on($Event.off(this.$toolbar.querySelector('button[name="refresh"]'), 'click'), 'click',
                            this.refresh.bind(this));

                    }

                    if (this.options.showToggle) {
                        $Event.on($Event.off(this.$toolbar.querySelector('button[name="toggle"]'), 'click'), 'click',
                            function () {
                                _this4.toggleView();
                            });

                    }

                    if (this.options.showColumns) {
                        $keepOpen = this.$toolbar.querySelector('.keep-open');

                        if (switchableCount <= this.options.minimumCountColumns) {
                            $keepOpen.querySelectorall('input').forEach(i => i.disabled = true);
                        }
                        $keepOpen.querySelectorAll('li').forEach(li => $Event.on($Event.off(li, 'click'), 'click',
                            function (e) {
                                e.stopImmediatePropagation();
                            }));
                        $keepOpen.querySelectorAll('input').forEach(p => $Event.on($Event.off(p, 'click'), 'click',

                            function (_ref6) {
                                var currentTarget = _ref6.currentTarget;

                                var $this = currentTarget;

                                _this4.toggleColumn($this.val(), $this['checked'], false);
                                _this4.trigger('column-switch', $this.dataset['field'], $this['checked']);
                            }));
                    }

                    if (this.options.search) {
                        html = [];
                        html.push(Utils.sprintf('<div class="%s-%s search">', CONSTANTS.classes.pull, this.options.searchAlign), Utils.sprintf('<input class="form-control' + Utils.sprintf(' input-%s', this.options.iconSize) + '" type="text" placeholder="%s">', this.options.formatSearch()), '</div>');

                        this.$toolbar.insertAdjacentHTML('beforeend', html.join(''));
                        $search = this.$toolbar.querySelector('.search input');
                        $Event.on($Event.off($search, 'keyup drop blur'), 'keyup drop blur',
                            function (event) {
                                if (_this4.options.searchOnEnterKey && event.keyCode !== 13) {
                                    return;
                                }

                                if ([37, 38, 39, 40].includes(event.keyCode)) {
                                    return;
                                }
                                const $ct = event.currentTarget
                                clearTimeout(timeoutId); // doesn't matter if it's 0
                                timeoutId = setTimeout(function () {
                                    _this4.onSearch({ currentTarget: $ct });
                                }, _this4.options.searchTimeOut);
                            });

                        if (Utils.isIEBrowser()) {
                            $Event.on($Event.off($search, 'mouseup'), function (event) {
                                const $ct = event.currentTarget
                                clearTimeout(timeoutId); // doesn't matter if it's 0
                                timeoutId = setTimeout(function () {
                                    _this4.onSearch({ currentTarget: $ct });
                                }, _this4.options.searchTimeOut);
                            });
                        }
                    }
                }
            }, {
                key: 'onSearch',
                value: function onSearch(_ref7) {
                    var currentTarget = _ref7.currentTarget,
                        firedByInitSearchText = _ref7.firedByInitSearchText;

                    var text = currentTarget.value.trim();
                    console.log(text)
                    // trim search input
                    if (this.options.trimOnSearch && currentTarget.value !== text) {
                        currentTarget.value = text;
                    }

                    if (text === this.searchText) {
                        return;
                    }
                    this.searchText = text;
                    this.options.searchText = text;

                    if (!firedByInitSearchText) {
                        this.options.pageNumber = 1;
                    }

                    this.initSearch();

                    if (firedByInitSearchText) {
                        if (this.options.sidePagination === 'client') {
                            this.updatePagination();
                        }
                    } else {
                        this.updatePagination();
                    }
                    this.trigger('search', text);
                }
            }, {
                key: 'initSearch',
                value: function initSearch() {
                    var _this5 = this;


                    if (this.options.sidePagination !== 'server') {
                        if (this.options.customSearch !== Function.prototype) {

                            Utils.calculateObjectValue(this.options, this.options.customSearch, [this.searchText]);
                            return;
                        }

                        var s = this.searchText && (this.options.escape ? Utils.escapeHTML(this.searchText) : this.searchText).toLowerCase();
                        var f = Utils.isEmptyObject(this.filterColumns) ? null : this.filterColumns;


                        // Check filter
                        this.data = f ? this.options.data.filter(function (item) {
                            for (var key in f) {
                                if (Array.isArray(f[key]) && !f[key].includes(item[key]) || !Array.isArray(f[key]) && item[key] !== f[key]) {
                                    return false;
                                }
                            }
                            return true;
                        }) : this.options.data;

                        this.data = s ? this.data.filter(function (item, i) {
                            for (var j = 0; j < _this5.header.fields.length; j++) {
                                if (!_this5.header.searchables[j]) {
                                    continue;
                                }

                                var key = Utils.isNumeric(_this5.header.fields[j]) ? parseInt(_this5.header.fields[j], 10) : _this5.header.fields[j];
                                var column = _this5.columns[_this5.fieldsColumnsIndex[key]];
                                var value = void 0;

                                if (typeof key === 'string') {
                                    value = item;
                                    var props = key.split('.');
                                    for (var _i2 = 0; _i2 < props.length; _i2++) {
                                        if (value[props[_i2]] !== null) {
                                            value = value[props[_i2]];
                                        }
                                    }
                                } else {
                                    value = item[key];
                                }

                                // Fix #142: respect searchForamtter boolean
                                if (column && column.searchFormatter) {
                                    value = Utils.calculateObjectValue(column, _this5.header.formatters[j], [value, item, i], value);
                                }

                                if (typeof value === 'string' || typeof value === 'number') {
                                    if (_this5.options.strictSearch) {
                                        if (('' + value).toLowerCase() === s) {
                                            return true;
                                        }
                                    } else {
                                        if (('' + value).toLowerCase().includes(s)) {
                                            return true;
                                        }
                                    }
                                }
                            }
                            return false;
                        }) : this.data;
                    }
                }
            }, {
                key: 'initPagination',
                value: function initPagination() {
                    var _this6 = this;

                    if (!this.options.pagination) {
                        this.$pagination.style.display = 'none';
                        return;
                    }
                    this.$pagination.style.display = '';

                    var html = [];
                    var $allSelected = false;
                    var i = void 0;
                    var from = void 0;
                    var to = void 0;
                    var $pageList = void 0;
                    var $pre = void 0;
                    var $next = void 0;
                    var $number = void 0;
                    var data = this.getData();
                    var pageList = this.options.pageList;

                    if (this.options.sidePagination !== 'server') {
                        this.options.totalRows = data.length;
                    }

                    this.totalPages = 0;
                    if (this.options.totalRows) {
                        if (this.options.pageSize === this.options.formatAllRows()) {
                            this.options.pageSize = this.options.totalRows;
                            $allSelected = true;
                        } else if (this.options.pageSize === this.options.totalRows) {
                            // Fix #667 Table with pagination,
                            // multiple pages and a search this matches to one page throws exception
                            var pageLst = typeof this.options.pageList === 'string' ? this.options.pageList.replace('[', '').replace(']', '').replace(/ /g, '').toLowerCase().split(',') : this.options.pageList;
                            console.log(pageLst)
                            if (pageLst.includes(this.options.formatAllRows().toLowerCase())) {
                                $allSelected = true;
                            }
                        }

                        this.totalPages = ~~((this.options.totalRows - 1) / this.options.pageSize) + 1;

                        this.options.totalPages = this.totalPages;
                    }
                    if (this.totalPages > 0 && this.options.pageNumber > this.totalPages) {
                        this.options.pageNumber = this.totalPages;
                    }
                    this.pageFrom = (this.options.pageNumber - 1) * this.options.pageSize + 1;
                    this.pageTo = this.options.pageNumber * this.options.pageSize;
                    if (this.pageTo > this.options.totalRows) {
                        this.pageTo = this.options.totalRows;
                    }

                    html.push(Utils.sprintf('<div class="%s-%s pagination-detail">', CONSTANTS.classes.pull, this.options.paginationDetailHAlign), '<span class="pagination-info">', this.options.onlyInfoPagination ? this.options.formatDetailPagination(this.options.totalRows) : this.options.formatShowingRows(this.pageFrom, this.pageTo, this.options.totalRows), '</span>');

                    if (!this.options.onlyInfoPagination) {
                        html.push('<span class="page-list">');

                        var pageNumber = [Utils.sprintf('<span class="btn-group %s">', this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ? 'dropdown' : 'dropup'), '<button type="button" class="btn' + Utils.sprintf(' btn-%s', this.options.buttonsClass) + Utils.sprintf(' btn-%s', this.options.iconSize) + ' dropdown-toggle" data-bs-toggle="dropdown">', '<span class="page-size">', $allSelected ? this.options.formatAllRows() : this.options.pageSize, '</span>', ' <span class="caret"></span>', '</button>', CONSTANTS.html.pageDropdown[0]];

                        if (typeof this.options.pageList === 'string') {
                            var list = this.options.pageList.replace('[', '').replace(']', '').replace(/ /g, '').split(',');

                            pageList = [];
                            var _iteratorNormalCompletion8 = true;
                            var _didIteratorError8 = false;
                            var _iteratorError8 = undefined;

                            try {
                                for (var _iterator8 = list[Symbol.iterator](), _step8; !(_iteratorNormalCompletion8 = (_step8 = _iterator8.next()).done); _iteratorNormalCompletion8 = true) {
                                    var value = _step8.value;

                                    pageList.push(value.toUpperCase() === this.options.formatAllRows().toUpperCase() || value.toUpperCase() === 'UNLIMITED' ? this.options.formatAllRows() : +value);
                                }
                            } catch (err) {
                                _didIteratorError8 = true;
                                _iteratorError8 = err;
                            } finally {
                                try {
                                    if (!_iteratorNormalCompletion8 && _iterator8.return) {
                                        _iterator8.return();
                                    }
                                } finally {
                                    if (_didIteratorError8) {
                                        throw _iteratorError8;
                                    }
                                }
                            }
                        }

                        pageList.forEach(function (page, i) {
                            if (!_this6.options.smartDisplay || i === 0 || pageList[i - 1] < _this6.options.totalRows || page === _this6.options.formatAllRows()) {
                                var active = void 0;
                                if ($allSelected) {
                                    active = page === _this6.options.formatAllRows() ? 'active' : '';
                                } else {
                                    active = page === _this6.options.pageSize ? 'active' : '';
                                }
                                pageNumber.push(Utils.sprintf(CONSTANTS.html.pageDropdownItem, active, page));
                            }
                        });
                        pageNumber.push(CONSTANTS.html.pageDropdown[1] + '</span>');

                        html.push(this.options.formatRecordsPerPage(pageNumber.join('')));
                        html.push('</span>');

                        html.push('</div>', Utils.sprintf('<div class="%s-%s pagination">', CONSTANTS.classes.pull, this.options.paginationHAlign), '<ul class="pagination' + Utils.sprintf(' pagination-%s', this.options.iconSize) + '">', Utils.sprintf('<li class="page-item page-pre"><a class="page-link" href="#">%s</a></li>', this.options.paginationPreText));

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

                        if (this.totalPages >= 6) {
                            if (this.options.pageNumber >= 3) {
                                html.push(Utils.sprintf('<li class="page-item page-first%s">', this.options.pageNumber === 1 ? ' active' : ''), '<a class="page-link" href="#">', 1, '</a>', '</li>');

                                from++;
                            }

                            if (this.options.pageNumber >= 4) {
                                if (this.options.pageNumber === 4 || this.totalPages === 6 || this.totalPages === 7) {
                                    from--;
                                } else {
                                    html.push('<li class="page-item page-first-separator disabled">', '<a class="page-link" href="#">...</a>', '</li>');
                                }

                                to--;
                            }
                        }

                        if (this.totalPages >= 7) {
                            if (this.options.pageNumber >= this.totalPages - 2) {
                                from--;
                            }
                        }

                        if (this.totalPages === 6) {
                            if (this.options.pageNumber >= this.totalPages - 2) {
                                to++;
                            }
                        } else if (this.totalPages >= 7) {
                            if (this.totalPages === 7 || this.options.pageNumber >= this.totalPages - 3) {
                                to++;
                            }
                        }

                        for (i = from; i <= to; i++) {
                            html.push(Utils.sprintf('<li class="page-item%s">', i === this.options.pageNumber ? ' active' : ''), '<a class="page-link" href="#">', i, '</a>', '</li>');
                        }

                        if (this.totalPages >= 8) {
                            if (this.options.pageNumber <= this.totalPages - 4) {
                                html.push('<li class="page-item page-last-separator disabled">', '<a class="page-link" href="#">...</a>', '</li>');
                            }
                        }

                        if (this.totalPages >= 6) {
                            if (this.options.pageNumber <= this.totalPages - 3) {
                                html.push(Utils.sprintf('<li class="page-item page-last%s">', this.totalPages === this.options.pageNumber ? ' active' : ''), '<a class="page-link" href="#">', this.totalPages, '</a>', '</li>');
                            }
                        }

                        html.push(Utils.sprintf('<li class="page-item page-next"><a class="page-link" href="#">%s</a></li>', this.options.paginationNextText), '</ul>', '</div>');
                    }
                    this.$pagination.innerHTML = html.join('');

                    if (!this.options.onlyInfoPagination) {
                        $pageList = this.$pagination.querySelectorAll('.page-list a');
                        $pre = this.$pagination.querySelector('.page-pre');
                        $next = this.$pagination.querySelector('.page-next');
                        $number = [...this.$pagination.querySelectorAll('.page-item')].filter(function (el) { return !(el.classList.contains('page-next') || el.classList.contains('page-pre')) });
                        if (this.options.smartDisplay) {
                            if (this.totalPages <= 1) {
                                this.$pagination.querySelector('div.pagination').style.display = 'none';
                            }
                            if (pageList.length < 2 || this.options.totalRows <= pageList[0]) {
                                this.$pagination.querySelector('span.page-list').style.display = 'none';
                            }

                            // when data is empty, hide the pagination
                            this.$pagination.style.display = this.getData().length ? '' : 'none';
                        }

                        if (!this.options.paginationLoop) {
                            if (this.options.pageNumber === 1) {
                                $pre.classList.add('disabled');
                            }
                            if (this.options.pageNumber === this.totalPages) {
                                $next.classList.add('disabled');
                            }
                        }

                        if ($allSelected) {
                            this.options.pageSize = this.options.formatAllRows();
                        }
                        // removed the events for last and first, onPageNumber executeds the same logic
                        $pageList.forEach(function (page) {
                            $Event.on($Event.off(page, 'click'), 'click', _this6.onPageListChange.bind(_this6));
                        });

                        $Event.on($Event.off($pre, 'click'), 'click', this.onPagePre.bind(this));
                        $Event.on($Event.off($next, 'click'), 'click', this.onPageNext.bind(this));
                        $number.forEach(function (number) {
                            $Event.on($Event.off(number, 'click'), 'click', _this6.onPageNumber.bind(_this6));
                        });
                    }
                }
            }, {
                key: 'updatePagination',
                value: function updatePagination(event) {
                    // Fix #171: IE disabled button can be clicked bug.
                    if (event && event.currentTarget.classList.contains('disabled')) {
                        return;
                    }

                    if (!this.options.maintainSelected) {
                        this.resetRows();
                    }

                    this.initPagination();
                    if (this.options.sidePagination === 'server') {
                        this.initServer();
                    } else {
                        this.initBody();
                    }

                    this.trigger('page-change', this.options.pageNumber, this.options.pageSize);
                }
            }, {
                key: 'onPageListChange',
                value: function onPageListChange(event) {
                    event.preventDefault();
                    var $this = event.currentTarget;
                    $this.parentNode.classList.add('active');
                    ([...$this.parentNode.children] || []).filter((child) =>
                        child !== $this
                    ).forEach(c => c.classList.remove('active'));
                    // childrens.forEach(c => c.classList.remove('active'));

                    this.options.pageSize = $this.textContent.toUpperCase() === this.options.formatAllRows().toUpperCase() ? this.options.formatAllRows() : +$this.textContent;
                    this.$pagination.querySelector('.page-size').textContent = this.options.pageSize;

                    this.updatePagination(event);
                    return false;
                }
            }, {
                key: 'onPagePre',
                value: function onPagePre(event) {
                    event.preventDefault();
                    if (this.options.pageNumber - 1 === 0) {
                        this.options.pageNumber = this.options.totalPages;
                    } else {
                        this.options.pageNumber--;
                    }
                    this.updatePagination(event);
                    return false;
                }
            }, {
                key: 'onPageNext',
                value: function onPageNext(event) {
                    event.preventDefault();
                    if (this.options.pageNumber + 1 > this.options.totalPages) {
                        this.options.pageNumber = 1;
                    } else {
                        this.options.pageNumber++;
                    }
                    this.updatePagination(event);
                    return false;
                }
            }, {
                key: 'onPageNumber',
                value: function onPageNumber(event) {
                    event.preventDefault();
                    if (this.options.pageNumber === +event.currentTarget.textContent) {
                        return;
                    }
                    this.options.pageNumber = +event.currentTarget.textContent;
                    this.updatePagination(event);
                    return false;
                }
                // }, {
                //     key: 'initTr',
                //     value: function initTr(item, idx, data, parentDom) {
                //         var that = this, _rowStyle = that.options.rowStyle;
                //         var nodes = that.options.onGetNodes.apply(that, [item, data]);
                //         item._nodes = nodes;
                //         parentDom.append(that.initRow.apply(that, [item, idx, data, parentDom]));
                //         // init sub node
                //         var len = nodes.length - 1;
                //         for (var i = 0; i <= len; i++) {
                //             var node = nodes[i];
                //             node._level = item._level + 1;
                //             node._parent = item;
                //             if (i === len) node._last = 1;
                //             // jquery.treegrid.js
                //             that.options.rowStyle = function (item, idx) {
                //                 var res = _rowStyle.apply(that, Array.prototype.slice.apply(arguments));
                //                 var id = item[that.options.idField] ? item[that.options.idField] : 0;
                //                 var pid = item[that.options.parentIdField] ? item[that.options.parentIdField] : 0;
                //                 res.classes = [res.classes || '', 'treegrid-' + id, 'treegrid-parent-' + pid].join(' ');
                //                 return res;
                //             };
                //             _this7.initTr.apply(that, [node, $.inArray(node, data), data, parentDom]);
                //         }
                // }
            }, {
                key: 'initRow',
                value: function initRow(item, i, data, parentDom) {
                    var _this7 = this;

                    var html = [];
                    var style = {};
                    var csses = [];
                    var data_ = '';
                    var attributes = {};
                    var htmlAttributes = [], _rowStyle = _this7.options.rowStyle;
                    //tree begin
                    // if (_this7.treeEnable) {
                    //     // init root node
                    //     if (_this7.options.onCheckRoot.apply(_this7, [item, data])) {
                    //         if (item._level === undefined) {
                    //             item._level = 0;
                    //         }
                    //         // jquery.treegrid.js
                    //         _this7.options.rowStyle = function (item) {
                    //             var res = _rowStyle.apply(_this7, Array.prototype.slice.apply(arguments));
                    //             var x = item[_this7.options.idField] ? item[_this7.options.idField] : 0;
                    //             res.classes = [res.classes || '', 'treegrid-' + x].join(' ');
                    //             return res;
                    //         };
                    //         _this7.initTr.apply(_this7, [item, i, data, parentDom]);

                    //         return true;
                    //     }
                    //     return false;


                    // };
                    //end

                    if (this.hiddenRows.includes(item)) {
                        return;
                    }

                    style = Utils.calculateObjectValue(this.options, this.options.rowStyle, [item, i], style);

                    if (style && style.css) {
                        var _iteratorNormalCompletion9 = true;
                        var _didIteratorError9 = false;
                        var _iteratorError9 = undefined;

                        try {
                            for (var _iterator9 = Object.entries(style.css)[Symbol.iterator](), _step9; !(_iteratorNormalCompletion9 = (_step9 = _iterator9.next()).done); _iteratorNormalCompletion9 = true) {
                                var _ref8 = _step9.value;

                                var _ref9 = _slicedToArray(_ref8, 2);

                                var key = _ref9[0];
                                var value = _ref9[1];

                                csses.push(key + ': ' + value);
                            }
                        } catch (err) {
                            _didIteratorError9 = true;
                            _iteratorError9 = err;
                        } finally {
                            try {
                                if (!_iteratorNormalCompletion9 && _iterator9.return) {
                                    _iterator9.return();
                                }
                            } finally {
                                if (_didIteratorError9) {
                                    throw _iteratorError9;
                                }
                            }
                        }
                    }

                    attributes = Utils.calculateObjectValue(this.options, this.options.rowAttributes, [item, i], attributes);

                    if (attributes) {
                        var _iteratorNormalCompletion10 = true;
                        var _didIteratorError10 = false;
                        var _iteratorError10 = undefined;

                        try {
                            for (var _iterator10 = Object.entries(attributes)[Symbol.iterator](), _step10; !(_iteratorNormalCompletion10 = (_step10 = _iterator10.next()).done); _iteratorNormalCompletion10 = true) {
                                var _ref10 = _step10.value;

                                var _ref11 = _slicedToArray(_ref10, 2);

                                var _key2 = _ref11[0];
                                var _value2 = _ref11[1];

                                htmlAttributes.push(_key2 + '="' + Utils.escapeHTML(_value2) + '"');
                            }
                        } catch (err) {
                            _didIteratorError10 = true;
                            _iteratorError10 = err;
                        } finally {
                            try {
                                if (!_iteratorNormalCompletion10 && _iterator10.return) {
                                    _iterator10.return();
                                }
                            } finally {
                                if (_didIteratorError10) {
                                    throw _iteratorError10;
                                }
                            }
                        }
                    }

                    if (item._data && !Utils.isEmptyObject(item._data)) {
                        var _iteratorNormalCompletion11 = true;
                        var _didIteratorError11 = false;
                        var _iteratorError11 = undefined;

                        try {
                            for (var _iterator11 = Object.entries(item._data)[Symbol.iterator](), _step11; !(_iteratorNormalCompletion11 = (_step11 = _iterator11.next()).done); _iteratorNormalCompletion11 = true) {
                                var _ref12 = _step11.value;

                                var _ref13 = _slicedToArray(_ref12, 2);

                                var k = _ref13[0];
                                var v = _ref13[1];

                                // ignore data-index
                                if (k === 'index') {
                                    return;
                                }
                                data_ += ' data-' + k + '="' + v + '"';
                            }
                        } catch (err) {
                            _didIteratorError11 = true;
                            _iteratorError11 = err;
                        } finally {
                            try {
                                if (!_iteratorNormalCompletion11 && _iterator11.return) {
                                    _iterator11.return();
                                }
                            } finally {
                                if (_didIteratorError11) {
                                    throw _iteratorError11;
                                }
                            }
                        }
                    }

                    html.push('<tr', Utils.sprintf(' %s', htmlAttributes.length ? htmlAttributes.join(' ') : undefined), Utils.sprintf(' id="%s"', Array.isArray(item) ? undefined : item._id), Utils.sprintf(' class="%s"', style.classes || (Array.isArray(item) ? undefined : item._class)), ' data-index="' + i + '"', Utils.sprintf(' data-uniqueid="%s"', item[this.options.uniqueId]), Utils.sprintf('%s', data_), '>');

                    if (this.options.cardView) {
                        html.push('<td colspan="' + this.header.fields.length + '"><div class="card-views">');
                    }

                    if (!this.options.cardView && this.options.detailView) {
                        html.push('<td>');

                        if (Utils.calculateObjectValue(null, this.options.detailFilter, [i, item])) {
                            html.push('\n            <a class="detail-icon" href="#">\n            <i class="' + this.options.iconsPrefix + ' ' + this.options.icons.detailOpen + '"></i>\n            </a>\n          ');
                        }

                        html.push('</td>');
                    }

                    this.header.fields.forEach(function (field, j) {
                        var text = '';
                        var value_ = Utils.getItemField(item, field, _this7.options.escape);
                        var value = '';
                        var type = '';
                        var cellStyle = {};
                        var id_ = '';
                        var class_ = _this7.header.classes[j];
                        var style_ = '';
                        var data_ = '';
                        var rowspan_ = '';
                        var colspan_ = '';
                        var title_ = '';
                        var column = _this7.columns[j];

                        if (_this7.fromHtml && typeof value_ === 'undefined') {
                            if (!column.checkbox && !column.radio) {
                                return;
                            }
                        }

                        if (!column.visible) {
                            return;
                        }

                        if (_this7.options.cardView && !column.cardVisible) {
                            return;
                        }

                        if (column.escape) {
                            value_ = Utils.escapeHTML(value_);
                        }

                        if (csses.concat([_this7.header.styles[j]]).length) {
                            style_ = ' style="' + csses.concat([_this7.header.styles[j]]).join('; ') + '"';
                        }
                        // handle td's id and class
                        if (item['_' + field + '_id']) {
                            id_ = Utils.sprintf(' id="%s"', item['_' + field + '_id']);
                        }
                        if (item['_' + field + '_class']) {
                            class_ = Utils.sprintf(' class="%s"', item['_' + field + '_class']);
                        }
                        if (item['_' + field + '_rowspan']) {
                            rowspan_ = Utils.sprintf(' rowspan="%s"', item['_' + field + '_rowspan']);
                        }
                        if (item['_' + field + '_colspan']) {
                            colspan_ = Utils.sprintf(' colspan="%s"', item['_' + field + '_colspan']);
                        }
                        if (item['_' + field + '_title']) {
                            title_ = Utils.sprintf(' title="%s"', item['_' + field + '_title']);
                        }
                        cellStyle = Utils.calculateObjectValue(_this7.header, _this7.header.cellStyles[j], [value_, item, i, field], cellStyle);
                        if (cellStyle.classes) {
                            class_ = ' class="' + cellStyle.classes + '"';
                        }
                        if (cellStyle.css) {
                            var csses_ = [];
                            var _iteratorNormalCompletion12 = true;
                            var _didIteratorError12 = false;
                            var _iteratorError12 = undefined;

                            try {
                                for (var _iterator12 = Object.entries(cellStyle.css)[Symbol.iterator](), _step12; !(_iteratorNormalCompletion12 = (_step12 = _iterator12.next()).done); _iteratorNormalCompletion12 = true) {
                                    var _ref14 = _step12.value;

                                    var _ref15 = _slicedToArray(_ref14, 2);

                                    var _key3 = _ref15[0];
                                    var _value3 = _ref15[1];

                                    csses_.push(_key3 + ': ' + _value3);
                                }
                            } catch (err) {
                                _didIteratorError12 = true;
                                _iteratorError12 = err;
                            } finally {
                                try {
                                    if (!_iteratorNormalCompletion12 && _iterator12.return) {
                                        _iterator12.return();
                                    }
                                } finally {
                                    if (_didIteratorError12) {
                                        throw _iteratorError12;
                                    }
                                }
                            }

                            style_ = ' style="' + csses_.concat(_this7.header.styles[j]).join('; ') + '"';
                        }

                        value = Utils.calculateObjectValue(column, _this7.header.formatters[j], [value_, item, i, field], value_);

                        if (item['_' + field + '_data'] && !$.isEmptyObject(item['_' + field + '_data'])) {
                            var _iteratorNormalCompletion13 = true;
                            var _didIteratorError13 = false;
                            var _iteratorError13 = undefined;

                            try {
                                for (var _iterator13 = Object.entries(item['_' + field + '_data'])[Symbol.iterator](), _step13; !(_iteratorNormalCompletion13 = (_step13 = _iterator13.next()).done); _iteratorNormalCompletion13 = true) {
                                    var _ref16 = _step13.value;

                                    var _ref17 = _slicedToArray(_ref16, 2);

                                    var _k2 = _ref17[0];
                                    var _v = _ref17[1];

                                    // ignore data-index
                                    if (_k2 === 'index') {
                                        return;
                                    }
                                    data_ += ' data-' + _k2 + '="' + _v + '"';
                                }
                            } catch (err) {
                                _didIteratorError13 = true;
                                _iteratorError13 = err;
                            } finally {
                                try {
                                    if (!_iteratorNormalCompletion13 && _iterator13.return) {
                                        _iterator13.return();
                                    }
                                } finally {
                                    if (_didIteratorError13) {
                                        throw _iteratorError13;
                                    }
                                }
                            }
                        }

                        if (column.checkbox || column.radio) {
                            type = column.checkbox ? 'checkbox' : type;
                            type = column.radio ? 'radio' : type;

                            var c = column['className'] || '';
                            var isChecked = value === true || value_ || value && value.checked;
                            var isDisabled = !column.checkboxEnabled || value && value.disabled;

                            text = [_this7.options.cardView ? '<div class="card-view ' + c + '">' : '<td class="bs-checkbox ' + c + '">', '<input\n              data-index="' + i + '"\n              name="' + _this7.options.selectItemName + '"\n              type="' + type + '"\n              ' + Utils.sprintf('value="%s"', item[_this7.options.idField]) + '\n              ' + Utils.sprintf('checked="%s"', isChecked ? 'checked' : undefined) + '\n              ' + Utils.sprintf('disabled="%s"', isDisabled ? 'disabled' : undefined) + ' />', _this7.header.formatters[j] && typeof value === 'string' ? value : '', _this7.options.cardView ? '</div>' : '</td>'].join('');

                            item[_this7.header.stateField] = value === true || !!value_ || value && value.checked;
                        } else {
                            value = typeof value === 'undefined' || value === null ? _this7.options.undefinedText : value;

                            if (_this7.options.cardView) {
                                var cardTitle = _this7.options.showHeader ? '<span class="title"' + style + '>' + Utils.getFieldTitle(_this7.columns, field) + '</span>' : '';

                                text = '<div class="card-view">' + cardTitle + '<span class="value">' + value + '</span></div>';

                                if (_this7.options.smartDisplay && value === '') {
                                    text = '<div class="card-view"></div>';
                                }
                            } else {
                                text = '<td' + id_ + class_ + style_ + data_ + rowspan_ + colspan_ + title_ + '>' + value + '</td>';
                            }
                        }

                        html.push(text);
                    });

                    if (this.options.cardView) {
                        html.push('</div></td>');
                    }
                    html.push('</tr>');

                    return html.join('');

                }
            }, {
                key: 'initBody',
                value: function initBody(fixedScroll) {
                    var _this8 = this;

                    var data = this.getData();

                    this.trigger('pre-body', data);

                    this.$body = this.$el.querySelector('tbody');
                    if (!this.$body) {
                        this.$body = document.createElement('tbody')
                        this.$el.appendChild(this.$body);
                    }

                    // Fix #389 Bootstrap-table-flatJSON is not working
                    if (!this.options.pagination || this.options.sidePagination === 'server') {
                        this.pageFrom = 1;
                        this.pageTo = data.length;
                    }

                    var trFragments = document.createDocumentFragment();
                    var hasTr = false;

                    for (var i = this.pageFrom - 1; i < this.pageTo; i++) {
                        var item = data[i];
                        var tr = this.initRow(item, i, data, trFragments);
                        hasTr = hasTr || !!tr;
                        if (tr && typeof tr === 'string') {
                            trFragments.append(tr);
                        }
                    }

                    // show no records
                    if (!hasTr) {
                        this.$body.innerHTML = '<tr class="no-records-found">' + Utils.sprintf('<td colspan="%s">%s</td>', this.$header.querySelectorAll('th').length, this.options.formatNoMatches()) + '</tr>';
                    } else {
                        this.$body.innerHTML = trFragments.textContent;
                    }

                    if (!fixedScroll) {
                        this.scrollTo(0);
                    }

                    // click to select by column
                    this.$body.querySelectorAll(' tr[data-index] > td').forEach(td => {
                        $Event.on($Event.off(td, 'click dblclick'), 'click dblclick', function (_ref18) {
                            var currentTarget = _ref18.currentTarget,
                                type = _ref18.type,
                                target = _ref18.target;

                            var $td = currentTarget;// document.querySelector(currentTarget);
                            var $tr = $td.parentNode;
                            var item = _this8.data[$tr.dataset['index']];
                            var index = $td.cellIndex;
                            var fields = _this8.getVisibleFields();
                            var field = fields[_this8.options.detailView && !_this8.options.cardView ? index - 1 : index];
                            var column = _this8.columns[_this8.fieldsColumnsIndex[field]];
                            var value = Utils.getItemField(item, field, _this8.options.escape);

                            if ($td.querySelectorAll('.detail-icon').length) {
                                return;
                            }

                            _this8.trigger(type === 'click' ? 'click-cell' : 'dbl-click-cell', field, value, item, $td);
                            _this8.trigger(type === 'click' ? 'click-row' : 'dbl-click-row', item, $tr, field);

                            // if click to select - then trigger the checkbox/radio click
                            if (type === 'click' && _this8.options.clickToSelect && column.clickToSelect && !_this8.options.ignoreClickToSelectOn(target)) {
                                var $selectItem = $tr.querySelectorAll(Utils.sprintf('[name="%s"]', _this8.options.selectItemName));
                                if ($selectItem.length) {
                                    $selectItem[0].click(); // #144: .trigger('click') bug
                                }
                            }
                        })
                    });

                    this.$body.querySelectorAll(' tr[data-index] > td > .detail-icon').forEach(item => {
                        $Event.on($Event.off(item, 'click'), 'click', function (e) {
                            e.preventDefault();

                            var $this = document.querySelector(e.currentTarget); // Fix #980 Detail view, when searching, returns wrong row
                            var $tr = $this.parentNode.parentNode;
                            var index = $tr.dataset['index'];
                            var row = data[index];

                            // remove and update
                            if ($tr.nextElementSibling.matches('tr.detail-view')) {
                                $this.querySelectorAll('i').forEach(v => v.classList.add(Utils.sprintf('%s %s', _this8.options.iconsPrefix, _this8.options.icons.detailOpen)));
                                _this8.trigger('collapse-row', index, row, $tr.nextElementSibling);
                                $tr.nextElementSibling.remove();
                            } else {
                                $this.find('i').attr('className', Utils.sprintf('%s %s', _this8.options.iconsPrefix, _this8.options.icons.detailClose));
                                $tr.after(Utils.sprintf('<tr class="detail-view"><td colspan="%s"></td></tr>', $tr.querySelectorAll('td').length));
                                var $element = $tr.nextElementSibling.querySelectorAll('td');
                                var content = Utils.calculateObjectValue(_this8.options, _this8.options.detailFormatter, [index, row, $element], '');
                                if ($element.length === 1) {
                                    $element.append(content);
                                }
                                _this8.trigger('expand-row', index, row, $element);
                            }
                            _this8.resetView();
                            return false;
                        })
                    }
                    );

                    this.$selectItem = this.$body.querySelectorAll(Utils.sprintf('[name="%s"]', this.options.selectItemName));
                    this.$selectItem.forEach(item => {
                        $Event.on($Event.off(item, 'click'), 'click', function (e) {
                            e.stopImmediatePropagation();

                            var $this = $(e.currentTarget);
                            _this8.check_($this['checked'], $this.dataset['index']);
                        });
                    });
                    this.header.events.forEach(function (_events, i) {
                        var events = _events;
                        if (!events) {
                            return;
                        }
                        // fix bug, if events is defined with namespace
                        if (typeof events === 'string') {
                            events = Utils.calculateObjectValue(null, events);
                        }

                        var field = _this8.header.fields[i];
                        var fieldIndex = _this8.getVisibleFields().indexOf(field);

                        if (fieldIndex === -1) {
                            return;
                        }

                        if (_this8.options.detailView && !_this8.options.cardView) {
                            fieldIndex += 1;
                        }

                        var _loop = function _loop(key, event) {
                            _this8.$body.querySelectorAll('tr:not(.no-records-found)').forEach(function (tr, I) {
                                var $tr = tr;
                                var $td = $tr.querySelector(_this8.options.cardView ? '.card-view' : 'td')[fieldIndex];
                                var index = key.indexOf(' ');
                                var name = key.substring(0, index);
                                var el = key.substring(index + 1);

                                $td.querySelectorAll(el).forEach(item => {
                                    $Event.on($Event.off(item, name), name, name, function (e) {
                                        var index = $tr.dataset['index'];
                                        var row = _this8.data[index];
                                        var value = row[field];

                                        event.apply(_this8, [e, value, row, index]);
                                    });
                                });
                            })
                        }


                        var _iteratorNormalCompletion14 = true;
                        var _didIteratorError14 = false;
                        var _iteratorError14 = undefined;

                        try {
                            for (var _iterator14 = Object.entries(events)[Symbol.iterator](), _step14; !(_iteratorNormalCompletion14 = (_step14 = _iterator14.next()).done); _iteratorNormalCompletion14 = true) {
                                var _ref19 = _step14.value;

                                var _ref20 = _slicedToArray(_ref19, 2);

                                var key = _ref20[0];
                                var event = _ref20[1];

                                _loop(key, event);
                            }
                        } catch (err) {
                            _didIteratorError14 = true;
                            _iteratorError14 = err;
                        } finally {
                            try {
                                if (!_iteratorNormalCompletion14 && _iterator14.return) {
                                    _iterator14.return();
                                }
                            } finally {
                                if (_didIteratorError14) {
                                    throw _iteratorError14;
                                }
                            }
                        }

                    });
                    this.updateSelected();
                    this.resetView();

                    this.trigger('post-body', data);
                }
            }, {
                key: 'initServer',
                value: function initServer(silent, query, url) {
                    var _this9 = this;

                    var data = {};
                    var index = this.header.fields.indexOf(this.options.sortName);

                    var params = {
                        searchText: this.searchText,
                        sortName: this.options.sortName,
                        sortOrder: this.options.sortOrder
                    };

                    if (this.header.sortNames[index]) {
                        params.sortName = this.header.sortNames[index];
                    }

                    if (this.options.pagination && this.options.sidePagination === 'server') {
                        params.pageSize = this.options.pageSize === this.options.formatAllRows() ? this.options.totalRows : this.options.pageSize;
                        params.pageNumber = this.options.pageNumber;
                    }

                    if (!(url || this.options.url) && !this.options.ajax) {
                        return;
                    }

                    if (this.options.queryParamsType === 'limit') {
                        params = {
                            search: params.searchText,
                            sort: params.sortName,
                            order: params.sortOrder
                        };

                        if (this.options.pagination && this.options.sidePagination === 'server') {
                            params.offset = this.options.pageSize === this.options.formatAllRows() ? 0 : this.options.pageSize * (this.options.pageNumber - 1);
                            params.limit = this.options.pageSize === this.options.formatAllRows() ? this.options.totalRows : this.options.pageSize;
                            if (params.limit === 0) {
                                delete params.limit;
                            }
                        }
                    }

                    if (!Utils.isEmptyObject(this.filterColumnsPartial)) {
                        params.filter = JSON.stringify(this.filterColumnsPartial, null);
                    }

                    data = Utils.calculateObjectValue(this.options, this.options.queryParams, [params], data);

                    Object.assign(data, query || {});

                    // false to stop request
                    if (data === false) {
                        return;
                    }

                    if (!silent) {
                        this.$tableLoading.show();
                    }
                    var request = Object.assign({}, Utils.calculateObjectValue(null, this.options.ajaxOptions), {
                        type: this.options.method,
                        url: url || this.options.url,
                        data: this.options.contentType === 'application/json' && this.options.method === 'post' ? JSON.stringify(data) : data,
                        cache: this.options.cache,
                        contentType: this.options.contentType,
                        dataType: this.options.dataType,
                        success: function success(_res) {
                            var res = Utils.calculateObjectValue(_this9.options, _this9.options.responseHandler, [_res], _res);

                            _this9.innerHTML = res;
                            _this9.trigger('load-success', res);
                            if (!silent) _this9.$tableLoading.style.display = 'none';
                        },
                        error: function error(res) {
                            var data = [];
                            if (_this9.options.sidePagination === 'server') {
                                data = {};
                                data[_this9.options.totalField] = 0;
                                data[_this9.options.dataField] = [];
                            }
                            _this9.load(data);
                            _this9.trigger('load-error', res.status, res);
                            if (!silent) _this9.$tableLoading.style.display = 'none';
                        }
                    });

                    if (this.options.ajax) {
                        Utils.calculateObjectValue(this, this.options.ajax, [request], null);
                    } else {
                        if (this._xhr && this._xhr.readyState !== 4) {
                            this._xhr.abort();
                        }
                        this._xhr = $.ajax(request);
                    }
                }
            }, {
                key: 'initSearchText',
                value: function initSearchText() {
                    if (this.options.search) {
                        this.searchText = '';
                        if (this.options.searchText !== '') {
                            var $search = this.$toolbar.querySelector('.search input');
                            $search.value = this.options.searchText;
                            this.onSearch({ currentTarget: $search, firedByInitSearchText: true });
                        }
                    }
                }
            }, {
                key: 'getCaret',
                value: function getCaret() {
                    var _this10 = this;

                    this.$header.querySelectorAll('th').forEach(function (th, i) {
                        th.querySelectorAll('.sortable').forEach(item => {
                            item.classList.remove('desc', 'asc')
                            item.classList.add(th.dataset['field'] === _this10.options.sortName ? _this10.options.sortOrder : 'both');
                        });
                    })
                }
            }, {
                key: 'updateSelected',
                value: function updateSelected() {
                    var $sel = [...this.$selectItem].filter((w) => w.disabled === false);
                    var checkAll = $sel.length && $sel.length === $sel.filter((w) => w.disabled === false).filter((w) => w.checked === true).length;

                    this.$selectAll.forEach(t => t['checked'] = checkAll);
                    this.$selectAll_?.forEach(t => t['checked'] = checkAll); //(datas || []).forEach
                    this.$selectItem.forEach(function (el) {
                        el.closest('tr').classList[el['checked'] ? 'add' : 'remove']('selected');
                    });
                }
            }, {
                key: 'updateRows',
                value: function updateRows() {
                    var _this11 = this;

                    this.$selectItem.forEach(function (el) {
                        _this11.data[el.dataset['index']][_this11.header.stateField] = el['checked'];
                    });
                }
            }, {
                key: 'resetRows',
                value: function resetRows() {
                    var _iteratorNormalCompletion15 = true;
                    var _didIteratorError15 = false;
                    var _iteratorError15 = undefined;

                    try {
                        for (var _iterator15 = this.data[Symbol.iterator](), _step15; !(_iteratorNormalCompletion15 = (_step15 = _iterator15.next()).done); _iteratorNormalCompletion15 = true) {
                            var row = _step15.value;

                            this.$selectAll.forEach(function (el) { el['checked'] = false });
                            this.$selectItem.forEach(function (el) { el['checked'] = false })
                            if (this.header.stateField) {
                                row[this.header.stateField] = false;
                            }
                        }
                    } catch (err) {
                        _didIteratorError15 = true;
                        _iteratorError15 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion15 && _iterator15.return) {
                                _iterator15.return();
                            }
                        } finally {
                            if (_didIteratorError15) {
                                throw _iteratorError15;
                            }
                        }
                    }

                    this.initHiddenRows();
                }
            }, {
                key: 'trigger',
                value: function trigger(_name) {
                    var _options;

                    var name = _name + '.bs.table';

                    for (var _len2 = arguments.length, args = Array(_len2 > 1 ? _len2 - 1 : 0), _key4 = 1; _key4 < _len2; _key4++) {
                        args[_key4 - 1] = arguments[_key4];
                    }

                    (_options = this.options)[BootstrapTable.EVENTS[name]].apply(_options, args);
                    // this.$el.trigger($.Event(name), args);
                    $Event.trigger(this.$el, name, args);
                    this.options.onAll(name, args);
                    $Event.trigger(this.$el, 'all.bs.table', [name, args]);
                }
            }, {
                key: 'resetHeader',
                value: function resetHeader() {
                    // fix #61: the hidden table reset header bug.
                    // fix bug: get $el.css('width') error sometime (height = 500)
                    clearTimeout(this.timeoutId_);
                    this.timeoutId_ = setTimeout(this.fitHeader.bind(this), this.$el.matches(':hidden') ? 100 : 0);
                }
            }, {
                key: 'fitHeader',
                value: function fitHeader() {
                    var _this12 = this;

                    if (this.$el.matches(':hidden')) {
                        this.timeoutId_ = setTimeout(this.fitHeader.bind(this), 100);
                        return;
                    }
                    var fixedBody = this.$tableBody;

                    var scrollWidth = fixedBody.scrollWidth > fixedBody.clientWidth && fixedBody.scrollHeight > fixedBody.clientHeight + this.$header.outerHeight() ? Utils.getScrollBarWidth() : 0;

                    this.$el.style.marginTop = -this.$header.outerHeight();
                    var focused = document.querySelectorAll(':focus');
                    focused.forEach(elem => {
                        let $th = Utils.parents(elem, 'th');
                        $th.forEach(elem => {
                            var dataField = $th['data-field'];
                            if (dataField !== undefined) {
                                var $headerTh = this.$header.querySelector('[data-field=\'' + dataField + '\']');
                                $headerTh.forEach(th => {
                                    th.querySelector(':input').classList.add('focus-temp');
                                })
                            }
                        })
                    })
                    this.$header_ = this.$header, cloneNode(true);
                    this.$selectAll_ = this.$header_.querySelectorAll('[name="btSelectAll"]');
                    this.$tableHeader.style.marginRight = scrollWidth
                    let $tab = this.$tableHeader.querySelector('table')
                    $tab.style.width = this.$el.outerWidth
                    $tab.innerHTML = ''
                    $tab['className'] = this.$el['className']
                    $tab.append(this.$header_);

                    var focusedTemp = document.querySelectorAll('.focus-temp');
                    focusedTemp = [...focusedTemp].filter(el => el.visible)
                    if (focusedTemp.length > 0) {
                        focusedTemp[0].focus();
                        [...this.$header.querySelectorAll('.focus-temp')].forEach(el => el.classList.remove('focus-temp'));
                    }

                    // fix bug: $.data() is not working as expected after $.append()
                    this.$header.querySelectorAll('th[data-field]').forEach(function (el) {
                        _this12.$header_.querySelector(Utils.sprintf('th[data-field="%s"]', el.dataset['field'])).dataset[el.dataset];
                    });

                    var visibleFields = this.getVisibleFields();
                    var $ths = this.$header_.querySelectorAll('th');

                    this.$body.querySelectorAll('tr').forEach(function (el) {
                        if (el.firstChild.classList.contains(no - records - found)) {
                            el.firstChild.childrens.forEach(function (el, i) {
                                var $this = el;
                                var index = i;

                                if (_this12.options.detailView && !_this12.options.cardView) {
                                    if (i === 0) {
                                        _this12.$header_.querySelectorAll('th.detail').forEach(function (el) {
                                            el.querySelectorAll('.fht-cell').forEach(e => e.style.width = $this.innerWidth() + 'px')
                                        });
                                    }
                                    index = i - 1;
                                }

                                if (index === -1) {
                                    return;
                                }

                                var $th = _this12.$header_.querySelectorAll(Utils.sprintf('th[data-field="%s"]', visibleFields[index]));
                                if ($th.length > 1) {
                                    $th = $ths[$this[0].cellIndex];
                                }

                                var zoomWidth = $th.style.width - $th.querySelector('.fht-cell').style.width;
                                $th.querySelector('.fht-cell').style.width = $this.innerWidth() - zoomWidth;
                            });

                            this.horizontalScroll();
                            this.trigger('post-header');
                        }
                    })
                }
            }, {
                key: 'resetFooter',
                value: function resetFooter() {
                    var data = this.getData();
                    var html = [];

                    if (!this.options.showFooter || this.options.cardView) {
                        // do nothing
                        return;
                    }

                    if (!this.options.cardView && this.options.detailView) {
                        html.push('<td><div class="th-inner">&nbsp;</div><div class="fht-cell"></div></td>');
                    }

                    var _iteratorNormalCompletion16 = true;
                    var _didIteratorError16 = false;
                    var _iteratorError16 = undefined;

                    try {
                        for (var _iterator16 = this.columns[Symbol.iterator](), _step16; !(_iteratorNormalCompletion16 = (_step16 = _iterator16.next()).done); _iteratorNormalCompletion16 = true) {
                            var column = _step16.value;

                            var falign = '';

                            var valign = '';
                            var csses = [];
                            var style = {};
                            var class_ = Utils.sprintf(' class="%s"', column['className']);

                            if (!column.visible) {
                                return;
                            }

                            if (this.options.cardView && !column.cardVisible) {
                                return;
                            }

                            falign = Utils.sprintf('text-align: %s; ', column.falign ? column.falign : column.align);
                            valign = Utils.sprintf('vertical-align: %s; ', column.valign);

                            style = Utils.calculateObjectValue(null, this.options.footerStyle);

                            if (style && style.css) {
                                var _iteratorNormalCompletion17 = true;
                                var _didIteratorError17 = false;
                                var _iteratorError17 = undefined;

                                try {
                                    for (var _iterator17 = Object.keys(style.css)[Symbol.iterator](), _step17; !(_iteratorNormalCompletion17 = (_step17 = _iterator17.next()).done); _iteratorNormalCompletion17 = true) {
                                        var _ref21 = _step17.value;

                                        var _ref22 = _slicedToArray(_ref21, 2);

                                        var key = _ref22[0];
                                        var value = _ref22[1];

                                        csses.push(key + ': ' + value);
                                    }
                                } catch (err) {
                                    _didIteratorError17 = true;
                                    _iteratorError17 = err;
                                } finally {
                                    try {
                                        if (!_iteratorNormalCompletion17 && _iterator17.return) {
                                            _iterator17.return();
                                        }
                                    } finally {
                                        if (_didIteratorError17) {
                                            throw _iteratorError17;
                                        }
                                    }
                                }
                            }

                            html.push('<td', class_, Utils.sprintf(' style="%s"', falign + valign + csses.concat().join('; ')), '>');
                            html.push('<div class="th-inner">');

                            html.push(Utils.calculateObjectValue(column, column.footerFormatter, [data], '&nbsp;') || '&nbsp;');

                            html.push('</div>');
                            html.push('<div class="fht-cell"></div>');
                            html.push('</div>');
                            html.push('</td>');
                        }
                    } catch (err) {
                        _didIteratorError16 = true;
                        _iteratorError16 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion16 && _iterator16.return) {
                                _iterator16.return();
                            }
                        } finally {
                            if (_didIteratorError16) {
                                throw _iteratorError16;
                            }
                        }
                    }

                    this.$tableFooter.querySelector('tr').innerHTML = html.join('');
                    this.$tableFooter.style.display = '';
                    clearTimeout(this.timeoutFooter_);
                    this.timeoutFooter_ = setTimeout(this.fitFooter.bind(this), this.$el.matches(':hidden') ? 100 : 0);
                }
            }, {
                key: 'fitFooter',
                value: function fitFooter() {
                    clearTimeout(this.timeoutFooter_);
                    if (this.$el.matches(':hidden')) {
                        this.timeoutFooter_ = setTimeout(this.fitFooter.bind(this), 100);
                        return;
                    }

                    var elWidth = this.$el.style.width;
                    var scrollWidth = elWidth > this.$tableBody.style.width ? Utils.getScrollBarWidth() : 0;

                    this.$tableFooter.style.marginRight = scrollWidth

                    this.$tableFooter.querySelector('table').style.width = elWidth
                    this.$tableFooter.querySelector('table')['className'] = this.$el['className'];

                    var $footerTd = this.$tableFooter.querySelectorAll('td');

                    this.$body.querySelectorAll('tr').forEach(function (el) {
                        if (el.firstChild.classList.contains(no - records - found)) {
                            el.firstChild.childrens.forEach(function (el, i) {
                                var $this = el;

                                $footerTd[i].querySelector('.fht-cell').style.width = $this.innerWidth();
                            })
                        }
                    }
                    );

                    this.horizontalScroll();
                }
            }, {
                key: 'horizontalScroll',
                value: function horizontalScroll() {
                    var _this13 = this;

                    // horizontal scroll event
                    // TODO: it's probably better improving the layout than binding to scroll event

                    this.trigger('scroll-body');
                    $Event.on($Event.off(this.$tableBody, 'scroll'), 'scroll', function (_ref23) {
                        var currentTarget = _ref23.currentTarget;

                        if (_this13.options.showHeader && _this13.options.height) {
                            _this13.$tableHeader.scrollLeft = currentTarget.scrollLeft;
                        }

                        if (_this13.options.showFooter && !_this13.options.cardView) {
                            _this13.$tableFooter.scrollLeft = currentTarget.scrollLeft;
                        }
                    });
                }
            }, {
                key: 'toggleColumn',
                value: function toggleColumn(index, checked, needUpdate) {
                    if (index === -1) {
                        return;
                    }
                    this.columns[index].visible = checked;
                    this.initHeader();
                    this.initSearch();
                    this.initPagination();
                    this.initBody();

                    if (this.options.showColumns) {
                        var $items = this.$toolbar.querySelectorAll('.keep-open input').forEach(i => i['disabled'] = false);

                        if (needUpdate) {
                            [...$items].filter(t => t.classList.contains(Utils.sprintf('[value="%s"]', index))).forEach(i => i['checked'] = checked);
                        }

                        if ([...$items].filter(t => t[checked]).length <= this.options.minimumCountColumns) {
                            [...$items].filter(t => t[checked]).forEach(i => i['disabled'] = true);
                        }
                    }
                }
            }, {
                key: 'getVisibleFields',
                value: function getVisibleFields() {
                    var visibleFields = [];

                    var _iteratorNormalCompletion18 = true;
                    var _didIteratorError18 = false;
                    var _iteratorError18 = undefined;

                    try {
                        for (var _iterator18 = this.header.fields[Symbol.iterator](), _step18; !(_iteratorNormalCompletion18 = (_step18 = _iterator18.next()).done); _iteratorNormalCompletion18 = true) {
                            var field = _step18.value;

                            var column = this.columns[this.fieldsColumnsIndex[field]];

                            if (!column.visible) {
                                continue;
                            }
                            visibleFields.push(field);
                        }
                    } catch (err) {
                        _didIteratorError18 = true;
                        _iteratorError18 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion18 && _iterator18.return) {
                                _iterator18.return();
                            }
                        } finally {
                            if (_didIteratorError18) {
                                throw _iteratorError18;
                            }
                        }
                    }

                    return visibleFields;
                }
            }, {
                key: 'resetView',
                value: function resetView(params) {
                    var padding = 0;

                    if (params && params.height) {
                        this.options.height = params.height;
                    }

                    this.$selectAll.forEach(i => i['checked'] = this.$selectItem.length > 0 && this.$selectItem.length === [...this.$selectItem].filter(s => s['checked']).length);

                    if (this.options.height) {
                        var toolbarHeight = this.$toolbar.outerHeight;
                        var paginationHeight = this.$pagination.outerHeight;
                        var height = this.options.height - toolbarHeight - paginationHeight;

                        this.$tableContainer.style.height = height + 'px';
                    }

                    if (this.options.cardView) {
                        // remove the element css
                        this.$el.style.marginTop = '0';
                        this.$tableContainer.style.paddingBottom = '0';
                        this.$tableFooter.style.display = 'none';
                        return;
                    }

                    if (this.options.showHeader && this.options.height) {
                        this.$tableHeader.style.display = '';
                        this.resetHeader();
                        padding += this.$header.outerHeight;
                    } else {
                        this.$tableHeader.style.display = 'none';
                        this.trigger('post-header');
                    }

                    if (this.options.showFooter) {
                        this.resetFooter();
                        if (this.options.height) {
                            padding += this.$tableFooter.outerHeight + 1;
                        }
                    }

                    // Assign the correct sortable arrow
                    this.getCaret();
                    this.$tableContainer.style.paddingBottom = padding + 'px';
                    this.trigger('reset-view');
                }
            }, {
                key: 'getData',
                value: function getData(useCurrentPage) {
                    var data = this.options.data;
                    if (this.searchText || this.options.sortName || !Utils.isEmptyObject(this.filterColumns) || !Utils.isEmptyObject(this.filterColumnsPartial)) {
                        data = this.data;
                    }

                    if (useCurrentPage) {
                        return data.slice(this.pageFrom - 1, this.pageTo);
                    }

                    return data;
                }
            }, {
                key: 'load',
                value: function load(_data) {
                    var fixedScroll = false;
                    var data = _data;

                    // #431: support pagination
                    if (this.options.pagination && this.options.sidePagination === 'server') {
                        this.options.totalRows = data[this.options.totalField];
                    }

                    fixedScroll = data.fixedScroll;
                    data = Array.isArray(data) ? data : data[this.options.dataField];

                    this.initData(data);
                    this.initSearch();
                    this.initPagination();
                    this.initBody(fixedScroll);
                }
            }, {
                key: 'append',
                value: function append(data) {
                    this.initData(data, 'append');
                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'prepend',
                value: function prepend(data) {
                    this.initData(data, 'prepend');
                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'remove',
                value: function remove(params) {
                    var len = this.options.data.length;
                    var i = void 0;
                    var row = void 0;

                    if (!params.hasOwnProperty('field') || !params.hasOwnProperty('values')) {
                        return;
                    }

                    for (i = len - 1; i >= 0; i--) {
                        row = this.options.data[i];

                        if (!row.hasOwnProperty(params.field)) {
                            continue;
                        }
                        if (params.values.includes(row[params.field])) {
                            this.options.data.splice(i, 1);
                            if (this.options.sidePagination === 'server') {
                                this.options.totalRows -= 1;
                            }
                        }
                    }

                    if (len === this.options.data.length) {
                        return;
                    }

                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'append',
                value: function append(data) {
                    this.initData(data, 'append');
                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'prepend',
                value: function prepend(data) {
                    this.initData(data, 'prepend');
                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'remove',
                value: function remove(params) {
                    var len = this.options.data.length;
                    var i = void 0;
                    var row = void 0;

                    if (!params.hasOwnProperty('field') || !params.hasOwnProperty('values')) {
                        return;
                    }

                    for (i = len - 1; i >= 0; i--) {
                        row = this.options.data[i];

                        if (!row.hasOwnProperty(params.field)) {
                            continue;
                        }
                        if (params.values.includes(row[params.field])) {
                            this.options.data.splice(i, 1);
                            if (this.options.sidePagination === 'server') {
                                this.options.totalRows -= 1;
                            }
                        }
                    }

                    if (len === this.options.data.length) {
                        return;
                    }

                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'removeAll',
                value: function removeAll() {
                    if (this.options.data.length > 0) {
                        this.options.data.splice(0, this.options.data.length);
                        this.initSearch();
                        this.initPagination();
                        this.initBody(true);
                    }
                }
            }, {
                key: 'getRowByUniqueId',
                value: function getRowByUniqueId(_id) {
                    var uniqueId = this.options.uniqueId;
                    var len = this.options.data.length;
                    var id = _id;
                    var dataRow = null;
                    var i = void 0;
                    var row = void 0;
                    var rowUniqueId = void 0;

                    for (i = len - 1; i >= 0; i--) {
                        row = this.options.data[i];

                        if (row.hasOwnProperty(uniqueId)) {
                            // uniqueId is a column
                            rowUniqueId = row[uniqueId];
                        } else if (row._data && row._data.hasOwnProperty(uniqueId)) {
                            // uniqueId is a row data property
                            rowUniqueId = row._data[uniqueId];
                        } else {
                            continue;
                        }

                        if (typeof rowUniqueId === 'string') {
                            id = id.toString();
                        } else if (typeof rowUniqueId === 'number') {
                            if (Number(rowUniqueId) === rowUniqueId && rowUniqueId % 1 === 0) {
                                id = parseInt(id);
                            } else if (rowUniqueId === Number(rowUniqueId) && rowUniqueId !== 0) {
                                id = parseFloat(id);
                            }
                        }

                        if (rowUniqueId === id) {
                            dataRow = row;
                            break;
                        }
                    }

                    return dataRow;
                }
            }, {
                key: 'removeByUniqueId',
                value: function removeByUniqueId(id) {
                    var len = this.options.data.length;
                    var row = this.getRowByUniqueId(id);

                    if (row) {
                        this.options.data.splice(this.options.data.indexOf(row), 1);
                    }

                    if (len === this.options.data.length) {
                        return;
                    }

                    this.initSearch();
                    this.initPagination();
                    this.initBody(true);
                }
            }, {
                key: 'updateByUniqueId',
                value: function updateByUniqueId(params) {
                    var allParams = Array.isArray(params) ? params : [params];

                    var _iteratorNormalCompletion19 = true;
                    var _didIteratorError19 = false;
                    var _iteratorError19 = undefined;

                    try {
                        for (var _iterator19 = allParams[Symbol.iterator](), _step19; !(_iteratorNormalCompletion19 = (_step19 = _iterator19.next()).done); _iteratorNormalCompletion19 = true) {
                            var _params = _step19.value;

                            if (!_params.hasOwnProperty('id') || !_params.hasOwnProperty('row')) {
                                continue;
                            }

                            var rowId = this.options.data.indexOf(this.getRowByUniqueId(_params.id));

                            if (rowId === -1) {
                                continue;
                            }
                            Object.assign(this.options.data[rowId], _params.row);
                        }
                    } catch (err) {
                        _didIteratorError19 = true;
                        _iteratorError19 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion19 && _iterator19.return) {
                                _iterator19.return();
                            }
                        } finally {
                            if (_didIteratorError19) {
                                throw _iteratorError19;
                            }
                        }
                    }

                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'refreshColumnTitle',
                value: function refreshColumnTitle(params) {
                    if (!params.hasOwnProperty('field') || !params.hasOwnProperty('title')) {
                        return;
                    }

                    this.columns[this.fieldsColumnsIndex[params.field]].title = this.options.escape ? Utils.escapeHTML(params.title) : params.title;

                    if (this.columns[this.fieldsColumnsIndex[params.field]].visible) {
                        var header = this.options.height !== undefined ? this.$tableHeader : this.$header;
                        header.querySelectorAll('th[data-field]').forEach(function (el) {
                            if (el.dataset['field'] === params.field) {
                                document.querySelector(el.querySelector('.th-inner')[0]).textContent = params.title;
                                return false;
                            }
                        });
                    }
                }
            }, {
                key: 'insertRow',
                value: function insertRow(params) {
                    if (!params.hasOwnProperty('index') || !params.hasOwnProperty('row')) {
                        return;
                    }
                    this.options.data.splice(params.index, 0, params.row);
                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'updateRow',
                value: function updateRow(params) {
                    var allParams = Array.isArray(params) ? params : [params];

                    var _iteratorNormalCompletion20 = true;
                    var _didIteratorError20 = false;
                    var _iteratorError20 = undefined;

                    try {
                        for (var _iterator20 = allParams[Symbol.iterator](), _step20; !(_iteratorNormalCompletion20 = (_step20 = _iterator20.next()).done); _iteratorNormalCompletion20 = true) {
                            var _params2 = _step20.value;

                            if (!_params2.hasOwnProperty('index') || !_params2.hasOwnProperty('row')) {
                                continue;
                            }
                            $.extend(this.options.data[_params2.index], _params2.row);
                        }
                    } catch (err) {
                        _didIteratorError20 = true;
                        _iteratorError20 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion20 && _iterator20.return) {
                                _iterator20.return();
                            }
                        } finally {
                            if (_didIteratorError20) {
                                throw _iteratorError20;
                            }
                        }
                    }

                    this.initSearch();
                    this.initPagination();
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'initHiddenRows',
                value: function initHiddenRows() {
                    this.hiddenRows = [];
                }
            }, {
                key: 'showRow',
                value: function showRow(params) {
                    this.toggleRow(params, true);
                }
            }, {
                key: 'hideRow',
                value: function hideRow(params) {
                    this.toggleRow(params, false);
                }
            }, {
                key: 'toggleRow',
                value: function toggleRow(params, visible) {
                    var row = void 0;

                    if (params.hasOwnProperty('index')) {
                        row = this.getData()[params.index];
                    } else if (params.hasOwnProperty('uniqueId')) {
                        row = this.getRowByUniqueId(params.uniqueId);
                    }

                    if (!row) {
                        return;
                    }

                    var index = this.hiddenRows.indexOf(row);

                    if (!visible && index === -1) {
                        this.hiddenRows.push(row);
                    } else if (visible && index > -1) {
                        this.hiddenRows.splice(index, 1);
                    }
                    this.initBody(true);
                }
            }, {
                key: 'getHiddenRows',
                value: function getHiddenRows(show) {
                    if (show) {
                        this.initHiddenRows();
                        this.initBody(true);
                        return;
                    }
                    var data = this.getData();
                    var rows = [];

                    var _iteratorNormalCompletion21 = true;
                    var _didIteratorError21 = false;
                    var _iteratorError21 = undefined;

                    try {
                        for (var _iterator21 = data[Symbol.iterator](), _step21; !(_iteratorNormalCompletion21 = (_step21 = _iterator21.next()).done); _iteratorNormalCompletion21 = true) {
                            var row = _step21.value;

                            if (this.hiddenRows.includes(row)) {
                                rows.push(row);
                            }
                        }
                    } catch (err) {
                        _didIteratorError21 = true;
                        _iteratorError21 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion21 && _iterator21.return) {
                                _iterator21.return();
                            }
                        } finally {
                            if (_didIteratorError21) {
                                throw _iteratorError21;
                            }
                        }
                    }

                    this.hiddenRows = rows;
                    return rows;
                }
            }, {
                key: 'mergeCells',
                value: function mergeCells(options) {
                    var row = options.index;
                    var col = this.getVisibleFields().indexOf(options.field);
                    var rowspan = options.rowspan || 1;
                    var colspan = options.colspan || 1;
                    var i = void 0;
                    var j = void 0;
                    var $tr = this.$body.querySelectorAll('tr');

                    if (this.options.detailView && !this.options.cardView) {
                        col += 1;
                    }

                    var $td = $tr[row].querySelectorAll('td')[col];

                    if (row < 0 || col < 0 || row >= this.data.length) {
                        return;
                    }

                    for (i = row; i < row + rowspan; i++) {
                        for (j = col; j < col + colspan; j++) {
                            $tr[i].querySelectorAll('td')[j].style.display = 'none';
                        }
                    }
                    $td['rowspan'] = rowspan;
                    $td['colspan'] = colspan;
                    $td.style.display = '';
                }
            }, {
                key: 'updateCell',
                value: function updateCell(params) {
                    if (!params.hasOwnProperty('index') || !params.hasOwnProperty('field') || !params.hasOwnProperty('value')) {
                        return;
                    }
                    this.data[params.index][params.field] = params.value;

                    if (params.reinit === false) {
                        return;
                    }
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'updateCellById',
                value: function updateCellById(params) {
                    var _this14 = this;

                    if (!params.hasOwnProperty('id') || !params.hasOwnProperty('field') || !params.hasOwnProperty('value')) {
                        return;
                    }
                    var allParams = Array.isArray(params) ? params : [params];

                    allParams.forEach(function (_ref24) {
                        var id = _ref24.id,
                            field = _ref24.field,
                            value = _ref24.value;

                        var rowId = _this14.options.data.indexOf(_this14.getRowByUniqueId(id));

                        if (rowId === -1) {
                            return;
                        }
                        _this14.data[rowId][field] = value;
                    });

                    if (params.reinit === false) {
                        return;
                    }
                    this.initSort();
                    this.initBody(true);
                }
            }, {
                key: 'getOptions',
                value: function getOptions() {
                    // Deep copy: remove data
                    var options = Object.assign({}, this.options);
                    delete options.data;
                    return options;
                }
            }, {
                key: 'getSelections',
                value: function getSelections() {
                    var _this15 = this;

                    // fix #2424: from html with checkbox
                    return this.options.data.filter(function (row) {
                        return row[_this15.header.stateField] === true;
                    });
                }
            }, {
                key: 'getAllSelections',
                value: function getAllSelections() {
                    var _this16 = this;

                    return this.options.data.filter(function (row) {
                        return row[_this16.header.stateField];
                    });
                }
            }, {
                key: 'checkAll',
                value: function checkAll() {
                    this.checkAll_(true);
                }
            }, {
                key: 'uncheckAll',
                value: function uncheckAll() {
                    this.checkAll_(false);
                }
            }, {
                key: 'checkInvert',
                value: function checkInvert() {
                    var $items = [...this.$selectItem].filter(row => !row.disabled);
                    var checked = $items.filter(itm => itm.checked);
                    $items.forEach(function (el) {
                        el['checked'] = !el['checked'];
                    });
                    this.updateRows();
                    this.updateSelected();
                    this.trigger('uncheck-some', checked);
                    checked = this.getSelections();
                    this.trigger('check-some', checked);
                }
            }, {
                key: 'checkAll_',
                value: function checkAll_(checked) {
                    var rows = void 0;
                    if (!checked) {
                        rows = this.getSelections();
                    }
                    this.$selectAll.forEach(t => t.checked = checked);
                    this.$selectAll_?.forEach(t => t.checked = checked);
                    [...this.$selectItem].filter(row => !row.disabled).forEach(itm => itm.checked = checked);
                    this.updateRows();
                    if (checked) {
                        rows = this.getSelections();
                    }
                    this.trigger(checked ? 'check-all' : 'uncheck-all', rows);
                }
            }, {
                key: 'check',
                value: function check(index) {
                    this.check_(true, index);
                }
            }, {
                key: 'uncheck',
                value: function uncheck(index) {
                    this.check_(false, index);
                }
            }, {
                key: 'check_',
                value: function check_(checked, index) {
                    var $el = [...this.$selectItem].filter(row => row.classList.contains('[data-index="' + index + '"]'));
                    var row = this.data[index];

                    if ($el.some(item => item.matches(':radio')) || this.options.singleSelect) {
                        var _iteratorNormalCompletion22 = true;
                        var _didIteratorError22 = false;
                        var _iteratorError22 = undefined;

                        try {
                            for (var _iterator22 = this.options.data[Symbol.iterator](), _step22; !(_iteratorNormalCompletion22 = (_step22 = _iterator22.next()).done); _iteratorNormalCompletion22 = true) {
                                var r = _step22.value;

                                r[this.header.stateField] = false;
                            }
                        } catch (err) {
                            _didIteratorError22 = true;
                            _iteratorError22 = err;
                        } finally {
                            try {
                                if (!_iteratorNormalCompletion22 && _iterator22.return) {
                                    _iterator22.return();
                                }
                            } finally {
                                if (_didIteratorError22) {
                                    throw _iteratorError22;
                                }
                            }
                        }

                        [... this.$selectItem].filter(itm => itm.checked).filter(function (el) {
                            return !$el.includes(el);
                        }).forEach(t => t['checked'] = false);
                    }

                    row[this.header.stateField] = checked;
                    $el.forEach(t => t['checked'] = checked);
                    this.updateSelected();
                    this.trigger(checked ? 'check' : 'uncheck', this.data[index], $el);
                }
            }, {
                key: 'checkBy',
                value: function checkBy(obj) {
                    this.checkBy_(true, obj);
                }
            }, {
                key: 'uncheckBy',
                value: function uncheckBy(obj) {
                    this.checkBy_(false, obj);
                }
            }, {
                key: 'checkBy_',
                value: function checkBy_(checked, obj) {
                    var _this17 = this;

                    if (!obj.hasOwnProperty('field') || !obj.hasOwnProperty('values')) {
                        return;
                    }

                    var rows = [];
                    this.options.data.forEach(function (row, i) {
                        if (!row.hasOwnProperty(obj.field)) {
                            return false;
                        }
                        if (obj.values.includes(row[obj.field])) {
                            var $el = _this17.$selectItem.filter(s => !s.disabled).filter(s => s.matches(Utils.sprintf('[data-index="%s"]', i))).forEach(e => e['checked'] = checked);
                            row[_this17.header.stateField] = checked;
                            rows.push(row);
                            _this17.trigger(checked ? 'check' : 'uncheck', row, $el);
                        }
                    });
                    this.updateSelected();
                    this.trigger(checked ? 'check-some' : 'uncheck-some', rows);
                }
            }, {
                key: 'destroy',
                value: function destroy() {
                    this.$el.insertBefore(this.$container);
                    this.options.toolbar?.insertAdjacentHTML('beforebegin ', this.$el);
                    this.$container.nextElementSibling.remove();
                    this.$container.remove();
                    this.$el.innerHTML = this.$el_.innerHTML
                    this.$el.style.marginTop = '0'
                    this.$el.setAttribute('className', this.$el_['className'] || '');
                }
            }, {
                key: 'showLoading',
                value: function showLoading() {
                    this.$tableLoading.style.display = '';
                }
            }, {
                key: 'hideLoading',
                value: function hideLoading() {
                    this.$tableLoading.style.display = 'none';
                }
            }, {
                key: 'togglePagination',
                value: function togglePagination() {
                    this.options.pagination = !this.options.pagination;
                    var button = this.$toolbar.querySelector('button[name="paginationSwitch"] i');
                    if (this.options.pagination) {
                        button['className'] = this.options.iconsPrefix + ' ' + this.options.icons.paginationSwitchDown;
                    } else {
                        button['className'] = this.options.iconsPrefix + ' ' + this.options.icons.paginationSwitchUp;
                    }
                    this.updatePagination();
                }
            }, {
                key: 'toggleFullscreen',
                value: function toggleFullscreen() {
                    this.$el.closest('.bootstrap-table').classList.toggle('fullscreen');
                }
            }, {
                key: 'refresh',
                value: function refresh(params) {
                    if (params && params.url) {
                        this.options.url = params.url;
                    }
                    if (params && params.pageNumber) {
                        this.options.pageNumber = params.pageNumber;
                    }
                    if (params && params.pageSize) {
                        this.options.pageSize = params.pageSize;
                    }
                    this.initServer(params && params.silent, params && params.query, params && params.url);
                    this.trigger('refresh', params);
                }
            }, {

                key: 'resetWidth',
                value: function resetWidth() {
                    if (this.options.showHeader && this.options.height) {
                        this.fitHeader();
                    }
                    if (this.options.showFooter && !this.options.cardView) {
                        this.fitFooter();
                    }
                }
            }, {
                key: 'showColumn',
                value: function showColumn(field) {
                    this.toggleColumn(this.fieldsColumnsIndex[field], true, true);
                }
            }, {
                key: 'hideColumn',
                value: function hideColumn(field) {
                    this.toggleColumn(this.fieldsColumnsIndex[field], false, true);
                }
            }, {
                key: 'getHiddenColumns',
                value: function getHiddenColumns() {
                    return this.columns.filter(function (_ref25) {
                        var visible = _ref25.visible;
                        return !visible;
                    });
                }
            }, {
                key: 'getVisibleColumns',
                value: function getVisibleColumns() {
                    return this.columns.filter(function (_ref26) {
                        var visible = _ref26.visible;
                        return visible;
                    });
                }
            }, {
                key: 'toggleAllColumns',
                value: function toggleAllColumns(visible) {
                    var _iteratorNormalCompletion23 = true;
                    var _didIteratorError23 = false;
                    var _iteratorError23 = undefined;

                    try {
                        for (var _iterator23 = this.columns[Symbol.iterator](), _step23; !(_iteratorNormalCompletion23 = (_step23 = _iterator23.next()).done); _iteratorNormalCompletion23 = true) {
                            var column = _step23.value;

                            column.visible = visible;
                        }
                    } catch (err) {
                        _didIteratorError23 = true;
                        _iteratorError23 = err;
                    } finally {
                        try {
                            if (!_iteratorNormalCompletion23 && _iterator23.return) {
                                _iterator23.return();
                            }
                        } finally {
                            if (_didIteratorError23) {
                                throw _iteratorError23;
                            }
                        }
                    }

                    this.initHeader();
                    this.initSearch();
                    this.initPagination();
                    this.initBody();
                    if (this.options.showColumns) {
                        var $items = this.$toolbar.querySelectorAll('.keep-open input').forEach(t => t['disabled'] = false);

                        if ([...$items].filter(s => s['checked']).length <= this.options.minimumCountColumns) {
                            [...$items].filter(s => s['checked']).forEach(s => s['disabled'] = true);
                        }
                    }
                }
            }, {
                key: 'showAllColumns',
                value: function showAllColumns() {
                    this.toggleAllColumns(true);
                }
            }, {
                key: 'hideAllColumns',
                value: function hideAllColumns() {
                    this.toggleAllColumns(false);
                }
            }, {
                key: 'filterBy',
                value: function filterBy(columns) {
                    this.filterColumns = Utils.isEmptyObject(columns) ? {} : columns;
                    this.options.pageNumber = 1;
                    this.initSearch();
                    this.updatePagination();
                }
            }, {
                key: 'scrollTo',
                value: function scrollTo(_value) {
                    if (typeof _value === 'undefined') {
                        return this.$tableBody.scrollTop;
                    }

                    var value = 0;
                    if (typeof _value === 'string' && _value === 'bottom') {
                        value = this.$tableBody[0].scrollHeight;
                    }
                    this.$tableBody.scrollTop = value;
                }
            }, {
                key: 'getScrollPosition',
                value: function getScrollPosition() {
                    return this.scrollTo();
                }
            }, {
                key: 'selectPage',
                value: function selectPage(page) {
                    if (page > 0 && page <= this.options.totalPages) {
                        this.options.pageNumber = page;
                        this.updatePagination();
                    }
                }
            }, {
                key: 'prevPage',
                value: function prevPage() {
                    if (this.options.pageNumber > 1) {
                        this.options.pageNumber--;
                        this.updatePagination();
                    }
                }
            }, {
                key: 'nextPage',
                value: function nextPage() {
                    if (this.options.pageNumber < this.options.totalPages) {
                        this.options.pageNumber++;
                        this.updatePagination();
                    }
                }
            }, {
                key: 'toggleView',
                value: function toggleView() {
                    this.options.cardView = !this.options.cardView;
                    this.initHeader();
                    // Fixed remove toolbar when click cardView button.
                    // this.initToolbar();
                    var $icon = this.$toolbar.querySelector('button[name="toggle"] i');
                    if (this.options.cardView) {
                        $icon.classList.remove(this.options.icons.toggleOff);
                        $icon.classList.add(this.options.icons.toggleOn);
                    } else {
                        $icon.classList.remove(this.options.icons.toggleOn);
                        $icon.classList.adds(this.options.icons.toggleOff);
                    }
                    this.initBody();
                    this.trigger('toggle', this.options.cardView);
                }
            }, {
                key: 'refreshOptions',
                value: function refreshOptions(options) {
                    // If the objects are equivalent then avoid the call of destroy / init methods
                    if (Utils.compareObjects(this.options, options, true)) {
                        return;
                    }
                    this.options = Object.assign(this.options, options);
                    this.trigger('refresh-options', this.options);
                    this.destroy();
                    this.init();
                }
            }, {
                key: 'resetSearch',
                value: function resetSearch(text) {
                    var $search = this.$toolbar.querySelector('.search input');
                    $search.value = text || '';
                    this.onSearch({ currentTarget: $search });
                }
            }, {
                key: 'expandRow_',
                value: function expandRow_(expand, index) {
                    var $tr = this.$body.querySelector(Utils.sprintf('> tr[data-index="%s"]', index));
                    if ($tr.nextElementSibling.matches('tr.detail-view') === !expand) {
                        $tr.querySelector(' td > .detail-icon').click();
                    }
                }
            }, {
                key: 'expandRow',
                value: function expandRow(index) {
                    this.expandRow_(true, index);
                }
            }, {
                key: 'collapseRow',
                value: function collapseRow(index) {
                    this.expandRow_(false, index);
                }
            }, {
                key: 'expandAllRows',
                value: function expandAllRows(isSubTable) {
                    var _this18 = this;

                    if (isSubTable) {
                        var $tr = this.$body.querySelector(Utils.sprintf('> tr[data-index="%s"]', 0));
                        var detailIcon = null;
                        var executeInterval = false;
                        var idInterval = -1;

                        if (!$tr.nextElementSibling.matches('tr.detail-view')) {
                            $tr.querySelector(' td > .detail-icon').click();
                            executeInterval = true;
                        } else if (!$tr.nextElementSibling.nextElementSibling.matches('tr.detail-view')) {
                            $tr.nextElementSibling.querySelector('.detail-icon').click();
                            executeInterval = true;
                        }

                        if (executeInterval) {
                            try {
                                idInterval = setInterval(function () {
                                    detailIcon = _this18.$body.querySelector('tr.detail-view').slice(-1).querySelector('.detail-icon');
                                    if (detailIcon.length > 0) {
                                        detailIcon.click();
                                    } else {
                                        clearInterval(idInterval);
                                    }
                                }, 1);
                            } catch (ex) {
                                clearInterval(idInterval);
                            }
                        }
                    } else {
                        var trs = this.$body.children;
                        for (var i = 0; i < trs.length; i++) {
                            this.expandRow_(true, trs[i].dataset['index']);
                        }
                    }
                }
            }, {
                key: 'collapseAllRows',
                value: function collapseAllRows(isSubTable) {
                    if (isSubTable) {
                        this.expandRow_(false, 0);
                    } else {
                        var trs = this.$body.children;
                        for (var i = 0; i < trs.length; i++) {
                            this.expandRow_(false, trs[i].dataset['index']);
                        }
                    }
                }
            }, {
                key: 'updateFormatText',
                value: function updateFormatText(name, text) {
                    if (this.options[Utils.sprintf('format%s', name)]) {
                        if (typeof text === 'string') {
                            this.options[Utils.sprintf('format%s', name)] = function () {
                                return text;
                            };
                        } else if (typeof text === 'function') {
                            this.options[Utils.sprintf('format%s', name)] = text;
                        }
                    }
                    this.initToolbar();
                    this.initPagination();
                    this.initBody();
                }

            },
            ]);
            return BootstrapTable;
        }();
        BootstrapTable.DEFAULTS = DEFAULTS;
        BootstrapTable.LOCALES = LOCALES;
        BootstrapTable.COLUMN_DEFAULTS = COLUMN_DEFAULTS;
        BootstrapTable.EVENTS = EVENTS;

        // BOOTSTRAP TABLE PLUGIN DEFINITION
        // =======================

        var allowedMethods = ['getOptions', 'getSelections', 'getAllSelections', 'getData', 'load', 'append', 'prepend', 'remove', 'removeAll', 'insertRow', 'updateRow', 'updateCell', 'updateByUniqueId', 'removeByUniqueId', 'getRowByUniqueId', 'showRow', 'hideRow', 'getHiddenRows', 'mergeCells', 'refreshColumnTitle', 'checkAll', 'uncheckAll', 'checkInvert', 'check', 'uncheck', 'checkBy', 'uncheckBy', 'refresh', 'resetView', 'resetWidth', 'destroy', 'showLoading', 'hideLoading', 'showColumn', 'hideColumn', 'getHiddenColumns', 'getVisibleColumns', 'showAllColumns', 'hideAllColumns', 'filterBy', 'scrollTo', 'getScrollPosition', 'selectPage', 'prevPage', 'nextPage', 'togglePagination', 'toggleView', 'refreshOptions', 'resetSearch', 'expandRow', 'collapseRow', 'expandAllRows', 'collapseAllRows', 'updateFormatText', 'updateCellById'];

        var fn = Element.prototype.bootstrapTable = Element.prototype.bt = function (option) {
            for (var _len3 = arguments.length, args = Array(_len3 > 1 ? _len3 - 1 : 0), _key5 = 1; _key5 < _len3; _key5++) {
                args[_key5 - 1] = arguments[_key5];
            }

            var value = void 0;


            var data = this.dataset['bootstrap.table'];
            var options = Object.assign({}, BootstrapTable.DEFAULTS, this.dataset, (typeof option === 'undefined' ? 'undefined' : _typeof(option)) === 'object' && option);

            if (typeof option === 'string') {
                var _data2;

                if (!allowedMethods.includes(option)) {
                    throw new Error('Unknown method: ' + option);
                }

                if (!data) {
                    return;
                }

                value = (_data2 = data)[option].apply(_data2, args);

                if (option === 'destroy') {
                    this.removeData('bootstrap.table');
                }
            }

            if (!data) {
                this.dataset['bootstrap.table'] = data = new BootstrapTable(this, options);
            }


            return typeof value === 'undefined' ? this : value;
        };
        fn.Constructor = BootstrapTable;
        fn.defaults = BootstrapTable.DEFAULTS;
        fn.columnDefaults = BootstrapTable.COLUMN_DEFAULTS;
        fn.locales = BootstrapTable.LOCALES;
        fn.methods = allowedMethods;
        fn.utils = Utils;
        // (function () {
        // this('[data-toggle="table"]').bootstrapTable();
        // })();


    })()

    !function () {
        'use strict';
        var fn = Element.prototype
        Object.assign(fn.bootstrapTable.defaults, {
            treeShowField: null,
            idField: 'id',
            parentIdField: 'pid',
            rootParentId: null,
            onGetNodes: function onGetNodes(row, data) {
                var that = this;
                var nodes = [];
                data.forEach(function (item) {
                    if (row[that.options.idField] === item[that.options.parentIdField]) {
                        nodes.push(item);
                    }
                });
                return nodes;
            },
            onCheckRoot: function onCheckRoot(row, data) {
                var that = this;
                return that.options.rootParentId === row[that.options.parentIdField] || !row[that.options.parentIdField];
            }
        });

        var BootstrapTable = fn.bootstrapTable.Constructor,
            _init = BootstrapTable.prototype.init,
            _initRow = BootstrapTable.prototype.initRow,
            _initHeader = BootstrapTable.prototype.initHeader,
            _rowStyle = null;

        BootstrapTable.prototype.init = function () {
            _rowStyle = this.options.rowStyle;
            _init.apply(this, Array.prototype.slice.apply(arguments));
        };

        // td
        BootstrapTable.prototype.initHeader = function () {
            var that = this;
            _initHeader.apply(that, Array.prototype.slice.apply(arguments));
            var treeShowField = that.options.treeShowField;
            if (treeShowField) {
                this.header.fields.forEach(function (field) {
                    if (treeShowField === field) {
                        that.treeEnable = true;
                        return false;
                    }
                });
            }
        };

        var initTr = function initTr(item, idx, data, parentDom) {
            var that = this;
            var nodes = that.options.onGetNodes.apply(that, [item, data]);
            item._nodes = nodes;
            parentDom.append(_initRow.apply(that, [item, idx, data, parentDom]));
            // console.log(item);
            // console.log(nodes);
            // init sub node
            var len = nodes.length - 1;
            for (var i = 0; i <= len; i++) {
                var node = nodes[i];
                node._level = item._level + 1;
                node._parent = item;
                if (i === len) node._last = 1;
                // jquery.treegrid.js
                that.options.rowStyle = function (item, idx) {
                    var res = _rowStyle.apply(that, Array.prototype.slice.apply(arguments));
                    var id = item[that.options.idField] ? item[that.options.idField] : 0;
                    var pid = item[that.options.parentIdField] ? item[that.options.parentIdField] : 0;
                    res.classes = [res.classes || '', 'treegrid-' + id, 'treegrid-parent-' + pid].join(' ');
                    return res;
                };
                initTr.apply(that, [node, Utils.inArray(node, data), data, parentDom]);
            }
        };

        // tr
        BootstrapTable.prototype.initRow = function (item, idx, data, parentDom) {
            var that = this;
            if (that.treeEnable) {
                // init root node
                if (that.options.onCheckRoot.apply(that, [item, data])) {
                    if (item._level === undefined) {
                        item._level = 0;
                    }
                    // jquery.treegrid.js
                    that.options.rowStyle = function (item, idx) {
                        var res = _rowStyle.apply(that, Array.prototype.slice.apply(arguments));
                        var x = item[that.options.idField] ? item[that.options.idField] : 0;
                        res.classes = [res.classes || '', 'treegrid-' + x].join(' ');
                        return res;
                    };
                    initTr.apply(that, [item, idx, data, parentDom]);

                    return true;
                }
                return false;
            }
            return _initRow.apply(that, Array.prototype.slice.apply(arguments));
        };
    }();

    (function () {
        var fn = Element.prototype, _tree = new WeakMap();
        const key = { 'treeWeakMap': 'treegrid' }, skey = ['setSettings']; //{ 'treeWeakMap': 'treegrid' };
        var methods = {
            /**
             * Initialize tree
             *
             * @param {Object} options
             * @returns {Object[]}
             */
            initTree: function (options) {
                var settings = Object.assign({}, this.treegrid.defaults, options);

                // var $this = this;
                // console.log(this)
                this.treegrid('setTreeContainer', this);
                this.treegrid('setSettings', settings);
                var rootnodes = settings.getRootNodes.apply(this, [this])
                console.log(rootnodes)
                rootnodes.forEach(rt => rt.treegrid('initNode', settings));


                // $this.treegrid('getRootNodes').treegrid('render');
                return this;
            },
            /**
             * Initialize node
             *
             * @param {Object} settings
             * @returns {Object[]}
             */
            initNode: function (settings) {

                // var $this = this;
                // console.log(this)
                this.treegrid('setTreeContainer', settings.getTreeGridContainer.apply(this));
                this.treegrid('getChildNodes').forEach(cn => cn.treegrid('initNode', settings));
                this.treegrid('initExpander').treegrid('initIndent').treegrid('initEvents').treegrid('initState').treegrid('initChangeEvent').treegrid("initSettingsEvents");
                return this;
            },
            initChangeEvent: function () {
                var $this = this;
                //Save state on change
                $Event.on($this, "change", function () {
                    var $this = this;
                    $this.treegrid('render');
                    if ($this.treegrid('getSetting', 'saveState')) {
                        $this.treegrid('saveState');
                    }
                });
                return $this;
            },
            /**
             * Initialize node events
             *
             * @returns {Node}
             */
            initEvents: function () {
                var $this = this;
                //Default behavior on collapse
                $Event.on($this, "collapse", function () {
                    var $this = this;
                    $this.classList.remove('treegrid-expanded');
                    $this.classList.add('treegrid-collapsed');
                });
                //Default behavior on expand
                $Event.on($this, "expand", function () {
                    var $this = this;
                    $this.classList.remove('treegrid-collapsed');
                    $this.classList.add('treegrid-expanded');
                });

                return $this;
            },
            /**
             * Initialize events from settings
             *
             * @returns {Node}
             */
            initSettingsEvents: function () {
                var $this = this;
                // console.log($this)
                //Save state on change
                $Event.on($this, "change", function () {
                    var $this = this;
                    if (typeof ($this.treegrid('getSetting', 'onChange')) === "function") {
                        $this.treegrid('getSetting', 'onChange').apply($this);
                    }
                });
                //Default behavior on collapse
                $Event.on($this, "collapse", function () {
                    var $this = this;
                    if (typeof ($this.treegrid('getSetting', 'onCollapse')) === "function") {
                        $this.treegrid('getSetting', 'onCollapse').apply($this);
                    }
                });
                //Default behavior on expand
                $Event.on($this, "expand", function () {
                    var $this = this;
                    if (typeof ($this.treegrid('getSetting', 'onExpand')) === "function") {
                        $this.treegrid('getSetting', 'onExpand').apply($this);
                    }

                });

                return $this;
            },
            /**
             * Initialize expander for node
             *
             * @returns {Node}
             */
            initExpander: function () {
                var $this = this;
                var cell = $this.querySelectorAll('td')[$this.treegrid('getSetting', 'treeColumn')];
                var tpl = $this.treegrid('getSetting', 'expanderTemplate');
                var expander = $this.treegrid('getSetting', 'getExpander').apply(this);
                if (expander) {
                    expander.forEach(ex => ex.removeChild());
                }
                // console.log(cell)
                cell.insertAdjacentHTML('afterbegin', tpl)
                document.querySelectorAll(".treegrid-expander").forEach(te => te.click(function () {
                    this.closest('tr').treegrid('toggle');
                }));
                return $this;
            },
            /**
             * Initialize indent for node
             *
             * @returns {Node}
             */
            initIndent: function () {

                this.querySelectorAll('.treegrid-indent').forEach(t => t.remove());
                // var tpl = $this.treegrid('getSetting', 'indentTemplate');
                // var expander = $this.querySelector('.treegrid-expander');
                // var depth = $this.treegrid('getDepth');
                // for (var i = 0; i < depth; i++) {
                // const tl = document.querySelector(tpl);
                // tl.parentNode.insertBefore(expander, tl);
                // }

                for (var i = 0; i < this.treegrid('getDepth'); i++) {
                    // tl.parentNode.insertBefore($this.querySelector('.treegrid-expander', tl));
                    this.querySelectorAll('.treegrid-expander').forEach(tr =>
                        tr.insertAdjacentHTML('beforeBegin', this.treegrid('getSetting', 'indentTemplate')));
                }

                return this;
            },
            /**
             * Initialise state of node
             *
             * @returns {Node}
             */
            initState: function () {
                var $this = this;
                if ($this.treegrid('getSetting', 'saveState') && !$this.treegrid('isFirstInit')) {
                    $this.treegrid('restoreState');
                } else {
                    if ($this.treegrid('getSetting', 'initialState') === "expanded") {
                        $this.treegrid('expand');
                    } else {
                        $this.treegrid('collapse');
                    }
                }
                return $this;
            },
            /**
             * Return true if this tree was never been initialised
             *
             * @returns {Boolean}
             */
            isFirstInit: function () {
                var tree = this.treegrid('getTreeContainer');
                if (tree.dataset['first_init'] === undefined) {
                    tree.dataset['first_init'] = document.cookie(tree.treegrid('getSetting', 'saveStateName')) === undefined;
                }
                return tree.dataset('first_init');
            },
            /**
             * Save state of current node
             *
             * @returns {Node}
             */
            saveState: function () {
                var $this = this;
                if ($this.treegrid('getSetting', 'saveStateMethod') === 'cookie') {

                    var stateArrayString = document.cookie($this.treegrid('getSetting', 'saveStateName')) || '';
                    var stateArray = (stateArrayString === '' ? [] : stateArrayString.split(','));
                    var nodeId = $this.treegrid('getNodeId');

                    if ($this.treegrid('isExpanded')) {
                        if (Utils.inArray(nodeId, stateArray) === -1) {
                            stateArray.push(nodeId);
                        }
                    } else if ($this.treegrid('isCollapsed')) {
                        if (Utils.inArray(nodeId, stateArray) !== -1) {
                            stateArray.splice(Utils.inArray(nodeId, stateArray), 1);
                        }
                    }
                    document.cookie($this.treegrid('getSetting', 'saveStateName')) = stateArray.join(',');
                }
                return $this;
            },
            /**
             * Restore state of current node.
             *
             * @returns {Node}
             */
            restoreState: function () {
                var $this = this;
                if ($this.treegrid('getSetting', 'saveStateMethod') === 'cookie') {
                    var stateArray = document.cookie($this.treegrid('getSetting', 'saveStateName')).split(',');
                    if (Utils.inArray($this.treegrid('getNodeId'), stateArray) !== -1) {
                        $this.treegrid('expand');
                    } else {
                        $this.treegrid('collapse');
                    }

                }
                return $this;
            },
            /**
             * Method return setting by name
             *
             * @param {type} name
             * @returns {unresolved}
             */
            getSetting: function (name) {
                if (!this.treegrid('getTreeContainer')) {
                    // console.log("TreeGrid: Tree container not found");
                    return null;
                }
                // console.log(_tree.get(skey));
                // return JSON.parse(this.treegrid('getTreeContainer').dataset['settings'])[name];
                return _tree.get(skey)[name];
            },
            /**
             * Add new settings
             *
             * @param {Object} settings
             */
            setSettings: function (settings) {
                var getTre = this.treegrid('getTreeContainer')
                // console.log(getTre);
                // this.treegrid('getTreeContainer').dataset['settings'] = JSON.stringify(settings);
                return _tree.set(skey, settings);
            },
            /**
             * Return tree container
             *
             * @returns {HtmlElement}
             */
            getTreeContainer: function () {
                // console.log("TreeGrid: get tree container ", _tree.get(key))
                // return document.querySelector('[data-treegrid=' + this.dataset['treegrid'] + ']');
                return _tree.get(key);
            },
            /**
             * Set tree container
             *
             * @param {HtmlE;ement} container
             */
            setTreeContainer: function (container) {
                // console.log("TreeGrid: Set tree container ", container.className, JSON.stringify(container));
                // return this.dataset['treegrid'] = container.className;
                // console.log("TreeGrid: Set tree container ", container)
                return _tree.set(key, container);
            },
            /**
             * Method return all root nodes of tree.
             *
             * Start init all child nodes from it.
             *
             * @returns {Array}
             */
            getRootNodes: function () {
                // console.log("TreeGrid: get root nodes ", this.treegrid('getSetting', 'getRootNodes'))
                return this.treegrid('getSetting', 'getRootNodes').apply(this, [this.treegrid('getTreeContainer')]);
            },
            /**
             * Method return all nodes of tree.
             *
             * @returns {Array}
             */
            getAllNodes: function () {
                return this.treegrid('getSetting', 'getAllNodes').apply(this, [this.treegrid('getTreeContainer')]);
            },
            /**
             * Mthod return true if element is Node
             *
             * @returns {String}
             */
            isNode: function () {
                return this.treegrid('getNodeId') !== null;
            },
            /**
             * Mthod return id of node
             *
             * @returns {String}
             */
            getNodeId: function () {
                // console.log("TreeGrid: get node id ", this.treegrid('getSetting', 'getNodeId'))
                if (this.treegrid('getSetting', 'getNodeId') === null) {
                    return null;
                } else {
                    return this.treegrid('getSetting', 'getNodeId').apply(this);
                }
            },
            /**
             * Method return parent id of node or null if root node
             *
             * @returns {String}
             */
            getParentNodeId: function () {
                return this.treegrid('getSetting', 'getParentNodeId').apply(this);
            },
            /**
             * Method return parent node or null if root node
             *
             * @returns {Object[]}
             */
            getParentNode: function () {
                if (this.treegrid('getParentNodeId') === null) {
                    return null;
                } else {
                    return this.treegrid('getSetting', 'getNodeById').apply(this, [this.treegrid('getParentNodeId'), this.treegrid('getTreeContainer')]);
                }
            },
            /**
             * Method return array of child nodes or null if node is leaf
             *
             * @returns {Object[]}
             */
            getChildNodes: function () {

                return this.treegrid('getSetting', 'getChildNodes').apply(this, [this.treegrid('getNodeId'), this.treegrid('getTreeContainer')]);
            },
            /**
             * Method return depth of tree.
             *
             * This method is needs for calculate indent
             *
             * @returns {Number}
             */
            getDepth: function () {
                if (this.treegrid('getParentNode') === null) {
                    return 0;
                }
                return this.treegrid('getParentNode').treegrid('getDepth') + 1;
            },
            /**
             * Method return true if node is root
             *
             * @returns {Boolean}
             */
            isRoot: function () {
                return this.treegrid('getDepth') === 0;
            },
            /**
             * Method return true if node has no child nodes
             *
             * @returns {Boolean}
             */
            isLeaf: function () {
                return this.treegrid('getChildNodes').length === 0;
            },
            /**
             * Method return true if node last in branch
             *
             * @returns {Boolean}
             */
            isLast: function () {
                if (this.treegrid('isNode')) {
                    var parentNode = this.treegrid('getParentNode');
                    if (parentNode === null) {
                        if (this.treegrid('getNodeId') === Array.prototype.slice.call(this.treegrid('getRootNodes'), -1).treegrid('getNodeId')) {
                            return true;
                        }
                    } else {
                        if (this.treegrid('getNodeId') === Array.prototype.slice.call(parentNode.treegrid('getChildNodes'), -1).treegrid('getNodeId')) {
                            return true;
                        }
                    }
                }
                return false;
            },
            /**
             * Method return true if node first in branch
             *
             * @returns {Boolean}
             */
            isFirst: function () {
                if (this.treegrid('isNode')) {
                    var parentNode = this.treegrid('getParentNode');
                    if (parentNode === null) {
                        if (this.treegrid('getNodeId') === Array.prototype.slice.call(this.treegrid('getRootNodes'), 0, 1).treegrid('getNodeId')) {
                            return true;
                        }
                    } else {
                        if (this.treegrid('getNodeId') === Array.prototype.slice.call(parentNode.treegrid('getChildNodes'), 0, 1).treegrid('getNodeId')) {
                            return true;
                        }
                    }
                }
                return false;
            },
            /**
             * Return true if node expanded
             *
             * @returns {Boolean}
             */
            isExpanded: function () {
                return this.classList.contains('treegrid-expanded');
            },
            /**
             * Return true if node collapsed
             *
             * @returns {Boolean}
             */
            isCollapsed: function () {
                return this.classList.contains('treegrid-collapsed');
            },
            /**
             * Return true if at least one of parent node is collapsed
             *
             * @returns {Boolean}
             */
            isOneOfParentsCollapsed: function () {
                var $this = this;
                if ($this.treegrid('isRoot')) {
                    return false;
                } else {
                    if ($this.treegrid('getParentNode').treegrid('isCollapsed')) {
                        return true;
                    } else {
                        return $this.treegrid('getParentNode').treegrid('isOneOfParentsCollapsed');
                    }
                }
            },
            /**
             * Expand node
             *
             * @returns {Node}
             */
            expand: function () {
                if (!this.treegrid('isLeaf') && !this.treegrid("isExpanded")) {
                    $Event.trigger(this, "expand");
                    $Event.trigger(this, "change");
                    return this;
                }
                return this;
            },
            /**
             * Expand all nodes
             *
             * @returns {Node}
             */
            expandAll: function () {
                var $this = this;
                $this.treegrid('getRootNodes').treegrid('expandRecursive');
                return $this;
            },
            /**
             * Expand current node and all child nodes begin from current
             *
             * @returns {Node}
             */
            expandRecursive: function () {


                this.treegrid('expand');
                if (!this.treegrid('isLeaf')) {
                    this.treegrid('getChildNodes').treegrid('expandRecursive');
                }
                return this;
            },
            /**
             * Collapse node
             *
             * @returns {Node}
             */
            collapse: function () {


                if (!this.treegrid('isLeaf') && !this.treegrid("isCollapsed")) {
                    $Event.trigger(this, "collapse");
                    $Event.trigger(this, "change");
                }
                return this;
            },
            /**
             * Collapse all nodes
             *
             * @returns {Node}
             */
            collapseAll: function () {
                var $this = this;
                $this.treegrid('getRootNodes').treegrid('collapseRecursive');
                return $this;
            },
            /**
             * Collapse current node and all child nodes begin from current
             *
             * @returns {Node}
             */
            collapseRecursive: function () {


                this.treegrid('collapse');
                if (!this.treegrid('isLeaf')) {
                    this.treegrid('getChildNodes').treegrid('collapseRecursive');
                }
                return this;
            },
            /**
             * Expand if collapsed, Collapse if expanded
             *
             * @returns {Node}
             */
            toggle: function () {
                var $this = this;
                if ($this.treegrid('isExpanded')) {
                    $this.treegrid('collapse');
                } else {
                    $this.treegrid('expand');
                }
                return $this;
            },
            /**
             * Rendering node
             *
             * @returns {Node}
             */
            render: function () {


                //if parent colapsed we hidden
                if (this.treegrid('isOneOfParentsCollapsed')) {
                    this.style.display = 'none';
                } else {
                    this.style.display = '';
                }
                if (!this.treegrid('isLeaf')) {
                    this.treegrid('renderExpander');
                    this.treegrid('getChildNodes'), forEach(cn => cn.treegrid('render'));
                }
                return this;
            },
            /**
             * Rendering expander depends on node state
             *
             * @returns {Node}
             */
            renderExpander: function () {

                var $this = this;
                var expander = $this.treegrid('getSetting', 'getExpander').apply(this);
                console.log(expander);
                if (expander) {
                    console.log($this.treegrid('getSetting', 'expanderExpandedClass'));
                    if (!$this.treegrid('isCollapsed')) {
                        expander.forEach(ex => {
                            ex.classList.remove($this.treegrid('getSetting', 'expanderCollapsedClass'));
                            ex.classList.add($this.treegrid('getSetting', 'expanderExpandedClass'));
                        })
                    } else {
                        expander.forEach(ex => {
                            ex.removeClass($this.treegrid('getSetting', 'expanderExpandedClass'));
                            ex.addClass($this.treegrid('getSetting', 'expanderCollapsedClass'))
                        });
                    }
                } else {
                    $this.treegrid('initExpander');
                    $this.treegrid('renderExpander');
                }
                return this;
            }
        };
        fn.treegrid = function (method) {
            if (methods[method]) {
                return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
            } else if (typeof method === 'object' || !method) {
                // console.log(method);
                return methods.initTree.apply(this, arguments);
            } else {
                throw new Error('Method with name ' + method + ' does not exists for jQuery.treegrid');
            }
        };
        /**
         *  Plugin's default options
         */
        fn.treegrid.defaults = {
            initialState: 'expanded',
            saveState: false,
            saveStateMethod: 'cookie',
            saveStateName: 'tree-grid-state',
            expanderTemplate: '<span class="treegrid-expander"></span>',
            indentTemplate: '<span class="treegrid-indent"></span>',
            expanderExpandedClass: 'treegrid-expander-expanded',
            expanderCollapsedClass: 'treegrid-expander-collapsed',
            treeColumn: 0,
            getExpander: function () {
                return this.querySelectorAll('.treegrid-expander');
            },
            getNodeId: function () {
                var template = /treegrid-([A-Za-z0-9_-]+)/;
                if (template.test(this['className'])) {
                    return template.exec(this['className'])[1];
                }
                return null;
            },
            getParentNodeId: function () {
                var template = /treegrid-parent-([A-Za-z0-9_-]+)/;
                if (template.test(this['className'])) {
                    return template.exec(this['className'])[1];
                }
                return null;
            },
            getNodeById: function (id, treegridContainer) {
                var templateClass = "treegrid-" + id;
                return treegridContainer.querySelector('tr.' + templateClass);
            },
            getChildNodes: function (id, treegridContainer) {
                var templateClass = "treegrid-parent-" + id;
                // console.log(treegridContainer);
                // console.log(templateClass);
                // console.log(treegridContainer.querySelectorAll('tr.' + templateClass));
                return treegridContainer.querySelectorAll('tr.' + templateClass);
            },
            getTreeGridContainer: function () {
                // console.log(this.closest('table'));
                return this.closest('table');
            },
            getRootNodes: function (treegridContainer) {
                // console.log(treegridContainer.querySelectorAll('tr'));
                var result = [...treegridContainer.querySelectorAll('tr')].filter(function (element) {
                    var classNames = element['className'];
                    var templateClass = /treegrid-([A-Za-z0-9_-]+)/;
                    var templateParentClass = /treegrid-parent-([A-Za-z0-9_-]+)/;
                    // console.log(classNames);
                    // console.log(templateClass.test(classNames));
                    // console.log(templateParentClass.test(classNames));
                    return templateClass.test(classNames) && !templateParentClass.test(classNames);
                });
                // console.log(result);
                return result;
            },
            getAllNodes: function (treegridContainer) {
                var result = [...treegridContainer.querySelectorAll('tr')].filter(function (element) {
                    var classNames = element['className'];
                    var templateClass = /treegrid-([A-Za-z0-9_-]+)/;
                    return templateClass.test(classNames);
                });
                return result;
            },
            //Events
            onCollapse: null,
            onExpand: null,
            onChange: null

        };
    })();

}));


