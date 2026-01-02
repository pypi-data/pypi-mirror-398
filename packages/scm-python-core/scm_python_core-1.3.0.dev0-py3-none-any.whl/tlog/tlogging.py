import logging, platform, os, sys, json, ast, re
from logging import handlers

is_linux = "Linux" == platform.system()
LIB_LOG_COLOR_GREY = "\x1b[38;21m" if is_linux else ""
LIB_LOG_COLOR_YELLOW = "\x1b[33m" if is_linux else ""
LIB_LOG_COLOR_RED = "\x1b[31m" if is_linux else ""
LIB_LOG_COLOR_RED_BOLD = "\x1b[31;1m" if is_linux else ""
LIB_LOG_COLOR_RESET = "\x1b[0m" if is_linux else ""
from tlog.log4j import Log4j

signal_handler_list = []
PRINT_DETAILS = False
LOG4J_LOG_FILE = os.path.abspath("all.log")
inherited = ""
# 上一个脚本执行的返回结果,用于pipeline中
__result = ""
QUIET = False
# Known issues: ssz, 2025.10.14, 日志文件名不能以-开头
for index, arg in enumerate(sys.argv):
    if "--quiet" == arg:
        QUIET = True
        inherited += arg
    elif arg == "--show-detail":
        PRINT_DETAILS = True
        inherited += arg
    elif arg == "--preserve-log":
        if index < len(sys.argv) - 1:
            preserve_log_file = sys.argv[index + 1]
            if not preserve_log_file.startswith("-"):
                LOG4J_LOG_FILE = preserve_log_file
        inherited += f'{arg} "{LOG4J_LOG_FILE}"'


def register_signal_handler(handler):
    signal_handler_list.append(handler)


def do_signal_handler(signum, frame):
    for handler in signal_handler_list:
        handler(signum, frame)


def result_context():
    if not __result:
        return {}
    try:
        result = ast.literal_eval(__result)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


def m(*args):
    lists = []
    for o in args:
        lists.append(str(o))
    return " ".join(lists)


if os.name == "nt":
    import msvcrt
else:
    import fcntl


class SafeTimedRotatingFileHandler(handlers.TimedRotatingFileHandler):
    """支持多进程安全写日志的 TimedRotatingFileHandler"""

    def emit(self, record):
        try:
            self._lock()
            super().emit(record)
        finally:
            self._unlock()

    def _lock(self):
        if not self.stream:
            return
        if os.name == "nt":
            try:
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_LOCK, 1)
            except OSError:
                pass
        else:
            try:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            except OSError:
                pass

    def _unlock(self):
        if not self.stream:
            return
        if self.stream is None:
            return
        if os.name == "nt":
            try:
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            try:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


class ColoredFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    def __init__(
        self,
        fmt="%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s",
        datestr="%Y-%m-%d,%H:%M:%S",
    ):
        yellow_underline = "\x1b[33;21m"
        red_underline = "\x1b[31;21m"
        self.FORMATTERS = {
            logging.DEBUG: logging.Formatter(
                LIB_LOG_COLOR_GREY + fmt + LIB_LOG_COLOR_RESET, datestr
            ),
            logging.INFO: logging.Formatter(
                LIB_LOG_COLOR_GREY + fmt + LIB_LOG_COLOR_RESET, datestr
            ),
            logging.WARNING: logging.Formatter(
                LIB_LOG_COLOR_YELLOW + fmt + LIB_LOG_COLOR_RESET, datestr
            ),
            logging.ERROR: logging.Formatter(
                LIB_LOG_COLOR_RED + fmt + LIB_LOG_COLOR_RESET, datestr
            ),
            logging.CRITICAL: logging.Formatter(
                LIB_LOG_COLOR_RED_BOLD + fmt + LIB_LOG_COLOR_RESET, datestr
            ),
        }

    def format(self, record):
        return self.FORMATTERS[record.levelno].format(record)


class TLog(object):
    level_relations = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "crit": logging.CRITICAL,
    }

    def __init__(
        self,
        filename,
        level="info",
        when="D",
        backCount=3,
        fmt="%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s",
        datestr="%Y-%m-%d,%H:%M:%S",
    ):
        self.logger = logging.getLogger(filename)
        format_str = ColoredFormatter(fmt, datestr)
        self.logger.setLevel(self.level_relations.get(level))
        # 必须添加sys.stdout,否则在多级进程调用会导致父进程死锁
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(format_str)
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th = SafeTimedRotatingFileHandler(
            filename=filename, when=when, backupCount=backCount, encoding="utf-8"
        )
        th.setFormatter(format_str)
        if not QUIET:
            self.logger.addHandler(sh)
            self.logger.addHandler(th)


"""
    def lists(self, args):
        lists = []
        for o in args: lists.append(str(o))
        return lists

    def debug(self, * args):
        self.logger.debug(' '.join(self.lists(args)))

    def info(self, * args):
        self.logger.info(' '.join(self.lists(args)))

    def error(self, * args):
        self.logger.error(' '.join(self.lists(args)))

    def warning(self, * args):
        self.logger.warning(' '.join(self.lists(args)))

    def critical(self, * args):
        self.logger.critical(' '.join(self.lists(args)))
"""


def mkdir_if_absent(path):
    if not path or os.path.exists(path):
        return False
    else:
        paths = os.path.split(path)
        mkdir_if_absent(paths[0])
        os.mkdir(path)
        return True


def defaultLogConfiguration():
    return [
        "### direct log messages to stdout ###",
        "log4j.rootLogger=error,stdout",
        "log4j.appender.stdout=org.apache.log4j.ConsoleAppender",
        "log4j.appender.stdout.Target=System.out",
        "log4j.appender.stdout.layout=com.tmp.core.log4j.CalibrationPatternLayout",
        "log4j.appender.stdout.layout.ConversionPattern=%d{yy-MM-dd HH:mm:ss.SSS} %-5p %t %C{1}.%M:%L - %m%n",
        "",
        "log4j.logger.com= info,A2",
        "log4j.appender.A2=org.apache.log4j.RollingFileAppender",
        "log4j.appender.A2.File=logs/python.log",
        "log4j.appender.A2.MaxFileSize=10000KB",
        "log4j.appender.A2.MaxBackupIndex=5",
        "",
        "log4j.appender.A2.layout=com.tmp.core.log4j.CalibrationPatternLayout",
        "log4j.appender.A2.layout.ConversionPattern=%d{yy-MM-dd HH:mm:ss.SSS} %-5p %t %C{1}.%M:%L - %m%n",
    ]


log = None


def is_not_default_log_file():
    return LOG4J_LOG_FILE != os.path.abspath("all.log")


def get_logger():
    global log
    if not log:
        prop = (
            Log4j(
                QUIET,
                PRINT_DETAILS,
                LOG4J_LOG_FILE,
                skip_log4j_config_file=is_not_default_log_file(),
            )
            .load()
            .properties
        )
        # print('log4j', prop)
        filename = prop["filename"]
        logPath = os.path.dirname(filename)
        mkdir_if_absent(logPath)
        log = TLog(
            prop["filename"],
            prop["level"],
            prop["when"],
            prop["backCount"],
            prop["fmt"],
            prop["datestr"],
        ).logger


get_logger()
if __name__ == "__main__":
    log = TLog("all.log", level="debug")
    log.logger.debug("debug")
    log.logger.info("info")
    log.logger.warning("警告")
    log.logger.error("报错")
    log.logger.critical("严重")
    TLog("error.log", level="error").logger.error("error")
