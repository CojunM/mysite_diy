#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/26 0026 20:10
# @Author  : CJ  Mao
# @Site    : 
# @File    : baseserver.py
# @Project : mysite_diy
# @Software: PyCharm

import socket
from wsgiref.simple_server import WSGIServer, make_server, WSGIRequestHandler


class WSGIRefServer(WSGIServer):
    quiet = False

    def __init__(self, host, port, **options):
        self.host = host
        self.port = int(port)
        self.options = options

    def run(self, app):
        if ':' in self.host:
            self.address_family = socket.AF_INET6
        srv = make_server(self.host, self.port, app)
        srv.serve_forever()

#
# class FileCheckerThread(Thread):
#     """ 一旦检测到更改的模块文件，立即中断主线程，锁文件被删除或变旧. """
#
#     def __init__(self, interval):  # 继承自Thread类，重写了它的构造函数
#         Thread.__init__(self)
#         self.interval = interval
#         #: Is one of 'reload', 'error' or 'exit'
#         self.status = None
#
#     def run(self):  # 继承自Thread类，重写了它的run()方法
#         exists = os.path.exists  # 判断括号里的文件是否存在的意思，括号内的可以是文件路径。
#         mtime = lambda path: os.stat(path).st_mtime  # st_mtime最后一次修改时间
#         files = dict()
#
#         for module in list(sys.modules.values()):  # 当某个模块第一次导入，字典sys.modules将自动记录该模块
#             path = getattr(module, '__file__', '') or ''  # __file__属性：查看模块的源文件路径
#             if path[-4:] in ('.pyo', '.pyc'): path = path[:-1]  # .pyc 作扩展名的文件是 python 编译文件,pyo 文件是优化编译后的程序
#             if path and exists(path): files[path] = mtime(path)  # 拿到所有导入模块文件的modify time
#
#         while not self.status:
#             for path, lmtime in list(files.items()):  # items() 函数以列表返回可遍历的(键, 值) 元组数组 list() 方法用于将元组转换为列表。
#                 if not exists(path) or mtime(path) > lmtime:  # 如果文件发生改动
#                     self.status = 'reload'
#                     interrupt_main()  # raise 一个 KeyboardInterrupt exception in 主线程
#                     break  # 跳出循环
#             time.sleep(self.interval)
#
#     # 当with语句在开始运行时，会在上下文管理器对象上调用 __enter__ 方法。
#     # with语句运行结束后，会在上下文管理器对象上调用 __exit__ 方法
#     def __enter__(self):
#         self.start()  # 开始线程活动，调用它的run()方法
#
#     # 这个地方是重新载入更新后模块的关键
#     # 当检测到文件变化时，终止主线程使监听请求停止，退出上下文管理器时，如果返回True则重现异常捕获
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if not self.status: self.status = 'exit'  # silent exit
#         self.join()
#         return exc_type is not None and issubclass(exc_type, KeyboardInterrupt)
#
#
# def server_run(app, host, port, interval, reloader, quiet, **kargs):
#     """Run server"""
#     # 第一次进来的时候，必然会进这个分支，因为没有地方设置过RUN_MAIN
#     if reloader and not os.environ.get("RUN_MAIN"):
#         try:
#             while True:
#                 # 其实这里会创建一个新的子进程来运行服务
#                 args = [sys.executable] + sys.argv  # sys.executable 是获取当前python解释器的路径
#                 new_environ = os.environ.copy()
#                 new_environ['RUN_MAIN'] = 'true'
#                 p = subprocess.Popen(args, env=new_environ)
#                 while p.poll() is None:  # Busy wait...如果返回None表示子进程未结束
#                     time.sleep(interval)
#                 if p.poll() != 3:
#                     sys.exit(p.poll())
#         except KeyboardInterrupt:
#             sys.exit(3)
#
#     else:
#         try:
#             server = WSGIRefServer(host=host, port=port, **kargs)
#             server.quiet = server.quiet or quiet
#             if not server.quiet:
#                 try:
#                     _stdout, _stderr = sys.stdout.write, sys.stderr.write
#                 except IOError:
#                     _stdout = lambda x: sys.stdout.write(x)
#                     _stderr = lambda x: sys.stderr.write(x)
#                 _stderr(" server starting up (using %s)...\n" % (repr(server)))
#                 _stderr("Listening on http://%s:%d/\n" % (server.host, server.port))
#                 _stderr("Hit Ctrl-C to quit.\n\n")
#             # 当选择自动重载时，如果解释器进程已经启动
#             # 则只需要检测应用相关内容有没有变化,如果有变化终止主线程并重新实现异常捕获
#             if reloader:
#                 bgcheck = FileCheckerThread(interval)
#                 with bgcheck:  # 开启新线程检测文件修改，如果修改终止当前主线程，抛出异常
#                     # 主线程监听请求
#                     server.run(app)
#                 if bgcheck.status == 'reload':
#                     sys.exit(3)
#             else:
#                 server.run(app)
#         except KeyboardInterrupt:
#             print('quit as KeyboardInterrupt')
#             sys.exit(3)
#         except (SystemExit, MemoryError):
#             print('quit as SystemExit')
#             raise
#         except:
#             if not reloader: raise
#             # if not getattr(server, 'quiet', quiet):
#             print_exc()
#             time.sleep(interval)
#             sys.exit(3)
#
