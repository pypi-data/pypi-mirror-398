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

"""
Functions to decode message information like downlink format and type code.

.. seealso:

   - `Message structure <https://mode-s.org/decode/content/ads-b/1-basics.html>`_
"""

import numpy as np

from ..types import Message, DownlinkFormat, TypeCode
from ..util import create_array

def df(data: Message) -> DownlinkFormat:
    """
    Decode downlink format address from ADS-B messages.

    :param data: ADS-B messages.
    """
    result = data[:, 0] >> 3
    result[result > 24] = 24
    return result  # type: ignore[return-value]

def typecode(data: Message, df_data: DownlinkFormat | None=None) -> TypeCode:
    """
    Decode type code information from ADS-B messages.

    :param data: ADS-B messages.
    :param df_data: Downlink format information for each ADS-B message.
    """
    result = np.zeros(len(data), dtype=np.uint8)
    df_v = df(data) if df_data is None else df_data
    idx = (df_v == 17) | (df_v == 18)
    result[idx] = data[idx, 4] >> 3
    return create_array(result, idx)

# vim: sw=4:et:ai
