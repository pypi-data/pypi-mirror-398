import unittest
import os
import tempfile
import time
from typing import Any

from gatling.utility.io_fctns import save_pickle, read_pickle
from gatling.utility.mem_tools import sizeof


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_speed(size_bytes: int, seconds: float) -> str:
    """Format speed in MB/s."""
    if seconds == 0:
        return "∞ MB/s"
    mb_per_sec = (size_bytes / (1024 * 1024)) / seconds
    return f"{mb_per_sec:.2f} MB/s"


# ==================== Test Classes ====================
class CustomClass:
    """Custom class for testing."""

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
        self.data = list(range(100))

    def __eq__(self, other):
        return (self.name == other.name and
                self.value == other.value and
                self.data == other.data)


class NestedClass:
    """Nested class for testing."""

    def __init__(self):
        self.inner = CustomClass("inner", 42)
        self.items = [CustomClass(f"item_{i}", i) for i in range(10)]

    def __eq__(self, other):
        return self.inner == other.inner and self.items == other.items


class TestPickleFunctions(unittest.TestCase):
    """Test save_pickle and read_pickle functions with various Python objects."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dpath = self.tempdir.name
        self.results = []

    def tearDown(self):
        self.tempdir.cleanup()

    def _run_test(self, name: str, data: Any, compression_level: int = 3):
        """Run a single test case with timing and size measurements."""
        fpath = os.path.join(self.dpath, f'{name}.pkl.zst')

        # Get object size
        obj_size = sizeof(data)

        # Save with timing
        start = time.perf_counter()
        save_pickle(data, fpath, level=compression_level)
        save_time = time.perf_counter() - start

        # Get compressed file size
        compressed_size = os.path.getsize(fpath)
        compression_ratio = (1 - compressed_size / obj_size) * 100 if obj_size > 0 else 0

        # Read with timing
        start = time.perf_counter()
        loaded = read_pickle(fpath)
        read_time = time.perf_counter() - start

        # Print results
        print(f"\n{'=' * 60}")
        print(f"Test: {name}")
        print(f"{'=' * 60}")
        print(f"  Object size (serialized): {format_size(obj_size)}")
        print(f"  Compressed size:          {format_size(compressed_size)}")
        print(f"  Compression ratio:        {compression_ratio:.1f}%")
        print(f"  Save time:                {save_time * 1000:.2f} ms")
        print(f"  Read time:                {read_time * 1000:.2f} ms")
        print(f"  Save speed:               {format_speed(obj_size, save_time)}")
        print(f"  Read speed:               {format_speed(obj_size, read_time)}")

        return loaded

    def test_file_not_found(self):
        """Test reading non-existent file raises FileNotFoundError."""
        fpath = os.path.join(self.dpath, 'not_exist.pkl.zst')
        with self.assertRaises(FileNotFoundError):
            read_pickle(fpath)

    # ==================== Basic Types ====================
    def test_none(self):
        """Test None value."""
        data = None
        result = self._run_test("none", data)
        self.assertIsNone(result)

    def test_bool(self):
        """Test boolean values."""
        for val in [True, False]:
            result = self._run_test(f"bool_{val}", val)
            self.assertEqual(result, val)

    def test_int(self):
        """Test integer values."""
        test_cases = [0, 1, -1, 42, -9999, 10 ** 100, -(10 ** 100)]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"int_{i}", val)
            self.assertEqual(result, val)

    def test_float(self):
        """Test float values."""
        test_cases = [0.0, 3.14159, -2.71828, 1e-100, 1e100, float('inf'), float('-inf')]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"float_{i}", val)
            if val != val:  # NaN check
                self.assertNotEqual(result, result)
            else:
                self.assertEqual(result, val)

    def test_complex(self):
        """Test complex numbers."""
        test_cases = [1 + 2j, -3 - 4j, 0 + 0j, complex(1e10, 1e-10)]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"complex_{i}", val)
            self.assertEqual(result, val)

    def test_string(self):
        """Test string values."""
        test_cases = [
            "",
            "hello",
            "Hello, 世界! 🌍🚀",
            "a" * 10000,
            "\n\t\r\0",
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"string_{i}", val)
            self.assertEqual(result, val)

    def test_bytes(self):
        """Test bytes values."""
        test_cases = [
            b"",
            b"hello",
            bytes(range(256)),
            os.urandom(1000),
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"bytes_{i}", val)
            self.assertEqual(result, val)

    # ==================== Collections ====================
    def test_list(self):
        """Test list values."""
        test_cases = [
            [],
            [1, 2, 3],
            list(range(1000)),
            [[1, 2], [3, 4], [5, 6]],
            [1, "two", 3.0, None, True],
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"list_{i}", val)
            self.assertEqual(result, val)

    def test_tuple(self):
        """Test tuple values."""
        test_cases = [
            (),
            (1, 2, 3),
            tuple(range(1000)),
            ((1, 2), (3, 4)),
            (1, "two", 3.0, None),
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"tuple_{i}", val)
            self.assertEqual(result, val)

    def test_set(self):
        """Test set values."""
        test_cases = [
            set(),
            {1, 2, 3},
            set(range(1000)),
            frozenset([1, 2, 3]),
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"set_{i}", val)
            self.assertEqual(result, val)

    def test_dict(self):
        """Test dictionary values."""
        test_cases = [
            {},
            {"a": 1, "b": 2},
            {i: i ** 2 for i in range(100)},
            {"nested": {"deep": {"value": 42}}},
            {(1, 2): "tuple_key", frozenset([1, 2]): "frozenset_key"},
        ]
        for i, val in enumerate(test_cases):
            result = self._run_test(f"dict_{i}", val)
            self.assertEqual(result, val)

    # ==================== Lambda and Functions ====================
    def test_lambda_simple(self):
        """Test simple lambda functions."""
        data = lambda x: x + 1
        result = self._run_test("lambda_simple", data)
        self.assertEqual(result(10), 11)

    def test_lambda_multi_args(self):
        """Test lambda with multiple arguments."""
        data = lambda x, y, z: x * y + z
        result = self._run_test("lambda_multi_args", data)
        self.assertEqual(result(2, 3, 4), 10)

    def test_lambda_with_closure(self):
        """Test lambda with closure."""
        multiplier = 10
        data = lambda x: x * multiplier
        result = self._run_test("lambda_closure", data)
        self.assertEqual(result(5), 50)

    def test_lambda_nested(self):
        """Test nested lambdas."""
        data = lambda x: (lambda y: x + y)
        result = self._run_test("lambda_nested", data)
        inner = result(10)
        self.assertEqual(inner(5), 15)

    def test_lambda_in_list(self):
        """Test list of lambdas."""
        data = [lambda x: x + i for i in range(5)]
        result = self._run_test("lambda_in_list", data)
        # Note: closure captures final value of i
        for f in result:
            self.assertEqual(f(0), 4)

    def test_lambda_in_dict(self):
        """Test dict of lambdas."""
        data = {
            "add": lambda x, y: x + y,
            "sub": lambda x, y: x - y,
            "mul": lambda x, y: x * y,
        }
        result = self._run_test("lambda_in_dict", data)
        self.assertEqual(result["add"](3, 2), 5)
        self.assertEqual(result["sub"](3, 2), 1)
        self.assertEqual(result["mul"](3, 2), 6)

    def test_regular_function(self):
        """Test regular function."""

        def my_func(x, y=10):
            """A test function with docstring."""
            return x ** 2 + y

        result = self._run_test("regular_function", my_func)
        self.assertEqual(result(3), 19)
        self.assertEqual(result(3, 5), 14)

    def test_recursive_function(self):
        """Test recursive function."""

        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        result = self._run_test("recursive_function", factorial)
        self.assertEqual(result(5), 120)

    # ==================== Classes and Objects ====================
    def test_custom_class_instance(self):
        """Test custom class instance."""
        data = CustomClass("test", 42)
        result = self._run_test("custom_class", data)
        self.assertEqual(result, data)

    def test_nested_class_instance(self):
        """Test nested class instance."""
        data = NestedClass()
        result = self._run_test("nested_class", data)
        self.assertEqual(result, data)

    def test_class_definition(self):
        """Test class definition itself."""

        class TempClass:
            CLASS_VAR = 100

            def method(self, x):
                return x * 2

        result = self._run_test("class_definition", TempClass)
        obj = result()
        self.assertEqual(obj.CLASS_VAR, 100)
        self.assertEqual(obj.method(5), 10)

    # ==================== Large Data ====================
    def test_large_list(self):
        """Test large list."""
        data = list(range(100000))
        result = self._run_test("large_list", data)
        self.assertEqual(result, data)

    def test_large_dict(self):
        """Test large dictionary."""
        data = {f"key_{i}": {"value": i, "data": list(range(10))} for i in range(1000)}
        result = self._run_test("large_dict", data)
        self.assertEqual(result, data)

    def test_large_nested(self):
        """Test large nested structure."""
        data = {
            "users": [
                {
                    "id": i,
                    "name": f"User_{i}",
                    "scores": list(range(100)),
                    "metadata": {"created": i * 1000, "active": i % 2 == 0}
                }
                for i in range(100)
            ],
            "config": {"version": 1, "settings": {f"opt_{i}": i for i in range(50)}}
        }
        result = self._run_test("large_nested", data)
        self.assertEqual(result, data)

    # ==================== Compression Levels ====================
    def test_compression_levels(self):
        """Test different compression levels."""
        data = list(range(50000))

        print(f"\n{'=' * 60}")
        print("Compression Level Comparison")
        print(f"{'=' * 60}")

        obj_size = sizeof(data)
        print(f"Original size: {format_size(obj_size)}")

        for level in [1, 3, 6, 9, 12, 19]:
            fpath = os.path.join(self.dpath, f'level_{level}.pkl.zst')

            start = time.perf_counter()
            save_pickle(data, fpath, level=level)
            save_time = time.perf_counter() - start

            compressed_size = os.path.getsize(fpath)
            ratio = (1 - compressed_size / obj_size) * 100

            start = time.perf_counter()
            loaded = read_pickle(fpath)
            read_time = time.perf_counter() - start

            print(f"\n  Level {level:2d}:")
            print(f"    Compressed: {format_size(compressed_size)} ({ratio:.1f}% reduction)")
            print(f"    Save: {save_time * 1000:.2f}ms ({format_speed(obj_size, save_time)})")
            print(f"    Read: {read_time * 1000:.2f}ms ({format_speed(obj_size, read_time)})")

            self.assertEqual(loaded, data)

    # ==================== Edge Cases ====================
    def test_circular_reference(self):
        """Test circular reference in list."""
        data = [1, 2, 3]
        data.append(data)  # Circular reference

        result = self._run_test("circular_reference", data)
        self.assertEqual(result[:3], [1, 2, 3])
        self.assertIs(result[3], result)

    def test_mixed_complex(self):
        """Test complex mixed structure with lambdas and objects."""
        data = {
            "functions": {
                "double": lambda x: x * 2,
                "square": lambda x: x ** 2,
            },
            "objects": [CustomClass(f"obj_{i}", i) for i in range(10)],
            "nested": {
                "level1": {
                    "level2": {
                        "values": list(range(100)),
                        "transform": lambda arr: [x * 2 for x in arr]
                    }
                }
            },
            "metadata": {
                "version": "1.0",
                "created": 1234567890,
            }
        }

        result = self._run_test("mixed_complex", data)

        # Verify functions work
        self.assertEqual(result["functions"]["double"](5), 10)
        self.assertEqual(result["functions"]["square"](5), 25)

        # Verify objects
        self.assertEqual(len(result["objects"]), 10)

        # Verify nested lambda
        transform = result["nested"]["level1"]["level2"]["transform"]
        self.assertEqual(transform([1, 2, 3]), [2, 4, 6])


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Pickle Functions Performance Test")
    print("=" * 60)

    unittest.main(verbosity=2)
