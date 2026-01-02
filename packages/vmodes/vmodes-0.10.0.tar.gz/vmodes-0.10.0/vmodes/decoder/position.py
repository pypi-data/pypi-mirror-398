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
Decoding aircraft position and position uncertanity.

Determining Positions
=====================
According to [icao9871]_, sections C.2.6.9 and C.2.6.10, for airborne messages

- determine starting position using globally unambiguous decoding

  - determine position P1 using first two ADS-B messages
  - determine position P2 using next two ADS-B messages
  - decode position P3 using position P1 and most recent ADS-B message
    of position P2
  - if distance |P2, P3| <= 5 meters, then position P1 is the starting
    position

- for each following ADS-B message determine new position with last valid
  position

Refer to [icao9871]_ for more details.
"""

import numpy as np

from .. import types as vmt
from ..util import create_array, hstack, vstack
from ._data import PosDecoderCtx, PosDecoderData, PosDecoderAuxData
from ._position import decode_positions, cpr_coordidnates

type VecIndex = vmt.UInt32

# page A-6 and A-7
LOOKUP_NUC_P = np.array(
    # typecode < 4
    [0] * 5
    # typecode in [5, 8], surface position
    + [9, 8, 7, 6]
    # typecode in [9, 18], airborne position, barometric
    + [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    # typecode = 19, difference between barometric altitude and GNSS height
    + [0]
    # typecode in [20, 22], airborne position, GNSS height
    + [9, 8, 0]
    # typecode in [23, 31]
    + [0] * 9
)

HPL = np.array([np.nan, 37040, 18520, 3704, 1852, 926, 370, 185, 25, 7.5])
RCU = np.array([np.nan, 18520, 9260, 1852, 926, 463, 185, 93, 10, 3])
RCV = np.array([np.nan] * 8 + [15, 4])

LOOKUP_HPL = HPL[LOOKUP_NUC_P]
LOOKUP_RCU = RCU[LOOKUP_NUC_P]
LOOKUP_RCV = RCV[LOOKUP_NUC_P]

assert len(LOOKUP_HPL) == len(LOOKUP_RCU) == len(LOOKUP_RCV)

def cpr_format_type(data: vmt.Message) -> vmt.CprFormat:
    """
    Determine CPR format type.

    CPR format type can be one of

    `0`
        Even format coding.
    `1`
        Odd format coding.

    .. seealso::

        - [icao9871]_, page A-8
        - https://mode-s.org/decode/content/ads-b/3-airborne-position.html

    """
    return ((data[:, 6] & 0x04) == 0x04).view(np.uint8)  # type: ignore

def nuc_p(data: vmt.Message, tc_data: vmt.TypeCode) -> vmt.MaUInt32:
    """
    Calculate navigational accuracy category for position (NUC_P).

    Return array with 3 columns

    - horizontal protection limit
    - 95% horizontal containment radius
    - 95% vertical containment radius

    :param data: ADS-B messages.
    :param tc_data: Type code information for each ADS-B message.
    """
    idx = (tc_data >= 5) & (tc_data <= 22)
    hpl = create_array(LOOKUP_HPL[tc_data], idx)
    rcu = create_array(LOOKUP_RCU[tc_data], idx)
    rcv = create_array(LOOKUP_RCV[tc_data], idx)
    return np.ma.column_stack([hpl, rcu, rcv])

def position(
        ctx: PosDecoderCtx,
        data: vmt.Message,
        time_data: vmt.Time,
        icao_data: vmt.Icao,
        tc_data: vmt.TypeCode,
) -> vmt.PositionData:
    """
    Decode aircraft surface and airborne positions.

    Use position decoder context to pass the state of calculations between
    function invocations.

    :param ctx: Position decoder context.
    :param data: ADS-B messages.
    :param time_data: Time of ADS-B messages.
    :param icao_data: ICAO address stored in ADS-B messages.
    :param tc_data: ADS-B message type code information.

    .. seealso::

        - [icao9871]_ section C.2.6.7, page C-54
    """

    # split data into surface and airborne positions
    idx_surface = (5 <= tc_data) & (tc_data <= 8)
    idx_airborne = ((9 <= tc_data) & (tc_data <= 18)) \
        | ((20 <= tc_data) & (tc_data <= 22))

    idx_pos = np.array(idx_surface) | np.array(idx_airborne)
    pos_msg = data[idx_pos]

    # merge carried over and new data
    pd_prev = ctx.carry_over
    msg_data = vstack(pd_prev.data.data, pos_msg)
    time_data = hstack(pd_prev.data.time, time_data[idx_pos])
    icao_data = hstack(pd_prev.data.icao, icao_data[idx_pos])
    tc_data = hstack(pd_prev.data.typecode, tc_data[idx_pos])
    idx_surface = hstack(pd_prev.is_surface, idx_surface[idx_pos])
    cpr_fmt = hstack(pd_prev.cpr_fmt, cpr_format_type(pos_msg))
    cpr_coord = vstack(pd_prev.cpr_coord, cpr_coordidnates(pos_msg))

    idx_pos_prev = np.full(pd_prev.size, True, dtype=np.bool_)
    idx_pos_all = hstack(idx_pos_prev, idx_pos)

    pd = PosDecoderData(msg_data, time_data, icao_data, tc_data)
    aux = PosDecoderAuxData(pd, idx_surface, cpr_fmt, cpr_coord)
    result = decode_positions(ctx, aux)
    idx_valid, pos, new_last_pos, carry_over = result

    positions = np.zeros((pd_prev.size + len(data), 2), dtype=np.double)
    positions[idx_pos_all] = pos

    idx_pos_all[idx_pos_all] = idx_valid

    positions: vmt.Position = create_array(positions, idx_pos_all)  # type: ignore
    # positions for carried over data
    prev_position: vmt.Position = positions[:pd_prev.size]  # type: ignore
    # positions for new message data
    new_position: vmt.Position = positions[pd_prev.size:]  # type: ignore

    # determine carry over data
    carry = PosDecoderAuxData(
        PosDecoderData(
            msg_data[carry_over],
            time_data[carry_over],
            icao_data[carry_over],
            tc_data[carry_over],
        ),
        idx_surface[carry_over],
        cpr_fmt[carry_over],
        cpr_coord[carry_over, :],
    )
    new_ctx = PosDecoderCtx(ctx.receiver, carry, new_last_pos)
    return vmt.PositionData(new_ctx, new_position, prev_position)

# vim: sw=4:et:ai
