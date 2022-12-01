#!/usr/bin/python
#coding: utf-8

from io import BytesIO

# from common.except_helper import exception_handling
# from common import verify_helper, log_helper, web_helper
from brick.core.wsgiapp import get
from brick.contrib import verify_helper, web_helper, log_helper
from brick.contrib.except_helper import exception_handling
from brick.core.httphelper.response import response


@get('/api/verify/')
@exception_handling
def get_verify():
    """生成验证码图片"""
    try:
        # 获取生成验证码图片与验证码
        code_img, verify_code = verify_helper.create_validate_code()

        # 将字符串转化成大写保存到session中
        s = web_helper.get_session()
        s['verify_code'] = verify_code.upper()
        s.save()

        # 输出图片流
        buffer = BytesIO()
        code_img.save(buffer, "jpeg")
        code_img.close()
        response.set_header('Content-Type', 'image/jpg')
        return buffer.getvalue()
    except Exception as e:
        log_helper.error(str(e.args))
#
# @get('/api/verify/')
# @exception_handling
# def get_verify():
#     code_img,shape_img, verify_code = verify_helper.GetPicVerify()