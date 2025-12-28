from gatling.runtime.taskflow_manager import TaskFlowManager
from gatling.storage.g_queue.memory_queue import MemoryQueue
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
