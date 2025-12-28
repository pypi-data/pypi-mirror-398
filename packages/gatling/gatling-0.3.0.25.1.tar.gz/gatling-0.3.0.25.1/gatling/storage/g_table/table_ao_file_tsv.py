import datetime
import os
import traceback
from dataclasses import dataclass
from typing import Optional, IO, Any, BinaryIO, Literal

import ciso8601

from gatling.storage.g_table.base_table_ao import BaseTableAO
from gatling.storage.g_table.help_tools.file_tools import readline_forward, append_line, extend_lines, readline_backward, goto_tail, get_pos, set_pos, goto_head, truncate, popout
from gatling.storage.g_table.help_tools.slice_tools import Slice
from gatling.utility.error_tools import FileAlreadyOpenedForWriteError, FileAlreadyOpenedError, FileAlreadyOpenedForReadError, FileNotOpenError
from gatling.utility.io_fctns import remove_file


def is_write_mode(file: IO) -> bool:
    """Check if the file is opened with write permission."""
    return bool(set(file.mode) & {"w", "a", "+", "x"})


keytype_to_sent = {
    str: str,
    int: str,
    float: str,
    bool: lambda x: str(int(x)),
    datetime.date: datetime.date.isoformat,
    datetime.time: datetime.time.isoformat,
    datetime.datetime: datetime.datetime.isoformat,
}

keytype_fm_sent = {
    str: str,
    int: int,
    float: float,
    bool: lambda x: x != '0',
    datetime.date: lambda x: ciso8601.parse_datetime(x).date(),
    datetime.time: lambda x: datetime.time.fromisoformat(x),
    datetime.datetime: ciso8601.parse_datetime,
}

sent_2_keytype = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'date': datetime.date,
    'time': datetime.time,
    'datetime': datetime.datetime,
}

KEY_IDX = "*"


@dataclass
class FileTableAOState:
    file: Optional[BinaryIO] = None
    key2type: Optional[dict[str, Any]] = None
    next_idx: Optional[int] = None


def head2sent(key2type):
    return '\t'.join([f"{keyname}.{keytype.__name__}" for keyname, keytype in key2type.items()])


def sent2head(sent):
    try:
        return {k: sent_2_keytype[v] for k, v in (item.rsplit('.', 1) for item in sent.split('\t'))}
    except ValueError as e:
        print(f"{e} error parsing (rsplit failed): {sent!r}")

        print(traceback.format_exc())
        raise
    except KeyError as e:
        print(f"{e} error parsing (unknown keytype {e}): {sent!r}")
        print(traceback.format_exc())
        raise


def row2sent(row, key2type):
    return '\t'.join(keytype_to_sent[ktype](row[kname]) for kname, ktype in key2type.items())


def sent2row(sent, key2type, key2idx=None):
    values = sent.split('\t')
    if key2idx is None:
        return {kname: keytype_fm_sent[ktype](val) for (kname, ktype), val in zip(key2type.items(), values)}
    else:

        return {
            key: keytype_fm_sent[key2type[key]](values[idx])
            for key, idx in key2idx.items()
        }


def sent2flat(sent, key2type, key2idx=None):
    values = sent.split('\t')
    if key2idx is None:
        return [keytype_fm_sent[ktype](val) for (kname, ktype), val in zip(key2type.items(), values)]
    else:
        return [keytype_fm_sent[key2type[key]](values[idx]) for key, idx in key2idx.items()]


def get_key2idx(keys, key2type):
    key2idx = None
    if keys is None:
        default_key2idx = {kname: i for i, kname in enumerate(key2type.keys()) if kname != KEY_IDX}
        return default_key2idx
    elif isinstance(keys, str):
        keys_all = list(key2type.keys())
        key2idx = {keys: keys_all.index(keys)}
    elif isinstance(keys, list):
        default_key2idx = {kname: i for i, kname in enumerate(key2type.keys())}
        key2idx = {key: default_key2idx[key] for key in keys}
    else:
        raise ValueError(f"keys must be Nonr or str or list, not {type(keys)}")
    return key2idx


def fetch_data(idxs, temp_state, keys, sent2x):
    key2type = temp_state.key2type
    N = temp_state.next_idx
    key2idx = get_key2idx(keys, key2type)
    if isinstance(idxs, int):
        row = None
        if idxs >= 0:
            if idxs >= N:
                raise IndexError(f"Index {idxs=} out of range for table with {N=} rows")
            goto_head(temp_state.file)
            readline_forward(temp_state.file)

            sent = readline_forward(temp_state.file)
            for i in range(idxs):
                sent = readline_forward(temp_state.file)
            row = sent2x(sent.decode(), temp_state.key2type, key2idx=key2idx)
        else:
            if idxs < -N:
                raise IndexError(f"Index {idxs=} out of range for table with {N=} rows")

            goto_tail(temp_state.file)
            sent = readline_backward(temp_state.file)
            for i in range(-idxs - 1):
                sent = readline_backward(temp_state.file)

            row = sent2x(sent.decode(), temp_state.key2type, key2idx=key2idx)

        if sent2x is sent2row:
            return row
        elif sent2x is sent2flat:
            keys = list(key2idx.keys())
            k2v = {key: val for key, val in zip(keys, row)}
            return k2v
        else:
            raise ValueError(f"sent2x must be sent2row or sent2flat, not {sent2x}")


    elif isinstance(idxs, slice):
        start, stop, step = idxs.indices(N)

        target_iter = iter(range(start, stop, step))
        next_target = next(target_iter, None)

        rows = []
        if step > 0:
            goto_head(temp_state.file)
            readline_forward(temp_state.file)
            for current_idx in range(N):
                sent = readline_forward(temp_state.file)

                if current_idx == next_target:
                    rows.append(sent2x(sent.decode(), temp_state.key2type, key2idx=key2idx))
                    next_target = next(target_iter, None)
                    if next_target is None:
                        break
        elif step < 0:
            goto_tail(temp_state.file)
            for current_idx in range(N - 1, -1, -1):
                sent = readline_backward(temp_state.file)
                if current_idx == next_target:
                    rows.append(sent2x(sent.decode(), temp_state.key2type, key2idx=key2idx))
                    next_target = next(target_iter, None)
                    if next_target is None:
                        break

        if sent2x is sent2row:
            return rows
        elif sent2x is sent2flat:
            keys = list(key2idx.keys())
            if len(rows) == 0:
                return {key: [] for key in keys}
            else:
                k2vs = {key: list(vals) for key, vals in zip(keys, zip(*rows))}
                return k2vs
        else:
            raise ValueError(f"sent2x must be sent2row or sent2flat, not {sent2x}")
    else:
        raise TypeError(f"Index must be int or slice, not {type(idxs)}")


# def row2sent_with_idx(idx, row, key2type):
#     """
#     Convert a row to a tab-separated string with index.
#
#     Avoids creating intermediate dictionary by handling KEY_IDX separately,
#     which is faster than {KEY_IDX: idx, **row} dict unpacking.
#
#     Args:
#         idx: Row index to be inserted
#         row: Dictionary containing row data
#         key2type: Ordered dictionary mapping column names to their types
#
#     Returns:
#         Tab-separated string representation of the row
#     """
#     parts = []
#     for kname, ktype in key2type.items():
#         if kname == KEY_IDX:
#             parts.append(keytype_to_sent[ktype](idx))
#         else:
#             parts.append(keytype_to_sent[ktype](row[kname]))
#     return '\t'.join(parts)


class TableAO_FileTSV(BaseTableAO):

    def __init__(self, fpath):
        super().__init__()
        self.fpath = fpath
        self.state = FileTableAOState()

    def get_key2type(self):
        target_file = self.state.file
        if target_file is not None and is_write_mode(target_file):
            raise FileAlreadyOpenedForWriteError(f'{self.fpath} is already opened with write permission.')

        with open(self.fpath, 'rb') as f:
            key2type = sent2head(readline_forward(f).decode())
        return key2type

    def get_first_row(self, key2type=None):
        target_file = self.state.file
        if target_file is not None and is_write_mode(target_file):
            raise FileAlreadyOpenedForWriteError(f'{self.fpath} is already opened with write permission.')
        if key2type is None:
            key2type = self.get_key2type()
        with open(self.fpath, 'rb') as f:
            _ = readline_forward(f)  # skip head

            first_sent = readline_forward(f).decode()
            if first_sent == '':
                return {}
            else:
                return sent2row(first_sent, key2type)

    def get_last_row(self, key2type=None):
        target_file = self.state.file
        if target_file is not None and is_write_mode(target_file):
            raise FileAlreadyOpenedForWriteError(f'{self.fpath} is already opened with write permission.')
        if key2type is None:
            key2type = self.get_key2type()
        with open(self.fpath, 'rb') as f:
            goto_tail(f)
            last_sent = readline_backward(f).decode()
            if last_sent[0] == KEY_IDX:
                return {}
            else:
                return sent2row(last_sent, key2type)


    def initialize(self, key2type)->'TableAO_FileTSV':
        target_file = self.state.file
        if target_file is not None:
            raise FileAlreadyOpenedError(f'{self.fpath} is already opened with read or write permission.')
        key2type = {KEY_IDX: int, **key2type}
        with open(self.fpath, 'wb') as f:
            append_line(f, head2sent(key2type).encode())
        return self

    def _build_state(self, ori_state: Optional[FileTableAOState] = None, open_mode: Literal['rb', 'rb+', 'ab'] = 'rb+') -> FileTableAOState:
        if ori_state is not None:
            target_file = ori_state.file
            if target_file is None:
                pass
            else:
                if is_write_mode(target_file):
                    raise FileAlreadyOpenedForWriteError(f'{self.fpath} is already opened with write permission.')
                elif open_mode != {'rb'}:
                    raise FileAlreadyOpenedForReadError(f'{self.fpath} is already opened with read permission.')

        fts = FileTableAOState() if ori_state is None else ori_state
        fts.key2type = self.get_key2type()
        last_row = self.get_last_row(fts.key2type)
        fts.next_idx = last_row[KEY_IDX] + 1 if last_row else 0
        fts.file = open(self.fpath, open_mode)
        return fts

    def __enter__(self):
        self.state = self._build_state(self.state)
        return self

    def _clean_state(self, ori_state: Optional[FileTableAOState]):
        target_file = ori_state.file
        if target_file is None:
            raise FileNotOpenError(f'{self.fpath} is not opened.')
        ori_state.file.close()
        ori_state.file = None
        ori_state.key2type = None
        ori_state.next_idx = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._clean_state(self.state)

    # ============= The functions above should not be called within a context manager =============

    # def _write_row(self, state, row):
    #     """
    #     Write a single row to file.
    #
    #     Uses row2sent_with_idx to avoid dictionary unpacking overhead.
    #
    #     Args:
    #         state: Current file state containing file handle and metadata
    #         row: Row dictionary to write
    #     """
    #     line = row2sent_with_idx(state.next_idx, row, state.key2type).encode()
    #     state.file.write(line + b'\n')
    #
    # def _write_rows(self, state, rows):
    #     """
    #     Write multiple rows to file in a single operation.
    #
    #     Optimizations:
    #     - Builds entire content as one string before encoding
    #     - Single encode() call instead of per-row encoding
    #     - Single file.write() call to minimize I/O operations
    #
    #     Args:
    #         state: Current file state containing file handle and metadata
    #         rows: List of row dictionaries to write
    #     """
    #     start_idx = state.next_idx
    #     key2type = state.key2type
    #
    #     # Join all rows with newlines, encode once, write once
    #     content = '\n'.join(
    #         row2sent_with_idx(start_idx + i, row, key2type)
    #         for i, row in enumerate(rows)
    #     ) + '\n'
    #
    #     state.file.write(content.encode())
    def exists(self) -> bool:
        return os.path.exists(self.fpath)

    def delete(self)->'TableAO_FileTSV':
        target_file = self.state.file
        if target_file is not None:
            raise FileAlreadyOpenedError(f'{self.fpath} is already opened with read or write permission.')
        remove_file(self.fpath)
        return self

    def clear(self)->'TableAO_FileTSV':
        target_file = self.state.file
        if target_file is not None:
            raise FileAlreadyOpenedError(f'{self.fpath} is already opened with read or write permission.')

        with open(self.fpath, 'rb+') as f:
            goto_head(f)
            readline_forward(f)
            truncate(f)
        return self

    def append(self, row)->'TableAO_FileTSV':
        if self.state.file is None:
            temp_state = self._build_state(open_mode='ab')
            try:
                append_line(temp_state.file, row2sent({KEY_IDX: temp_state.next_idx, **row}, temp_state.key2type).encode())
                # self._write_row(temp_state, row)
            finally:
                self._clean_state(temp_state)
        else:
            cur_state = self.state
            cur_pos = get_pos(cur_state.file)
            goto_tail(cur_state.file)
            append_line(cur_state.file, row2sent({KEY_IDX: cur_state.next_idx, **row}, cur_state.key2type).encode())
            # self._write_row(cur_state, row)
            cur_state.next_idx += 1
            set_pos(cur_state.file, cur_pos)
        return self

    def extend(self, rows)->'TableAO_FileTSV':
        if self.state.file is None:
            temp_state = self._build_state(open_mode='ab')
            try:
                if len(rows) == 0:
                    return self
                start_idx = temp_state.next_idx
                extend_lines(temp_state.file, [
                    row2sent({KEY_IDX: start_idx + i, **row}, temp_state.key2type).encode()
                    for i, row in enumerate(rows)
                ])
                # self._write_rows(temp_state, rows)
            finally:
                self._clean_state(temp_state)
        else:
            cur_state = self.state
            if len(rows) == 0:
                return self
            cur_pos = get_pos(cur_state.file)
            goto_tail(cur_state.file)
            start_idx = cur_state.next_idx
            extend_lines(cur_state.file, [
                row2sent({KEY_IDX: start_idx + i, **row}, cur_state.key2type).encode()
                for i, row in enumerate(rows)
            ])
            # self._write_rows(cur_state, rows)
            cur_state.next_idx += len(rows)
            set_pos(cur_state.file, cur_pos)
        return self

    def keys(self)->list:
        if self.state.file is None:
            temp_state = self._build_state(open_mode='rb')
            try:
                return list(temp_state.key2type.keys())
            finally:
                self._clean_state(temp_state)

        else:
            return list(self.state.key2type.keys())

    def __len__(self):
        if self.state.file is None:
            temp_state = self._build_state(open_mode='rb')
            res_len = temp_state.next_idx
            try:
                return res_len
            finally:
                self._clean_state(temp_state)
        else:
            return self.state.next_idx

    def __getitem__(self, args):
        if isinstance(args, tuple):
            idxs = args[0]
            keys = args[1] if len(args) > 1 else None
            sent2x = args[2] if len(args) > 2 else sent2row
        else:
            idxs = args
            keys = None
            sent2x = sent2row

        # printi(idxs)
        # printi(keys)

        # idxs, keys = args

        if self.state.file is None:
            temp_state = self._build_state(open_mode='rb')
            try:
                data = fetch_data(idxs, temp_state, keys, sent2x)
                return data

            finally:
                self._clean_state(temp_state)
        else:
            cur_state = self.state
            cur_pos = get_pos(cur_state.file)
            try:
                data = fetch_data(idxs, cur_state, keys, sent2x)
                return data
            finally:
                set_pos(cur_state.file, cur_pos)

    def rows(self, idxs=Slice[::], keys=None):
        return self[idxs, keys]

    def cols(self, keys=None, idxs=Slice[::]):
        return self[idxs, keys, sent2flat]

    def pop(self) -> dict:
        if self.state.file is None:
            temp_state = self._build_state(open_mode='rb+')
            try:
                if temp_state.next_idx == 0:
                    return {}
                else:
                    sent = popout(temp_state.file)
                    item = sent2row(sent.decode(), temp_state.key2type, key2idx=None)

                    return item

            finally:
                self._clean_state(temp_state)
        else:
            cur_state = self.state
            cur_pos = get_pos(cur_state.file)
            try:
                if cur_state.next_idx == 0:
                    return {}
                else:
                    sent = popout(cur_state.file)
                    item = sent2row(sent.decode(), cur_state.key2type, key2idx=None)
                    return item

            finally:
                set_pos(cur_state.file, cur_pos)

    def shrink(self, n: int) -> list:
        if self.state.file is None:
            temp_state = self._build_state(open_mode='rb+')
            try:
                if temp_state.next_idx == 0:
                    return []
                else:
                    sents = []
                    cur_idx = temp_state.next_idx
                    goto_tail(temp_state.file)
                    for i in range(n):
                        if cur_idx == 0:
                            break
                        else:
                            sent = readline_backward(temp_state.file)
                            sents.append(sent)
                            cur_idx -= 1
                    items = [sent2row(sent.decode(), temp_state.key2type, key2idx=None) for sent in sents]
                    truncate(temp_state.file)
                    temp_state.next_idx = n
                    return items

            finally:
                self._clean_state(temp_state)
        else:
            cur_state = self.state
            cur_pos = get_pos(cur_state.file)
            try:
                if cur_state.next_idx == 0:
                    return []
                else:
                    sents = []
                    cur_idx = cur_state.next_idx
                    goto_tail(cur_state.file)
                    for i in range(n):
                        if cur_idx == 0:
                            break
                        else:
                            sent = readline_backward(cur_state.file)
                            sents.append(sent)
                            cur_idx -= 1
                    items = [sent2row(sent.decode(), cur_state.key2type, key2idx=None) for sent in sents]
                    truncate(cur_state.file)
                    cur_state.next_idx = n
                    return items

            finally:
                set_pos(cur_state.file, cur_pos)


if __name__ == '__main__':
    pass

    from gatling.utility.xprint import printi, print_rows
    from a_const_debug import fpath_temp_tsv, const_key2type, row1, row2, rows

    ft = TableAO_FileTSV(fpath_temp_tsv)
    ft.delete()

    if False:
        printi(ft.get_key2type())
        printi(ft.get_first_row())
        printi(ft.get_last_row())
        printi('#' * 100)

    ft.initialize(key2type=const_key2type)

    if False:
        printi(ft.get_key2type())
        printi(ft.get_first_row())
        printi(ft.get_last_row())
        printi('#' * 100)

        ft.append(row1)

        printi(ft.get_key2type())
        printi(ft.get_first_row())
        printi(ft.get_last_row())
        printi('#' * 100)

        ft.append(row2)

        printi(ft.get_key2type())
        printi(ft.get_first_row())
        printi(ft.get_last_row())
        printi('#' * 100)

        # printi(ft[0])
        # printi(ft[1])
        # printi(ft[-1])
        # printi(ft[-2])
        #
        # printi(ft[:])
        # printi(ft[:, ['score', 'name']])
        # printi(ft[:1,])
        #
        # printi(ft[:1, ['score', 'name']])
    if False:
        ft.extend(rows)
        # print_rows(rows_extra[::-2])
        # print()
        # print_rows(ft[::-2])

        ft.cols(['name'], Slice[:])
    if False:
        ft.extend(rows)
        print_rows(rows)
        print('==')
        while True:
            item = ft.pop()
            if item == {}:
                break
            print_rows([item])

    if True:
        ft.extend(rows)
        print_rows(ft[:])

        print('==')
        print_rows(ft.shrink(2))
        print('==')
        print_rows(ft[:])

    #
    # x = input('press enter to exit')
    # ft.clear()
