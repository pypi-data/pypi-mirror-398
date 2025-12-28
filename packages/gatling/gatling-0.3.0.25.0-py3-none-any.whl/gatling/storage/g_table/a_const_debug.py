import datetime
import os
from pathlib import Path

from gatling.utility.xprint import print_rows

const_key2type = {
    'name': str,
    'age': int,
    'score': float,
    'active': bool,
    'birthday': datetime.date,
    'alarm': datetime.time,
    'created_at': datetime.datetime,
}

row1 = {
    'name': 'Harry Mozilla',
    'age': 25,
    'score': 98.5,
    'active': True,
    'birthday': datetime.date(1999, 5, 20),
    'alarm': datetime.time(8, 30, 0),
    'created_at': datetime.datetime(2024, 1, 15, 14, 30, 45),
}
row2 = {
    'name': 'Bunny Mozilla',
    'age': 32,
    'score': 87.3,
    'active': False,
    'birthday': datetime.date(1992, 11, 8),
    'alarm': datetime.time(7, 15, 0),
    'created_at': datetime.datetime(2023, 6, 22, 9, 45, 12),
}
row3 = {
    'name': 'Tom Mozilla',
    'age': 28,
    'score': 95.2,
    'active': True,
    'birthday': datetime.date(1997, 10, 12),
    'alarm': datetime.time(10, 0, 0),
    'created_at': datetime.datetime(2023, 12, 25, 18, 30, 15),
}
row4 = {
    'name': 'Alice Mozilla',
    'age': 29,
    'score': 92.1,
    'active': True,
    'birthday': datetime.date(1998, 7, 15),
    'alarm': datetime.time(9, 0, 0),
    'created_at': datetime.datetime(2023, 11, 10, 16, 15, 30),
}

row5 = {
    'name': 'Jack Mozilla',
    'age': 26,
    'score': 96.3,
    'active': False,
    'birthday': datetime.date(1995, 12, 20),
    'alarm': datetime.time(11, 30, 0),
    'created_at': datetime.datetime(2023, 10, 1, 12, 45, 5),
}

rows = [row1, row2, row3, row4, row5]

rows_extra = [{'*': i, **row} for i, row in enumerate(rows)]


dtemp = os.path.join(Path(__file__).resolve().parent.parent, 'temp')
fpath_temp_tsv = os.path.join(dtemp, 'temp.tsv')


if __name__ == '__main__':
    print_rows(rows_extra)
