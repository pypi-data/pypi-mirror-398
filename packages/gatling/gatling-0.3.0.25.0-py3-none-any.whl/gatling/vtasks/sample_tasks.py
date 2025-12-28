import asyncio
import inspect
import random
import time
from collections.abc import Callable

from gatling.utility.decorator_tools import combo_wraps
from gatling.utility.watch import Watch
from gatling.vtasks.a_const import size_target, network_bytes_per_sec, disk_bytes_per_sec, flops_target
from gatling.vtasks.b_attach_flops import attach_flops
from gatling.vtasks.c_base_fctns import mix64, random_seed_int

mix64 = attach_flops(mix64, 150)
random_seed_int = attach_flops(random_seed_int, 625)


#################################################################### basic prepend funciton ############################################################################


async def async_fake_net(size_bytes=size_target, bytes_per_sec=network_bytes_per_sec):
    seconds = size_bytes / bytes_per_sec
    await asyncio.sleep(seconds)
    return


def fake_diskio(size_bytes=size_target * 1024, bytes_per_sec=disk_bytes_per_sec):
    seconds = size_bytes / bytes_per_sec
    time.sleep(seconds)
    return


def real_cpu(flops=flops_target, fctn=mix64, xrange=range):
    temp = random_seed_int()
    num = int(flops / fctn.flops) + 1
    for i in xrange(num):
        temp = fctn(temp)

    return temp


def fake_errr(rate=0.5):
    if random.random() < rate:
        raise Exception("Fake error")


###################################################################### basic decorator function ##########################################################################

def prepend(ahead_fctn: Callable):
    def decorator(func):
        @combo_wraps(func)
        def pp(*args, **kwargs):
            ahead_fctn()
            return func(*args, **kwargs)

        return pp

    return decorator


def async_prepend(ahead_fctn):
    def decorator(func):
        @combo_wraps(func)
        async def ap(*args, **kwargs):
            await ahead_fctn()
            return func(*args, **kwargs)

        return ap

    return decorator


def repeat(n=2):
    def decorator(func):
        @combo_wraps(func)
        def rp(*args, **kwargs):
            for i in range(n):
                yield func(*args, **kwargs)

        return rp

    return decorator


def async_repeat(n=2):
    def decorator(func):
        @combo_wraps(func)
        async def ar(*args, **kwargs):
            for i in range(n):
                yield await func(*args, **kwargs)

        return ar

    return decorator


async def async_iter2list(iter):
    res = []
    async for item in iter:
        res.append(item)
    return res


######################################################## combination ########################################################################################

target_base_fctn = mix64

async_fake_fctn_net = async_prepend(async_fake_net)(target_base_fctn)
fake_fctn_disk = prepend(fake_diskio)(target_base_fctn)
fake_fctn_cpu = prepend(real_cpu)(target_base_fctn)

async_fake_iter_net = async_repeat(n=2)(async_prepend(async_fake_net)(target_base_fctn))
fake_iter_disk = repeat(n=2)(prepend(fake_diskio)(target_base_fctn))
fake_iter_cpu = repeat(n=2)(prepend(real_cpu)(target_base_fctn))


errr_base_fctn = prepend(fake_errr)(target_base_fctn)
async_errr_fctn_net = async_prepend(async_fake_net)(errr_base_fctn)
errr_fctn_disk = prepend(fake_diskio)(errr_base_fctn)
errr_fctn_cpu = prepend(real_cpu)(errr_base_fctn)

async_errr_iter_net = async_repeat(n=2)(async_prepend(async_fake_net)(errr_base_fctn))
errr_iter_disk = repeat(n=2)(prepend(fake_diskio)(errr_base_fctn))
errr_iter_cpu = repeat(n=2)(prepend(real_cpu)(errr_base_fctn))


if __name__ == '__main__':
    pass

    fctns = [
        async_fake_fctn_net,
        async_fake_iter_net,
        fake_fctn_disk,
        fake_iter_disk,
        fake_fctn_cpu,
        fake_iter_cpu
    ]

    seed = random_seed_int()
    result_real = target_base_fctn(seed)
    for fctn in fctns:
        w = Watch()

        if inspect.iscoroutinefunction(fctn):
            res = asyncio.run(fctn(seed))
        elif inspect.isasyncgenfunction(fctn):
            res = asyncio.run(async_iter2list(fctn(seed)))[0]
        elif inspect.isgeneratorfunction(fctn):
            res = list(fctn(seed))[0]
        else:
            res = fctn(seed)

        assert res == result_real, f"{fctn.__name__} {res} != {result_real} result is not equal to seed"
        cost = w.see_seconds()
        print(f"=== {fctn.__name__} {cost=}===")
