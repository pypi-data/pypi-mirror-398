"""
command line entry

"""

import io, ast, sys, os, traceback, importlib, json
import tlog.tlogging as tl
import tio.tcli as tcli
import tutils.thpe as thpe
import tutils.tssh as tssh
import tutils.cli_opt as cli_opt
from typing import Union
from tutils.dynmic_module import DecoratedFunction
import tutils.dynmic_module as dm
import tutils.tplugin_installer as tpi
from tkinter import _flatten  # type: ignore
from os.path import expanduser
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from importlib import metadata
import signal


class FunctionInvokeArgDefinition:
    """
    函数调用的每个参数的定义
    """

    def __init__(
        self,
        short_option_name: str,
        long_option_name: str,
        arg_description: str,
        *subcmd_list: list[str],
    ):
        self.short_option_name = short_option_name
        self.long_option_name = long_option_name
        self.arg_description = arg_description
        self.subcmd_list = (
            (subcmd_list[0] if isinstance(subcmd_list[0], list) else [*subcmd_list])
            if len(subcmd_list) > 0
            else []
        )

    def __str__(self):
        # 用户友好的字符串表示
        return f"FunctionInvokeArgDefinition(short_option_name={self.short_option_name}, long_option_name={self.long_option_name})"

    def __repr__(self):
        # 官方的字符串表示，用于调试
        return f"FunctionInvokeArgDefinition(short_option_name={self.short_option_name}, long_option_name={self.long_option_name})"


class SubFlag:
    """
    每个函数的定义,每个subcmd都有一个,冗余定义
    """

    def __init__(
        self,
        flags1: list,
        imported_module,
        function_name="",
        function_args=None,
        function_comment="",
        arg_type_desc="",
    ):
        self.function_arg_definition_list: list[FunctionInvokeArgDefinition] = [
            FunctionInvokeArgDefinition(*flag_item)
            for flag_item in tcli.default_flags + flags1
        ]
        # FunctionInvokeArgDefinition(short_option_name=f:, long_option_name=file=)
        # print(
        #     "------ SubFlag:: function_arg_definition_list",
        #     function_name,
        #     self.function_arg_definition_list,
        # )
        self.imported_module = imported_module
        self.function_name = function_name
        self.function_args: ast.arguments = function_args  # type: ignore
        self.function_comment = function_comment
        self.arg_type_desc = arg_type_desc

    def append_undefined_argument(self, subcmd: str):
        if self.function_args:
            function_arg_definition_dict: dict[str, FunctionInvokeArgDefinition] = {}
            for fad in self.function_arg_definition_list:
                function_arg_definition_dict[fad.long_option_name.replace("=", "")] = (
                    fad
                )
            # 找出所有是布尔型的数据类型,布尔型都要设置默认值
            arg_names: list = [*self.function_args.args]
            arg_names.reverse()
            arg_values: list = [*self.function_args.defaults]
            arg_values.reverse()
            bool_arg_name_list: list[str] = []
            for foo_arg_name, foo_default in zip(arg_names, arg_values):
                if isinstance(foo_default, ast.Constant) and isinstance(
                    foo_default.value, bool
                ):
                    # print(
                    #     "------ append_undefined_argument::",
                    #     foo_arg_name.arg,
                    #     foo_default.value,
                    # )
                    bool_arg_name_list.append(foo_arg_name.arg)
            for arg_name in self.function_args.args:  # type: ignore
                long_option_name = arg_name.arg
                if long_option_name not in function_arg_definition_dict:
                    self.function_arg_definition_list.append(
                        FunctionInvokeArgDefinition(
                            "",
                            (
                                long_option_name
                                if long_option_name in bool_arg_name_list
                                else long_option_name + "="
                            ),
                            "undefined argument",
                            [subcmd],
                        )
                    )
                    # ------ SubFlag:: function_args schedule_vilink_handler alias
                    # print(
                    #     "------ SubFlag:: function_args undefined",
                    #     self.function_name,
                    #     long_option_name,
                    # )
        return self

    def get_arg_type_desc_of_subcmd(self, subcmd: str):
        return list(
            map(
                lambda v: (v.short_option_name, v.long_option_name, v.arg_description),
                filter(
                    lambda v: len(v.subcmd_list) == 0 or startwith_in_list(subcmd, v),
                    self.function_arg_definition_list,
                ),
            )
        )

    def invoke(self, function_name: str, *args):
        if hasattr(self.imported_module, function_name):
            return getattr(self.imported_module, function_name)(*args)
        # else:
        #     print(f"{function_name} is not found in {self.imported_module}")

    def invoke_arg_definition(self, *args):
        if self.arg_type_desc:
            foo = self.arg_type_desc.split(",")
            arg_type_defintion_fuc_name = foo.pop(0)
            return self.invoke(f"{arg_type_defintion_fuc_name}", *foo)
        return self.invoke(f"{self.function_name}_arg_definition", *args)

    def __str__(self):
        return f"SubFlag(function_name={self.function_name}, function_arg_definition_list={self.function_arg_definition_list})"


log = tl.log
log.debug(os.path.abspath("."))

flags = [] + tcli.default_flags
subcmds = ["help", "test", "markdown", "install-plugin", "update-yaml"]
sub_flags = {
    "test": SubFlag([], {}),
    "markdown": SubFlag([], {}),
    "install-plugin": SubFlag([], {}),
    "update-yaml": SubFlag([], {}),
}


# 判断当前 Python 版本
if sys.version_info >= (3, 10):
    # Python 3.10 及以上版本使用 | 符号
    FlagType = list | FunctionInvokeArgDefinition
else:
    # Python 3.9 及以下版本使用 Union
    FlagType = Union[list, FunctionInvokeArgDefinition]


def main():
    cli_context_init()
    runtime_log_errors: list[str] = []
    runtime_log_infos: list[str] = []
    set_lib_path(
        runtime_log_infos=runtime_log_infos, runtime_log_errors=runtime_log_errors
    )
    if tl.PRINT_DETAILS:
        print(sys.path)
        log_runtime_msg(
            runtime_log_infos=runtime_log_infos, runtime_log_errors=runtime_log_errors
        )
    if "install-plugin" == sys.argv[1]:
        tpi.install_plugin_handler(sys.argv[2:])
        exit(0)
    if "update-yaml" == sys.argv[1]:
        tpi.update_yaml_handler(sys.argv[2:])
        exit(0)
    module_name_index = 0
    for cli_invoker in dm.ClassScaner(["lib"], ["@cli_invoker"]).scan():
        # module_name = cli_invoker.module_name
        module_file = cli_invoker.module_abs_file
        functions = cli_invoker.decorated_functions
        im = None
        try:
            # spec = spec_from_file_location(module_file)
            external_file = Path(module_file)
            module_name = f"{external_file.stem}_{module_name_index}"
            module_name_index += 1
            # print("---main", module_name, module_file)
            spec = spec_from_file_location(module_name, str(external_file))
            im = module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(im)  # type: ignore
            # print("---main", im.opp, module_file)
            # im = importlib.import_module(module_name)
        except ImportError as e:
            # No module named 'xmltodict'
            failed_module_name = e.msg.split(" ")[-1:][0].strip("'")
            import subprocess

            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", failed_module_name]
                )
                print(f"module {failed_module_name} install successfully!")
            except subprocess.CalledProcessError:
                print(f"install failure, please manually install {failed_module_name}")
            raise e
        opt_parser_in_lib: tcli.OptParser = im.opp
        for subcmd in opt_parser_in_lib.initcli_invoker():
            subcmds.append(subcmd)
            sub_func = [item for item in functions if match_decorator(subcmd, item)][0]
            # subFunc格式@cli_invoker('idea/settings-color')#set idea color\n.idea_setting_color
            # tt = sub_func.split('\n')
            arg_type_desc = tcli.arg_type_desc_mapping[subcmd]
            sub_flags[subcmd] = SubFlag(
                opt_parser_in_lib.src_flags,
                im,
                sub_func.function_name,
                sub_func.function_args,
                sub_func.comment,
                arg_type_desc,
            ).append_undefined_argument(subcmd)

            # bug in there, if x and x= exists both, the last will be skip, so please sure all short is equal
            # if short name is same, please sure long name is same
            # for opt1 in flags1:
            #     tt = [
            #         item
            #         for item in flags
            #         if tcli.strip_equal(opt1[1])[1] == tcli.strip_equal(item[1])[1]
            #         or opt1[0]
            #         and item[0]
            #         and item[0][0:1] == opt1[0][0:1]
            #     ]
            #     if not tt:
            #         flags.append(opt1)
            #     else:
            #         log.debug("duplicated " + str(opt1) + "," + str(tt[0]))

    log.debug(sys.argv)
    cli_args = (
        cli_opt.SubcmdOptParser2(*sys.argv)
        if (
            len(sys.argv) > 2
            and not (sys.argv[1].startswith("-") or sys.argv[2].startswith("-"))
        )
        else cli_opt.SubcmdOptParser1(sys.argv)
    )
    try:
        subcmd = cli_args.get_subcmd()
        # 如果是直接命中的,不需要重新查找了
        if subcmd not in sub_flags:
            # 遍历sub_flags的key,去寻找和输入相同的longest common prefxi
            match_sub_cmd: list[str] = cli_opt.get_all_match_enum_input_value(
                subcmd, *sub_flags.keys()
            )
            # print("------ main", subcmd, match_sub_cmd, sub_flags.keys())
            if len(match_sub_cmd) == 1:
                subcmd = match_sub_cmd[0]
                log.warning(
                    f"the correactive subcmd is {subcmd.replace('/', ' ')} for {cli_args.get_subcmd().replace('/', ' ')}"
                )
            elif len(match_sub_cmd) > 1:
                print(
                    f"Could you try the flollowing for {subcmd}?",
                )
                for foo_subcmd in match_sub_cmd:
                    print(foo_subcmd.replace("/", " "))
        if subcmd not in sub_flags:
            # log.error(f"sub command {subcmd.replace('/', ' ')} is not defined!")
            return print_usage()
            # sys.exit(1)
        # print("------ main:: sub_flags", sub_flags[subcmd])
        arg_type_desc_of_subcmd = sub_flags[subcmd].get_arg_type_desc_of_subcmd(subcmd)
        short_str = "".join([key[0] for key in arg_type_desc_of_subcmd])
        long_arr = [key[1] for key in arg_type_desc_of_subcmd]
        # subcmds ['help', 'test', 'code/test', 'code/gitlog', 'code/vscode', 'code/autonum', 'code/charts', 'code/log', 'code/show', 'code/print', 'code/cat', 'code/more', 'code/list', 'code', 'code/route', 'code/python-plugin', 'code/linux-plugin', 'code/linux-cli', 'install/hello', 'install', 'install/mvn', 'install/ium', 'install/opsclear', 'install/opswar', 'install/pushopswar', 'install/ciswar', 'install/pushciswar', 'install/gwt', 'install/plugins', 'install/mscommon', 'install/msapp', 'install/only', 'install/demo', 'install/npmlink', 'install/rtc', 'install/dns', 'install/hpe', 'install/route', 'install/sync', 'install/synclicense', 'install/syncl', 'install/patch', 'install/clone', 'install/batch', 'install/fingerprint', 'eclipse', 'eclipse/ops', 'eclipse/cis', 'eclipse/ide.eclipse', 'eclipse/opsdebug', 'eclipse/externalium', 'eclipse/ei', 'eclipse/runtime', 'eclipse/ri', 'eclipse/test', 'host/show', 'host/print', 'host/cat', 'host/more', 'host/test', 'host', 'host/enable', 'host/disable', 'host/vscode', 'host/npm', 'host/python', 'image/test', 'syncapp', 'k8s', 'k8s/deploy', 'k8s/yaml', 'linux', 'linux/hello', 'sshcli/put', 'sshcli/get', 'sshcli/ssh', 'sshcli', 'sshcli/test', 'vilink/monitor', 'vilink', 'vilink/push', 'vilink/push-umbrella', 'vilink/push-file', 'vilink/pull', 'vilink/init', 'vilink/add', 'vilink/remove', 'vilink/github', 'vilink/redo', 'sha1', 'build']
        # short_str hf:dn:n:
        # long_arr ['help', 'file=', 'debug', 'name=', 'name-type']
        # opts, args [('-n', 'aaaa'), ('-d', '')] []
        # opts, args [('--name', 'aaaa'), ('-d', '')], []

        # print("---cli_args.getopt", long_arr)

        opts, args = cli_args.getopt(arg_type_desc_of_subcmd, short_str, long_arr)
        # print(
        #     "---opts, args",
        #     opts,
        #     args,
        #     "arg_type_desc_of_subcmd=",
        #     arg_type_desc_of_subcmd,
        #     "short_str=",
        #     short_str,
        #     "long_arr=",
        #     long_arr,
        # )
        # sys.exit(0)
        if subcmd == "help":
            return print_usage()
        else:
            for flag, arg in opts:
                if flag == "-h" or flag == "--help":
                    return print_subcmd_usage(subcmd)

    except cli_opt.SubcmdException as e:
        log.debug(e)
        subcmd = str(e).split()[0][1:]
        if subcmd and [item for item in subcmds if (subcmd + "/") in item]:
            return print_subcmd2_usage(subcmd)
        else:
            print(e)
            return print_usage()
    except Exception as e:
        print(e, type(e))
        errorTrace = traceback.format_exc()
        log.error(errorTrace)
        return print_usage()
    try:
        opts = tcli.convert_arg_dict(subcmd, opts_2_dict(opts))
        # print("------ main:: opts subcmd", opts, subcmd)
        if "test" == subcmd:
            all_2_step_subcmds = [subcmd for subcmd in subcmds if "/" in subcmd]
            with open("pycli-help.json", "w") as outfile:
                json.dump(
                    [to_usage_json(subcmd) for subcmd in all_2_step_subcmds], outfile
                )
            # log.info(ts.call('ps -ef', 'grep s'))

            # log.info(getattr(importlib.import_module('lib.libchanged'),'cli_invoker')())
        elif "markdown" == subcmd:
            all_2_step_subcmds = [subcmd for subcmd in subcmds if "/" in subcmd]
            with open("pycli-help.md", "w", encoding="utf-8") as outfile:
                outfile.write(
                    f"""
# pycli 命令行
"""
                )
                for lines in [
                    to_usage_markdown(subcmd) for subcmd in all_2_step_subcmds
                ]:
                    outfile.writelines(
                        [line if line.endswith("\n") else f"{line}\n" for line in lines]
                    )

        elif subcmd in sub_flags:
            im = sub_flags[subcmd].imported_module
            opt_parser_in_lib: tcli.OptParser = im.opp
            opt_parser_in_lib.set_subcmd(subcmd, arg_type_desc_of_subcmd)
            subFuncs = sub_flags[subcmd].function_name.split(".")
            classname = None if len(subFuncs) <= 1 else subFuncs[0]
            funcname = subFuncs[len(subFuncs) - 1]
            if classname:
                log.info("no support for classname")
            else:
                # 通过调用create_wrapper来完成最终调用,
                getattr(im, funcname)(opts, opt_parser_in_lib)

        else:
            log.error("unkown function:" + subcmd)
    except cli_opt.NoArgException as e:
        print("Argument Validation::", e)
        # errorTrace = traceback.format_exc()
        # log.error(errorTrace)
    except Exception as e:
        errorTrace = traceback.format_exc()
        # sys.stderr.write(errorTrace)
        # sys.stderr.write('directory scp:')
        log.error(errorTrace)
        sys.exit(1)


def print_usage():
    usages = ["Usage:", "   pycli command", "   Commands"]
    for line in usages:
        print(line)
    for line in list(set([l.split("/")[0] for l in subcmds])):
        print("{:5}{}".format(" ", line))
    print("command -h or --help to get help information")


def print_subcmd2_usage(subcmd):
    usages = ["Usage:", "   pycli " + subcmd + " command", "   Commands"]
    for line in usages:
        print(line)
    for line in [
        line2[len(subcmd) + 1 :] for line2 in subcmds if (subcmd + "/") in line2
    ]:
        print("{:5}{}".format(" ", line))
    print("command -h or --help to get help information")


def startwith_in_list(subcmd: str, flag: FlagType):
    """
    flag 有可能是个多重数组,所以需要扁平化
    subcmd 可能是没有/的,也需要判断加上/的
    """
    if isinstance(flag, FunctionInvokeArgDefinition):
        for item in flag.subcmd_list:
            if subcmd == item or (subcmd + "/") in item:
                return True
    else:
        for item in _flatten(flag):
            if subcmd == item or (subcmd + "/") in item:
                return True
    return False


def to_usage_markdown(subcmd: str):
    args = []
    if subcmd not in sub_flags:
        return args
    func_sub_flag: SubFlag = sub_flags[subcmd]
    if not sub_flags[subcmd].function_name:
        return args
    comment = sub_flags[subcmd].function_comment
    subcmd_input = subcmd.replace("/", " ").replace("install", "deploy")
    # description
    args.append(
        f"""
## {subcmd_input}"""
    )
    args.append(
        f"""
{comment}

"""
    )
    short_option_arg_definition_dict: dict[str, str] = (
        func_sub_flag.invoke_arg_definition()
    )  # type: ignore
    if not short_option_arg_definition_dict:
        short_option_arg_definition_dict = {}
    for fad in func_sub_flag.function_arg_definition_list:
        if len(fad.subcmd_list) == 0 or startwith_in_list(subcmd, fad):
            short_option_name = (
                fad.short_option_name[0:1] if fad.short_option_name else ""
            )
            arg_description = (
                short_option_arg_definition_dict[short_option_name]
                if short_option_name in short_option_arg_definition_dict
                else fad.arg_description
            )
            onOff, long_param = tcli.strip_equal(fad.long_option_name)
            long_hints = "string" if onOff else "boolean"
            args.append(
                f"- {long_hints} -{short_option_name}, --{long_param}: {arg_description}"
            )
    addition_sub_cmd = subcmd.replace("/", "-").replace("install", "deploy")
    addition_sub_cmd_json_file = os.path.join(
        expanduser("~"), ".ium", f"pycli-{addition_sub_cmd}.json"
    )
    # 检查额外得~\.ium\pycli-{}
    if os.path.exists(addition_sub_cmd_json_file):
        with open(addition_sub_cmd_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data, start=1):
            args.append(
                f"""
### {subcmd_input} {item.get("name", "")}

{item.get("description", "")}

"""
            )
            if item.get("params"):
                for key, value in item.get("params", {}).items():
                    print_value = value
                    if "pw" == key or "usr" == key:
                        print_value = "******"
                    args.append(f"- --{key}: {print_value}")
    return args


def to_usage_json(subcmd: str):
    args = {}
    if subcmd not in sub_flags:
        return args
    func_sub_flag: SubFlag = sub_flags[subcmd]
    if not sub_flags[subcmd].function_name:
        return args
    comment = sub_flags[subcmd].function_comment
    args["description"] = comment
    args["func"] = subcmd
    params = []
    args["arguments"] = params
    short_option_arg_definition_dict: dict[str, str] = (
        func_sub_flag.invoke_arg_definition()
    )  # type: ignore
    if not short_option_arg_definition_dict:
        short_option_arg_definition_dict = {}
    for fad in func_sub_flag.function_arg_definition_list:
        if len(fad.subcmd_list) == 0 or startwith_in_list(subcmd, fad):
            short_option_name = (
                fad.short_option_name[0:1] if fad.short_option_name else ""
            )
            arg_description = (
                short_option_arg_definition_dict[short_option_name]
                if short_option_name in short_option_arg_definition_dict
                else fad.arg_description
            )
            parameter = {}
            onOff, long_param = tcli.strip_equal(fad.long_option_name)
            long_hints = "string" if onOff else "boolean"
            parameter["mandatory"] = long_hints
            parameter["short_option"] = short_option_name
            parameter["long_option"] = long_param
            parameter["description"] = arg_description
            params.append(parameter)
    return args


def print_subcmd_usage(subcmd):
    if subcmd and [item for item in subcmds if (subcmd + "/") in item]:
        print_subcmd2_usage(subcmd)
        print("{:->60}".format(""))
    func_sub_flag: SubFlag = sub_flags[subcmd]
    comment = func_sub_flag.function_comment
    if comment:
        print(comment)
    print("Usage:", subcmd, "flags", "options")
    # [('h', 'help', 'print help information'), ('f:', 'file=', 'the context file by yaml format')]
    # subFlags[subcmd][0]
    # [('d', 'debug', 'enable/disable debug, boolean type sample', ['install/hello']), ('n:', 'name=', 'foo name, data passed sample', ['install/hello']), ('n:', 'name-type', 'foo name, data passed sample', ['install/hello']), ('s:', 'src=', 'src folder', 'install/sync'), ('t:', 'target=', 'target folder', 'install/sync'), ('i:', 'include=', 'include sync folder/file template', 'install/sync'), ('e:', 'exclude=', 'exclude sync folder/file template', 'install/sync'), ('r', 'recursive', 'search all child folder', 'install/sync'), ('v', 'verbose', 'show detail infomation', 'install/sync'), ('m', 'mirror', 'target mirror src', 'install/sync'), ('s', 'source', 'source:jar', 'install', 'install/mvn'), ('j', 'jdk8', 'use jdk8 to build', 'install', 'install/mvn'), ('b', 'nobuild', 'skip build', 'install', 'install/mvn', 'install/rtc'), ('p:', 'pom=', '-f pom.xml', 'install', 'install/mvn'), ('l', 'npmlink', 'use npmlink or js', 'install/npmlink', 'install/rtc'), ('v:', 'version=', 'version like 10.1', 'install/npmlink', 'install/rtc'), ('m:', 'module=', 'module name like rtc', 'install/npmlink', 'install/rtc'), ('w', 'web', 'build react web', 'install/rtc'), ('k', 'backend', 'build total backend for dependency', 'install/rtc'), ('t', 'git', 'back to git repo and deploy to cloud', 'install/opswar', 'install/ciswar', 'install/plugins', 'install/rtc'), ('r:', 'branch=', 'branch 90_cpe, build which branch', ['install/ium', 'install/opsclear', 'install/opswar', 'install/ciswar', 'install/pushopswar', 'install/pushciswar', 'install/plugins', 'install/patch']), ('t:', 'target=', 'ant target', 'install/ium'), ('r:', 'branch=', 'sync which npm package like antd', 'install/npmlink'), ('r:', 'branch=', 'demo branch,any char', 'install/demo'), ('', 'total_type=', 'demo total,any char', 'install/demo'), ('', 'total=', 'demo total,any char', 'install/demo'), ('', 'total-type=', 'demo total,any char', 'install/demo'), ('m:', 'module=', 'demo module,any char', 'install/demo'), ('r:', 'branch=', 'which gwt branch to compile, [2.9.0/master]', 'install/gwt'), ('p:', 'params=', 'additional parameters in scripts', 'install/batch'), ('n:', 'name=', 'by name', 'install/batch'), ('r:', 'branch=', 'new branch name', 'install/clone'), ('n:', 'reponame=', 'by git repo name', 'install/clone'), ('u:', 'user=', 'user name in remote', ['install/pushopswar', 'install/pushciswar']), ('n:', 'host=', 'hostname or ip', ['install/fingerprint', 'install/pushopswar', 'install/pushciswar'])]
    short_option_arg_definition_dict: dict[str, str] = (
        func_sub_flag.invoke_arg_definition()
    )  # type: ignore
    if not short_option_arg_definition_dict:
        short_option_arg_definition_dict = {}
    for fad in func_sub_flag.function_arg_definition_list:
        log.debug(fad.subcmd_list)
        if len(fad.subcmd_list) == 0 or startwith_in_list(subcmd, fad):
            onOff, long_param = tcli.strip_equal(fad.long_option_name)
            long_hints = "string" if onOff else "      "
            short_option_name = (
                fad.short_option_name[0:1] if fad.short_option_name else ""
            )
            arg_description = (
                short_option_arg_definition_dict[short_option_name]
                if short_option_name in short_option_arg_definition_dict
                else fad.arg_description
            )
            print(
                (("-" if short_option_name else " ") + "{:5}--{:20}{:20}{}").format(
                    short_option_name if short_option_name else "  ",
                    long_param + ":",
                    long_hints,
                    arg_description,
                )
            )


# opts [('--name', 'aaaa'), ('-d', '')]
def opts_2_dict(opts: list[tuple[str, str]]) -> dict[str, str]:
    dic: dict[str, str] = {}
    for arg_name, arg_value in opts:
        dic[arg_name.replace("-", "", 2)] = arg_value
    return dic


def match_decorator(subcmd, item: DecoratedFunction):
    # isinstance(item.decorator.args[0], ast.Str)
    # print(
    #     "---match_decorator",
    #     ast.unparse(item.decorator.args[0]).strip("'"),
    #     item.decorator.args[0].s,
    #     item.decorator.args[0].value,
    # )
    # 第一个参数(args[0])是函数定义字符串例如code/react,第二个参数是函数类型定义(args[1])
    subcmd_str: str = item.decorator.args[0].value  # type: ignore
    return subcmd in tcli.more_subcmd(subcmd_str)


def cli_context_init():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf8")
    tssh.init_sshcli(thpe.load_yaml_from_install("sshcli"))
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)


def log_runtime_msg(runtime_log_infos: list[str], runtime_log_errors: list[str]):
    for msg in runtime_log_errors:
        log.error(msg)
    for msg in runtime_log_infos:
        log.info(msg)


def set_lib_path_sys_path_handler(
    runtime_log_infos: list[str], runtime_log_errors: list[str]
):
    # 29 ms
    for name in metadata.distributions():
        if name.metadata["Name"].startswith("scm-python-"):  # scm-python-
            plugin_name = name.metadata["Name"]
            base_path = name.locate_file("")
            external_lib_path = str(base_path / plugin_name.replace("-", "_"))
            external_lib = Path(external_lib_path)
            if not external_lib.exists():
                runtime_log_errors.append(f"{external_lib_path} is not exists")
            else:
                runtime_log_infos.append(f"found external lib in {external_lib_path}")
                sys.path.append(str(external_lib.resolve()))
                dm.ClassScaner.class_paths.append(str(external_lib.resolve()))


def set_lib_path_user_customized_handler(
    runtime_log_infos: list[str], runtime_log_errors: list[str]
):
    python_dict = thpe.load_yaml_from_install("python", skip_replace=True)
    if python_dict and "external_lib" in python_dict:
        for external_lib_path in python_dict["external_lib"]:
            external_lib = Path(external_lib_path)
            if not external_lib.exists():
                runtime_log_errors.append(f"{external_lib_path} is not exists")
            else:
                runtime_log_infos.append(f"found external lib in {external_lib_path}")
                # (external_lib / "__init__.py").touch(exist_ok=True)
                sys.path.append(str(external_lib.resolve()))
                dm.ClassScaner.class_paths.append(str(external_lib.resolve()))


def set_lib_path(runtime_log_infos: list[str], runtime_log_errors: list[str]):
    set_lib_path_sys_path_handler(
        runtime_log_infos=runtime_log_infos, runtime_log_errors=runtime_log_errors
    )
    set_lib_path_user_customized_handler(
        runtime_log_infos=runtime_log_infos, runtime_log_errors=runtime_log_errors
    )


def sigint_handler(signum, frame):
    print("catched interrupt signal!", flush=True)
    tl.do_signal_handler(signum, frame)
    sys.exit(0)


if __name__ == "__main__":
    main()
