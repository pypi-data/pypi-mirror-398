import os
from pathlib import Path

from gatling.storage.g_table.table_ao_file_tsv import TableAO_FileTSV
from gatling.utility.io_fctns import save_jsonl, read_jsonl, remove_file, save_pickle, read_pickle
from gatling.utility.watch import Watch
from storage.g_table.a_const_test import rand_row, const_key2type

if __name__ == '__main__':
    pass

    dtemp = os.path.join(Path(__file__).resolve().parent, 'temp')
    os.makedirs(dtemp, exist_ok=True)

    fpath_temp_tsv = os.path.join(dtemp, 'temp.tsv')
    fpath_temp_jsonl = os.path.join(dtemp, 'temp.jsonl')
    fpath_temp_pkl = os.path.join(dtemp, 'temp.pkl')
    remove_file(fpath_temp_tsv)
    remove_file(fpath_temp_jsonl)

    print(fpath_temp_tsv)

    N = 10000

    rows = []
    for i in range(N):
        rows.append(rand_row())

    w = Watch()
    save_jsonl(rows, fpath_temp_jsonl)
    print(f"save_jsonl {w.see_timedelta()}")


    save_pickle(rows,fpath_temp_pkl)
    print(f"save_pickle {w.see_timedelta()}")

    ft = TableAO_FileTSV(fpath_temp_tsv).initialize(key2type=const_key2type)
    ft.extend(rows)
    print(f"FileTableAO.extend {w.see_timedelta()}")

    _ = read_jsonl(fpath_temp_jsonl)
    print(f"read_jsonl {w.see_timedelta()}")

    _ = read_pickle(fpath_temp_pkl)
    print(f"read_pickle {w.see_timedelta()}")

    w = Watch()
    _ = ft[:]
    print(f"FileTableAO[:] {w.see_timedelta()}")


    _ = input("Press Enter to continue...")
    remove_file(fpath_temp_tsv)
    remove_file(fpath_temp_jsonl)
    remove_file(fpath_temp_pkl)

