from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseQueue(ABC, Generic[T]):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def put(self, item: T, block=True, timeout=None):
        pass

    @abstractmethod
    def get(self, block=True, timeout=None) -> T:
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)})-{id(self)}>"

    def open(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    pass
