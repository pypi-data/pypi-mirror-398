import asyncio
import inspect
import threading
import time
from contextlib import contextmanager
from datetime import timedelta
from typing import Callable, List, Any

from gatling.runtime.task_manager.runtime_task_manager_base import RuntimeTaskManager
from gatling.runtime.task_manager.runtime_task_manager_process_function import RuntimeTaskManagerProcessFunction
from gatling.runtime.task_manager.runtime_task_manager_process_iterator import RuntimeTaskManagerProcessIterator
from gatling.runtime.task_manager.runtime_task_manager_processing_function import RuntimeTaskManagerProcessingFunction
from gatling.runtime.task_manager.runtime_task_manager_processing_iterator import RuntimeTaskManagerProcessingIterator
from gatling.runtime.task_manager.runtime_task_manager_thread_function import RuntimeTaskManagerThreadFunction
from gatling.runtime.task_manager.runtime_task_manager_thread_iterator import RuntimeTaskManagerThreadIterator
from gatling.runtime.task_manager.runtime_task_manager_coroutine_function import RuntimeTaskManagerCoroutineFunction
from gatling.runtime.task_manager.runtime_task_manager_coroutine_iterator import RuntimeTaskManagerCoroutineIterator
from gatling.storage.g_queue.base_queue import BaseQueue
from gatling.storage.g_queue.memory_queue import MemoryQueue

from gatling.utility.watch import Watch
from gatling.utility.xprint import check_globals_pickable, print_flush, print_none

K_cost = 'cost'
K_speed = 'speed'
K_srate = 'srate'
K_remain = 'remain'

K_wait = 'wait'
K_work = 'work'
K_done = 'done'
K_errr = 'errr'


def format_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


class TaskFlowManager:

    def __init__(self, wait_queue: BaseQueue[Any], done_queue: BaseQueue[Any] = None, errr_queue: BaseQueue[Any] = None, retry_on_error=True, retry_empty_interval=0, errlogfctn=print_flush):

        # Build stages
        self.runtime_task_manager_s: List[RuntimeTaskManager] = []
        self.wait_queue: BaseQueue[Any] = wait_queue
        self.done_queue: BaseQueue[Any] = MemoryQueue() if done_queue is None else done_queue
        self.retry_on_error = retry_on_error
        self.retry_empty_interval = retry_empty_interval
        self.errlogfctn = errlogfctn
        self.running = False

    def print_rtm(self, msg):
        print(f"==={msg}===" * 128)
        print(f"{id(self.wait_queue)=}")
        for i, rtm in enumerate(self.runtime_task_manager_s):
            print(f"{i}. {rtm.fctn.__name__} wait={id(rtm.qwait)} {rtm.qwait.__class__.__name__}")
            print(f"{i}. {rtm.fctn.__name__} done={id(rtm.qdone)} {rtm.qdone.__class__.__name__}")
        print(f"{id(self.done_queue)=}")

    def make_coroutine(self, fctn: Callable, qwait: BaseQueue[Any], qwork: BaseQueue[Any], qerrr: BaseQueue[Any], qdone: BaseQueue[Any], worker):
        is_async_iter = inspect.isasyncgenfunction(fctn)
        is_async_fctn = asyncio.iscoroutinefunction(fctn)
        if is_async_fctn:
            rtm_cls = RuntimeTaskManagerCoroutineFunction
        elif is_async_iter:
            rtm_cls = RuntimeTaskManagerCoroutineIterator
        else:
            raise RuntimeError(f"fctn={fctn} is neither async function nor async generator")
        rtm = rtm_cls(fctn, qwait=qwait, qwork=qwork, qerrr=qerrr, qdone=qdone, worker=worker, retry_on_error=self.retry_on_error, retry_empty_interval=self.retry_empty_interval, errlogfctn=self.errlogfctn)
        return rtm

    def make_thread(self, fctn: Callable, qwait: BaseQueue[Any], qwork: BaseQueue[Any], qerrr: BaseQueue[Any], qdone: BaseQueue[Any], worker):
        is_iter = inspect.isgeneratorfunction(fctn)
        rtm_cls = RuntimeTaskManagerThreadIterator if is_iter else RuntimeTaskManagerThreadFunction
        rtm = rtm_cls(fctn, qwait=qwait, qwork=qwork, qerrr=qerrr, qdone=qdone, worker=worker, retry_on_error=self.retry_on_error, retry_empty_interval=self.retry_empty_interval, errlogfctn=self.errlogfctn)
        return rtm

    def make_processing(self, fctn: Callable, qwait: BaseQueue[Any], qwork: BaseQueue[Any], qerrr: BaseQueue[Any], qdone: BaseQueue[Any], worker):
        is_iter = inspect.isgeneratorfunction(fctn)
        rtm_cls = RuntimeTaskManagerProcessingIterator if is_iter else RuntimeTaskManagerProcessingFunction
        rtm = rtm_cls(fctn, qwait=qwait, qwork=qwork, qerrr=qerrr, qdone=qdone, worker=worker, retry_on_error=self.retry_on_error, retry_empty_interval=self.retry_empty_interval, errlogfctn=self.errlogfctn)
        return rtm

    def make_process(self, fctn: Callable, qwait: BaseQueue[Any], qwork: BaseQueue[Any], qerrr: BaseQueue[Any], qdone: BaseQueue[Any], worker):
        is_iter = inspect.isgeneratorfunction(fctn)
        rtm_cls = RuntimeTaskManagerProcessIterator if is_iter else RuntimeTaskManagerProcessFunction
        rtm = rtm_cls(fctn, qwait=qwait, qwork=qwork, qerrr=qerrr, qdone=qdone, worker=worker, retry_on_error=self.retry_on_error, retry_empty_interval=self.retry_empty_interval, errlogfctn=self.errlogfctn)
        return rtm

    def _register_generic(self, make_rtm: Callable, fctn: Callable, worker: int):
        if len(self.runtime_task_manager_s) == 0:
            curr_qwait = self.wait_queue
        else:
            curr_qwait = MemoryQueue()
            prev_rtm = self.runtime_task_manager_s[-1]
            prev_rtm.qdone = curr_qwait

        curr_qerrr = MemoryQueue()
        rtm = make_rtm(fctn, qwait=curr_qwait, qwork=MemoryQueue(), qerrr=curr_qerrr, qdone=self.done_queue, worker=worker)
        self.runtime_task_manager_s.append(rtm)

    def register_coroutine(self, fctn: Callable, worker=1):
        self._register_generic(self.make_coroutine, fctn, worker)

    def register_thread(self, fctn: Callable, worker=1):
        self._register_generic(self.make_thread, fctn, worker)

    def register_processing(self, fctn: Callable, worker=1):
        self._register_generic(self.make_processing, fctn, worker)

    def register_process(self, fctn: Callable, worker=1):
        self._register_generic(self.make_process, fctn, worker)

    def before_start_record(self):
        self.N_already_done = len(self.done_queue)
        self.N_origin_wait = len(self.wait_queue)
        self.w = Watch()

    def start(self):
        self.before_start_record()
        for rtm in self.runtime_task_manager_s:
            rtm.start(rtm.worker)
        self.running = True

    def stop(self):
        for rtm in self.runtime_task_manager_s:
            rtm.stop()
        self.running = False

    @contextmanager
    def execute(self, log_interval=1):
        try:
            yield self
            self.start()
            self.await_print(log_interval=log_interval)

        finally:
            self.stop()

    def check_done(self) -> bool:
        isdone = all(rtm.check_done() for rtm in self.runtime_task_manager_s)
        return isdone

    def get_speedinfo(self):
        N_done = len(self.done_queue)

        N_wait = len(self.wait_queue)
        N_cur_done = N_done - self.N_already_done  # setup in self.before_start_record()
        N_error = sum(len(stage.qerrr) for stage in self.runtime_task_manager_s if stage.qerrr is not None)

        self.w.see_timedelta()  # setup in self.before_start_record()
        cost_td = self.w.total_timedelta()
        cost_sec = cost_td.total_seconds()

        srate = N_cur_done / (N_cur_done + N_error) if (N_cur_done + N_error) > 0 else 0

        speed = N_cur_done / cost_sec if cost_sec > 0 else 0

        cost = format_timedelta(cost_td)

        N_remain = self.N_origin_wait - N_done  # setup in self.before_start_record()
        remain = format_timedelta(timedelta(seconds=(N_remain / speed)) if speed > 0 else timedelta.max)
        speedinfo = {}
        speedinfo[K_cost] = cost
        speedinfo[K_speed] = speed
        speedinfo[K_srate] = srate
        speedinfo[K_wait] = N_wait
        speedinfo[K_remain] = remain

        return speedinfo

    def __str__(self):
        sent = f"wait[{len(self.wait_queue)}]"
        for tfm in self.runtime_task_manager_s:
            sent += f" => {str(tfm)}"
        return sent

    def pack(self, logfctn=print):
        speedinfo = self.get_speedinfo()

        cost = speedinfo[K_cost]
        speed = speedinfo[K_speed]
        srate = speedinfo[K_srate]
        remain = speedinfo[K_remain]

        sent = f"[{cost}] remain={remain} {speed:.1f} iter/sec {srate=:.2f} {self}"
        logfctn(sent)

    def await_print(self, log_interval=1.0, logfctn=print):

        while not self.check_done():
            self.pack(logfctn=logfctn)
            time.sleep(log_interval)
        self.pack(logfctn=logfctn)
        logfctn("DONE !!!")

    def block_while_print(self, log_interval=1.0, logfctn=print):
        while self.running:
            self.pack(logfctn=logfctn)
            time.sleep(log_interval)
        self.pack(logfctn=logfctn)
        logfctn("DONE !!!")

    def while_print(self, log_interval=1.0, logfctn=print):
        t = threading.Thread(target=self.block_while_print, args=(log_interval, logfctn), daemon=True)
        t.start()
        return t

    def get_qdone(self):
        return self.done_queue

    def get_qwait(self):
        return self.wait_queue


if __name__ == '__main__':
    pass
    from gatling.vtasks.sample_tasks import fake_iter_disk, fake_fctn_disk, async_fake_iter_net, async_fake_fctn_net, fake_fctn_cpu, fake_iter_cpu
    from gatling.vtasks.sample_tasks import errr_iter_disk, errr_fctn_disk, async_errr_iter_net, async_errr_fctn_net, errr_fctn_cpu, errr_iter_cpu

    # ---------- Build and run the pipeline ----------
    check_globals_pickable()
    if False:

        q_wait = MemoryQueue()

        # for i in range(10):
        #     q_wait.put(i + 1)

        tfm = TaskFlowManager(q_wait, retry_on_error=False)

        with tfm.execute(log_interval=1):
            tfm.register_process(fake_fctn_cpu, worker=2)
            tfm.register_thread(fake_fctn_disk, worker=2)
            tfm.register_coroutine(async_fake_fctn_net, worker=2)

            tfm.register_process(fake_iter_cpu, worker=2)
            tfm.register_thread(fake_iter_disk, worker=2)
            tfm.register_coroutine(async_fake_iter_net, worker=2)

            for i in range(10):
                q_wait.put(i + 1)

        q_done = tfm.get_qdone()
        results = list(q_done)
        print(f"\n=== Final Results ({len(results)})===")
    if False:
        q_wait = MemoryQueue()

        # for i in range(10):
        #     q_wait.put(i + 1)

        tfm = TaskFlowManager(q_wait, retry_on_error=True, errlogfctn=print_none)

        with tfm.execute(log_interval=1):
            tfm.register_process(errr_fctn_cpu, worker=2)
            tfm.register_thread(errr_fctn_disk, worker=2)
            tfm.register_coroutine(async_errr_fctn_net, worker=5)

            tfm.register_process(errr_iter_cpu, worker=2)
            tfm.register_thread(errr_iter_disk, worker=2)
            tfm.register_coroutine(async_errr_iter_net, worker=2)

            for i in range(10):
                q_wait.put(i + 1)

        q_done = tfm.get_qdone()
        results = list(q_done)
        print(f"\n=== Final Results ({len(results)})===")

    if True:
        q_wait = MemoryQueue()

        # for i in range(10):
        #     q_wait.put(i + 1)

        tfm = TaskFlowManager(q_wait, retry_on_error=True, errlogfctn=print_none)

        tfm.register_process(errr_fctn_cpu, worker=2)
        tfm.register_thread(errr_fctn_disk, worker=2)
        tfm.register_coroutine(async_errr_fctn_net, worker=5)

        tfm.register_process(errr_iter_cpu, worker=2)
        tfm.register_thread(errr_iter_disk, worker=2)
        tfm.register_coroutine(async_errr_iter_net, worker=2)
        tfm.start()
        while_t = tfm.while_print(log_interval=1)

        for i in range(10):
            q_wait.put(i + 1)

        # q_done = tfm.get_qdone()
        # results = list(q_done)
        # print(f"\n=== Final Results ({len(results)})===")
