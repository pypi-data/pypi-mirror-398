import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tutils.thpe as thpe

log = tl.log
UT = unittest.TestCase()


def exercise_lib_thpe_handler():
    log.info("exercise_lib_thpe_handler")
    ping_latency = 1.0
    for _ in range(10):
        UT.assertLess(ping_latency := thpe.ping_workaround("192.168.50.236"), 100)
    if isinstance(ping_latency, float) and ping_latency < 5:
        UT.assertEqual("home", thpe.work_environment())
    UT.assertTupleEqual(
        ("root", None, "ssz1", "/sh/app"), thpe.parse_remote_path("root@ssz1://sh/app")
    )
    thpe_env_context_dict = thpe.create_env_context()
    if not thpe.is_linux:
        UT.assertIn("SH_HOME", thpe_env_context_dict)
        UT.assertIn("env_file:envs/env/repocache", thpe_env_context_dict)
    UT.assertIn("SCM_PYTHON_SH_HOME", thpe_env_context_dict)
    UT.assertIn("env:PATH", thpe_env_context_dict)
