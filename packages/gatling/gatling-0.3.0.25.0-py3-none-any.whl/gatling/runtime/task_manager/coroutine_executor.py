import asyncio
import traceback

from gatling.utility.xprint import print_flush


class CoroutineExecutor():

    def __init__(self, max_workers=5, logfctn=print_flush):
        self.max_workers = max_workers
        self.logfctn = logfctn
        self.coroutine_tasks = []

    def submit(self, loop_func, *args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            use_existing_loop = True
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            use_existing_loop = False


        async def main():
            tasks = [asyncio.create_task(loop_func(*args, **kwargs)) for i in range(self.max_workers)]
            self.coroutine_tasks.extend(tasks)
            await asyncio.gather(*tasks, return_exceptions=True)

        if use_existing_loop:
            return loop.create_task(main())
        try:
            loop.run_until_complete(main())
        except Exception:
            self.logfctn(f"{loop_func.__name__} event loop exception:")
            self.logfctn(traceback.format_exc())
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending:
                    t.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                self.logfctn(traceback.format_exc())
            finally:
                loop.close()
        self.coroutine_tasks.clear()


if __name__ == '__main__':
    pass
