import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tutils.context_opt as tcontext

log = tl.log

UT = unittest.TestCase()


def exercise_dict_handler():
    dict_x = {"a": 1, "b": 3, "inner": {"n1": "1"}}
    dict_y = {"a": 11, "c": 3, "inner": {"n2": "1"}}
    print("flatten dict", flatten_dict_x := tcontext.flatten_dict(dict_x))
    UT.assertIn("inner.n1", flatten_dict_x)
    UT.assertEqual("1", flatten_dict_x["inner.n1"])

    for key_item, key_value in dict_x.items():
        print("dict itme with k,v", key_item, key_value)
    # 浅拷贝 shallow copy
    print(
        "merge dict", shallow_copy_dict := {**dict_x, **dict_y}, type(shallow_copy_dict)
    )
    UT.assertIsInstance(shallow_copy_dict, dict)
    UT.assertNotIn("n1", shallow_copy_dict["inner"])
    print(
        "deep merge dict",
        deep_copy_dict := tcontext.deep_merge(dict_x, dict_y),
        type(deep_copy_dict),
    )
    UT.assertIsInstance(deep_copy_dict, dict)
    UT.assertIn("inner", deep_copy_dict)
    UT.assertIn("n1", deep_copy_dict["inner"])
    UT.assertIn("n2", deep_copy_dict["inner"])
    # 解构 unpacking dict is not supported
    # a , b  = dict_x
    # print('unpacking dict', a, b)
