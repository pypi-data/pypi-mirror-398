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

from ..crc import crc, CRC_LOOKUP
from ..types import Message

def test_crc(message: Message) -> None:
    """
    Test message CRC calculation.
    """
    result = crc(CRC_LOOKUP, message)
    expected = [
        0xc6f5d, 0xaa4bda, 0xdf3ecf, 0x37c86e, 0xe5b7ab, 0xc41a4a,
        0xe1b4c3, 0xd3bd58, 0xa6832f, 0x983ecb, 0x903de6, 0x14f867, 0x5466d3,
        0x478a59,
    ]
    assert np.array_equal(expected, result)

# vim: sw=4:et:ai
