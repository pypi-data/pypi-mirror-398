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
Functions to decode aircraft identification information like ICAO address,
category and callsign.

.. seealso::

   - `ICAO address <https://mode-s.org/decode/content/ads-b/1-basics.html>`_
   - 'Aircraft identification and category <https://mode-s.org/decode/content/ads-b/2-identification.html>`_
"""

import numpy as np

from ..crc import CRC_LOOKUP, crc
from ..const import CALLSIGN_TRANS_TABLE, CALLSIGN_DROP, DF_ICAO_S, DF_ICAO_C
from ..types import Message, DownlinkFormat, TypeCode
from ..util import base64_decode, to_uint24, create_array

from ..types import String, Category, Icao
from .msg_info import df, typecode

def icao(data: Message, df_data: DownlinkFormat | None=None) -> Icao:
    """
    Decode ICAO address from ADS-B messages.

    :param data: ADS-B messages.
    :param df_data: Downlink format information for each ADS-B message.
    """
    result = np.zeros(len(data), dtype=np.uint32)

    df_v = df(data) if df_data is None else df_data

    idx_s = np.isin(df_v, DF_ICAO_S)
    result[idx_s] = to_uint24(data[idx_s, :4])

    idx_c = np.isin(df_v, DF_ICAO_C)
    crc_ver = crc(CRC_LOOKUP, data[idx_c])
    result[idx_c] = to_uint24(data[idx_c, -4:]) ^ crc_ver

    idx = idx_s | idx_c

    return create_array(result, idx)

def category(data: Message, tc_data: TypeCode | None=None) -> Category:
    """
    Decode aircraft category from ADS-B messages.

    :param data: ADS-B messages.
    :param tc_data: Type code information for each ADS-B message.
    """
    tc = typecode(data) if tc_data is None else tc_data
    idx = (1 <= tc) & (tc <= 4)

    catr = create_array(data[:, 4] & 0x07, idx)
    tcr = create_array(tc, idx)
    return np.ma.hstack([catr, tcr]).reshape(2, -1).T

def callsign(data: Message, tc_data: TypeCode | None=None) -> String:
    """
    Decode aircraft callsign from ADS-B messages.

    :param data: ADS-B messages.
    :param tc_data: Type code information for each ADS-B message.
    """
    result = np.zeros(len(data), dtype='U8')

    tc = typecode(data) if tc_data is None else tc_data
    idx = (1 <= tc) & (tc <= 4)

    decoded = np.hstack([
        *base64_decode(data[idx, 5:9].view('>u4')),
        *base64_decode(data[idx, 8:12].view('>u4')),
    ]).view('S8')[:, 0]

    result[idx] = np.char.translate(  # type: ignore[call-overload]
        decoded, CALLSIGN_TRANS_TABLE, deletechars=CALLSIGN_DROP
    )
    return create_array(result, idx)

# vim: sw=4:et:ai
