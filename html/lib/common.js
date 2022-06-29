/*检查是否登录失效*/
function checkLogin(data, is_show_err) {
    if (!data) {
        layer.msg('数据加载出错！请刷新页面！', {icon: 1, time: 3000});
        return false;
    }
    else if (data.state == -1 && is_show_err) {
        layer.msg(data.msg, {icon: 1, time: 3000});
        return false;
    }
    else if (data.state == -404) {
        $(location).prop('href', '/api/login');
        return false;
    }
    else {
        return true;
    }
}

/*获取url中的参数*/
function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return r[2];
    return '';
}