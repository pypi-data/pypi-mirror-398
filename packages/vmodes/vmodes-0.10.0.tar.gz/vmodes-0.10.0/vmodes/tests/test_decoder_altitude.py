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
import numpy.testing as npt
from collections.abc import Iterable
from functools import partial

from ..decoder import altitude as palt
from ..types import Message, Int32

import pytest
from .conftest import to_bin_msg

type QBitData = list[tuple[str, int, int, int]]

np_assert_equal = partial(npt.assert_almost_equal, decimal=4)

@pytest.fixture
def altitude_qbit_unset() -> QBitData:
    """
    ADS-B messsages with barometric altitude and Q-bit unset.
    """
    return [
        ('950e6a5549102ef8dca0e325f48b', 0x11, 0x00, 0),  # n100 == 0
        ('906a51d352b0d61634b9e465a969', 0xd2, 0x06, 77100),
        ('92db7b49674e895e6b5aab6c94bb', 0x2e, 0x01, 24800),
        ('918918416a223e02595b06bfa636', 0x45, 0x02, 59500),
        ('9518639f77b83312f07f93808a2f', 0x51, 0x07, 0), # n100 == 5
        ('92509e0d78c605137bb75964817f', 0x2c, 0x04, 26300),
        ('9044c60d850ad792654a90b09326', 0xc6, 0x01, 64800),
        ('9784bd4397f042b161b12814f867', 0xb0, 0x06, 110400),
    ]

def extract_altitude_data(input: Iterable[str]) -> Int32:
    """
    Extract altitude data from ADS-B messages.

c   The altitude data is 12-bit of bytes 5 and 6.
    """
    data = to_bin_msg(input)
    return ((data[:, 5].astype(np.uint32) << 4) | (data[:, 6] >> 4)) & 0x0fff

def test_altitude(message: Message) -> None:
    """
    Test ADS-B altitude parsing.
    """
    result = palt.altitude(message)

    expected = [0, 0, 0, 0, 11277.5996, -68.57999, 33649.9179, 2429, 2558]
    np_assert_equal(result.compressed(), expected)

    expected = [0] * 9 + [11277.5996, -68.57999, 33649.9179, 2429, 2558]
    np_assert_equal(result, expected)

def test_altitude_barometric_qbit_set() -> None:
    """
    Test parsing of barometric altitude with Q-bit set.
    """
    data = [
        ['906a8ccc4ea51ab7b5abb26d59d5', 31825],
        ['95072c2955d56a86a356a4c6250e', 41550],
        ['932b2b4759594a05aa1d3f502ee9', 16700],
        ['903138556789eba48717aa4afdd5', 26550],
        ['903e3ca86c41f01626ea000f6e7b', 12175],
        ['9766158e709304691879887a0c81', 28200],
        ['94bc73017a83e843133f28041f65', 25350],
        ['93b492bf85e943d35611b36f1335', 45500],
        ['910bd87e8bf1c9bbedff80d84fb0', 47300],
        ['9416710194754012341c78075a0d', 22300],
    ]
    items, expected = zip(*data)
    input = extract_altitude_data(items)
    result = palt.altitude_barometric_qbit_set(input)
    npt.assert_array_equal(result, expected)

def test_altitude_barometric_qbit_unset(altitude_qbit_unset: QBitData) -> None:
    """
    Test parsing of barometric altitude with Q-bit unset.
    """
    items, *_, expected = zip(*altitude_qbit_unset)
    input = extract_altitude_data(items)
    result, idx_result = palt.altitude_barometric_qbit_unset(input)
    npt.assert_array_equal(result, expected)

    expected_idx = [False, True, True, True] * 2
    npt.assert_array_equal(expected_idx, idx_result)

def test_reorder_altitude(altitude_qbit_unset: QBitData) -> None:
    """
    Test reordering altitude data received in ADS-B messages.
    """
    items, gc_500, gc_100, *_ = zip(*altitude_qbit_unset)
    input = extract_altitude_data(items)
    expected_gc_500, expected_gc_100 = palt.reorder_altitude(input)
    npt.assert_array_equal(gc_500, expected_gc_500)
    npt.assert_array_equal(gc_100, expected_gc_100)

def test_altitude_gnss() -> None:
    """
    Test parsing of GNSS altitude.
    """
    data = [
        ['8fb93f32a29e620fc63e07203001', 2534],
        ['88b0037fafb2840f1c5bedf1cdb1', 2856],
        ['8fa2a77bb407939edcc97e0011bd', 121],
        ['978005ffa0800ce7dc4064c07d6f', 2048],
        ['93ddbce2a97466b89ae6d8286688', 1862],
        ['9570100cb0c438ed6d535860f22d', 3139],
    ]
    items, expected = zip(*data)
    input = to_bin_msg(items)
    result = palt.altitude(input)
    npt.assert_array_equal(result, expected)

# vim: sw=4:et:ai
