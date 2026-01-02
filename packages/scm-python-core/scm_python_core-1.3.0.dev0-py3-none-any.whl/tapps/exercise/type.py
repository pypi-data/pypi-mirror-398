import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.tssh as tssh
import tutils.context_opt as tcontext
from typing import Callable, Union

log = tl.log
UT = unittest.TestCase()


def exercise_type_handler():
    log.info("exercise_type_handler")
    obj_1: object = {"a": 1, "b": {}}
    inner_obj2: object = obj_1["b"]

    result_list: list[str] = []
    result_list.append("aaa")
    result_list.append("bbb")

    # Alternative syntax for unions requires Python 3.10 or newer
    # def multi_return_type1(a:int, b:str)-> (int | None):
    #     if a == 1 : return b
    #     if a == 2 : return 2
    #     return None
    def multi_return_type(a: int, b: str) -> Union[int, str, None]:
        if a == 1:
            return b
        if a == 2:
            return 2
        return None

    print("multi_return_type", func_value := multi_return_type(2, "b"))
    UT.assertEqual(2, func_value)
    UT.assertIsInstance(func_value, int)

    def multi_return_type2(a: int, b: str) -> Union[tuple[int, str], tuple[int, None]]:
        if a == 1:
            return 1, b
        if a == 2:
            return 2, b
        return 1, None

    int_value, str_value = multi_return_type2(3, "b")
    UT.assertEqual(1, int_value)
    UT.assertIsNone(str_value)

    func1: Callable[..., int] = lambda a1, a2: max(a1, a2)
    print("fuction name", func_name := type(func1).__name__)
    UT.assertEqual("function", func_name)

    # NameError: name 'function' is not defined if the func0: function exists
    def function_as_parameter(a1: int, a2: int, a3: int, func0: Callable[..., int]):
        return max(a1, func0(a2, a3))

    print("function_as_parameter", func_value := function_as_parameter(1, 2, 3, func1))
    UT.assertEqual(3, func_value)
    UT.assertIsInstance(func_value, int)
