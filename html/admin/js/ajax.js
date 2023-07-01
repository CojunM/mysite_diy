

const $ = function () {

    function _ajax(opt) {

        // 从opt对象中获取AJAX配置信息
        let url = opt.url,
            dataType = opt.dataType || 'json' ,
            // 请求成功的回调函数
            success = opt.success || function () {
                };

        let method = (opt.method || 'GET').toUpperCase(),
            cache = opt.cache || false,
            data = opt.data || null,
            // 无论请求是否成功都会执行的完成回调函数类似于finally
            complete = opt.complete || function () {
            },
            beforeSend = opt.complete || function () {
            },
            // 请求失败的回调函数
            error = opt.error || function () {
            },
            // 请求是否异步
            // 如果直接使用opt.async || true，传入的值为false时也会因为或运算符而得到true值
            async = opt.async === false;
        // 兼容性创建xhr对象
        // 其中IE5/6是不支持XMLHttpRequest的
        // IE5/6/Opera Mini是只支持微软的ActiveXObject对象发送HTTP请求
        let xhr = window.XMLHttpRequest
            ? new XMLHttpRequest()
            : new ActiveXObject('Microsoft.XMLHTTP');

        if (!xhr) {
            // 如果无法创建xhr对象, 返回异常信息
            throw new Error('您的浏览器不支持异步发送HTTP请求');
        }
            // 兼容性timeout
            // 发送请求后设置超时定时器，若在设定的超时时间内未清除定时器，则判断请求超时
            // t = setTimeout(function() {
            //   timeout();
            //   xhr.abort('请求超时');
              // // 以下是一种写法,可以省略
              // clearTimeout(t);
              // xhr = null;
              // t = null;
              // throw new Error('请求超时');
            // }, timeout);

        // switch (cache) {
        //         case false:
        //            xhr.setRequestHeader('Cache-Control',"no-cache");
        //             break;
        //     case true:
        //             xhr.setRequestHeader('Cache-Control',  "public");
        //             break;
        //     }
        // 同时在xhr对象状态变化的事件处理函数中对超时进行处理
         // 设置xhr对象的状态改变事件监听处理函数
        xhr.onreadystatechange = function () {
          if (xhr.readyState === 4) {
            // 当readyState处于状态4时，表示请求已完成、响应已就绪即未超时
            // 我们取消定时任务
            // clearTimeout(t);
            // 200-300之间都为请求成功的状态码, 304为浏览器使用缓存的重定向状态码
            if ((xhr.status >= 200 && xhr.status <= 300) || xhr.status === 304) {
              // 请求成功执行成功回调函数
               switch (dataType) {
                            case 'json':
                                success(JSON.parse(xhr.responseText));
                                break;
                            case 'text':
                                success(xhr.responseText);
                                break;
                            case 'xml':
                               success(xhr.responseXML);
                                break;
                                             }

            } else {
              // 请求失败执行失败回调函数
              error(xhr.responseText);
            }
            // 请求完成执行完成回调函数
            complete(xhr.responseText);
            // t = null;
            xhr = null;
          }
        };

        // 建立客户端与服务器的连接、设置相应url、方法以及是否异步
        xhr.open(method, url, async);

        // 当请求为POST请求时要设置客户端的Content-type以使服务器识别到请求是post请求的键值对形式
        // 此处也可以作为配置对象中的一个属性 -> 成为一个配置项
        // a&& b :如果执行a后返回true，则执行b并返回b的值；如果执行a后返回false，则整个表达式返回a的值，b不执行；
        method === 'POST' && xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

        beforeSend&&beforeSend();
        // xhr对象发送请求，如果是GET请求不传入请求体、是POST请求则传入标准格式请求体
        // 如 name=zhangsan&&age=13
        xhr.send(method === 'GET' ? null : stringify(data));
    }

       // 将对象转化为标准请求体格式
    function stringify(data) {
            let str = '';
            for (let key in data) {
                if (Object.prototype.hasOwnProperty.call(data, key)) {
                    str += key + '=' + data[key] + '&';
                }
            }
            return str.replace(/&$/, '');
        }

    return {
            ajax: function (options) {
                _ajax(options);
            },
            get: function (url, success, error) {
                _ajax({
                    url: url,
                    method: 'GET',
                    success: success,
                    error: error,
                });
            },
            post: function (url, data, success, error) {
                _ajax({
                    url: url,
                    method: 'POST',
                    data: data,
                    success: success,
                    error: error,
                });
            }
        }
}();




//     function ajax1(obj) {
//         let type = obj.type || 'GET',//默认是GET
//             url = obj.url,
//             asny = obj.asny !== false,
//             data = '',
//             dType = obj.dataType || 'json',
//             success = obj.success,
//             error = obj.error;
//
//
//         let xhr = null;//创建XMLHttpRequest
//         // if (window.XMLHttpRequest) {
//         //     // IE7+, Firefox, Chrome, Opera, Safari 浏览器执行代码
//         //     xhr = new XMLHttpRequest();
//         // }
//         // else {
//         //     // IE6, IE5 浏览器执行代码
//         //     xhr=new ActiveXObject("Microsoft.XMLHTTP");
//         // }
//
//         try {
//             xhr = new XMLHttpRequest();
//             // IE7+, Firefox, Chrome, Opera, Safari 浏览器执行代码
//         } catch (e) {
//             xhr = new ActiveXObject('Microsoft.XMLHTTP');
//             // IE6, IE5 浏览器执行代码
//         }
// // var param = ''
//         //处理data
//         // if (data != {} && data != null) {
//         for (var key in obj.data) {
//             data += key + '=' + obj.data[key] + '&';
//             // data= data.substring(0,data.length-1)
//             //  param = param + key + '=' +  obj.data[key] + '&';
//
//             // console.log(data)
//         }
//         // }
//         // data=param.substring(0,param.length-1)
//         data = data.substring(0, data.length - 1);
//         // alert(data)
//         if (type.toUpperCase() == 'GET') {//处理GET
//             var d = new Date();
//             url += '?' + data + '_=' + d.getTime();//处理缓存问题
//             data = null;
//         }
//
//         //xhr监听
//         if (xhr != null) {
//             xhr.onreadystatechange = function () {
//                 if (xhr.readyState == 4) {
//                     if (xhr.status >= 200) {
//                         var response;
//                         if (dType == 'text' || dType == 'json') {
//                             if (dType == 'json') {//json
//                                 response = JSON.parse(xhr.responseText);
//                             } else {//普通文本
//                                 response = xhr.responseText;
//                             }
//                         } else {//XML
//                             response = xhr.responseXML;
//                         }
//                         success && success(response);//成功回调函数
//                     } else {
//                         //请求失败
//                         error && error(response);//失败回调函数console.log("请求失败")
//                     }
//
//                 }
//
//                 // alert(data)
//             };
//             xhr.open(type, url, asny);
//             xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');//设置请求头信息
//             xhr.send(data);//发送数据
//         } else {
//             alert("Your browser does not support XMLHTTP.");
//         }
//     }
//
//     function loginIn() {
//         // e.preventDefault();
//         let username = document.getElementById("username").value;
//         let password = document.getElementById("password").value;
//         // debugger
//         ajax1({
//             type: 'POST',
//             url: "/api/login1/",
//             data: {'_method': 'put', 'username': username, 'password': password,},
//             dataType: 'json',
//             // withCredentials: true,
//             success: function (data) {
//                 if (data && data.state > -1) {
//                     // $(location).attr('href', 'main');
//                     alert(data.msg);
//                     location.href = ('desk');
//                 } else {
//                     document.getElementById("msg").innerHTML = data.msg;
//
//                 }
//             },
//             error: function (data) {
//                 if (data) {
//                     alert(data.msg);
//                 }
//
//             }
//         }); }

