import unittest
import tutils.tssh as tssh
import tlog.tlogging as tl

log = tl.log
UT = unittest.TestCase()


def exercise_hello_world_handler(debug=False, name="diameter"):
    """
    debug: bool
    name: str
    """
    log.info(f"exercise_hello_world_handler debug={debug}, name={name}")
    float_value = 0.0
    UT.assertIsInstance(float_value, float)
    UT.assertLess(float_value, 0.005)
    # print(tssh.sshcli_authorizations)
