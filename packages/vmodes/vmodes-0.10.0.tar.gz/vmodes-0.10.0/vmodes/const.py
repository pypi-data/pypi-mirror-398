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

CRC_POLY = 0xFFF409

MASK_UINT24 = 0xffffff

# callsign translation table and characters to drop
CALLSIGN_CHAR = b'#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######'
CALLSIGN_TRANS_TABLE = bytes.maketrans(
    bytes(range(len(CALLSIGN_CHAR))), CALLSIGN_CHAR
)
CALLSIGN_DROP = bytes(k for k, v in enumerate(CALLSIGN_CHAR) if v == 35)

# simple icao parsing
DF_ICAO_S = np.array([11, 17, 18])

# crc based icao parsing
DF_ICAO_C = np.array([0, 4, 5, 16, 20, 21])

# vim: sw=4:et:ai
