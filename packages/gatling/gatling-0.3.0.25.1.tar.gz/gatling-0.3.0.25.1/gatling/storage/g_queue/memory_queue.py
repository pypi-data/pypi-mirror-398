import queue
from gatling.storage.g_queue.base_queue import BaseQueue


class MemoryQueue(BaseQueue):
    """Thread-safe in-memory queue with optional exclusive access control."""

    def __init__(self, maxsize=0):
        super().__init__()
        self._queue = queue.Queue(maxsize=maxsize)

    def put(self, item, block=False, timeout=None):
        self._queue.put(item, block=block, timeout=timeout)

    def get(self, block=False, timeout=None):
        return self._queue.get(block=block, timeout=timeout)

    def clear(self):
        self._queue.queue.clear()

    def __len__(self):
        return self._queue.qsize()

    def __iter__(self):
        return iter(list(self._queue.queue))


if __name__ == '__main__':
    pass
