# 🧩 Gatling Utility Library

**Gatling** is a lightweight asynchronous utility library built on `aiohttp`, `asyncio`, and `threading`.
It provides concurrent HTTP requests, coroutine-thread orchestration, data pipelines, and handy file utilities.

---

## 📦 Installation

```bash
pip install gatling
```

---

## 📁 Module Overview

| Module                     | Description                                |
|----------------------------|--------------------------------------------|
| `http_client.py`           | Async/sync HTTP request handling           |
| `file_utils.py`            | Common file read/write helpers             |
| `taskflow_manager.py`      | Multi-stage task pipeline system           |
| `watch.py`                 | Stopwatch and timing tools                 |

---

## 🧵 1. Process & Coroutine & Thread Manager

A hybrid **process + thread + coroutine** manager that can run both sync and async tasks concurrently.

### Example

```python
from gatling.runtime.taskflow_manager import TaskFlowManager
from gatling.storage import MemoryQueue
from gatling.utility.xprint import check_globals_pickable
from gatling.vtasks.sample_tasks import fake_iter_disk, fake_fctn_disk, async_fake_iter_net, async_fake_fctn_net, fake_fctn_cpu, fake_iter_cpu

if __name__ == '__main__':
    pass

    # ---------- Build and run the pipeline ----------
    check_globals_pickable()
    if True:

        q_wait = MemoryQueue()
        # you can push to quque at here
        for i in range(10):
            q_wait.put(i + 1)

        tfm = TaskFlowManager(q_wait, retry_on_error=False)

        # or you can push to queue at here

        with tfm.execute(log_interval=1):
            tfm.register_process(fake_fctn_cpu, worker=2)
            tfm.register_coroutine(async_fake_fctn_net, worker=5)
            tfm.register_thread(fake_fctn_disk, worker=2)

            tfm.register_process(fake_iter_cpu, worker=2)
            tfm.register_coroutine(async_fake_iter_net, worker=8)
            tfm.register_thread(fake_iter_disk, worker=8)

            # or you can push to queue at here

        q_done = tfm.get_qdone()
        results = list(q_done)
        print(f"\n=== Final Results ({len(results)})===")

```

## 🌐 2. HTTP Client Module

**File:** `gatling/utility/http_client.py`

Provides unified async/sync HTTP request helpers supporting `GET`, `POST`, `PUT`, and `DELETE`.

### Example

```python
from gatling.utility.http_fetch_fctns import sync_fetch_http, async_fetch_http, fwrap
import asyncio

target_url = "https://httpbin.org/get"
print("--- Synchronous request ---")
result, status, size = sync_fetch_http(target_url, rtype="json")
print(status, size, result)

print("--- Asynchronous request ---")
result, status, size = asyncio.run(fwrap(async_fetch_http, target_url=target_url, rtype="json"))
print(status, size, result)
```

**Main functions**

* `async_fetch_http(...)`: Generic async HTTP fetcher
* `fwrap(...)`: Safely manages aiohttp session lifecycle
* `sync_fetch_http(...)`: Simple synchronous wrapper (for scripts)

---

## 💾 3. File Utility Module

**File:** `gatling/utility/io_fctns.py`

Convenient helpers for reading and writing JSON, JSONL, Pickle, TOML, text, and byte files.

### Example

```python
from gatling.utility.io_fctns import *

save_json({"a": 1}, "data.json")
print(read_json("data.json"))
remove_file("data.json")

save_jsonl([{"x": 1}, {"x": 2}], "data.jsonl")
print(read_jsonl("data.jsonl"))

remove_file("data.jsonl")

save_text("Hello world", "msg.txt")
print(read_text("msg.txt"))

remove_file("msg.txt")

```

**Main functions**

* `save_json / read_json`
* `save_jsonl / read_jsonl`
* `save_text / read_text`
* `save_pickle / read_pickle`
* `save_bytes / read_bytes`
* `read_toml`
* `remove_file`

---

## ⏱️ 4. Watch Utility

**File:** `gatling/utility/watch.py`

A simple stopwatch for timing operations, plus a decorator for measuring function execution time.

### Example

```python
from gatling.utility.watch import Watch, watch_time
import time


@watch_time
def slow_func():
    time.sleep(1)


slow_func()

w = Watch()
time.sleep(0.5)
print("Δt:", w.see_seconds(), "Total:", w.total_seconds())

```

**Main items**

* `Watch`: Manual stopwatch class for measuring intervals
* `watch_time`: Decorator that prints function execution time

---
