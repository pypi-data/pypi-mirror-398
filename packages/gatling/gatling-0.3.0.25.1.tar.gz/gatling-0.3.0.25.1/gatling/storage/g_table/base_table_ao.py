from abc import abstractmethod


class BaseTableAO():

    def __init__(self):
        super().__init__()

    @abstractmethod
    def append(self, row):
        pass

    @abstractmethod
    def extend(self, iterable):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def rows(self):
        pass

    def col(self, key):
        pass

    @abstractmethod
    def __getitem__(self, slice: slice):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)}x{len(self.keys())})-{id(self)}>"

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def exists(self) -> bool:
        pass

    @abstractmethod
    def pop(self) -> dict:
        pass

    @abstractmethod
    def shrink(self, n: int) -> list:
        pass


if __name__ == '__main__':
    pass
