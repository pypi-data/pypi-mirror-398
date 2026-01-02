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

import dataclasses as dtc
import numpy as np
import numpy.typing as npt
import typing as tp
from numpy.ma import MaskedArray

from .decoder._data import PosDecoderCtx

# define aliases for basic types to support static type analysis; these are
# for a convenience
# NOTE: waiting for shape support i.e. np.ndarray[shape, dtype]

type MArray[T: np.generic] = MaskedArray[tp.Any, np.dtype[T]]

type UInt8 = npt.NDArray[np.uint8]
type UInt24 = npt.NDArray[np.uint32]
type UInt32 = npt.NDArray[np.uint32]
type UInt64 = npt.NDArray[np.uint64]
type Int32 = npt.NDArray[np.int32]
type Int64 = npt.NDArray[np.int64]
type BIndex = npt.NDArray[np.bool_]

type MaUInt8 = MArray[np.uint8]
type MaUInt24 = MArray[np.uint32]
type MaUInt32 = MArray[np.uint32]
type String = MArray[np.str_]

# scalar types
type SCprNl = np.int32
type SCoordinate = np.float64
type SCprCoordinate = np.float64
SAltitude: tp.TypeAlias = np.float32  # noqa: UP040
type SCategory = np.uint8

# vector types
type Time = npt.NDArray[np.float64]
type Message = UInt8
type DownlinkFormat = UInt8
type TypeCode = MaUInt8
type Icao = MaUInt24
type Category = MArray[SCategory]  # TODO: 2 dimensions
type Altitude = MArray[SAltitude]
type CprFormat = UInt8
type CprCoordinate = npt.NDArray[SCprCoordinate]
type CprNl = npt.NDArray[SCprNl]
type Coordinate = npt.NDArray[SCoordinate]
type Position = MArray[SCoordinate]  # TODO: 2 dimensions

@dtc.dataclass(frozen=True, slots=True)
class PositionData:
    """
    Result of decoding of aircraft position.

    :var ctx: Position decoding context.
    :var position: Aircraft position coordinates.
    :var all_position: Aircraft position coordinates, including carried
        over data.
    """
    ctx: PosDecoderCtx
    position: Position
    prev_position: Position

class CPosition(tp.TypedDict):
    # used on Cython level and in unit tests
    longitude: float
    latitude: float
    is_valid: bool

# vim: sw=4:et:ai
