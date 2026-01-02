import yaml
import sys, re, os, socket
import tempfile, unittest
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.tssh as tssh
import tutils.context_opt as tcontext
from tutils.context_opt import SectionReplacementReactor

log = tl.log
UT = unittest.TestCase()


def exercise_lib_context_handler():
    log.info("exercise_lib_context_handler")
    context = {
        "VAR1": "11",
        "list::JAR": ["1", "2"],
        "VARC": "cba",
    }
    UT.assertEqual(
        "ab d1\n cd",
        str_replace_by_context := SectionReplacementReactor.replace(
            context, "ab ::{VAR1\nd1\n::}\n cd"
        ),
        str_replace_by_context,
    )
    UT.assertEqual(
        "ab d1\n cd",
        str_replace_by_context := SectionReplacementReactor.replace(
            context, 'ab ::{VAR1=="11"\nd1\n::}else{\nd2\n::}\n cd'
        ),
        str_replace_by_context,
    )
    UT.assertEqual(
        "ab d2\n cd",
        str_replace_by_context := SectionReplacementReactor.replace(
            context, 'ab ::{VAR1=="10"\nd1\n::}else{\nd2\n::}\n cd'
        ),
    )
    UT.assertEqual(
        "ab new jar 1new jar 2 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context, "ab ${list::JAR}<list::>new jar ${JAR}</list::> cd"
        ),
    )
    context["LIST_SPLIT_JAR"] = ","
    UT.assertEqual(
        'ab [{"name":"1"},{"name":"2"}] cd',
        str_replace_by_context := tcontext.replace_by_context(
            context, 'ab [${list::JAR}<list::>{"name":"${JAR}"}</list::>] cd'
        ),
    )
    del context["LIST_SPLIT_JAR"]
    UT.assertEqual(
        "ab new jar Cbanew jar Cba cd",
        str_replace_by_context := tcontext.replace_by_context(
            context, "ab ${list::JAR}<list::>new jar ${initCap::VARC}</list::> cd"
        ),
    )

    UT.assertEqual(
        "ab \n\tnew jar 1\tnew jar 2 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context, "ab \n\t${list::JAR}<list::>new jar ${JAR}</list::> cd"
        ),
    )
    UT.assertEqual(
        "\nab new jar 1new jar 2 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context, "\nab ${list::JAR}<list::>new jar ${JAR}</list::> cd"
        ),
    )
    context = {
        "VAR1": "11",
        "list::JAR": [{"VAR2": "3"}, {"VAR2": "4"}],
        "list::V1": [5, 6],
        "list::V2": [7, 8],
    }
    UT.assertEqual(
        "ab new3new4new5new6 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context,
            "ab ${list::JAR}<list::>new${VAR2}</list::>${list::V1}<list::>new${V1}</list::> cd",
        ),
    )
    UT.assertEqual(
        "ab new3new7new8new4new7new8new5new6 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context,
            "ab ${list::JAR}<list::>new${VAR2}${list::V2}<list::>new${V2}</list::></list::>${list::V1}<list::>new${V1}</list::> cd",
        ),
    )
    UT.assertEqual(
        "ab new jar 3new jar 4 cd",
        str_replace_by_context := tcontext.replace_by_context(
            context, "ab ${list::JAR}<list::>new jar ${VAR2}</list::> cd"
        ),
    )
    text_content = """
::{cond
a
::}else{
b
::}
c
"""
    expected_result = "\na\nc\n"
    UT.assertEqual(
        "\na\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": "1"}, text_content),
        f"{tf.hex(expected_result)}",
    )
    expected_result = "\nb\nc\n"
    UT.assertEqual(
        "\nb\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": None}, text_content),
    )
    expected_result = "\nb\nc\n"
    UT.assertEqual(
        "\nb\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": ""}, text_content),
    )
    text_content = """
::{cond
a
::}
c
"""
    expected_result = "\na\nc\n"
    UT.assertEqual(
        "\na\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": "1"}, text_content),
        f"{expected_result}{tf.hex(expected_result)} expected, got: {formatted_text}{tf.hex(formatted_text)}",
    )
    expected_result = "\nc\n"
    UT.assertEqual(
        "\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": None}, text_content),
        f"{expected_result}{tf.hex(expected_result)} expected, got: {formatted_text}{tf.hex(formatted_text)}",
    )
    expected_result = "\nc\n"
    UT.assertEqual(
        "\nc\n",
        formatted_text := tcontext.replace_by_context({"cond": ""}, text_content),
        f"{expected_result} expected, got: {formatted_text}",
    )
    log.info("exercise_lib_context_handler")
