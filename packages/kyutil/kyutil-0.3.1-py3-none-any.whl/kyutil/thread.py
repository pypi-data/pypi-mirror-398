# -*- coding: UTF-8 -*-
"""
@File ：thread.py
Python的线程池实现
"""
import threading


def thread_it(func, args=None, kwargs=None):
    """ thread_it(func, args=None, kwargs=None)"""
    # 创建
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    # 守护 !!! 主线程不会等待子线程结束，会直接结束整个程序
    t.setDaemon(True)
    # 启动
    t.start()
