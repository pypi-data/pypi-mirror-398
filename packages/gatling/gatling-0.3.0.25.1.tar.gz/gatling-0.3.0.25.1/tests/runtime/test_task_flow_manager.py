import unittest

from gatling.runtime.taskflow_manager import TaskFlowManager
from gatling.storage.g_queue.memory_queue import MemoryQueue
from gatling.vtasks.sample_tasks import fake_fctn_cpu, fake_iter_cpu, fake_iter_disk, fake_fctn_disk, async_fake_iter_net, async_fake_fctn_net
from helper.dynamic_testcase import DynamicTestCase

R_process = 'process'
R_thread = 'thread'
R_coroutine = 'coroutine'


# DynamicTestCase.set_name('TestRuntimeTaskManagerCoroutine')
class TestRuntimeTaskManagerThread(DynamicTestCase):
    pass


# Define Test Case Function
def testcase_fctn(resources, fctns, worker=2, use_ctx=False, retry_empty_interval=0, log_interval=0.001):
    q_wait = MemoryQueue()
    for i in range(5):
        q_wait.put(i + 1)

    tfm = TaskFlowManager(q_wait, retry_on_error=False, retry_empty_interval=retry_empty_interval)

    for resource, fctn in zip(resources, fctns):
        if resource == R_process:
            tfm.register_process(fctn, worker=worker)
        elif resource == R_thread:
            tfm.register_thread(fctn, worker=worker)
        elif resource == R_coroutine:
            tfm.register_coroutine(fctn, worker=worker)

    if use_ctx:
        with tfm.execute(log_interval=log_interval):
            pass
    else:
        tfm.start()
        tfm.await_print(log_interval=log_interval)
        tfm.stop()

    assert len(q_wait) == 0, f"❌ Queue not empty: remaining={list(q_wait)}"

    q_done = tfm.get_qdone()
    assert q_done is not None, "❌ TaskFlowManager has no q_done or get_qdone()"

    done_items = list(q_done)
    assert len(done_items) > 0, "❌ Done queue is empty — no tasks were completed"

    print(done_items)


tname2rsc_fctn_s = {
    'fake_fctn_cpu': [[R_process, fake_fctn_cpu]],
    'fake_iter_cpu': [[R_process, fake_iter_cpu]],

    'fake_fctn_disk': [[R_thread, fake_fctn_disk]],
    'fake_iter_disk': [[R_thread, fake_iter_disk]],

    'async_fake_fctn_net': [[R_coroutine, async_fake_fctn_net]],
    'async_fake_iter_net': [[R_coroutine, async_fake_iter_net]],

}

# === Dynamic Register Test Case ===
for fname, rsc_fctn_s, in tname2rsc_fctn_s.items():
    for worker in [1, 2]:
        for use_ctx in [True, False]:
            for retry_empty_interval in [0, 0.001]:
                testcase_name = f"test_{fname}_{worker=}_{use_ctx=}_{retry_empty_interval=:.0e}"

                resources, fctns = zip(*rsc_fctn_s)
                TestRuntimeTaskManagerThread.append_testcase(testcase_name, testcase_fctn, resources, fctns, worker, use_ctx, retry_empty_interval)

if __name__ == "__main__":
    unittest.main(verbosity=2)
