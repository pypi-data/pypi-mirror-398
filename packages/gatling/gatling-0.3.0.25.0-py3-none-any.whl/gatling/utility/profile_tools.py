from line_profiler import LineProfiler
import functools


def profile_time(func):
    """Line-by-line time profiler, prints detailed timing after execution"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        lp = LineProfiler()
        lp.add_function(func)
        lp_wrapper = lp(func)
        result = lp_wrapper(*args, **kwargs)
        lp.print_stats()
        return result

    return wrapper


if __name__ == '__main__':
    pass
    