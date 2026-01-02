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

from .. import types as vmt
from vmodes.util import create_array, data_index

import pytest

DATA_INDEX = (
    (np.ma.array([1, 2, 3]), [True] * 3),
    (np.ma.array([1, 2, 3], mask=True), [False] * 3),
    (np.ma.array([1, 2, 3], mask=[True, False, False]), [False, True, True]),
    (
        np.ma.array(
            [[1, 5], [2, 6], [3, 1]],
            mask=[[True, True], [False, False], [False, False]]
        ),
        [False, True, True],
    ),
)

def test_create_array() -> None:
    """
    Test creating masked array.
    """
    idx = np.array([False, True, True, False, True])
    result = create_array(np.array([1, 2, 3, 4, 5]), idx)

    assert result[0] is np.ma.masked
    assert result[3] is np.ma.masked

    assert np.array_equal([1, 2, 3, 4, 5], result)
    assert np.array_equal([2, 3, 5], result.compressed())

def test_create_array_2d() -> None:
    """
    Test creating masked 2d array.
    """
    idx = np.array([False, True, True, False, True])
    m = np.array([[1, 11], [2, 22], [3, 33], [4, 44], [5, 55]])
    result = create_array(m, idx)

    assert result[0][0] is np.ma.masked
    assert result[0][1] is np.ma.masked
    assert result[3][0] is np.ma.masked
    assert result[3][1] is np.ma.masked

    expected = [[1, 11], [2, 22], [3, 33], [4, 44], [5, 55]]
    assert np.array_equal(expected, result)
    expected = [[2, 22], [3, 33], [5, 55]]
    assert np.array_equal(expected, result.compressed().reshape(-1, 2))

@pytest.mark.parametrize('array, index', DATA_INDEX)
def test_data_index(array: vmt.MArray[np.uint32], index: vmt.BIndex) -> None:
    """
    Test getting index of valid values from an array.
    """
    npt.assert_array_equal(data_index(array), index)

# vim: sw=4:et:ai
