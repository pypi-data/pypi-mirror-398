from posixpath import islink
import yaml, tempfile, requests
import sys, re, os, platform
import socket
import tlog.tlogging as tl
import tio.tfile as tf
import tutils.context_opt as tcontext
from typing import Union
import certifi
from datetime import datetime

from ping3 import ping

is_linux = "Linux" == platform.system()
TEMPEST_HOST_FOLDER = "ub-8dev" if is_linux else "win-8001"
PREFIX_CALL = "" if is_linux else "call "
log = tl.log
# SCM_PYTHON_SH_HOME = tcontext.get_field(os.environ, "SCM_PYTHON_SH_HOME", os.path.abspath(os.path.join("~", ".scm_python")))
SCM_PYTHON_SH_HOME = os.path.join(os.path.expanduser("~"), ".scm_python")
if "SCM_PYTHON_SH_HOME" in os.environ:
    SCM_PYTHON_SH_HOME = os.path.join(os.environ.get("SCM_PYTHON_SH_HOME"), "..")  # type: ignore
SCM_PYTHON_SH_HOME = os.path.abspath(SCM_PYTHON_SH_HOME)
SSZ_ROOT_CA = os.environ.get("SSZ_ROOT_CA")
SSZ_PYTHON_ROOT_CA = ""
CERTIFICATE_BUNDLE = certifi.where()
INSTALLATION_FOLDER = SCM_PYTHON_SH_HOME
target_path = f"{INSTALLATION_FOLDER}/sh/etc"
HOST_FOLDER = os.path.abspath(os.path.join(INSTALLATION_FOLDER, socket.gethostname()))
# 如果没有本机的Override,启用公众模板主机win-8001
# 所以调用顺序为hostname -> win-8001 -> sh, sh里只包含模板,且必须以sample命名, runtime里必须要以runtime命名
if not os.path.exists(HOST_FOLDER):
    HOST_FOLDER = os.path.abspath(f"{INSTALLATION_FOLDER}/{TEMPEST_HOST_FOLDER}")
sample_target_file = f"{target_path}/code_target.sample.txt"
runtime_target_file = tf.override(
    sample_target_file, f"{HOST_FOLDER}/etc/code_target.runtime.txt"
)

# 如果不存在runtime,就用sample文件替换
sample_install_file = f"{target_path}/install.sample.yaml"
runtime_install_file = tf.override(
    sample_install_file, f"{HOST_FOLDER}/etc/install.runtime.yaml"
)

sample_eclipse_file = f"{target_path}/eclipse.sample.yaml"
runtime_eclipse_file = tf.override(
    sample_eclipse_file, f"{HOST_FOLDER}/etc/eclipse.runtime.yaml"
)

sample_template_file = f"{target_path}/template.sample.yaml"
runtime_template_file = tf.override(
    sample_template_file, f"{HOST_FOLDER}/etc/template.runtime.yaml"
)
if tl.PRINT_DETAILS:
    log.info(f"runtime_install_file is {runtime_install_file}")
    log.info(f"runtime_eclipse_file is {runtime_eclipse_file}")
    log.info(f"runtime_template_file is {runtime_template_file}")
    log.info(f"SCM_PYTHON_SH_HOME is {SCM_PYTHON_SH_HOME}")
    log.info(f"HOST_FOLDER is {HOST_FOLDER}")
CACHED_YAML_FILE = {}

"""
    扩展文件,如果大量的host是相同的runtime.yaml,可以着这个文件里指定引用到公共的host
"""
__EXTENSIONS_FILE = f"{HOST_FOLDER}/etc/__lib_extends.txt"
__EXTENSIONS = tf.properties(__EXTENSIONS_FILE)
__EXTENSIONS_OVERRIDE = False
EIUM_COMPILE_VERSION = "compile.version"
EIUM_VERSION = "eium.version"
EIUM_JDK_VERSION = "build.jdk.version"
EIUM_JDK_ROOT = "build.jdk.root"
EIUM_ANT_VERSION = "build.ant.version"
EIUM_MAVEN_VERSION = "build.maven3.version"
EIUM_MAVEN_ROOT = "build.m3.root"
EIUM_MAVEN_SETTINGS = "build.m3.settings"
EIUM_THIRDPARTYROOT = "eium.third_party.root"
EIUM_CLEAN_BUILD = "rm -rf build"
EIUM_DEFAULT_BUILD_CMD = (
    "ant build jar build.test" if is_linux else "call ant build jar build.test"
)
EIUM_DEFAULT_WAR_BUILD_CMD = (
    "ant build war package" if is_linux else "call ant build war package"
)
FAILURE_EXIT = "if %errorlevel% gtr 0 exit /B 1"
FAILURE_EXIT_IN_PWSH = "if ($LASTEXITCODE -gt 0) { exit 1 }"
EXIT_IF_ERROR = (
    "[ $? -eq 0 ] || exit 1" if is_linux else "if %errorlevel% gtr 0 exit /B 1"
)
__EXTENSION_ATTR = "<<*"
"""
    追加数组到自身的对象中,一般用于继承后的追加
    for example, <<*: snap10.1,<<*_mavens:['a','b','c']
    extend from snap10.1, then append ['a','b','c'] into mavens named array
"""
__APPEND_ARRAY_PREFIX = "<<*_"
"""
    删除已有的对象
    for example, <<*: snap10.1,>>*:['a','b','c']
    extend from snap10.1, then remove by the attribute in ['a','b','c']
    for example, <<*: snap10.1,>>*:[ {"name": 'a'} ]
    extend from snap10.1, then remove by the attribute in name == 'a'
"""
__REMOVE_PREFIX = ">>*"
PING_LATENCY_SECONDS_IN_LAN = 0.005
PING_LATENCY_MILLS_IN_LAN = 5

GATEWAY_HPE = "10.43.172.1"
GATEWAY_LANXI = "192.168.4.1"
GATEWAY_SH = "192.168.50.236"
GATEWAY_LINGANG = "192.168.10.1"
GATEWAY_HPE_PRIVATE = "192.168.58.1"
GATEWAY_NSB_PRIVATE = "10.243.136.1"
GATEWAY_SH_TO_HPE = "192.168.50.68"
GATEWAY_LANXI_TO_SH = "192.168.4.133"
GATEWAY_LINGANG_TO_SH = "192.168.10.109"
GATEWAY_HPE_TO_PRIVATE = "10.43.173.40"

WORK_ENV_HPE = "hpe"
WORK_ENV_HPE_PRIVATE = "hpe-private"
WORK_ENV_SH = "home"
WORK_ENV_LINGANG = "shlg"
WORK_ENV_LANXI = "lanxi"
WORK_ENV_NSB = "nsb"

GATEWAYS_FOR_WORK_ENV = {
    WORK_ENV_HPE: GATEWAY_HPE,
    WORK_ENV_HPE_PRIVATE: GATEWAY_HPE_PRIVATE,
    WORK_ENV_SH: GATEWAY_SH,
    WORK_ENV_LINGANG: GATEWAY_LINGANG,
    WORK_ENV_LANXI: GATEWAY_LANXI,
}

VPN_FOR_WORK_ENV = {
    WORK_ENV_HPE: GATEWAY_HPE_TO_PRIVATE,
    WORK_ENV_NSB: GATEWAY_NSB_PRIVATE,
    WORK_ENV_HPE_PRIVATE: GATEWAY_HPE_PRIVATE,
    WORK_ENV_SH: GATEWAY_SH_TO_HPE,
    WORK_ENV_LINGANG: GATEWAY_LINGANG_TO_SH,
    WORK_ENV_LANXI: GATEWAY_LANXI_TO_SH,
}


def get_exit_if_error(shell_language_type: str):
    return FAILURE_EXIT_IN_PWSH if "pwsh" == shell_language_type else EXIT_IF_ERROR


def ca_content(app="ssz"):
    return (
        root_ca_content()
        if app == "ssz"
        else "".join(tf.readlines(SSZ_ROOT_CA, allowStrip=False))
    )


def root_ca_content():
    return "".join(tf.readlines(SSZ_PYTHON_ROOT_CA, allowStrip=False))


from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath


def filename_from_url(url: str) -> str:
    """
    从 URL 获取最后的文件名（若 URL 以 / 结尾或没有文件名，返回空字符串）。
    会去掉 query/fragment 并对 percent-encoding 解码。
    """
    parsed = urlparse(url)
    path = parsed.path or ""
    name = PurePosixPath(path).name  # 兼容 POSIX 路径分隔
    return unquote(name)


def check_or_create_ca_temp_dir_and_download():
    global SSZ_ROOT_CA
    global SSZ_PYTHON_ROOT_CA
    if not SSZ_ROOT_CA or not os.path.exists(SSZ_ROOT_CA):
        SSZ_ROOT_CA = download_to_temp_dir(
            "http://192.168.50.246:39002/tools/win/sszRootCA.crt"
        )
    if not SSZ_PYTHON_ROOT_CA or not os.path.exists(SSZ_PYTHON_ROOT_CA):
        SSZ_PYTHON_ROOT_CA = download_to_temp_dir(
            "http://192.168.50.246:39002/tools/win/sszPythonRootCA.crt"
        )


def download_to_temp_dir(url: str, folder="SSZ_ROOT_CA"):
    temp_dir = tempfile.gettempdir()  # 获取系统临时目录路径
    target_dir = os.path.join(temp_dir, folder)  # 目标临时目录
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    base_file_name = filename_from_url(url)
    download_file_path = os.path.join(target_dir, base_file_name)
    if not os.path.exists(download_file_path):
        response = requests.get(url, verify=False)
        with open(download_file_path, "wb") as file:
            file.write(response.content)
    return download_file_path


check_or_create_ca_temp_dir_and_download()


def print_system():
    log.info(f"runtime_install_file is {runtime_install_file}")
    log.info(f"runtime_eclipse_file is {runtime_eclipse_file}")
    log.info(f"runtime_template_file is {runtime_template_file}")
    print("SCM_PYTHON_SH_HOME", SCM_PYTHON_SH_HOME)
    print("INSTALLATION_FOLDER", INSTALLATION_FOLDER)
    print("__EXTENSIONS_FILE", __EXTENSIONS_FILE)
    print("__EXTENSIONS", __EXTENSIONS)
    # print("CACHED_YAML_FILE", CACHED_YAML_FILE)
    print("SSZ_ROOT_CA", SSZ_ROOT_CA)


def termainal_echo_warning(cmd_line: str):
    return (
        f"echo $(tput bold)$(tput -Txterm setaf 3)$(tput -Txterm setab 0){cmd_line}$(tput sgr0)"
        if is_linux
        else f"echo {cmd_line}"
    )


def termainal_echo_error(cmd_line: str):
    return (
        f"echo $(tput bold)$(tput -Txterm setaf 1){cmd_line}$(tput sgr0)"
        if is_linux
        else f"echo {cmd_line}"
    )


def exec_with_failure_exit(cmds, cmd_line: str):
    cmds.append(cmd_line)
    echo_error_cmd_line = termainal_echo_warning(cmd_line)
    cmds.append(
        f"__error_code=$?;[ $__error_code -eq 0 ] || {echo_error_cmd_line};[ $__error_code -eq 0 ] || exit 1"
        if is_linux
        else f"if %errorlevel% gtr 0 {echo_error_cmd_line} && exit /B 1"
    )


def load_from_yaml(filename: str):
    # 如果文件不存在直接返回空集合,不应该返回其它假定的文件
    build_mapping = {}
    if not os.path.exists(filename):
        return build_mapping
    if tl.PRINT_DETAILS:
        log.info(f"load yaml file from {filename}")
    with open(filename, "r+", encoding="utf-8") as fo:
        build_mapping = yaml.load(fo.read(), Loader=yaml.FullLoader)
    return build_mapping


def load_from_cached_yaml(filename: str):
    if filename not in CACHED_YAML_FILE:
        CACHED_YAML_FILE[filename] = load_from_yaml(filename)
    return CACHED_YAML_FILE[filename]


# please don't use replace_env_variables in the function
def load_base_install_yaml():
    return deep_merge_yaml(sample_install_file, runtime_install_file)


def load_yaml_file_with_variable(sample_file: str):
    return replace_env_variables(load_from_yaml(sample_file))


def load_install_yaml(module: str = "", env_context: dict = None, skip_replace=False):  # type: ignore
    config = deep_merge_yaml(sample_install_file, runtime_install_file, module)
    if skip_replace:
        return config
    if env_context:
        tcontext.replace_object(env_context, config)
        return config
    return replace_env_variables(config)


def load_template_yaml(module: str = ""):
    """
    返回template定义中的一段配置
    module: 子模块名字,例如python,maven
    """
    return deep_merge_yaml(sample_template_file, runtime_template_file, module)


def list_solution_names(module: str, search_path: str, include_search_path=""):
    """
    返回模板子模块中某个查询路径下的一层子路径
    module: 子模块名字,例如python,maven
    search_path: 搜索子路径,例如misc
    include_search_path: 是否包含search_path到结果中
    """
    return [
        f"{include_search_path}/{key_name}" if include_search_path else key_name
        for key_name in tcontext.load_item(
            load_template_yaml(module), search_path
        ).keys()
    ]


def load_eclipse_yaml(module: str = ""):
    log.info(f"load yaml from {sample_eclipse_file}/{runtime_eclipse_file}")
    return replace_env_variables(
        deep_merge_yaml(sample_eclipse_file, runtime_eclipse_file, module)
    )


"""
    本方法支持__lib_extends.txt
"""


def deep_merge_yaml_search_all_yaml_file_handler(
    extend_yaml_file: str, module_name: str
):
    folder = os.path.dirname(extend_yaml_file)
    # print(
    #     "---deep_merge_yaml_search_all_yaml_file_handler 1",
    #     extend_yaml_file,
    #     module_name,
    # )
    result = [extend_yaml_file]
    for file_name in tf.listdir(os.path.join(INSTALLATION_FOLDER, folder, module_name)):
        # print("---deep_merge_yaml_search_all_yaml_file_handler 2", file_name)
        if file_name.endswith(".yaml"):
            result.append(os.path.join(folder, module_name, file_name))
    return result


def deep_merge_yaml(sample_file: str, runtime_file: str, module: str = ""):
    if tl.PRINT_DETAILS:
        log.info(f"start merge yaml from {sample_file}, {runtime_file}, {module}")
    file_name = os.path.basename(sample_file)
    foo = file_name.split(".")
    module_name = f"{module}.{foo[0]}" if module else foo[0]
    config = __load_generic_yaml(sample_file, module)
    if module_name in __EXTENSIONS:
        for extend_yaml_file in __EXTENSIONS[module_name].split(","):
            for extend_yaml_file in deep_merge_yaml_search_all_yaml_file_handler(
                extend_yaml_file, module_name
            ):
                config = tcontext.deep_merge(
                    config,
                    __load_generic_yaml(
                        os.path.join(INSTALLATION_FOLDER, extend_yaml_file)
                    ),
                )
    # Known Issues: ssz, 2025.10.29, 检查是否有runtime存在于本机配置目录, 如果是override extension, 此处就不能读取本机的配置了
    if not __EXTENSIONS_OVERRIDE:
        if module and (
            module_runime_file := get_exists_runtime_module(sample_file, module)
        ):
            # print("---deep_merge_yaml", sample_file, module)
            if tl.PRINT_DETAILS:
                log.info(f"found runtime yaml file {module_runime_file}")
            for extend_yaml_file in deep_merge_yaml_search_all_yaml_file_handler(
                module_runime_file, module_name
            ):
                config = tcontext.deep_merge(
                    config, __load_generic_yaml(extend_yaml_file)
                )
        else:
            config = (
                config
                if sample_file == runtime_file
                else tcontext.deep_merge(
                    config, __load_generic_yaml(runtime_file, module)
                )
            )
    deep_merge_parse_extension(config, config)
    if tl.PRINT_DETAILS:
        log.info(f"merge end")
    return config


def get_exists_runtime_module(sample_file: str, module: str):
    filename = os.path.basename(sample_file)
    base_modue_name = filename.split(".")[0]
    yaml_file_name = os.path.join(
        HOST_FOLDER, "etc", f"{module}.{base_modue_name}.runtime.yaml"
    )
    return yaml_file_name if os.path.exists(yaml_file_name) else ""


def deep_merge_dict_parse_extension(
    parent_config: dict, config: dict, key_name: str = ""
):
    while __EXTENSION_ATTR in config:
        extension_name = config.pop(__EXTENSION_ATTR)
        before_replace_key_value = key_name in config and config[key_name]
        extension_config = tcontext.load_item(parent_config, extension_name)
        if not extension_config:
            print(
                f"---------please check the configuration, {extension_name} = {extension_config}",
                parent_config,
            )
        config.update(
            tcontext.deep_merge(
                tcontext.load_item(parent_config, extension_name), config
            )
        )
        if before_replace_key_value:
            config[key_name] = before_replace_key_value
    # 处理数组append
    append_array = [
        key_item
        for key_item in config.keys()
        if key_item.startswith(__APPEND_ARRAY_PREFIX)
    ]
    for key_item in append_array:
        key_value = config.pop(key_item)
        target_array_name = key_item.replace(__APPEND_ARRAY_PREFIX, "")
        target_array = (
            config[target_array_name] if target_array_name in config else None
        )
        if target_array and tcontext.is_list(target_array):
            if tcontext.is_list(key_value):
                target_array += key_value
            else:
                log.warning(f"{key_item} is not list type, skip it")
        else:
            log.warning(
                f"{target_array_name} is not found or not array type, skip {key_item}"
            )
    if __REMOVE_PREFIX in config:
        print(config)
    for key_item, key_value in config.items():
        deep_merge_parse_extension(config, key_value)


def list_2_dict_with_key(config: list, key_name: str) -> dict:
    parent_config = {}
    for key_value in config:
        if key_name not in key_value:
            print(f"{key_name} not in key_value, it is required", key_value)
            log.error(f"{key_name} not in key_value, it is required")
        parent_key_name = key_value[key_name]
        parent_config[parent_key_name] = key_value
    return parent_config


def deep_merge_list_parse_extension(parent_config: object, config: list):
    key_name: str = len(config) > 0 and tcontext.is_dict(config[0]) and tcontext.key_provider_in_dict(config[0])  # type: ignore
    parent_config = key_name and list_2_dict_with_key(config, key_name) or parent_config
    want_remove_attributes: list[str] = []
    for key_value in config:
        if key_name and key_value and key_value[key_name] == __REMOVE_PREFIX:
            want_remove_attributes = key_value["value"]
            log.info(f"---found the remove prefix " + str(key_value))
            config.remove(key_value)
        else:
            deep_merge_parse_extension(parent_config, key_value, key_name)
    if want_remove_attributes:
        for key_value in config:
            child_key_name_value = key_value[key_name]
            if child_key_name_value in want_remove_attributes:
                config.remove(key_value)


"""
当前只支持一层往上extensions, parent_config和config只允许差一层
"""


def deep_merge_parse_extension(
    parent_config: object, config: Union[dict, list], key_name: str = ""
) -> bool:
    if tcontext.is_dict(config):
        deep_merge_dict_parse_extension(parent_config, config, key_name)  # type: ignore
    elif tcontext.is_list(config):
        deep_merge_list_parse_extension(parent_config, config)  # type: ignore
    return True


def envs_interface_main():
    build_mapping = load_install_yaml()
    net_interfaces = tcontext.load_item(build_mapping, "envs/netInterfaces")
    return net_interfaces[0] if net_interfaces else None


def env_in_install():
    return replace_env_variables(tcontext.load_item(load_base_install_yaml(), "envs"))


def route_in_install():
    build_mapping = load_install_yaml()
    return replace_env_variables(tcontext.load_item(build_mapping, "envs/route"))


"""
ping 192.168.58.1
0.005983591079711914 15.657901763916016
"""


def work_environment():
    ip_pools = GATEWAYS_FOR_WORK_ENV
    #  通过ping值大小来判断是否为那个本地网络
    for key in ip_pools.keys():
        ip = ip_pools[key]
        # 如果不加ttl=63返回s有时候0.015返回0.0,
        # 在临港有时候ping latency会>5ms, 所以需要确认3次
        ping_num = 3
        for start_count in range(ping_num):
            ping_latency = ping_workaround(ip)
            log.info(
                f"ping {key}:{ip} latency is {ping_latency} and type is {type(ping_latency)}"
            )
            if 0.0 == ping_latency:
                raise Exception(f"0.0 is impossible in ping as millseconds output")
            # if float 0.0 means False
            # if ping_latency and ping_latency < PING_LATENCY_MILLS_IN_LAN:
            if (
                isinstance(ping_latency, float)
                and ping_latency < PING_LATENCY_MILLS_IN_LAN
            ):
                return key
            elif not isinstance(ping_latency, float):
                break
    return WORK_ENV_SH


"""
有时候10+返回0.0
ping 192.168.50.236
15.657901763916016
"""


def ping_workaround(ip: str) -> float:
    while (ping_latency := ping(ip, timeout=2, unit="ms", ttl=63)) == 0.0:
        log.info(f"retry ping {ip} because latency is 0.0")
    return ping_latency  # type: ignore



def is_lanxi_work_environment(environment=None):
    if not environment:
        environment = work_environment()
    return WORK_ENV_LANXI == environment


def is_home_work_environment(environment=None):
    if not environment:
        environment = work_environment()
    return WORK_ENV_SH == environment


def is_hpe_work_environment(environment=None):
    if not environment:
        environment = work_environment()
    return WORK_ENV_HPE == environment


def is_hpe_private_work_environment(environment=None):
    if not environment:
        environment = work_environment()
    return WORK_ENV_HPE_PRIVATE == environment


def append_dynamic_env_into_context(context: dict):
    install_sample_yaml_config = load_from_cached_yaml(sample_install_file)
    dynamic_env_dict = tcontext.load_item(install_sample_yaml_config, f"envs/dynamic")
    if dynamic_env_dict:
        for dynamic_env_name, env_path_list in dynamic_env_dict.items():
            cloned_env_path_list = [
                tf.USER_PROFILE if env_path_item == "~" else env_path_item
                for env_path_item in env_path_list
            ]
            search_workspace_list = []
            for env_path_item in env_path_list:
                if "*" not in env_path_item:
                    search_workspace_list.append(cloned_env_path_list.pop(0))
                else:
                    break
            search_workspace = os.path.join(*search_workspace_list)
            search_keyword = "/".join(cloned_env_path_list)
            matched_folder = (
                tf.search(search_workspace, search_keyword)
                if len(search_keyword) > 0
                else [search_workspace]
            )
            if len(matched_folder) > 0:
                context[f"env:{dynamic_env_name}"] = matched_folder[0]
            else:
                if tl.PRINT_DETAILS:
                    log.error(
                        f"{dynamic_env_name} is not found in {search_workspace}/{search_keyword}"
                    )


def create_env_context():
    if "create_env_context" not in CACHED_YAML_FILE:
        context = {}
        # load from environment variable in os, by cli env to check it
        for env_name, env_value in os.environ.items():
            if os.environ.get(env_name):
                context[f"{env_name.upper()}"] = os.path.abspath(
                    os.environ.get(env_name)  # type: ignore
                )  # type: ignore
            context[f"env:{env_name.upper()}"] = env_value
        # load dynamic environment, configurated in install.sample.yaml
        append_dynamic_env_into_context(context)
        credential_env_file = os.path.join(tf.USER_PROFILE, "credential.env")
        # load from environment variable in credential.env, host in the user home
        if os.path.exists(credential_env_file):
            for credential_item in tf.readlines(credential_env_file):
                env_name, env_value = credential_item.split("=")
                context[f"env:{env_name.upper()}"] = env_value
        env_file_context = {}
        __create_env_file_context(env_file_context)
        tcontext.replace_object(context, env_file_context)
        CACHED_YAML_FILE["create_env_context"] = {**context, **env_file_context}
    return {**CACHED_YAML_FILE["create_env_context"]}


def replace_env_variables(config: Union[dict, None]):
    tcontext.replace_object(create_env_context(), config)
    return config


def __create_env_file_context_put_into_context(
    context: dict, root_path: str, config: Union[dict, None]
):
    if not config:
        return
    for key_item, key_value in config.items():
        root_path_tmp = f"{root_path}/{key_item}"
        if tcontext.is_dict(key_value):
            __create_env_file_context_put_into_context(
                context, root_path_tmp, key_value
            )
        elif tcontext.is_list(key_value):
            log.warning(f"not support for list in {root_path_tmp}")
        else:
            context[f"env_file:{root_path_tmp}"] = key_value


def __create_env_file_context(context: dict):
    if tl.PRINT_DETAILS:
        log.info(f"__create_env_file_context to load base install yaml")
    build_mapping = load_base_install_yaml()
    root_path = "envs/env"
    __create_env_file_context_put_into_context(
        context, root_path, tcontext.load_item(build_mapping, root_path)
    )


def __lookupEIUMBranch(branch: str, eium: object):
    for branchItem in tcontext.load_item(eium, "branches"):  # type: ignore
        branchAlias = branchItem["name"]
        if branchAlias == branch or branchAlias.startswith(branch + "_"):
            currentPath = os.path.abspath(".")
            index = currentPath.find("\\siu")
            siuRoot = currentPath[0:index] if index > -1 else currentPath
            return siuRoot, eium, branchItem


def __lookupRtcBranch(module: str, version: str, reactstudio: object):
    # rtcRoot = branchItem['web'][0: branchItem['web'].find('\\dev\\')]
    rtcRoot = tf.left_folder_by_first(os.path.abspath("."), "cmbuild/build.xml", False)
    # version = __parse_rtc_version(rtcRoot)
    moduleAndVersion = f"{module}{version}"
    log.info(f"{moduleAndVersion}")
    branchItem = tcontext.load_item(reactstudio, f"branches/{moduleAndVersion}")  # type: ignore
    return rtcRoot, reactstudio, branchItem


def __parse_rtc_version(rtcRoot: str):
    version = "10.1"
    for line in tf.readlines(os.path.join(rtcRoot, "cmbuild", "build.xml")):
        if "<iummodule" in line:
            flag = 'version="'
            version = line[line.find(flag) + len(flag) :]
            version = version[0 : version.find('"')]
            foo = version.split(".")
            version = f"{foo[0]}.{foo[1]}"
            break
    return version


def lookupRtcStudioBranch(branch: str):
    build_mapping = load_install_yaml("build")
    rtcstudio = tcontext.load_item(build_mapping, "install/products/rtcStudio")
    rtcstudioRoot = tcontext.load_item(rtcstudio, "root")
    for branch_item in tcontext.load_item(rtcstudio, "modules"):  # type: ignore
        branch_alias = branch_item["name"]
        if branch_alias == branch or branch_alias.endswith(branch):
            return rtcstudioRoot, rtcstudio, branch_item


def ms_lookup_branch(branch: str):
    if not branch:
        branch = "1.1.0"
    return lookup_branch_by_type(branch, "install/products/ms")


"""
    return
    rtcRoot, object in build, branch item
"""


def lookupRtcBranch(
    module: str = "rtc", version: str = "10.1", product: str = "reactstudio"
):
    return __lookupRtcBranch(
        module,
        version,
        tcontext.load_item(load_install_yaml("build"), f"install/products/{product}"),
    )


def lookupEIUMBranch(branch: str):
    return __lookupEIUMBranch(
        branch, tcontext.load_item(load_install_yaml("build"), "install/products/eium")
    )


def lookupEIUMEclipseBranch(branch: str):
    return __lookupEIUMBranch(branch, tcontext.load_item(load_eclipse_yaml(), "ops"))


def lookup_project_in_eclipse(project: str):
    return tcontext.load_item(load_eclipse_yaml(), project)


def load_yaml_from_install(
    ypath: str, module: str = "", env_context: dict = None, skip_replace=False  # type: ignore
):
    return tcontext.load_item(
        load_install_yaml(module, env_context, skip_replace), ypath
    )


def git_repo_home():
    return os.path.abspath(os.path.join(os.getenv("SH_HOME"), ".."))  # type: ignore


def sh_home():
    return os.path.abspath(os.getenv("SH_HOME"))  # type: ignore


def common_home():
    return os.path.abspath(git_repo_home(), "common")  # type: ignore


"""
Arguments:
    remote: root@ssz1://sh/app
Attributes:
    ('root', None, 'ssz1', '/sh/app')
"""


def parse_remote_path(remote: str):
    usr = "root"
    passwd = None
    if "@" in remote:
        usr = remote[0 : remote.find("@")]
        remote = remote[remote.find("@") + 1 :]
    host = remote[0 : remote.find(":")]
    remotePath = remote[remote.find(":") + 1 :].replace("//", "/")
    for authorization in load_yaml_from_install("sshcli/authorizations"):  # type: ignore
        # alias有可能没有配置
        alias = authorization["alias"] if "alias" in authorization else ""
        if usr == authorization["usr"] and (
            host in authorization["host"] or host == alias
        ):
            passwd = authorization["passwd"] if "passwd" in authorization else None
            if host == alias:
                host = authorization["host"][0]
            break
    return usr, passwd, host, remotePath


def lookup_match_branch_from_all_definitions(
    all_branche_definitions: list, branch: str
):
    for branch_item in all_branche_definitions:
        branch_alias = branch_item["name"]
        if eium_branch_alias_match(branch, branch_alias):
            return branch_item
    log.error(f"no any branch is found for {branch}")
    sys.exit(1)


# def load_branch_with_extension(all_branche_definitions: list, branch_item: dict):
#     if 'extend' not in branch_item:
#         return branch_item
#     extended_branch_item = tcontext.deep_merge(load_branch_with_extension(all_branche_definitions
#             , lookup_match_branch_from_all_definitions(all_branche_definitions, branch_item['extend'])), branch_item)
#     del extended_branch_item['extend']
#     return extended_branch_item


def lookup_branch_by_type(
    branch, web_app_type, root_flag_folder=None, yaml_context=None
):
    branch = branch.upper()
    build_mapping = yaml_context if yaml_context else load_install_yaml("build")
    eium = replace_env_variables(tcontext.load_item(build_mapping, web_app_type))
    siu_root: str = None  # type: ignore
    if root_flag_folder:
        root_flag_folder_str = f"/{root_flag_folder}"
        current_path = tf.linuxPath(os.path.abspath("."))
        if not (
            current_path.endswith(root_flag_folder_str)
            or current_path.find(root_flag_folder_str) > 0
        ):
            error_message = f"no folder[{root_flag_folder}] in {current_path}"
            log.error(error_message)
            raise Exception(error_message)
        siu_root = current_path[0 : current_path.find(root_flag_folder_str)]
        siu_root = os.path.abspath(siu_root)
    match_branch_items = []
    all_branche_definitions = tcontext.load_item(eium, "branches")
    if not all_branche_definitions:
        raise Exception("")
    # branch extend is required
    for branch_item in all_branche_definitions:
        branch_alias = branch_item["name"]  # type: ignore
        if eium_branch_alias_match(branch, branch_alias):
            match_branch_items.append(branch_item)
    if match_branch_items:
        match_branch_items = [
            branch_item
            for branch_item in match_branch_items
            if branch_item["name"] == branch
        ] + match_branch_items
        branch_item: object = match_branch_items[0]
        log.info(
            f'input branch name {branch} is match defined branch alias {branch_item["name"]}'  # type: ignore
        )
        return (
            (siu_root, eium, branch_item) if root_flag_folder else (eium, branch_item)
        )
    log.error(f"input {branch} is not defined in install.runtime.yaml")


def eium_init_build_context(jdk_root):
    build_context = {}
    build_context[EIUM_JDK_ROOT] = jdk_root
    return build_context


def eium_find_branch_build_context():
    build_context = {}
    siu_root = tf.left_folder_by_first(os.path.abspath("."), "siu/build.xml")
    eium_version_patchname = None
    eium_old_version_file = os.path.join(siu_root, "siu", "eiumversion.txt")
    # compile.version
    for line in tf.readlines(os.path.join(siu_root, "siu", "core", "build-share.xml")):
        if re.search(rf'^\s*<property name="{EIUM_COMPILE_VERSION}"', line):
            build_context[EIUM_COMPILE_VERSION] = tf.xml_properties(line)["value"]
            break
    if os.path.exists(eium_old_version_file):
        build_context[EIUM_VERSION] = tf.readlines(eium_old_version_file)[0].strip()
        return build_context
    # eium.version
    for line in tf.readlines(os.path.join(siu_root, "siu", "branch.properties")):
        if line and (
            line.startswith(EIUM_VERSION)
            and ".release" in line
            or line.startswith("eium.version.patchname")
            or line.startswith("build.")
        ):
            tmp = line.split("=")
            if line.startswith("build."):
                build_context[tmp[0]] = tmp[1]
            elif tmp[0] == "eium.version.patchname":
                eium_version_patchname = tmp[1]
            else:
                build_context[EIUM_VERSION] = tmp[1]
    if eium_version_patchname:
        build_context[EIUM_VERSION] += eium_version_patchname
    return build_context


# branch have two format
# 1. 10.6.0, 10.5.1, 9.0FP01, 9.0FP02
# 2. 106=10.6.0,105=10.5, 90=9.0, 91=9.0FP01, 92=9.0FP02
def eium_branch_alias_match(branch, branch_alias):
    if branch_alias == branch:
        return True
    eium_version_alias_arrays = branch_alias.split(".")
    branch = branch.replace(".", "")
    index = 0
    while branch and index < len(eium_version_alias_arrays):
        split_item = eium_version_alias_arrays[index]
        if "x" == split_item:
            return True
        elif "0FP01" == split_item:
            split_item = "1"
        elif "0FP02" == split_item:
            split_item = "2"
        if branch.startswith(split_item):
            branch = branch.replace(split_item, "", 1)
        else:
            return False
        index = index + 1
    return True


def eium_parse_properties_file(properties_file, *attributes) -> object:
    contexts = {}
    for line in tf.readlines(properties_file):
        if line and "=" in line:
            foo = line.split("=")
            attribute = foo[0]
            attribute_value = foo[1]
            # TODO support regexp in attributes
            if attribute in attributes:
                contexts[attribute] = attribute_value
    return contexts


def set_interface(cmds, adaptor, dns_list, metric=""):
    if not dns_list:
        return
    cmds.append(f'netsh interface ipv4 set interface "{adaptor}"{metric}')
    for key_item, dns_item in enumerate(dns_list):
        if key_item:
            cmds.append(
                f'netsh interface ipv4 add dnsserver name="{adaptor}" address={dns_item} index={key_item + 1}'
            )
        else:
            cmds.append(f'netsh interface ip set dns "{adaptor}" static {dns_item}')


"""
parse apps\\web\\build.properties
"""


def eium_get_web_app_modules(siu_root, excludings) -> list:
    all_web_app_modules: list = eium_parse_properties_file(
        os.path.join(siu_root, "siu", "apps", "web", "build.properties"), "projects"  # type: ignore
    )["projects"].split(",")
    if excludings:
        for module in excludings:
            if module in all_web_app_modules:
                all_web_app_modules.remove(module)
    return all_web_app_modules


def eium_jdk_switch(build_context):
    java_home = "JAVA_HOME=" + build_context[EIUM_JDK_ROOT]
    return java_home if is_linux else f"SET {java_home}"


def eium_m3_switch(build_context):
    m3_home = "M3_HOME=" + build_context[EIUM_MAVEN_ROOT]
    return m3_home if is_linux else f"SET {m3_home}"


def eium_ant_path(build_context):
    if is_linux:
        return "$THIRDPARTYROOT/3rdParty/apache-ant-" + build_context[EIUM_ANT_VERSION]
    return "%THIRDPARTYROOT%\\3rdParty\\apache-ant-" + build_context[EIUM_ANT_VERSION]


def eium_iumant_path(build_context):
    if is_linux:
        return "$THIRDPARTYROOT/3rdParty/iumant-1.0"
    return "%THIRDPARTYROOT%\\3rdParty\\iumant-1.0"


def __override_file_before_build(siu_root, eium, branch_item):
    override_mapping = tcontext.merge_design_runtime(eium, branch_item, "override")
    if not override_mapping:
        return
    for target_item in override_mapping:
        target_folder = target_item["target"]
        for target_file in target_item["froms"]:
            tf.copy(target_file, os.path.abspath(siu_root + "/" + target_folder))


def override_file_after_build(siu_root, eium, branch_item, cmds):
    override_mapping = tcontext.merge_design_runtime(eium, branch_item, "override")
    if not override_mapping:
        return
    for target_item in override_mapping:
        target_folder = target_item["target"]
        for target_file in target_item["froms"]:
            target_file_name = os.path.basename(target_file)
            target_abs_file = os.path.abspath(
                siu_root + "/" + target_folder + "/" + target_file_name
            )
            cmds.append(f"git checkout -- {target_abs_file}")


def eium_disable_antivirus(cmds):
    if not is_linux:
        cmds.append("powershell Set-MpPreference -DisableRealtimeMonitoring $true")


def eium_start_ant_task(siu_root, eium, branch_item):
    build_context = eium_find_branch_build_context()
    __override_file_before_build(siu_root, eium, branch_item)
    cmds = []
    prefixCmd = tcontext.merge_design_runtime(eium, branch_item, "prefixCmd")
    if prefixCmd:
        cmds.append(prefixCmd)
    if not EIUM_JDK_VERSION in build_context:
        build_context[EIUM_JDK_VERSION] = tcontext.merge_design_runtime(
            eium, branch_item, EIUM_JDK_VERSION
        )
    if not EIUM_ANT_VERSION in build_context:
        build_context[EIUM_ANT_VERSION] = tcontext.merge_design_runtime(
            eium, branch_item, EIUM_ANT_VERSION
        )
    if not EIUM_JDK_ROOT in build_context:
        jdk_folder = tcontext.merge_design_runtime(eium, branch_item, EIUM_JDK_ROOT)
        if is_linux:
            jdk_folder = f"{jdk_folder}-linux"
        build_context[EIUM_JDK_ROOT] = jdk_folder
    if is_linux:
        cmds += [
            eium_jdk_switch(build_context),
            "DEVROOT=" + siu_root,
            "ANT_HOME=" + eium_ant_path(build_context),
            "IUMANT_HOME=" + eium_iumant_path(build_context),
            "PATH=$JAVA_HOME/bin:$ANT_HOME/bin:$IUMANT_HOME:$PATH",
            "export DEVROOT JAVA_HOME ANT_HOME PATH",
        ]
    else:
        cmds += [
            eium_jdk_switch(build_context),
            "SET DEVROOT=" + siu_root,
            "SET ANT_HOME=" + eium_ant_path(build_context),
            "SET IUMANT_HOME=" + eium_iumant_path(build_context),
            "set PATH=%JAVA_HOME%\\bin;%ANT_HOME%\\bin;%IUMANT_HOME%;%PATH%",
        ]
    return cmds


def eium_start_java_task(cmds, build_context, eium=None, branch_item=None):
    cmds += [eium_jdk_switch(build_context)]
    if EIUM_MAVEN_ROOT in build_context:
        cmds += [eium_m3_switch(build_context)]
    if is_linux:
        cmds += [
            "PATH=$JAVA_HOME/bin:$M3_HOME/bin:$PATH",
            "export JAVA_HOME M3_HOME PATH",
            "export MAVEN_OPTS=-Duser.language=en",
        ]
    else:
        cmds += [
            "set PATH=%JAVA_HOME%\\bin;%M3_HOME%\\bin;%PATH%",
            "set MAVEN_OPTS=-Duser.language=en",
        ]


def list_trims(plugins: list):
    return [value for value in plugins if value]


def list_set(plugins: list):
    tmp_plugins = list(set(plugins))
    plugins.clear()
    plugins += tmp_plugins


def __load_generic_yaml(runtime_file, module=""):
    if module:
        foo = os.path.split(runtime_file)
        filename = f"{module}.{foo[1]}"
        return load_from_yaml(os.path.join(foo[0], filename))
    return load_from_yaml(runtime_file)


def override_extensions(module_name: str, yaml_file: str):
    __EXTENSIONS[module_name] = yaml_file
    global __EXTENSIONS_OVERRIDE
    __EXTENSIONS_OVERRIDE = True


def get_request_session():
    # Known issues: ssz, 2025.10.9, workaround to load .netrc and drop headers
    s = requests.Session()
    s.trust_env = False
    return s


def system_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
