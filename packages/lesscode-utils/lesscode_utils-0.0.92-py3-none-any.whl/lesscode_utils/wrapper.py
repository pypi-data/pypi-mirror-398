import functools
import logging
import time
import traceback
from typing import Any, Callable


def retry(num=3, check_func=None):
    """
    重试装饰器
    :param num: 重试次数
    :param check_func: 校验结果函数
    example:
        def check_func(res):
            assert res == 1111


        class A:
            @retry(check_func=check_func)
            def test(self):
                return 1111

            @staticmethod
            @retry(check_func=check_func)
            def test2():
                return 1111

            @classmethod
            @retry(check_func=check_func)
            def test3(cls):
                return 1111


        @retry(check_func=check_func)
        def test4():
            return 1111
    """

    def _retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for i in range(num):
                try:
                    result = func(*args, **kwargs)
                    if check_func is not None:
                        if check_func(result):
                            break
                except Exception as e:
                    traceback.print_exc()
                    if i == num - 1:
                        raise e
            return result

        return wrapper

    return _retry


def timing_wrapper(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            # 获取函数名和类名信息
            func_name = func.__name__
            class_name = ""

            if hasattr(func, '__self__') and getattr(func, '__self__') is not None:
                instance_or_class = args[0] if args else func.__self__
                class_name = instance_or_class.__class__.__name__
            elif args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__

            if class_name:
                logging.info(f"{class_name}.{func_name} 执行时间: {elapsed_time:.6f} 秒")
            else:
                logging.info(f"{func_name} 执行时间: {elapsed_time:.6f} 秒")

    return wrapper
