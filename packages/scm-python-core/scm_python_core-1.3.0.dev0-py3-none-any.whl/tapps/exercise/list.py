import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tutils.tworkaround as tworkaround

from tkinter import _flatten  # type: ignore

log = tl.log

UT = unittest.TestCase()


def exercise_list_handler():
    log.info("exercise_list_handler")
    # 解构
    list1 = [1, 2, 3]
    head, *tail = list1
    UT.assertEqual(1, head)
    UT.assertListEqual([2, 3], tail)
    list2 = list(map(lambda v: v + 10, list1))
    UT.assertListEqual([11, 12, 13], list2)
    UT.assertListEqual([3, 2, 1], list1[::-1])
    UT.assertListEqual([2, 3], list2 := [value for value in list1 if value > 1], list2)
    UT.assertTrue(not [], "empty list is not empty")
    # 扁平化多层数组
    multi_list = [[1, 2], 3]
    UT.assertListEqual([1, 2, 3], flat_list := list(_flatten(multi_list)), flat_list)
    # instanceof
    UT.assertListEqual([1, 2, 3, 4], [1, 2] + [3, 4])
    UT.assertRaises(TypeError, lambda: [1, 2] + None)
    UT.assertListEqual([1, 2, 3, 4], tworkaround.list_add([1, 2], [3, 4], None))
    UT.assertListEqual(
        [1, 2, 3, 4], tworkaround.list_add_with_trim([1, 2], [3, 4, ""], None)
    )
    list_remove = [1, 2]
    list_remove.remove(1)
    UT.assertListEqual([2], list_remove)
    # 循环
    for key_item, key_value in enumerate(["a", "b"]):
        UT.assertTrue(isinstance(key_item, int))
        UT.assertTrue(isinstance(key_value, str))
    # filter
    UT.assertListEqual(
        [2, 3],
        filtered_list := [item0 for item0 in [1, 2, 3] if item0 > 1],
        filtered_list,
    )
    # 解构 unpacking, only supported for tuple and list, too many values to unpack (expected 2), it is required that unpacked param count == list.size
    dirname, filename = "a,b".split(",")
    UT.assertEqual("a", dirname)
    UT.assertEqual("b", filename)
    colours = ["pink", "red", "green"]
    cloths = ["shirt", "hat", "socks", "shorts"]
    zip_list = list(zip(colours, cloths))
    colour, cloth = zip_list[0]
    UT.assertTupleEqual(("pink", "shirt"), (colour, cloth))
    UT.assertEqual(3, len(zip_list))
