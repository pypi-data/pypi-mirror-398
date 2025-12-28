import os
import tempfile
import unittest

from gatling.storage.g_table.table_ao_file_tsv import TableAO_FileTSV, KEY_IDX
from gatling.ztest.subtestcase import SubTestCase
from storage.g_table.a_const_test import const_key2type, rand_row, const_key2type_extra, const_keys_extra, rows2cols, const_keys


class TestFileTableBase(SubTestCase):
    """Unit tests for TestFileTable class."""

    def prerun_0row_trivial(self):
        return []

    def prerun_0row_extend(self):
        rows = []
        self.ft.extend(rows)
        return rows

    def prerun_1row_append(self):
        row0 = rand_row()
        self.ft.append(row0)
        return [row0]

    def prerun_1row_extend(self):
        row0 = rand_row()
        self.ft.extend([row0])
        return [row0]

    def prerun_2row_append_link(self):
        row0, row1 = rand_row(), rand_row()
        self.ft.append(row0).append(row1)
        return [row0, row1]

    def prerun_2row_append_line(self):
        row0, row1 = rand_row(), rand_row()
        self.ft.append(row0)
        self.ft.append(row1)
        return [row0, row1]

    def prerun_2row_extend_batch(self):
        row0, row1 = rand_row(), rand_row()
        self.ft.extend([row0, row1])
        return [row0, row1]

    def prerun_2row_extend_link(self):
        row0, row1 = rand_row(), rand_row()
        self.ft.extend([row0]).extend([row1])
        return [row0, row1]

    def prerun_2row_extend_line(self):
        row0, row1 = rand_row(), rand_row()
        self.ft.extend([row0])
        self.ft.extend([row1])
        return [row0, row1]

    def setUp(self):
        self.preruns_0row = [self.prerun_0row_trivial, self.prerun_0row_extend]
        self.preruns_1row = [self.prerun_1row_append, self.prerun_1row_extend]
        self.preruns_2row = [self.prerun_2row_append_link,
                             self.prerun_2row_append_line,
                             self.prerun_2row_extend_batch,
                             self.prerun_2row_extend_link,
                             self.prerun_2row_extend_line]
        self.preruns_notrivial = [self.prerun_0row_extend] + self.preruns_1row + self.preruns_2row

        self.preruns = self.preruns_0row + self.preruns_1row + self.preruns_2row

    def TearDown(self):
        pass

    def subSetUp(self):
        """Create a temporary directory and test file path before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_fname = os.path.join(self.temp_dir.name, "test_table.tsv")
        print(f"Test file path: {self.test_fname}")
        self.ft = TableAO_FileTSV(self.test_fname)

    def subTearDown(self):
        """Clean up temporary directory after each test."""
        self.temp_dir.cleanup()

    def test_nofile_x_getkey(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                self.ft.get_key2type()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_getfirstrow(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                self.ft.get_first_row()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_getlastrow(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                self.ft.get_last_row()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_exists(self):
        with self.subTestCase():
            self.assertFalse(self.ft.exists())

    def test_nofile_x_delete_allow(self):
        with self.subTestCase():
            self.assertFalse(self.ft.exists())
            self.ft.delete()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_clear(self):
        with self.subTestCase():
            self.assertFalse(self.ft.exists())
            with self.assertRaises(FileNotFoundError):
                self.ft.clear()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_prerun(self):
        for prerun in self.preruns_notrivial:
            with self.subTestCase(prerun=prerun.__name__):
                self.assertFalse(self.ft.exists())
                with self.assertRaises(FileNotFoundError):
                    _ = prerun()
                self.assertFalse(self.ft.exists())

    def test_nofile_x_keys(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                self.ft.keys()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_len(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                len(self.ft)
            self.assertFalse(self.ft.exists())

    def test_nofile_x_getitem(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft[:]
            self.assertFalse(self.ft.exists())

    def test_nofile_x_rows(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft.rows()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_cols(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft.cols()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_pop(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft.pop()
            self.assertFalse(self.ft.exists())

    def test_nofile_x_shrink1(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft.shrink(1)
            self.assertFalse(self.ft.exists())

    def test_nofile_x_shrink2(self):
        with self.subTestCase():
            with self.assertRaises(FileNotFoundError):
                _ = self.ft.shrink(2)
            self.assertFalse(self.ft.exists())

    def test_prerun_x_getkey(self):

        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                _ = prerun()
                self.assertEqual(self.ft.get_key2type(), const_key2type_extra)

    def test_prerun_x_getfirstrow(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                if prerun in self.preruns_0row:
                    self.assertEqual(self.ft.get_first_row(), {})
                elif prerun in self.preruns_1row:
                    self.assertEqual(self.ft.get_first_row(), {KEY_IDX: 0, **rows[0]})
                elif prerun in self.preruns_2row:
                    self.assertEqual(self.ft.get_first_row(), {KEY_IDX: 0, **rows[0]})

    def test_prerun_x_getlastrow(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                if prerun is self.preruns_0row:
                    self.assertEqual(self.ft.get_last_row(), {})
                elif prerun in self.preruns_1row:
                    self.assertEqual(self.ft.get_last_row(), {KEY_IDX: 0, **rows[-1]})
                elif prerun in self.preruns_2row:
                    self.assertEqual(self.ft.get_last_row(), {KEY_IDX: 1, **rows[-1]})

    def test_prerun_x_exists(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.assertFalse(self.ft.exists())
                self.ft.initialize(key2type=const_key2type)
                self.assertTrue(self.ft.exists())
                _ = prerun()
                self.assertTrue(self.ft.exists())

    def test_prerun_x_delete(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.assertFalse(self.ft.exists())

                self.ft.initialize(key2type=const_key2type)
                self.assertTrue(self.ft.exists())

                _ = prerun()
                self.assertTrue(self.ft.exists())

                self.ft.delete()
                self.assertFalse(self.ft.exists())

    def test_prerun_x_clear(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.assertFalse(self.ft.exists())

                self.ft.initialize(key2type=const_key2type)
                self.assertTrue(self.ft.exists())
                _ = prerun()
                self.assertTrue(self.ft.exists())

                self.ft.clear()
                self.assertTrue(self.ft.exists())
                self.assertEqual(self.ft.get_key2type(), const_key2type_extra)
                self.assertEqual(self.ft.keys(), const_keys_extra)
                self.assertEqual(self.ft.get_first_row(), {})
                self.assertEqual(self.ft.get_last_row(), {})
                self.assertEqual(len(self.ft), 0)
                self.assertEqual(self.ft.rows(), [])

    def test_prerun_append_extend(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                self.assertEqual(self.ft.rows(), rows)

    def test_prerun_x_keys(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                _ = prerun()
                self.assertEqual(self.ft.keys(), const_keys_extra)

    def test_prerun_x_len(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                self.assertEqual(len(self.ft), len(rows))

    def test_prerun_x_getitem(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                self.assertEqual(self.ft[:], rows)

    def test_prerun_x_rows(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                self.assertEqual(self.ft.rows(), rows)

    def test_prerun_x_cols(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                self.assertEqual(self.ft.cols(), rows2cols(rows, const_keys))

    def test_prerun_x_pop(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                res = self.ft.pop()
                if prerun in self.preruns_0row:
                    self.assertEqual(res, {})
                elif prerun in self.preruns_1row:
                    self.assertEqual(res, {KEY_IDX: 0, **rows[-1]})
                elif prerun in self.preruns_2row:
                    self.assertEqual(res, {KEY_IDX: 1, **rows[-1]})
                self.assertEqual(self.ft.rows(), rows[:-1])

    def test_prerun_x_shrink1(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()

                res = self.ft.shrink(1)
                if prerun in self.preruns_0row:
                    self.assertEqual(res, [])
                elif prerun in self.preruns_1row:
                    self.assertEqual(res, [{KEY_IDX: 0, **rows[-1]}])
                elif prerun in self.preruns_2row:
                    self.assertEqual(res, [{KEY_IDX: 1, **rows[-1]}])
                self.assertEqual(self.ft.rows(), rows[:-1])

    def test_prerun_x_shrink2(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                self.ft.initialize(key2type=const_key2type)
                rows = prerun()
                res = self.ft.shrink(2)
                if prerun in self.preruns_0row:
                    self.assertEqual(res, [])
                elif prerun in self.preruns_1row:

                    self.assertEqual(res, [{KEY_IDX: 0, **rows[-1]}])
                elif prerun in self.preruns_2row:
                    actual = res
                    expected = [{KEY_IDX: 1, **rows[-1]}, {KEY_IDX: 0, **rows[-2]}]
                    self.assertEqual(actual, expected, msg=f"\nActual:\n{actual}\nExpected:\n{expected}")
                self.assertEqual(self.ft.rows(), rows[:-2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
