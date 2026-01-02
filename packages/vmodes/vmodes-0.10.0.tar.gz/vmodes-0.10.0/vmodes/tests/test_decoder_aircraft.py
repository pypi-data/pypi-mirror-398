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

import numpy.testing as npt

from vmodes import icao, category, callsign
from ..types import Message

def test_icao(message: Message) -> None:
    """
    Test parsing of Mode S and ADS-B ICAO address.
    """
    result = icao(message)
    expected = [
        0x896217, 0x406b90, 0x4ca3da, 0x7ba7ca, 0x4ca2d4, 0x4ca44c,
        0x4ca3a3, 0x4cafe2, 0x4ca37c, 0x3c4ad0, 0x4ca4ed, 0x84bd43,
        0xabc6ea, 0x300bba,
    ]
    npt.assert_array_equal(expected, result.compressed())

def test_category(message: Message) -> None:
    """
    Test ADS-B category parsing.
    """
    result = category(message)

    expected = [[0, 0], [0, 4], [2, 2], [5, 1], [3, 4]] + 9 * [[0, 0]]
    npt.assert_array_equal(expected, result)

    expected = [[0, 4], [2, 2], [5, 1], [3, 4]]
    npt.assert_array_equal(expected, result.compressed().reshape(-1, 2))

def test_callsign(message: Message) -> None:
    """
    Test ADS-B callsign parsing.
    """
    result = callsign(message)
    expected = ['', 'EZY85MH_', 'DAA_OPS5', '8YE_2', 'RYR5QR__'] + 9 * ['']
    npt.assert_array_equal(expected, result)

    expected = ['EZY85MH_', 'DAA_OPS5', '8YE_2', 'RYR5QR__']
    npt.assert_array_equal(expected, result.compressed())

# vim: sw=4:et:ai
