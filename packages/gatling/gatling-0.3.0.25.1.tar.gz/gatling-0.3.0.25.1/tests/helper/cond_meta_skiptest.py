import unittest
from abc import ABCMeta, ABC


class ConditionalMetaSkipTest(ABCMeta):

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if issubclass(cls, unittest.TestCase):
            if ABC in bases:
                cls.__unittest_skip__ = True
                cls.__unittest_skip_why__ = "Abstract TestCase"
            else:
                cls.__unittest_skip__ = False

        return cls
