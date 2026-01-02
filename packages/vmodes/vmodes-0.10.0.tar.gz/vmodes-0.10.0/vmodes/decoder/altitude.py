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

from .msg_info import typecode
from ..util import create_array
from .. import types as vmt

# Based on
#
#   https://github.com/bistromath/gr-air-modes/blob/master/python/altitude.py
#
# but for 12-bit input (ADS-B)
ALTITUDE_MASK_C1, ALTITUDE_SHIFT_C1= 0x0800, 9
ALTITUDE_MASK_A1, ALTITUDE_SHIFT_A1= 0x0400, 5
ALTITUDE_MASK_C2, ALTITUDE_SHIFT_C2= 0x0200, 8
ALTITUDE_MASK_A2, ALTITUDE_SHIFT_A2= 0x0100, 4
ALTITUDE_MASK_C4, ALTITUDE_SHIFT_C4= 0x0080, 7
ALTITUDE_MASK_A4, ALTITUDE_SHIFT_A4= 0x0040, 3  # skip bit 6
ALTITUDE_MASK_B1, ALTITUDE_SHIFT_B1= 0x0020, 3
ALTITUDE_MASK_B2, ALTITUDE_SHIFT_B2= 0x0008, 2
ALTITUDE_MASK_D2, ALTITUDE_SHIFT_D2= 0x0004, 5
ALTITUDE_MASK_B4, ALTITUDE_SHIFT_B4= 0x0002, 1
ALTITUDE_MASK_D4, ALTITUDE_SHIFT_D4= 0x0001, 6

def altitude(
        data: vmt.Message, tc_data: vmt.TypeCode | None=None
) -> vmt.Altitude:
    """
    Decode altitude reported by an aircraft.

    The altitude is reported in meters.

    :param data: Mode S and ADS-B messages.
    :param tc_data: Type code information for each message.
    """
    result = np.zeros(len(data), dtype=vmt.SAltitude)

    tc = typecode(data) if tc_data is None else tc_data
    msg = ((data[:, 5].astype(np.uint32) << 4) | (data[:, 6] >> 4)) & 0x0fff
    msg = msg.astype(np.int32)

    # altitude 0, no need for calculation
    idx_surface = (5 <= tc) & (tc <= 8)

    # barometric altitude, which calculation depends on Q-bit value
    idx_barometric = (9 <= tc) & (tc <= 18)

    # metric calculation
    idx_gnss = (20 <= tc) & (tc <= 22)

    idx_qbit = (msg & 0x0010) == 0x0010
    idx_qbit_set = idx_barometric & idx_qbit
    result[idx_qbit_set] = altitude_barometric_qbit_set(msg[idx_qbit_set]) / 3.28084

    idx_qbit_unset = idx_barometric & ~idx_qbit
    alt_barometric_qbit_unset, idx_valid = altitude_barometric_qbit_unset(msg[idx_qbit_unset])
    result[idx_qbit_unset] = alt_barometric_qbit_unset / 3.28084
    idx_barometric[idx_qbit_unset] = idx_valid

    result[idx_gnss] = msg[idx_gnss]

    idx = idx_surface | idx_barometric | idx_gnss
    return create_array(result, idx)

def altitude_barometric_qbit_set(data: vmt.Int32) -> vmt.Int32:
    """
    Decode barometric altitude with Q-bit set.
    """
    # remove q-bit
    result = ((data & 0x0fe0) >> 1) | (data & 0x000f)
    return result * 25 - 1000

def altitude_barometric_qbit_unset(
        data: vmt.Int32
) -> tuple[vmt.Int32, vmt.BIndex]:
    """
    Decode barometric altitude with Q-bit unset.

    Return tuple of arrays

    - altitude values in feet
    - index of valid altitude values

    The input data is split into 500 feet and 100 feet resolution values,
    then combined together. When 100 feet resolution data is one of 0, 5 or
    6 then an altitude value is invalid.

    .. seealso:: https://en.wikipedia.org/wiki/Gillham_code
    """
    gc_500, gc_100 = reorder_altitude(data)
    alt_500 = decode_gray_code(gc_500)
    alt_100 = decode_gray_code(gc_100)

    # create the index of valid values *before* alt_100 == 7 check
    idx_valid = (alt_100 != 0) & (alt_100 != 5) & (alt_100 != 6)

    idx = alt_100 == 7
    alt_100[idx] = 5

    idx = gc_500 % 2 == 1
    alt_100[idx] = 6 - alt_100[idx]

    altitude = alt_500 * 500 + alt_100 * 100 - 1300
    altitude[~idx_valid] = 0

    return altitude, idx_valid

def decode_gray_code(num: vmt.Int32) -> vmt.Int32:
    """
    Decode Gray code.

    Implementation from: https://en.wikipedia.org/wiki/Gray_code.
    """
    num ^= num >> 8
    num ^= num >> 4
    num ^= num >> 2
    num ^= num >> 1
    return num

def reorder_altitude(data: vmt.Int32) -> tuple[vmt.Int32, vmt.Int32]:
    """
    Algorithm based on

        https://github.com/bistromath/gr-air-modes/blob/master/python/altitude.py

    but for 12-bit input (ADS-B)
    """
    gc = data

    gc_500 = ((gc & ALTITUDE_MASK_B4) >> ALTITUDE_SHIFT_B4) \
        | ((gc & ALTITUDE_MASK_B2) >> ALTITUDE_SHIFT_B2) \
        | ((gc & ALTITUDE_MASK_B1) >> ALTITUDE_SHIFT_B1) \
        | ((gc & ALTITUDE_MASK_A4) >> ALTITUDE_SHIFT_A4) \
        | ((gc & ALTITUDE_MASK_A2) >> ALTITUDE_SHIFT_A2) \
        | ((gc & ALTITUDE_MASK_A1) >> ALTITUDE_SHIFT_A1) \
        | ((gc & ALTITUDE_MASK_D4) << ALTITUDE_SHIFT_D4) \
        | ((gc & ALTITUDE_MASK_D2) << ALTITUDE_SHIFT_D2)

    gc_100 = ((gc & ALTITUDE_MASK_C4) >> ALTITUDE_SHIFT_C4) \
        | ((gc & ALTITUDE_MASK_C2) >> ALTITUDE_SHIFT_C2) \
        | ((gc & ALTITUDE_MASK_C1) >> ALTITUDE_SHIFT_C1)

    return gc_500, gc_100

# vim: sw=4:et:ai
