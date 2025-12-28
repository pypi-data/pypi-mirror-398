import asyncio
import queue
import threading
import traceback
from concurrent.futures import Future
from typing import Callable, Optional, Any

from gatling.runtime.task_manager.coroutine_executor import CoroutineExecutor
from gatling.runtime.task_manager.runtime_task_manager_base import RuntimeTaskManager
from gatling.storage.g_queue.base_queue import BaseQueue
from gatling.storage.g_queue.memory_queue import MemoryQueue
from gatling.utility.xprint import print_flush


async def async_producer_fctn_loop(fctn, qwait, qwork, qerrr, qdone, asyncio_stop_event, retry_on_error, retry_empty_interval, errlogfctn):
    while True:
        try:
            arg = qwait.get(block=False)
            qwork.put(arg)
            try:
                res = await fctn(arg)
                qdone.put(res)
            except Exception:
                errlogfctn(traceback.format_exc())
                qerrr.put(arg)
                if retry_on_error:
                    errlogfctn(f"retry on error : {arg}")
                    qwait.put(arg)
            finally:
                qwork.get(block=False)
        except queue.Empty:
            if asyncio_stop_event.is_set():
                break
            else:
                await asyncio.sleep(retry_empty_interval)


class RuntimeTaskManagerCoroutineFunction(RuntimeTaskManager):

    def __init__(self, fctn: Callable,
                 qwait: BaseQueue[Any],
                 qwork: BaseQueue[Future],
                 qerrr: BaseQueue[Any],
                 qdone: BaseQueue[Any],
                 worker: int = 1,
                 retry_on_error:bool=False,
                 retry_empty_interval=0.001,
                 errlogfctn=print_flush):
        super().__init__(fctn, qwait, qwork, qerrr, qdone, worker=worker, retry_on_error=retry_on_error,retry_empty_interval=retry_empty_interval)

        self.asyncio_stop_event: asyncio.Event = asyncio.Event()  # False
        self.asyncio_running_executor: Optional[CoroutineExecutor] = None
        self.errlogfctn = errlogfctn
        self.producers = []

    def __len__(self):
        return 0 if (self.asyncio_running_executor is None) else self.asyncio_running_executor.max_workers

    def __str__(self):
        return "CoFn" + super().__str__()

    def start(self, worker):

        if self.asyncio_running_executor is not None:
            raise RuntimeError(f"{str(self)} already started")
        if self.asyncio_stop_event.is_set():
            raise RuntimeError(f"{str(self)} is stopping")

        self.errlogfctn(f"{self} start triggered ... ")
        self.asyncio_running_executor = CoroutineExecutor(max_workers=worker, logfctn=self.errlogfctn)

        # submit coroutine task
        producer_thread = threading.Thread(target=self.asyncio_running_executor.submit, args=(async_producer_fctn_loop, self.fctn, self.qwait, self.qwork, self.qerrr, self.qdone, self.asyncio_stop_event, self.retry_on_error, self.retry_empty_interval, self.errlogfctn), daemon=True)
        producer_thread.start()
        self.producers.append(producer_thread)

        self.errlogfctn(f"{str(self)} started >>>")

    def stop(self):
        if self.asyncio_running_executor is None:
            return False
        if self.asyncio_stop_event.is_set():
            return False

        self.errlogfctn(f"{self} stop triggered ... ")
        self.asyncio_stop_event.set()

        for producer_thread in self.producers:
            producer_thread.join()
        self.producers.clear()

        self.asyncio_running_executor_worker = 0

        self.asyncio_stop_event.clear()

        self.errlogfctn(f"{str(self)} stopped !!!")
        return True


if __name__ == '__main__':
    pass

    from gatling.vtasks.sample_tasks import async_fake_fctn_net

    rt = RuntimeTaskManagerCoroutineFunction(async_fake_fctn_net, qwait=MemoryQueue(), qwork=MemoryQueue(), qerrr=MemoryQueue(), qdone=MemoryQueue())

    with rt.execute(worker=5, log_interval=1, logfctn=print_flush):
        for i in range(10):
            rt.qwait.put(i)

    print(f"[{len(rt.qdone)}] : {list(rt.qdone)}")
