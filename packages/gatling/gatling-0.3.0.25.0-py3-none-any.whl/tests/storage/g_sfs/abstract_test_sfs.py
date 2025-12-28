import tempfile
import unittest
from typing import Optional

from gatling.storage.g_sfs.sfs_helper import PathRouterTrivial, PathRouterBranch
from gatling.storage.g_sfs.sfs_main import SuperFileSystem
from gatling.ztest.subtestcase import SubTestCase


class TestSFS(SubTestCase):

    def prerun_sfs_trivial(self):
        self.sfs = SuperFileSystem(dbname='test_db', path_router=PathRouterTrivial())

    def prerun_sfs_branch(self):
        self.sfs = SuperFileSystem(dbname='test_db', path_router=PathRouterBranch())

    def setUp(self):
        self.preruns = [self.prerun_sfs_trivial, self.prerun_sfs_branch]

    def tearDown(self):
        pass

    def subSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        SuperFileSystem.config(dpath_root=self.temp_dir.name)
        self.sfs: Optional[SuperFileSystem] = None


    def subTearDown(self):
        pass
        self.temp_dir.cleanup()

    def test_00_empty(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                res = self.sfs.list_dirs()
                self.assertEqual(res, set())

    def test_01_empty(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                res = self.sfs.list_files()
                self.assertEqual(res, set())

    def test_10_delete_non_empty_db(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.delete(force=True)
                res = self.sfs.list_dirs()
                self.assertEqual(res, set())

    def test_11_delete_empty_db(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.delete(force=True)
                res = self.sfs.list_dirs()
                self.assertEqual(res, set())

    def test_20_create_new_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                res = self.sfs.list_dirs()
                self.assertEqual(res, {'folder1'})

    def test_21_create_exist_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.mkdir('folder1')
                res = self.sfs.list_dirs()
                self.assertEqual(res, {'folder1'})

    def test_22_exists_true_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                res = self.sfs.exists('folder1')
                self.assertTrue(res)

    def test_23_exists_false_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                res = self.sfs.exists('folder2')
                self.assertFalse(res)

    def test_22_remove_exist_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.rmdir('folder1')
                res = self.sfs.list_dirs()
                self.assertEqual(res, set())

    def test_23_remove_non_exist_folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.rmdir('folder2')
                res = self.sfs.list_dirs()
                self.assertEqual(res, {'folder1'})

    def test_30_create_3folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.mkdir('folder2')
                self.sfs.mkdir('folder3')
                res = self.sfs.list_dirs()
                self.assertEqual(res, {'folder1', 'folder2', 'folder3'})

    def test_31_exists_3folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.mkdir('folder2')
                self.sfs.mkdir('folder3')
                res1 = self.sfs.exists('folder1')
                res2 = self.sfs.exists('folder2')
                res3 = self.sfs.exists('folder3')
                self.assertTrue(res1)
                self.assertTrue(res2)
                self.assertTrue(res3)

    def test_32_remove_3folder(self):
        for prerun in self.preruns:
            with self.subTestCase(prerun=prerun.__name__):
                prerun()
                self.sfs.mkdir('folder1')
                self.sfs.mkdir('folder2')
                self.sfs.mkdir('folder3')
                self.sfs.rmdir('folder1')
                self.sfs.rmdir('folder2')
                self.sfs.rmdir('folder3')

                res = self.sfs.list_dirs()
                self.assertEqual(res, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
    pass
