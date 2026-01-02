import yaml
import copy
import inspect
import traceback
from datetime import datetime
from tkinter import _flatten  # type: ignore
from typing import Callable, Union, List, TypeVar, Any

import tlog.tlogging as tl
import tutils.cli_opt as opt

log = tl.log
default_flags = [
    ("h", "help", "print help information"),
    ("", "show-detail", "print debug information"),
    ("", "quiet", "no log"),
    ("", "preserve-log", "preserve log"),
    ("f:", "file=", "the context file by yaml format"),
]


def is_default_flag(long_option_name: str):
    for option_tuple_item in default_flags:
        if option_tuple_item[1].rstrip("=") == long_option_name:
            return True
    return False


arg_type_desc_mapping: dict[str, str] = {}
arggreation_command_options_mapping: dict = {}
no_any_cli_handler_mapping: dict = {}
command_is_match_handler_mapping: dict = {}
arg_data_type_converter: dict = {}


def get_aggregation_defintion(subcmd: str) -> Union[list[dict], None]:
    if subcmd in arggreation_command_options_mapping:
        return arggreation_command_options_mapping[subcmd]()


def get_no_any_cli_handler_defintion(subcmd: str) -> Union[list[dict], None]:
    if subcmd in no_any_cli_handler_mapping:
        return no_any_cli_handler_mapping[subcmd]


def get_command_is_match_handler_defintion(subcmd: str) -> Union[list[dict], None]:
    if subcmd in command_is_match_handler_mapping:
        return command_is_match_handler_mapping[subcmd]


def convert_arg_dict(subcmd: str, arg_dict: dict[str, str]):
    if subcmd in arg_data_type_converter:
        arg_data_type_cd_item = arg_data_type_converter[subcmd]
        for arg_name, arg_value in arg_dict.items():
            if arg_name in arg_data_type_cd_item:
                arg_dict[arg_name] = convert_data_by_type(  # type: ignore
                    arg_value, arg_data_type_cd_item[arg_name]
                )
    return arg_dict


def convert_data_by_type(arg_value: str, arg_data_type: str):
    """根据类型转变数据
    "bool": "True or False",
    "int": "123",
    "float": "2.3",
    "datetime": "datetime",
    Args:
        arg_value (str): _description_
        arg_data_type (str): _description_
    Returns:
        _type_: _description_
    """
    # print("------ convert_data_by_type:: ", arg_data_type, arg_value)
    if "int" == arg_data_type:
        return int(arg_value)
    if "bool" == arg_data_type:
        return arg_value.lower() in ["false", "0", "no"]
    if "float" == arg_data_type:
        return float(arg_value)
    if "datetime" == arg_data_type:
        return datetime.strptime(arg_value, "%Y-%m-%d %H:%M:%S")
    return arg_value


def strip_equal(longStr):
    tt = longStr.split("=")
    onOff = len(tt) > 1
    return onOff, tt[0]


def arg_filter(subcmd, item):
    # 缺省的arg长度小于等于3
    if len(item) < 4:
        return True
    matched_subcmd_list = _flatten(item[3:])
    return subcmd in matched_subcmd_list


class OptParser(object):
    def __init__(self, flags=[]):
        tmp_flags = []
        tmp_item = []
        self.arg_type_desc_of_subcmd: list[tuple[str, str, str]] = []
        self.multi_line_flags = []
        # 对longStr做下转换
        for item in flags:
            if isinstance(item[1], list):
                sameItem = []
                for v in item[1]:
                    tmp_item = list(copy.deepcopy(item))
                    tmp_item[1] = v
                    sameItem.append(v.split("=")[0])
                    tmp_flags.append(tuple(tmp_item))
                self.multi_line_flags.append([sameItem, _flatten(item[3:])])
            else:
                tmp_flags.append(item)
        self.src_flags = tmp_flags
        self.flags = [
            (item[0][0:1], strip_equal(item[1])[1], item[2]) for item in default_flags
        ] + [
            (
                item[0][0:1] if item[0] else "",
                strip_equal(item[1])[1],
                item[2],
                item[3:],
            )
            for item in tmp_flags
        ]

    def get_mapping_args(self, subcmd: str, src_arg):
        mapping_args = []
        for item in [
            filted_item
            for filted_item in self.multi_line_flags
            if subcmd in filted_item[1]
        ]:
            if item[0][0] == src_arg:
                mapping_args = item[0][1:]
        # log.info(mapping_args)
        # log.info(src_arg)
        # log.info(self.multiLineFlags)
        return mapping_args

    def initcli_invoker(self):
        lists = [item for item in subcmds]
        subcmds.clear()
        return lists

    def set_subcmd(
        self, subcmd: str, arg_type_desc_of_subcmd: list[tuple[str, str, str]]
    ):
        self.subcmd = subcmd
        self.arg_type_desc_of_subcmd = arg_type_desc_of_subcmd
        self.arg_type_desc_of_subcmd_without_equal_colon: list[tuple[str, str, str]] = (
            []
        )
        for arg_definition_tuple in arg_type_desc_of_subcmd:
            self.arg_type_desc_of_subcmd_without_equal_colon.append(
                (
                    arg_definition_tuple[0].replace(":", ""),
                    arg_definition_tuple[1].replace("=", ""),
                    arg_definition_tuple[2],
                )
            )

    def _opts_from_file(self, file):
        dic = {}
        with open(file, "r+", encoding="utf-8") as fo:
            data = yaml.load(fo.read(), Loader=yaml.FullLoader)
            for k, v in data.items():
                long_options = [item[1] for item in self.flags if item[1] == k]
                if long_options:
                    dic[long_options[0]] = v
        return dic, data

    def runtime_flags(self):
        subcmd = self.subcmd
        if not subcmd:
            raise opt.NoArgException(
                "subcmd is not found, please confirm subcmd is set before invoke it"
            )
        return self.arg_type_desc_of_subcmd_without_equal_colon

    def option_mapping(self, option: str):
        """
        短名转换为长名 或者 长名转换为短名
        Known issues: 2024-8-22,第一个长参数必须和函数定义的名字相同,否则输入短名会找不到值,对于其它长参数是带'-'可以被workaround支持
        """

        # IndexError: list index out of range
        # arg_type_desc ('h', 'help', 'print help information')
        match_array = [
            (arg_type_desc[0] if len(option) > 1 else arg_type_desc[1])
            for arg_type_desc in self.runtime_flags()
            if option == arg_type_desc[0] or option == arg_type_desc[1]
        ]
        if len(match_array) == 0:
            log.error(self.runtime_flags())
            log.error(
                option
                + " is not found in option_mapping, please contact admin for the issue"
            )
            return None
        # 跳过所有带'-'的参数,workaround Known issues 2024-8-22
        match_array = [arg_name for arg_name in match_array if "-" not in arg_name]
        return match_array[0]

    def parse_context_if_present(self, opts: dict[str, str]):
        """
        通过它转换用户输入数据到函数调用的参数, 会把短名转换成长名
        短名唯一,长名多个
        Known issues: 2024-8-22,第一个长参数必须和函数定义的名字相同,否则输入短名会找不到值,对于其它长参数是带'-'可以被workaround支持
        """
        # opts, {'name-type': 'aaaa', 'd': ''}
        self.opts = opts
        option_definitions = self.runtime_flags()
        # print(
        #     "------ parse_context_if_present:: option_definitions", option_definitions
        # )
        # self.runtime_flags() [('h', 'help', 'print help information'), ('f', 'file', 'the context file by yaml format'), ('d', 'debug', 'enable/disable debug, boolean type sample', (['install/hello'],)), ('n', 'name', 'foo name, data passed sample', (['install/hello'],)), ('n', 'name-type', 'foo name, data passed sample', (['install/hello'],))]
        for user_input_option in [arg_name for arg_name in opts]:
            toggle_input_option: str = self.option_mapping(user_input_option)
            # print(
            #     "------ parse_context_if_present:: toggle_input_option",
            #     user_input_option,
            #     toggle_input_option,
            # )
            if toggle_input_option:
                opts[toggle_input_option] = opts[user_input_option]
            if len(user_input_option) > 1:
                # 如果用户输入的是长名,需要把所有相同类型的长名都补齐,免除了自定义出来的参数转换的过程
                for short_option, long_option, *other_params in option_definitions:
                    # short_option可能是''
                    if short_option and short_option == toggle_input_option:
                        opts[long_option] = opts[user_input_option]
        file = self.toggle_between_long_and_short_option("f", False)
        data = False
        # log.info(file)
        if file:
            # print("------ parse_context_if_present:: file", file)
            opts2, data = self._opts_from_file(file)
            log.debug(opts2)
            for long_option in opts2:
                short_option = self.option_mapping(long_option)
                if not (long_option in opts or (short_option and short_option in opts)):
                    opts[long_option] = opts2[long_option]
        self.data = data
        return opts

    def toggle_between_long_and_short_option(self, option_name: str, default=None):
        """
        'short_option', 'long_option', 'description', [sub command lists]
        long_option is compulsory, short_option is optional
        """
        dic = self.opts
        subcmd = self.subcmd
        # log.info(f'----{f}')
        # dic, {'name-type': 'aaaa', 'd': '', 'n': 'aaaa', 'debug': ''}
        # log.info(dic)
        # log.info(flags)
        # traceback.print_stack()
        if option_name in dic:
            return dic[option_name]
        for mapping_args in self.get_mapping_args(subcmd, option_name):
            if mapping_args in dic:
                return dic[mapping_args]
        error = False
        if len(option_name) == 1:
            long_option_list = [
                item[1]
                for item in self.arg_type_desc_of_subcmd_without_equal_colon
                if item[0] and item[0] == option_name
            ]
            if long_option_list:
                long_param = long_option_list[0]
                if long_param in dic:
                    return dic[long_param]
            else:
                error = f"the corresponding long option of {option_name} is not in args definition {self.arg_type_desc_of_subcmd}"
        else:
            short_option_list = [
                item[0]
                for item in self.arg_type_desc_of_subcmd_without_equal_colon
                if item[1] == option_name
            ]
            if short_option_list:
                short_param = short_option_list[0]
                if short_param and short_param in dic:
                    return dic[short_param]
            else:
                error = f"the corresponding short option of {option_name} is not in args definition {self.arg_type_desc_of_subcmd}"
        if error:
            raise opt.NoArgException(error + ", please contact admin for the issue")
        if default is not None:
            return default
        item = (
            [
                item1
                for item1 in self.arg_type_desc_of_subcmd_without_equal_colon
                if item1[0] and item1[0] == option_name
            ][0]
            if len(option_name) == 1
            else [
                item1
                for item1 in self.arg_type_desc_of_subcmd_without_equal_colon
                if item1[1] and item1[1] == option_name
            ][0]
        )
        raise opt.NoArgException(
            " ".join(
                [
                    "-" + item[0] + "or" if item[0] else "",
                    "--" + item[1],
                    "is compulsory for",
                    item[2],
                ]
            )
        )

    def bool(self, option_name: str):
        """
        获取参数名相对应的bool值
        """
        return (
            self.toggle_between_long_and_short_option(option_name, False) is not False
        )


def more_subcmd(subcmd: str):
    if "|" not in subcmd:
        return [subcmd]
    if "/" not in subcmd:
        return subcmd.split("|")
    foo = subcmd.split("/")
    return [foo[0] + (("/" + item) if item else "") for item in foo[1].split("|")]


def create_wrapper(lamb: Callable[[OptParser, Callable[..., Any]], Any]):
    """
    这个闭包函数用于完成动态调用命令行的函数
    """

    def wrapper0(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: OptParser):
            arg_dict = args[0]
            if isinstance(arg_dict, dict):
                opp: OptParser = args[1]
                if not opp:
                    raise opt.NoArgException(
                        fn.__name__
                        + " is not inited, please contact admin for the issue"
                    )
                # print("------ create_wrapper:: arg_dict", arg_dict)
                opts = opp.parse_context_if_present(arg_dict)
                # print("------ create_wrapper:: arg_dict", opts)
                log.debug(opts)
                return lamb(opp, fn)
            else:
                return fn(*args)

        return wrapper

    return wrapper0


subcmds: list[str] = []


def __option(opp: OptParser, option: str, bools: list[str]):
    log.debug(option)
    return (
        opp.bool(option)
        if option in bools
        else opp.toggle_between_long_and_short_option(option)
    )


# 函数入口
def __invoke(opp: OptParser, fn: Callable[[], None]):
    bools: list[str] = [
        strip_equal(item[1])[1]
        for item in opp.arg_type_desc_of_subcmd
        if not item[1].endswith("=")
    ]
    spec = inspect.getfullargspec(fn)
    func_argument_default_value_tuple: list = (
        list(spec.defaults) if spec.defaults else []
    )
    func_defined_argument_name_list: list[str] = spec.args
    func_argument_default_value_tuple.reverse()
    func_defined_argument_name_list.reverse()
    arg_dict: dict = {}
    for arg_name, arg_default_value in zip(
        func_defined_argument_name_list, func_argument_default_value_tuple
    ):
        arg_dict[arg_name] = arg_default_value
    func_argument_default_value_tuple.reverse()
    func_defined_argument_name_list.reverse()
    # print("-----", arg_dict, opp.opts)
    # 有bug,这里arg_name可能是短名
    for arg_name, arg_value in opp.opts.items():
        if arg_name in bools:
            arg_dict[arg_name] = True
        else:
            arg_dict[arg_name] = arg_value
    # print(
    #     "------ __invoke:: bools",
    #     bools,
    #     func_argument_default_value_tuple,
    #     func_defined_argument_name_list,
    #     arg_dict,
    # )
    first_has_default_value_argument_index_in_argument_list = len(
        func_defined_argument_name_list
    ) - (
        len(func_argument_default_value_tuple)
        if func_argument_default_value_tuple
        else 0
    )
    # offset = 0
    # func_argument_default_value_tuple = (False, False, True)
    # opp.opts, {'name-type': 'aaaa', 'd': '', 'n': 'aaaa', 'debug': ''}
    # args, ['major', 'minor', 'patch'], 函数的定义参数列表
    # bools = ['config', 'storage', 'tcp', 'hostPath', 'explorer', 'greedy', 'ignore', 'summary', 'major', 'minor', 'patch']
    func_runtime_argument_value_list: list = [
        (
            __option(opp, option, bools)
            if index < first_has_default_value_argument_index_in_argument_list
            or option in opp.opts
            else func_argument_default_value_tuple[
                index - first_has_default_value_argument_index_in_argument_list
            ]
        )
        for index, option in enumerate(func_defined_argument_name_list)
    ]  # type: ignore
    # print(
    #     "------ __invoke:: func_defined_argument_name_list",
    #     first_has_default_value_argument_index_in_argument_list,
    #     func_defined_argument_name_list,
    #     func_runtime_argument_value_list,
    # )
    log.debug(func_defined_argument_name_list)
    log.debug(func_runtime_argument_value_list)
    return fn(*func_runtime_argument_value_list)  # fn(**arg_dict)


def fileter_subcmd(cmd_prefix: str) -> list[str]:
    return [
        subcmd.replace(cmd_prefix, "")
        for subcmd in arg_type_desc_mapping.keys()
        if subcmd.startswith(cmd_prefix)
    ]


def hello_world():
    print("---hello_world")


def cli_invoker(
    subcmd: str,
    arg_type_desc="",
    arggreation=None,
    no_any_cli_handler=None,
    command_is_match_handler=None,
    arg_data_type="",
):
    # print("---cli_invoker", subcmd)
    for sd in more_subcmd(subcmd):
        subcmds.append(sd)
        arg_type_desc_mapping[sd] = arg_type_desc
        if arggreation:
            arggreation_command_options_mapping[sd] = arggreation
        if no_any_cli_handler:
            no_any_cli_handler_mapping[sd] = no_any_cli_handler
        if command_is_match_handler:
            command_is_match_handler_mapping[sd] = command_is_match_handler
        if arg_data_type:
            arg_data_type_dict: dict[str, str] = {}
            for arg_data_type_item in arg_data_type.split(","):
                foo_arr = arg_data_type_item.split("=")
                arg_data_type_dict[foo_arr[0]] = foo_arr[1]
            arg_data_type_converter[sd] = arg_data_type_dict
    # 装饰器只有在函数调用的时候才能生效
    return create_wrapper(__invoke)
