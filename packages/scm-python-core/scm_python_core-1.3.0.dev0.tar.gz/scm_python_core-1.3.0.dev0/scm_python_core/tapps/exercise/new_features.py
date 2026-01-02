import unittest
from typing import Callable, Union, Literal
from enum import Enum
import tlog.tlogging as tl

EiumModuleTypeLiteral = Literal["plugins", "core"]

log = tl.log
UT = unittest.TestCase()


def exercise_new_features_handler():
    log.info("exercise_new_features_handler")
    # 海象牙运算符 The Walrus Operator
    print("set and print", cmd_line := "aaaaa")
    print("after set", cmd_line)
    # inline statement or function
    b = True and "1" or None
    print(b)
    # 三元表达式 ternary
    a = "abcde" == "abcd" and "aaa" or "bbbb"
    assert isinstance(a, str) and "bbbb" == a, f"ternary a is str expected, got: {a}"
    len(a) % 2 == 0 and print(a) or print("a is idle")
    assert (
        isinstance(a, str) and len(a) % 2 == 0
    ), f"print(a) that is expected, got: print('a is idle')"
    print("ternary expression", len(a) % 2 == 0 and (b := "1") or (b := "2"))
    assert b == "1", f"b is 1 expected, got: {b}"
    c = "2"
    d = "2"
    # 单行语句
    print("ternary expression1", len(a) % 2 != 0 and (c := "1"))
    assert c == "2", f"c is 2 expected, got: {c}"
    # 多行语句
    print("ternary expression2", len(a) % 2 != 0 and (c := "1") and (d := "1"))
    assert d == "2", f"d is 2 expected, got: {c} {d}"

    def literal_check(type: EiumModuleTypeLiteral):
        return type

    aa = {"aa": "bb"}["aa"]
    print("literal_check", literal_check(aa))  # type: ignore

    class EiumModuleType(Enum):
        Plugins = "plugins"
        Core = "core"

    print(
        "enum class",
        repr(EiumModuleType.Plugins),
        list(EiumModuleType),
        eium_module_type := EiumModuleType("plugins"),
    )
    assert (
        isinstance(eium_module_type, EiumModuleType)
        and EiumModuleType.Plugins == eium_module_type
    ), f"EiumModuleType is a enum class expected, got: {EiumModuleType}"

    def yeild_func():
        for item in [1, 2, 3]:
            yield item

        print(
            "enum class",
            repr(EiumModuleType.Plugins),
            list(EiumModuleType),
            eium_module_type := EiumModuleType("plugins"),
        )

    assert (
        isinstance(eium_module_type, EiumModuleType)
        and EiumModuleType.Plugins == eium_module_type
    ), f"EiumModuleType is a enum class expected, got: {EiumModuleType}"
