import sys, getopt, re, glob, os, ast
from datetime import datetime
from turtle import clone
import tlog.tlogging as tl
import tio.tfile as tf
from typing import Any, Callable, Tuple, Union, Sized, Literal
from tutils.tstr import split_by_low_upper_break

log = tl.log
BUILT_IN_KEYWORD_LITERAL = Literal[
    "dotenv",
    "vault_id",
    "vault_secret",
    "vault_secret_with_root_token",
    "leadingZeroPadding2",
    "initCap",
    "upper",
    "underline",
    "pythonPackage",
    "space_join",
    "eval",
]
BUILT_IN_KEYWORD_AS_CONSTANT = ["eval"]


def is_list(value: object) -> bool:
    return isinstance(value, list) or isinstance(value, tuple)


def is_dict(value: object) -> bool:
    return isinstance(value, dict)


def is_text(value: Sized) -> bool:
    return is_str(value) and len(value) > 200


def is_str(value: object) -> bool:
    return isinstance(value, str)


def is_bool(value: object) -> bool:
    return isinstance(value, bool)


def flatten_dict(context: dict, parent_key="", sep="."):
    items = []
    for k, v in context.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


"""
2023-09-13T09:59:28.000+0800
"""
REG_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}.+\d{2}:\d{2}:\d{2}")
REG_TIME = re.compile(r"^\d{2}:\d{2}:\d{2}")


def is_datetime(value: object) -> bool:
    if not is_str(value):
        return False
    return REG_DATE_TIME.match(value)  # type: ignore


def is_time(value: str) -> bool:
    if not is_str(value):
        return False
    return REG_TIME.match(value)  # type: ignore


def has_variable(line: str) -> bool:
    return "${" in line


def get_field(context: Union[dict, None], filed_name: str, default_value):
    if filed_name in context:  # type: ignore
        return context[filed_name]  # type: ignore
    elif isinstance(default_value, Exception):
        raise default_value
    return default_value


def find_matching_brace(s: str) -> int:
    brace_level = 0
    i = 0
    while i < len(s):
        if s[i] == "{":
            brace_level += 1
        elif s[i] == "}":
            if brace_level == 0:
                return i  # 找到匹配的最后一个 '}'
            brace_level -= 1
        i += 1
    return -1  # 未找到匹配


def first_variable(line: str, skip_context={}):
    if not isinstance(line, str):
        print("---first_variable line is object", line)
        return None
    index_variable = 0
    # Known Issues: ssz,2025.11.1 存在嵌套的{}的时候需要找出最后一个}
    while index_variable >= 0:
        index_variable = line.find("${", index_variable)
        if index_variable >= 0:
            variable = line[index_variable + 2 : len(line)]
            variable = variable[0 : find_matching_brace(variable)]
            if variable not in skip_context:
                return variable
            else:
                index_variable += 3 + len(variable)
    return None


def __has_reference(value: str) -> bool:
    return value.startswith("::reference ")


def __load_reference(line: str, value: str):
    reference = value[len("::reference ") :]
    return reference


def __has_include(value: str) -> bool:
    return value.startswith("::include ")


def __load_include_file(prefix: str, value: str) -> str:
    file = value if isinstance(value, list) else value[len("::include ") :]
    included_lines = (
        file
        if isinstance(file, list)
        else tf.readlines(file, allowEmpty=True, allowStrip=False)
    )
    return "".join([(prefix + line) for line in included_lines])


def merge_design_runtime(
    design_context: dict, runtime_context: dict, path: str
) -> Union[dict, None]:
    if not runtime_context:
        log.error(f"runtime_context is None for {path}")
    runtime_context_value = (
        load_item(runtime_context, path) if runtime_context else None
    )
    return (
        runtime_context_value
        if runtime_context_value
        else load_item(design_context, path)
    )


def load_item_support_dot(
    build_mapping: Union[dict, None], path: str
) -> Union[dict, None]:
    # 同时支持., /作为分割符号(yaml path 插件中用.作为分隔符号)
    return load_item(build_mapping, replace_all(path, ".", "/"))


def load_item(build_mapping: Union[dict, None], path: str) -> Union[dict, None]:
    if not build_mapping and tl.PRINT_DETAILS:
        log.error(f"buildMapping is None for {path}, please check it")
        return None
    k0 = path[0 : path.find("/")] if "/" in path else path
    k1 = path[(path.find("/") + 1) : len(path)] if "/" in path else None
    if k1:
        return load_item(build_mapping[k0], k1) if k0 in build_mapping else None  # type: ignore
    else:
        return build_mapping[k0] if k0 in build_mapping else None  # type: ignore


def __replace_object_item(
    context: dict, config: object, key_item: str, key_value: object
):
    if __is_replacable(key_value):
        replace_object(context, key_value)
    elif is_str(key_value):
        config[key_item] = replace_by_context(context, key_value)  # type: ignore


def replace_all(line: str, target: str, replacement: str):
    while line.find(target) > -1:
        line = line.replace(target, replacement)
    return line


def replace_object(context: dict, config: object) -> bool:
    """
    替换一个对象中所有的变量, 注意config里的内容会被替换掉
    """
    if is_dict(config):
        for key_item, key_value in config.items():  # type: ignore
            __replace_object_item(context, config, key_item, key_value)
    elif is_list(config):
        for key_item, key_value in enumerate(config):  # type: ignore
            __replace_object_item(context, config, key_item, key_value)  # type: ignore
    return True


def replace_by_context_is_debug_handler(line: str):
    return '[${list::COMPONENT}<list::>{"name":"${COMPONENT}"}</list::>]' == line


def replace_by_context(
    context: dict, line: str, replace_callback=None, max_replace_num=10
):
    """
    the followings 3 variable type is support
    ${variable}, list means that read lines from list
    ${::include file}, variable from context, str means that read lines from file, list means that read lines from list
    ::reference varaible, varaible from context
    对于部分的list替换的变量名称必须要以list::开头,例如list:SIU_LIB
    known issues: 2024-08-21, 有block section的模板内容不能放在多个行内,必须在一个line里,如果是多行模板可以用\n来表示换行
    """

    # 如果第一个变量没有被替换，此时会循环n次啥也不替换, 所以用skip_context来workaround
    def __replace_variable(line0: str, variable: str, variable_value: str):
        return line0.replace(f"${{{variable}}}", variable_value)

    skip_context = {}
    if isinstance(line, str):
        line = SectionReplacementReactor.replace(context=context, section=line)

    while context and max_replace_num > 0:
        max_replace_num = max_replace_num - 1
        variable = first_variable(line, skip_context)
        if not variable:
            break
        if variable in context:
            value = context[variable]
            if is_list_replace(variable):
                line = replace_by_context_for_list(line, variable, value, context)
            elif (
                isinstance(value, str)
                and __has_include(value)
                or isinstance(value, list)
            ):
                line = __load_include_file(line[0 : line.find("$")], value)  # type: ignore
            elif isinstance(value, str) and __has_reference(value):
                line = __replace_variable(line, variable, __load_reference(line, value))
            else:
                line = __replace_variable(line, variable, str(value))
        else:
            if is_built_in_replace(variable):
                # if replace_by_context_is_debug_handler(line):
                #     print("---replace_by_context", line)
                line = __replace_variable(
                    line,
                    variable,
                    replace_by_context_get_variable_value_built_in(
                        variable=variable, context=context
                    ),
                )
            else:
                skip_context[variable] = 1
    return line


CONTEXT_LIST_SCHEMA = "list::"
CONTEXT_BUILT_IN_SCHEMA = "::"
CONTEXT_LIST_SPLIT = "LIST_SPLIT"
CONTEXT_LIST_OBJECT = "LIST_OBJECT"


def is_list_replace(varaible: str):
    return varaible.startswith(CONTEXT_LIST_SCHEMA)


def is_built_in_replace(varaible: str):
    return not is_list_replace(varaible) and varaible.find(CONTEXT_BUILT_IN_SCHEMA) > 0


def remove_content_in_keyword_pair(line: str, keyword: str):
    """
    删除在保留关键字对里的内容
    如果line是个文件名,等效于直接返回,不处理
    """
    results: list[str] = []
    toggle_int = 0
    while (keyword_index := line.find(keyword)) >= 0:
        if toggle_int % 2 == 0:
            previous_line = line[:keyword_index]
            results.append(previous_line[: previous_line.rindex("\n")])
        line = line[line.index("\n", keyword_index) :]
        toggle_int += 1
    results.append(line)
    return "".join(results)


__COND = "__COND"


def get_condition_flags(context: dict[str, Any]):
    return [context_flag for context_flag in context.keys() if context_flag.startswith(__COND)]  # type: ignore


def skip_conditions_in_section(context: dict[str, Any], line: str):
    """
    删除在保留关键字对里的内容
    如果line是个文件名,等效于直接返回,不处理
    如果context没有__COND开头的变量,模板不做任何改变
    如果context包含__COND开头的变量,只保留相应__COND${}的区块,其它都删除
    """
    condition_flags: list[str] = get_condition_flags(context)
    if len(condition_flags) == 0:
        return line
    for condition in condition_flags:
        if condition in context:
            line = re.compile(f"::{condition}.*\n").sub("", line)
    line = remove_content_in_keyword_pair(line, f"::{__COND}")
    return line


class ListReplacementReactor:
    BEGIN = f"${{{CONTEXT_LIST_SCHEMA}"
    END = f"</{CONTEXT_LIST_SCHEMA}>"

    @staticmethod
    def find_list_end_position(last_str: str, list_end_point: int):
        last_end_point = list_end_point
        depth = 0
        count = 0
        while (
            list_end_point := last_str.find(
                ListReplacementReactor.END, list_end_point + 5
            )
        ) > -1:
            depth += 1
            count += 1
            if count > 10:
                raise Exception(
                    f"not support count={count},list_end_point={list_end_point}"
                )
            content_part = last_str[last_end_point:list_end_point]
            last_end_point = list_end_point
            if content_part.find(ListReplacementReactor.BEGIN) > -1:
                depth -= 1
            if depth == 1:
                return list_end_point
        return list_end_point


RE_EMPTY_STR = re.compile(r"^\s+$")
"""
line template: ${list::JAR}<list::>abc${JAR}</list::>
对于部分的list替换的变量名称必须要以list::开头,例如list:SIU_LIB,否则会把本line替换N次
"""


def replace_by_context_for_list(line: str, variable: str, value: list, context: dict):
    # print("---replace_by_context_for_list", variable, line)
    list_point = line.find(f"${{{variable}}}<{CONTEXT_LIST_SCHEMA}>")
    if list_point < 0:
        log.error(f"<{CONTEXT_LIST_SCHEMA}> is not found in template")
        return line
    # depth,init_list_point = ListReplacementReactor.find_list_begin_depth(line, list_point + 5)
    previous_str = line[0:list_point]
    last_str = line[list_point:]
    last_str = last_str[
        last_str.find(f"<{CONTEXT_LIST_SCHEMA}>") + len(CONTEXT_LIST_SCHEMA) + 2 :
    ]
    list_end_point = ListReplacementReactor.find_list_end_position(last_str, 0)
    if list_end_point < 0:
        # print('---',depth, previous_str)
        log.error(
            f"</{CONTEXT_LIST_SCHEMA}> is not found in template,variable={variable}"
        )
        return line
    # 在template.yaml里定义的模板
    replace_template = last_str[0:list_end_point]
    # 需要考虑区块替换要占用一个回车
    if (
        replace_template[0] == "\n"
        and replace_template[len(replace_template) - 1] == "\n"
        and (not replace_template.endswith(f"{SectionReplacementReactorItem.END}\n"))
    ):
        replace_template = replace_template[0 : len(replace_template) - 1]

    last_str = last_str[list_end_point + len(CONTEXT_LIST_SCHEMA) + 3 :]
    cloned_context = deep_merge(context, {})
    previous_str_trans_line_index = previous_str.rfind("\n")
    previous_str_trans_line_before = previous_str
    previous_str_trans_line_after = ""
    if previous_str_trans_line_index >= 0:
        previous_str_trans_line_before = previous_str[
            0 : previous_str_trans_line_index + 1
        ]
        previous_str_trans_line_after = previous_str[
            previous_str_trans_line_index + 1 :
        ]
        if not RE_EMPTY_STR.match(previous_str_trans_line_after):
            previous_str_trans_line_before = previous_str
            previous_str_trans_line_after = ""
    # print('==',len(previous_str_trans_line_after),previous_str_trans_line_index)
    output_lines: list[str] = [previous_str_trans_line_before]
    list_split_str = replace_by_context_for_list_get_list_split_str_handler(
        context, variable, value
    )
    list_index = 0
    for list_value in value:
        output_lines.append(previous_str_trans_line_after)
        if is_dict(list_value):
            cloned_context = deep_merge(context, list_value)
        else:
            inner_variable = variable[variable.find("::") + 2 :]
            cloned_context[inner_variable] = list_value
        replaced_str = replace_by_context(
            cloned_context, skip_conditions_in_section(cloned_context, replace_template)
        )
        if (
            replaced_str
            and replaced_str[0] == "\n"
            and replaced_str[len(replaced_str) - 1] == "\n"
        ):
            replaced_str = replaced_str[0 : len(replaced_str) - 1]
        output_lines.append(
            replaced_str
            if list_index == len(value) - 1
            else f"{replaced_str}{list_split_str}"
        )
        list_index += 1
    # 动态调整引入的2种回车的情况,注:不会同时存在
    if len(value) > 0:
        first_line = output_lines[2]
        if (
            first_line[0] == "\n"
            and previous_str_trans_line_before
            and previous_str_trans_line_before[len(previous_str_trans_line_before) - 1]
            == "\n"
        ):
            output_lines[2] = first_line[1:]
        last_line = output_lines[len(output_lines) - 1]
        if (
            last_line
            and last_line[len(last_line) - 1] == "\n"
            and last_str
            and last_str[0] == "\n"
        ):
            last_str = last_str[1:]
    output_lines.append(last_str)
    result = "".join(output_lines)
    # print("---replace_by_context_for_list", variable, result)
    # Known Issues: ssz,2025.10.25 support to convert result to object
    return (
        ast.literal_eval(result)
        if replace_by_context_for_list_has_convert_to_object_handler(context, variable)
        else result
    )


def replace_by_context_for_list_get_list_split_str_handler(
    context: dict, variable: str, output_lines: list[str]
):
    list_split_variable = (
        f'{CONTEXT_LIST_SPLIT}_{variable.replace(CONTEXT_LIST_SCHEMA, "")}'
    )
    # print(
    #     "---replace_by_context_for_list_get_list_split_str_handler",
    #     list_split_variable,
    #     output_lines,
    # )
    return context[list_split_variable] if list_split_variable in context else ""


def replace_by_context_for_list_has_convert_to_object_handler(
    context: dict, variable: str
):
    list_convert_to_object_variable = (
        f'{CONTEXT_LIST_OBJECT}_{variable.replace(CONTEXT_LIST_SCHEMA, "")}'
    )
    return (
        list_convert_to_object_variable in context
        and context[list_convert_to_object_variable]
    )


def replace_by_context_get_variable_value_built_in(
    variable: str, context: dict, latest_built_in_keyword=""
):
    """
    替换::开始的block section
    known issues: 如果变量没有被定义在context,但它出现在block section里,那所有的raw block section都会出现在代码里,主要是为了兼容'${}'的原始内容
    """

    def constant_or_variable():
        if latest_built_in_keyword in BUILT_IN_KEYWORD_AS_CONSTANT:
            return variable
        # Known issues: ssz,2025.10.11, 用引号括起来表示常量
        if "'" in variable or '"' in variable:
            return variable.replace("'", "").replace('"', "")
        return f"${{{variable}}}"

    build_in_pos = variable.find(CONTEXT_BUILT_IN_SCHEMA)
    if build_in_pos < 0:
        # if variable not in context: raise BaseException(f'variable[{variable}] is not defined in context')
        # 如果找不到就认为是个常量,可用于表达式eval
        return get_field(context, variable, constant_or_variable())
    built_in_keyword = variable[:build_in_pos]
    remainder = variable[build_in_pos + len(CONTEXT_BUILT_IN_SCHEMA) :]
    # try:
    # 有时候会误判导致没有进入list,就先进入这里，然后context就会没有值,此时需要直接返回源字符串
    return replace_by_context_get_built_in(
        built_in_keyword,  # type: ignore
        context,
        replace_by_context_get_variable_value_built_in(
            variable=remainder,
            context=context,
            latest_built_in_keyword=built_in_keyword,
        ),
    )
    # except BaseException as error:
    #     print(error)
    #     return f'${{{variable}}}'


def replace_by_context_get_built_in(
    built_in_keyword: BUILT_IN_KEYWORD_LITERAL, context: dict, value: str
):
    # eval函数中使用
    def variable_if_present(variable_name, default_variable_name):
        runtime_variable_name = variable_name or default_variable_name
        return f"${{{runtime_variable_name}}}"

    if "dotenv" == built_in_keyword:
        # print("---replace_by_context_get_built_in dotenv", value)
        return (
            "${dotenv::" + f"{value[2:]}" if has_variable(value) else tf.dotenv(value)
        )
    if "vault_id" == built_in_keyword:
        from tutils.tvault_api import vault_id

        return (
            "${vault_id::" + f"{value[2:]}" if has_variable(value) else vault_id(value)
        )
    if "vault_secret_with_root_token" == built_in_keyword:
        from tutils.tvault_api import vault_secret_with_root_token

        # print("---replace_by_context_get_built_in vault", value)
        return (
            "${vault_secret_with_root_token::" + f"{value[2:]}"
            if has_variable(value)
            else vault_secret_with_root_token(value)
        )
    if "vault_secret" == built_in_keyword:
        from tutils.tvault_api import vault_secret

        # print("---replace_by_context_get_built_in vault", value)
        return (
            "${vault_secret::" + f"{value[2:]}"
            if has_variable(value)
            else vault_secret(value)
        )
    if "leadingZeroPadding2" == built_in_keyword:
        return f"0{value}" if len(value) == 1 else value
    if "initCap" == built_in_keyword:
        return value.upper() if len(value) == 1 else f"{value[0].upper()}{value[1:]}"
    if "upper" == built_in_keyword:
        return value.upper()
    if "underline" == built_in_keyword:
        return "_".join(split_by_low_upper_break(value))
    if "pythonPackage" == built_in_keyword:
        # print("---replace_by_context_get_built_in", value)
        return value.replace("-", "_")
    if "space_join" == built_in_keyword:
        return " ".join(split_by_low_upper_break(value))
    if "eval" == built_in_keyword:
        return eval(value, {**context, "variable_if_present": variable_if_present})
    return unknown_embed_function(built_in_keyword, value)


def unknown_embed_function_built_in_folder_name(folder_name_pattern):
    return sorted(
        glob.glob(f"{folder_name_pattern}"), key=os.path.getmtime, reverse=True
    )[0]


def unknown_embed_function(built_in_keyword: str, value: str, globals={}):
    # print("---unknown embed function", built_in_keyword, value)
    globals_context = {**globals}
    globals_context["built_in_folder_name"] = (
        unknown_embed_function_built_in_folder_name
    )
    replaced_script = built_in_keyword.replace("###", value)
    source_scripts = f"""
import sys, re, os, platform,socket
import tutils.thpe as thpe
import tutils.tstr as tstr
import tutils.tvault_api as tvault
import tlog.tlogging as tl
import tio.tfile as tf
try:
    __result = {replaced_script}
except Exception as e:
    import traceback
    print(traceback.format_exc())
    #pass
    """
    locals = {}
    # Known issues: ssz,2025.10.5, linux 3.9.6报错 exec(compiled, globals=globals_context, locals=locals), TypeError: exec() takes no keyword arguments
    compiled = compile(source_scripts, filename="<dynamic-script>", mode="exec")
    exec(compiled, globals_context, locals)
    if "__result" in locals:
        return locals["__result"]
    return value


def replace(replace_callback: Callable[..., Any], line: str) -> str:
    if has_variable(line):
        variable: str = first_variable(line)  # type: ignore
        line = line.replace("${" + variable + "}", str(replace_callback(variable)))
    return line


def __is_replacable(config: object) -> bool:
    return is_dict(config) or is_list(config)


def __is_extensible(base: object, extend: object) -> bool:
    return (is_dict(base) and is_dict(extend)) or (is_list(base) and is_list(extend))


def deep_merge_dict_no_check(base: dict, extend: dict) -> dict:
    result = {**base, **extend}
    for attribute in result.keys():
        if (
            attribute in base
            and attribute in extend
            and __is_extensible(base[attribute], extend[attribute])
        ):
            result[attribute] = deep_merge(base[attribute], extend[attribute])
    return result


"""
    simple implement to use constant list, good solutions is key_provider
    if want to use key provider, please ensure name or path exist in dict
    lookup proirity is name and path
"""


def key_provider_in_dict(dict_0: dict):
    for key in ["name", "path"]:
        if key in dict_0:
            return key
    return None


def deep_merge_list_no_check(base: list, extend: list) -> list:
    if (
        len(base) > 0
        and len(extend) > 0
        and is_dict(base[0])
        and key_provider_in_dict(base[0])
    ):
        unique_attr_name = key_provider_in_dict(base[0])
        base_dict = {}
        for tmp_item in base:
            base_dict[tmp_item[unique_attr_name]] = tmp_item
        extend_dict = {}
        for tmp_item in extend:
            extend_dict[tmp_item[unique_attr_name]] = tmp_item
        result_tmp = deep_merge_dict_no_check(base_dict, extend_dict)
        return [result_tmp[name] for name in result_tmp.keys()]
    else:
        # simple implement to use extend replace base for list, consider that list merge/append/sort in future
        return extend


def deep_merge(base: object, extend: object) -> Any:
    """
    深拷贝合并2个对象,返回一个新对象,会用extend里的key覆盖base
    """
    if not __is_extensible(base, extend):
        log.error("deep merge argument[base]" + str(is_dict(base)) + str(base))
        log.error("deep merge argument[extend]" + str(type(extend)) + str(extend))
        raise TypeError(
            f"base, extend shoule be list or dict both, but base={base},extend={extend}"
        )
    if is_dict(base):
        return deep_merge_dict_no_check(base, extend)  # type: ignore
    else:
        return deep_merge_list_no_check(base, extend)  # type: ignore


"""
allow_escape_char = True, 否者 \\n, \\t不能被替换为规避字符
"""


def write_to_file_with_replace(
    target_file: str,
    lines,
    context: dict,
    auto_crlf: bool = False,
    allow_escape_char=False,
    skip_write_file=False,
):
    """
    known issues: 2024-08-21, 有block section的模板内容不能放在多个行内,必须在一个line里,如果是多行模板可以用\n来表示换行,所以block section不能拆分放在lines里
    """
    # tf.backup(target_file)
    newline = "" if auto_crlf else None
    write_lines: list[str] = []

    def __escape_write_lines(line0: str):
        if line0.endswith("\n"):
            write_lines.append(line0)
        else:
            write_lines.append(line0 + "\n")

    if isinstance(lines, str):
        lines = [lines]
    for line in lines:
        line = replace_by_context(context, line, max_replace_num=100)
        if isinstance(line, list):
            for sub_line in line:
                __escape_write_lines(sub_line)
                log.debug(str(line))
        else:
            if allow_escape_char:
                line = line.replace("\\\\n", "\n").replace("\\\\t", "\t")
            __escape_write_lines(line)
            log.debug(line)
    if not skip_write_file:
        with open(target_file, "w", newline=newline, encoding="utf-8") as fw:
            log.info("save to " + target_file)
            for line in write_lines:
                fw.write(line)
    return write_lines


"""
'ab c\n::{if VAR=="11"\ndd\n::}\nb cd'
"""


class SectionReplacementReactorItem:
    SECTION_FLAG = "::"
    BEGIN = "::{"
    ELIF = "::}elif{"
    ELSE = "::}else{"
    END = "::}"

    def __init__(
        self,
        section: str,
        leading: str,
        instruction: str,
        expression: str,
        content: str,
        guard: str,
    ) -> None:
        self.__section = section
        # ab c
        self.__leading = leading
        # if,跟一个{
        self.__instruction = instruction
        # VAR=="11", 以\n结尾
        self.__expression = expression
        # dd
        self.__content = content
        # \nb cd
        self.__guard = guard

    def get_leading(self):
        return self.__leading

    def get_instruction(self):
        return self.__instruction

    def get_expression(self):
        return self.__expression

    def get_content(self):
        return self.__content

    def get_guard(self):
        return self.__guard

    @staticmethod
    def find(section: str, keyword: str, start=0):
        start_pos = section.find(keyword, start)
        if start_pos > -1 and (end_line_pos := section.find("\n", start_pos)) > -1:
            return start_pos, end_line_pos
        return False, False

    @staticmethod
    def find_begin(section: str, start=0, depth=0):
        start_pos, end_line_pos = SectionReplacementReactorItem.find(
            section, SectionReplacementReactorItem.BEGIN, start
        )
        if end_line_pos:
            start_pos1, end_line_pos1, depth = SectionReplacementReactorItem.find_begin(
                section, end_line_pos, depth + 1
            )
        return start_pos, end_line_pos, depth

    @staticmethod
    def find_end(section: str, start: int, depth: int):
        start_pos, end_line_pos = SectionReplacementReactorItem.find(
            section, SectionReplacementReactorItem.END, start
        )
        if end_line_pos:
            depth -= 1
            if depth > 0:
                (
                    start_pos1,
                    end_line_pos1,
                    depth,
                ) = SectionReplacementReactorItem.find_end(section, end_line_pos, depth)
        return start_pos, end_line_pos, depth

    @staticmethod
    def has_section(section: str):
        start_pos, end_line_pos, depth = SectionReplacementReactorItem.find_begin(
            section
        )
        if end_line_pos:
            start_pos1, end_line_pos1, depth = SectionReplacementReactorItem.find_end(
                section, end_line_pos, depth
            )
            if end_line_pos1:
                return start_pos, end_line_pos, start_pos1, end_line_pos1
        # print('========', section)
        return False, False, False, False

    @staticmethod
    def parse(section: str):
        (
            start_pos,
            end_line_pos,
            start_pos1,
            end_line_pos1,
        ) = SectionReplacementReactorItem.has_section(section)
        # print(start_pos, end_line_pos, start_pos1, end_line_pos1)
        if end_line_pos:
            leading_part = section[:start_pos]
            content_part = section[end_line_pos + 1 : start_pos1]
            guard_part = section[end_line_pos1 + 1 :]
            expression_parts = section[start_pos:end_line_pos].split("{")
            if len(expression_parts) > 2:
                expression_parts = expression_parts[len(expression_parts) - 2 :]
            expression_parts1 = section[start_pos1 : end_line_pos1 + 1]
            # else{ or elif{
            if expression_parts1.find("{") > 0:
                # 保留::
                guard_part = f'{expression_parts1.replace("}", "{")}{guard_part}'
            expression_part = expression_parts[1]
            instruction_part = (
                expression_parts[0]
                .replace(SectionReplacementReactorItem.END, "")
                .replace(SectionReplacementReactorItem.SECTION_FLAG, "")
            )
            # print('---- expression_parts', expression_parts )
            # print('---- leading_part', leading_part )
            # print('---- instruction_part', instruction_part )
            # print('---- expression_part', expression_part )
            # print('---- content_part', content_part )
            # print('---- guard_part', guard_part )
            return SectionReplacementReactorItem(
                section=section,
                leading=leading_part,
                instruction=instruction_part,
                expression=expression_part,
                content=content_part,
                guard=guard_part,
            )


class SectionReplacementReactor:
    def __init__(self) -> None:
        pass

    @staticmethod
    def has_name_error(context: dict[str, Any], expression: str):
        try:
            expression and eval(expression, context)  # type: ignore
            return False
        except NameError:
            return True

    @staticmethod  # eval可能会返回None, 会影响判断,从而没有一个条件能满足,此时我们严格要求是True或False
    def eval(expression: str, context: dict[str, Any]):
        return True if eval(expression, context) else False

    @staticmethod
    def get_expression_value(
        context: dict[str, Any], expression: str, expression_value=None
    ):
        # 未开始条件
        if expression_value == None:
            return (
                SectionReplacementReactor.eval(expression, context)
                if expression
                else False
            )
        else:
            # 上次是False
            if not expression_value:
                return (
                    SectionReplacementReactor.eval(expression, context)
                    if expression
                    else True
                )
            # 上次是True,接下来都是False
            else:
                return False

    @staticmethod
    def replace(context: dict[str, Any], section: str, expression_value=None):
        section_item: SectionReplacementReactorItem = (
            SectionReplacementReactorItem.parse(section)
        )  # type: ignore
        if section_item and not SectionReplacementReactor.has_name_error(
            context, section_item.get_expression()
        ):
            instruction = section_item.get_instruction()
            if not instruction:
                expression_value = None
            expression = section_item.get_expression()
            # last_expression_value = expression_value
            expression_value = SectionReplacementReactor.get_expression_value(
                context, expression, expression_value
            )
            content = (
                SectionReplacementReactor.replace(context, section_item.get_content())
                if expression_value
                else ""
            )
            # if 'CLASS_NAME' in context and context['CLASS_NAME'] == 'ReservationBatteryModel':
            # print('--------', f'"{expression}"', f"{last_expression_value}->{expression_value}", section_item.get_instruction(), section_item.get_content(), content)
            return f"{section_item.get_leading()}{content}{SectionReplacementReactor.replace(context, section_item.get_guard(), expression_value)}"
        return section
