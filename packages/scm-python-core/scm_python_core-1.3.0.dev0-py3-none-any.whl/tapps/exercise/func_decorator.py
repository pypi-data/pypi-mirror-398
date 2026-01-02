import sys, re, os, unittest, inspect, functools
import tlog.tlogging as tl
import tutils.cli_opt as cli_opt
import tio.tcli as tcli

log = tl.log

UT = unittest.TestCase()


def print_runtime_args_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取函数的参数列表
        sig = inspect.signature(func)
        params = sig.parameters
        param_names = list(params.keys())

        # 打印参数列表
        print(f"Function '{func.__name__}' called with:")
        for name, value in zip(param_names, args):
            print(f"  {name} = {value}")
        for name, value in kwargs.items():
            print(f"  {name} = {value}")

        # 调用原函数
        return func(*args, **kwargs)

    return wrapper


# 使用装饰器
@print_runtime_args_decorator
def example_function(a, b, c=3):
    return a + b + c


def exercise_func_decorator_handler():
    log.info(f"exercise_func_decorator_handler")
    cli_opt.ENABLE_UNIT_TEST = True
    example_function(1, 2)
