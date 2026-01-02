import yaml
import sys, re, os, socket, unittest
import binascii
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.ttemplate as ttemplate
import tutils.context_opt as tcontext

log = tl.log
UT = unittest.TestCase()


def exercise_lib_ttemplate_handler():
    log.info("exercise_lib_ttemplate_handler")
    lines: list[str] = [
        "a",
        "\t::__COND1",
        "b",
        "\t::__COND1",
        "c",
        "\t::__COND2",
        "d",
        "\t::__COND2",
        "e",
    ]
    UT.assertEqual(
        "a\nc\ne",
        str_remove_content_by_keyword := tcontext.remove_content_in_keyword_pair(
            "\n".join(lines), "::__COND"
        ),
        f"{binascii.b2a_hex(str_remove_content_by_keyword.encode('utf-8'))}",  # type: ignore
    )
    text_content = """
::{available_condition
a
::}
c
"""
    UT.assertListEqual(
        ["\na\nc\n"],
        tcontext.write_to_file_with_replace(
            target_file="c:/temp",
            lines=text_content,
            context={"available_condition": "1"},
            allow_escape_char=True,
            skip_write_file=True,
        ),
    )
    UT.assertListEqual(
        ["\nc\n"],
        tcontext.write_to_file_with_replace(
            target_file="c:/temp",
            lines=text_content,
            context={"available_condition": ""},
            allow_escape_char=True,
            skip_write_file=True,
        ),
    )
    # block section放在数组内无效
    UT.assertListEqual(
        ["\n", "::{available_condition\n", "a\n", "::}\n", "c\n"],
        tcontext.write_to_file_with_replace(
            target_file="c:/temp",
            lines=["", "::{available_condition", "a", "::}", "c"],
            context={"available_condition": ""},
            allow_escape_char=True,
            skip_write_file=True,
        ),
    )
    text_content = """
::{available_condition
a
::}else{
b
::}
c
"""
    UT.assertListEqual(
        ["\nb\nc\n"],
        tcontext.write_to_file_with_replace(
            target_file="c:/temp",
            lines=text_content,
            context={"available_condition": ""},
            allow_escape_char=True,
            skip_write_file=True,
        ),
    )
