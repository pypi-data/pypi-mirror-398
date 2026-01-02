from distutils import core
import re, os, unittest, inspect
import tlog.tlogging as tl


from tio.tcli import *


import tapps.exercise.hello_world as exercise_hello_world
import tapps.exercise.log4j as exercise_log4j
import tapps.exercise.ast as exercise_ast
import tapps.exercise.new_features as exercise_new_features
import tapps.exercise.str as exercise_str
import tapps.exercise.eval as exercise_eval
import tapps.exercise.dict as exercise_dict
import tapps.exercise.list as exercise_list
import tapps.exercise.os as exercise_os
import tapps.exercise.type as exercise_type
import tapps.exercise.regexp as exercise_regexp
import tapps.exercise.lib_context as exercise_lib_context
import tapps.exercise.lib_diff as exercise_lib_diff
import tapps.exercise.lib_tfile as exercise_lib_tfile
import tapps.exercise.lib_thpe as exercise_lib_thpe
import tapps.exercise.lib_tssh as exercise_lib_tssh
import tapps.exercise.lib_ttemplate as exercise_lib_ttemplate
import tapps.exercise.lib_vilink as exercise_lib_vilink
import tapps.exercise.lib_gitlab_api as exercise_lib_gitlab_api
import tapps.exercise.lib_cli_opt as exercise_lib_cli_opt
import tapps.exercise.func_decorator as exercise_func_decorator


# from translate import Translator
# from googletrans import Translator


log = tl.log
# for each new plugin, please register cmd/sh in ${SCM_PYTHON_SH_HOME}/bin
# use for SUB_PLUGIN_NAME helper, for example xxxxx

# name= means that name follow string parameter
# mandatory is by func with default parameter
# Known issues: 2024-8-22,第一个长参数必须和函数定义的名字相同,否则输入短名会找不到值,对于其它长参数是带'-'可以被workaround支持
flags = [
    (
        "d",
        "debug",
        "enable/disable debug, boolean type sample",
        ["exercise", "exercise/hello-world"],
    ),
    (
        "n:",
        ["name="],
        "foo name, data passed sample",
        ["exercise", "exercise/hello-world"],
    ),
    ("p:", "params=", "additional parameters in scripts", "exercise/aggregation"),
    ("n:", "name=", "by name", "exercise/aggregation"),
    (
        "l",
        [
            "local-template",
            "local_template",
        ],
        "foo to use local template",
        ["exercise/cli-long-options"],
    ),
    (
        "b:",
        ["branch="],
        "foo branch name",
        ["exercise/cli-long-options"],
    ),
]

opp = OptParser(flags)


# please put entry function into top, and hello function in the top 1
"""
hell world for exercise
"""


@cli_invoker("exercise/|hello-world")
def exercise_hello_world_handler(debug=False, name="diameter"):
    """
    debug: bool
    name: str
    """
    exercise_hello_world.exercise_hello_world_handler(debug, name)


@cli_invoker("exercise/|log4j")
def exercise_log4j_handler():
    exercise_log4j.exercise_log4j_handler()


@cli_invoker("exercise/ast")  # ast sample
def exercise_ast_handler():
    exercise_ast.exercise_ast_handler()


@cli_invoker("exercise/cli-long-options")
def exercise_cli_long_options_handler(
    local_template=False, branch=""
):  # long option longest prefix match
    log.info(
        f"exercise_long_options_handler(local_template={local_template},branch={branch})"
    )


# please put entry function into top, and hello function in the top 1
@cli_invoker(
    "exercise/new-features"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_new_features_handler():
    exercise_new_features.exercise_new_features_handler()


# please put entry function into top, and hello function in the top 1
@cli_invoker(
    "exercise/eval"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_eval_handler():
    exercise_eval.exercise_eval_handler()


@cli_invoker(
    "exercise/str"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_str_handler():
    exercise_str.exercise_str_handler()


@cli_invoker(
    "exercise/list"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_list_handler():
    exercise_list.exercise_list_handler()


@cli_invoker(
    "exercise/dict"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_dict_handler():
    exercise_dict.exercise_dict_handler()


@cli_invoker(
    "exercise/os"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_os_handler():
    exercise_os.exercise_os_handler()


# @dataclass
# class Question:
#     key_word: str
#     statements: str
#     question_func: function


@cli_invoker(
    "exercise/type"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_type_handler():
    exercise_type.exercise_type_handler()


@cli_invoker(
    "exercise/regexp"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_regexp_handler():
    exercise_regexp.exercise_regexp_handler()


@cli_invoker(
    "exercise/lib-tssh"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_lib_tssh_handler():
    exercise_lib_tssh.exercise_lib_tssh_handler()


@cli_invoker(
    "exercise/lib-thpe"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_lib_thpe_handler():
    exercise_lib_thpe.exercise_lib_thpe_handler()


@cli_invoker(
    "exercise/lib-context"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_lib_context_handler():
    exercise_lib_context.exercise_lib_context_handler()


@cli_invoker("exercise/lib-ttemplate")  # junit test for lib ttemplate
def exercise_lib_ttemplate_handler():
    exercise_lib_ttemplate.exercise_lib_ttemplate_handler()


@cli_invoker(
    "exercise/lib-vilink"
)  # generate eclipse projecct for ops, please sure the current folder is web-console
def exercise_lib_vilink_handler():
    exercise_lib_vilink.exercise_lib_vilink_handler()


@cli_invoker("exercise/lib-diff")  # diff test suitcases
def exercise_lib_diff_handler():
    exercise_lib_diff.exercise_lib_diff_handler()


@cli_invoker("exercise/lib-tfile")  # tfile test suitcases
def exercise_lib_tfile_handler():
    exercise_lib_tfile.exercise_lib_tfile_handler()


@cli_invoker("exercise/lib-gitlab-api")  # gitlab-api test suitcases
def exercise_lib_gitlab_api_handler():
    exercise_lib_gitlab_api.exercise_lib_gitlab_api_handler()


@cli_invoker("exercise/lib-cli-opt")  # cli-opt test suitcases
def exercise_lib_cli_opt_handler():
    exercise_lib_cli_opt.exercise_lib_cli_opt_handler()


@cli_invoker(
    "exercise/cli-undefined-argument", arg_data_type="ptest=int"
)  # cli undefined argument test suitcases
def exercise_cli_undefined_argument_handler(ptest: int, vparam="123", bparam=False):
    unittest.TestCase().assertIsInstance(ptest, int)
    unittest.TestCase().assertIsInstance(vparam, str)
    unittest.TestCase().assertIsInstance(bparam, bool)
    exercise_lib_cli_opt.exercise_cli_undefined_argument_handler(ptest, vparam, bparam)


@cli_invoker(
    "exercise/aggregation",
    arggreation=lambda: [
        {
            "name": "a b c",
            "description": "abc",
            "params": {"ptest": "123", "vparm": "456"},
        }
    ],
)  # aggregation test suitcases, the name and params are required
def exercise_aggregation_handler(name: str, params: str = ""):
    log.info(f"name={name},params={params}")


@cli_invoker("exercise/func-decorator")  # cli-opt test suitcases
def exercise_func_decorator_handler():
    exercise_func_decorator.exercise_func_decorator_handler()


@cli_invoker("exercise/unit-test")  # cli-opt test suitcases
def exercise_unit_test_handler():
    for only_subcmd in fileter_subcmd("exercise/"):
        if "unit-test" != only_subcmd:
            func_name = f"exercise_{only_subcmd.replace('-', '_')}_handler"
            if not func_name:
                print("------ exercise_unit_test_handler:: undefined func", func_name)
            else:
                print("------ exercise_unit_test_handler:: func_name", func_name)
                func = globals().get(func_name)
                func({}, opp)  # type: ignore
            # eval()
    return
