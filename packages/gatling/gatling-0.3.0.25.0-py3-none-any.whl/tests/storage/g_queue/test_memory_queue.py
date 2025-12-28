import unittest
import threading
from queue import Empty, Full
from gatling.storage.g_queue.memory_queue import MemoryQueue

Item_A = "A"
Item_B = "B"
Item_C = "C"


class TestMemoryQueue(unittest.TestCase):
    """Unit tests for MemoryQueue class."""

    def test_basic_put_get_len(self):
        q = MemoryQueue()
        q.put(Item_A)
        q.put(Item_B)
        self.assertEqual(len(q), 2)
        self.assertEqual(q.get(), Item_A)
        self.assertEqual(q.get(), Item_B)
        self.assertEqual(len(q), 0)

    def test_put_raise_full(self):
        q = MemoryQueue(maxsize=1)
        q.put(Item_A)
        with self.assertRaises(Full):
            q.put(Item_B)

    def test_get_raise_empty(self):
        q = MemoryQueue()
        with self.assertRaises(Empty):
            q.get()

    def test_clear_queue(self):
        q = MemoryQueue()
        q.put(Item_A)
        q.put(Item_B)
        self.assertEqual(len(q), 2)
        q.clear()
        self.assertEqual(len(q), 0)

    def test_len_and_iter(self):
        q = MemoryQueue()
        q.put(Item_A)
        q.put(Item_B)
        q.put(Item_C)
        self.assertEqual(len(q), 3)
        items = list(q)
        self.assertEqual(items, [Item_A, Item_B, Item_C])

    def test_thread_safe_put_get(self):
        q = MemoryQueue()
        results = []

        def producer():
            for i in range(5):
                q.put(i)

        def consumer():
            for _ in range(5):
                results.append(q.get())

        t1 = threading.Thread(target=producer)
        t2 = threading.Thread(target=consumer)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(sorted(results), [0, 1, 2, 3, 4])
        self.assertTrue(q._queue.empty())

    def test_open_and_close(self):
        q = MemoryQueue()
        try:
            q.open()
            q.close()
        except Exception as e:
            self.fail(f"open/close raised unexpectedly: {e}")

    def test_context_manager(self):
        q = MemoryQueue()
        try:
            with q:
                pass
        except Exception as e:
            self.fail(f"context manager raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
