import sys, fnmatch, os, glob, unittest
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.tssh as tssh
import tutils.context_opt as tcontext

log = tl.log
UT = unittest.TestCase()


def exercise_os_handler():
    log.info("exercise_os_handler")
    UT.assertIsNotNone(os.environ.get("SCM_PYTHON_SH_HOME"))
    UT.assertIsNotNone(os.path.expanduser("~"))
    if not thpe.is_linux:
        UT.assertEqual(
            "/app/ms/k8sdeploy/app/bin\\testcaseRpcServer\\.sh",
            os.path.join("/app/ms/k8sdeploy/app/bin", "testcaseRpcServer", ".sh"),
        )
    if not thpe.is_linux:
        UT.assertIn("\\", os.path.abspath("."))
        abs_file = "C:/Users/shaoshu/AppData/Roaming/Code/User/workspaceStorage/ff1f25c6a6cf541d2834a429c5dfae43/vscjava.vscode-java-test"
        UT.assertTrue(fnmatch.fnmatch(abs_file, "*.vscode-java-test"))
        UT.assertFalse(fnmatch.fnmatch(abs_file, "vscjava.*"))
        if os.path.exists("C:\\git\\snap.rtc"):
            UT.assertListEqual(
                ["C:\\git\\snap.rtc\\cmbuild"], glob.glob("C:\\git\\snap.rtc\\cmbuild")
            )
            UT.assertListEqual(
                [
                    "C:\\git\\snap.rtc\\cmbuild\\snap_rtc_build.download.source.sh",
                    "C:\\git\\snap.rtc\\cmbuild\\snap_rtc_build.sh",
                ],
                os_glob_list := glob.glob("C:\\git\\snap.rtc\\cmbuild\\*.sh"),
            )
            UT.assertIsInstance(os_glob_list, list)
            UT.assertIn("C:\\git\\snap.rtc\\cmbuild", os_glob_list[0])
