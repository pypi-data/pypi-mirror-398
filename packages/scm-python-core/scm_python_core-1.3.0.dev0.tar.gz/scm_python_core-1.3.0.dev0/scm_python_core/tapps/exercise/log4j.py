import tlog.tlogging as tl
import tio.tfile as tf
from tlog.log4j import Log4j

log = tl.log


def test_log():
    log.debug("debug")
    log.info("info")
    log.warning("警告")
    log.error("报错")
    log.critical("严重")
    log.info(tl.m("1", "2", "3", "4"))
    tl.TLog("error.log", level="error").logger.error("error")


def test_tfile():
    tf.mkdir_if_absent("os/abc/efg")
    tf.remove_dirs("os/abc/efg")


def test_log4j():
    print(
        Log4j().parseFormatter("%d{yy-MM-dd HH:mm:ss.SSS} %-5p %t %C{1}.%M:%L - %m%n")
    )


def exercise_log4j_handler():
    log.info("exercise_log4j_handler")
    test_log()
    test_tfile()
    test_log4j()
