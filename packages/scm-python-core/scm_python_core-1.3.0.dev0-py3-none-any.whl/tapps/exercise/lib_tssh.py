import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tutils.tssh as tssh

log = tl.log
UT = unittest.TestCase()


def exercise_lib_tssh_handler():
    log.info("exercise_lib_tssh_handler")
    remote_path_tuple = list(tssh.parse_remote_path("build@scm:/snap_share"))
    remote_path_tuple[1] = "***"
    UT.assertListEqual(
        ["build", "***", 22, "15.116.68.130", "/snap_share"],
        remote_path_tuple,
    )
    UT.assertTupleEqual(
        ("root", None, 10022, "bz.vicp.net", "/snap_share"),
        tssh.parse_remote_path("root@bz.vicp.net:/snap_share"),
    )
    remote_path_tuple = list(tssh.parse_remote_path("root@192.168.58.3:/snap_share"))
    remote_path_tuple[1] = "***"
    UT.assertListEqual(
        ["root", "***", 22, "192.168.58.3", "/snap_share"],
        remote_path_tuple,
    )
    remote_path_tuple = list(tssh.parse_remote_path("root@nas246.shao.sh:/snap_share"))
    remote_path_tuple[1] = "***"
    UT.assertListEqual(
        ["root", "***", 22, "nas246.shao.sh", "/snap_share"],
        remote_path_tuple,
    )
    remote_path_tuple = list(
        tssh.parse_remote_path("root@eium-5803.ssz.hpqcorp.net:/snap_share")
    )
    remote_path_tuple[1] = "***"
    UT.assertListEqual(
        ["root", "***", 22, "eium-5803.ssz.hpqcorp.net", "/snap_share"],
        remote_path_tuple,
    )
