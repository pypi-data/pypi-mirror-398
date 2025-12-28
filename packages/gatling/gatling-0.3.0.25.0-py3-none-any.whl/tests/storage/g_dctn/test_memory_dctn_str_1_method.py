import json
import unittest
from gatling.utility.mem_tools import sizeof
from helper.get_varname import get_var_name
from storage.g_dctn import test_memory_dctn_str_0_objs
from gatling.storage.g_dctn.memory_dctn import MemoryDctn
from helper.dynamic_testcase import DynamicTestCase

varname2obj = {get_var_name(obj, vars(test_memory_dctn_str_0_objs)): obj for obj in test_memory_dctn_str_0_objs.memorydctn_objs}


# DynamicTestCase.set_name('TestRuntimeTaskManagerCoroutine')
class TestMemoryDctnStr(DynamicTestCase):
    pass


# Define Test Case Function
def testcase_fctn(cand: dict, level):
    md = MemoryDctn()

    md.setmany(cand)
    sent = md.str(level)
    # sent = str(md)
    print(f"===candidate===[{sizeof(cand)}]")
    print(cand)
    print(f"===serialized[{sizeof(md)}]===")
    print(sent)
    print("===end===\n")
    back = json.loads(sent)

    assert md == back, f"{sent} != {back}"


# === Dynamic Register Test Case ===
for varname, obj in varname2obj.items():
    for level in [-1, 0, 1, 2, 3]:
        testcase_name = f"test_{varname}_{level=}"
        TestMemoryDctnStr.append_testcase(testcase_name, testcase_fctn, obj, level)

if __name__ == "__main__":
    unittest.main(verbosity=2)
