#
# VModeS - vectorized decoding of Mode S and ADS-B data
#
# Copyright (C) 2020-2025 by Artur Wroblewski <wrobell@riseup.net>
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
import numpy.typing as npt
import typing as tp

from .const import MASK_UINT24
from .types import Message, BIndex, UInt8, MaUInt24, MArray

Tb = tp.TypeVar('Tb', bound=npt.NBitBase)

def to_uint24(data: Message) -> MaUInt24:
    result = data.view('>u4').reshape(-1) & MASK_UINT24
    return tp.cast(MaUInt24, result)

def base64_decode(data: Message) -> UInt8:
    """
    Decode 32-bit unsigned integer into four 6-bit codes.

    The decoding starts at most significant bits. Last 8 bits are ignored.

    Return array of 8-bit unsigned integers.
    """
    return np.array([
        data >> 26,
        (data >> 20) & 0x3f,
        (data >> 14) & 0x3f,
        (data >> 8) & 0x3f,
    ]).astype(np.uint8)

def create_array[T: np.generic](data: npt.NDArray[T], idx: BIndex) -> MArray[T]:
    """
    Create NumPy masked array.

    Note, that this function differes from NumPy constructor semantics. The
    index indicates the valid values (not the invalid as in the default
    masked array in NumPy).

    :param data: Input data.
    :param idx: Index of valid values.
    """
    mask = np.ma.column_stack([~idx] * data.ndim)  # or recordmask?
    return np.ma.array(data, mask=mask)

def data_index[T: np.generic](data: MArray[T]) -> BIndex:
    """
    Utility function to get index of valid rows from NumPy masked array.

    The function returns one-dimensional vector of boolean values. True
    values indicate valid values in the input array.

    The boolean values are opposite of a mask of NumPy masked array. It is
    also a boolean vector with *one* dimension - for VModeS purposes, each
    row always has the same mask.

    :param data: Input NumPy array.
    """
    mask = data.mask
    size = data.shape[0]

    result: BIndex
    if np.isscalar(mask):
        result = np.full(size, not bool(mask), dtype=np.bool_)
    elif len(mask.shape) == 1:
        result = ~data.mask  # type: ignore[assignment]
    else:
        result = ~data.mask[:, 0]  # type: ignore[index]

    return result

def hstack[T: np.generic](
        a1: MArray[T] | npt.NDArray[T],
        a2: MArray[T] | npt.NDArray[T],
) -> MArray[T]:
    return np.ma.hstack([a1, a2])

def vstack[T: np.generic](
        a1: MArray[T] | npt.NDArray[T],
        a2: MArray[T] | npt.NDArray[T],
) -> MArray[T]:
    return np.ma.vstack([a1, a2])

# vim: sw=4:et:ai
