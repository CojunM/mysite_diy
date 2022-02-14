#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Time    : 2022/6/21 18:39
# @Author  : Cojun  Mao
# @Site    : https://Cojun.net
# @File    : email_validcode.py
# @Project : mysite_diy
# @Software: PyCharm
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      ☃      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
import smtplib
import re
from os import environ
from os.path import exists
from platform import system,node
from time import strftime
from email.mime.text import MIMEText
from email.utils import formataddr
from random import randint
from easygui import msgbox,enterbox
print('库加载完成')

title = '这是标题（请自行更改）'
my_sender = 'advance_software@126.com' #发件者邮箱（请自行更改）
my_pass = 'QFAQPLFQZRZBMVWQ' #授权码（请自行更改）
dt = strftime('%Y-%m-%d %H:%M:%S')
print('已经获取时间')
my_user = userMail
username = environ['USERNAME']
system = system()
computer = node()
number = randint(100000,999999) #验证码
err = Exception
print('设备信息获取完成\n变量定义完成')

def mail():
    global err
    ret = True
    print('嵌套入检查语句')
    try:
        msg = MIMEText('这是邮件内容（请自行更改）', 'plain', 'utf-8')
        msg['From'] = formataddr(["发件人名称（请自行更改）", my_sender])
        msg['To'] = formataddr(["FK", my_user])
        msg['Subject'] = "xxx的验证码（请自行更改）"
        print('已经设置好邮件信息')

        server = smtplib.SMTP_SSL("smtp.126.com", 465)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, [my_user, ], msg.as_string())
        server.quit()
        print('邮件发送已完成')
    except Exception as e:
        ret = False
        err = str(e)
        print('进入错误语句\n错误是%s' % (err))
    return ret
    print('返回信息')

def checkmail(email):
    print('进入验证语句')
    reg = "\w+[@][a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+"
    result = re.findall(reg,email)
    if result:
        ret = mail()
        if ret:
            num = enterbox('发送成功！请输入您的验证码：',title)
            if num == str(number):
                with open('canRegister.txt','w+',encoding = 'UTF-8') as f:
                    f.write('canRegister')
                msgbox('验证成功！',title)
            else:
                msgbox('验证失败！',title)
        else:
            msgbox('邮件发送失败！\n原因是：%s' % (err),title)
    else:
        msgbox('您的输入不合法，请重新打开程序输入！',title)


if __name__ == '__main__':
    print('进入主程序')
    checkmail(my_user)
# -----------------------------------
# ©著作权归作者所有：来自51CTO博客作者PanDaoxi的原创作品，请联系作者获取转载授权，否则将追究法律责任
# Python实现发送邮件验证码
# https://blog.51cto.com/pandaoxi/4878504