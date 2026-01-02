import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tutils.thpe as thpe

log = tl.log
UT = unittest.TestCase()


def exercise_lib_vilink_handler():
    log.info("exercise_lib_vilink_handler")
    jobs = thpe.load_yaml_from_install("vilink/jobs", "vilink")
    if not jobs:
        return
    for job in jobs:
        UT.assertIn("alias", job)
        UT.assertIn("cron", job)
        UT.assertIn("batch", job)
