import yaml
import glob
import sys, re, os
import tempfile
import tlog.tlogging as tl
import tio.tfile as tf
import tutils.context_opt as tcontext
import tutils.tworkaround as tworkaround
import tutils.tgitlab_api as tgitlab_api
from typing import Union

log = tl.log

FILE_BEGIN_KEYWORD = "::FILE_BEGIN"
FILE_MIDDLE_KEYWORD = "::FILE_MIDDLE"
FILE_END_KEYWORD = "::FILE_END"
TEMPLATE_KEYWORD_TEMPLATE_FILE = "${::TEMPLATE_FILE}="
UPDATE_KEYWORD_APPEND_KEYWORD = "appendKeyword"
UPDATE_KEYWORD_KEYWORD = "keyword"
UPDATE_KEYWORD_KEYWORD2 = "keyword2"
UPDATE_KEYWORD_KEYWORD_BLOCK_BEGIN = "keywordBlockBegin"
UPDATE_KEYWORD_KEYWORD_BLOCK_END = "keywordBlockEnd"
UPDATE_KEYWORD_DEPENDENCY = "dependency"
UPDATE_KEYWORD_BEFORE = "before"
UPDATE_KEYWORD_AFTER = "after"
UPDATE_KEYWORD_DELETE = "delete"
UPDATE_KEYWORD_UPDATE = "update"
UPDATE_KEYWORD_PART = "part"
UPDATE_KEYWORD_MULTIPLE = "multiple"
UPDATE_KEYWORD_NINDENT = "nindent"
UPDATE_KEYWORD_NO_RELATIVE = "noRelative"
UPDATE_KEYWORD_BLOCK = "block"
UPDATE_KEYWORD_TEMPLATE = "template"
ALLOW_KEYWORD: dict[str, list[str]] = {
    UPDATE_KEYWORD_KEYWORD: [
        FILE_BEGIN_KEYWORD,
        FILE_MIDDLE_KEYWORD,
        FILE_END_KEYWORD,
        "*",
    ],
    UPDATE_KEYWORD_KEYWORD2: ["*"],
    UPDATE_KEYWORD_APPEND_KEYWORD: ["*"],
    UPDATE_KEYWORD_DEPENDENCY: [
        "*"
    ],  # 与keyword是And关系,多个dependency是Or关系,只要有一个存在context就可以,值可以是str(一个) or list[str],存在依赖就满足
    UPDATE_KEYWORD_BEFORE: ["*"],  # direction, operation向前替换
    UPDATE_KEYWORD_AFTER: ["*"],  # 缺省direction, operation向下替换
    UPDATE_KEYWORD_DELETE: ["*"],  # operation删除本行
    UPDATE_KEYWORD_UPDATE: ["*"],  # operation替换本行
    UPDATE_KEYWORD_PART: [
        "*"
    ],  # operation替换本行部分内容,主要应用场景为替换k8s registry保持其它路径不变
    UPDATE_KEYWORD_MULTIPLE: [
        "*"
    ],  # 允许匹配多次, 缺省只匹配一次,主要应用场景为多个相同的地方需要operation
    UPDATE_KEYWORD_NO_RELATIVE: [
        "*"
    ],  # 返回的结果是否需要加相对部分,默认要加,可以设置任意值取消
    UPDATE_KEYWORD_NINDENT: [
        "2"
    ],  # 在relative的基础上返回的结果加2个空格,已匹配文档(yaml)
    UPDATE_KEYWORD_BLOCK: [
        "2"
    ],  # keyword是一个块,表示需要匹配连续2行,关键字为keyword{n}
    UPDATE_KEYWORD_KEYWORD_BLOCK_BEGIN: [
        "2"
    ],  # keywordBlockEnd是一个块,从keywordBlockBegin开始到它结束,中间的行都会被自动skip,然后替换成template的内容
    UPDATE_KEYWORD_KEYWORD_BLOCK_END: [
        "2"
    ],  # keywordBlockEnd是一个块,从keyword开始到它结束,中间的行都会被自动skip,然后替换成template的内容
    UPDATE_KEYWORD_TEMPLATE: [
        TEMPLATE_KEYWORD_TEMPLATE_FILE,
        "*",
    ],  # 替换后的模板,如果多行用'|'开始
}
NEW_KEYWORD_NEW = "new"
NEW_KEYWORD_COPY = "copy"
NEW_KEYWORD_FILES = "files"
NEW_KEYWORD_EXISTS_SKIP = "exists_skip"
NEW_KEYWORD_RM_SKIP = "rm_skip"
NEW_OPERATION_FILES: dict[str, set[str]] = {}


def print_files_not_in_new_operation_files(*extensions):
    for folder, files in NEW_OPERATION_FILES.items():
        files_with_extension = []
        if len(extensions) > 0:
            for extension in extensions:
                files_with_extension += glob.glob(
                    os.path.join(folder, f"*.{extension}")
                )
        else:
            files_with_extension = os.listdir(folder)
        for file in files_with_extension:
            abs_file = os.path.join(folder, file)
            if os.path.isdir(abs_file):
                continue
            if abs_file not in files:
                print(f"rm {abs_file}")


def __get_operation_in_line_templates(line_template):
    if UPDATE_KEYWORD_BEFORE in line_template:
        return UPDATE_KEYWORD_BEFORE
    if UPDATE_KEYWORD_UPDATE in line_template:
        return UPDATE_KEYWORD_UPDATE
    if UPDATE_KEYWORD_DELETE in line_template:
        return UPDATE_KEYWORD_DELETE
    return UPDATE_KEYWORD_AFTER


def __get_template_text(line_template):
    return __get_template_text_by_string(line_template[UPDATE_KEYWORD_TEMPLATE])


def __get_template_text_by_string(line_template_str: str):
    """
    返回模板文本内容,它可以解析,比如TEMPLATE_FILE它会读取真实的内容
    line_template_str: 模板定义的内容
    """
    template_context = line_template_str
    if TEMPLATE_KEYWORD_TEMPLATE_FILE in template_context:
        template_tmp_lines: list[str] = []
        for template_line in template_context.splitlines():
            if TEMPLATE_KEYWORD_TEMPLATE_FILE in template_line:
                template_file_lines = []
                prefix_value = __get_relative_prefix_value(template_line)
                template_file = template_line[
                    len(TEMPLATE_KEYWORD_TEMPLATE_FILE) + len(prefix_value) :
                ]
                # 如果是二进制的文件,只需要返回文件名,而且只支持一个文件名
                if tf.is_binary_file(template_file):
                    return template_file
                for template_file_line in tf.readlines(template_file, allowStrip=False):
                    template_file_lines.append(f"{prefix_value}{template_file_line}")
                template_tmp_lines.append("".join(template_file_lines))
            else:
                template_tmp_lines.append(template_line)
        template_context = "\n".join(template_tmp_lines)
    return template_context


def __get_line_templates_by_keyword(last_line, line, line2, values, file_position_flag):
    line_templates: list[dict] = []
    if not values:
        return line_templates

    def ____keyword_match(line_template, line, line2):
        if line_template[UPDATE_KEYWORD_KEYWORD] == file_position_flag:
            return True
        if line_template[UPDATE_KEYWORD_KEYWORD] not in line:
            return False
        if (
            UPDATE_KEYWORD_KEYWORD2 in line_template
            and line_template[UPDATE_KEYWORD_KEYWORD2] not in line2
        ):
            return False
        return True

    for line_template in values:
        if ____keyword_match(line_template, line, line2):
            line_templates.append(line_template)
            # please don't remove in here, otherwise num is error
            # values.remove(line_template)
    # 这里控制line template只被执行一次,除非有multiple
    if len(line_templates) > 0:
        for line_template in line_templates:
            if UPDATE_KEYWORD_MULTIPLE not in line_template:
                values.remove(line_template)
    return line_templates


def __get_relative_prefix_value(line, no_relative=False):
    prefix_value = ""
    for index in range(0, len(line)):
        if not (line[index] == " " or line[index] == "\t"):
            prefix_value = "" if no_relative else line[0:index]
            break
    return prefix_value


def __k8s_helm_chart_create_process_template(context, line, line_template):
    prefix_value = __get_relative_prefix_value(
        line, UPDATE_KEYWORD_NO_RELATIVE in line_template
    )
    if UPDATE_KEYWORD_NINDENT in line_template:
        for i in range(line_template[UPDATE_KEYWORD_NINDENT]):
            prefix_value += " "
    lines = []
    replaced_lines = tcontext.replace_by_context(
        context, __get_template_text(line_template), max_replace_num=100
    ).split("\n")
    for line_index in range(0, len(replaced_lines)):
        line = replaced_lines[line_index]
        if line_index == (len(replaced_lines) - 1) and not line:
            continue
        lines.append(prefix_value + line)
    log.debug("want to replaced lines len:" + str(len(lines)))
    return lines
    # return '\n'.join(lines)  + '\n'


"""
name is mandatory in context

"""


def file_replace_and_persist(context, item_definitions, target_files):
    if not os.path.exists(target_files):
        return
    # 这里要预先处理下keyword里的变量替换,要不然肯定找不到
    # values, 是所有模板的集合
    values = []
    for template_definition in item_definitions:
        cloned_template_definition = tcontext.deep_merge(template_definition, {})
        values.append(cloned_template_definition)
        if UPDATE_KEYWORD_KEYWORD in cloned_template_definition:
            cloned_template_definition[UPDATE_KEYWORD_KEYWORD] = (
                tcontext.replace_by_context(
                    context, cloned_template_definition[UPDATE_KEYWORD_KEYWORD]
                )
            )
    lines = []
    last_line = ""
    last_update_line = ""

    def ____template_to_string(template_lines):
        return "\n".join(template_lines) + "\n"

    """
        如果替换后的代码刚好和前面行的最后一行一样, 就不会替换了
        可以用删除before: true, 再去find </classpathentry>来workaround
    """

    def ____template_replaced_in_line(
        line: str,
        last_update_line: list[str],
        line_templates: list[dict],
        src_file_lines: list[str],
        line_index: int,
    ):
        log.debug("keyword line:" + line)
        log.debug("want to replace:" + str(last_update_line))
        if not last_update_line:
            return False
        scope = ""
        last_line_template = {}
        for line_template in line_templates:
            last_line_template = line_template
            foo_scope = __get_operation_in_line_templates(line_template)
            if UPDATE_KEYWORD_DELETE != foo_scope:
                scope = foo_scope
                break
        if (
            scope == UPDATE_KEYWORD_UPDATE
            and UPDATE_KEYWORD_BLOCK in last_line_template
        ):
            for index in range(last_line_template[UPDATE_KEYWORD_BLOCK]):
                foo_line = last_update_line[index] + "\n"
                if foo_line != src_file_lines[line_index + index]:
                    return False
            return f"scope == update and block in f{last_line_template}"

        # before就是替换find到的行的前一行
        # 如果替换后的代码刚好和前面行的最后一行一样, 就不会替换了
        def ____replaced_line_exists_in_scr_files(upwards=False):
            len_last_update_line = len(last_update_line)
            len_src_file_lines = len(src_file_lines)
            if upwards:
                # 向前缺少len_last_update_line行
                if line_index - len_last_update_line < 0:
                    return False
                for tmp_line_index in range(len_last_update_line):
                    if (
                        last_update_line[tmp_line_index] + "\n"
                        != src_file_lines[
                            line_index - len_last_update_line + tmp_line_index
                        ]
                    ):
                        return False
            else:
                # 向后缺少len_last_update_line行
                if len_src_file_lines < line_index + len_last_update_line:
                    return False
                for tmp_line_index in range(len_last_update_line):
                    if (
                        line_index + 1 + tmp_line_index >= len(src_file_lines)
                        or last_update_line[tmp_line_index] + "\n"
                        != src_file_lines[line_index + 1 + tmp_line_index]
                    ):
                        return False
            return True

        if scope == UPDATE_KEYWORD_BEFORE:
            return (
                f"before scope情况下{last_update_line} 和上一行一致"
                if ____replaced_line_exists_in_scr_files(True)
                else False
            )
        if scope == UPDATE_KEYWORD_AFTER:
            return (
                f"after scope情况下{last_update_line} 和下一行一致"
                if ____replaced_line_exists_in_scr_files(False)
                else False
            )
        return False

    src_file_lines = tf.readlines(target_files, True, False)
    """
    """

    def ____match_dependency_in_context(line_template):
        # log.info('----dependency----' + str(line_template))
        if UPDATE_KEYWORD_DEPENDENCY in line_template:
            dependencies = line_template[UPDATE_KEYWORD_DEPENDENCY]
            if isinstance(dependencies, list):
                # 多个依赖是Or关系,只要有一个存在就可以
                for dependency_item in dependencies:
                    # log.info('----isinstance----' + dependency_item + ' ' + str(dependency_item in context))
                    if dependency_item in context:
                        return True
                return False
            # dependencies还可以是个string, 表示只是一个依赖
            return dependencies in context
        # 因为只是在keyword过滤后多加一个条件,所以默认应该是返回True
        return True

    """
    """

    def ____aviable_line_templates(line_templates):
        if len(line_templates) == 0:
            return False
        for line_template in line_templates:
            if ____match_dependency_in_context(line_template):
                return True
        return False

    def ____discard_src_line(line_templates):
        for line_template in line_templates:
            scope = __get_operation_in_line_templates(line_template)
            if UPDATE_KEYWORD_DELETE == scope:
                return True
        return False

    def ____last_before_line_template(line_templates, line_template):
        foo = []
        for __line_template in line_templates:
            if UPDATE_KEYWORD_BEFORE == __get_operation_in_line_templates(
                line_template
            ):
                foo.append(__line_template)
        if len(foo) < 2:
            return True
        return foo[len(foo) - 1] == line_template

    def ____skip_block_line_num_inc_1(line_template):
        return (
            line_template[UPDATE_KEYWORD_BLOCK]
            if UPDATE_KEYWORD_BLOCK in line_template
            else 0
        )

    def ____merged_last_update_line(line, line_templates):
        merged_last_update_lines: list[str] = []
        for line_template in line_templates:
            last_update_line = (
                __k8s_helm_chart_create_process_template(context, line, line_template)
                if UPDATE_KEYWORD_TEMPLATE in line_template
                else ""
            )
            if last_update_line:
                merged_last_update_lines = merged_last_update_lines + last_update_line
        return merged_last_update_lines

    """
    search the wanted_append_keyword whether exists in the file
    """

    def ____match_appendKeyword_in_files(wanted_append_keyword: str):
        for var_line in src_file_lines:
            if wanted_append_keyword in var_line:
                return False
        return True

    """
    查找是否有keywordBlockEnd存在,返回0表示不存在
    """

    def __get_keyword_block_end(
        line_template: dict, line_index: int, lines_between_block: list[str]
    ):
        if UPDATE_KEYWORD_KEYWORD_BLOCK_END not in line_template:
            return 0
        # 此时line_index指向keyword
        tmp_line_index = line_index + 1
        # 如果存在block begin关键字先要定位到它,并且keyword和begin之间的内容要保留
        if UPDATE_KEYWORD_KEYWORD_BLOCK_BEGIN in line_template:
            tmp_line_index0 = tmp_line_index
            tmp_lines = []
            while tmp_line_index0 < len(src_file_lines):
                tmp_line = src_file_lines[tmp_line_index0]
                if line_template[UPDATE_KEYWORD_KEYWORD_BLOCK_BEGIN] in tmp_line:
                    tmp_line_index = tmp_line_index0 + 1
                    lines_between_block += tmp_lines
                    break
                # keyword begin已经包含在模板里面了
                tmp_lines.append(tmp_line)
                tmp_line_index0 += 1

        while tmp_line_index < len(src_file_lines):
            tmp_line = src_file_lines[tmp_line_index]
            if line_template[UPDATE_KEYWORD_KEYWORD_BLOCK_END] in tmp_line:
                return tmp_line_index - 1
            tmp_line_index += 1
        return 0

    # range stop should be len instead of len -1, or the last line will be skip
    line_index = 0
    file_position_flag = FILE_BEGIN_KEYWORD
    while line_index < len(src_file_lines):
        line = src_file_lines[line_index]
        file_position_flag = (
            FILE_MIDDLE_KEYWORD
            if line_index < len(src_file_lines) - 1
            else FILE_END_KEYWORD
        )
        if line_index == 0:
            file_position_flag = FILE_BEGIN_KEYWORD
        line2 = (
            src_file_lines[line_index + 1]
            if line_index < len(src_file_lines) - 1
            else ""
        )
        # 根据keyword找到所有匹配的行
        line_templates = __get_line_templates_by_keyword(
            last_line, line, line2, values, file_position_flag
        )
        last_update_line = ""
        # Known Issues: 2024-11-15, 模板里的keyword是个变量没处理
        # if line.startswith("kernal-app"):
        #     print(
        #         "------ file_replace_and_persist:: line.startswith",
        #         line_templates,
        #         last_line,
        #         line,
        #         line2,
        #         values,
        #         file_position_flag,
        #     )

        if ____aviable_line_templates(line_templates):
            discard_src_line = ____discard_src_line(line_templates)
            merged_last_update_lines = ____merged_last_update_line(line, line_templates)
            # 不可能又不符合模板,又符合keyword, 所以不用考虑else的continue
            if skip_case := ____template_replaced_in_line(
                line,
                merged_last_update_lines,
                line_templates,
                src_file_lines,
                line_index,
            ):
                last_line = line
                log.info(
                    f"{skip_case} so skip to replace:" + str(merged_last_update_lines)
                )
                if not discard_src_line:
                    lines.append(line)
                    discard_src_line = True
            else:
                check_line_miss = True  # 此标志用于最后去补全关键字所在行
                for line_template in line_templates:
                    if not ____match_dependency_in_context(line_template):
                        # print(
                        #     "------ file_replace_and_persist:: not ____match_dependency_in_context",
                        #     line_template,
                        # )
                        continue
                    # append模式,需要判断当前文档内不存在这个appendKeyword,如果没有一条规则被执行,当前line会丢失
                    if (
                        UPDATE_KEYWORD_APPEND_KEYWORD in line_template
                        and not ____match_appendKeyword_in_files(
                            line_template[UPDATE_KEYWORD_APPEND_KEYWORD]
                        )
                    ):
                        # print(
                        #     "------ file_replace_and_persist:: not ____match_appendKeyword_in_files",
                        #     line_template,
                        # )
                        continue
                    scope = __get_operation_in_line_templates(line_template)
                    last_update_line = (
                        __k8s_helm_chart_create_process_template(
                            context, line, line_template
                        )
                        if UPDATE_KEYWORD_TEMPLATE in line_template
                        else ""
                    )
                    # 检查是否有块结束关键字,有的话跳过中间的内容,然后用template内容替换它,用于多个元素组合的替换
                    lines_between_block = []
                    if (
                        keyword_block_end_line_index := __get_keyword_block_end(
                            line_template,
                            line_index,
                            lines_between_block=lines_between_block,
                        )
                    ) > 0:
                        line_index = keyword_block_end_line_index
                    if scope == UPDATE_KEYWORD_AFTER:
                        print(
                            "------ file_replace_and_persist:: UPDATE_KEYWORD_AFTER",
                            line_template,
                        )
                        if not discard_src_line:
                            lines.append(line)
                            # keyword block begin只支持after
                            if len(lines_between_block) > 0:
                                lines += lines_between_block
                            discard_src_line = True
                        check_line_miss = False
                        lines.append(____template_to_string(last_update_line))
                    elif scope == UPDATE_KEYWORD_BEFORE:
                        print(
                            "------ file_replace_and_persist:: UPDATE_KEYWORD_BEFORE",
                            line_template,
                        )
                        check_line_miss = False
                        lines.append(____template_to_string(last_update_line))
                        if not discard_src_line and ____last_before_line_template(
                            line_templates, line_template
                        ):
                            lines.append(line)
                            discard_src_line = True
                    elif scope == UPDATE_KEYWORD_UPDATE:
                        check_line_miss = False
                        # 一行的部分替换
                        if UPDATE_KEYWORD_PART in line_template:
                            lines.append(
                                ____template_to_string(
                                    [
                                        line.replace(
                                            line_template[UPDATE_KEYWORD_KEYWORD],
                                            line_template[UPDATE_KEYWORD_TEMPLATE],
                                        )
                                    ]
                                )
                            )
                        else:
                            lines.append(____template_to_string(last_update_line))
                        line_index = line_index + ____skip_block_line_num_inc_1(
                            line_template
                        )
                    elif scope == UPDATE_KEYWORD_DELETE:
                        check_line_miss = False
                        line_index = line_index + ____skip_block_line_num_inc_1(
                            line_template
                        )
                        discard_src_line = True
                if check_line_miss:
                    lines.append(line)
        else:
            lines.append(line)
        line_index += 1
        last_line = line
    with open(target_files, "w+", encoding="utf-8") as fo:
        fo.writelines(lines)


def handle_template_for_common_scripts(
    plugin_folder: str,
    module_definition: Union[dict, None],
    context: Union[dict, None],
    auto_crlf=False,
    comments="#",
    skip_predicate=None,
    allow_escape_char=False,
    skip_write_file=False,
    path_snippets="",
    exists_skip="",
):
    """
    module_definition = tcontext.load_item(thpe.load_template_yaml('linux'), f'linux/{module}')
    module_definition is load in template yaml
    the function to handle constant file structure
    ${module}.update.files[].templates[]
    in update.files[].path is relative path in plugin_folder
    ${module}.new.files
    in new.files, it is dict, key is new file name, values is file contents.
    allow_escape_char = True, 否者 \\n, \\t不能被替换为规避字符
    path_snippets: 附加的路径,类似与copy的效果,格式为path=url1,url2;..., 支持多个,因为','已被定义为多个url,所以此处用';'来分隔多个snippet
    exists_skip: 附加的存在就跳过文件,格式为file_pattern,...,用','分割支持多个
    """
    # log.info(f'use context to build{context}')
    if not module_definition:
        module_definition = {}
    if not context:
        context = {}
    new_files: list[str] = []
    excuted = False

    # 如果设置了comments,将替换所有comments开始的行
    def __skip_comments_in_file(lines, comments="#"):
        """
        如果lines是个文件名,等效于不处理,直接返回
        """
        if not comments:
            return lines
        return re.compile("#[^#\r\n]+\n").sub("", lines)

    def put_create_if_not_present(folder: str, file: str):
        if folder not in NEW_OPERATION_FILES:
            NEW_OPERATION_FILES[folder] = set()
        NEW_OPERATION_FILES[folder].add(file)

    def resolve(file_path: str):
        return (
            file_path
            if os.path.isabs(file_path)
            else os.path.abspath(os.path.join(plugin_folder, file_path))
        )

    if UPDATE_KEYWORD_UPDATE in module_definition:
        operation_update_definition = module_definition[UPDATE_KEYWORD_UPDATE]
        excuted = True
        for file_path in operation_update_definition["files"].keys():
            file_definition = operation_update_definition["files"][file_path]
            if skip_predicate and skip_predicate(file_path):
                continue
            log.info(f"{file_path} handler")
            target_file = os.path.abspath(os.path.join(plugin_folder, file_path))
            file_replace_and_persist(context, file_definition["templates"], target_file)
    if NEW_KEYWORD_NEW in module_definition:
        operation_new_definition = module_definition[NEW_KEYWORD_NEW]
        excuted = True
        exists_skip_definition: list[str] = tworkaround.list_add_with_trim(
            tcontext.get_field(operation_new_definition, NEW_KEYWORD_EXISTS_SKIP, []),
            exists_skip.split(","),
        )
        rm_skip_definition: list[str] = tcontext.get_field(
            operation_new_definition, NEW_KEYWORD_RM_SKIP, []
        )
        copy_definition: dict[str, str] = tcontext.get_field(
            operation_new_definition, NEW_KEYWORD_COPY, {}
        )
        tcontext.replace_object(context=context, config=rm_skip_definition)
        # 需要合并copy 和 files中生成的模板一起处理
        runtime_new_files: dict[str, str] = (
            tcontext.deep_merge({}, operation_new_definition[NEW_KEYWORD_FILES])
            if NEW_KEYWORD_FILES in operation_new_definition
            else {}
        )
        # src_file可以是由,隔开的多个地址合并项目
        runtime_copy_definition_dict: dict[str, str] = {**copy_definition}
        for path_snippet in tworkaround.list_add_with_trim(path_snippets.split(";")):
            target_file, raw_src_file = path_snippet.split("=")
            # 已经定义了的路径,需要用','把它们合并
            if target_file in runtime_copy_definition_dict:
                runtime_copy_definition_dict[target_file] += "," + raw_src_file
            else:
                runtime_copy_definition_dict[target_file] = raw_src_file
        for target_file, raw_src_file in runtime_copy_definition_dict.items():
            target_file_path = resolve(
                tcontext.replace_by_context(context, target_file)
            )
            # 处理多个src_file的情况
            for src_file in raw_src_file.split(","):
                src_file_path = tcontext.replace_by_context(context, src_file)
                # 此处还应该支持从url中获取模板并解析
                if tf.is_http(src_file):
                    for file_name, file_url in tgitlab_api.gitlab_api_list(
                        src_file_path
                    ).items():
                        runtime_new_files[f"{target_file_path}/{file_name}"] = file_url
                else:
                    src_file_path = resolve(src_file_path)
                    for file_name, file_url in tf.template_file_dict(
                        src_file_path
                    ).items():
                        runtime_new_files[f"{target_file_path}/{file_name}"] = file_url

        for file_name in runtime_new_files.keys():
            file_path = tcontext.replace_by_context(context, file_name)
            folder_path = os.path.dirname(file_path)
            target_file = resolve(file_path)
            if folder_path not in rm_skip_definition:
                put_create_if_not_present(os.path.dirname(target_file), target_file)
            if (
                skip_predicate
                and skip_predicate(target_file)
                or exists_skip_handler(exists_skip_definition, target_file)  # type: ignore
            ):
                log.warning(f"{target_file} is skip")
                print(
                    "------ exists_skip_definition",
                    skip_predicate,
                    exists_skip_definition,
                )
                continue
            log.debug(f"{file_path} handler")
            file_definition = __get_template_text_by_string(
                runtime_new_files[file_name]
            )
            file_definition = __skip_comments_in_file(file_definition, comments)
            file_definition = tcontext.skip_conditions_in_section(
                context, file_definition
            )
            # 支持之创建文件夹, 所以此时文件内容是没有的, 例如src/main/java:
            if file_definition:
                tf.mkdir_if_absent(os.path.dirname(target_file))
                if tf.is_binary_file(target_file):
                    # 复制二进制内容,此时file_definition为原始文件名,可能是个url
                    tf.copy(file_definition, target_file)
                else:
                    write_lines = tcontext.write_to_file_with_replace(
                        target_file=target_file,
                        lines=file_definition,
                        context=context,
                        auto_crlf=auto_crlf,
                        allow_escape_char=allow_escape_char,
                        skip_write_file=skip_write_file,
                    )
                if skip_write_file:
                    new_files += write_lines
            else:
                tf.mkdir_if_absent(target_file)
            # 不写文件需要返回替换的行
            if not skip_write_file:
                new_files.append(target_file)
    if not excuted:
        log.error(f"please define at least one new/files or update/files!")
    return new_files


def exists_skip_handler(
    exists_skip_definition: Union[list[str], None], target_files: str
):
    if not exists_skip_definition:
        return False
    for filename_template in exists_skip_definition:
        if (
            filename_template
            and re.search(filename_template, target_files)
            and os.path.exists(target_files)
        ):
            return True
