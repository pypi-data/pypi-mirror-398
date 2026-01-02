import sys, re, os, unittest
import tlog.tlogging as tl
import tutils.cli_opt as cli_opt
import tio.tcli as tcli

log = tl.log

UT = unittest.TestCase()


def exercise_cli_undefined_argument_handler(ptest: int, vparam: str, bparam: bool):
    log.info(
        f"exercise_cli_undefined_argument_handler ptest={ptest},vparam={vparam},bparam={bparam}"
    )


def exercise_lib_cli_opt_handler():
    log.info(f"exercise_lib_cli_opt_handler")
    cli_opt.ENABLE_UNIT_TEST = True
    UT.assertEqual(
        "Sub-task",
        cli_opt.get_all_match_enum_input_value("Sub-Task", "Story", "Sub-task")[0],
    )
    UT.assertEqual(
        "exercise/lib",
        cli_opt.get_match_enum_input_value("exercise", "exercise/lib", "abc/lib"),
    )
    UT.assertEqual(
        "",
        cli_opt.get_match_enum_input_value(
            "exercise", "exercise/lib", "exercise/lib-ttemplate", "abc/lib"
        ),
    )
    UT.assertEqual(
        "exercise/lib",
        cli_opt.get_match_enum_input_value("exercise/lib", "exercise/lib", "abc/lib"),
    )
    UT.assertListEqual(
        [
            "exercise/lib-ttemplate",
            "exercise/lib-webapp",
            "exercise/lib-vilink",
        ],
        cli_opt.get_all_match_enum_input_value(
            "exercise",
            "exercise/lib-ttemplate",
            "exercise/lib-webapp",
            "exercise/lib-vilink",
        ),
    )
    UT.assertListEqual(
        [
            "exercise/lib-ttemplate",
            "exercise/lib-webapp",
            "exercise/lib-vilink",
        ],
        cli_opt.get_all_match_enum_input_value(
            "exercise/lib",
            "exercise/lib-ttemplate",
            "exercise/lib-webapp",
            "exercise/lib-vilink",
        ),
    )
    # UT.assertIsInstance(tcli.get_aggregation_defintion("install/batch"), list)
    UT.assertIsInstance(tcli.get_aggregation_defintion("exercise/aggregation"), list)
    UT.assertEqual(
        "a b c", tcli.get_aggregation_defintion("exercise/aggregation")[0]["name"]
    )

    arg_type_desc_of_subcmd = [
        ("h", "help", "print help information"),
        ("", "quiet", "no log"),
        ("f:", "file=", "the context file by yaml format"),
        ("p:", "params=", "additional parameters in scripts", "exercise/aggregation"),
        ("n:", "name=", "by name", "exercise/aggregation"),
    ]
    option_tupple = ("hf:p:n:", ["help", "quiet", "file=", "params=", "name="])

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "--name=aa", "--params", "c=d"
    )
    UT.assertEqual("exercise/aggregation", arg_parse.get_subcmd())
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "aa"), ("--params", "c=d")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "--name=aa", "--params=c=d"
    )
    UT.assertEqual("exercise/aggregation", arg_parse.get_subcmd())
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "aa"), ("--params", "c=d")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "a", "b", "c", "--ptest=abc"
    )
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "a", "b", "c", "--ptest", "abc"
    )
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "a", "b", "c", "--pt", "abc"
    )
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "a", "b", "--pt", "abc"
    )
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "b", "c", "--pt", "abc"
    )
    UT.assertRaises(
        Exception, lambda: arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    )

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "a", "b", "c", "--pt", "abc", "--vp=33"
    )
    opt, args = arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc,vparm=33")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "abdd", "b", "c", "--pt", "abc", "--vp=33"
    )
    UT.assertListEqual([("--name", "a b c"), ("--params", "ptest=abc,vparm=33")], opt)
    UT.assertListEqual([], args)

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "ab", "b", "c", "e", "--pt", "abc"
    )
    UT.assertRaises(
        Exception, lambda: arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    )

    arg_parse = cli_opt.SubcmdOptParser2(
        "pycli", "exercise", "aggregation", "g", "c", "e", "--pt", "abc"
    )
    UT.assertRaises(
        Exception, lambda: arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    )

    # arg_parse = cli_opt.SubcmdOptParser2(
    #     "pycli", "install", "batch", "g", "u", "d", "f", "e", "--pt", "abc"
    # )
    # UT.assertRaises(
    #     Exception, lambda: arg_parse.getopt(arg_type_desc_of_subcmd, *option_tupple)
    # )
