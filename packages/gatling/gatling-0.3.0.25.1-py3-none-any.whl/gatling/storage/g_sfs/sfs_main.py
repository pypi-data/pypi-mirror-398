import os
import shutil
from pathlib import Path
from typing import Optional

from gatling.storage.g_sfs.sfs_helper import PathRouterTrivial, PathRouter, PathRouterBranch, is_empty, check_safe


class SuperFileSystem:
    dpath_root = None

    @classmethod
    def config(cls, dpath_root: str):
        cls.dpath_root = dpath_root
        os.makedirs(cls.dpath_root, exist_ok=True)

    def __init__(self, dbname: str, path_router: Optional[PathRouter] = None):
        self.dbname: str = dbname

        if self.__class__.dpath_root is None:
            raise ValueError("SuperFileSystem not configured. Call SuperFileSystem.config(dpath_root) with a valid directory path.")

        self.dpath_root_dbname: str = os.path.join(self.__class__.dpath_root, self.dbname)
        os.makedirs(self.dpath_root_dbname, exist_ok=True)
        if path_router is None:
            self.path_router: PathRouter = PathRouterTrivial()
        else:
            self.path_router: PathRouter = path_router

        print(f"Create SFS-database at {self.dpath_root_dbname}")

    def delete(self, force: bool = False) -> bool:
        if not force:
            confirm = input(f"Are you sure you want to delete all data at {self.dpath_root_dbname}? (confirm/no): ")
            if confirm.lower().strip() != 'confirm':
                print("Deletion aborted.")
                return False
        shutil.rmtree(self.dpath_root_dbname)
        return True

    def exists(self, dirname: str) -> bool:
        subpaths = self.path_router(dirname)
        dpath = os.path.join(self.dpath_root_dbname, *subpaths, dirname)
        return os.path.exists(dpath)

    def mkdir(self, dirname: str, logfctn=None) -> str:
        check_safe(dirname)
        subpaths = self.path_router(dirname)
        dpath = os.path.join(self.dpath_root_dbname, *subpaths, dirname)
        if os.path.exists(dpath):
            if logfctn is not None:
                logfctn(f"Directory already exists at {dpath}")
        else:
            os.makedirs(dpath, exist_ok=True)
            if logfctn is not None:
                logfctn(f"Created directory at {dpath}")
        return dpath

    def rmdir(self, dirname: str) -> bool:
        check_safe(dirname)
        subpaths = self.path_router(dirname)
        dpath_root_dbname_subpaths = os.path.join(self.dpath_root_dbname, *subpaths)
        dpath = os.path.join(dpath_root_dbname_subpaths, dirname)
        if os.path.exists(dpath):
            shutil.rmtree(dpath)
            print(f"Deleted directory at {dpath}")
            for i in range(len(subpaths), 0, -1):
                current = os.path.join(self.dpath_root_dbname, *subpaths[:i])
                if is_empty(current):
                    os.rmdir(current)
                else:
                    break
            return True
        else:
            print(f"No directory at {dpath}")
            return False

    def list_files(self):
        pattern = '/'.join(['*'] * (len(self.path_router) + 1))
        return {f.name for f in Path(self.dpath_root_dbname).glob(pattern) if f.is_file()}

    def list_dirs(self):
        pattern = '/'.join(['*'] * (len(self.path_router) + 1))
        return {f.name for f in Path(self.dpath_root_dbname).glob(pattern) if f.is_dir()}


if __name__ == "__main__":
    dpath_root_sfs = r'D:\d_database\sfs'

    print(dpath_root_sfs)

    SuperFileSystem.config(dpath_root_sfs)

    sfst = SuperFileSystem('test_trivial')
    sfst.mkdir('test1')
    sfst.mkdir('test2')
    sfst.mkdir('test3')

    sfsb = SuperFileSystem('test_branch', path_router=PathRouterBranch())
    sfsb.mkdir('test1')
    sfsb.mkdir('test2')
    sfsb.mkdir('test3')

    sfst.delete()
    sfsb.delete()
