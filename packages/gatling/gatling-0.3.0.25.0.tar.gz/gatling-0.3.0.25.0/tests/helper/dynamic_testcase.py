import unittest


class DynamicTestCase(unittest.TestCase):

    @classmethod
    def set_name(cls, name):
        cls.__name__ = name

    @classmethod
    def append_testcase(cls, test_case_name, test_case_fctn, *args, **kwargs):
        """append a test case to the class"""
        if not test_case_name.startswith("test_"):
            test_case_name = f"test_{test_case_name}"

        def testcase_method(self):
            return test_case_fctn(*args, **kwargs)
        testcase_method.__name__ = test_case_name
        setattr(cls, test_case_name, testcase_method)


if __name__ == '__main__':
    pass
    DynamicTestCase.set_name('MyTestCase')
    # or
    class MyTestCase(DynamicTestCase):
        pass
