import sys, re, os, socket, unittest
import tlog.tlogging as tl
from xpinyin import Pinyin

log = tl.log
UT = unittest.TestCase()
piny = Pinyin()


def exercise_regexp_handler():
    log.info("exercise_regexp_handler")
    # split by regexp
    regexp_split_match = re.search(r"\s+", "a b c")
    UT.assertIsInstance(regexp_split_match, re.Match)
    UT.assertTrue(regexp_split_match)
    regexp_split_match = re.search(r"\s+", "abc")
    UT.assertIsInstance(regexp_split_match, type(None))
    UT.assertIsNone(regexp_split_match)
    regexp_split_list = re.split(r"\s+", "a b c")
    UT.assertIsInstance(regexp_split_list, list)
    UT.assertEqual("a", regexp_split_list[0])

    regexp_split_list = re.split(r"[0-9A-Za-z]+", "工位1小车X转向电机word自己")
    UT.assertIsInstance(regexp_split_list, list)
    UT.assertEqual(4, len(regexp_split_list))
    UT.assertEqual("工位", regexp_split_list[0])

    regexp_match_obj = re.match(r"^\s*$", "\r\n")
    UT.assertIsInstance(regexp_match_obj, object)
    UT.assertEqual("\r\n", regexp_match_obj.group())  # type: ignore
    UT.assertEqual("bbb", re.compile(r"#[^#\r\n]+\r\n").sub("", "bbb#aabcc\r\n"))
    UT.assertEqual(
        "registry=http://127.0.0.1:58081/repository/shao-npm-group/",
        re.compile(r"//.+:58081").sub(
            "//127.0.0.1:58081",
            "registry=http://58.37.32.250:58081/repository/shao-npm-group/",
        ),
    )
    UT.assertEqual(
        "registry=http://58.37.32.250:58081_abc/repository/shao-npm-group/",
        re.compile("//.+:58081").sub(
            lambda repl: f"{repl.group()}_abc",
            "registry=http://58.37.32.250:58081/repository/shao-npm-group/",
        ),
    )
    UT.assertEqual(
        "gong-wei1xiao-cheXzhuan-xiang-dian-jiWordzi-ji",
        re.compile("[\u4e00-\u9fa5]+").sub(
            lambda repl: f"{piny.get_pinyin(repl.group())}",
            "工位1小车X转向电机Word自己",
        ),
    )
