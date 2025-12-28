import unittest
import os
import tempfile
import orjson
import sys
from io import StringIO
from gatling.utility.io_fctns import read_json, save_json, read_jsonl, save_jsonl


class TestIOFunctions(unittest.TestCase):
    """Test read/save functions for JSON and JSONL files"""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dpath = self.tempdir.name
        self._stderr = sys.stderr
        sys.stderr = StringIO()
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        self.tempdir.cleanup()
        sys.stderr = self._stderr
        sys.stdout = self._stdout

    # ==================== read_json ====================
    def test_read_json_simple(self):
        """Test reading a simple JSON file"""
        fpath = os.path.join(self.dpath, 'simple.json')
        data = {'name': 'test', 'value': 123}
        with open(fpath, 'wb') as f:
            f.write(orjson.dumps(data))

        result = read_json(fpath)
        self.assertEqual(result, data)

    def test_read_json_nested(self):
        """Test reading nested JSON structure"""
        fpath = os.path.join(self.dpath, 'nested.json')
        data = {
            'user': {
                'name': 'Alice',
                'address': {'city': 'New York', 'zip': '10001'}
            },
            'tags': ['a', 'b', 'c']
        }
        with open(fpath, 'wb') as f:
            f.write(orjson.dumps(data))

        result = read_json(fpath)
        self.assertEqual(result, data)

    def test_read_json_array(self):
        """Test reading JSON array as root"""
        fpath = os.path.join(self.dpath, 'array.json')
        data = [1, 2, 3, {'a': 1}]
        with open(fpath, 'wb') as f:
            f.write(orjson.dumps(data))

        result = read_json(fpath)
        self.assertEqual(result, data)

    def test_read_json_special_types(self):
        """Test reading JSON with null, bool, numbers"""
        fpath = os.path.join(self.dpath, 'special.json')
        data = {'null_val': None, 'bool_true': True, 'bool_false': False, 'float': 3.14, 'negative': -100}
        with open(fpath, 'wb') as f:
            f.write(orjson.dumps(data))

        result = read_json(fpath)
        self.assertEqual(result, data)

    def test_read_json_unicode(self):
        """Test reading JSON with unicode characters"""
        fpath = os.path.join(self.dpath, 'unicode.json')
        data = {'name': 'Alice', 'emoji': '😀🎉', 'chinese': '你好'}
        with open(fpath, 'wb') as f:
            f.write(orjson.dumps(data))

        result = read_json(fpath)
        self.assertEqual(result, data)

    def test_read_json_empty_object(self):
        """Test reading empty JSON object"""
        fpath = os.path.join(self.dpath, 'empty_obj.json')
        with open(fpath, 'wb') as f:
            f.write(b'{}')

        result = read_json(fpath)
        self.assertEqual(result, {})

    def test_read_json_empty_array(self):
        """Test reading empty JSON array"""
        fpath = os.path.join(self.dpath, 'empty_arr.json')
        with open(fpath, 'wb') as f:
            f.write(b'[]')

        result = read_json(fpath)
        self.assertEqual(result, [])

    def test_read_json_empty_file(self):
        """Test reading empty file returns None"""
        fpath = os.path.join(self.dpath, 'empty.json')
        with open(fpath, 'wb') as _:
            pass

        result = read_json(fpath)
        self.assertIsNone(result)

    def test_read_json_invalid(self):
        """Test reading invalid JSON returns None"""
        fpath = os.path.join(self.dpath, 'invalid.json')
        with open(fpath, 'wb') as f:
            f.write(b'{invalid json}')

        result = read_json(fpath)
        self.assertIsNone(result)

    def test_read_json_not_found(self):
        """Test reading non-existent file raises FileNotFoundError"""
        fpath = os.path.join(self.dpath, 'not_exist.json')
        with self.assertRaises(FileNotFoundError):
            read_json(fpath)

    # ==================== save_json ====================
    def test_save_json_simple(self):
        """Test saving a simple JSON file"""
        fpath = os.path.join(self.dpath, 'save_simple.json')
        data = {'name': 'test', 'value': 456}

        result = save_json(data, fpath)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(fpath))
        self.assertEqual(read_json(fpath), data)

    def test_save_json_nested(self):
        """Test saving nested JSON structure"""
        fpath = os.path.join(self.dpath, 'save_nested.json')
        data = {'level1': {'level2': {'level3': [1, 2, 3]}}}

        result = save_json(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), data)

    def test_save_json_array(self):
        """Test saving JSON array as root"""
        fpath = os.path.join(self.dpath, 'save_array.json')
        data = [{'id': 1}, {'id': 2}]

        result = save_json(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), data)

    def test_save_json_special_types(self):
        """Test saving JSON with null, bool, numbers"""
        fpath = os.path.join(self.dpath, 'save_special.json')
        data = {'null_val': None, 'bool_true': True, 'bool_false': False, 'float': 3.14159, 'negative': -100}

        result = save_json(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), data)

    def test_save_json_unicode(self):
        """Test saving JSON with unicode characters"""
        fpath = os.path.join(self.dpath, 'save_unicode.json')
        data = {'name': 'Bob', 'emoji': '🎉', 'japanese': 'こんにちは'}

        result = save_json(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), data)

    def test_save_json_empty_object(self):
        """Test saving empty JSON object"""
        fpath = os.path.join(self.dpath, 'save_empty_obj.json')

        result = save_json({}, fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), {})

    def test_save_json_empty_array(self):
        """Test saving empty JSON array"""
        fpath = os.path.join(self.dpath, 'save_empty_arr.json')

        result = save_json([], fpath)
        self.assertTrue(result)
        self.assertEqual(read_json(fpath), [])

    def test_save_json_indent(self):
        """Test saving JSON with indentation"""
        fpath = os.path.join(self.dpath, 'save_indent.json')
        data = {'a': 1, 'b': 2}

        result = save_json(data, fpath, indent=True)
        self.assertTrue(result)

        with open(fpath, 'rb') as f:
            content = f.read()
        self.assertIn(b'\n', content)

    def test_save_json_overwrite(self):
        """Test overwriting existing file"""
        fpath = os.path.join(self.dpath, 'overwrite.json')
        save_json({'old': 1}, fpath)
        save_json({'new': 2}, fpath)

        result = read_json(fpath)
        self.assertEqual(result, {'new': 2})

    def test_save_json_invalid_path(self):
        """Test saving to invalid path returns False"""
        fpath = '/invalid_path/no_permission/test.json'
        result = save_json({'a': 1}, fpath)
        self.assertFalse(result)

    # ==================== read_jsonl ====================
    def test_read_jsonl_simple(self):
        """Test reading a simple JSONL file"""
        fpath = os.path.join(self.dpath, 'simple.jsonl')
        data = [{'id': 1}, {'id': 2}, {'id': 3}]
        with open(fpath, 'wb') as f:
            f.write(b'\n'.join(orjson.dumps(d) for d in data))

        result = read_jsonl(fpath)
        self.assertEqual(result, data)

    def test_read_jsonl_single_line(self):
        """Test reading JSONL with single line"""
        fpath = os.path.join(self.dpath, 'single.jsonl')
        with open(fpath, 'wb') as f:
            f.write(b'{"id": 1}')

        result = read_jsonl(fpath)
        self.assertEqual(result, [{'id': 1}])

    def test_read_jsonl_nested(self):
        """Test reading JSONL with nested objects"""
        fpath = os.path.join(self.dpath, 'nested.jsonl')
        data = [{'user': {'name': 'Alice', 'info': {'age': 20}}}, {'user': {'name': 'Bob', 'info': {'age': 30}}}]
        with open(fpath, 'wb') as f:
            f.write(b'\n'.join(orjson.dumps(d) for d in data))

        result = read_jsonl(fpath)
        self.assertEqual(result, data)

    def test_read_jsonl_special_types(self):
        """Test reading JSONL with null, bool, numbers"""
        fpath = os.path.join(self.dpath, 'special.jsonl')
        data = [{'val': None}, {'val': True}, {'val': False}, {'val': 3.14}, {'val': -100}]
        with open(fpath, 'wb') as f:
            f.write(b'\n'.join(orjson.dumps(d) for d in data))

        result = read_jsonl(fpath)
        self.assertEqual(result, data)

    def test_read_jsonl_unicode(self):
        """Test reading JSONL with unicode characters"""
        fpath = os.path.join(self.dpath, 'unicode.jsonl')
        data = [{'name': 'Alice', 'emoji': '😀'}, {'name': 'Bob', 'chinese': '你好'}]
        with open(fpath, 'wb') as f:
            f.write(b'\n'.join(orjson.dumps(d) for d in data))

        result = read_jsonl(fpath)
        self.assertEqual(result, data)

    def test_read_jsonl_empty_lines(self):
        """Test reading JSONL with empty lines"""
        fpath = os.path.join(self.dpath, 'empty_lines.jsonl')
        with open(fpath, 'wb') as f:
            f.write(b'{"id": 1}\n\n{"id": 2}\n\n')

        result = read_jsonl(fpath)
        self.assertEqual(len(result), 2)

    def test_read_jsonl_empty_file(self):
        """Test reading empty JSONL file"""
        fpath = os.path.join(self.dpath, 'empty.jsonl')
        with open(fpath, 'wb') as _:
            pass

        result = read_jsonl(fpath)
        self.assertEqual(result, [])

    def test_read_jsonl_partial_invalid(self):
        """Test reading JSONL with some invalid lines"""
        fpath = os.path.join(self.dpath, 'partial_invalid.jsonl')
        with open(fpath, 'wb') as f:
            f.write(b'{"id": 1}\n{invalid}\n{"id": 3}')

        result = read_jsonl(fpath)
        self.assertEqual(len(result), 2)

    def test_read_jsonl_many_lines(self):
        """Test reading JSONL with many lines"""
        fpath = os.path.join(self.dpath, 'many.jsonl')
        data = [{'id': i} for i in range(1000)]
        with open(fpath, 'wb') as f:
            f.write(b'\n'.join(orjson.dumps(d) for d in data))

        result = read_jsonl(fpath)
        self.assertEqual(len(result), 1000)
        self.assertEqual(result[0], {'id': 0})
        self.assertEqual(result[-1], {'id': 999})

    def test_read_jsonl_not_found(self):
        """Test reading non-existent JSONL raises FileNotFoundError"""
        fpath = os.path.join(self.dpath, 'not_exist.jsonl')
        with self.assertRaises(FileNotFoundError):
            read_jsonl(fpath)

    # ==================== save_jsonl ====================
    def test_save_jsonl_simple(self):
        """Test saving a simple JSONL file"""
        fpath = os.path.join(self.dpath, 'save_simple.jsonl')
        data = [{'id': 1}, {'id': 2}, {'id': 3}]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(fpath))
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_single_item(self):
        """Test saving JSONL with single item"""
        fpath = os.path.join(self.dpath, 'save_single.jsonl')
        data = [{'id': 1}]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_nested(self):
        """Test saving JSONL with nested objects"""
        fpath = os.path.join(self.dpath, 'save_nested.jsonl')
        data = [{'user': {'info': {'age': 20}}}, {'user': {'info': {'age': 30}}}]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_special_types(self):
        """Test saving JSONL with null, bool, numbers"""
        fpath = os.path.join(self.dpath, 'save_special.jsonl')
        data = [{'val': None}, {'val': True}, {'val': False}, {'val': -99.99}]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_unicode(self):
        """Test saving JSONL with unicode characters"""
        fpath = os.path.join(self.dpath, 'save_unicode.jsonl')
        data = [{'name': 'Charlie', 'korean': '안녕하세요'}, {'name': 'Diana', 'emoji': '🚀'}]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_empty(self):
        """Test saving empty JSONL"""
        fpath = os.path.join(self.dpath, 'save_empty.jsonl')

        result = save_jsonl([], fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), [])

    def test_save_jsonl_many_items(self):
        """Test saving JSONL with many items"""
        fpath = os.path.join(self.dpath, 'save_many.jsonl')
        data = [{'id': i, 'value': f'item_{i}'} for i in range(1000)]

        result = save_jsonl(data, fpath)
        self.assertTrue(result)
        self.assertEqual(read_jsonl(fpath), data)

    def test_save_jsonl_overwrite(self):
        """Test overwriting existing JSONL file"""
        fpath = os.path.join(self.dpath, 'overwrite.jsonl')
        save_jsonl([{'old': 1}], fpath)
        save_jsonl([{'new': 2}], fpath)

        result = read_jsonl(fpath)
        self.assertEqual(result, [{'new': 2}])

    def test_save_jsonl_invalid_path(self):
        """Test saving to invalid path returns False"""
        fpath = '/invalid_path/no_permission/test.jsonl'
        result = save_jsonl([{'a': 1}], fpath)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)