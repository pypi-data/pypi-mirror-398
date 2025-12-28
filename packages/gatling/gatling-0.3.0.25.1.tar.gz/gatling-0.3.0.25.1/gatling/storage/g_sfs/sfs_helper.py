import hashlib
import math
import os
from abc import abstractmethod, ABC
from typing import List


def hash_md5(input_string):
    input_bytes = input_string.encode('utf-8')
    md5_hash = hashlib.md5(input_bytes)
    hex_result = md5_hash.hexdigest()
    return hex_result


def get_hash_folder(filename: str, branches=4096):
    hash_cut = int(math.log2(branches) / math.log2(16))
    return hash_md5(filename)[:hash_cut]


class PathRouter(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def __call__(self, name: str) -> List[str]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class PathRouterTrivial(PathRouter):

    def __init__(self):
        super().__init__()
        pass

    def __call__(self, name: str) -> List[str]:
        return []

    def __len__(self) -> int:
        return 0


class PathRouterBranch(PathRouter):

    def __init__(self, branches=4096):
        super().__init__()
        self.branches = branches
        self.router_fctn = get_hash_folder

    def __call__(self, name: str) -> List[str]:
        return [get_hash_folder(name, self.branches)]

    def __len__(self) -> int:
        return 1


def count_files_or_dirs(dpath):
    return sum(1 for _ in os.scandir(dpath))


def is_empty(dpath):
    return next(os.scandir(dpath), None) is None


def check_safe(dirname: str):
    if '..' in dirname or os.sep in dirname or '/' in dirname or '\\' in dirname:
        raise ValueError(f"Invalid dirname: {dirname}")


if __name__ == '__main__':
    pass

    prt = PathRouterTrivial()
    print(prt('test0.txt'))
    print(prt('test1.txt'))
    print(prt('test2.txt'))

    prb = PathRouterBranch()
    print(prb('test0.txt'))
    print(prb('test1.txt'))
    print(prb('test2.txt'))
