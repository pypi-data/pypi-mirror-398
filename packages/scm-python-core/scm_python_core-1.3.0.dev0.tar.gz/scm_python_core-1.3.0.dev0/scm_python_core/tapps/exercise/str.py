import time, unittest, re, sys
import tutils.tstr as tstr
import tlog.tlogging as tl

log = tl.log
UT = unittest.TestCase()


def exercise_str_handler():
    log.info(f"exercise_str_handler {sys.version_info}")
    UT.assertEqual(5, len("1 2 3 4 5".split()))
    if sys.version_info >= (3, 10):
        UT.assertTrue(sys.version_info >= (3, 9))
        UT.assertFalse(sys.version_info >= (3, 13))
    else:
        UT.assertTrue(sys.version_info >= (3, 9))
        UT.assertFalse(sys.version_info >= (3, 10))
        UT.assertFalse(sys.version_info >= (3, 11))

    regexp_pattern = r"(?:'[^']*'|\"[^\"]*\"|\S+)"
    result: list[str] = re.findall(regexp_pattern, "1 2 '3 3.1' 4 5")
    UT.assertEqual(5, len(result))
    UT.assertEqual("'3 3.1'", result[2])
    UT.assertListEqual(
        ["1", "aa==bb", "3", "4", "5"], tstr.split_by_space("1 aa==bb 3 4 5")
    )
    UT.assertListEqual(
        ["1", "'aa'=='bb'", "3", "4", "5"], tstr.split_by_space("1 'aa'=='bb' 3 4 5")
    )
    UT.assertListEqual(
        ["1", "\"'a' in ['a', 'b', 'c']\"", "3"],
        tstr.split_by_space("1 \"'a' in ['a', 'b', 'c']\" 3"),
    )
    UT.assertListEqual(["1", "'a b c'"], tstr.split_by_space("1 'a b c'"))
    UT.assertListEqual(["1", "'a b c'"], tstr.split_by_space("1 'a b c' "))
    UT.assertListEqual(["1", "'a b c'"], tstr.split_by_space(" 1 'a b c' "))
    UT.assertEqual("123456789", "1234567890"[:-1])
    UT.assertEqual("12345678", "1234567890"[:-2])
    UT.assertEqual("0", "1234567890"[-1])
    UT.assertEqual("9", "1234567890"[-2])
    UT.assertListEqual(
        ["Abc", "Def", "Ghi", "J"],
        split_statement := tstr.split_by_low_upper_break("AbcDefGhiJ"),
    )
    id = 1
    UT.assertEqual("0001", formatted_str := f"{id:04d}")
    # b前缀表示后面是单字节字符串
    str1 = b"--------"
    # 不显示b前缀
    UT.assertEqual("--------", str1.decode())
    now = int(round(time.time() * 1000))
    # f前缀表示format, {}内可以是表达式
    pipeline_file = f"__pipeline-{now}.bat"
    UT.assertNotIn("{now}", pipeline_file)
    # f"""是段落字符串
    str1 = f"""
  currently, time is
  {now}
  are you known
  """
    UT.assertNotIn("{now}", str1)
    # """内的f前缀不生效，显示原始内容
    str1 = """
  currently, time is
  f'{now}'
  are you known
  """
    UT.assertIn("{now}", str1)
    # 相当于三元表达式recursive=False, 选择b'scp -t ', list[0/1]
    recursive = False
    scp_command = (b"scp -t ", b"scp -r -t ")[recursive]
    UT.assertIsInstance(scp_command, bytes)
    UT.assertEqual(scp_command, b"scp -t ")
    # 新操作符
    int_num = 0
    int_num += 1
    UT.assertEqual(1, int_num)
    str1 = "/home/snap/git/ium-dev/siu"
    UT.assertEqual("/home/snap/git/ium-dev", str_lfind := str1[0 : str1.find("/siu")])
    UT.assertEqual("/home/snap/git/ium-dev", str_lfind := str1[: str1.find("/siu")])
    UT.assertEqual("/home/snap", str_lfind := str1[: str1.find("/git")])
    line = "k8s-app-shells::{"
    UT.assertEqual(f"k8s", line[: line.index("-app-shells::{")])
    str_variable = "aaa"
    # 规避{}字符
    UT.assertEqual("${aaa}", line := f"${{{str_variable}}}")
    UT.assertTrue(
        tstr.exist_in_object_with_similarity(
            "Jira jql中不能直接含--xxx类似字符,会报错,意味着summary中也不能包含--xxx,或者用--xxx包裹起来",
            [
                "Jira jql中不能直接含--xxx类似字符,会报错,意味着summary中也不能包含--xxx,或者用'--xxx'包裹起来"
            ],
            passed_similarity=0.9,
        )
    )

    UT.assertTrue(
        tstr.exist_in_object_with_contain(
            " 直接     报错 意味着 ",
            [
                "Jira jql中不能直接含--xxx类似字符,会报错,意味着summary中也不能包含--xxx,或者用'--xxx'包裹起来"
            ],
        )
    )

    UT.assertIsNone(
        tstr.exist_in_object_with_contain(
            " 直接报错意味着 ",
            [
                "Jira jql中不能直接含--xxx类似字符,会报错,意味着summary中也不能包含--xxx,或者用'--xxx'包裹起来"
            ],
        )
    )
