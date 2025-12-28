import sys
import math
import random
from faker import Faker

fake_zh = Faker('zh_CN')
fake_en = Faker('en_US')

rand_bool = lambda: random.random() < 0.5

rand_int8 = lambda: random.randint(-2 ** 7, 2 ** 7 - 1)
rand_uint8 = lambda: random.randint(0, 2 ** 8 - 1)
rand_int16 = lambda: random.randint(-2 ** 15, 2 ** 15 - 1)
rand_uint16 = lambda: random.randint(0, 2 ** 16 - 1)
rand_int32 = lambda: random.randint(-2 ** 31, 2 ** 31 - 1)
rand_uint32 = lambda: random.randint(0, 2 ** 32 - 1)
rand_int64 = lambda: random.randint(-2 ** 63, 2 ** 63 - 1)
rand_uint64 = lambda: random.randint(0, 2 ** 64 - 1)

rand_float_01 = lambda: random.random()
rand_float_11 = lambda: random.uniform(-1.0, 1.0)
rand_float_pos = lambda: math.exp(random.uniform(math.log(sys.float_info.min), math.log(sys.float_info.max)))
rand_float_zeropos = lambda: random.choice([0.0, rand_float_pos()])
rand_float_any = lambda: random.choice([-rand_float_pos(), 0.0, rand_float_pos()])
rand_float_inf = lambda: random.choice([rand_float_any(), float('inf'), float('-inf')])
rand_float_nan = lambda: random.choice([rand_float_any(), float('nan')])

rand_name_zh = lambda: fake_zh.name()  # Zhang Wei, Li Na
rand_name_en = lambda: fake_en.name()  # John Smith
rand_email = lambda: fake_en.email()  # john@example.com

rand_url = lambda: fake_en.url()  # https://example.com/
rand_domain = lambda: fake_en.domain_name()  # example.com
rand_ip = lambda: fake_en.ipv4()  # 192.168.1.1
rand_mac = lambda: fake_en.mac_address()  # 00:1B:44:11:3A:B7
rand_username = lambda: fake_en.user_name()  # john_doe
rand_password = lambda: fake_en.password()  # xK9#mP2$
rand_fname = lambda: fake_en.file_name()  # document.pdf
rand_fpath = lambda: fake_en.file_path()  # /home/user/doc.pdf

rand_date = lambda: fake_en.date_object()  # 2023-05-15
rand_time = lambda: fake_en.time_object().replace(microsecond=0)  # 14:30:25
rand_datetime = lambda: fake_en.date_time().replace(microsecond=0)  # datetime object

if __name__ == '__main__':
    pass

    current_module = sys.modules[__name__]
    rand_funcs = {
        name: obj for name, obj in vars(current_module).items()
        if name.startswith('rand_') and callable(obj)
    }

    for name, func in rand_funcs.items():
        print(f"\n{name}:")
        for _ in range(3):
            val = func()
            print(f"{type(val)} {[val]}")
