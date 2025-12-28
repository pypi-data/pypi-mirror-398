import sys


def sizeof(obj, seen=None) -> int:
    """Recursively calculate total size of object and all nested objects"""
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(sizeof(k, seen) + sizeof(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(sizeof(i, seen) for i in obj)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        pass
    else:
        if hasattr(obj, '__dict__'):
            size += sizeof(obj.__dict__, seen)
        if hasattr(obj, '__slots__'):
            for slot in obj.__slots__:
                if hasattr(obj, slot):
                    size += sizeof(getattr(obj, slot), seen)

    return size
