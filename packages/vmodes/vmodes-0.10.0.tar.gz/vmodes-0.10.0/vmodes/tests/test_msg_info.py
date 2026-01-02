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

from vmodes import df, typecode
from ..types import Message

import numpy.testing as npt

def test_df(message: Message) -> None:
    """
    Test parsing of ADS-B downlink format.
    """
    result = df(message)
    excepted = [21, 17, 18, 18, 17, 18, 18, 17, 17, 17, 17, 18, 17, 18]
    npt.assert_array_equal(excepted, result)

def test_typecode(message: Message) -> None:
    """
    Test ADS-B type code parsing.
    """
    result = typecode(message)

    expected = [0, 4, 2, 1, 4, 5, 6, 7, 8, 9, 11, 18, 20, 20]
    npt.assert_array_equal(expected, result)
    expected = [4, 2, 1, 4, 5, 6, 7, 8, 9, 11, 18, 20, 20]
    npt.assert_array_equal(expected, result.compressed())

# vim: sw=4:et:ai
