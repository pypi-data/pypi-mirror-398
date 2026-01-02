import unittest
import tlog.tlogging as tl

log = tl.log

UT = unittest.TestCase()


def exercise_eval_handler():
    log.info("exercise_eval_handler")
    context_globals = {"x": 1}
    context_locals = {"y": 1}
    print("---", eval("\"'a' in ['a','b','c']\""))
    UT.assertIsInstance(eval("'a' in ['a','b','c']"), bool)
    UT.assertIsInstance(eval("1==1"), bool)
    UT.assertIsInstance(eval("'aa'=='bb'"), bool)
    UT.assertTrue(eval("'__name__' in globals()"))
    UT.assertEqual("tapps.exercise.eval", eval("globals()['__name__']"))
    UT.assertTrue(eval("'context_globals' in vars()"))
    UT.assertTrue(eval("'context_locals' in vars()"))
    UT.assertTrue(eval("x == 1", context_globals))
    UT.assertTrue(eval("'x' in globals()", context_globals))
    UT.assertTrue(eval("'y' in vars()", context_globals, context_locals))
    # 表示eval后不会对下个eval的vars产生影响
    UT.assertTrue(eval("'context_globals' in vars()"))
    UT.assertTrue(eval("'context_locals' in vars()"))
