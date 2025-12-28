import unittest

from gatling.storage.g_dctn.memory_dctn import MemoryDctn

Key_A = "A"
Key_B = "B"
Key_C = "C"
Value_1_A = 1
Value_3_B = 3
Value_2_C = 2


class TestMemoryDctnBase(unittest.TestCase):
    """Unit tests for MemoryDctn get, set, pop methods."""

    # ==================== __getitem__ ====================

    def test_getitem_existing_key(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        self.assertEqual(d[Key_A], Value_1_A)

    def test_getitem_missing_key_raises_keyerror(self):
        d = MemoryDctn()
        with self.assertRaises(KeyError):
            _ = d[Key_A]

    # ==================== __setitem__ ====================

    def test_setitem_new_key(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        self.assertEqual(d[Key_A], Value_1_A)
        self.assertEqual(len(d), 1)

    def test_setitem_overwrite_key(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        d[Key_A] = Value_3_B
        self.assertEqual(d[Key_A], Value_3_B)
        self.assertEqual(len(d), 1)

    # ==================== __delitem__ ====================

    def test_delitem_existing_key(self):
        d = MemoryDctn()
        d[Key_A] = Value_1_A
        del d[Key_A]
        self.assertEqual(len(d), 0)
        self.assertNotIn(Key_A, d)

    def test_delitem_missing_key_raises_keyerror(self):
        d = MemoryDctn()
        with self.assertRaises(KeyError):
            del d[Key_A]

    # ==================== set ====================

    def test_set_new_key_returns_true(self):
        d = MemoryDctn()
        result = d.set(Key_A, Value_1_A)
        self.assertTrue(result)
        self.assertEqual(d[Key_A], Value_1_A)

    def test_set_existing_key_returns_false(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.set(Key_A, Value_3_B)
        self.assertFalse(result)
        self.assertEqual(d[Key_A], Value_3_B)

    # ==================== get ====================

    def test_get_existing_key(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        self.assertEqual(d.get(Key_A), Value_1_A)

    def test_get_missing_key_raises_keyerror(self):
        d = MemoryDctn()
        with self.assertRaises(KeyError):
            d.get(Key_A)

    def test_get_missing_key_with_default(self):
        d = MemoryDctn()
        result = d.get(Key_A, Value_2_C)
        self.assertEqual(result, Value_2_C)

    def test_get_missing_key_with_none_default(self):
        d = MemoryDctn()
        result = d.get(Key_A, None)
        self.assertIsNone(result)

    def test_get_missing_key_raises_custom_exception(self):
        d = MemoryDctn()
        with self.assertRaises(ValueError):
            d.get(Key_A, ValueError)

    # ==================== pop ====================

    def test_pop_existing_key(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.pop(Key_A)
        self.assertEqual(result, Value_1_A)
        self.assertNotIn(Key_A, d)

    def test_pop_missing_key_raises_keyerror(self):
        d = MemoryDctn()
        with self.assertRaises(KeyError):
            d.pop(Key_A)

    def test_pop_missing_key_with_default(self):
        d = MemoryDctn()
        result = d.pop(Key_A, Value_2_C)
        self.assertEqual(result, Value_2_C)

    def test_pop_missing_key_with_none_default(self):
        d = MemoryDctn()
        result = d.pop(Key_A, None)
        self.assertIsNone(result)

    def test_pop_missing_key_raises_custom_exception(self):
        d = MemoryDctn()
        with self.assertRaises(ValueError):
            d.pop(Key_A, ValueError)

    # ==================== setmany ====================

    def test_setmany_with_dict(self):
        d = MemoryDctn()
        count = d.setmany({Key_A: Value_1_A, Key_B: Value_3_B})
        self.assertEqual(count, 2)
        self.assertEqual(d[Key_A], Value_1_A)
        self.assertEqual(d[Key_B], Value_3_B)

    def test_setmany_with_kwargs(self):
        d = MemoryDctn()
        count = d.setmany(A=Value_1_A, B=Value_3_B)
        self.assertEqual(count, 2)
        self.assertEqual(d[Key_A], Value_1_A)
        self.assertEqual(d[Key_B], Value_3_B)

    def test_setmany_with_iterable(self):
        d = MemoryDctn()
        count = d.setmany([(Key_A, Value_1_A), (Key_B, Value_3_B)])
        self.assertEqual(count, 2)
        self.assertEqual(d[Key_A], Value_1_A)
        self.assertEqual(d[Key_B], Value_3_B)

    def test_setmany_with_dict_and_kwargs(self):
        d = MemoryDctn()
        count = d.setmany({Key_A: Value_1_A}, B=Value_3_B)
        self.assertEqual(count, 2)
        self.assertEqual(d[Key_A], Value_1_A)
        self.assertEqual(d[Key_B], Value_3_B)

    # ==================== getmany ====================

    def test_getmany_all_exist(self):
        d = MemoryDctn()
        d.setmany({Key_A: Value_1_A, Key_B: Value_3_B})
        result = d.getmany({Key_A: 0, Key_B: 0})
        self.assertEqual(result, {Key_A: Value_1_A, Key_B: Value_3_B})

    def test_getmany_with_defaults(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.getmany({Key_A: 0, Key_C: Value_2_C})
        self.assertEqual(result, {Key_A: Value_1_A, Key_C: Value_2_C})
        self.assertEqual(len(d), 1)  # unchanged

    def test_getmany_with_kwargs(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.getmany(A=0, C=Value_2_C)
        self.assertEqual(result, {Key_A: Value_1_A, Key_C: Value_2_C})

    def test_getmany_raises_on_missing(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        with self.assertRaises(KeyError):
            d.getmany({Key_A: 0, Key_C: KeyError})

    # ==================== popmany ====================

    def test_popmany_all_exist(self):
        d = MemoryDctn()
        d.setmany({Key_A: Value_1_A, Key_B: Value_3_B})
        result = d.popmany({Key_A: 0, Key_B: 0})
        self.assertEqual(result, {Key_A: Value_1_A, Key_B: Value_3_B})
        self.assertEqual(len(d), 0)

    def test_popmany_with_defaults(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.popmany({Key_A: 0, Key_C: Value_2_C})
        self.assertEqual(result, {Key_A: Value_1_A, Key_C: Value_2_C})
        self.assertEqual(len(d), 0)

    def test_popmany_with_kwargs(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        result = d.popmany(A=0, C=Value_2_C)
        self.assertEqual(result, {Key_A: Value_1_A, Key_C: Value_2_C})
        self.assertEqual(len(d), 0)

    def test_popmany_raises_on_missing(self):
        d = MemoryDctn()
        d.set(Key_A, Value_1_A)
        with self.assertRaises(KeyError):
            d.popmany({Key_A: 0, Key_C: KeyError})
