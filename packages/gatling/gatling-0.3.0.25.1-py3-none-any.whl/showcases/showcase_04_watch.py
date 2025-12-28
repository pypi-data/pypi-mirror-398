from gatling.utility.watch import Watch, watch_time
import time


@watch_time
def slow_func():
    time.sleep(1)


slow_func()

w = Watch()
time.sleep(0.5)
print("Δt:", w.see_seconds(), "Total:", w.total_seconds())
