import tlog.tlogging as tl
import glob
import os, datetime, re
from enum import Enum
import fnmatch
import hashlib
import shutil
import yaml
import tempfile
import mimetypes
import urllib.request
import tutils.tssh as tssh
import xml.etree.ElementTree as ET
import chardet
import codecs
from pathlib import Path
from typing import Union, Literal

log = tl.log if hasattr(tl, "log") else None
URI_LITERAL = Literal[r"^[a-zA-Z]:\\", r"^https?://"]
# 替换doc-template用本地文件, 可以不用提交而立刻生效
USE_LOCAL_FILE_FOR_DOC_TEMPLATE = False
DOC_TEMPLATE_PREFIX = "https://de.vicp.net:58443/Shao/doc-template/-/raw/main"
DOC_TEMPLATE_LOCAL_FOLDER = "C:\\usr\\ssz\\workspace\\git\\app\\doc-template"
USER_PROFILE = os.path.expanduser("~")


class UriType(Enum):
    FILE = r"^[a-zA-Z]:\\"
    URL = r"^https?://"


class TFile(object):
    def __init__(self):
        print()
        if log:
            log.debug("TFile init")


def linuxPath(winPath):
    return winPath.replace("\\", "/")


"""
    if os is windows, replace \\ to \\\\
    if os is linux or mac, skip it
"""


def escape_path(path):
    return path.replace("\\", "\\\\")


def copy(src: str, dest: str, checkSha1: bool = False):
    if checkSha1:
        if os.path.isfile(src) and os.path.isfile(dest) and sha1(src) == sha1(dest):
            return
    if log:
        log.info(f"copy {src} to {dest}")
    if is_remote_path(src):
        remote_src = src
        src = os.path.join(tempfile.gettempdir(), "tmp.bin")
        tssh.get(remote_src, local=src)
    if is_http(src):
        download_from_http(src, dest)
        return
    if is_remote_path(dest):
        tssh.put(dest, local=src)
    else:
        # PermissionError: [errno 13] permission denied workaround for other ownship file
        # removeIfPresent(dest)
        os.path.exists(src) and shutil.copy(src, dest) or log.warning(
            f"{src} not found"
        )


def tar(dir: str, abs_filename_without_ext: str):
    shutil.make_archive(abs_filename_without_ext, "tar", dir)


def zip(dir: str, abs_filename_without_ext: str):
    shutil.make_archive(abs_filename_without_ext, "zip", dir)


def yaml_load(filename: str):
    if not os.path.exists(filename):
        return None
    with open(filename, "r+", encoding="utf-8") as fo:
        return yaml.load(fo.read(), Loader=yaml.FullLoader)


def yaml_dump(filename: str, json: object):
    with open(filename, "w+", encoding="utf-8") as fo:
        yaml.dump(json, fo)


def backup(src: str):
    if not os.path.exists(src):
        return
    nowTime = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    target_file = f"{src}.bak.{nowTime}"
    copy(src, target_file)
    return target_file


def getpythonpath():
    pythonPath = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(pythonPath + "/..")


def override(sample_file, runtime_file):
    return runtime_file if os.path.exists(runtime_file) else sample_file


def convert_file_to_utf8(filename):
    # !!! does not backup the origin file
    #  with open(filename, 'r+') as fo:
    #         lines = fo.read()
    content = codecs.open(filename, "rb").read()
    source_encoding = chardet.detect(content)["encoding"]
    if source_encoding == None:
        log.error(f"{filename}")
        return
    log.info(f"{source_encoding}, {filename}")
    if source_encoding != "utf-8" and source_encoding != "UTF-8-SIG":
        content = content.decode(source_encoding, "ignore")  # .encode(source_encoding)
        codecs.open(filename, "w", encoding="UTF-8").write(content)


def readlines_from_file(file: str, allowEmpty=False, allowStrip=True):
    projects: list[str] = []
    with open(file, "r+", encoding=detect_encoding(file)) as fo:
        for line in fo.readlines():
            if allowStrip:
                line = line.strip()
            if line or allowEmpty:
                projects.append(line)
    return projects


def readlines_from_http(url: str, allowEmpty=False, allowStrip=True):
    projects: list[str] = []
    token_regexp = r"(https?://)(.+@)*(.+)"
    headers = {}
    if url_match := re.match(token_regexp, url):
        url = f"{url_match.group(1)}{url_match.group(3)}"
        if url_match.group(2):
            headers["Authorization"] = f"Token {url_match.group(2)[:-1]}"
    log.info(f"request from {url}")
    if USE_LOCAL_FILE_FOR_DOC_TEMPLATE and url.startswith(DOC_TEMPLATE_PREFIX):
        local_doc_template_file = os.path.join(
            DOC_TEMPLATE_LOCAL_FOLDER, *url[len(DOC_TEMPLATE_PREFIX) :].split("/")
        )
        if os.path.exists(local_doc_template_file):
            log.info(
                f"redirect to load from {local_doc_template_file} because USE_LOCAL_FILE_FOR_DOC_TEMPLATE is enabled"
            )
            return readlines_from_file(local_doc_template_file, allowEmpty, allowStrip)
        else:
            log.warning(
                f"failure redirect to load from {local_doc_template_file} because it is not exists with USE_LOCAL_FILE_FOR_DOC_TEMPLATE is enabled, load it from http again!"
            )
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers)
    ) as response:
        # splitlines一定要带True参数,否则不是所有line都会合并成一行
        for line in response.read().decode("utf-8").splitlines(True):
            if allowStrip:
                line = line.strip()
            if line or allowEmpty:
                projects.append(line)
    return projects


def download_from_http(url: str, target_file_path: str):
    token_regexp = r"(https?://)(.+@)*(.+)"
    headers = {}
    if url_match := re.match(token_regexp, url):
        url = f"{url_match.group(1)}{url_match.group(3)}"
        if url_match.group(2):
            headers["Authorization"] = f"Token {url_match.group(2)[:-1]}"
    log.info(f"request from {url}")
    if USE_LOCAL_FILE_FOR_DOC_TEMPLATE and url.startswith(DOC_TEMPLATE_PREFIX):
        local_doc_template_file = os.path.join(
            DOC_TEMPLATE_LOCAL_FOLDER, *url[len(DOC_TEMPLATE_PREFIX) :].split("/")
        )
        log.info(
            f"redirect to load from {local_doc_template_file} becasue USE_LOCAL_FILE_FOR_DOC_TEMPLATE is enabled"
        )
        os.path.exists(local_doc_template_file) and shutil.copy(
            local_doc_template_file, target_file_path
        ) or log.warning(f"{local_doc_template_file} not found")
        return True
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers)
    ) as response:
        # 将文件内容写入本地文件
        with open(target_file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    return True


def readstring(file: str):
    return "".join(readlines(file, allowStrip=False))


def readlines(file: str, allowEmpty=False, allowStrip=True):
    """读取行,支持file, http, ssh

    Args:
        file (str): 文件名, URL
        allowEmpty (bool, optional): 结果集允许空行. Defaults to False.
        allowStrip (bool, optional): 结果集合的每行开头和结尾删除空白字符. Defaults to True.

    Returns:
        _type_: list[str]
    """
    if re.match(UriType.URL.value, file):
        return readlines_from_http(file, allowEmpty, allowStrip)
    return readlines_from_file(file, allowEmpty, allowStrip)


def writelines(file: str, lines: list[str], append=False):
    if not os.path.exists(file):
        mkdir_if_absent(os.path.dirname(file))
    append_mode = "a+" if append else "w+"
    with open(file, append_mode, encoding="utf-8") as fw:
        fw.writelines([line if line.endswith("\n") else f"{line}\n" for line in lines])


def removeLine(file, line):
    backup(file)
    writes = []
    # 在一个循环内同时读写会导致文件为空
    for line_text in readlines(file):
        if not re.match(line, line_text):
            writes.append(line_text)
    with open(file, "w") as fw:
        for line_text in writes:
            fw.write(line_text + "\n")


"""
<property name="compile.version" value="1.7"/>
"""


def xml_properties(xml_line: str):
    root: ET.Element = ET.XML(xml_line)
    return root.attrib or {}


def xml_attribs(plugins_xml_file, xml_path, ns=None):
    root = ET.parse(plugins_xml_file).getroot()
    ns = {"ium": "http://ov.hp.com/ium/namespace/plugin"}
    results = []
    for item in root.findall(xml_path, ns):
        result_item = {}
        for attribute, value in item.items():
            result_item[attribute] = value
        results.append(result_item)
    return results


def properties(properties_file):
    context = {}
    if not os.path.exists(properties_file):
        return context
    # merged_lines in using load continue line for \\, so only 1 line, don't use it
    merged_lines = []
    for line in readlines(properties_file, True):
        if not line or line.startswith("#"):
            continue
        # = is flag to commit the merge line
        if "=" in line:
            if merged_lines:
                __properties_handle_1_line(context, "".join(merged_lines))
            merged_lines.clear()
        if line.endswith("\\"):
            merged_lines.append(line.replace("\\", ""))
        else:
            # two situation, 1 is the last for \\, 2 is only 1 line with =
            __properties_handle_1_line(context, line)
            if "=" not in line:
                merged_lines.append(line)
    if merged_lines:
        __properties_handle_1_line(context, "".join(merged_lines))
    return context


def dotenv(key: str):
    dotnet_file = os.path.join(os.path.expanduser("~"), ".env")
    context = dotenv_context(dotnet_file)
    if key in context:
        return context[key]
    raise ValueError(f"{key} not found in {dotnet_file}")


def dotenv_context(dotnet_file=os.path.join(os.path.expanduser("~"), ".env")):
    from tutils.context_opt import replace_object

    context = properties(dotnet_file)
    replace_object(context, context)
    return context


def replace(file, regexp, replace_str, not_exists_add=False):
    writes = []
    found = False
    for line_text in readlines(file):
        if re.match(regexp, line_text):
            writes.append(replace_str)
            found = True
        else:
            writes.append(line_text)
    if not_exists_add and not found:
        writes.append(replace_str)
    with open(file, "w") as fw:
        for line_text in writes:
            fw.write(line_text + "\n")


def read_file(filename: str):
    lines: list[str] = []
    try:
        with open(os.path.join(filename, filename), "r+") as fo:
            lines = fo.readlines()
    except Exception as e:
        if log:
            log.error(e)
    return lines


def remove_dirs(path):
    if log:
        log.info("rm -rf " + path)
    if os.path.exists(path):
        shutil.rmtree(path)


def remove_folder(path):
    if log:
        log.info("rm -rf " + path)
    if is_remote_path(path):
        usr, passwd, port, host, remote_path = tssh.parse_remote_path(path)
        if remote_path.strip() == "/":
            log.error("remove / is not allowed, please check it again.")
            return
        tssh.ssh(host, passwd, f"rm -rf {remote_path}", port, usr=usr)
    else:
        if os.path.exists(path):
            shutil.rmtree(path)


def remove_if_present(path):
    if is_remote_path(path):
        if log:
            log.info("remove " + path)
        usr, passwd, port, host, remote_path = tssh.parse_remote_path(path)
        tssh.ssh(host, passwd, f"rm -f {remote_path}", port, usr=usr)
        return
    if os.path.exists(path):
        if log:
            log.info("remove " + path)
        os.remove(path)


def mkdir_if_absent_path_prefix_or_get_first(workspace: str, path: str):
    workspace = os.path.dirname(path)
    file_keyword = os.path.basename(path)
    if log:
        log.info(f"search {file_keyword} in {workspace}")
    folders = [
        str(path) for path in Path(os.path.abspath(workspace)).rglob(f"{file_keyword}*")
    ]
    if len(folders) > 0:
        return folders[0]
    return path


def mkdir_if_absent(path: str):
    if not path:
        return False
    if is_remote_path(path):
        usr, passwd, port, host, remote_path = tssh.parse_remote_path(path)
        tssh.ssh(host, passwd, f"mkdir -p {remote_path}", port, usr=usr)
        return True
    if os.path.exists(path):
        if os.path.isfile(path):
            if log:
                log.info("remove file" + path)
            os.remove(path)
            if log:
                log.info("mkdir " + path)
            os.mkdir(path)
            return True
        if log:
            log.debug(" ".join([path, "exists"]))
        return False
    else:
        paths = os.path.split(path)
        mkdir_if_absent(paths[0])
        if log:
            log.info(f"mkdir {path}")
        os.mkdir(path)
        return True


def digest(file: str, algorithm) -> str:
    with open(file, "rb") as fr:
        str = " "
        while str:
            str = fr.read(65536)
            if str:
                algorithm.update(str)
        return algorithm.hexdigest()


def sha1(
    file: Union[str, list[str]], ssh_remote_path: bool = False, verbose: bool = False
) -> Union[str, dict[str, str], None]:
    """计算文件hash

    Args:
        file (Union[str, list[str]]): 文件
        ssh_remote_path (bool, optional): 文件是linux远程路径例如root@xxx:/yyy. Defaults to False.
        verbose (bool, optional): 详细打印执行步骤. Defaults to False.

    Returns:
        Union[str, dict[str,str], None]: 文件hash,或者文件hash的dict,不存在返回None
    """
    if ssh_remote_path:
        usr, passwd, port, host, remote_path = tssh.parse_remote_path(ssh_remote_path)
        if verbose:
            log.info(f"sha1sum {str(file)} from {ssh_remote_path}")
        if isinstance(file, str):
            return tssh.ssh(host, passwd, f"sha1sum {file}", port, usr).split()[0]
        else:
            sha1s = {}
            if not file:
                return sha1s
            last_sha1_sum = "notexists"
            continue_flag = False
            for runtime_file in tssh.ssh(
                host, passwd, f'sha1sum {" ".join(file)}', 22, usr
            ).split():
                # for runtime_file in tssh.ssh(host, passwd, f'[ -f {remote_path}/sha1sum.txt ] && cat {remote_path}/sha1sum.txt || sha1sum {" ".join(file)}', 22, usr).split():
                # if continue_flag:
                #     continue_flag = False
                #     continue
                if "/" in runtime_file:
                    # if runtime_file not in file:
                    #     continue_flag = True
                    #     continue
                    sha1s[os.path.basename(runtime_file)] = last_sha1_sum
                else:
                    last_sha1_sum = runtime_file
            return sha1s
    if isinstance(file, str):
        if not os.path.exists(file):
            return None
        return digest(file, hashlib.sha1())
    else:
        sha1s = {}
        if not file:
            return sha1s
        for runtime_file in file:
            sha1s[os.path.basename(runtime_file)] = sha1(
                runtime_file, ssh_remote_path, verbose
            )
        return sha1s


def md5(file):
    return digest(file, hashlib.md5())


def ensure_change_dir(cmds: list[str], dir: str):
    cmds.append(os.path.splitdrive(dir)[0])
    cmds.append("cd " + dir)


def search_dirs(directory: str, pattern: str):
    """
    返回目录下符合规则的文件列表
    """
    matches = []
    for filename in fnmatch.filter(os.listdir(directory), pattern):
        matches.append(os.path.join(directory, filename))
    return matches


def match_include(abs_file: str, include_array: Union[list[str], None]):
    """
    see :func:`match_exclude`
    如果没有定义include pattern或 include数组为空, always return True
    所有pattern都搜索完成了还是没有符合的,就认为不应该include
    """
    if not include_array or len(include_array) == 0:
        return True
    for template in include_array:
        if fnmatch.fnmatch(abs_file, template):
            return True
    return False


def match_exclude(abs_file: str, exclude_array: Union[list[str], None]):
    """
    如果没有定义exclude pattern或 exclude数组为空, always return False, 意味着skip exclude
    所有pattern都搜索完成了还是没有符合的,就认为不需要exclude
    template, https://c.biancheng.net/view/2543.html
    fnmatch 模块匹配文件名的模式使用的就是 UNIX shell 风格，其支持使用如下几个通配符：
    *：可匹配任意个任意字符。
    ？：可匹配一个任意字符。
    [字符序列]：可匹配中括号里字符序列中的任意字符。该字符序列也支持中画线表示法。比如 [a-c] 可代表 a、b 和 c 字符中任意一个。
    [!字符序列]：可匹配不在中括号里字符序列中的任意字符。
    """
    if not exclude_array or len(exclude_array) == 0:
        return False
    for template in exclude_array:
        if fnmatch.fnmatch(abs_file, template):
            return True
    return False


def match(
    abs_file: str,
    include_array: Union[list[str], None] = None,
    exclude_array: Union[list[str], None] = None,
):
    """
    include_array, exclude_array 同时有, 如果同时满足,就排除它,否则只包含include中的内容
    include_array, 返回包含在include_array的
    exclude_array, 返回包含在exclude_array的
    """
    if include_array and exclude_array:
        return match_include(abs_file, include_array) and not match_exclude(
            abs_file, exclude_array
        )
    if include_array:
        return match_include(abs_file, include_array)
    # print(exclude_array)
    if exclude_array:
        return not match_exclude(abs_file, exclude_array)
    return True


def list_remote_dir(path: str):
    if path.endswith("/"):
        path = path[:-1]
    usr, passwd, port, host, remote_path = tssh.parse_remote_path(path)
    return tssh.ssh(host, passwd, f"ls --file-type {remote_path}", port, usr).split()


def search(workspace: str, file_keyword: str, exact=True):
    """
    根据文件名关键字搜索所有符合条件的文件
    file_keyword: 如果exact = True, 也支持* ?
    返回的结果集合为绝对路径的数组
    """
    return [
        str(path)
        for path in Path(os.path.abspath(workspace)).rglob(
            file_keyword if exact else f"*{file_keyword}*"
        )
    ]


def search_file_in_folder_to_match_text(
    workspace: str,
    file_keyword: str,
    target_text: str,
    exact_match_file_name=True,
):
    """用文件内容来搜索文件以递归方式

    Args:
        workspace (str): 工作区
        file_keyword (str): 文件名模板, 即使精确匹配,自身也支持*?
        target_text (str): 文件内容模板
        exact_match_file_name (bool, optional): 文件名模板不会给你加上前后*. Defaults to True.

    Returns:
        _type_: 匹配到的文件名列表,是绝对路径
    """
    return [
        file
        for file in search(workspace, file_keyword, exact=exact_match_file_name)
        if (not target_text) or search_text_in_file(file, target_text)
    ]


def search_text_in_file(file_path: str, target_text: str):
    with open(file_path, "r") as file:
        file_content = file.read()
        pattern = re.compile(target_text, re.DOTALL)
        if pattern.search(file_content):
            return True
    return False


def detect_encoding(file_path: str):
    with open(os.path.abspath(file_path), "rb") as file:
        result = chardet.detect(file.read())
    if not result["encoding"]:
        log.warning(f"{file_path} should be a binary file, encoding not found")
    return result["encoding"]


def convert_to_encoding(file_path: str, encoding="utf-8"):
    detected_encoding = detect_encoding(file_path)
    with codecs.open(
        file_path, "r", encoding=detected_encoding, errors="ignore"
    ) as file:
        content = file.read()
    with codecs.open(file_path, "w", encoding=encoding) as file:
        file.write(content)


def find_context_in_file(
    absolute_file: str, match_reg: str, expected_match_count=1, exact=False
) -> Union[str, None]:
    if not os.path.exists(absolute_file):
        return None
    if not exact:
        line_match_reg = re.compile(match_reg)
    match_count_num = 0
    for line in readlines(absolute_file):
        if not exact and (result := line_match_reg.search(line)):
            match_count_num += 1
            if expected_match_count == match_count_num:
                return (
                    result.groups(1)[0] if len(result.groups()) >= 1 else result.group()
                )
        if line == match_reg and exact:
            match_count_num += 1
            if expected_match_count == match_count_num:
                return line


def sync_folder(
    src,
    target,
    include=None,
    exclude=None,
    mirror: bool = False,
    verbose: bool = False,
    recursive: bool = False,
):
    """
    include 可以是文件,格式 *.bak.*
    exclude 可以是文件,格式 *.bak.*
    如果include, exclude同时满足, exlude它, 否则只包含include里的内容
    mirror src 和 target保持完全一致
    """
    if not os.path.exists(src):
        return
    if src.endswith("/"):
        src = src[:-1]
    if target.endswith("/"):
        target = target[:-1]
    mkdir_if_absent(target)
    log.debug("include is " + str(include))
    log.debug("exclude is " + str(exclude))
    include_array = __sync_folder_parse_filter(include)
    exclude_array = __sync_folder_parse_filter(exclude)
    log.info("include_array is " + str(include_array))
    log.debug("exclude_array is " + str(exclude_array))
    updates = []
    removes = []
    try:
        target_sha_cache = (
            diff(target, oldSha1s={}, updates=[], removes=[], verbose=verbose)
            if mirror
            else diff(
                target,
                oldSha1s={},
                updates=[],
                removes=[],
                include=include_array,
                exclude=exclude_array,
                verbose=verbose,
            )
        )
        diff(
            src,
            oldSha1s=target_sha_cache,
            updates=updates,
            removes=removes,
            include=include_array,
            exclude=exclude_array,
            mirror=mirror,
            verbose=verbose,
        )
    except Exception as e1:
        print(e1)
    for file in updates:
        try:
            copy(os.path.join(src, file), os.path.join(target, file))
        except Exception as e:
            print(e)
    for file in removes:
        remove_if_present(os.path.join(target, file))
    src_subfolders = {}

    for file in listdir(src):
        src_folder = os.path.join(src, file)
        src_subfolders[file] = src_folder
    # 如果已经有了include, recursive是否应该自动开启呢?,否则include包含子目录,但确不会去自动寻找
    if recursive:
        match_sub_folder: dict[str, str] = {}
        for src_file in [
            f
            for f in glob.glob(os.path.join(src, "**"), recursive=True)
            if os.path.isfile(f) and match(f, include_array, exclude_array)
        ]:
            src_folder = os.path.dirname(src_file)
            if not src_folder == src:
                match_sub_folder[src_folder] = "1"
        for src_folder in match_sub_folder.keys():
            relative_target_path = src_folder.replace(src, "")
            sync_folder(
                src_folder,
                target + relative_target_path,
                include_array,
                exclude_array,
                mirror,
                verbose,
                recursive=False,
            )
    if mirror:
        for file in listdir(target):
            target_file = os.path.join(target, file)
            if isdir(target_file) and file not in src_subfolders:
                remove_folder(target_file)
    log.info(f"{target} completed!!!")


def __get_true_folder(path: str):
    """
    获取真正的路径,支持远程路径
    """
    if is_remote_path(path):
        usr, passwd, port, host, remote_path = tssh.parse_remote_path(path)
        return True, remote_path
    return False, path


def listdir(path: str, recursive=False, result_suffix=""):
    """
    不抛出异常,如果文件不存在,返回空数组
    recursive: 递归寻找子目录
    result_suffix: 返回结果集合里的前缀(文件名前会加上这个部分)
    """
    if is_remote_path(path):
        return list_remote_dir(path)
    result = os.listdir(path) if os.path.exists(path) else []
    if recursive:
        merged_result = [
            f"{result_suffix}/{result_item}" if result_suffix else result_item
            for result_item in result
        ]
        for file_name in result:
            abs_file_path = os.path.join(path, file_name)
            if os.path.isdir(abs_file_path):
                merged_result += listdir(
                    abs_file_path,
                    recursive,
                    result_suffix=(
                        f"{result_suffix}/{file_name}" if result_suffix else file_name
                    ),
                )
        return merged_result
    else:
        return result


def template_file_dict(path: str, is_template_file=True):
    """
    遍历一个本地目录,返回模板文件集合
    path: 本地路径或一个文件名,如果是文件名只返回一个文件
    is_template_file: 作为模板文件返回
    """
    result_files: dict[str, str] = {}
    runtime_file_path_list: list[str]
    if os.path.isfile(path):
        # 需要兼容listdir的返回结果所以需要把文件名和路径名分隔开
        runtime_file_path_list = [os.path.basename(path)]
        path = os.path.dirname(path)
    else:
        runtime_file_path_list = listdir(path, recursive=True)
    for file_path in runtime_file_path_list:
        abs_file_path = os.path.join(path, file_path)
        file_url = abs_file_path
        if os.path.isfile(abs_file_path):
            result_files[file_path] = (
                f"${{::TEMPLATE_FILE}}={file_url}" if is_template_file else file_url
            )
    return result_files


def is_remote_path(abs_file: str):
    return "@" in abs_file


def is_http(url: str):
    return True if re.match(UriType.URL.value, url) else False


def hex(line: str):
    return bytes(line, "UTF-8").hex()


def isfile(abs_file, ssh_remote_path=False):
    if is_remote_path(abs_file):
        ssh_remote_path = True
    return not abs_file.endswith("/") if ssh_remote_path else os.path.isfile(abs_file)


def isdir(abs_file, ssh_remote_path=False):
    if is_remote_path(abs_file):
        ssh_remote_path = True
    return abs_file.endswith("/") if ssh_remote_path else os.path.isdir(abs_file)


# def left_folder_by_first(abspath, path='siu'):
#     if '/' not in path: return __left_folder_by_first(abspath, path)
#     sub_folder = os.path.dirname(path)
#     file_name = os.path.basename(path)
#     home = __left_folder_by_first(abspath, sub_folder)
#     abs_file = os.path.abspath(os.path.join(home, sub_folder, file_name))
#     print('-----', abspath, abs_file, sub_folder, file_name, home)
#     if os.path.exists(abs_file): return home
#     raise FileNotFoundError(f'{path} is not found in {abspath}')


# look first folder whether exist the special file
# after finding, return the folder name
def left_folder_by_first(abspath: str, path="siu/build.xml", throw_error=True):
    """
    往上层目录一直寻找匹配path的路径
    """
    home = linuxPath(abspath)
    while "/" in home and not os.path.exists(os.path.abspath(os.path.join(home, path))):
        # print(os.path.abspath(os.path.join(home, path)))
        home = home[0 : home.rfind("/")]
    if "/" not in home:
        # 如果找不到直接返回当前目录
        if throw_error:
            raise FileNotFoundError(f"{path} is not found in {abspath}")
        else:
            return abspath
    return os.path.abspath(home)


def __left_folder_by_first(abspath, sub_folder="siu"):
    abspath = linuxPath(abspath)
    sub_folder_tmp = linuxPath(f"/{sub_folder}")
    return abspath[0 : abspath.find(sub_folder_tmp)]


def diff(
    path: str,
    oldSha1s: dict = {},
    updates: list[str] = [],
    removes: list[str] = [],
    child_dirs: list[str] = [],
    include: Union[str, list[str], None] = None,
    exclude: Union[str, list[str], None] = None,
    mirror: bool = False,
    verbose: bool = False,
):
    """只返回被include, exclude约束的文件hash

    Args:
        path (str): 文件夹
        oldSha1s (dict, optional): 缓存的hash dict, 用来快速比较. Defaults to {}.
        updates (list[str], optional): 返回那些文件发生了变化,增加的文件也会被加入updates列表. Defaults to [].
        removes (list[str], optional): 返回那些文件被删除了. Defaults to [].
        include (Union[str, list[str],None], optional): 可以是pattern文件或者以,分隔的pattern. Defaults to None.
        exclude (Union[str, list[str],None], optional): 可以是pattern文件或者以,分隔的pattern. Defaults to None.
        mirror (bool, optional): 是否保持完全一致. Defaults to False.
        verbose (bool, optional): 详细打印执行步骤. Defaults to False.

    Returns:
        _type_: 只返回被include, exclude约束的文件hash
    """
    include_array = include.split(",") if isinstance(include, str) else include
    exclude_array = exclude.split(",") if isinstance(exclude, str) else exclude
    ssh_remote_path, folder = __get_true_folder(path)
    need_sha1sum_files = []
    for file in listdir(path):
        # 增加的文件也会被加入updates列表
        # 由于path support remote ssh, so 不要把它转换成os.path.join()
        target_file = f"{folder}/{file}"
        if isdir(target_file, ssh_remote_path):
            child_dirs.append(file)
        if isfile(target_file, ssh_remote_path) and match(
            target_file, include_array, exclude_array
        ):
            need_sha1sum_files.append(target_file)
            # sha1s[file] = sha1(target_file, ssh_remote_path, verbose)
    sha1s = sha1(need_sha1sum_files, ssh_remote_path, verbose)
    for file in sha1s.keys():
        if file not in oldSha1s or not oldSha1s[file] == sha1s[file]:
            updates.append(file)
    for file in oldSha1s:
        target_file = f"{folder}/{file}"
        runtime_match = (
            True if mirror else match(target_file, include_array, exclude_array)
        )
        if file not in sha1s and runtime_match:
            # sha1只有文件才会生成,所以不需要判断它不是directory
            # if not os.path.isdir(target_file) and file not in sha1s and runtime_match:
            removes.append(file)
    return sha1s


def merge_properity_array(dict_properties: dict[str, str], results: list, key: str):
    if key in dict_properties and dict_properties[key]:
        for new_key in dict_properties[key].split(","):
            if new_key and new_key not in results:
                if new_key.startswith("$"):
                    new_key2 = new_key[2 : len(new_key) - 1]
                    # 3rd jar如果也替换会出错,直接就被删除了,因为它不在dict_properties里定义
                    if new_key2 in dict_properties:
                        merge_properity_array(dict_properties, results, new_key2)
                    else:
                        results.append(new_key)
                else:
                    results.append(new_key)


def line_not_in_lines(lines, tpl):
    foo = tpl.split("\n")
    for line in lines:
        for line_foo in foo:
            if line_foo == line or (line_foo + "\n") == line:
                foo.remove(line_foo)
                break
    return foo


EMBED_BINARY_EXT_FILE = [".eot", ".ttf", ".woff"]


def is_binary_file(file_path: str) -> bool:
    """
    判断文件是否为二进制文件
    file_path: 全路径文件名
    Known issues: 2024-09-11, ts会被认定为文本文件typescript,它和视频文件ts同名
    """
    _, file_extension = os.path.splitext(file_path)
    if file_extension in EMBED_BINARY_EXT_FILE:
        return True
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype is None:
        # 如果无法判断 MIME 类型，返回 None
        # raise Exception(f"{file_path} is not support in mimetypes module")
        return False
    elif mimetype.startswith("application"):
        return False
    elif mimetype.startswith("text"):
        return False  # MIME 类型以 'text/' 开头的文件通常是文本文件
    elif mimetype.startswith("video/vnd.dlna.mpeg-tts"):
        return False  # MIME 规避typescript文件,它和视频文件ts同名
    else:
        print("---------- is_binary_file", mimetype, file_path)
        return True  # 其他类型通常是二进制文件


def __sync_folder_parse_filter(
    filter: Union[str, list[str], None] = None,
) -> Union[list[str], None]:
    """
    filter, str:文件名,读取文件内容转换为list[str], str: 以,分隔的filter字符串,转换为list[str]
    """
    if isinstance(filter, str):
        if os.path.isfile(filter):
            with open(filter, "r+", encoding="utf8") as fo:
                filter_array = []
                for line in fo.readlines():
                    if line and line.strip():
                        filter_array.append(line.strip())
                return filter_array
        if ":" in filter:
            raise IOError("incorrect file " + filter)
        return [pattern.strip() for pattern in filter.split(",")]
    return filter


def __properties_handle_1_line(context, line):
    if "=" in line:
        foo = line.split("=")
        context[foo[0]] = foo[1]
