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
from collections.abc import Iterable

from .types import Message

def message_array(data: Iterable[bytes]) -> Message:
    """
    Create Numpy array of Mode S and ADS-B messages.

    The array is the input for other decoding functions, like
    :py:func:`vmodes.icao`, :py:func:`vmodes.altitude`, etc.

    :param data: Collection of Mode S and ADS-B messages.
    """
    vec = np.array(data, dtype='|S14')
    result = vec.view(dtype=np.uint8)
    return result.reshape(-1, 14)

# vim: sw=4:et:ai
