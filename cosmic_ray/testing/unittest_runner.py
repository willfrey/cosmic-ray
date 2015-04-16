from itertools import chain
import unittest

from .test_runner import TestRunner


class UnittestRunner(TestRunner):
    """A TestRunner using `unittest`'s discovery mechanisms.

    This discovers all tests under `test_dir` and executes them.
    """

    def _run(self):
        suite = unittest.TestLoader().discover(self.test_dir)
        result = unittest.TestResult()
        suite.run(result)

        return (
            result.wasSuccessful(),
            [(str(r[0]), r[1])
             for r in chain(result.errors,
                            result.failures)])
