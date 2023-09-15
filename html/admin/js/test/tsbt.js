
(function (global, factory) {
    // alert(global)
    // 检查上下文环境是否为Nodejs环境'
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory(require('global')) :
        // 检测上下文环境是否为AMD或CMD
        typeof define === 'function' && define.amd ? define(['global'], factory) :

            (global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.jTool=factory(global));
})(this, (function ($w) {
    'use strict';

   
   function isWindow(object) {
	return object !== null && object === object.window;
}

    function each(object, callback) {

        // 当前为jTool对象,循环目标更换为jTool.DOMList
        if(object && object.jTool){
            object = object.DOMList;
        }
    
        var objType = type(object);
    
        // 为类数组时, 返回: index, value
        if (objType === 'array' || objType === 'nodeList' || objType === 'arguments') {
            // 由于存在类数组 NodeList, 所以不能直接调用 every 方法
            [].every.call(object, function(v, i){
                var tmp = isWindow(v) ? noop() : (v.jTool ? v = v.get(0) : noop()); // 处理jTool 对象
                return callback.call(v, i, v) === false ? false : true;
            });
        } else if (objType === 'object') {
            for(var i in object){
                if(callback.call(object[i], i, object[i]) === false) {
                    break;
                }
            }
        }
    }
    
// 通过html字符串, 生成DOM.  返回生成后的子节点
// 该方法无处处理包含table标签的字符串,但是可以处理table下属的标签
function createDOM(htmlString) {	var jToolDOM = document.querySelector('#jTool-create-dom');
if (!jToolDOM || jToolDOM.length === 0) {
    // table标签 可以在新建element时可以更好的容错.
    // div标签, 添加thead,tbody等表格标签时,只会对中间的文本进行创建
    // table标签,在添加任务标签时,都会成功生成.且会对table类标签进行自动补全
    var el = document.createElement('table');
    el.id = 'jTool-create-dom';
    el.style.display = 'none';
    document.body.appendChild(el);
    jToolDOM = document.querySelector('#jTool-create-dom');
}

jToolDOM.innerHTML = htmlString || '';
var childNodes = jToolDOM.childNodes;

// 进行table类标签清理, 原因是在增加如th,td等table类标签时,浏览器会自动补全节点.
if (childNodes.length == 1 && !/<tbody|<TBODY/.test(htmlString) && childNodes[0].nodeName === 'TBODY') {
    childNodes = childNodes[0].childNodes;
}
if (childNodes.length == 1 && !/<thead|<THEAD/.test(htmlString) && childNodes[0].nodeName === 'THEAD') {
    childNodes = childNodes[0].childNodes;
}
if (childNodes.length == 1 && !/<tr|<TR/.test(htmlString) &&  childNodes[0].nodeName === 'TR') {
    childNodes = childNodes[0].childNodes;
}
if (childNodes.length == 1 && !/<td|<TD/.test(htmlString) && childNodes[0].nodeName === 'TD') {
    childNodes = childNodes[0].childNodes;
}
if (childNodes.length == 1 && !/<th|<TH/.test(htmlString) && childNodes[0].nodeName === 'TH') {
    childNodes = childNodes[0].childNodes;
}
document.body.removeChild(jToolDOM);
return childNodes;
}

var jTool = function (selector, context){
	return new jTool.fn.init(selector, context);
};

jTool.fn = jTool.prototype = {
    constructor : jTool ,//加上一句constructor指向自己，就能修正constructor的指向问题

    init : function(selector, context) {

       var DOMList;
   
       // selector -> undefined || null
       if (!selector) {
           selector = null;
       }
   
       // selector -> window
       else if (isWindow(selector)) {
           DOMList = [selector];
           context = undefined;
       }
   
       // selector -> document
       else if (selector === document) {
           DOMList = [document];
           context = undefined;
       }
   
       // selector -> DOM
       else if (selector instanceof HTMLElement) {
           DOMList = [selector];
           context = undefined;
       }
   
       // selector -> NodeList || selector -> Array
       else if (selector instanceof NodeList || selector instanceof Array) {
           DOMList = selector;
           context = undefined;
       }
   
       // selector -> jTool Object
       else if (selector.jTool) {
           DOMList = selector.DOMList;
           context = undefined;
       }
   
       // selector -> Html String
       else if (/<.+>/.test(selector)) {
           // TODO
           DOMList = createDOM(selector);
           context = undefined;
       }
   
       // selector -> 字符CSS选择器
       else {
           // context -> undefined
           if (!context) {
            
               DOMList = document.querySelectorAll(selector);
           }
   
           // context -> 字符CSS选择器
           else if (typeof context === 'string') {
               context = document.querySelectorAll(context);
           }
   
           // context -> DOM 将HTMLElement转换为数组
           else if (context instanceof HTMLElement) {
               context = [context];
           }
   
           // context -> NodeList
           else if (context instanceof NodeList) {
               context = context;
           }
   
           // context -> jTool Object
           else if (context.jTool) {
               context = context.DOMList;
           }
   
           // 其它不可以用类型
           else {
               context = undefined;
           }
   
           // 通过父容器获取 NodeList: 存在父容器
           if (context) {
               DOMList = [];
               each(context, function (i, v) {
                   // NodeList 只是类数组, 直接使用 concat 并不会将两个数组中的参数边接, 而是会直接将 NodeList 做为一个参数合并成为二维数组
                   each(v.querySelectorAll(selector), function (i2, v2) {
                       if(v2){
                           DOMList.push(v2);
                       }
                   });
               });
           }
       }
   
       if (!DOMList || DOMList.length === 0) {
           DOMList = undefined;
       }
   
       // 用于确认是否为jTool对象
       this.jTool = true;
   
       // 用于存储当前选中的节点
       this.DOMList = DOMList;
       this.length = this.DOMList ? this.DOMList.length : 0;
   
       // 存储选择器条件
       this.querySelector = selector;
       return this;
   },
   html: function(html) {

    if (this.length < 1) {
   
        return this;
    }
    //设置HTML
    if (typeof(html) != 'undefined') {
        for (var i = 0; i < this.length; i++) {
            this.DOMList[i].innerHTML = html;
        }
        return this;
    }
},}
jTool.fn.init.prototype =jTool.prototype 

   if(typeof($w.$) !== 'undefined') {
	$w._$ = $;
}
// 抛出全局变量jTool  $
 $w.$ = jTool;
}))