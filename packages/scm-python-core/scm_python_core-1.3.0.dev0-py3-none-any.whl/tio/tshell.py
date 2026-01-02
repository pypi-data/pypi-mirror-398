import tlog.tlogging as tl
import io, os, subprocess, sys, re, platform
import time, signal
import locale
import threading
from .tfile import readlines
from typing import Callable, Union, Literal, Tuple

log = tl.log if hasattr(tl, "log") else None
# 是否保留生成的pipeline.bat文件
PERSERVE_PIPELINE = False


class TShell(object):
    def __init__(self):
        if log:
            log.debug("TShell init")


def signal_callback(singal_handler: Callable[..., None]):
    def signal_listener(signum, frame):
        singal_handler()

    signal.signal(signal.SIGINT, signal_listener)
    signal.signal(signal.SIGTERM, signal_listener)


def is_chinese(word):
    for ch in word:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def call_parent_process(*cmds):
    with open("call_parent_proccess.bat", "w", encoding="utf-8") as fw:
        content = "\n".join(cmds)
        if is_chinese(content):
            fw.write("chcp 65001\n")
        fw.write(content)


def call(*cmds: list[str]):
    if log:
        log.info("|".join(cmds))  # type: ignore
    # known issues: ssz,2025.9.26, 所有的日志里面都 包含 \n
    return [item.split() for item in os.popen("|".join(cmds)).readlines()]  # type: ignore


def call_cmd(cmd: str, encoding="utf-8"):
    if log:
        log.info(cmd)  # type: ignore
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding=encoding,
        # encoding=locale.getpreferredencoding(),
        errors="replace",
    )
    # Known issues: ssz,2025.9.26, 所有的日志里面都 不包含 \n
    commit_messages = result.stdout.splitlines()
    return commit_messages


def is_pwsh_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env pwsh")


def is_python_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env python")


def is_java_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env java")


def is_jsh_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env jsh")


def is_bash_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env bash")


def is_javascript_script(first_line: str):
    return first_line.startswith("#!/usr/bin/env node")


def get_shell_language_type(shell_line: str):
    foo = shell_line.splitlines()
    return (
        re.compile(r"#!/usr/bin/env\s+").sub("", foo[0]).strip()
        if foo[0].startswith("#!/usr/bin/env")
        else ""
    )


def is_enable_error_exit(shell_language_type: str):
    # is default shell, windows batch
    if not shell_language_type:
        return True
    if "pwsh" == shell_language_type:
        return True
    return False


def get_first_non_import_line_index(lines: list[str]):
    for line_index in range(1, len(lines)):
        line = lines[line_index]
        foo_line = line.strip()
        if foo_line and not foo_line.startswith("import "):
            # print("---get_first_non_import_line_index", foo_line, line_index)
            return line_index
    return 1


def try_catch_jsh_scripts(python_scripts: str):
    lines = python_scripts.splitlines()
    line_number = get_first_non_import_line_index(lines)
    line_index = line_number
    for line_index in range(line_number + 1, len(lines)):
        lines[line_index] = f"  {lines[line_index]}"
    lines.append("/exit")
    return "\n".join(lines[1:])


java_function_definition_pattern = r"""
    ^\s*                                 # 行首可有空格
    (public|private|protected|static|final|\s+)*   # 可选修饰符
    \s*                                   # 空格
    ([\w\<\>\[\]]+)                       # 返回类型（如 int, List<String>）
    \s+                                   # 空格
    (\w+)                                 # 方法名
    \s*                                   # 空格
    \(
        ([^\)]*)                          # 参数列表，不包含右括号
    \)
    \s*                                   # 空格
    (\{)?                                 # 可选 {，因为有时只写方法声明
"""


def try_catch_java_scripts(python_scripts: str, pipeline_file: str):
    lines = python_scripts.splitlines()
    line_number = get_first_non_import_line_index(lines)
    line_index = line_number
    # print("---try_catch_java_scripts", line_index)
    regex = re.compile(java_function_definition_pattern, re.VERBOSE)
    lines.insert(line_index, f"public class {os.path.splitext(pipeline_file)[0]}{{")
    for line_index in range(line_number + 1, len(lines)):
        line = lines[line_index]
        if not line.strip():
            continue
        # print(line_index, lines[line_index])
        if regex.match(line):
            lines[line_index] = f"static {line}"
        elif line.startswith("# main"):
            lines[line_index] = "public static void main(String[] args){"
        lines[line_index] = f"  {lines[line_index]}"
    # } catch (Exception e){
    #   e.printStackTrace();
    # }
    lines.append(
        """
    }
}
                 """,
    )
    return "\n".join(lines[1:])


def try_catch_python_scripts(python_scripts: str):
    lines = python_scripts.splitlines()
    line_index = 1
    lines.insert(line_index, "try:")
    for line_index in range(2, len(lines)):
        print(line_index, lines[line_index])
        lines[line_index] = f"  {lines[line_index]}"
    lines.append(
        """
except Exception as e:
  print(e, type(e))
  import traceback
  print(traceback.format_exc())
                 """,
    )
    return "\n".join(lines)


def try_catch_javascript_scripts(js_scripts: str):
    lines = js_scripts.splitlines()
    line_index = 1
    lines.insert(line_index, "try{")
    for line_index in range(2, len(lines)):
        print(line_index, lines[line_index])
        lines[line_index] = f"\t {lines[line_index]}"
    lines.append(
        """
} catch (err) {
  // 出错时执行这里
  console.error("捕获到异常:", err);
} finally {
  // 无论是否出错都会执行
  console.log("清理资源、关闭连接等");
}
                 """,
    )
    return "\n".join(lines)


def try_catch_powershell_scripts(powershell_scripts: str, pipeline_file: str):
    lines = powershell_scripts.splitlines()
    # 要先跳过param
    line_index = 1
    for index in range(1, len(lines) - 1, 1):
        line_str_striped = lines[index].strip()
        if "param(" == line_str_striped:
            line_index = index
        elif line_index >= 1:
            if ")" == line_str_striped:
                line_index = index + 1
                break
        elif line_str_striped:
            break

    lines.insert(line_index, "try {")
    for index in range(line_index + 1, len(lines) - 1, 1):
        lines[index] = f"\t{lines[index]}"
    lines.append(
        f"""
}}
finally {{
    Write-Host "正在清理..."
    cd {os.path.abspath('.')}
    Remove-Item {pipeline_file} -Force
    Write-Host "已删除脚本"
}}
                 """
    )
    return "\n".join(lines)


def pipeline_call_pwsh_handler(pipeline_file: str, script_encoding=""):
    if PERSERVE_PIPELINE:
        print(f"pwsh -NoProfile -ExecutionPolicy Bypass -File {pipeline_file}")
    else:
        encoding = script_encoding if script_encoding else locale.getpreferredencoding()
        raw(
            f'pwsh -NoProfile -ExecutionPolicy Bypass -File {os.path.join(os.path.abspath("."),pipeline_file)}',
            encoding=encoding,
        )


def pipeline_call_bash_handler(pipeline_file: str, script_encoding=""):
    if PERSERVE_PIPELINE:
        print(f"bash {pipeline_file}")
    else:
        encoding = script_encoding if script_encoding else locale.getpreferredencoding()
        raw(
            f'bash {os.path.join(os.path.abspath("."),pipeline_file)}',
            encoding=encoding,
        )


def pipeline_call_jsh_handler(pipeline_file: str, script_encoding=""):
    if PERSERVE_PIPELINE:
        print(f"jshell {pipeline_file}")
    else:
        encoding = script_encoding if script_encoding else locale.getpreferredencoding()
        raw(
            f'jshell {os.path.join(os.path.abspath("."),pipeline_file)}',
            encoding=encoding,
        )


def pipeline_call_java_handler(pipeline_file: str, script_encoding=""):
    if PERSERVE_PIPELINE:
        print(f"java {pipeline_file}")
    else:
        encoding = script_encoding if script_encoding else locale.getpreferredencoding()
        raw(
            f'java {os.path.join(os.path.abspath("."),pipeline_file)}',
            encoding=encoding,
        )


def pipeline_call_javascript_handler(pipeline_file: str):
    raw(f'node {os.path.join(os.path.abspath("."),pipeline_file)}')


def pipeline_call_python_handler(script_contents: str, script_encoding=""):
    encoding = script_encoding if script_encoding else locale.getpreferredencoding()
    compiled = compile(script_contents, filename="<dynamic-script>", mode="exec")
    locals = {}
    globals = {}
    exec(compiled, globals, locals)
    if "__result" in locals:
        tl.__result = locals["__result"]
    else:
        tl.__result = ""


def pipeline_get_pipeline_file_name_handler(
    now: int,
    is_linux: bool,
    is_pwsh: bool,
    is_python: bool,
    is_javascript: bool,
    is_java: bool,
    is_jsh: bool,
    is_bash: bool,
):
    if is_pwsh:
        return f"__pipeline.ps1" if PERSERVE_PIPELINE else f"__pipeline_{now}.ps1"
    if is_java:
        return f"__pipeline.java" if PERSERVE_PIPELINE else f"__pipeline_{now}.java"
    if is_bash:
        return f"__pipeline.sh" if PERSERVE_PIPELINE else f"__pipeline_{now}.sh"
    if is_jsh:
        return f"__pipeline.jsh" if PERSERVE_PIPELINE else f"__pipeline_{now}.jsh"
    if is_python:
        return f"__pipeline.py" if PERSERVE_PIPELINE else f"__pipeline_{now}.py"
    if is_javascript:
        return f"__pipeline.js" if PERSERVE_PIPELINE else f"__pipeline_{now}.js"
    if is_linux:
        return os.path.join(
            os.path.abspath("."),
            f"__pipeline.sh" if PERSERVE_PIPELINE else f"__pipeline_{now}.sh",
        )
    # is window env
    return f"__pipeline.bat" if PERSERVE_PIPELINE else f"__pipeline_{now}.bat"


def pipeline_rewrite_pipeline_file_handler(
    pipeline_file: str,
    script_contents: str,
    is_linux: bool,
    is_pwsh: bool,
    is_python: bool,
    is_javascript: bool,
    is_java: bool,
    is_jsh: bool,
    is_bash: bool,
):
    if is_pwsh:
        return (
            try_catch_powershell_scripts(script_contents, pipeline_file)
            if PERSERVE_PIPELINE
            else script_contents
        )
    if is_java:
        return try_catch_java_scripts(script_contents, pipeline_file=pipeline_file)
    if is_jsh:
        return try_catch_jsh_scripts(script_contents)
    if is_python:
        return try_catch_python_scripts(script_contents)
    if is_javascript:
        return try_catch_javascript_scripts(script_contents)
    if is_linux:
        return f"#!/bin/bash\nshopt -s expand_aliases\nsource /etc/profile\n{script_contents}"
    # window env
    return script_contents


def pipeline(*cmds, script_encoding=""):
    now = int(round(time.time() * 1000))
    is_pwsh = is_pwsh_script(cmds[0])
    is_python = is_python_script(cmds[0])
    is_java = is_java_script(cmds[0])
    is_jsh = is_jsh_script(cmds[0])
    is_bash = is_bash_script(cmds[0])
    is_javascript = is_javascript_script(cmds[0])
    is_linux = "Linux" == platform.system()
    pipeline_file = pipeline_get_pipeline_file_name_handler(
        now,
        is_linux=is_linux,
        is_pwsh=is_pwsh,
        is_python=is_python,
        is_javascript=is_javascript,
        is_java=is_java,
        is_jsh=is_jsh,
        is_bash=is_bash,
    )
    script_contents = pipeline_rewrite_pipeline_file_handler(
        pipeline_file=pipeline_file,
        script_contents="\n".join(cmds),  # type: ignore
        is_linux=is_linux,
        is_pwsh=is_pwsh,
        is_python=is_python,
        is_javascript=is_javascript,
        is_java=is_java,
        is_jsh=is_jsh,
        is_bash=is_bash,
    )
    # Known issues: ssz, 2025.10.23 上一个脚本执行的结果用###来代替
    script_contents = script_contents.replace("###", f"{tl.__result}")
    if not is_python:
        with open(pipeline_file, "w", encoding="utf-8") as fw:
            fw.write(script_contents)
    if log:
        log.info(script_contents)
    if is_linux:
        raw(f"chmod +x {pipeline_file}")
    if is_pwsh:
        pipeline_call_pwsh_handler(pipeline_file, script_encoding=script_encoding)
    elif is_java:
        pipeline_call_java_handler(pipeline_file, script_encoding=script_encoding)
    elif is_jsh:
        pipeline_call_jsh_handler(pipeline_file, script_encoding=script_encoding)
    elif is_bash:
        pipeline_call_bash_handler(pipeline_file, script_encoding=script_encoding)
    elif is_python:
        pipeline_call_python_handler(script_contents, script_encoding=script_encoding)
    elif is_javascript:
        pipeline_call_javascript_handler(pipeline_file)
    else:
        if PERSERVE_PIPELINE:
            print(f"{pipeline_file};del {pipeline_file}")
        else:
            encoding = locale.getpreferredencoding()
            raw(pipeline_file, encoding=encoding)
    if not (PERSERVE_PIPELINE or is_python):
        os.remove(pipeline_file)
    gone_seconds = (int(round(time.time() * 1000))) - now
    gone_seconds_str = to_interval(gone_seconds)
    log_gone_seconds = f"pipeline execute time: {gone_seconds_str}"
    if gone_seconds > 60 * 1000:
        log.warning(log_gone_seconds)
    else:
        log.info(log_gone_seconds)


def to_interval(interval):
    millseconds = interval % 1000
    tmp = round((interval - millseconds) / 1000)
    seconds = tmp % 60
    tmp = round((tmp - seconds) / 60)
    minutes = tmp % 60
    tmp = round((tmp - minutes) / 60)
    hours = tmp % 60
    if hours:
        return f"{hours}h:{minutes}m:{seconds}s:{millseconds}ms"
    if minutes:
        return f"{minutes}m:{seconds}s:{millseconds}ms"
    if seconds:
        return f"{seconds}s:{millseconds}ms"
    return f"{millseconds}ms"


def raw_detail(*cmds):
    retStr, returncode = raw_subprocess_adapter(*cmds)
    return retStr, returncode


def raw_detail_batch(*cmds):
    for cmd_line in cmds:
        retStr, returncode = raw_subprocess_adapter(*cmd_line)
    return retStr, returncode


def raw_with_errors(*cmds):
    _, returncode = raw_popen_adapter(*cmds)
    return returncode


def raw(*cmds, encoding="utf-8"):
    retStr, _ = raw_popen_adapter(*cmds, encoding=encoding)
    retStrReserved = False
    if retStr:
        for line in retStr.splitlines():
            if line.startswith("__result="):
                tl.__result = line[len("__result=") :]
                retStrReserved = True
    if not retStrReserved:
        tl.__result = ""
    return retStr


def __raw_subprocess33(*cmds):
    if log:
        log.info("|".join(cmds))
    results = []
    line = True
    oldLine = False
    with subprocess.Popen(
        "|".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=-1,
    ) as proc:
        for line in proc.stdout:
            line = str(line)
            log.info(line)
            if line:
                stdout_writer(line, oldLine)
                oldLine = line
                results.append(line)
    # double output
    # if results and log: log.info(''.join(results))
    # only returncode can to be return, no error message
    # None-successful, 1+ Failure
    returncode = proc.returncode
    if returncode != 0:
        errors = proc.stderr.readlines()
        retStr = "".join(errors)
        print("\n".join(errors))
    else:
        retStr = "".join(results)
    return retStr, returncode


def raw_subprocess_adapter(*cmds):
    if log:
        log.info("|".join(cmds))

    proc = subprocess.Popen(
        "|".join(cmds),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=-1,
    )
    stderr = os._wrap_close(io.TextIOWrapper(proc.stderr, encoding="utf-8"), proc)
    out = os._wrap_close(io.TextIOWrapper(proc.stdout, encoding="utf-8"), proc)
    results = []
    line = True
    oldLine = False
    while line:
        line = out.readline()
        if line:
            stdout_writer(line, oldLine)
            oldLine = line
            results.append(line)
    # double output
    # if results and log: log.info(''.join(results))
    # only returncode can to be return, no error message
    # None-successful, 1+ Failure
    returncode = out.close()
    if returncode:
        errors = stderr.readlines()
        lines = errors if errors else results
        retStr = "".join(lines)
        print("\n".join(lines))
    else:
        retStr = "".join(results)
    return retStr, returncode


def __is_different(line, oldLine):
    if not isinstance(line, str) or not isinstance(oldLine, str):
        return True
    lineArray = re.split(r"\s+", line)
    oldLineArray = re.split(r"\s+", oldLine)
    MIN_COMP_LEN = 2
    if len(lineArray) < MIN_COMP_LEN or len(oldLineArray) < MIN_COMP_LEN:
        return True
    for i in range(MIN_COMP_LEN):
        if not lineArray[i] == oldLineArray[i]:
            return True
    return False


def stdout_writer(line, oldLine):
    changeLine = "\r\n" if __is_different(line, oldLine) else "\r"
    line = line.replace("\r", "").replace("\n", "")
    formatter = "%s %s"
    line_lower = line.lower()
    if "critical" in line_lower:
        formatter = f"{tl.LIB_LOG_COLOR_RED_BOLD}%s %s{tl.LIB_LOG_COLOR_RESET}"
    elif "error" in line_lower:
        formatter = f"{tl.LIB_LOG_COLOR_RED}%s %s{tl.LIB_LOG_COLOR_RESET}"
    elif "warn" in line_lower:
        formatter = f"{tl.LIB_LOG_COLOR_YELLOW}%s %s{tl.LIB_LOG_COLOR_RESET}"
    sys.stdout.write(formatter % (line, changeLine))


# def raw_popen_adapter(*cmds, encoding="utf-8"):
#     if log:
#         log.info("|".join(cmds))
#     out = os.popen("|".join(cmds), mode="r", encoding="utf-8")
#     results = []
#     line = True
#     oldLine = False
#     while line:
#         try:
#             line = out.readline()
#             if line:
#                 stdout_writer(line, oldLine)
#                 results.append(line)
#                 oldLine = line
#         except UnicodeDecodeError:
#             oldLine = False
#     returncode = out.close()
#     retStr = str(out.errors) if returncode else "".join(results)
#     return retStr, returncode


def raw_popen_adapter_reader(pipe, results: list[str]):
    for line in iter(pipe.readline, ""):
        print(line.strip(), flush=True)
        results.append(line)
    pipe.close()


def raw_popen_adapter(*cmds, encoding="utf-8"):
    if log:
        log.info("|".join(cmds))
    try:
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE  # Hides the window
        else:
            startupinfo = None  # Not applicable on non-Windows systems
        p = subprocess.Popen(
            "|".join(cmds),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # 打开文本模式
            universal_newlines=True,
            # encoding="utf-8",  # 强制 UTF-8 解码
            encoding=encoding,
            errors="replace",  # 出错时用 � 替换，避免抛异常
            bufsize=1,  # 行缓冲
            startupinfo=startupinfo if os.name == "nt" else None,
        )
        results = []
        errors = []

        # for line in iter(p.stdout.readline, ""):  # 逐行读取，实时输出
        # Known issues: ssz, 2025.10.14, 这里不会显示在日志里
        # for line in p.stdout:
        #     print(line.strip(), flush=True)
        #     results.append(line)

        t1 = threading.Thread(target=raw_popen_adapter_reader, args=(p.stdout, results))
        t2 = threading.Thread(target=raw_popen_adapter_reader, args=(p.stderr, errors))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        p.wait()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Sending SIGINT to subprocess...")
        if os.name == "nt":
            # On Windows, SIGINT is mapped to CTRL_C_EVENT
            p.send_signal(signal.CTRL_C_EVENT)
        else:
            p.send_signal(signal.SIGINT)
        p.wait(timeout=5)  # Give the subprocess a chance to clean up
        if p.poll() is None:
            print("Subprocess did not terminate, killing it...")
            p.terminate()
            p.wait()

    finally:
        if "process" in locals() and p.poll() is None:
            p.kill()  # Ensure the process is terminated if still running
    returncode = p.returncode
    stdout = "".join(results)
    # stderr = p.stderr.read()
    stderr = "".join(errors)
    return (stderr if returncode else stdout), returncode


def chdir(path: str, console=False):
    log.debug(path)
    if console:
        driver = os.path.splitdrive(path)[0]
        (
            call_parent_process(driver, "cd " + path)
            if os.path.exists(path)
            else log.error(path + " is not exist")
        )
    else:
        (
            raw("explorer " + path)
            if os.path.exists(path)
            else log.error(path + " is not exist")
        )


class Timer:
    def __init__(self, label: str = "代码段"):
        self.label = label

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        self.interval = self.end - self.start
        print(f"[{self.label}] 执行时间: {self.interval:.6f} 秒")
