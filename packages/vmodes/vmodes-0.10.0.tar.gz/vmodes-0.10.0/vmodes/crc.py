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

from .const import MASK_UINT24, CRC_POLY
from .types import Message, UInt24

def crc_init() -> UInt24:
    """
    Based on CRC functions implemented by bladeRF project

        https://github.com/Nuand/bladeRF-adsb/blob/master/c/adsb.c
    """
    crc_lut = np.array([0] * 256, dtype=np.uint32)

    for i in range(256):
        crc = i << 16
        for _ in range(8):
            if crc & 0x800000:
                crc = ((crc << 1) ^ CRC_POLY) & MASK_UINT24
            else:
                crc  = (crc << 1) & MASK_UINT24
        crc_lut[i] = crc & MASK_UINT24
    return crc_lut

def crc(crc_lut: UInt24, data: Message) -> UInt24:
    """
    Based on CRC functions implemented by bladeRF project

        https://github.com/Nuand/bladeRF-adsb/blob/master/c/adsb.c
    """
    crc = np.zeros(len(data), dtype=np.uint32)
    for i in range(11):
        k = ((crc >> 16) ^ data[:, i]) & 0xff
        crc = crc_lut[k] ^ (crc << 8)
    return crc & MASK_UINT24  # type: ignore[return-value]

CRC_LOOKUP = crc_init()

# vim: sw=4:et:ai
