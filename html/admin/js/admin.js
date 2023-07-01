/*阻止默认行为*/
function stopDefault(e) {
    if (e && e.preventDefault) {
        e.preventDefault(); //阻止默认浏览器动作(W3C)
    } else {
        window.event.returnValue = false; //IE中阻止函数器默认动作的方式
    }
    return false;
}


document.addEventListener("DOMContentLoaded", function () {

    let that;

    class Tab {
        constructor() {
            that = this;
            // 获取元素,获取的这些只能是之前的，动态添加的不能够获取到
            this.main = document.querySelector("main");
            // this.add = this.main.querySelector(".add");
            // this.ul = this.main.querySelector(".ul");
            this.iframe_box = this.main.querySelector("#iframe_box");
            // console.log(that.iframe_box);
            this.show_nav = this.main.querySelector('#min_title_list');
            // this.iframe=this.main.querySelector("iframe");
            // 实例化对象后直接实现init()方法即可
            this.init();


        };

        updateNode() {
            this.lis = this.main.querySelectorAll("li");
            this.show_iframe = this.main.querySelectorAll(".show_iframe");
            // console.log(this.show_iframe);
            // 获取删除按钮
            this.errors = this.main.querySelectorAll(" li i");//CSS3 :nth-child(n) 选择器匹配父元素中的第 n 个子元素，元素类型没有限制。
            // if (this.errors.length!==0) {
            // console.log(this.errors)
            // }
            // 动态获取所有li里面的第一个span标签
            // this.span1s = this.main.querySelectorAll("li span:nth-child(1)");
        }

        init() {
            // 初始化操作，让相关元素绑定事件   [指向constructor]
            // 获取一下li和section，一定要放到前面，先获取元素才能绑定事件
            // 直接把他放到这，重新获取一下li和section也为新的元素重新绑定一下
            this.updateNode();
            // 当点击添加按钮的时候，执行添加方法
            // that.add.onclick = this.addTab;
            for (let i = 0; i < that.lis.length; i++) {
                // 给所有的li的index属性赋值
                this.lis[i].index = i;
                // 点击之后执行toggleTab这个方法
               this.lis[i].onclick =that.toggleTab;
                // 输出的this指向的是 被点击的那个li的index属性
                // console.log(this.index);
                // 循环遍历，当点击删除按钮时,当前被点击按钮的操作
                // if (this.errors.length!==0) {this.errors[i].onclick = this.removeTab}
                // this.errors[i].onclick = this.removeTab;
                // // 当双击被选中的li里面第一个span的时候，执行edit方法
                // this.span1s[i].ondblclick = this.editTab;
                // // section也绑定双击事件
                // this.sections[i].ondblclick = this.editTab;
                //为啥在这地方输出的i是3
            }
            // 循环遍历，当点击删除按钮时,当前被点击按钮的操作
            if (this.errors.length !== 0) {
                for (let i = 0; i < this.errors.length; i++) {
                    this.errors[i].index = i;
                    this.errors[i].onclick = this.removeTab;
                    // console.log(i)
                }

            }
        };


        clearClass() {
            // for循环排他的思想
            // 让他的所有的类先清除掉
            for (let i = 0; i < this.lis.length; i++) {
                // 把li的所有li的类名全去掉，不用管指向谁直接
                that.lis[i].classList.remove('active');
                // console.log(this.lis[i].classList);
                 that.show_iframe[i].classList.remove('active');
            }
            // for (let i = 0; i < this.show_iframe.length; i++) {
            //         // 把li的所有li的类名全去掉，不用管指向谁直接
            //         that.show_iframe[i].classList.remove('active');
            //
            // }
        };

        // 1、切换功能
        toggleTab() {
            // 指向被点击的哪个li
            // 切换之前，先调用clearClass()，把所有的类先清除，再添加,
            // 用that，toggleTab()指向的是li
            that.clearClass();
            // 点击哪个li就给那个li添加bottom类，让他的下边框去掉
            // let index = this.parentNode.index;
            // this.show_iframe[this.index].classList.add ('active');
            // console.log(this.index);
            that.lis[this.index].classList.add("active");
            // console.log(that.lis[this.index].classList);
            that.show_iframe[this.index].classList.add("active");

        };

        // 2、添加功能
        addTab(href, title) {
            // 指向点击的添加按钮
            // 在添加元素前，清除一下所有的类名，让刚添加的元素处于选中状态
            that.clearClass();
            // 创建一个li元素
            // var li = '<li class="active"><span>' + title + '</span><span><i class="bi  bi-x"></i></span></li>';
            // 把li追加到ul里面
            // let nav_li=that.show_nav.querySelectorAll('li');
            // for (let i = 0; i <nav_li.length; i++) {
            //    nav_li[i].remove("active");
            // }
            that.show_nav.insertAdjacentHTML("beforeend", '<li class="tab_item  active"><span data-href="' + href + '">' + title + '</span><i></i><em></em></li>');
            // var section = '<section class="block">模块内容' + (that.lis.length + 1) + '</section>';
            /*创建iframe*/
            that.iframe_box.insertAdjacentHTML("beforeend", '<div class="show_iframe active"><div class="loading"></div><iframe frameborder="0" src=' + href + '></iframe></div>');
            // console.log(that.iframe_box);
            // that.iframe.src= href ;
            // that.iframe.contentWindow.location.reload(true);
            // 点击添加按钮后再重新获取一下li和section和绑定元素
            that.init();
        }

        //
        // 3删除功能功能
        removeTab(e) {
            // [指向被点击的删除按钮]
            // 阻止冒泡事件
            e.stopPropagation();
            // 获取被点击的li的索引号 拿到父亲的索引号
            // let index = this.index;
            let index = this.parentNode.index;
            // console.log(index);
            that.lis[index].remove();
            that.show_iframe[index].remove();
            // 点击添加按钮后再重新获取一下li和section和绑定元素
            that.init();
            // 当我们删除之后，还有li处于选中状态（也就是说删除的不是处于选中状态的）
            // 就直接return，不再进行前一个选中操作，保持原来的选中状态不变
            // 当我们删除选中状态的li后，让他的前一个处于选中状态
            index--;//先用再减
            // 手动调用一下点击事件
            // 如果点击的这个元素前面为空，index值不存在就不执行点击事件，否则会报错
            that.lis[index] && that.lis[index].click();
        };


    }

    const tab = new Tab();

    let sidebar = document.querySelector(".sidebar"),
        al = sidebar.querySelectorAll('a');

    for (let i = 0; i < al.length; i++) {

        let href = al[i].getAttribute('data-href'),
            title = al[i].getAttribute("data-title");

        if (href || href !== "") {

            al[i].addEventListener('click', function (ev) {
                //阻止默认行为
                stopDefault(ev);

                let bStop = false;
                tab.lis.forEach(function (e) {

                    if (e.querySelector('span').getAttribute("data-href") === href) {
                        bStop = true;
                        e.click();
                    }
                });
                if (!bStop) {
                    tab.addTab(href, title);

                }
            });

            // 点击标签，实现选中效果
            al[i].addEventListener('click', function () {
                al[i].classList.add("active");
                for (let j = 0; j < al.length; j++) {
                    if (j !== i) {
                        al[j].classList.remove("active");
                    }
                }

            })

        }
    }
});
