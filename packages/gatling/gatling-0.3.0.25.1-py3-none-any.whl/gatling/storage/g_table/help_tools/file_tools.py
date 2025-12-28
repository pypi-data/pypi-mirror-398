import io
from typing import BinaryIO


def goto_head(file):
    file.seek(0, io.SEEK_SET)


def goto_tail(file):
    file.seek(0, io.SEEK_END)


def goto_offset(file, n=1):
    file.seek(n, io.SEEK_CUR)


def get_pos(file):
    return file.tell()


def set_pos(file, pos):
    file.seek(pos, io.SEEK_SET)


def append_line(file: BinaryIO, data: bytes):
    file.write(data + b'\n')


def extend_lines(file: BinaryIO, lines: list[bytes]):
    if len(lines) > 0:
        file.write(b'\n'.join(lines) + b'\n')


def read_backward(file, n=1):
    pos = get_pos(file)
    n = min(n, pos)
    if n == 0:
        return b''
    goto_offset(file, -n)  # now at pos - n
    res = file.read(n)  # after read, at pos
    set_pos(file, pos - n)  # back to pos - n
    return res


def readline_forward(file):
    return file.readline().rstrip(b'\n')


def readline_backward(file, chunk_size=1024):
    if get_pos(file) == 0:
        return b''
    goto_offset(file, -1)  # skip trailing \n
    end_pos = get_pos(file)
    if end_pos == 0:
        return b''

    chunks = []
    while True:
        cur_chunk = read_backward(file, chunk_size)
        if cur_chunk == b'':
            break

        idx = cur_chunk.rfind(b'\n')
        if idx != -1:
            cur_chunk = cur_chunk[idx + 1:]
            chunks.append(cur_chunk)
            # set pos to the \n (end of previous line)
            set_pos(file, get_pos(file) + idx + 1)
            break
        else:
            chunks.append(cur_chunk)

    return b''.join(reversed(chunks))


def truncate(file):
    file.truncate(get_pos(file))


def popout(file):
    goto_tail(file)
    res = readline_backward(file)
    truncate(file)
    return res


if __name__ == '__main__':
    from gatling.utility.xprint import printi

    with open('test.txt', 'w') as x:
        pass

    file = open('test.txt', 'r+b')
    extend_lines(file, [b'line1', b'line2', b'line3'])
    append_line(file, b'line4')

    # test forward
    printi('--- Forward ---')
    goto_head(file)
    printi(readline_forward(file))
    printi(readline_forward(file))
    printi(readline_forward(file))
    printi(readline_forward(file))
    printi(readline_forward(file))

    # test backward
    printi('--- Backward ---')
    goto_tail(file)
    printi(readline_backward(file, chunk_size=1))
    printi(readline_backward(file, chunk_size=1))
    printi(readline_backward(file, chunk_size=1))
    printi(readline_backward(file, chunk_size=1))
    printi(readline_backward(file, chunk_size=1))

    #
    # test extend
    # print('--- Extend ---')
    # extend_lines(f, ['line4', 'line5'])
    #
    # validation
    # goto_head(f)
    # print(f.read())
