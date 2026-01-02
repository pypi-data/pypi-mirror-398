import sys, re, os, socket, unittest
import tlog.tlogging as tl
import tio.tfile as tf

log = tl.log
UT = unittest.TestCase()


def exercise_lib_diff_handler():
    log.info("exercise_lib_diff_handler")
    py_file_name = os.path.join(tf.getpythonpath(), "cli.py")
    UT.assertTrue(tf.match_include(py_file_name, include_array := None))
    UT.assertTrue(tf.match_include(py_file_name, include_array := ["*.py"]))
    UT.assertFalse(tf.match_include(py_file_name, include_array := ["*.exe"]))
    UT.assertTrue(tf.match_include(py_file_name, include_array := ["*cli.py"]))
    UT.assertFalse(tf.match_exclude(py_file_name, exclude_array := None))
    UT.assertTrue(tf.match_exclude(py_file_name, exclude_array := ["*.py"]))
    UT.assertFalse(tf.match_exclude(py_file_name, exclude_array := ["*.exe"]))

    dict_diff = tf.diff(
        tf.getpythonpath(), updates=(updates := []), exclude=(exclude := "*.py")
    )
    UT.assertNotIn("cli.py", dict_diff)
    UT.assertNotIn("cli.py", updates)
    UT.assertIn(".gitignore", dict_diff)
    UT.assertIn(".gitignore", updates)

    dict_diff = tf.diff(
        tf.getpythonpath(), updates=(updates := []), include=(include := "*.py")
    )
    UT.assertIn("cli.py", dict_diff)
    UT.assertIn("cli.py", updates)
    UT.assertNotIn(".gitignore", dict_diff)
    UT.assertNotIn(".gitignore", updates)

    dict_diff = tf.diff(
        tf.getpythonpath(),
        updates=(updates := []),
        include=(include := "*.py"),
        exclude=(exclude := "*.py"),
    )
    UT.assertEqual(0, len(dict_diff.keys()))
    dict_diff = tf.diff(
        tf.getpythonpath(),
        updates=(updates := []),
        include=(include := "*.py"),
        exclude=(exclude := "*cli.py"),
    )
    UT.assertIn("__init__.py", dict_diff)
    UT.assertIn("__init__.py", updates)
    UT.assertNotIn("cli.py", dict_diff)
    UT.assertNotIn("cli.py", updates)
