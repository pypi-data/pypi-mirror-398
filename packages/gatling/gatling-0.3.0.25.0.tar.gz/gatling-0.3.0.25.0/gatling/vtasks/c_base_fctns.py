import random


def random_seed_int():
    return random.getrandbits(64)


def mix64(x: int) -> int:
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9
    x = (x ^ (x >> 27)) * 0x94d049bb133111eb
    x = x ^ (x >> 31)
    return x & 0xFFFFFFFFFFFFFFFF
