"""
Dump utilities for nested data structures.
- dumps_soft: collapse large objects to (count)[size] summary
- dumps_hard: indent up to level, flatten deeper content into single line
"""

import json
from typing import Any

from gatling.utility.mem_tools import sizeof


def _get_summary(obj, shown: int = None, trailing: bool = False) -> str:
    """
    Return summary for object.

    Args:
        obj: object to summarize
        shown: number of items already shown (None for collapsed value)
        trailing: if True, this is trailing summary for a list/dict (no type brackets needed)

    Returns:
        - dict: {...(shown/total)[size]...} or ...(shown/total)[size]... if trailing
        - list: [...(shown/total)[size]...] or ...(shown/total)[size]... if trailing
        - str: (len)[size]
        - other: [size]
    """
    size = sizeof(obj)
    if isinstance(obj, dict):
        count_str = f"...({shown if shown is not None else 0}/{len(obj)})[{size}]..."
        if trailing:
            return count_str
        return "{" + count_str + "}"
    elif isinstance(obj, (list, tuple)):
        count_str = f"...({shown if shown is not None else 0}/{len(obj)})[{size}]..."
        if trailing:
            return count_str
        bracket_open = "[" if isinstance(obj, list) else "("
        bracket_close = "]" if isinstance(obj, list) else ")"
        return bracket_open + count_str + bracket_close
    elif isinstance(obj, str):
        return f"({len(obj)})[{size}]"
    else:
        return f"[{size}]"


def _should_collapse(obj, max_items: int, max_size: int) -> bool:
    """Check if object should be collapsed to summary"""
    size = sizeof(obj)
    if size > max_size:
        return True
    if isinstance(obj, dict) and len(obj) > max_items:
        return True
    if isinstance(obj, (list, tuple)) and len(obj) > max_items:
        return True
    return False


def dumps_soft(
        obj: Any,
        level: int = -1,
        indent: int = 2,
        max_items: int = 10,
        max_size: int = 1000,
        show_items: int = 3,
        _depth: int = 0
) -> str:
    """
    Soft dump: collapse large objects to (count)[size] summary.

    Args:
        obj: object to dump
        level: max indent depth (-1 for unlimited, 0 for single line)
        indent: spaces per indent level
        max_items: collapse if item count exceeds this
        max_size: collapse if byte size exceeds this
        show_items: show first N items before collapsing (0 = show nothing, capped at max_items)
        _depth: internal use for recursion

    Returns:
        formatted string representation
    """
    # cap show_items at max_items
    show_items = min(show_items, max_items)

    ind = " " * (indent * _depth)
    ind_next = " " * (indent * (_depth + 1))

    # level 0: single line
    if level == 0:
        if _should_collapse(obj, max_items, max_size):
            return _get_summary(obj)
        return json.dumps(obj, ensure_ascii=False)

    # beyond depth limit
    if level > 0 and _depth >= level:
        if _should_collapse(obj, max_items, max_size):
            return _get_summary(obj)
        return json.dumps(obj, ensure_ascii=False)

    if isinstance(obj, dict):
        if not obj:
            return "{}"

        should_collapse_dict = _should_collapse(obj, max_items, max_size)
        items = []
        shown_count = 0

        for k, v in obj.items():
            # if dict should collapse and we've shown enough
            if should_collapse_dict and shown_count >= show_items:
                break

            key_str = json.dumps(k, ensure_ascii=False)
            if _should_collapse(v, max_items, max_size):
                val_str = _get_summary(v)  # collapsed value: include type brackets
            else:
                val_str = dumps_soft(v, level, indent, max_items, max_size, show_items, _depth + 1)
            items.append(f"{ind_next}{key_str}: {val_str}")
            shown_count += 1

        # add collapse summary if not all shown (trailing: no type brackets needed)
        if shown_count < len(obj):
            items.append(f"{ind_next}{_get_summary(obj, shown_count, trailing=True)}")

        return "{\n" + ",\n".join(items) + f"\n{ind}}}"

    elif isinstance(obj, (list, tuple)):
        if not obj:
            return "[]" if isinstance(obj, list) else "()"

        bracket_open = "[" if isinstance(obj, list) else "("
        bracket_close = "]" if isinstance(obj, list) else ")"

        should_collapse_list = _should_collapse(obj, max_items, max_size)
        items = []
        shown_count = 0

        for i, item in enumerate(obj):
            # if list should collapse and we've shown enough
            if should_collapse_list and shown_count >= show_items:
                break

            if _should_collapse(item, max_items, max_size):
                # collapsed item: show index and type brackets
                val_str = f"#{i}: {_get_summary(item)}"
            else:
                # full item: no index, keep original structure
                val_str = dumps_soft(item, level, indent, max_items, max_size, show_items, _depth + 1)
            items.append(f"{ind_next}{val_str}")
            shown_count += 1

        # add collapse summary if not all shown (trailing: no type brackets needed)
        if shown_count < len(obj):
            items.append(f"{ind_next}{_get_summary(obj, shown_count, trailing=True)}")

        return f"{bracket_open}\n" + ",\n".join(items) + f"\n{ind}{bracket_close}"

    else:
        return json.dumps(obj, ensure_ascii=False)


def dumps_hard(
        obj: Any,
        level: int = -1,
        indent: int = 2,
        max_items: int = None,
        max_size: int = None,
        show_items: int = None,
        _depth: int = 0
) -> str:
    """
    Hard dump: indent up to level, flatten deeper content into single line.

    Args:
        obj: object to dump
        level: max indent depth (-1 for unlimited, 0 for single line)
        indent: spaces per indent level
        max_items: ignored (for interface compatibility)
        max_size: ignored (for interface compatibility)
        show_items: ignored (for interface compatibility)
        _depth: internal use for recursion

    Returns:
        formatted JSON string
    """
    if level == 0:
        return json.dumps(obj, ensure_ascii=False)

    if level == -1:
        return json.dumps(obj, ensure_ascii=False, indent=indent)

    if _depth >= level:
        return json.dumps(obj, ensure_ascii=False)

    ind = " " * (indent * _depth)
    ind_next = " " * (indent * (_depth + 1))

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = []
        for k, v in obj.items():
            key_str = json.dumps(k, ensure_ascii=False)
            val_str = dumps_hard(v, level, indent, _depth=_depth + 1)
            items.append(f"{ind_next}{key_str}: {val_str}")
        return "{\n" + ",\n".join(items) + f"\n{ind}}}"

    elif isinstance(obj, (list, tuple)):
        if not obj:
            return "[]" if isinstance(obj, list) else "()"
        bracket_open = "[" if isinstance(obj, list) else "("
        bracket_close = "]" if isinstance(obj, list) else ")"
        items = []
        for item in obj:
            val_str = dumps_hard(item, level, indent, _depth=_depth + 1)
            items.append(f"{ind_next}{val_str}")
        return f"{bracket_open}\n" + ",\n".join(items) + f"\n{ind}{bracket_close}"

    else:
        return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    test_data = {
        "small": {"a": 1, "b": 2},
        "big_list": list(range(100)),
        "nested": {
            "level1": {
                "level2": {
                    "huge": list(range(1000))
                }
            }
        },
        "users": [
            {"name": "Alice", "scores": list(range(50))},
            {"name": "Bob", "scores": list(range(50))},
            {"name": "Charlie", "scores": list(range(50))},
            {"name": "David", "scores": list(range(50))},
            {"name": "Eve", "scores": list(range(50))},
        ],
        "simple_list": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    }

    print("=== dumps_soft show_items=3 ===")
    print(dumps_soft(test_data, level=3, max_items=5, max_size=500, show_items=3))

    print("\n=== dumps_soft show_items=0 (no items, keep brackets) ===")
    print(dumps_soft(test_data, level=3, max_items=5, max_size=500, show_items=0))

    print("\n=== List example: users ===")
    print(dumps_soft(test_data["users"], level=2, max_items=3, max_size=500, show_items=2))

    print("\n=== List example: big_list ===")
    print(dumps_soft(test_data["big_list"], level=2, max_items=5, max_size=200, show_items=3))
