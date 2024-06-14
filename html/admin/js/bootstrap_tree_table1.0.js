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

    /**
 * 代理事件
 * ========================================================
 * 说明：代码修改至 Nicolas Gallagher 的 delegate.js
 * 项目 GitHub 地址：https://github.com/necolas/delegate.js
 * jQuery
 * ========================================================
 */
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
                    if (!fn._flag) fn._flag = selector + Math.random().toString(36).substr(2, 8);
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
    let Utils = {
        //比较对象
        compareObjects: function (objectA, objectB, compareLength) {
            // Create arrays of property names
            var objectAProperties = Object.getOwnPropertyNames(objectA),
                objectBProperties = Object.getOwnPropertyNames(objectB),
                propName = '';
            if (compareLength) {
                // If number of properties is different, objects are not equivalent
                if (objectAProperties.length !== objectBProperties.length) {
                    return false;
                }
            }
            for (var i = 0; i < objectAProperties.length; i++) {
                propName = objectAProperties[i];
                // If the property is not in the object B properties, continue with the next property
                if ($.inArray(propName, objectBProperties) > -1) {
                    // If values of same property are not equal, objects are not equivalent
                    if (objectA[propName] !== objectB[propName]) {
                        return false;
                    }
                }
            }
            // If we made it this far, objects are considered equivalent
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
            return !!(navigator.userAgent.indexOf("MSIE ") > 0 || !!navigator.userAgent.match(/Trident.*rv\:11\./));
        },
        getPropertyFromOther: function (list, from, to, value) {
            var result = '';
            list.forEach(function (item, i) {
                if (item[from] === value) {
                    result = item[to];
                    return false;
                }
                return true;
            });
            return result;
        },
        getScrollBarWidth: function () {
            if (cachedWidth === null) {
                var inner = document.querySelectorAll('<p/>'),
                    outer = document.querySelectorAll('<div/>'),
                    w1, w2;
                inner.forEach(function (item, i) {
                    item.classList.add('fixed-table-scroll-inner');
                })
                outer.forEach(function (item, i) {
                    item.classList.add('fixed-table-scroll-outer');
                })

                outer.forEach(o => {
                    o.appendChild(inner);
                })

                document.querySelector('body').appendChild(outer);
                w1 = inner[0].offsetWidth;
                outer.forEach((o) => o.styles.overflow = 'scroll');
                w2 = inner[0].offsetWidth;
                if (w1 === w2) {
                    w2 = outer[0].clientWidth;
                }
                outer.parentNode.removeChild(outer);;
                cachedWidth = w1 - w2;
            }
            return cachedWidth;
        },
        compareObjects: function (objectA, objectB, compareLength) {
            // Create arrays of property names
            var objectAProperties = Object.getOwnPropertyNames(objectA),
                objectBProperties = Object.getOwnPropertyNames(objectB),
                propName = '';
            if (compareLength) {  // If number of properties is different, objects are not equivalent
                if (objectAProperties.length !== objectBProperties.length) {
                    return false;
                }
            }
            for (var i = 0; i < objectAProperties.length; i++) {
                propName = objectAProperties[i];
                // If the property is not in the object B properties, continue with the next property
                if ($.inArray(propName, objectBProperties) > -1) {
                }
            }
            // If we made it this far, objects are considered equivalent
            return true;
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
        // 判断是否为空对象 
        isEmptyObject: function (value) {
            return Object.keys(value).length === 0;
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
        sprintf:
            function (str) {
                var args = arguments,
                    flag = true,
                    i = 1;
                str = str.replace(/%s/g, function () {
                    var arg = args[i++];
                    if (typeof arg === 'undefined') {
                        flag = false;
                        return '';
                    }
                    return arg;
                });
                return flag ? str : '';
            },
        // function () {
        // if (!arguments.length) return '';
        // var str = arguments[0],
        // i = 1;
        // str.replace(/%s/g, function () {
        // var arg = arguments[i++];
        // return typeof arg !== 'undefined' ? arvg : '';// 对每个匹配值应用函数，i自加1，直到无匹配值; 
        // return str;
        // });
        // },
        /* 这个函数的作用是对表格的列进行排序，并为每个列分配一个唯一的索引。这个索引是根据列的行跨度（rowspan）和列跨度（colspan）计算得出的。
        函数的参数是一个数组（columns），其中每个元素都是一个包含列对象的一维数组。列对象可以包含以下属性：
        - colspan：列的列跨度，默认为 1
        - rowspan：列的行跨度，默认为 1
        - field：列的数据字段，默认为索引
        函数的实现首先计算总的列数（totalCol），然后为每个列的状态数组（flag）分配内存。接下来，遍历所有列，并为每个列分配一个唯一的索引。最后，为每个列分配一个唯一的索引，并根据其行跨度和列跨度更新状态数组。
        这个函数的主要目的是为每个列分配一个唯一的索引，以便在后续处理中可以使用该索引来访问和操作列。 */

        setFieldIndex: function (columns) {
            var i, j, k,
                totalCol = 0,
                flag = [];
            for (i = 0; i < columns[0].length; i++) {
                totalCol += columns[0][i].colspan || 1;
            }
            for (i = 0; i < columns.length; i++) {
                flag[i] = [];
                for (j = 0; j < totalCol; j++) {
                    flag[i][j] = false;
                }
            }
            for (i = 0; i < columns.length; i++) {
                for (j = 0; j < columns[i].length; j++) {
                    var r = columns[i][j],
                        rowspan = r.rowspan || 1,
                        colspan = r.colspan || 1,
                        index = Utils.inArray(false, flag[i]);
                    if (colspan === 1) {
                        r.fieldIndex = index;
                        // when field is undefined, use index instead
                        if (typeof r.field === 'undefined') {
                            r.field = index;
                        }
                    }
                    for (k = 0; k < rowspan; k++) {
                        flag[i + k][index] = true;
                    }
                    for (k = 0; k < colspan; k++) {
                        flag[i][index + k] = true;
                    }
                }
            }
        },
        //                                                                                                                                                                                         // 获取真实的data-attr属性值
        getRealDataAttr: function (dataAttr) {

            for (var attr in dataAttr) {
                var auxAttr = attr.split(/(?=[A-Z])/).join('-').toLowerCase();// /(?=[A-Z])/从大写字母处分割
                if (auxAttr !== attr) {
                    dataAttr[auxAttr] = dataAttr[attr];
                    delete dataAttr[attr];
                }
            }
            return dataAttr;
        },
        getFieldIndex: function (columns, field) {
            var index = -1;
            for (const [i, column] of columns.entries()) {
                if (column.field === field) {
                    index = i;
                    break;
                }
                continue;
            };
            return index;
        },
        // 计算对象值
        calculateObjectValue: function (self, name, args, defaultValue) {
            var func = name;
            if (typeof name === 'string') {
                // support obj.func1.func2
                var names = name.split('.');
                if (names.length > 1) {
                    func = window;
                    names.forEach(function (f) {
                        func = func[f];
                    });
                } else {
                    func = window[name];
                }
            }
            if (typeof func === 'object') {
                return func;
            }
            if (typeof func === 'function') {
                return func.apply(self, args || []);
            }
            if (!func && typeof name === 'string' && sprintf.apply(this, [name].concat(args))) {
                return sprintf.apply(this, [name].concat(args));
            }
            return defaultValue;
        },
        getItemField: function (item, field, escape) {
            var value = item;
            if (typeof field !== 'string' || item.hasOwnProperty(field)) {
                return escape ? Utils.escapeHTML(item[field]) : item[field];
            }
            var props = field.split('.');
            for (var p in props) {
                if (props.hasOwnProperty(p)) {
                    value = value && value[props[p]];
                }
            }
            return escape ? Utils.escapeHTML(value) : value;
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
        parents: function getParents(el, parentSelector /* optional */) {
            // console.log(el);
            // If no parentSelector defined will bubble up all the way to *document*
            if (parentSelector === undefined) {
                parentSelector = document;
            }
            var parents = [];
            var p = el.parentNode;
            while (p !== parentSelector) {
                var o = p;
                parents.push(o);
                p = o.parentNode;
            }
            parents.push(parentSelector);
            return parents;
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


    // 定义一个数组，用于存储允许的方法
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


    // 定义BootstrapTable函数，接收两个参数：el和options
    let BootstrapTable = function (el, options) {
        this.options = options;
        this.$el = el;
        this.$el_ = this.$el.cloneNode(true);// 记录触发元素的初始值，destroy销毁重置的时候使用
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
        //tree
        treeView: false,//treeView视图
        // treeGridModel: "adjacency",
        expandField: "id",//treeView视图字段
        treeField: "id",
        parentField: "ParentId",//treeView视图id
        treeRootLevel: 0,//根节点序号
        expandAll: false,//是否全部展开
        initialState: 'expanded',
        saveState: false,
        saveStateMethod: 'cookie',
        saveStateName: 'tree-grid-state',
        expanderTemplate: '<span class="treegrid-expander"></span>',
        indentTemplate: '<span class="treegrid-indent"></span>',
        expanderExpandedClass: 'treegrid-expander-expanded',
        expanderCollapsedClass: 'treegrid-expander-collapsed',
        collapseIcon: "glyphicon glyphicon-chevron-right",//折叠样式
        expandIcon: "glyphicon glyphicon-chevron-down",//展开样式
        treeColumn: 0,
        getExpander: function () {
            return this.querySelector('.treegrid-expander');
        },
        getNodeId: function () {
            var template = /treegrid-([A-Za-z0-9_-]+)/;
            if (template.test(this.getAttribute('class'))) {
                return template.exec(this.getAttribute('class'))[1];
            }
            return null;
        },
        getParentNodeId: function () {
            var template = /treegrid-parent-([A-Za-z0-9_-]+)/;
            if (template.test(this.getAttribute('class'))) {
                return template.exec(this.getAttribute('class'))[1];
            }
            return null;
        },
        getNodeById: function (id, treegridContainer) {
            var templateClass = "treegrid-" + id;
            return treegridContainer.querySelector('tr.' + templateClass);
        },
        getChildNodes: function (id, treegridContainer) {
            var templateClass = "treegrid-parent-" + id;
            return treegridContainer.querySelectorAll('tr.' + templateClass);
        },
        getTreeGridContainer: function () {
            return this.closest('table');
        },
        getRootNodes: function (treegridContainer) {
            var result = [].filter.call(treegridContainer.querySelectorAll('tr'), function (element) {
                var classNames = document.querySelector(element).getAttribute('class');
                var templateClass = /treegrid-([A-Za-z0-9_-]+)/;
                var templateParentClass = /treegrid-parent-([A-Za-z0-9_-]+)/;
                return templateClass.test(classNames) && !templateParentClass.test(classNames);
            });
            return result;
        },
        getAllNodes: function (treegridContainer) {
            var result = [].filter.call(treegridContainer.querySelectorAll('tr'), function (element) {
                var classNames = document.querySelector(element).getAttribute('class');
                var templateClass = /treegrid-([A-Za-z0-9_-]+)/;
                return templateClass.test(classNames);
            });
            return result;
        },
        //Events
        onCollapse: null,
        onExpand: null,
        onChange: null,
        //end
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
            // console.log('yunxing')
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
            return Utils.sprintf('%s records per page', pageNumber);
        },// 每页显示条目数提示文案  
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return Utils.sprintf('Showing %s to %s of %s rows', pageFrom, pageTo, totalRows);
        },// 分页提示当前页从第pageFrom到pageTo，总totalRows条  
        formatDetailPagination: function (totalRows) {
            return Utils.sprintf('Showing %s rows', totalRows);// 分页提示供多少条数据  
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
    // 定义BootstrapTable原型上的init方法
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
        this.initHiddenRows();
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
        // console.log('将语言包添加进配置项')
        if (this.options.locale) {
            var parts = this.options.locale.split(/-|_/);
            parts[0].toLowerCase();
            parts[1] && parts[1].toUpperCase();
            if (fn.locales[this.options.locale]) {
                Object.assign(this.options, fn.locales[this.options.locale]);
            } else if (fn.locales[parts.join('-')]) {
                Object.assign(this.options, fn.locales[parts.join('-')]);
            } else if (fn.locales[parts[0]]) {
                Object.assign(this.options, fn.locales[parts[0]]);
            }
        }

    };

    // 创建包裹元素this.container及其子元素this.$toolbar、this.$pagination等，为表格添加样式;  
    BootstrapTable.prototype.initContainer = function () {
        this.$container = document.createElement('div');
        this.$container.className = 'bootstrap-table';

        this.$container.insertAdjacentHTML('afterbegin', [
            '<div class="fixed-table-toolbar"></div>',
            this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ?//分页对齐
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

        ].join(''));

        this.$el.parentNode.replaceChild(this.$container, this.$el);
        // this.$container.insertAfter(this.$el);
        this.$tableContainer = this.$container.querySelector('.fixed-table-container');
        this.$tableHeader = this.$container.querySelector('.fixed-table-header');
        this.$tableBody = this.$container.querySelector('.fixed-table-body');
        this.$tableLoading = this.$container.querySelector('.fixed-table-loading');
        this.$tableFooter = this.$container.querySelector('.fixed-table-footer');
        this.$toolbar = this.$container.querySelector('.fixed-table-toolbar');
        this.$pagination = this.$container.querySelector('.fixed-table-pagination');

        this.$tableBody.appendChild(this.$el);
        this.$container.insertAdjacentHTML('afterend', '<div class="clearfix"></div>');
        // alert(this.$container.parentNode.innerHTML);

        // this.$el.classList.add(this.options.classes);
        this.$el.className = this.options.classes;
        if (this.options.striped) {
            this.$el.classList.add('table-striped');
        }
        if (this.options.classes.split(' ').includes('table-no-bordered')) {
            this.$tableContainer.classList.add('table-no-bordered');
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
        if (this.$header === null) {
            this.$header = document.createElement('thead')
            this.$el.appendChild(this.$header);
        }
        this.$header.querySelectorAll('tr').forEach(function () {
            var column = [];
            this.querySelectorAll('th').forEach(function () {
                column.push(Object.assign({}, {
                    title: this.innertext,
                    'class': this.classList,
                    titleTooltip: this['title'],
                    rowspan: this['rowspan'] ? +this['rowspan'] : undefined,
                    colspan: this['colspan'] ? +this['colspan'] : undefined
                }, this.dataset));
            });
            columns.push(column);
        });

        if (!Array.isArray(this.options.columns[0])) {
            this.options.columns = [this.options.columns];// 都处理成两维数组的形式  

        }
        this.options.columns = Object.assign([], columns, this.options.columns);

        // 借用this.columns[fieldIndex]=column构建this.columns;  
        // this.column的数据格式为{[column]}，列坐标相同的标题栏取靠后的子标题;  
        // 意义：填充表体内容时，this.column提供每列数据的相关信息;  
        this.columns = [];

        // setFieldIndex将标题栏的fieldIndex属性赋值为标题栏所在列坐标;  
        Utils.setFieldIndex(this.options.columns);
        // console.log('12' + this.options.columns)
        this.options.columns.forEach(function (columns, i) {

            // Object.entries(columns).forEach(function (column, j) {
            columns.forEach(function (column, j) {
                // console.log([column])//[key, value]
                column = Object.assign({}, BootstrapTable.COLUMN_DEFAULTS, column);

                if (typeof column.fieldIndex !== 'undefined') {
                    that.columns[column.fieldIndex] = column;
                }
                that.options.columns[i][j] = column;
                // console.log(that.options.columns)

            });
        });

        if (this.options.data.length) {
            return;
        }

        this.$el.querySelectorAll('tbody>tr').forEach(function () {
            var row = {};

            // 获取每一行tr的id、class、data属性，以数组形式赋值给data  
            row._id = this.getAttribute('id');
            row._class = this.getAttribute('class');
            row._data = getRealDataAttr(this.dataset);

            // 获取某一行每个子元素的内容、id、class、rowspan、title、data属性  
            this.querySelectorAll('td').forEach(function (_
                , i) {
                //  field通常是后台数据的id号，没有该值的时候赋值为column列坐标信息，写入本地数据的时候  
                var field = that.columns[i].field;

                row[field] = this.innertext;                // save td's id, class and data-* attributes  
                row['_' + field + '_id'] = this.getAttribute('id');
                row['_' + field + '_class'] = this.getAttribute('class');
                row['_' + field + '_rowspan'] = this.getAttribute('rowspan');
                row['_' + field + '_title'] = this.getAttribute('title');
                row['_' + field + '_data'] = getRealDataAttr(this.dataset);
            });
            data.push(row);
        });
        // console.log(data)
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

        this.options.columns.forEach(function (columns, i) {
            html.push('<tr>');

            // 页面以表格显示且有卡片式详情点击按钮的时候，表头首列为该按钮开辟一个空白的单元格  
            if (i == 0 && !that.options.cardView && that.options.detailView) {
                html.push(Utils.sprintf('<th class="detail" rowspan="%s"><div class="fht-cell"></div></th>',
                    that.options.columns.length));
                // console.log('123ab')
            }

            columns.forEach(function (column) {
                var text = '',
                    halign = '',
                    align = '',
                    style = '',
                    class_ = Utils.sprintf(' class="%s"', column['class']),
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

                halign = Utils.sprintf('text-align: %s; ', column.halign ? column.halign : column.align);
                align = Utils.sprintf('text-align: %s; ', column.align);
                style = Utils.sprintf('vertical-align: %s; ', column.valign);
                style += Utils.sprintf('width: %s; ', (column.checkbox || column.radio) && !width ?
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
                html.push('<th' + Utils.sprintf('  title="%s"', column.titleTooltip),
                    column.checkbox || column.radio ?
                        Utils.sprintf(' class="bs-checkbox %s"', column['class'] || '') :
                        class_,
                    Utils.sprintf(' style="%s"', halign + style),
                    Utils.sprintf(' rowspan="%s"', column.rowspan),
                    Utils.sprintf(' colspan="%s"', column.colspan),
                    Utils.sprintf(' data-field="%s"', column.field),
                    "tabindex='0'",
                    '>');

                html.push(Utils.sprintf('<div class="th-inner  %s">', that.options.sortable && column.sortable ?
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
        this.$header.querySelectorAll('th[data-field]').forEach(function (item) {
            // 标题栏data属性写入各自的column数据，展开卡片式详情时使用  
            item.dataset[visibleColumns[item.dataset['field']]];
        });

        // 绑定点击排序事件
        $Event.on(this.$container.querySelector('.th-inner'), function (event) {
            var target = this;
            if (target.closest('.bootstrap-table')[0] !== that.$container[0])
                return false;

            if (that.options.sortable && target.parentNode.dataset.sortable) {
                that.onSort(event);
            }
        });

        // 确认键排序  
        let childrens = this.$header.children
        for (let i = 0; i < childrens.length; i++) {
            if (childrens[i].children.length > 0) {
                let children = childrens[i].children
                for (let j = 0; j < children.length; j++) {
                    $Event.off(children[j], 'keypress')
                    $Event.on(children[j], "keypress", function (event) {
                        if (that.options.sortable && this.dataset.sortable) {
                            var code = event.keyCode || event.which;
                            if (code == 13) { //Enter keycode  
                                that.onSort(event);
                            }
                        }
                    })



                }
            }
        };
        // 显示隐藏表头，调整this.$tableLoading位置;options.cardView为真时卡片式显示隐藏表头  
        if (!this.options.showHeader || this.options.cardView) {
            this.$header.style.display = 'none';
            this.$tableHeader.style.display = 'none';
            this.$tableLoading.style.top = 0;
        } else {
            this.$header.style.display = '';
            this.$tableHeader.style.display = '';
            this.$tableLoading.style.top = this.$header.outerHeight + 1;

            this.getCaret();// 更新排序箭头显示情况  
        }

        // 全选  
        this.$selectAll = Array.from(this.$header.querySelectorAll('[name="btSelectAll"]'));
        this.$selectAll.forEach(item => {
            // item.indeterminate = false,
            $Event.on(item, 'click', function () {
                var checked = this['checked'];
                that[checked ? 'checkAll' : 'uncheckAll']();// 改变复选框勾选状态，更新上传数据  
                that.updateSelected();// tr添加selected类  
            })
        })
    };


    // 显示隐藏表尾  
    BootstrapTable.prototype.initFooter = function () {
        if (!this.options.showFooter || this.options.cardView) {
            this.$tableFooter.style.display = 'none';
        } else {
            this.$tableFooter.style.display = '';
        }
    };


    // 页面初始化时this.data赋值为this.options.data;  
    // ajax交互时this.data赋值为后台返回的数据，options.data也同样更新为后台返回的数据;  
    // type为append时，表格尾部插入数据，this.data、options.data尾部插入相应数据;  
    // type为prepend时，表格顶部插入数据，this.data、options.data头部插入相应数据;   
    // 前台分页的情况下调用this.initSort，后台分页以返回数据为准;  
    BootstrapTable.prototype.initData = function (data, type) {
        let that = this;
        if (type === 'append') {
            this.data = this.data.concat(data);
        } else if (type === 'prepend') {
            this.data = [].concat(data).concat(this.data);
        } else {
            this.data = data || this.options.data;
        }

        if (this.options.sidePagination === 'server') {
            return;
        }
        this.initSort();
        //    增加treeView
        if (this.options.treeView && this.options.data.length > 0) {
            var rows = [], parentField = this.options.parentField,
                roots = this.options.data.filter(function (row, index) {
                    return !row[parentField] || row[parentField] == 0 || row[parentField] == 'null'
                    // //return row[parentField] == '' || row[parentField] == null || row[parentField] == 'null' || String(row[parentField]).toLowerCase() === "null";
                });

            console.log(roots);
            roots.forEach(function (item, index) {
                rows.push(item);
                var child = Utils.getChild(item, that.options.data, that.options.treeField, that.options.parentField);
                console.log(child);
                child.forEach(function (n, i) {
                    if (that.options.treeCollapseAll) {
                        n.hidden = true;
                    }
                    console.log(n);
                    rows.push(n);
                });
            });


            that.options.data = that.data = rows;

        }
    };
    // onSort方法设置点击排序按钮时，更新options.sortName为相应标题栏column.field值;  
    // initSort由column.field值获得相应的sortName;  
    // 调用option.sorter函数或window[option.sorter]方法进行比较排序;  
    // 或者直接比较data[sortName]进行排序;  
    // 排序通过更新this.data数据实现,this.data渲染到页面使用initBody方法;  
    BootstrapTable.prototype.initSort = function () {
        var that = this,
            name = this.options.sortName,
            order = this.options.sortOrder === 'desc' ? -1 : 1,
            index = -1;
        if (Array.isArray(this.options.sortName)) {
            index = this.options.sortName.indexOf(this.header.fields);
        };
        if (index !== -1) {
            this.data.sort(function (a, b) {
                if (that.header.sortNames[index]) {
                    name = that.header.sortNames[index];// 获取colum.sortName  
                }
                // 获取每行数据的data[sortName]的值，转义后返回  
                var aa = Utils.getItemField(a, name, that.options.escape),
                    bb = Utils.getItemField(b, name, that.options.escape),
                    // 调用column.sorter函数或window[column.sorter]方法进行比较，上下文是that.header  
                    value = Utils.Utils.calculateObjectValue(that.header, that.header.sorters[index], [aa, bb]);

                if (value !== undefined) {
                    return order * value;
                }

                if (aa === undefined || aa === null) {
                    aa = '';
                }
                if (bb === undefined || bb === null) {
                    bb = '';
                }

                if (Utils.isNumeric(aa) && Utils.isNumeric(bb)) {
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

                if (typeof aa !== 'string') {
                    aa = aa.toString();
                }

                if (aa.localeCompare(bb) === -1) {//bb为何不要转换？  
                    return order * -1;
                }

                return order;
            });
        }
    };

    // 点击排序时更新options.sortName为被排序列数据对应column[field]值，以便initSort获取sortName;  
    // 更新options.sortOrder为被排序列数据对应column[order]值，或保持原有值;  
    // 触发sort事件，调用initServer获取后台数据，调用initSort排序、initBody渲染表体;  
    BootstrapTable.prototype.onSort = function (event) {
        var $this = event.type === "keypress" ? event.currentTarget : event.currentTarget.parentNode,
            $this_ = this.$header.querySelectorAll('th')[$this.index()];// 记录this.$header下相同元素  

        this.$header.querySelectorAll('span.order').forEach(item => item.remove());
        this.$header_.querySelectorAll('span.order').forEach(item => item.remove());

        // options.sortName更新被排序列数据对应column[field]值，以便initSort获取sortName加以比较;  
        if (this.options.sortName === $this.data['field']) {
            this.options.sortOrder = this.options.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.options.sortName = $this.data['field'];
            this.options.sortOrder = $this.data['order'] === 'asc' ? 'desc' : 'asc';
        }
        $Event.trigger(this.$el, 'sort-change', {
            sortName: this.options.sortName, sortOrder: this.options.sortOrder
        })
            ;
        $this.dataset.order = this.options.sortOrder;
        $this_.dataset.order = this.options.sortOrder;
        this.getCaret();// 更新排序箭头样式  

        if (this.options.sidePagination === 'server') {
            this.initServer(this.options.silentSort);
            return;
        }

        this.initSort();
        this.initBody();
    };

    // 创建工具栏内的用户自定义按钮组、分页显示隐藏切换按钮、刷新按钮、筛选条目按钮  
    // 以及卡片表格显示切换按钮、搜索框，并绑定相应事件；  
    // 筛选条目时触发column-switch事件;  
    BootstrapTable.prototype.initToolbar = function () {
        var that = this,
            html = [],
            timeoutId = 0,
            $keepOpen,
            $search,
            switchableCount = 0;

        if (this.$toolbar.querySelector('.bs-bars')?.children.length) {
            // cannot read property of undefined报错的五种解决方案https://juejin.cn/post/7013545448308899870
            document.querySelector('body').append(this.options.toolbar);
        }
        this.$toolbar.innerHTML = '';

        if (typeof this.options.toolbar === 'string' || typeof this.options.toolbar === 'object') {
            this.$toolbar.append(Utils.sprintf('<div class="bars pull-%s"></div>', this.options.toolbarAlign))
            this.$toolbar.append(this.options.toolbar);
            // $(this.options.toolbar)引用对象形式，只会在页面上创建一次  
        }

        html = [Utils.sprintf('<div class="columns columns-%s btn-group pull-%s">',
            this.options.buttonsAlign, this.options.buttonsAlign)];

        if (typeof this.options.icons === 'string') {
            // 调用window[options.icons]函数显示按钮列表  
            this.options.icons = Utils.Utils.calculateObjectValue(null, this.options.icons);
        }

        // 显示隐藏分页按钮  
        if (this.options.showPaginationSwitch) {
            html.push(Utils.sprintf('<button class="btn btn-default" type="button" name="paginationSwitch" title="%s">',
                this.options.formatPaginationSwitch()),
                Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.paginationSwitchDown),
                '</button>');
        }

        // 刷新按钮  
        if (this.options.showRefresh) {
            html.push(Utils.sprintf('<button class="btn btn-default' +
                Utils.sprintf(' btn-%s', this.options.iconSize) +
                '" type="button" name="refresh" title="%s">',
                this.options.formatRefresh()),
                Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.refresh),
                '</button>');
        }

        // 卡片式显示或表格详情显示切换按钮  
        if (this.options.showToggle) {
            html.push(Utils.sprintf('<button class="btn btn-default' +
                Utils.sprintf(' btn-%s', this.options.iconSize) +
                '" type="button" name="toggle" title="%s">',
                this.options.formatToggle()),
                Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.toggle),
                '</button>');
        }

        // 筛选条目按钮，并创建下拉列表  
        if (this.options.showColumns) {
            html.push(Utils.sprintf('<div class="keep-open btn-group" title="%s">',
                this.options.formatColumns()),
                '<button type="button" class="btn btn-default' +
                Utils.sprintf(' btn-%s', this.options.iconSize) +
                ' dropdown-toggle" data-toggle="dropdown">',
                Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.columns),
                ' <span class="caret"></span>',
                '</button>',
                '<ul class="dropdown-menu" role="menu">');

            this.columns.forEach(function (column, i) {
                if (column.radio || column.checkbox) {
                    return;
                }

                if (that.options.cardView && (!column.cardVisible)) {
                    return;
                }

                var checked = column.visible ? ' checked="checked"' : '';

                if (column.switchable) {
                    html.push(Utils.sprintf('<li>' +
                        '<label><input type="checkbox" data-field="%s" value="%s"%s> %s</label>' +
                        '</li>', column.field, i, checked, column.title));
                    switchableCount++;
                }
            });
            html.push('</ul>',
                '</div>');
        }

        html.push('</div>');

        if (this.showToolbar || html.length > 2) {
            this.$toolbar.append(html.join(''));
        }

        // 绑定分页显示隐藏按钮点击事件  
        if (this.options.showPaginationSwitch) {
            let paginationSwitch = this.$toolbar.querySelector('button[name="paginationSwitch"]')
            $Event.off(paginationSwitch, 'click');
            $Event.off(paginationSwitch, 'click', this.togglePagination.bind(this));
        }

        // 绑定刷新按钮点击事件  
        if (this.options.showRefresh) {
            let refresh = this.$toolbar.querySelector('button[name="refresh"]')
            $Event.off(refresh, 'click');
            $Event.on(refresh, 'click', this.refresh.bind(this));
        }

        // 绑定卡片式显示、表格详情显示切换按钮点击事件  
        if (this.options.showToggle) {
            let toggle = this.$toolbar.querySelector('button[name="toggle"]')
            $Event.off(toggle, 'click');
            $Event.on(toggle, 'click', function () { that.toggleView() });
        }

        // 帮点筛选条目下拉列表中复选框的点击事件，筛选条目按钮点击事件由bootstrap提供  
        if (this.options.showColumns) {
            $keepOpen = this.$toolbar.querySelector('.keep-open');

            if (switchableCount <= this.options.minimumCountColumns) {
                $keepOpen.querySelectorAll('input').forEach(elem => elem['disabled'] = true);
            }

            $keepOpen.querySelectorAll('li').forEach(elem => {
                $Event.off(elem, 'click');
                $Event.on(elem, 'click', function (event) {
                    event.stopImmediatePropagation();// 阻止事件冒泡，并阻止同类型事件的冒泡  
                })
            });
            $keepOpen.querySelectorAll('input').forEach(elem => {
                $Event.off(elem, 'click');
                $Event.on(elem, 'click',
                    function () {
                        var $this = this;

                        that.toggleColumn(Utils.getFieldIndex(that.columns,
                            this.dataset.field), $this['checked'], false);
                        that.trigger('column-switch', { field: this.dataset.field, checked: $this['checked'] });
                    })
            });
        }

        // 创建搜索框，并绑定搜索事件  
        if (this.options.search) {
            html = [];
            html.push(
                '<div class="pull-' + this.options.searchAlign + ' search">',
                Utils.sprintf('<input class="form-control' +
                    Utils.sprintf(' input-%s', this.options.iconSize) +
                    '" type="text" placeholder="%s">', this.options.formatSearch()),
                '</div>');
            // console.log(this.options.formatSearch())
            this.$toolbar.insertAdjacentHTML('beforeend', html.join(''));
            $search = this.$toolbar.querySelector('.search input');
            $Event.off($search, 'keyup drop');
            $Event.on($search, 'keyup drop',
                function (event) {
                    if (that.options.searchOnEnterKey) {
                        if (event.keyCode !== 13) {
                            return;
                        }
                    }

                    clearTimeout(timeoutId);
                    timeoutId = setTimeout(function (event) {
                        $search = event.currentTarget
                        that.onSearch({ currentTarget: $search });
                    }, that.options.searchTimeOut);
                });

            if (Utils.isIEBrowser()) {
                $Event.off($search, 'mouseup');
                $Event.on($search, 'mouseup',
                    function (event) {
                        clearTimeout(timeoutId);
                        timeoutId = setTimeout(function (event) {
                            $search = event.currentTarget
                            that.onSearch({ currentTarget: $search });
                        }, that.options.searchTimeOut);
                    });
            }
        }
    };

    // this.text，this.options.text设为搜索框去除两端空白的值，pageNumber设为1;  
    // 调用initSearch将筛选本地数据;调用updatePagination完成远程交互或单渲染本地数据;  
    // 触发search事件;  
    BootstrapTable.prototype.onSearch = function (event) {
        console.log(event)
        var text = event.currentTarget.value.trim();

        if (this.options.trimOnSearch && event.currentTarget.value !== text) {
            event.currentTarget.value = text;
        }

        if (text === this.searchText) {
            return;
        }
        this.searchText = text;
        this.options.searchText = text;

        this.options.pageNumber = 1;
        this.initSearch();
        this.updatePagination();
        this.trigger('search', text);
    };

    // 前台分页的情况下，先通过this.filterColumns通过this.option.data过滤this.data数据;  
    // 再通过搜索文本过滤this.data数据;  
    // 输入文本和经this.header.formatters或window[this.header.formatters]函数格式化匹配比对;  
    BootstrapTable.prototype.initSearch = function () {
        var that = this;

        if (this.options.sidePagination !== 'server') {
            var s = this.searchText && this.searchText.toLowerCase();
            var f = Utils.isEmptyObject(this.filterColumns) ? null : this.filterColumns;

            // options.data和this.filterColumns相符则在this.data中保留，不相符则在this.data中删除  
            this.data = f ? this.options.data.filter(function (item, i) {
                for (var key in f) {
                    if (Array.isArray(f[key])) {
                        if (f[key].indexOf(item[key]) === -1) {
                            return false;
                        }
                    } else if (item[key] !== f[key]) {
                        return false;
                    }
                }
                return true;
            }) : this.options.data;

            // 在前台分页的情况下检索数据，使用$.grep返回筛选后的数组内容  
            this.data = s ? this.data.filter(function (item, i) {
                for (var key in item) {
                    key = Utils.isNumeric(key) ? parseInt(key, 10) : key;
                    var value = item[key],//data[key]  
                        // 当key为field时，getFieldIndex获取相应列条目数据fieldIndex值，否则返回-1  
                        // 问题，可以设置if语句排除key不等于field的情况，j和index等值  
                        column = that.columns[Utils.Utils.getFieldIndex(that.columns, key)],
                        j = that.header.fields.indexOf(key);

                    if (column && column.searchFormatter) {
                        value = Utils.Utils.calculateObjectValue(column,
                            that.header.formatters[j], [value, item, i], value);
                    }

                    var index = that.header.fields.indexOf(key);
                    if (index !== -1 && that.header.searchables[index] && (typeof value === 'string' || typeof value === 'number')) {
                        if (that.options.strictSearch) {
                            if ((value + '').toLowerCase() === s) {
                                return true;
                            }
                        } else {
                            if ((value + '').toLowerCase().indexOf(s) !== -1) {
                                return true;
                            }
                        }
                    }
                }
                return false;
            }) : this.data;
        }
    };

    // 初始化设置分页相关页面信息显示情况，包括当前页显示第几条到第几天数据，共几条数据，每页显示几条数据;  
    // 以及每页显示数据量切换按钮，选择页面的分页栏显示情况，再绑定事件;  
    // 通过options.pageNumber获取this.pageFrom、this.pageTo，以便前台分页时initBody获取相应数据;  
    BootstrapTable.prototype.initPagination = function () {
        if (!this.options.pagination) {
            this.$pagination.style.display = 'none';
            return;
        } else {
            this.$pagination.style.display = '';
        }

        var that = this,
            html = [],
            $allSelected = false,// 为真时，显示所有数据条目，同时显示数据量切换按钮文本改为options.formatAllRows()  
            i, from, to,
            $pageList,
            $first, $pre,
            $next, $last,
            $number,
            data = this.getData();

        if (this.options.sidePagination !== 'server') {
            this.options.totalRows = data.length;// 数据总条数  
        }

        // this.options.totalRows数据总条数;  
        // this.options.pageSize一页显示几条数据，显示数据量切换按钮默认文本;  
        // this.totalPages总页数，与this.options.totalPages似没有差别，疑为插件作者未调优代码;  
        // this.options.totalPages总页数;  
        // this.options.pageNumber当前页页码;  
        // this.pageFrom当前页从总数据的第几条开始;  
        // this.pageTo当前页到总数据的第几条为止;  
        if (this.options.totalRows) {
            // 当options.pageSize和options.formatAllRows()相同时，意味显示所有条目  
            // 或者options.pageSize即为options.totalRows总条目数，且options.formatAllRows()在pageList设置中  
            // $allSelected记为真，页面显示数据量切换按钮的显示文本为options.formatAllRows()  
            if (this.options.pageSize === this.options.formatAllRows()) {
                this.options.pageSize = this.options.totalRows;
                $allSelected = true;
            } else if (this.options.pageSize === this.options.totalRows) {
                var pageLst = typeof this.options.pageList === 'string' ?
                    this.options.pageList.replace('[', '').replace(']', '')
                        .replace(/ /g, '').toLowerCase().split(',') : this.options.pageList;// 每页显示数据条数列表项  
                if (pageLst.indexOf(this.options.formatAllRows().toLowerCase()) > -1) {
                    $allSelected = true;
                }
            }

            this.totalPages = ~~((this.options.totalRows - 1) / this.options.pageSize) + 1;//~~()取整操作
            // -1针对this.options.totalRows是this.options.pageSize倍数的情况  

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

        // 分页提示文案，即总共包含几条数据，或当前页从第几条到第几条  
        html.push(
            '<div class="pull-' + this.options.paginationDetailHAlign + ' pagination-detail">',
            '<span class="pagination-info">',
            this.options.onlyInfoPagination ? this.options.formatDetailPagination(this.options.totalRows) :
                this.options.formatShowingRows(this.pageFrom, this.pageTo, this.options.totalRows),
            '</span>');

        if (!this.options.onlyInfoPagination) {
            html.push('<span class="page-list">');

            // 分页提示文案，即每页显示几条数据，每页显示数据量下拉列表  
            // var pageNumber = [Utils.sprintf('<div class="btn-group %s">', this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ?
            // 'dropdown' : 'dropup'),
            // '<select  class="form-select' + Utils.sprintf(' btn-%s', this.options.iconSize) + '" id="sel2" name="sellist2">',
            // '<option class="page-size">', $allSelected ? this.options.formatAllRows() : this.options.pageSize,
            // '</option> ',],

            var pageNumber = [
                Utils.sprintf('<span class="btn-group %s">',
                    this.options.paginationVAlign === 'top' || this.options.paginationVAlign === 'both' ?
                        'dropdown' : 'dropup'),
                '<button type="button" class="btn btn-default ' +
                Utils.sprintf(' btn-%s', this.options.iconSize) +
                ' dropdown-toggle" data-bs-toggle="dropdown" >',
                '<span class="page-size">',
                $allSelected ? this.options.formatAllRows() : this.options.pageSize,
                '</span>',
                ' <span class="caret"></span>',
                '</button>',
                '<ul class="dropdown-menu" role="menu">'
            ],
                pageList = this.options.pageList;

            // 每页切换条目数下拉列表实现  
            if (typeof this.options.pageList === 'string') {
                var list = this.options.pageList.replace('[', '').replace(']', '')
                    .replace(/ /g, '').split(',');

                pageList = [];
                list.forEach(function (value) {
                    pageList.push(value.toUpperCase() === that.options.formatAllRows().toUpperCase() ?
                        that.options.formatAllRows() : +value);
                });
            }

            pageList.forEach(function (page, i) {
                // this.options.smartDisplay为真，当总页数为1时，屏蔽分页，以及下拉列表仅有一条时，屏蔽切换条目数按钮下拉功能  
                if (!that.options.smartDisplay || i === 0 || pageList[i - 1] <= that.options.totalRows) {

                    var active;
                    if ($allSelected) {
                        active = page === that.options.formatAllRows() ? ' class="active"' : '';
                    } else {
                        active = page === that.options.pageSize ? ' class="active"' : '';
                    }
                    // pageNumber.push(Utils.sprintf('<option%s>%s</option>', active, page));

                    pageNumber.push(Utils.sprintf('<li%s><a href="javascript:void(0)">%s</a></li>', active, page));
                }
            });
            // pageNumber.push('</select>');
            pageNumber.push('</ul></span>');

            html.push(this.options.formatRecordsPerPage(pageNumber.join('')));
            html.push('</div>');

            // 分页  
            // 策略：通过from初始页、to结尾页，先设置首页起的显示情况，再设置...按钮的显示情况，接着尾页的显示情况  
            // 顺序设置，由一般到具体  
            html.push('</div>',
                '<div class="pull-' + this.options.paginationHAlign + ' pagination">',
                '<ul class="pagination' + Utils.sprintf(' pagination-%s', this.options.iconSize) + '">',
                '<li class="page-pre"><a href="javascript:void(0)">' + this.options.paginationPreText + '</a></li>');

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

            // 总页数大于6时，显示第一页，最后一页，pageNumber--，pageNumber，pageNumber++，以及两串...  
            if (this.totalPages >= 6) {
                if (this.options.pageNumber >= 3) {
                    html.push('<li class="page-first' + (1 === this.options.pageNumber ? ' active' : '') + '">',
                        '<a href="javascript:void(0)">', 1, '</a>',
                        '</li>');

                    from++;
                }

                if (this.options.pageNumber >= 4) {
                    // from--显示第二页按钮  
                    if (this.options.pageNumber == 4 || this.totalPages == 6 || this.totalPages == 7) {
                        from--;
                    } else {
                        html.push('<li class="page-first-separator disabled">',
                            '<a href="javascript:void(0)">...</a>',
                            '</li>');
                    }

                    to--;
                }
            }


            // 根据上一条if语句form++的情况，pageNumber临近尾页的时候执行from--，显示后五条  
            if (this.totalPages >= 7) {
                if (this.options.pageNumber >= (this.totalPages - 2)) {
                    from--;
                }
            }

            // 根据上一条if语句to--的情况，pageNumber挨近尾页的时候执行to--，显示后五条  
            if (this.totalPages == 6) {
                if (this.options.pageNumber >= (this.totalPages - 2)) {
                    to++;
                }
            } else if (this.totalPages >= 7) {
                if (this.totalPages == 7 || this.options.pageNumber >= (this.totalPages - 3)) {
                    to++;
                }
            }

            for (i = from; i <= to; i++) {
                html.push('<li class="page-number' + (i === this.options.pageNumber ? ' active' : '') + '">',
                    '<a href="javascript:void(0)">', i, '</a>',
                    '</li>');
            }

            if (this.totalPages >= 8) {
                if (this.options.pageNumber <= (this.totalPages - 4)) {
                    html.push('<li class="page-last-separator disabled">',
                        '<a href="javascript:void(0)">...</a>',
                        '</li>');
                }
            }

            if (this.totalPages >= 6) {
                if (this.options.pageNumber <= (this.totalPages - 3)) {
                    html.push('<li class="page-last' + (this.totalPages === this.options.pageNumber ? ' active' : '') + '">',
                        '<a href="javascript:void(0)">', this.totalPages, '</a>',
                        '</li>');
                }
            }

            html.push(
                '<li class="page-next"><a href="javascript:void(0)">' + this.options.paginationNextText + '</a></li>',
                '</ul>',
                '</div>');
        }
        this.$pagination.innerHTML = html.join('');

        if (!this.options.onlyInfoPagination) {
            $pageList = this.$pagination.querySelectorAll('.page-list a');// 每页显示数据量切换按钮  
            $first = this.$pagination.querySelector('.page-first');
            $pre = this.$pagination.querySelector('.page-pre');
            $next = this.$pagination.querySelector('.page-next');
            $last = this.$pagination.querySelector('.page-last');
            $number = this.$pagination.querySelectorAll('.page-number');

            if (this.options.smartDisplay) {
                if (this.totalPages <= 1) {
                    this.$pagination.querySelector('div.pagination').style.display = 'none';
                }
                if (pageList.length < 2 || this.options.totalRows <= pageList[0]) {
                    this.$pagination.querySelector('span.page-list').style.display = 'none';
                }

                this.$pagination.style.display = this.getData().length ? '' : 'none';
            }

            if ($allSelected) {
                this.options.pageSize = this.options.formatAllRows();
            }

            // 绑定事件 
            $pageList.forEach(function (page) {
                $Event.on($Event.off(page, 'click'), 'click', that.onPageListChange.bind(that));
            });

            $Event.on($Event.off($first, 'click'), 'click', this.onPageFirst.bind(this));
            $Event.on($Event.off($pre, 'click'), 'click', this.onPagePre.bind(this));
            $Event.on($Event.off($next, 'click'), 'click', this.onPageNext.bind(this));
            $Event.on($Event.off($last, 'click'), 'click', this.onPageLast.bind(this));
            $number.forEach(function (number) {
                $Event.on($Event.off(number, 'click'), 'click', that.onPageNumber.bind(that));
            });
        }
    };

    // 分页点选按钮有disabled属性则返回，无则重新布局分页显示面板;  
    // maintainSelected为否时，调用resetRows重置复选框为不选中，调用initServer交互或initbody渲染页面;  
    // initSever由后台返回数据;  
    // initPagination通过options.pageNumber取得options.pageFrom、options.pageTo;  
    // initBody由options.pageFrom、options.pageTo获取需要渲染的数据data;  
    // 触发page-change事件;  
    BootstrapTable.prototype.updatePagination = function (event) {
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


        const event_ = new CustomEvent('page-change', { detail: (this.options.pageNumber, this.options.pageSize) });

        this.trigger('page-change', [this.options.pageNumber, this.options.pageSize]);



    };

    // 每页显示数据量下拉列表选中时触发，替换每页显示数据量按钮文本;  
    // 更新options.pageSize，通过updatePagination调用initPagination设置this.pageFrom、this.pageTo;  
    // updatePagination再调用initServer完成交互，或initBody渲染本地数据;  
    BootstrapTable.prototype.onPageListChange = function (event) {
        var $this = event.currentTarget;
        $this.parentNode.classList.add('active')
        let childrens = $this.parentNode.children
        for (let i = 0; i < childrens.length; i++) { // 遍历所有兄弟节点，移除active类;
            if (childrens[i].nodeType === 1 && childrens[i] !== $this) { // 排除文本节点;
                childrens[i].classList.remove('active')
            }
        };
        this.options.pageSize = $this.textContent.toUpperCase() === this.options.formatAllRows().toUpperCase() ?
            this.options.formatAllRows() : +$this.textContent;
        this.$pagination.querySelector('.page-size').textContent = this.options.pageSize;
        this.updatePagination(event);
    };

    // 更新options.pageNumber,通过updatePagination调用initPagination设置this.pageFrom、this.pageTo;  
    // updatePagination再调用initServer完成交互，或initBody渲染本地数据;  
    // 跳转分页首页  
    BootstrapTable.prototype.onPageFirst = function (event) {
        this.options.pageNumber = 1;
        this.updatePagination(event);
    };
    // 跳转分页上一页  
    BootstrapTable.prototype.onPagePre = function (event) {
        if ((this.options.pageNumber - 1) == 0) {
            this.options.pageNumber = this.options.totalPages;
        } else {
            this.options.pageNumber--;
        }
        this.updatePagination(event);
    };
    // 跳转分页下一页  
    BootstrapTable.prototype.onPageNext = function (event) {
        if ((this.options.pageNumber + 1) > this.options.totalPages) {
            this.options.pageNumber = 1;
        } else {
            this.options.pageNumber++;
        }
        this.updatePagination(event);
    };
    // 跳转尾页  
    BootstrapTable.prototype.onPageLast = function (event) {
        this.options.pageNumber = this.totalPages;
        this.updatePagination(event);
    };
    // 由页码跳转  
    BootstrapTable.prototype.onPageNumber = function (event) {
        if (this.options.pageNumber === +event.currentTarget.textContent) {
            return;
        }
        this.options.pageNumber = +event.currentTarget.textContent;
        this.updatePagination(event);
    };

    BootstrapTable.prototype.initRow = function (item, i, data, parentDom) {
        var that = this,
            key,
            html = [],
            style = {},
            csses = [],
            data_ = '',
            attributes = {},
            htmlAttributes = [];
        if (this.hiddenRows.indexOf(item) > -1) {
            return;
        }
        style = Utils.calculateObjectValue(this.options, this.options.rowStyle, [item, i], style);
        if (style && style.css) {
            for (key in style.css) {
                csses.push(key + ': ' + style.css[key]);
            }
        }
        // 通过options.rowAttributes(row,index)函数或window[options.rowAttributes](row,index)获取tbody>
        attributes = Utils.calculateObjectValue(this.options,
            this.options.rowAttributes, [item, i], attributes);
        if (attributes) {
            for (key in attributes) {
                htmlAttributes.push(Utils.sprintf('%s="%s"', key, Utils.escapeHTML(attributes[key])));
            }
        }
        // 通过row._data，row._id，row._class，row[options.uniqueId]渲染tb
        if (item._data && !Utils.isEmptyObject(item._data)) {
            item._data.forEach(function (k, v) {
                if (k === 'index') {
                    return;
                }
                data_ += Utils.sprintf(' data-%s="%s"', k, v);
            });
        }
        html.push('<tr',
            Utils.sprintf(' %s', htmlAttributes.join(' ')),
            Utils.sprintf(' id="%s"', Array.isArray(item) ? undefined : item._id),
            Utils.sprintf(' class="%s"', style.classes || (Array.isArray(item) ? undefined : item._class)),
            Utils.sprintf(' data-index="%s"', i),
            Utils.sprintf(' data-uniqueid="%s"', item[this.options.uniqueId]),
            Utils.sprintf('%s', data_),
            '>'
        );
        // 卡片式显示跨列  
        if (this.options.cardView) {
            html.push(Utils.sprintf('<td colspan="%s">', this.header.fields.length));
        }
        // 表格显示时添加每行数据前点击展示卡片式详情按钮  
        if (!this.options.cardView && this.options.detailView) {
            html.push('<td>',
                '<a class="detail-icon" href="#">',
                Utils.sprintf('<i class="%s %s"></i>', this.options.iconsPrefix, this.options.icons.detailOpen),
                '</a>',
                '</td>');
        }
        // 遍历this.header.fields获取主键field值，再由主键field拼接row中的属性取值，包括row[field]  
        // 显示文本row[field]调用对应的this.header.formatter[j]处理后获取  
        // j即列坐标  
        this.header.fields.forEach(function (field, j) {
            var text = '',
                value = Utils.getItemField(item, field, that.options.escape),// 获取row[field]  
                type = '',
                cellStyle = {},
                id_ = '',
                class_ = that.header.classes[j],
                data_ = '',
                rowspan_ = '', colspan_ = '',
                title_ = '',
                // column = that.columns[Utils.getFieldIndex(that.columns, field)];
                column = that.columns[j];
            if (that.fromHtml && typeof value_ === 'undefined') {
                return;
            }
            if (!column.visible) {// 筛选时设置  
                return;
            }
            if (that.options.cardView && (!column.cardVisible)) {
                return;
            }
            if (column.escape) {
                value_ = Utils.escapeHTML(value_);
            }


            style = Utils.sprintf('style="%s"', csses.concat(that.header.styles[j]).join('; '));
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
                colspan_ = sprintf(' colspan="%s"', item['_' + field + '_colspan']);
            }
            if (item['_' + field + '_title']) {
                title_ = Utils.sprintf(' title="%s"', item['_' + field + '_title']);
            }
            // 调用that.header.cellStyles[j](item.field,item,i)设置单元格显示样式  
            cellStyle = Utils.calculateObjectValue(that.header,
                that.header.cellStyles[j], [value, item, i], cellStyle);
            if (cellStyle.classes) {
                class_ = Utils.sprintf(' class="%s"', cellStyle.classes);
            }
            if (cellStyle.css) {
                var csses_ = [];
                for (var key in cellStyle.css) {
                    csses_.push(key + ': ' + cellStyle.css[key]);
                }
                style = Utils.sprintf('style="%s"', csses_.concat(that.header.styles[j]).join('; '));
            }
            // 调用that.header.formatters[j](item.field,item,i)格式化显示内容
            // 特别当单元格是复选框的时候，value返回值可以是对象形式{checked:true;disabled:true}，此时无显
            value = Utils.calculateObjectValue(column,
                that.header.formatters[j], [value, item, i], value);
            if (item['_' + field + '_data'] && !Utils.isEmptyObject(item['_' + field + '_data'])) {
                item['_' + field + '_data'].forEach(function (k, v) {
                    if (k === 'index') {
                        return;
                    }
                    data_ += Utils.sprintf(' data-%s="%s"', k, v);
                });
            }
            if (column.checkbox || column.radio) {
                type = column.checkbox ? 'checkbox' : type;
                type = column.radio ? 'radio' : type;
                text = [Utils.sprintf(that.options.cardView ?
                    '<div class="card-view %s">' : '<td class="bs-checkbox %s">', column['class'] || ''),
                '<input' +
                Utils.sprintf(' data-index="%s"', i) +
                Utils.sprintf(' name="%s"', that.options.selectItemName) +
                Utils.sprintf(' type="%s"', type) +
                Utils.sprintf(' value="%s"', item[that.options.idField]) +
                Utils.sprintf(' checked="%s"', value === true ||
                    (value && value.checked) ? 'checked' : undefined) +
                Utils.sprintf(' disabled="%s"', !column.checkboxEnabled ||
                    (value && value.disabled) ? 'disabled' : undefined) +
                ' />',
                that.header.formatters[j] && typeof value === 'string' ? value : '',
                that.options.cardView ? '</div>' : '</td>'
                ].join('');
                // 复选框上传内容字段名属性后添加true选中/false未选中值  
                item[that.header.stateField] = value === true || (value && value.checked);
            } else {
                value = typeof value === 'undefined' || value === null ?
                    that.options.undefinedText : value;
                //tree 实现
                // var indent, icon;
                // if (that.options.treeView && column.field == that.options.expandField) {
                // var rows = [], parentField = this.options.parentField,
                // roots = data.filter(function (row, index) {
                // return !row[parentField] || row[parentField] == 0 || row[parentField] == 'null'
                // return row[parentField] == '' || row[parentField] == null || row[parentFiel
                // });
                // roots.forEach(function (i, item) {
                // var tr = $('<tr></tr>');
                // tr.addClass('treegrid-' + (j + i));
                // $.each(options.columns, function (index, column) {
                // var td = $('<td></td>');
                // td.text(item[column.field]);
                // tr.append(td);
                // });
                // tbody.append(tr);
                // });

                // var indent = item.Level == that.options.Level ? '' : Utils.sprintf('<span style="margi
                //   var child = data.filter(function (d, i) {
                // return d.parentField == item[that.options.parentField] && !d.hidden;
                // });
                // icon = Utils.sprintf('<span class="tree-icon %s" style="cursor: pointer; margin: 0px 5
                //icon = sprintf('<span class="tree-icon %s" style="cursor: pointer; margin: 0px 5px;"
                //   }
                // 结束
                // getPropertyFromOther卡片式显示时获取标题栏的文本内容  
                text = that.options.cardView ? ['<div class="card-view">',
                    that.options.showHeader ? Utils.sprintf('<span class="title" %s>%s</span>', style,
                        Utils.getPropertyFromOther(that.columns, 'field', 'title', field)) : '',
                    Utils.sprintf('<span class="value">%s</span>', value),
                    '</div>'
                ].join('') : [Utils.sprintf('<td%s %s %s %s %s %s %s>', id_, class_, style, data_, rowspan_, colspan_, title_),
                    value, //indent, icon,
                    '</td>'
                ].join('');
                // Hide empty data on Card view when smartDisplay is set to true.
                if (that.options.cardView && that.options.smartDisplay && value === '') {
                    // 占位符，以利于根据元素序号准确地绑定事件  
                    text = '<div class="card-view"></div>';
                }
            }
            html.push(text);
        });
        if (this.options.cardView) {
            html.push('</div></td>');
        }
        html.push('</tr>');
        return html.join(' ');

    };
    // fixedScroll为否的情况下，表体移动到顶部;  
    // 通过this.pageFrom、this.pageTo截取this.getData()数据row渲染表体，主要是tbody>tr以及tbody>tr>td;  
    // tbody>tr的data-index设为行号，class、id为row._class、row._id，样式、data数据通过调用函数获得;  
    // tbody>tr>td区分为卡片显示和表格显示两类，显示值取经this.header.formatters[i]处理后的row[field];  
    // tbody>tr>td其他class、id、title、data取row[_field_class]等;  
    // 绑定展开卡片详情按钮点击事件、复选框点击事件、this.header.events中的事件;  
    // 触发post-body、pre-body事件;   
    BootstrapTable.prototype.initBody = function (fixedScroll) {
        var that = this,
            html = [],
            data = this.getData();// 获取搜索过滤后的数据  
        // console.log(data);
        // data的数据格式为对象形式  
        // [{   // 行tr中的属性设置  
        //      _data:{  
        //          index:1,// 后续会自动赋值为数据在当前页的所在行号  
        //          field:field  
        //      },  
        //      _id:id,  
        //      _class:class,  
        //      field1:value1,field2:value2, //填充在单元格中的显示内容，从this.header.fields数组中获取属性名field1等  
        //      _field_id  
        // }] // 每一行特定的样式、属性根据this.options.rowStyle、this.options.rowAttributes获取  
        // 数组形式  
        // [["field","class"]] // 数组形式不能对每一行添加特定的data属性、id以及class  
        //                     // 特定的的样式、属性仍可由this.options.rowStyle、this.options.rowAttributes获取  
        //                     // 以及data-index添加行号、data-uniqueId每行的唯一标识，根据options.uniqueId从data中获取  
        //                       
        // tr以及checkbox中data数组的序号data-index，以便于获取data[data-index]数据调用  
        // 触发pre-body事件，传递data数据
        this.trigger('pre-body', data);
        this.$body = this.$el.querySelector('tbody');
        if (!this.$body) {
            this.$body = document.createElement('tbody')
            this.$el.appendChild(this.$body);
            // console.log('!this.$body')
        }// 页面初始化存在tbody>tr>td的情况下，this.options.data数据由initTable获取  

        //Fix #389 Bootstrap-table-flatJSON is not working  
        // 未作分页或后台分页的情况返回所有数据  
        if (!this.options.pagination || this.options.sidePagination === 'server') {
            this.pageFrom = 1;
            this.pageTo = data.length;
        }
        var hasTr, trFragments = document.createDocumentFragment();

        for (var i = this.pageFrom - 1; i < this.pageTo; i++) {
            var item = data[i],
                tr = this.initRow(item, i, data, trFragments);
            hasTr = hasTr || !!tr;
            if (tr && tr !== true) {
                trFragments.append(tr);
            }
        }
        // show no records
        if (!hasTr) {
            trFragments.append('<tr class="no-records-found">' +
                Utils.sprintf('<td colspan="%s">%s</td>',
                    this.$header.querySelectorAll('th').length,
                    this.options.formatNoMatches()) +
                '</tr>');
        }
        // this.$body.appendChild(trFragments); // html.join('');
        this.$body.innerHTML = trFragments.textContent
        if (!fixedScroll) {
            this.scrollTo(0);
        }

        // 点击单元格触发单元格以及当前行点击事件，复选框则勾选  
        this.$body.querySelectorAll(' tr[data-index] > td').forEach(td => {
            $Event.on($Event.off(td, 'click dblclick'), 'click dblclick',
                function (e) {
                    var $td = this,
                        $tr = $td.parentNode,
                        item = that.data[$tr.dataset.index],// 获取当前行的data[data-index]数据调用  
                        index = $td.cellIndex,// 返回一行内单元格所在的列坐标  
                        fields = that.getVisibleFields(),
                        field = fields[that.options.detailView && !that.options.cardView ? index - 1 : index],
                        // field = that.header.fields[that.options.detailView && !that.options.cardView ? index - 1 : index],
                        column = that.columns[Utils.getFieldIndex(that.columns, field)],
                        value = Utils.getItemField(item, field, that.options.escape);
                    if ($td.querySelectorAll('.detail-icon').length) {
                        return;
                    }
                    // console.log('field:', field, 'value:', value, 'item:', item, '$td:', $td)
                    // 单元格点击事件传入单元格的field（借此获取data中的有关数据）、显示内容value值data[data-index][field]、  
                    // 当前行data数据item值data[data-index]、单元格jquery对象$td  
                    that.trigger(e.type === 'click' ? 'click-cell' : 'dbl-click-cell', field, value, item, $td);
                    that.trigger(e.type === 'click' ? 'click-row' : 'dbl-click-row', item, $tr, field);
                    // if click to select - then trigger the checkbox/radio click
                    if (e.type === 'click' && that.options.clickToSelect && column.clickToSelect) {
                        var $selectItem = $tr.querySelectorAll(Utils.sprintf('[name="%s"]', that.options.selectItemName));
                        if ($selectItem.length) {
                            $selectItem[0].click(); // #144: .trigger('click') bug  
                        }
                    }
                });
        });

        // 展开折叠卡片式详情  
        this.$body.querySelectorAll(' tr[data-index] > td > .detail-icon').forEach(item => {
            $Event.on($Event.off(item, 'click'),
                function () {
                    var $this = this,
                        $tr = $this.parentNode.parentNode,
                        index = $tr.dataset.index,
                        row = data[index];// Fix #980 Detail view, when searching, returns wrong row
                    if ($tr.nextSibling.matches('tr.detail-view')) {
                        $this.querySelectorAll('i').forEach(v => v.classList.add(Utils.sprintf('%s %s', that.options.iconsPrefix, that.options.icons.detailOpen)));
                        $tr.nextSibling.remove();
                        that.trigger('collapse-row', index, row);
                    } else {
                        $this.querySelectorAll('i').forEach(v => v.classList.add(Utils.sprintf('%s %s', that.options.iconsPrefix, that.options.icons.detailClose)));
                        $tr.insertAdjacentHTML('afterEnd', Utils.sprintf('<tr class="detail-view"><td colspan="%s"></td></tr>', $tr.querySelectorAll('td').length));
                        var $element = $tr.nextSibling.querySelectorAll('td');
                        // options.detailFormatter执行后渲染折叠式卡片详情文本内容，包含html标签、Dom元素  
                        var content = Utils.calculateObjectValue(that.options, that.options.detailFormatter, [index, row, $element], '');
                        if ($element.length === 1) {
                            $element.forEach(item => item.insertAdjacentHTML('beforeEnd', content));
                        }

                        that.trigger('expand-row', index, row, $element);
                    }
                    that.resetView();
                });
        });
        //tree
        // this.$body.querySelectorAll(' tr[data-index] > td > .tree-icon').forEach(item => {
        // $Event.on($Event.off(item, 'click'), function (e) {
        // debugger;
        // e.stopPropagation();
        // var $this = this,
        // $tr = $this.parent().parent(),
        // index = $tr.data('index'),
        // row = data[index],
        // var icon = $(this);
        // child = Utils.getChild(data[index], data, that.options.parentField);
        // child.forEach(function (c, i) {
        // that.data.forEach(function (item, index) {
        // if (item[that.options.parentField] == c[that.options.parentField]) {
        // item.hidden = $this.classList.contains(that.options.expandIcon);
        // that.uncheck(index);
        // return;
        // }
        // });
        // });
        // if ($this.classList.contains(that.options.expandIcon)) {
        // $this.classList.remove(that.options.expandIcon).classList.add(that.options.collapseIcon);
        // } else {
        // $this.classList.remove(that.options.collapseIcon).classList.add(that.options.expandIcon);
        // }
        // that.options.data = that.data;
        // that.initBody(true);
        // })
        // });

        // 绑定复选框点击事件  
        this.$selectItem = this.$body.querySelectorAll(Utils.sprintf('[name="%s"]', this.options.selectItemName));
        console.log('this.$selectItem:', this.$selectItem);
        this.$selectItem.forEach(item => {
            $Event.on($Event.off(item, 'click'), 'click',
                function (event) {
                    event.stopImmediatePropagation();

                    var $this = this,
                        checked = $this['checked'],
                        row = that.data[$this.dataset.index];

                    if (that.options.maintainSelected && $this.matches("[type='radio']")) {
                        that.options.data.forEach(function (row) {
                            row[that.header.stateField] = false;
                        });
                    }

                    row[that.header.stateField] = checked;

                    if (that.options.singleSelect) {
                        that.$selectItem.filter(v => { return v !== $this; }).forEach(function (item) {
                            that.data[item.dataset.index][that.header.stateField] = false;
                        });
                        that.$selectItem.filter(item => item['checked'] == true).filter(
                            v => v !== $this).forEach(v => v['checked'] = false);
                    }

                    that.updateSelected();
                    that.trigger(checked ? 'check' : 'uncheck', row, $this);
                })
        });

        // 由this.header.events为tbody>tr>td中子元素绑定事件  
        this.header.events.forEach(function (events, i) {
            if (!events) {
                return;
            }
            // fix bug, if events is defined with namespace  
            if (typeof events === 'string') {
                events = Utils.calculateObjectValue(null, events);
            }

            var field = that.header.fields[i],
                fieldIndex = that.getVisibleFields().indexOf(field);

            if (that.options.detailView && !that.options.cardView) {
                fieldIndex += 1;
            }

            for (var key in events) {
                that.$body.querySelectorAll('tr:not(.no-records-found)').forEach(function () {
                    var $tr = this,
                        $td = $tr.querySelector(that.options.cardView ? '.card-view' : 'td')[fieldIndex],
                        index = key.indexOf(' '),
                        name = key.substring(0, index),
                        el = key.substring(index + 1),
                        func = events[key];
                    // $td.find(el).off(name).on(name, function (e) { TODO
                    $td.querySelectorAll(el).forEach(item => {
                        $Event.on($Event.off(item, name), name, function (e) {
                            var index = $tr.dataset['index'],
                                row = that.data[index],
                                value = row[field];
                            func.apply(this, [e, value, row, index]);
                        })
                    });
                });
            }
        });

        this.updateSelected();
        this.resetView();

        this.trigger('post-body');
    };

    // 触发ajax事件（可以是用户自定义的方法options.ajax），上传数据格式为  
    // {  
    //      searchText:this.searchText,  
    //      sortName:this.options.sortName,  
    //      sortOrder:this.options.sortOrder,  
    //      pageSize/limit:...,  
    //      pageNumber/offset:...,  
    //      [filter]:...,  
    //      query:...  
    // }  
    // 触发上传成功调用this.load方法，触发load-success事件、上传失败load-error事件  
    BootstrapTable.prototype.initServer = function (silent, query) {
        var that = this,
            data = {},
            params = {
                searchText: this.searchText,
                sortName: this.options.sortName,
                sortOrder: this.options.sortOrder
            },
            request;// ajax配置  

        if (this.options.pagination) {
            params.pageSize = this.options.pageSize === this.options.formatAllRows() ?
                this.options.totalRows : this.options.pageSize;
            params.pageNumber = this.options.pageNumber;
        }

        if (!this.options.url && !this.options.ajax) {
            return;
        }

        // 意义？？？  
        if (this.options.queryParamsType === 'limit') {
            params = {
                search: params.searchText,
                sort: params.sortName,
                order: params.sortOrder
            };
            if (this.options.pagination) {
                params.limit = this.options.pageSize === this.options.formatAllRows() ?
                    this.options.totalRows : this.options.pageSize;
                params.offset = this.options.pageSize === this.options.formatAllRows() ?
                    0 : this.options.pageSize * (this.options.pageNumber - 1);
            }
        }

        // this.filterColumnsPartial用于设置后台过滤？？？  
        if (!(Utils.isEmptyObject(this.filterColumnsPartial))) {
            params['filter'] = JSON.stringify(this.filterColumnsPartial, null);
        }

        // 调用options.queryParams处理上传的内容param，包括搜索文本、排序字段、排序方式  
        // 以及当前页显示几条数据、当前页数或limit、offset  
        data = Utils.calculateObjectValue(this.options, this.options.queryParams, [params], data);

        Object.assign(data, query || {});

        if (data === false) {
            return;
        }

        if (!silent) {
            this.$tableLoading.style.display = '';
        }
        request = Object.assign({}, Utils.calculateObjectValue(null, this.options.ajaxOptions), {
            type: this.options.method,
            url: this.options.url,
            data: this.options.contentType === 'application/json' && this.options.method === 'post' ?
                JSON.stringify(data) : data,
            cache: this.options.cache,
            contentType: this.options.contentType,
            dataType: this.options.dataType,
        });

        if (this.options.ajax) {
            Utils.calculateObjectValue(this, this.options.ajax, [request], null);
        } else {
            Utils.$.ajax(request).then(function (res) {
                res = Utils.calculateObjectValue(that.options, that.options.responseHandler, [res], res);
                that.load(res);
                that.trigger('load-success', res);
                if (!silent) that.$tableLoading.style.display = 'none';
            }, function (res) {
                that.trigger('load-error', res.status, res);
                if (!silent) that.$tableLoading.style.display = 'none';
            })
        }
    };

    // 初始化若设置搜索文本，开启搜索，不支持本地数据搜索  
    BootstrapTable.prototype.initSearchText = function () {
        if (this.options.search) {
            if (this.options.searchText !== '') {
                var $search = this.$toolbar.querySelector('.search input');
                $search.value = this.options.searchText;
                this.onSearch({ currentTarget: $search });
            }
        }
    };

    // getCaret改变排序点击箭头的上下方向  
    BootstrapTable.prototype.getCaret = function () {
        var that = this;

        this.$header.querySelectorAll('th').forEach(function (th, i) {

            th.querySelectorAll('.sortable').forEach(item => {
                item.classList.remove('desc asc')
                item.classList.add($th.dataset['field'] === that.options.sortName ? that.options.sortOrder : 'both');
            })
        });
    };

    // 全选以及全不选时改变全选复选框的勾选状态，以及tr行添加或删除selected类  
    BootstrapTable.prototype.updateSelected = function () {
        var $selectItems = [].filter.call(this.$selectItem, (w) => w.disabled === false),
            checkAll = $selectItems.length &&
                $selectItems.length ===
                [].filter.call($selectItems, ((w) => w.checked === true)).length;

        if (this.$selectAll_) this.$selectAll.push(this.$selectAll_);
        this.$selectAll.forEach(element => {
            if (element) element['checked'] = checkAll;
        });
        this.$selectItem.forEach(function (item) {
            item['checked'] ? item.closest('tr').classList.add('selected') : item.closest('tr').classList.remove('selected');
        });
    };

    // 复选框选中或撤销选中后更新this.data数据中的[this.header.stateField]属性，以便上传复选框的状态  
    BootstrapTable.prototype.updateRows = function () {
        var that = this;

        this.$selectItem.forEach(function (item) {
            that.data[item.dataset['index']][that.header.stateField] = item['checked'];
        });
    };

    // 重置，撤销复选框选中，以及data[i][that.header.stateField]赋值为false  
    BootstrapTable.prototype.resetRows = function () {
        var that = this;

        this.data.forEach(function (row, i) {
            that.$selectAll['checked'] = false;
            that.$selectItem['checked'] = false;
            if (that.header.stateField) {
                row[that.header.stateField] = false;
            }
        });
    };

    // 执行this.options[BootstrapTable.EVENTS[name]]函数(类似浏览器默认事件)，并触发事件  
    BootstrapTable.prototype.trigger = function (name) {
        var args = [].slice.call(arguments, 1);
        name += '.bs.table';
        this.options[BootstrapTable.EVENTS[name]].apply(this.options, args);
        Utils.trigger(this.$el, name, args);

        this.options.onAll(name, args);
        Utils.trigger(this.$el, 'all.bs.table', args);
    };

    // 一定时间内触发this.fitHeader函数调整表头的水平偏移，垂直滚动不影响表头  
    BootstrapTable.prototype.resetHeader = function () {
        // fix #61: the hidden table reset header bug.  
        // fix bug: get $el.css('width') error sometime (height = 500)  
        clearTimeout(this.timeoutId_);
        this.timeoutId_ = setTimeout(this.fitHeader.bind(this), this.$el.matches(':hidden') ? 100 : 0);
    };

    // 克隆this.$el中的表头，置入this.$tableHeader中，出使垂直滚动时，表头信息不变  
    // 调整表体水平偏移量和表体水平一致  
    BootstrapTable.prototype.fitHeader = function () {
        var that = this,
            fixedBody,
            scrollWidth,
            focused,
            focusedTemp;

        if (that.$el.matches(':hidden')) {
            that.timeoutId_ = setTimeout(that.fitHeader.bind(that), 100);
            return;
        }
        fixedBody = this.$tableBody;// 包裹表单的.fixed-table-body元素  

        // .fixed-table-container有固定高度，其子元素.fixed-table-body超过该高度就显示滚动条  
        scrollWidth = fixedBody.scrollWidth > fixedBody.clientWidth &&
            fixedBody.scrollHeight > fixedBody.clientHeight + this.$header.outerHeight() ?
            Utils.getScrollBarWidth() : 0;

        this.$el.style.marginTop = -this.$header.outerHeight();

        // 表头聚焦的元素添加focus-temp类，从而使this.$tableHeader的同个元素获得焦点  
        focused = document.querySelectorAll(':focus');
        if (focused.length > 0) {
            focused.forEach(elem => {
                let $th = Utils.parents(elem, 'th');
                if ($th.length > 0) {
                    $th.forEach(elem => {
                        var dataField = elem['data-field'];
                        if (dataField !== undefined) {
                            var $headerTh = this.$header.querySelectorAll("[data-field='" + dataField + "']");
                            if ($headerTh.length > 0) {
                                $headerTh.forEach(elem => {
                                    elem.querySelectorAll(":input").forEach(elem => elem.classList.add("focus-temp"));
                                })
                            }
                        }
                    })
                }
            })
        };

        this.$header_ = this.$header.cloneNode(true);
        this.$selectAll_ = this.$header_.querySelector('[name="btSelectAll"]');
        this.$tableHeader.style.marginRight = scrollWidth;
        let $headertable = this.$tableHeader.querySelector('table');
        $headertable.style.width = this.$el.outerWidth();

        $headertable.innerHTML = ''
        $headertable.append(this.$header_);
        $headertable['class'] = this.$el.attr('class');


        focusedTemp = document.querySelectorAll('.focus-temp:visible')[0];
        if (focusedTemp.length > 0) {
            focusedTemp.focus();
            this.$header.querySelectorAll('.focus-temp').forEach(
                elem => elem.classList.remove('focus-temp')
            );
        }

        // fix bug: $.data() is not working as expected after $.append()  
        // that.$header_是jquery对象，如果改变了this的值，$(this).data()获取内容和bug是咋回事？？？  
        this.$header.querySelectorAll('th[data-field]').forEach(function () {
            that.$header_.querySelectorAll(Utils.sprintf('th[data-field="%s"]', this.dataset['field'])).forEach(
                function () { this.dataset[this.dataset]; }
            );
        });

        var visibleFields = this.getVisibleFields();

        // 标题栏单元格中的.fht-cell元素和表格中元素的宽度相一致，意义？？？  
        this.$body.querySelectorAll('tr:first-child:not(.no-records-found) > *').forEach((element, i) => {
            var $this = element,
                index = i;
            if (that.options.detailView && !that.options.cardView) {
                if (i === 0) {
                    that.$header_.querySelectorAll('th.detail').forEach(element => {
                        element.querySelectorAll('.fht-cell').forEach(
                            function () { this.style.width = $this.innerWidth() + 'px'; }
                        );

                    });
                }
                index = i - 1;
            }
        });
        that.$header_.querySelectorAll(Utils.sprintf('th[data-field="%s"]', visibleFields[index])).forEach(
            function () {
                this.querySelectorAll('.fht-cell').forEach(
                    function () { this.style.width = $this.innerWidth() + 'px'; }
                );

            });

        // 当窗口缩放时，出现滚动条，表头表尾水平偏移情况相当  
        this.$tableBody.onscroll = function () {
            that.$tableHeader.scrollLeft = this.scrollLeft();

            if (that.options.showFooter && !that.options.cardView) {
                that.$tableFooter.scrollLeft = this.scrollLeft();
            }
        };
        that.trigger('post-header');
    };

    // 创建表尾，利用footerFormatter填充表尾内容，调用fitFooter调整表尾偏移  
    BootstrapTable.prototype.resetFooter = function () {
        var that = this,
            data = that.getData(),
            html = [];

        if (!this.options.showFooter || this.options.cardView) {
            return;
        }

        if (!this.options.cardView && this.options.detailView) {
            html.push('<td><div class="th-inner">&nbsp;</div><div class="fht-cell"></div></td>');
        }

        this.columns.forEach(function (column) {
            var falign = '',
                style = '',
                class_ = Utils.sprintf(' class="%s"', column['class']);

            if (!column.visible) {
                return;
            }

            if (that.options.cardView && (!column.cardVisible)) {
                return;
            }

            falign = Utils.sprintf('text-align: %s; ', column.falign ? column.falign : column.align);
            style = Utils.sprintf('vertical-align: %s; ', column.valign);

            html.push('<td', class_, Utils.sprintf(' style="%s"', falign + style), '>');
            html.push('<div class="th-inner">');

            html.push(Utils.calculateObjectValue(column, column.footerFormatter, [data], '&nbsp;') || '&nbsp;');

            html.push('</div>');
            html.push('<div class="fht-cell"></div>');
            html.push('</div>');
            html.push('</td>');
        });

        this.$tableFooter.querySelectorAll('tr').forEach(
            function (tr) { tr.innerHTML = html.join(''); }
        );
        clearTimeout(this.timeoutFooter_);
        this.timeoutFooter_ = setTimeout(this.fitFooter.bind(this),
            this.$el.matches(':hidden') ? 100 : 0);
    };

    // 调整表尾水平偏移，设置表尾fnt-cell的宽度  
    BootstrapTable.prototype.fitFooter = function () {
        var that = this,
            $footerTd,
            elWidth,
            scrollWidth;

        clearTimeout(this.timeoutFooter_);
        if (this.$el.matches(':hidden')) {
            this.timeoutFooter_ = setTimeout(this.fitFooter.bind(this), 100);
            return;
        }

        elWidth = this.$el.style.width;
        scrollWidth = elWidth > this.$tableBody.clientWidth ? getScrollBarWidth() : 0;

        this.$tableFooter.style.marginRight = scrollWidth + 'px';
        his.$tableFooter.querySelectorAll('table').forEach(
            function (table) {
                table.style.width = elWidth + 'px';
                table['class'] = this.$el['class'];
            }
        );


        $footerTd = this.$tableFooter.query('td');

        this.$body.querySelectorAll('tr:first-child:not(.no-records-found) > *').forEach(function (tr, i) {
            var $this = tr;

            $footerTd[i].querySelectorAll('.fht-cell').forEach(element => {
                element.style.width = $this.innerWidth();

            });
        });
    };

    // toggleColumn筛选条目下拉菜单点选时更新columns[i].visible信息;  
    // this.columns信息的改变，重新调用表头、表体、搜索框、分页初始化函数;  
    // 当勾选的显示条目小于this.options.minimumCountColumns时，勾选的条目设置disabled属性;  
    BootstrapTable.prototype.toggleColumn = function (index, checked, needUpdate) {
        if (index === -1) {
            return;
        }
        this.columns[index].visible = checked;

        this.initHeader();
        this.initSearch();
        this.initPagination();
        this.initBody();

        if (this.options.showColumns) {// this.options.showColumns显示筛选条目按钮  
            var $items = this.$toolbar.querySelectorAll('.keep-open input').forEach(ki => ki['disabled'] = false);

            if (needUpdate) {
                $items.filter(itm => itm['value'] === index).forEach(
                    itm => itm.setAttribute('checked', checked));
            }

            if ($items.querySelectorAll(':checked').length <= this.options.minimumCountColumns) {
                $items.querySelectorAll(':checked').forEach(itm => itm.setAttribute('disabled', true))
                    ;
            }
        }
    };

    // 从表体中找到data-index=index或data-uniqueid=uniqueId那一行，根据visible显示或隐藏  
    BootstrapTable.prototype.toggleRow = function (index, uniqueId, visible) {
        if (index === -1) {
            return;
        }

        this.$body.querySelectorAll(typeof index !== 'undefined' ?
            Utils.sprintf('tr[data-index="%s"]', index) :
            Utils.sprintf('tr[data-uniqueid="%s"]', uniqueId)).forEach(function (row) {
                row.style.display = visible ? '' : 'none';

            })
    };

    // 从this.column中剔除visible为false的项，返回field数组  
    BootstrapTable.prototype.getVisibleFields = function () {
        var that = this,
            visibleFields = [];

        this.header.fields.forEach(function (field) {
            // this.columns以列坐标:数据的形式保存  
            var column = that.columns[Utils.getFieldIndex(that.columns, field)];

            if (!column.visible) {
                return;
            }
            visibleFields.push(field);
        });
        return visibleFields;
    };



    /**公共方法：通过bootstrap(fnName,argunments)调用 
     * 
     * resetView(): 
     *     调整表体的高度; 
     * getData(): 
     *     搜索过滤后的数据保存在this.data中，过滤前数据保存在options.data,针对数据在前台的情况; 
     *     有过滤数据，返回过滤数据this.data，无则返回未过滤数据this.options.data; 
     *     前台分页，获取this.pageFrom-1到this.pageTo的data数据或者整个data数据; 
     * load(): 
     *     使用后台传回的数据或本地data数据更新data、搜索框、分页、表体显示; 
     *     后台传回数据格式为{total:,rows:,[fixedScroll]:}; 
     * append(): 
     *     从表格尾部插入数据; 
     * prepend(): 
     *     从表格头部插入数据; 
     * remove(): 
     *     移除指定行数据，通过行数据row中的某个属性比较删除拥有相同值的行数据data; 
     *     param数据格式为{field:paramName,values:paramValues},paramName、paramValues和data对应; 
     * removeAll(): 
     *     移除所有行数据; 
     * getRowByUniqueId(): 
     *     获取row[options.uniqueId]或者row._data[options.uniqueId]同id相等的某一行数据;  
     * removeByUniqueId(): 
     *     移除row[options.uniqueId]或者row._data[options.uniqueId]同id相等的某一行数据; 
     * updateByUniqueId(): 
     *     更新替换某一行数据，参数格式为{id:row[options.uniqueId],row:row替换数据}; 
     * insertRow(): 
     *     在某一行后插入数据，参数格式为{index:index行号,row:row插入数据内容}; 
     * updateRow(): 
     *     更新替换某一行数据，参数格式为{index:index行号,row:row替换数据}; 
     * showRow(): 
     *     根据{[index:index],[uniqueid:uniqueId]}找到某一行，显示; 
     * hideRow(): 
     *     根据{[index:index],[uniqueid:uniqueId]}找到某一行，隐藏; 
     * getRowsHidden():   
     *     获取并返回隐藏的行，根据show将这些行数据显示出来; 
     * mergeCells(): 
     *     合并单元格，传参为{index:index.field:field,rowspan:3,colspan:4}; 
     *     隐藏被合并单元格，重新设置显示单元格rowspan、colspan属性; 
     * updateCell(): 
     *     更新单元的显示文本，传参为{index:index,field:field,value:value}，根据index、field找到单元格; 
     * getOptions(): 
     *     返回配置项; 
     * getSelections(): 
     *     通过过滤后的数据this.data返回选中行的数据; 
     * getAllSelections(): 
     *     通过未过滤的数据this.options.data返回选中行的数据; 
     * checkAll(): 
     *     全选; 
     * unCheckAll(): 
     *     全不选; 
     * checkInvert(): 
     *     反选; 
     * checkAll_(): 
     *     全选或全不选执行函数; 
     * check(): 
     *     选中; 
     * unCheck(): 
     *     取消选中; 
     * check_(): 
     *     选中、取消选中执行函数; 
     * checkBy(): 
     *     选中某几行数据; 
     * unCheckBy(): 
     *     取消选中某几行数据; 
     * checkBy_(): 
     *     根据条件选中、取消选中某几行数据执行函数，obj参数格式为{field:paramName,values:paramValues}; 
     * destory(): 
     *     移出触发元素，其内容、样式通过this.$el_改为初始值，移除构造函数添加最外层包裹元素this.$container; 
     * showLoading(): 
     *     显示后台数据载入文案; 
     * hideLoading(): 
     *     隐藏后台数据载入文案; 
     * togglePagination(): 
     *     分页切换按钮显示隐藏分页内容; 
     * refresh(): 
     *     刷新页面到第一页，传入参数为{url:url,slient:slient,query:query}; 
     * resetWidth(): 
     *     调用fitHeader、fitFooter函数调整表头、表尾的宽度; 
     * showColumn(): 
     *     根据field属性获得fieldIndex，再调用toggleColumn显示某列; 
     * hideColumn(): 
     *     根据field属性获得fieldIndex，再调用toggleColumn隐藏某列; 
     * getHiddenColumns(): 
     *     获得隐藏的某几列; 
     * filterBy(): 
     *     设置过滤数组this.filterColumns; 
     *     options.data和this.filterColumns相符则在this.data中保留，不相符则在this.data中删除; 
     *     设置页码为1，重新调用initSearch、updatePagination渲染表格;  
     * scrollTo(): 
     *     设置this.$tableBody滚动条的垂直偏移，意义是移动到第几行数据; 
     * getScrollPosition(): 
     *     表体滚动到顶部; 
     * selectPage(): 
     *     设置this.options.pageNumber当前页，调用updatePagination更新表体，initBody或initServer方法; 
     * prevPage(): 
     * nextPage(): 
     *     上一页，下一页; 
     * toggleView(): 
     *     切换卡片式显示或者表格详情显示; 
     * refreshView(): 
     *     更新传入的配置项options，调用destory重置，init重新渲染页面; 
     * resetSearch(): 
     *     设置搜索框文本，启动数据搜索; 
     * expandRow_(): 
     *     表格详情显示时，折叠展开按钮执行函数; 
     * expandRow(): 
     *     展开对应行的卡片详情; 
     * collapseRow(): 
     *     折叠对应行的卡片详情; 
     * expandAllRows(): 
     *     expandAllRows展开所有卡片式详情，在表格显示的时候; 
     *     isSubTable为真，展开父子表格的详情; 
     * collapseAllRows(): 
     *     expandAllRows展开所有卡片式详情，在表格显示的时候; 
     * updateFormatText(): 
     *     更新配置项中的格式化函数; 
     */

    // 调整表体的高度  
    BootstrapTable.prototype.resetView = function (params) {
        var padding = 0, that = this;

        if (params && params.height) {
            this.options.height = params.height;
        }

        this.$selectAll.forEach(element => {
            if (element) {
                element.setAttribute('checked', that.$selectItem.length > 0 &&
                    that.$selectItem.length === [].filter.call(that.$selectItem, item => item.checked === true).length)
            }
        });

        if (this.options.height) {
            var toolbarHeight = getRealHeight(this.$toolbar),
                paginationHeight = getRealHeight(this.$pagination),
                height = this.options.height - toolbarHeight - paginationHeight;

            this.$tableContainer.style.height = height + 'px';
        }

        if (this.options.cardView) {
            this.$el.style.marginTop = '0';
            this.$tableContainer.style.paddingBottom = '0';
            return;
        }

        if (this.options.showHeader && this.options.height) {
            this.$tableHeader.style.display = '';
            this.resetHeader();
            padding += this.$header.outerHeight();
        } else {
            this.$tableHeader.style.display = 'none';
            this.trigger('post-header');
        }

        if (this.options.showFooter) {
            this.resetFooter();
            if (this.options.height) {
                padding += this.$tableFooter.outerHeight() + 1;
            }
        }

        this.getCaret();
        this.$tableContainer.style.paddingBottom = padding + 'px';
        this.trigger('reset-view');
    };

    //  过滤或搜索过滤后的数据保存在this.data中，过滤前的数据保存在this.options.data,针对数据在前台的情况;  
    //  有过滤数据，返回过滤数据this.data，无则返回未过滤数据this.options.data;  
    //  前台分页，获取this.pageFrom-1到this.pageTo的data数据或者整个data数据;  
    BootstrapTable.prototype.getData = function (useCurrentPage) {
        return (this.searchText || !Utils.isEmptyObject(this.filterColumns || {}) || !Utils.isEmptyObject(this.filterColumnsPartial || {})) ?
            (useCurrentPage ? this.data.slice(this.pageFrom - 1, this.pageTo) : this.data) :
            (useCurrentPage ? this.options.data.slice(this.pageFrom - 1, this.pageTo) : this.options.data);
    };

    // 使用后台传回的数据或本地data数据更新data、搜索框、分页、表体显示  
    // 后台传回数据格式为{total:,rows:,[fixedScroll]:}  
    BootstrapTable.prototype.load = function (data) {
        var fixedScroll = false;

        // #431: support pagination  
        if (this.options.sidePagination === 'server') {
            this.options.totalRows = data.total;
            fixedScroll = data.fixedScroll;
            data = data[this.options.dataField];
        } else if (!Array.isArray(data)) { // support fixedScroll  
            fixedScroll = data.fixedScroll;
            data = data.data;
        }

        this.initData(data);
        this.initSearch();
        this.initPagination();
        this.initBody(fixedScroll);
    };

    // 从表格尾部插入数据  
    BootstrapTable.prototype.append = function (data) {
        this.initData(data, 'append');
        this.initSearch();
        this.initPagination();
        this.initSort();
        this.initBody(true);
    };

    // 从表格头部插入数据  
    BootstrapTable.prototype.prepend = function (data) {
        this.initData(data, 'prepend');
        this.initSearch();
        this.initPagination();
        this.initSort();
        this.initBody(true);
    };

    // 移除指定行数据，通过行数据row中的某个属性比较删除拥有相同值的行数据data  
    // param数据格式为{field:paramName,values:paramValues},paramName、paramValues和data对应  
    /** var ids = $.map($table.bootstrapTable('getSelections'), function (row) { 
            return row.id; 
        }); 
        $table.bootstrapTable('remove', { 
            field: 'id', 
            values: ids 
        }); 
    */
    BootstrapTable.prototype.remove = function (params) {
        var len = this.options.data.length,
            i, row;

        if (!params.hasOwnProperty('field') || !params.hasOwnProperty('values')) {
            return;
        }

        for (i = len - 1; i >= 0; i--) {
            row = this.options.data[i];

            if (!row.hasOwnProperty(params.field)) {
                continue;
            }
            if (params.values.indexOf(row[params.field]) !== -1) {
                this.options.data.splice(i, 1);
            }
        }

        if (len === this.options.data.length) {
            return;
        }

        this.initSearch();
        this.initPagination();
        this.initSort();
        this.initBody(true);
    };

    // 移除所有行数据  
    BootstrapTable.prototype.removeAll = function () {
        if (this.options.data.length > 0) {
            this.options.data.splice(0, this.options.data.length);
            this.initSearch();
            this.initPagination();
            this.initBody(true);
        }
    };

    // 获取row[options.uniqueId]或者row._data[options.uniqueId]同id相等的某一行数据  
    BootstrapTable.prototype.getRowByUniqueId = function (id) {
        var uniqueId = this.options.uniqueId,
            len = this.options.data.length,
            dataRow = null,
            i, row, rowUniqueId;

        for (i = len - 1; i >= 0; i--) {
            row = this.options.data[i];

            if (row.hasOwnProperty(uniqueId)) { // uniqueId is a column  
                rowUniqueId = row[uniqueId];
            } else if (row._data.hasOwnProperty(uniqueId)) { // uniqueId is a row data property  
                rowUniqueId = row._data[uniqueId];
            } else {
                continue;
            }

            if (typeof rowUniqueId === 'string') {
                id = id.toString();
            } else if (typeof rowUniqueId === 'number') {
                if ((Number(rowUniqueId) === rowUniqueId) && (rowUniqueId % 1 === 0)) {
                    id = parseInt(id);
                } else if ((rowUniqueId === Number(rowUniqueId)) && (rowUniqueId !== 0)) {
                    id = parseFloat(id);
                }
            }

            if (rowUniqueId === id) {
                dataRow = row;
                break;
            }
        }

        return dataRow;
    };

    // 移除row[options.uniqueId]或者row._data[options.uniqueId]同id相等的某一行数据  
    BootstrapTable.prototype.removeByUniqueId = function (id) {
        var len = this.options.data.length,
            row = this.getRowByUniqueId(id);

        if (row) {
            this.options.data.splice(this.options.data.indexOf(row), 1);
        }

        if (len === this.options.data.length) {
            return;
        }

        this.initSearch();
        this.initPagination();
        this.initBody(true);
    };

    // 更新替换某一行数据，参数格式为{id:row[options.uniqueId],row:row替换数据}  
    BootstrapTable.prototype.updateByUniqueId = function (params) {
        var rowId;

        if (!params.hasOwnProperty('id') || !params.hasOwnProperty('row')) {
            return;
        }

        rowId = this.options.data.indexOf(this.getRowByUniqueId(params.id));

        if (rowId === -1) {
            return;
        }

        Object.assign(this.data[rowId], params.row);
        this.initSort();
        this.initBody(true);
    };

    // 在某一行后插入数据，参数格式为{index:index行号,row:row插入数据内容}  
    BootstrapTable.prototype.insertRow = function (params) {
        if (!params.hasOwnProperty('index') || !params.hasOwnProperty('row')) {
            return;
        }
        this.data.splice(params.index, 0, params.row);
        this.initSearch();
        this.initPagination();
        this.initSort();
        this.initBody(true);
    };

    // 更新替换某一行数据，参数格式为{index:index行号,row:row替换数据}  
    BootstrapTable.prototype.updateRow = function (params) {
        if (!params.hasOwnProperty('index') || !params.hasOwnProperty('row')) {
            return;
        }
        Object.assign(this.data[params.index], params.row);
        this.initSort();
        this.initBody(true);
    };

    BootstrapTable.prototype.initHiddenRows = function () {
        this.hiddenRows = [];
    };
    // 根据{[index:index],[uniqueid:uniqueId]}找到某一行，显示  
    BootstrapTable.prototype.showRow = function (params) {
        if (!params.hasOwnProperty('index') && !params.hasOwnProperty('uniqueId')) {
            return;
        }
        this.toggleRow(params.index, params.uniqueId, true);
    };

    // 根据{[index:index],[uniqueid:uniqueId]}找到某一行，隐藏  
    BootstrapTable.prototype.hideRow = function (params) {
        if (!params.hasOwnProperty('index') && !params.hasOwnProperty('uniqueId')) {
            return;
        }
        this.toggleRow(params.index, params.uniqueId, false);
    };

    // 获取并返回隐藏的行，根据show将这些行数据显示出来  
    BootstrapTable.prototype.getRowsHidden = function (show) {
        var rows = this.$body[0].children.filter(
            function (row) { return row.style.display === 'none'; }//offsetParent === null
        ),
            i = 0;
        if (show) {
            for (; i < rows.length; i++) {
                rows[i].style.display = '';
            }
        }
        return rows;
    };

    // 合并单元格，传参为{index:index.field:field,rowspan:3,colspan:4}  
    // 隐藏被合并单元格，重新设置显示单元格rowspan、colspan属性  
    BootstrapTable.prototype.mergeCells = function (options) {
        var row = options.index,
            col = this.getVisibleFields().indexOf(options.field),
            rowspan = options.rowspan || 1,
            colspan = options.colspan || 1,
            i, j,
            $tr = this.$body.querySelectorAll('tr'),
            $td;

        if (this.options.detailView && !this.options.cardView) {
            col += 1;
        }

        $td = $tr[row].querySelectorAll('td')[col];

        if (row < 0 || col < 0 || row >= this.data.length) {
            return;
        }

        for (i = row; i < row + rowspan; i++) {
            for (j = col; j < col + colspan; j++) {
                $tr[i].querySelectorAll('td')[j].style.display === 'none';
            }
        }

        $td.setAttribute('rowspan', rowspan)
        $td.setAttribute('colspan', colspan)
        $td.style.display = '';
    };

    // 更新单元的显示文本，传参为{index:index,field:field,value:value}，根据index、field找到单元格  
    BootstrapTable.prototype.updateCell = function (params) {
        if (!params.hasOwnProperty('index') ||
            !params.hasOwnProperty('field') ||
            !params.hasOwnProperty('value')) {
            return;
        }
        this.data[params.index][params.field] = params.value;

        if (params.reinit === false) {
            return;
        }
        this.initSort();
        this.initBody(true);
    };

    // 返回配置项  
    BootstrapTable.prototype.getOptions = function () {
        return this.options;
    };

    // 通过过滤后的数据this.data返回选中行的数据  
    BootstrapTable.prototype.getSelections = function () {
        var that = this;

        return this.data.filter(function (row) {
            return row[that.header.stateField];
        });
    };

    // 通过未过滤的数据this.options.data返回选中行的数据  
    BootstrapTable.prototype.getAllSelections = function () {
        var that = this;

        return this.options.data.filter(function (row) {
            return row[that.header.stateField];
        });
    };

    // 执行全选  
    BootstrapTable.prototype.checkAll = function () {
        this.checkAll_(true);
    };

    // 执行全不选  
    BootstrapTable.prototype.uncheckAll = function () {
        this.checkAll_(false);
    };

    // 反选，调用updateRows执行initSort、initBody，调用updateSelect为行元素tr添加selected类  
    BootstrapTable.prototype.checkInvert = function () {
        var that = this;
        var rows = that.$selectItem.filter(itm => !itm.disabled);
        var checked = rows.filter(itm => itm.checked === true);
        rows.forEach(function () {
            this.setAttribute('checked', !this.checked);
        });
        that.updateRows(); 29
        that.updateSelected();
        that.trigger('uncheck-some', { check: checked });
        checked = that.getSelections();
        that.trigger('check-some', { check: checked });
    };

    // 全选或全不选执行函数，为什么这时又不像所在的行添加selected类？？？  
    BootstrapTable.prototype.checkAll_ = function (checked) {
        var rows;

        if (!checked) {
            rows = this.getSelections();
        }
        if (this.$selectAll_) this.$selectAll.push(this.$selectAll_);
        this.$selectAll.forEach(function (item) {
            item.checked = checked;
        }
        );
        //全选按钮
        [].filter.call(this.$selectItem, function (item) {
            return !item.disabled;
        }).forEach(function (item) { item.checked = checked; });
        this.updateRows();
        if (checked) {
            rows = this.getSelections();
        }
        this.trigger(checked ? 'check-all' : 'uncheck-all', { rows: rows });
    };

    // 选中  
    BootstrapTable.prototype.check = function (index) {
        this.check_(true, index);
    };

    // 取消选中  
    BootstrapTable.prototype.uncheck = function (index) {
        this.check_(false, index);
    };

    // 选中、取消选中执行函数  
    BootstrapTable.prototype.check_ = function (checked, index) {
        var $el = this.$selectItem.filter(
            function () { return this.dataset.index === index; }
        ).forEach(
            function () { this.checked = checked; });
        this.data[index][this.header.stateField] = checked;
        this.updateSelected();
        this.trigger(checked ? 'check' : 'uncheck', { detail: [this.data[index], $el] });
    };

    // 选中某几行数据  
    BootstrapTable.prototype.checkBy = function (obj) {
        this.checkBy_(true, obj);
    };

    // 取消选中某几行数据  
    BootstrapTable.prototype.uncheckBy = function (obj) {
        this.checkBy_(false, obj);
    };

    // 根据条件选中、取消选中某几行数据执行函数，obj参数格式为{field:paramName,values:paramValues}  
    BootstrapTable.prototype.checkBy_ = function (checked, obj) {
        if (!obj.hasOwnProperty('field') || !obj.hasOwnProperty('values')) {
            return;
        }

        var that = this,
            rows = [];
        this.options.data.forEach(function (row, index) {
            if (!row.hasOwnProperty(obj.field)) {
                return false;
            }
            if (obj.values.indexOf(row[obj.field]) !== -1) {
                var $el = that.$selectItem.filter(function () { return this.enabled === true; }).filter(
                    function () { return this.dataset.index === index; }
                ).forEach(function () { this.checked = checked; });
                row[that.header.stateField] = checked;
                rows.push(row);
                that.trigger(checked ? 'check' : 'uncheck', { detail: [row, $el] });
            }
        });
        this.updateSelected();
        this.trigger(checked ? 'check-some' : 'uncheck-some', { detail: rows });
    };

    // 移出触发元素，其内容、样式通过this.$el_改为初始值，移除构造函数添加最外层包裹元素this.$container  
    BootstrapTable.prototype.destroy = function () {
        this.$el.insertAdjacentHTML('beforebegin ', this.$container);
        this.options.toolbar.insertAdjacentHTML('beforebegin ', this.$el);
        this.$container.nextElementSibling.remove();
        this.$container.remove();
        this.$el.innerHTML = this.$el_.innerHTML
        this.$el.style.marginTop = '0'
        this.$el.setAttribute('class', this.$el_['class'] || ''); // reset the class  
    };

    // 显示后台数据载入文案  
    BootstrapTable.prototype.showLoading = function () {
        this.$tableLoading.style.display = '';
    };

    // 隐藏后台数据载入文案  
    BootstrapTable.prototype.hideLoading = function () {
        this.$tableLoading.style.display = 'none';
    };

    // 分页切换按钮显示隐藏分页内容  
    BootstrapTable.prototype.togglePagination = function () {
        this.options.pagination = !this.options.pagination;
        var button = this.$toolbar.querySelector('button[name="paginationSwitch"] i');
        if (this.options.pagination) {
            button.setAttribute("class", this.options.iconsPrefix + " " + this.options.icons.paginationSwitchDown);
        } else {
            button.setAttribute("class", this.options.iconsPrefix + " " + this.options.icons.paginationSwitchUp);
        }
        this.updatePagination();
    };

    // 刷新页面到第一页，传入参数为{url:url,slient:slient,query:query}  
    BootstrapTable.prototype.refresh = function (params) {
        if (params && params.url) {
            this.options.url = params.url;
            this.options.pageNumber = 1;
        }
        this.initServer(params && params.silent, params && params.query);
    };

    // 调用fitHeader、fitFooter函数调整表头、表尾的宽度  
    BootstrapTable.prototype.resetWidth = function () {
        if (this.options.showHeader && this.options.height) {
            this.fitHeader();
        }
        if (this.options.showFooter) {
            this.fitFooter();
        }
    };

    // 根据field属性获得fieldIndex，再调用toggleColumn显示某列  
    BootstrapTable.prototype.showColumn = function (field) {
        this.toggleColumn(Utils.getFieldIndex(this.columns, field), true, true);
    };

    // 根据field属性获得fieldIndex，再调用toggleColumn隐藏某列  
    BootstrapTable.prototype.hideColumn = function (field) {
        this.toggleColumn(Utils.getFieldIndex(this.columns, field), false, true);
    };

    // 获得隐藏的某几列  
    BootstrapTable.prototype.getHiddenColumns = function () {
        return $.grep(this.columns, function (column) {
            return !column.visible;
        });
    };

    // 设置过滤数组this.filterColumns;  
    // options.data和this.filterColumns相符则在this.data中保留，不相符则在this.data中删除;  
    // 设置页码为1，重新调用initSearch、updatePagination渲染表格;  
    BootstrapTable.prototype.filterBy = function (columns) {
        this.filterColumns = Utils.isEmptyObject(columns) ? {} : columns;
        this.options.pageNumber = 1;
        this.initSearch();
        this.updatePagination();
    };

    // 设置this.$tableBody滚动条的垂直偏移，意义是移动到第几行数据  
    BootstrapTable.prototype.scrollTo = function (value) {
        if (typeof value === 'string') {
            value = value === 'bottom' ? this.$tableBody[0].scrollHeight : 0;
        }
        if (typeof value === 'number') {
            this.$tableBody.scrollTop = value;
        }
        if (typeof value === 'undefined') {
            return this.$tableBody.scrollTop();// 返回顶部  
        }
    };

    // 表体滚动到顶部  
    BootstrapTable.prototype.getScrollPosition = function () {
        return this.scrollTo();
    };

    // 设置this.options.pageNumber当前页，调用updatePagination更新表体，initBody或initServer方法  
    BootstrapTable.prototype.selectPage = function (page) {
        if (page > 0 && page <= this.options.totalPages) {
            this.options.pageNumber = page;
            this.updatePagination();
        }
    };

    // 前一页  
    BootstrapTable.prototype.prevPage = function () {
        if (this.options.pageNumber > 1) {
            this.options.pageNumber--;
            this.updatePagination();
        }
    };

    // 后一页  
    BootstrapTable.prototype.nextPage = function () {
        if (this.options.pageNumber < this.options.totalPages) {
            this.options.pageNumber++;
            this.updatePagination();
        }
    };

    // 切换卡片式显示或者表格详情显示  
    BootstrapTable.prototype.toggleView = function () {
        this.options.cardView = !this.options.cardView;
        this.initHeader();
        // Fixed remove toolbar when click cardView button.  
        //that.initToolbar();  
        this.initBody();
        this.trigger('toggle', { detail: this.options.cardView });
    };

    // 更新传入的配置项options，调用destory重置，init重新渲染页面  
    BootstrapTable.prototype.refreshOptions = function (options) {
        //If the objects are equivalent then avoid the call of destroy / init methods  
        // 当this.options和options长度相当，其中一个属性不同的时候，也会被if语句提前返回？？？  
        if (Utils.compareObjects(this.options, options, true)) {
            return;
        }
        this.options = object.assign(this.options, options);
        this.trigger('refresh-options', { detail: this.options });
        this.destroy();
        this.init();
    };

    // 设置搜索框文本，启动数据搜索  
    BootstrapTable.prototype.resetSearch = function (text) {
        var $search = this.$toolbar.querySelector('.search input');
        $search.value = text || '';
        this.onSearch({ currentTarget: $search });
    };

    // 表格详情显示时，折叠展开按钮执行函数  
    BootstrapTable.prototype.expandRow_ = function (expand, index) {
        var $tr = this.$body.querySelector(Utils.sprintf(' tr[data-index="%s"]', index));
        if ($tr.nextElementSibling.matches('tr.detail-view') === (expand ? false : true)) {
            $tr.querySelector(' td > .detail-icon').click();
        }
    };

    // 展开对应行的卡片详情  
    BootstrapTable.prototype.expandRow = function (index) {
        this.expandRow_(true, index);
    };

    // 折叠对应行的卡片详情  
    BootstrapTable.prototype.collapseRow = function (index) {
        this.expandRow_(false, index);
    };

    // expandAllRows展开所有卡片式详情，在表格显示的时候  
    // isSubTable为真，展开父子表格的详情  
    BootstrapTable.prototype.expandAllRows = function (isSubTable) {
        if (isSubTable) {
            var $tr = this.$body.querySelectorAll(Utils.sprintf('tr[data-index="%s"]', 0)),
                that = this,
                detailIcon = null,
                executeInterval = false,
                idInterval = -1;

            if (!$tr.nextElementSibling.matches('tr.detail-view')) {
                $tr.querySelector(' td > .detail-icon').click();
                executeInterval = true;
            } else if (!$tr.nextElementSibling.nextElementSibling.matches('tr.detail-view')) {
                $tr.nextElementSibling.querySelector(".detail-icon").click();
                executeInterval = true;
            }

            if (executeInterval) {
                try {
                    idInterval = setInterval(function () {
                        // 父子表格情况，从.detail-view中找到.detail-icon并点击  
                        detailIcon = that.$body.querySelectorAll("tr.detail-view").slice(-1).querySelector(".detail-icon");
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
            var trs = this.$body.children();
            for (var i = 0; i < trs.length; i++) {
                this.expandRow_(true, trs[i].dataset("index"));
            }
        }
    };

    // expandAllRows展开所有卡片式详情，在表格显示的时候  
    BootstrapTable.prototype.collapseAllRows = function (isSubTable) {
        if (isSubTable) {
            this.expandRow_(false, 0);
        } else {
            var trs = this.$body.children();
            for (var i = 0; i < trs.length; i++) {
                this.expandRow_(false, $(trs[i]).data("index"));
            }
        }
    };

    // 更新配置项中的格式化函数  
    BootstrapTable.prototype.updateFormatText = function (name, text) {
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
    };

    // BOOTSTRAP TABLE PLUGIN DEFINITION  
    // =======================  

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
    // 定义一个函数，用于创建一个BootstrapTable实例
    var fn = Element.prototype.bootstrapTable = Element.prototype.bt = function (option) {

        var value,
            args = Array.prototype.slice.call(arguments, 1);// slice() 方法以新的数组对象，返回数组中被选中的元素

        // this.forEach(function () {
        var $this = this,
            data = $this.dataset['bootstrap.table'],
            // 配置项在触发元素的data数据中，或在js的option传参中  
            options = Object.assign({}, BootstrapTable.DEFAULTS, $this.dataset,
                typeof option === 'object' && option);
        //typeof option === 'object' && option,如果所有条件都是真实的，
        //它将始终将其设置为最后一个真实变量。如果要将该变量用作布尔值，则可以双倍否定(!!）该变量，以便它返回布尔
        if (typeof option === 'string') {
            if (allowedMethods.indexOf(option) < 0) {
                throw new Error("Unknown method: " + option);
            }

            if (!data) {
                return;
            }

            value = data[option].apply(data, args);//执行指定方法

            if (option === 'destroy') {
                delete $this.dataset['bootstrap.table'];
            }
        }

        if (!data) {
            // 创建一个新的BootstrapTable实例
            $this.dataset['bootstrap.table'] = data = new BootstrapTable(this, options);
        };
        // });

        return typeof value === 'undefined' ? this : value;
    };

    fn.Constructor = BootstrapTable;
    fn.defaults = BootstrapTable.DEFAULTS;
    fn.columnDefaults = BootstrapTable.COLUMN_DEFAULTS;
    fn.locales = BootstrapTable.LOCALES;
    fn.methods = allowedMethods;

}));