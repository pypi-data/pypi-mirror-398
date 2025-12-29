# -*- coding: UTF-8 -*-
# 计算所用时间
import functools
import time

from logzero import logger as log


def timer(func):
    """
    :param func: 需要传入的函数
    :return:
    """

    def _warp(*args, **kwargs):
        """
        :param args: func需要的位置参数
        :param kwargs: func需要的关键字参数
        :return: 函数的执行结果
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        elastic_time = time.time() - start_time
        print("执行了 %.3fs\t方法：'%s' " % (elastic_time, func.__name__))
        return result

    return _warp


def handle_exception(expected_exception=Exception, default_return=None, logger=log):
    """
    更灵活的异常处理装饰器。

    参数:
        expected_exception: 要捕捉的异常类型（可以是元组）
        default_return: 发生异常时的默认返回值
        on_error: 异常发生时的回调函数，接收异常对象作为参数
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except expected_exception as e:
                logger.error(f"函数 {func.__name__} 发生异常: {e}")
                return default_return

        return wrapper

    return decorator


if __name__ == '__main__':
    # 定义一个错误处理回调
    def log_error(e):
        print(f"[ERROR] 发生错误: {e}")


    # 使用装饰器，只捕捉 ZeroDivisionError，并指定回调和默认返回值
    @handle_exception(
        expected_exception=ZeroDivisionError,
        default_return="计算错误",
        logger=log_error
    )
    def safe_divide(a, b):
        return a / b


    # 测试
    print(safe_divide(10, 2))  # 输出: 5.0
    print(safe_divide(10, 0))  # 输出: [ERROR] 发生错误: division by zero \n 计算错误
