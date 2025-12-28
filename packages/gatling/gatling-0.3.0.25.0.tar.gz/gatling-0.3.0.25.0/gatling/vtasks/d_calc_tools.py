from typing import Callable

from gatling.utility.decorator_tools import call_with
from gatling.utility.watch import Watch
from gatling.vtasks.a_const import cpu_flops_per_sec, flops_target


def calc_fctn_flops(fctn: Callable, init_flops, flops_per_sec=cpu_flops_per_sec, num=1, xrange=range):
    w = Watch()
    for i in xrange(num):
        fctn()
    total_cost_secs = w.see_seconds()
    percall_cost_secs = total_cost_secs / num
    percall_flops = flops_per_sec * percall_cost_secs

    return percall_flops


def approx_calc_fctn_flops(fctn: Callable, init_flops, iter, flops_per_sec=cpu_flops_per_sec, xrange=range, flops=flops_target, name=''):
    print(f"{fctn.__name__ if not name else name}.flops : {init_flops:.0f}", end='')
    percall_flops = init_flops
    for i in xrange(iter):
        num = int(flops / percall_flops) + 1
        percall_flops: int = calc_fctn_flops(fctn=fctn, init_flops=percall_flops, flops_per_sec=flops_per_sec, num=num, xrange=xrange)
        print(f" => {percall_flops:.0f}", end='')
    print()
    return percall_flops


################################################################################################################################################

if __name__ == '__main__':
    pass
    from gatling.vtasks.c_base_fctns import random_seed_int, mix64

    approx_calc_fctn_flops(random_seed_int, init_flops=100, iter=10)
    approx_calc_fctn_flops(call_with(10)(mix64), init_flops=100, iter=10)
