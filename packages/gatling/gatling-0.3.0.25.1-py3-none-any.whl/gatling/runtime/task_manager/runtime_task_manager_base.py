import time
from contextlib import contextmanager
from typing import Callable, Any
from abc import ABC, abstractmethod

from gatling.storage.g_queue.base_queue import BaseQueue
from gatling.utility.xprint import check_picklable


class RuntimeTaskManager(ABC):

    def __init__(self, fctn: Callable,
                 qwait: BaseQueue[Any],
                 qwork: BaseQueue[Any],
                 qerrr: BaseQueue[Any],
                 qdone: BaseQueue[Any],
                 worker: int = 1,
                 retry_on_error: bool = False,
                 retry_empty_interval: float = 0.001):

        self.fctn = fctn
        self.qwait = qwait
        self.qwork = qwork
        self.qerrr = qerrr
        self.qdone = qdone
        self.worker = worker
        self.retry_on_error = retry_on_error
        self.retry_empty_interval = retry_empty_interval

        check_picklable(fctn)

    @abstractmethod
    def start(self, worker):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @contextmanager
    def execute(self, worker=1, log_interval=1, logfctn=print):
        """
        A context wrapper for use with the with syntax:
        Starts on entry and automatically stops on exit.
        """
        try:
            yield self
            self.start(worker)
            self.await_done(log_interval=log_interval, logfctn=logfctn)
        finally:
            self.stop()

    def len_qwait(self):
        return len(self.qwait) if self.qwait else 0

    def len_qwork(self):
        return len(self.qwork) if self.qwork else 0

    def len_qdone(self):
        return len(self.qdone) if self.qdone else 0

    def len_qerrr(self):
        return len(self.qerrr) if self.qerrr else 0

    def check_done(self):
        return self.len_qwait() == 0 and self.len_qwork() == 0

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.fctn.__name__}[{len(self)}] wait={self.len_qwait()}, work={self.len_qwork()}, done={self.len_qdone()}, errr={self.len_qerrr()}>"

    def __str__(self):
        return f"({len(self)}){self.fctn.__name__}[{self.len_qwork()}|{self.len_qerrr()}|{self.len_qdone()}]"

    def await_done(self, log_interval=1, logfctn=print):
        while not self.check_done():
            time.sleep(log_interval)
            logfctn(str(self))
        logfctn(f"{str(self)}")
        logfctn("DONE !!!")


if __name__ == "__main__":
    pass
