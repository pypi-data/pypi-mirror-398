import unittest

from gatling.storage.g_dctn.memory_dctn import MemoryDctn

Key_A = "A"
Key_B = "B"
Key_C = "C"
Value_1_A = 1
Value_3_B = 3
Value_2_C = 2


class TestMemoryDctnMore(unittest.TestCase):
    """Unit tests for MemoryDctn class."""

    def test_basic_set_get_len(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertEqual(len(d), 1)
        self.assertEqual(d[Key_A], Value_1_A)

    def test_basic_set_pop_len(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertEqual(len(d), 1)
        self.assertEqual(d.pop(Key_A), Value_1_A)
        self.assertEqual(len(d), 0)

    def test_basic_get_default(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertEqual(d.get(Key_C, Value_2_C), Value_2_C)

    def test_basic_pop_default(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertEqual(d.pop(Key_C, Value_2_C), Value_2_C)
        self.assertEqual(len(d), 1)

    def test_clear(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        d[Key_B] = Value_3_B
        self.assertEqual(len(d), 2)
        d.clear()
        self.assertEqual(len(d), 0)

    def test_del(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        del d[Key_A]
        self.assertEqual(len(d), 0)
        with self.assertRaises(KeyError):
            print(d[Key_A])

    def test_keys(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        d[Key_B] = Value_3_B
        self.assertEqual(list(d.keys()), [Key_A, Key_B])

    def test_values(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        d[Key_B] = Value_3_B
        self.assertEqual(list(d.values()), [Value_1_A, Value_3_B])

    def test_items(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        d[Key_B] = Value_3_B
        self.assertEqual(list(d.items()), [(Key_A, Value_1_A), (Key_B, Value_3_B)])

    def test_contains(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertIn(Key_A, d)
        self.assertNotIn(Key_B, d)

    def test_eq(self):
        d1 = MemoryDctn()
        d1.setmany({Key_A: Value_1_A, Key_B: Value_3_B})
        d2 = MemoryDctn()
        d2.setmany({Key_B: Value_3_B, Key_A: Value_1_A})
        self.assertEqual(d1, d2)
        d3 = {Key_B: Value_3_B, Key_A: Value_1_A}
        self.assertEqual(d1, d3)

    def test_ne(self):
        d1 = MemoryDctn()
        d1.setmany({Key_A: Value_1_A, Key_B: Value_3_B})
        d2 = MemoryDctn()
        d2.setmany({Key_B: Value_3_B, Key_A: Value_2_C})
        self.assertNotEqual(d1, d2)
        d3 = {Key_B: Value_3_B, Key_A: Value_2_C}
        self.assertNotEqual(d1, d3)

    def test_sort(self):
        d = MemoryDctn()
        d[Key_C] = Value_2_C
        d[Key_A] = Value_1_A
        d[Key_B] = Value_3_B
        self.assertEqual(list(d.keys()), [Key_C, Key_A, Key_B])
        d.sort()
        self.assertEqual(list(d.keys()), [Key_A, Key_C, Key_B])
        d.sort(reverse=True)
        self.assertEqual(list(d.keys()), [Key_B, Key_C, Key_A])
        d.sort(by='key')
        self.assertEqual(list(d.keys()), [Key_A, Key_B, Key_C])
        d.sort(by='key', reverse=True)
        self.assertEqual(list(d.keys()), [Key_C, Key_B, Key_A])
        d.sort(by=lambda k, v: {Key_B: 0, Key_A: 1, Key_C: 2}[k])
        self.assertEqual(list(d.keys()), [Key_B, Key_A, Key_C])


    def test_open_and_close(self):
        d = MemoryDctn()
        try:
            d.open()
            d.close()
        except Exception as e:
            self.fail(f"open/close raised unexpectedly: {e}")

    def test_context_manager(self):
        d = MemoryDctn()
        try:
            with d:
                pass
        except Exception as e:
            self.fail(f"context manager raised unexpectedly: {e}")
