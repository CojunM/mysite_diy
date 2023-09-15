(function (global, factory) {

    // 检查上下文环境是否为Nodejs环境'
typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
      // 检测上下文环境是否为AMD或CMD
typeof define === 'function' && define.amd ? define(factory) :

(global = typeof globalThis !== 'undefined' ? globalThis : global || self, global.myth = factory());
})(this, (function () { 'use strict';


; //JavaScript 弱语法的特点,如果前面刚好有个函数没有以";"结尾,那么可能会有语法错误
	var _myth = function(selector) {
		//如果默认参数不设置，自动赋值document
		if (!selector) {
			selector = document;
		}
		//获取selector数据类型，代码后面序号1有详细用法解释
		var selectorType = typeof(selector);
		//根据selector数据类型，进行同操作,代码后面序号2有详细用法解释
		switch (selectorType) {
			case 'string': //如果是字符串类型，使用querySelectorAll获取selector对象，结果记录到reObj内
				var doms = document.querySelectorAll(selector); //通过该方法查找HMTL中select对象，代码后面序号2有详细用法解释
				//reObj是个数据对象，目前设置了两个属性：dom是Javascript数据对象，length表示doms对象数量
				var reObj = {
					dom: doms,
					length: doms.length
				};
				break;
			case 'object': //如果是object类型，结果直接记录到reObj内
				var reObj = {
					dom: [selector],
					length: 1
				};
				break;
			default: //除了上述两种类型外，其它返回null对象
				return null;
		}
		reObj.__proto__ = mythExtends;
		//__proto__：表示一个对象拥有的内置属性，是JS内部使用寻找原型链的属性。可以理解为它是一个指针，用于指向创建它的函数对象的原型对象prototype（即构造函数的prototype），简单理解为“为reObj添加了一些扩展属性，myth(selector)选择对象后，可以进一步执行mythExtends中的方法。
		return reObj;
	};
	//myth(selector)对象的扩展方法
	var mythExtends = {
		/* dom 元素遍历 */
		each: function(callBack) {
			if (!callBack) {
				return;
			}
			for (var i = 0; i < this.length; i++) {
				this.dom[i].index = i;
				callBack(this.dom[i]); //返回每一个dom对象
			}
		},
		// 设置或读取html
		html: function(html) {
			if (this.length < 1) {
				return this;
			}
			//设置HTML
			if (typeof(html) != 'undefined') {
				for (var i = 0; i < this.length; i++) {
					this.dom[i].innerHTML = html;
				}
				return this;
			}
			//读取HTML
			try {
				return this.dom[0].innerHTML;
			} catch (e) {
				return null;
			}
		},
		/*读取或设置属性开始*/
		attr: function(attrName, val) {
			if (val) {
				this.setAttr(attrName, val);
			} else {
				return this.getAttr(attrName);
			}
		},
		getAttr: function(attrName) {
			try {
				return this.dom[0].getAttribute(attrName);
			} catch (e) {
				console.log(_lang.domEmpty);
				return null;
			}
		},
		setAttr: function(attrName, val) {
			for (var i = 0; i < this.length; i++) {
				this.dom[i].setAttribute(attrName, val);
			}
			return this;
		},
		/*读取或设置属性结束*/
		/* 样式操作开始 */
		css: function(csses) {
			for (var i = 0; i < this.length; i++) {
				var styles = this.dom[i].style;
				for (var k in csses) {
					styles[k] = csses[k];
				}
			}
			return this;
		},
		hasClass: function(cls) {
			if (this.length != 1) {
				return false;
			}
			return this.dom[0].className.match(new RegExp('(\\s|^)' + cls + '(\\s|$)'));
		},
		addClass: function(cls) {
			for (var i = 0; i < this.length; i++) {
				if (!this.dom[i].className.match(new RegExp('(\\s|^)' + cls + '(\\s|$)'))) {
					this.dom[i].className += " " + cls;
				}
			}
			return this;
		},
		removeClass: function(cls) {
			var reg = new RegExp('(\\s|^)' + cls + '(\\s|$)');
			for (var i = 0; i < this.length; i++) {
				this.dom[i].className = this.dom[i].className.replace(reg, ' ');
			}
			return this;
		},
		/* 样式操作结束 */
		// 隐藏元素。isAnimate为真，动画方式隐藏元素
		hide: function(isAnimate) {
			for (var i = 0; i < this.length; i++) {
				if (isAnimate) {
					var ctdom = myth(this.dom[i]);
					ctdom.addClass('myth-fade-out');
					setTimeout(function() {
						ctdom.dom[0].style.display = 'none';
						ctdom.removeClass('myth-fade-out');
					}, 300);
				} else {
					this.dom[i].style.display = 'none';
				}
			}
			return this;
		},
		// 显示元素 isAnimate为真，动画方式显示元素
		show: function(isAnimate) {
			for (var i = 0; i < this.length; i++) {
				if (isAnimate) {
					var ctdom = _myth(this.dom[i]);
					ctdom.addClass('myth-fade-in');
					setTimeout(function() {
						ctdom.dom[0].style.display = 'block';
						ctdom.removeClass('myth-fade-in');
					}, 300);
				} else {
					this.dom[i].style.display = 'block';
				}
			}
			return this;
		},
		// 单击事件
		click: function(callBack) {
			for (var i = 0; i < this.length; i++) {
				if (callBack == undefined) {
					_myth(this.dom[i]).trigger('click');
				}
				this.dom[i].addEventListener('click', callBack);
			}
		},
		setWidth: function(swidth) { //设置myth(selector)对象宽度
			this.dom[0].style.width = swidth;
		},
		getWidth: function() { //获取myth(selector)对象宽度
			return this.dom[0].offsetWidth;
		},
		setHeight: function(sheight) { //设置myth(selector)对象高度
			this.dom[0].style.height = sheight;
		},
		getHeight: function() { //获取myth(selector)对象高度
			return this.dom[0].offsetHeight;
		}
	}
	_myth.version = 'myth 1.0'; //设置版本
	return _myth;


}))
