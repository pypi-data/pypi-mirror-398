#
# VModeS - vectorized decoding of Mode S and ADS-B data
#
# Copyright (C) 2020-2024 by Artur Wroblewski <wrobell@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import numpy as np
import typing as tp
from binascii import unhexlify
from collections.abc import Iterable, Sequence

from vmodes import message_array, df, typecode
from ..types import Time, Message, DownlinkFormat, TypeCode

import pytest

np.set_printoptions(precision=12, floatmode='unique')

type TimeMsg = Sequence[tuple[float, str]]

@pytest.fixture
def message() -> Message:
    data: Sequence[str] = [
        # various
        'a8281d3030000000000000850d4a',  # df = 21
        '8d406b902015a678d4d220000000',  # example from https://mode-s.org/decode/content/ads-b/8-error-control.html
        '904ca3da121010603d04f5df3ecf',  # df = 18, tc = 2
        '977ba7ca0daa3e1915d83237c86e',  # df = 18, tc = 1
        '8d4ca2d4234994b5452820e5b7ab',  # df = 17, tc = 4

        # altitude testing (surface), 5 <= tc <= 8
        '904ca44c28000419f344c3c41a4a',  # df = 18, tc = 5
        '904ca3a33219741c85465ae1b4c3',  # df = 18, tc = 6
        '8c4cafe2399b841aa3466dd3bd58',  # df = 17, tc = 7
        '8c4ca37c448e241487468ba6832f',  # df = 17, tc = 8

        # altitude testing, 9 <= tc <= 18
        '8d3c4ad048bf06601ca788983ecb',  # df = 17, tc = 9, q-bit = 1, 37000
        '8d4ca4ed5803f707f8d032903de6',  # df = 17, tc = 11, q-bit = 1, -68.57999 (yes, negative)
        '9784bd4397f042b161b12814f867',  # df = 18, tc = 18, q-bit = 0, 110400

        # altitude testing, 20 <= tc <= 22
        '8dabc6eaa697d8adbce3005466d3',  # df = 17, tc = 20, 7969.16036
        '96300bbaa19fe7cf9efbc9478a59',  # df = 18, tc = 20, 8392.38872
    ]
    return to_bin_msg(data)

@pytest.fixture
def df_message(message: Message) -> DownlinkFormat:
    return df(message)

@pytest.fixture
def tc_message(message: Message, df_message: DownlinkFormat) -> TypeCode:
    return typecode(message, df_message)

@pytest.fixture
def message_cpr() -> Message:
    data: Sequence[str] = [
        # even
        '8d4750015879038226be8c4be170',
        '8d475001587903828cbf0b67481a',
        '8d475001587903837ec03ca970da',
        '8d4750015879038434c1208bd5b9',
        '8d4750015879038444c135663935',
        # odd
        '8d475001587906ea28c71ffda0e0',
        '8d475001587906ea66c76ac86d0b',
        '8d475001587906eab8c7d1ce31bc',
        '8d475001587906eb1cc84cdff3a4',
        '8d475001587906ebbcc9147d9574',
    ]
    return to_bin_msg(data)

def to_bin_msg(data: Iterable[str]) -> Message:
    """
    Convert collection of strings to VModeS messages.
    """
    return message_array([unhexlify(v) for v in data])

def to_ts_msg(data: Sequence[tuple[tp.Any, ...]], *, start: int=0) -> tuple[Time, Message]:
    """
    Convert tuples (time, str) to VModeS time and message vectors.
    """
    end = start + 2
    items = [v[start:end] for v in data]
    assert all(len(v) == 2 for v in items)
    ts, dt = list(zip(*items)) if items else ([], [])
    return np.array(ts, dtype=np.double), to_bin_msg(dt)

# vim: sw=4:et:ai
