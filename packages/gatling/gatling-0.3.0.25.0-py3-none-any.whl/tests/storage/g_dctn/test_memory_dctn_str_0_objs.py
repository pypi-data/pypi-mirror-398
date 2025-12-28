# Basic types
obj_basic = {
    "string": "hello world",
    "string_cn": "中文测试",
    "int": 42,
    "int_neg": -100,
    "int_zero": 0,
    "int_big": 10 ** 18,
    "float": 3.14159,
    "float_neg": -2.718,
    "float_exp": 1.23e-10,
    "float_zero": 0.0,
    "bool_true": True,
    "bool_false": False,
    "null": None,
}

# String edge cases
obj_string_edge = {
    "string_escape": "line1\nline2\ttab\"quote'单引号",
    "string_tricky": "It's True! None of them, False alarm",
    "string_backslash": "C:\\Users\\test",
    "string_unicode": "emoji 🎉 and \u0000 null",
    "string_json_like": '{"not": "real"}',
    "empty_str": "",
}

# Empty containers
obj_empty = {
    "empty_dict": {},
    "empty_list": [],
    "empty_str": "",
}

# Nested structures
obj_nested = {
    "nested_dict": {
        "level2": {
            "level3": {
                "level4": {"deep": "value"}
            }
        }
    },
    "nested_list": [[[["deep"]]]],
    "mixed_nest": {
        "users": [
            {"name": "Alice", "scores": [95, 87, 92]},
            {"name": "Bob", "scores": [88, 91, 85]}
        ]
    },
}

# Special keys
obj_special_keys = {
    "": "empty key",
    "key with space": "space",
    "key\"quote": "has quote",
    "key'single": "single quote",
    "key\nnewline": "newline in key",
    "123": "numeric string key",
    "True": "key looks like bool",
    "None": "key looks like null",
    "null": "key is literal null word",
}

# Tricky string values (look like other types)
obj_tricky_values = {
    "word_true": "true",
    "word_false": "false",
    "word_null": "null",
    "word_True": "True",
    "word_None": "None",
}

# Mixed type list
obj_list_mixed = {
    "list_mixed": [1, "two", 3.0, True, False, None, {"a": 1}, [1, 2]],
}

# All test cases
memorydctn_objs = [
    obj_basic,
    obj_string_edge,
    obj_empty,
    obj_nested,
    obj_special_keys,
    obj_tricky_values,
    obj_list_mixed,
]
