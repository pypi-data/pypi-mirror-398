import sys, getopt, re
from typing import Literal
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tcli as tcli
from .context_opt import get_field

log = tl.log
BUILT_IN_ENUM_RETURN_TYPE_LITERAL = Literal["unique", "all"]
ENABLE_UNIT_TEST = False


def get_match_enum_input_value(input_value: str, *enum_strs: str):
    foo_list_str = [*enum_strs]
    if input_value.find("/") > -1:
        separator_num = 1
        for arg_name in input_value.split("/"):
            foo_list_str = get_option_enum_input_value(
                arg_name, "unique", separator_num, *foo_list_str
            )
            separator_num += 1
    else:
        foo_list_str = get_option_enum_input_value(
            input_value, "unique", 0, *foo_list_str
        )
    return "" if len(foo_list_str) == 0 else foo_list_str[0]


def get_all_match_enum_input_value(input_value: str, *enum_strs: str):
    foo_list_str = [*enum_strs]
    if input_value.find("/") > -1:
        separator_num = 1
        for arg_name in input_value.split("/"):
            foo_list_str = get_option_enum_input_value(
                arg_name, "all", separator_num, *foo_list_str
            )
            separator_num += 1
    else:
        foo_list_str = get_option_enum_input_value(input_value, "all", 0, *foo_list_str)
    return foo_list_str


def get_option_enum_input_value(
    input_value: str,
    return_type: BUILT_IN_ENUM_RETURN_TYPE_LITERAL,
    separator_num: int,
    *enum_strs: str,
) -> list[str]:
    exact_match_input_value: list[str] = []
    prefix_match_input_value: list[str] = []
    lcp_match_input_value: list[str] = []
    contain_match_intput_value: list[str] = []
    lcp_match_input_value_match_char_number_dict: dict = {}
    for v1 in enum_strs:
        if separator_num > 0:
            foo_list = v1.split("/")
            if len(foo_list) < separator_num:
                continue
            arg_name = foo_list[separator_num - 1]
        else:
            arg_name = v1
        # known issues: ssz,2025.9.24 此时大小写是区分的,是否不区分大小写更加合理?
        # if input_value.casefold() == arg_name.casefold():
        if input_value == arg_name:
            exact_match_input_value.append(v1)
            continue
        if input_value and arg_name.startswith(input_value):
            prefix_match_input_value.append(v1)
        foo_lcp_str = longest_common_prefix(input_value, arg_name)
        # know issues: ssz, 2025.9.24 匹配最长的应该放在开始, 一般代码都采用list[0]
        if foo_lcp_str:
            # lcp_match_input_value.append(v1)
            lcp_match_input_value_match_char_number_dict[v1] = len(foo_lcp_str)
        # 还是包含在longest common prefix中比较make sense
        elif input_value and arg_name.find(input_value) > -1:
            contain_match_intput_value.append(v1)
    if exact_match_input_value:
        return exact_match_input_value
    if lcp_match_input_value_match_char_number_dict:  # 非空时为 True
        # 按 value 从大到小排序，返回 key 的列表
        lcp_match_input_value = sorted(
            lcp_match_input_value_match_char_number_dict,
            key=lambda k: lcp_match_input_value_match_char_number_dict[k],
            reverse=True,
        )
    # 可能还有其它返回方式
    if "unique" == return_type and len(prefix_match_input_value) == 1:
        return prefix_match_input_value
    if "unique" == return_type and len(lcp_match_input_value) == 1:
        return lcp_match_input_value
    if "unique" == return_type and len(contain_match_intput_value) == 1:
        return contain_match_intput_value
    if "all" == return_type and len(prefix_match_input_value) >= 1:
        return prefix_match_input_value
    if "all" == return_type and len(lcp_match_input_value) >= 1:
        return lcp_match_input_value
    if "all" == return_type and len(contain_match_intput_value) >= 1:
        return contain_match_intput_value
    return []


def longest_common_prefix(*strs: str):
    if not strs:
        return ""

    # 取第一个字符串作为参考前缀
    prefix = strs[0]

    # 从第二个字符串开始与前缀比较
    for string in strs[1:]:
        # 比较当前字符串与当前前缀，逐字符截断前缀
        while string[: len(prefix)] != prefix and prefix:
            prefix = prefix[:-1]

        # 如果前缀为空，直接返回空字符串
        if not prefix:
            return ""
    return prefix


def workaround_for_short_options(opts):
    """
    dos batch cmd中有时候会把-u=的=带进去所以要workaround它
    """
    index = 0
    for flag, arg in opts:
        if len(flag) == 2 and arg[0:1] == "=":
            opts[index] = (flag, arg[1:])
        index += 1


def get_long_option_name(long_option: str) -> tuple[str, str]:
    """
    如果包含'='的部分结尾去掉它
    """
    index = long_option.find("=")
    return (
        (long_option[:index], long_option[index:]) if index > -1 else (long_option, "")
    )


def aggregation_correactive_command_is_match_handler(
    aggregation_command_list: list[str], aggregation_command_name: str
):
    arg_num = 0
    match_arg_num = 0
    # print(
    #     "---aggregation_correactive_command_is_match_handler",
    #     aggregation_command_name,
    #     aggregation_command_list,
    # )
    for arg_name in re.split(r"\s+", aggregation_command_name):
        if (
            arg_num < len(aggregation_command_list)
            and len(
                get_all_match_enum_input_value(
                    aggregation_command_list[arg_num], arg_name
                )
            )
            > 0
        ):
            match_arg_num += 1
        arg_num += 1
    # print(
    #     "------ aggregation_correactive_command_is_match_handler:: arg_num",
    #     arg_num,
    #     match_arg_num,
    #     aggregation_command_name,
    #     len(aggregation_command_list),
    # )
    return match_arg_num >= len(aggregation_command_list)


def aggregation_correactive_command_handler(
    subcmd: str,
    aggregation_command_list: list[str],
    aggregation_defintion: list[dict],
    args: list[str],
    no_any_cli_handler,
    command_is_match_handler=None,
):
    match_command_list: list[str] = []
    last_aggregation_command_definition: dict
    if not command_is_match_handler:
        command_is_match_handler = aggregation_correactive_command_is_match_handler
    for aggregation_command_definition in aggregation_defintion:
        aggregation_command_name = aggregation_command_definition["name"]
        if command_is_match_handler(aggregation_command_list, aggregation_command_name):
            match_command_list.append(aggregation_command_name)
            last_aggregation_command_definition = aggregation_command_definition
    # 如果完全匹配就直接命中
    if len(match_command_list) > 1:
        for aggregation_command_name in match_command_list:
            if aggregation_command_name == " ".join(aggregation_command_list):
                match_command_list = [aggregation_command_name]
                break
    if len(match_command_list) > 1:
        print(
            f"1Could you try the following for {subcmd.replace('/', ' ')}[{len(match_command_list)}]"
        )
        for aggregation_command_name in match_command_list:
            print(f"--{subcmd.replace('/', ' ')} {aggregation_command_name}")
        if ENABLE_UNIT_TEST:
            raise Exception(
                f"Multiple cli handle found for {subcmd.replace('/', ' ')} {aggregation_command_list}"
            )
        else:
            sys.exit(1)
    if len(match_command_list) == 0:
        print(
            f"It seems that no any cli handler for {subcmd.replace('/', ' ')} {' '.join(aggregation_command_list)}"
        )
        if no_any_cli_handler:
            no_any_cli_handler(" ".join(aggregation_command_list), args)
        if ENABLE_UNIT_TEST:
            raise Exception(
                f"It seems that no any cli handler for {subcmd.replace('/', ' ')} {' '.join(aggregation_command_list)}"
            )
        else:
            sys.exit(1)
    return match_command_list[0], last_aggregation_command_definition


def aggregation_correactive_long_option_handler(
    longopts: list[str], aggregation_params_defintion: dict
):
    longopts.clear()
    for long_optio_tuple in tcli.default_flags:
        longopts.append(long_optio_tuple[1])
    for long_option_name in aggregation_params_defintion:
        longopts.append(f"{long_option_name}=")


def aggregation_correactive_handler(
    subcmd: str, args: list[str], longopts: list[str]
) -> bool:
    has_option = False
    aggregation_command_list: list[str] = []
    for arg in args:
        if arg.startswith("-"):
            has_option = True
            if len(aggregation_command_list) > 0:
                break
        else:
            if not has_option:
                aggregation_command_list.append(arg)
    has_aggreation = len(aggregation_command_list) > 0
    if has_aggreation:
        # print(
        #     "------ aggregation_correactive_handler:: has_aggreation",
        #     aggregation_command_list,
        # )
        aggregation_defintion = tcli.get_aggregation_defintion(subcmd)
        if not aggregation_defintion:
            print(f"define aggregation for {subcmd.replace('/', ' ')} is required")
            sys.exit(1)
        aggregation_correactive_commands, aggregation_command_definition = (
            aggregation_correactive_command_handler(
                subcmd,
                aggregation_command_list,
                aggregation_defintion,
                args,
                tcli.get_no_any_cli_handler_defintion(subcmd),
                tcli.get_command_is_match_handler_defintion(subcmd),
            )
        )
        # 纠正--name
        for arg_name in aggregation_command_list:
            args.remove(arg_name)
        new_aggregation_command_list: list[str] = (
            aggregation_correactive_commands.split(r"\s+")
        )
        new_aggregation_command_list.reverse()
        for arg_name in new_aggregation_command_list:
            args.insert(0, arg_name)
        aggregation_params_defintion = aggregation_command_definition["params"]
        aggregation_correactive_long_option_handler(
            longopts, aggregation_params_defintion
        )

    return has_aggreation


def prefix_match_getopt(
    subcmd: str,
    arg_type_desc_of_subcmd: list[tuple[str, str, str]],
    args: list[str],
    short_str: str,
    longopts: list[str],
):

    new_args: list[str] = []
    # arg_type_desc_of_subcmd_dict {'help': 'h', 'quiet': '', 'file': 'f:', 'type': 't:', 'local_template': 'l', 'local-template': 'l', 'package': 'a:', 'solution_package': 's:', 'solution-package': 's:', 'project': 'p:'}
    arg_type_desc_of_subcmd_dict: dict[str, str] = {}
    for arg_type_desc_item in arg_type_desc_of_subcmd:
        foo_long_option = arg_type_desc_item[1]
        foo_short_str = arg_type_desc_item[0]
        if foo_long_option:
            foo_handled_long_option, _ = get_long_option_name(foo_long_option)
            arg_type_desc_of_subcmd_dict[foo_handled_long_option] = foo_short_str
    # args ['--package=com.demo.dd.tools', '--project=xxx', '--local']
    for arg in args:
        if arg.startswith("--"):
            # user_input_long_option package=com.demo.dd.tools
            user_input_long_option, user_input_long_option_remains = (
                get_long_option_name(arg[2:])
            )
            # print(
            #     "------ prefix_match_getopt::user_input_long_option, user_input_long_option_remains",
            #     user_input_long_option,
            #     user_input_long_option_remains,
            # )
            long_option_name_list = [
                (
                    foo_long_option
                    if foo_long_option.find("=") == -1
                    else foo_long_option[:-1]
                )
                for foo_long_option in longopts
            ]
            # print(
            #     "------ prefix_match_getopt::long_option_name_list",
            #     long_option_name_list,
            # )
            prefix_match: list[str] = get_all_match_enum_input_value(
                user_input_long_option,
                # 去掉最后一个=,参数定义里的,表示带值的参数
                *long_option_name_list,
            )
            # print(
            #     "------ prefix_match_getopt::prefix_match",
            #     prefix_match,
            #     "user_input_long_option",
            #     user_input_long_option,
            #     "long_option_name_list",
            #     long_option_name_list,
            # )
            # 如果是直接命中的,不需要重新查找了
            # if user_input_long_option not in arg_type_desc_of_subcmd_dict:
            #     prefix_match = [
            #         opt
            #         for opt in longopts
            #         if longest_common_prefix(opt, user_input_long_option)
            #     ]
            # 过滤掉短参数相同的长参数
            # known issues: ssz,2025.9.24 如果长参数都没有相应的短参数,那最终返回参数就是第一个匹配的值,而最长前缀队列是从大到小排序的,Sub-task和Sub-Task输入最长前缀是3,比Story大,所以返回它
            if len(prefix_match) > 1:
                long_arg_name_foo = prefix_match[0]
                prefix_match = [
                    long_arg_name
                    for long_arg_name in prefix_match
                    if get_field(arg_type_desc_of_subcmd_dict, long_arg_name, "")
                    != get_field(arg_type_desc_of_subcmd_dict, long_arg_name_foo, "")
                ]
                prefix_match.insert(0, long_arg_name_foo)
            if len(prefix_match) == 1:
                # print(
                #     "------ prefix_match_getopt::",
                #     "--" + prefix_match[0],
                #     "user_input_long_option_remains=",
                #     user_input_long_option_remains,
                # )
                # 如果有聚合,纠正当前输入参数名字没有意义,因为参数名字为止
                # if has_aggreation:
                #     new_args.append(
                #         "--" + user_input_long_option + user_input_long_option_remains
                #     )
                # else:
                new_args.append("--" + prefix_match[0] + user_input_long_option_remains)
            elif len(prefix_match) > 1:
                print(f"2Could you try the following for {arg}")
                for foo_long_option in prefix_match:
                    print(f"--{foo_long_option}")
                sys.exit(1)
                # raise getopt.GetoptError(f"Ambiguous option: {arg}")
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)
            # ['--port', '22', '--remote', 'root@192.168.50.246:/ssz_share/scripts/lib/kernal/', '--local', 'C:/usr/ssz/workspace/git/app/scm/linux-bash/common/kernal/__lib_kernal.sh']
    # print("------ prefix_match_getopt:: getopt.getopt", new_args, short_str, longopts)
    return getopt.getopt(new_args, short_str, longopts)


def aggregation_handler(opts: list[tuple[str, str]], args: list[str]):
    name_list: list[str] = []
    params_list: list[str] = []
    pending_option_name: str = ""
    # Known issues: ssz, 2025.10.13, 考虑系统缺省的参数,它们不应该被聚合
    for arg_item in args:
        if arg_item.startswith("-"):
            # 输入--option=option_value形式
            if arg_item.find("=") > -1:
                long_option_name_value_pair = arg_item.lstrip("-")
                long_option_name, long_option_value = long_option_name_value_pair.split(
                    "=", 1
                )
                if tcli.is_default_flag(long_option_name):
                    opts.append((f"--{long_option_name}", long_option_value))
                else:
                    params_list.append(long_option_name_value_pair)
            else:
                # 连续输入二个--,说明前一个是bool
                if pending_option_name:
                    if tcli.is_default_flag(pending_option_name):
                        opts.append((f"--{pending_option_name}", True))
                    else:
                        params_list.append(f"{pending_option_name}=true")
                pending_option_name = arg_item.lstrip("-")
        else:
            # 如果有pending option name, 说明是参数部分,输入--option option_value形式
            if pending_option_name:
                if tcli.is_default_flag(pending_option_name):
                    opts.append((f"--{pending_option_name}", arg_item))
                else:
                    params_list.append(f"{pending_option_name}={arg_item}")
                pending_option_name = ""
            else:
                name_list.append(arg_item)
    # 检查最后一个是否为bool
    if pending_option_name:
        if tcli.is_default_flag(pending_option_name):
            opts.append((f"--{pending_option_name}", True))
        else:
            params_list.append(f"{pending_option_name}=true")
        pending_option_name = ""
    args.clear()
    if len(name_list) > 0:
        opts.append(("--name", " ".join(name_list)))
    if len(params_list) > 0:
        opts.append(("--params", ",".join(params_list)))


class NoArgException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class IlleagalArgException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SubcmdException(NoArgException):
    pass


class SubcmdOptParser1(object):
    """
    一段命令处理器,一般为cli lib的缺省处理函数例如pycli host
    """

    argv = []

    def __init__(self, argv):
        self.argv = argv

    def get_subcmd(self) -> str:
        """get subcmd
        Returns:
            str: _description_
            Known Issus: 2024-09-03,deploy需要转换为install,如果绕过批处理直接输入pycli deploy
        """
        raw_subcmd = self.argv[1] if len(self.argv) > 1 else ""
        return "install" if raw_subcmd == "deploy" else raw_subcmd

    def getopt(
        self,
        arg_type_desc_of_subcmd: list[tuple[str, str, str]],
        short_str: str,
        long_options: list[str],
    ):
        if len(self.argv) < 2:
            raise NoArgException("at lease one argument")
        raw_argv = self.argv[2:]
        try:
            opts, args = (
                prefix_match_getopt(
                    self.get_subcmd(),
                    arg_type_desc_of_subcmd,
                    self.argv[2:],
                    short_str,
                    long_options,
                )
                if long_options
                else getopt.getopt(self.argv[2:], short_str)
            )
            return opts, args
        except getopt.GetoptError as e:
            print(
                "-------- SubcmdOptParser1",
                raw_argv,
                self.argv[2:],
                short_str,
                long_options,
            )
            raise NoArgException(e)


class SubcmdOptParser2(SubcmdOptParser1):
    """
    带/参数的处理器,有2段命令组成,例如code solution
    """

    argv: list[str] = []

    def __init__(self, *argv: str):
        self.argv = list(argv)

    def get_subcmd(self):
        """get subcmd
        Returns:
            str: _description_
            Known Issus: 2024-09-03,deploy需要转换为install,如果绕过批处理直接输入pycli deploy
        """
        raw_command = self.argv[1] if self.argv[1] != "deploy" else "install"
        return f"{raw_command}/{self.argv[2]}"

    def getopt(
        self,
        arg_type_desc_of_subcmd: list[tuple[str, str, str]],
        short_str: str,
        long_options: list[str],
    ):
        if len(self.argv) < 3:
            raise NoArgException("at lease two argument")
        raw_argv = self.argv[3:]
        try:
            # opts: [('-l', ''), ('--branch', 'aaa')]
            # print("------ getopt:: prefix_match_getopt argv", self.argv)
            args = self.argv[3:]
            has_aggreation = aggregation_correactive_handler(
                self.get_subcmd(), args, long_options
            )
            # Known issues: ssz, 2025.10.13, 这里会修改args内容, 之前都是用户输入的
            opts, args = (
                prefix_match_getopt(
                    self.get_subcmd(),
                    arg_type_desc_of_subcmd,
                    args,
                    short_str,
                    long_options,
                )
                if long_options
                else getopt.getopt(args, short_str)
            )
            workaround_for_short_options(opts)
            # print("------ getopt::opts,args", opts, args)
            # Known issues: ssz, 2025.10.13, 这里会修改args的内容
            if has_aggreation:
                aggregation_handler(opts, args)
            return opts, args
        except getopt.GetoptError as e:
            print(
                "--------SubcmdOptParser2",
                raw_argv,
                self.argv[3:],
                short_str,
                long_options,
            )
            raise NoArgException(e)
