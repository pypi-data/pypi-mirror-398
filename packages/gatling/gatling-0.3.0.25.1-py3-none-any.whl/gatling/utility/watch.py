import functools
import datetime
import time


class Watch:
    """A simple stopwatch class using the datetime library."""

    def __init__(self, fctn=time.perf_counter):
        self.fctn = fctn
        self.tick = self.fctn()
        self.records = []

    def see_seconds(self, rd=6) -> float:
        tick = self.fctn()
        delta_seconds = tick - self.tick
        self.records.append(delta_seconds)
        self.tick = tick
        return round(delta_seconds, rd) if rd is not None else delta_seconds

    def see_timedelta(self, rd=6) -> datetime.timedelta:
        seconds = self.see_seconds(rd=rd)
        res = datetime.timedelta(seconds=seconds)
        return res

    def total_seconds(self, rd=6):
        raw_secs = sum(self.records, 0)
        return round(raw_secs, rd) if rd is not None else raw_secs

    def total_timedelta(self, rd=6):
        total_seconds = self.total_seconds(rd=rd)
        return datetime.timedelta(seconds=total_seconds)


def watch_time(func):
    pass
    """A decorator to measure and print the execution time of a function."""

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        w = Watch()
        res = func(*args, **kwargs)
        # The first and only call to see_seconds() measures the total duration
        print(f"Time Cost : '{func.__name__}' took {w.see_seconds()} seconds")
        return res

    return wrap


if __name__ == '__main__':
    pass


    @Watch()
    def slow_func():
        time.sleep(1)


    slow_func()
