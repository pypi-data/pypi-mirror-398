import unittest
from contextlib import contextmanager


class SubTestCase(unittest.TestCase):

    def subSetUp(self):
        pass

    def subTearDown(self):
        pass

    @contextmanager
    def subTestCase(self, **params):
        """subTestCase with setup/teardown"""
        with self.subTest(**params):
            # setup
            self.subSetUp()
            try:
                yield self
            finally:
                # teardown
                self.subTearDown()
