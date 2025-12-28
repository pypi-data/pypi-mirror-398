from collections import defaultdict

from pygments.lexers import data

from gatling.storage.g_table.table_ao_file_tsv import KEY_IDX
from gatling.utility.rand_tools import (
    rand_bool, rand_uint8, rand_int32, rand_float_01, rand_float_pos,
    rand_float_any, rand_float_inf, rand_name_zh,
    rand_name_en, rand_url, rand_ip, rand_username, rand_password,
    rand_fpath, rand_date, rand_time, rand_datetime
)

const_key2rand = {
    # str - account
    'account': rand_username,
    'secret': rand_password,

    # bool
    'is_active': rand_bool,

    # int
    'level': rand_uint8,
    'balance': rand_int32,

    # float
    'progress': rand_float_01,
    'price': rand_float_pos,
    'temperature': rand_float_any,
    'threshold_inf': rand_float_inf,

    # str - name
    'nickname_zh': rand_name_zh,
    'nickname_en': rand_name_en,

    # str - network
    'homepage': rand_url,
    'ip_address': rand_ip,

    # str - path
    'save_path': rand_fpath,

    # datetime
    'birthday': rand_date,
    'alarm': rand_time,
    'created_at': rand_datetime,
}

const_key2type = {key: type(rf()) for key, rf in const_key2rand.items()}
const_key2type_extra = {KEY_IDX: int, **const_key2type}
const_keys = list(const_key2rand.keys())
const_keys_extra =[KEY_IDX, *const_keys]

def rand_row():
    return {key: rf() for key, rf in const_key2rand.items()}


def filterbykeys(data, keys):
    if isinstance(data, dict):
        return {k: data[k] for k in keys}
    elif isinstance(data, list):
        return [filterbykeys(row, keys) for row in data]


def rows2cols(rows,keys):
    if isinstance(rows, dict):
        return rows
    elif isinstance(rows, list):
        if len(rows) == 0:
            return {k:[] for k in keys}
        else:
            res = defaultdict(list)
            for row in rows:
                for k, v in row.items():
                    res[k].append(v)
            return dict(res)


if __name__ == '__main__':
    pass
    data = [
        {'a': 1, 'b': 2},
        {'a': 3, 'b': 4},
        {'a': 5, 'b': 6}
    ]

    print(rows2cols(data))
