from abc import ABC, abstractmethod
from dataclasses import MISSING
from typing import Literal, Self, Callable, TypeVar, Any

K = TypeVar('K')
V = TypeVar('V')


class BaseDctn(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def set(self, key, value) -> bool:
        """Set a key-value pair.
        Returns:
            True if key was added, False if key was overwritten.
        """
        pass

    @abstractmethod
    def __getitem__(self, item):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __delitem__(self, key):
        pass

    @abstractmethod
    def get(self, key, default=MISSING) -> Any:
        pass

    @abstractmethod
    def pop(self, key, default=MISSING) -> Any:
        pass

    @abstractmethod
    def setmany(self, E=None, **F) -> int:
        pass

    @abstractmethod
    def getmany(self, E=None, **F) -> dict:
        pass

    @abstractmethod
    def popmany(self, E=None, **F) -> dict:
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def values(self):
        pass

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def __contains__(self, item) -> bool:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    def __ne__(self, other) -> bool:
        pass

    @abstractmethod
    def sort(self, by: Literal["key", "value"] | Callable[[K, V], any] = "value", reverse: bool = False) -> Self:
        pass

    @abstractmethod
    def str(self, mode: Literal["inline", "compact", "expand", "json"] = "inline") -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({len(self)})-{id(self)}> {str(self)}"

    def open(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


"""



"""
