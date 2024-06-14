

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
            return elem;
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




    },
    addEvent(el, types, callback, context, selector, capture) {
        var handleObj;
        // Only attach events to objects that accept data
        if (!$Event.acceptData(el) || !types || !callback) return;

        // Caller can pass in an object of custom data in lieu of the handlerof the handler
        if (callback.handler) {
            handleObjIn = callback;
            handler = handleObjIn.callback;
            selector = handleObjIn.selector;
        }
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
        return el

    },
    // Detach an event or set of events from an element
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
                if (handleObj = handlers[type]) {
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
        return el;
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
        return owner.nodeType === 1 || owner.nodeType === 9 || !(+owner.nodeType);
    },
}




