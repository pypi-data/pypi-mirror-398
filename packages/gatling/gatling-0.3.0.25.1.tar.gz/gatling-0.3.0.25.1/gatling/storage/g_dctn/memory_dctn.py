from typing import Literal, Self, Callable

from gatling.storage.g_dctn.base_dctn import BaseDctn, K, V
from gatling.utility.xstr import dumps_hard, dumps_soft


class MemoryDctn(BaseDctn):
    def __init__(self):
        super().__init__()
        self._dctn = {}

    def clear(self):
        self._dctn.clear()

    def _arg2map(self, E=None, **F) -> dict:
        if E is None:
            return F
        if not isinstance(E, dict):
            E = dict(E)
        return {**E, **F} if F else E

    def _resolve_default(self, key, default):
        """If default is an Exception class, raise it. Otherwise return default."""
        if isinstance(default, type) and issubclass(default, Exception):
            raise default(key)
        return default

    def set(self, key, value) -> bool:
        """Set a key-value pair.

        Returns:
            True if key was added, False if key was overwritten.
        """
        is_new = key not in self._dctn
        self._dctn[key] = value
        return is_new

    def get(self, key, default=KeyError):
        """Get value by key.

        Args:
            key: The key to get.
            default: Default value if key not found. If an Exception class, raises it.

        Returns:
            The value, or default if key not found.
        """
        if key in self._dctn:
            return self._dctn[key]
        return self._resolve_default(key, default)

    def pop(self, key, default=KeyError):
        """Pop value by key.

        Args:
            key: The key to pop.
            default: Default value if key not found. If an Exception class, raises it.

        Returns:
            The value, or default if key not found.
        """
        if key in self._dctn:
            return self._dctn.pop(key)
        return self._resolve_default(key, default)

    def getmany(self, E=None, **F) -> dict:
        """Get multiple values.

        Args:
            E: A dict or iterable of (key, default) pairs.
            **F: Additional key=default pairs.

        Returns:
            Dict of {key: value or default}.
        """
        mapping = self._arg2map(E, **F)
        return {k: self.get(k, v) for k, v in mapping.items()}

    def popmany(self, E=None, **F) -> dict:
        """Pop multiple values.

        Args:
            E: A dict or iterable of (key, default) pairs.
            **F: Additional key=default pairs.

        Returns:
            Dict of {key: value or default}.
        """
        mapping = self._arg2map(E, **F)
        return {k: self.pop(k, v) for k, v in mapping.items()}

    def setmany(self, E=None, **F) -> int:
        """Set multiple key-value pairs.

        Args:
            E: A dict or iterable of (key, value) pairs.
            **F: Additional key=value pairs.

        Returns:
            Number of keys set.
        """
        mapping = self._arg2map(E, **F)
        self._dctn.update(mapping)
        return len(mapping)

    def __getitem__(self, key):
        return self._dctn[key]

    def __setitem__(self, key, value):
        self._dctn[key] = value

    def __delitem__(self, key):
        del self._dctn[key]

    def keys(self):
        return self._dctn.keys()

    def values(self):
        return self._dctn.values()

    def items(self):
        return self._dctn.items()

    def __contains__(self, item) -> bool:
        return item in self._dctn

    def __len__(self) -> int:
        return len(self._dctn)

    def __eq__(self, other) -> bool:
        return self._dctn == dict(other)

    def __ne__(self, other) -> bool:
        return self._dctn != dict(other)

    def sort(self, by: Literal["key", "value"] | Callable[[K, V], any] = "value", reverse: bool = False) -> Self:
        key_func = lambda x: x
        if by == "key":
            key_func = lambda kv: kv[0]
        elif by == "value":
            key_func = lambda kv: kv[1]
        elif callable(by):
            key_func = lambda kv: by(kv[0], kv[1])
        else:
            raise ValueError(f"Invalid sortby: {by}")

        temp_items = self._dctn.items()
        temp_items = sorted(temp_items, key=key_func, reverse=reverse)
        self._dctn = dict(temp_items)
        return self

    # soft dump defaults (reasonable for terminal/logging)
    SOFT_MAX_ITEMS = 20  # collapse if > 20 items
    SOFT_MAX_SIZE = 1024  # collapse if > 4KB
    SOFT_LEVEL = 3  # default indent depth
    DEFAULT_INDENT = 2

    def str(self, level: int = -1, indent: int = DEFAULT_INDENT) -> str:
        """
        Hard dump: complete output, no collapse. support json
        Args:
            level: -1 (full indent), 0 (single line), >0 (indent to level N)
            indent: spaces per level
        """
        return dumps_hard(self._dctn, level=level, indent=indent)

    def __str__(self) -> str:
        """
        Soft dump: safe for large data, collapses big objects to (count)[size].
        Uses reasonable defaults for terminal/logging output.
        """
        return dumps_soft(
            self._dctn,
            level=self.SOFT_LEVEL,
            indent=self.DEFAULT_INDENT,
            max_items=self.SOFT_MAX_ITEMS,
            max_size=self.SOFT_MAX_SIZE
        )


if __name__ == '__main__':
    pass
