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
.. note::

   1. Start position is used to start a track of an aircraft
      - it is globally determined position
      - it is not reported as a position of an aircraft in an explicit way
        (see below)
   2. Track position is used to report a track of an aircraft
      - it is locally determined position
      - first position of a track uses 2nd position message of start position;
        first position and start position are the same
"""

import cython
import logging
import numpy as np
from cython import Py_ssize_t

cimport numpy as cnp
from cpython.ref cimport PyObject
from libc.stdint cimport uint8_t, uint32_t, uint64_t, int32_t
from libc.math cimport acos, cos, fabs, floor, fmod, sqrt

from ._data cimport PosDecoder, PosDecoderCtx, PosDecoderAuxData, \
    PositionTime, Receiver, MessageCheck, Position, t_time, t_bool, \
    t_func_check_message

logger = logging.getLogger(__name__)

cdef extern from "arpa/inet.h":
    uint32_t ntohl(uint32_t)

# maximum time between even and odd ADS-B position messages
DEF TIME_SURFACE_MSG_PAIR = 50   # [icao9871]_, C.2.6.8
DEF TIME_AIRBORNE_MSG_PAIR = 10  # [icao9871]_, C.2.6.7

# maximum time between last position and ADS-B position message for locally
# unambiguous decoding of position [icao9871]_, C.2.6.10.3
DEF TIME_POS_TRACK = 30

# specification says "based on reception of a new odd and an even Position
# Message" ([icao9871]_, C.2.6.10.2), but we need to have some time limit when
# looking up next pair;
DEF TIME_NEXT_MESSAGE_PAIR = 30

# use maximum of above specified times for carry over cutoff
DEF TIME_CUTOFF_LAST = TIME_POS_TRACK
DEF TIME_CUTOFF_SRF = TIME_NEXT_MESSAGE_PAIR + 2 * TIME_SURFACE_MSG_PAIR
DEF TIME_CUTOFF_AIR = TIME_NEXT_MESSAGE_PAIR + 2 * TIME_AIRBORNE_MSG_PAIR

DEF M_PI = 3.14159265358979323846
# cos(M_PI / 30) 0.9945218953682733
DEF NL_A = 1 - 0.9945218953682733  # 30 == 15 * 2 == NZ * 2
DEF PI_DEG = M_PI / 180
DEF PI_2 = M_PI * 2

DEF R_EARTH = 6371000
DEF GRID_POS_AIRBORNE_VER = (5 / R_EARTH) ** 2
DEF GRID_POS_SURFACE_VER = (1.25 / R_EARTH) ** 2
DEF GRID_RECEIVER_VER = (666000 / R_EARTH) ** 2

# 2.5 nautical mile, surface participant receiving airborne position
# message
DEF GRID_TRACK_AIRBORNE = (2.5 * 1852 / R_EARTH) ** 2
# 0.75 nautical mile, surface participant receiving surface position
# message
DEF GRID_TRACK_SURFACE = (0.75 * 1852 / R_EARTH) ** 2

# definitions of decoders for surface and airborne positions decoding; used
# by `pos_decoder` function
cdef PosDecoder[2] POS_DECODER = [
    PosDecoder(
        decode_pos_air_local, decode_pos_air_global,
        TIME_AIRBORNE_MSG_PAIR, GRID_POS_AIRBORNE_VER, GRID_TRACK_AIRBORNE,
    ),
    PosDecoder(
        decode_pos_srf_local, decode_pos_srf_global,
        TIME_SURFACE_MSG_PAIR, GRID_POS_SURFACE_VER, GRID_TRACK_SURFACE,
    ),
]

#  constants for determining number of longitude zone for given latitude
DEF NL_INVALID = 0
DEF NL_NUM = 59

# transition latitudes for calculating longitude zones, see
#
# - [icao9871]_, section C.2.6.2, point (d)
# - [icao9871]_, section D.2.4.7.8, table D-3
#
# NL = table index + 1
cdef double[NL_NUM] NL_ARRAY = [
    # starting with NL 1 to 5
    90.0000000, 87.0000000, 86.5353700, 85.7554162, 84.8916619,
    83.9917356, 83.0719944, 82.1395698, 81.1980135, 80.2492321,
    79.2942823, 78.3337408, 77.3678946, 76.3968439, 75.4205626,
    74.4389342, 73.4517744, 72.4588454, 71.4598647, 70.4545107,
    69.4424263, 68.4232202, 67.3964677, 66.3617101, 65.3184531,
    64.2661652, 63.2042748, 62.1321666, 61.0491777, 59.9545928,
    58.8476378, 57.7274735, 56.5931876, 55.4437844, 54.2781747,
    53.0951615, 51.8934247, 50.6715017, 49.4277644, 48.1603913,
    46.8673325, 45.5462672, 44.1945495, 42.8091401, 41.3865183,
    39.9225668, 38.4124189, 36.8502511, 35.2289960, 33.5399344,
    31.7720971, 29.9113569, 27.9389871, 25.8292471, 23.5450449,
    # ending with NL 56 to 59
    21.0293949, 18.1862636, 14.8281744, 10.4704713,
]

#
# public API; functions
#

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
def cpr_coordidnates(uint8_t[:, :] data):
    """
    Calculate CPR coordinates.

    :param data: ADS-B messages.
    """
    cdef:
        Py_ssize_t size = len(data)
        Py_ssize_t i
        cnp.ndarray[cnp.double_t, ndim=2] result = np.zeros((size, 2), dtype=np.double)

    for i in range(size):
        result[i, 0] = (unpack_uint32(&data[i, 7]) & 0x0001ffff) / 131072.0
        result[i, 1] = ((unpack_uint32(&data[i, 5]) >> 1) & 0x0001ffff) / 131072.0

    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
def decode_positions(PosDecoderCtx ctx, PosDecoderAuxData aux):
    cdef:
        Py_ssize_t i
        t_bool in_past, is_track
        t_time time_delta, cutoff_last, cutoff_srf, cutoff_air, last_time
        Position pos
        PositionTime last

        # index of data to carry over for next position decoding
        cnp.ndarray[t_bool, ndim=1, cast=True] carry_over = np.full(
            aux.size, True, dtype=np.bool_
        )
        # index of valid positions in the result array
        cnp.ndarray[t_bool, ndim=1, cast=True] index = np.zeros(
            aux.size, dtype=np.bool_
        )
        cnp.ndarray[cnp.double_t, ndim=2] result = np.zeros(
            (aux.size, 2), dtype=np.double
        )

    # determine cutoff time for
    #
    # - last position of an aircraft in the position decoder context
    # - data for surface positions
    # - data for airborne positions
    #
    #  an item older than a cutoff is no longer necessary, and is not
    #  carried over
    if aux.size > 0:
        last_time = aux.data.time[aux.size - 1]
        cutoff_last = last_time - TIME_CUTOFF_LAST
        cutoff_srf = last_time - TIME_CUTOFF_SRF
        cutoff_air = last_time - TIME_CUTOFF_AIR
    else:
        cutoff_last = 0
        cutoff_srf = 0
        cutoff_air = 0

    for i in range(aux.size):
        last = ctx.get(aux.data.icao[i], aux.data.time[i])
        time_delta = aux.data.time[i] - last.time
        in_past = last.position.is_valid and time_delta <= 0

        # do not carry over data
        # - for which position is not to be determined
        # - which is no longer necessary
        carry_over[i] = not (
            in_past
            or aux.is_surface[i] and aux.data.time[i] < cutoff_srf
            or not aux.is_surface[i] and aux.data.time[i] < cutoff_air
        )

        # there is a valid position in the future; we are going over
        # carried over data, so let's skip
        if in_past:
            continue

        pos, is_track = aircraft_position(ctx, <PyObject*> aux, i, last, time_delta)

        if is_track and pos.is_valid:
            # only track positions are in the result; use start positions
            # to start a track only
            index[i] = True
            result[i, 0] = pos.longitude
            result[i, 1] = pos.latitude
        elif not is_track and not pos.is_valid:
            # if track is stopped, then invalidate last position to start
            # a new track
            ctx.unset(aux.data.icao[i])

        # start position starts a track, track position continues a track
        if pos.is_valid:
            last.time = aux.data.time[i]
            last.position = pos

        # do not carry over data for positions
        # - both valid and invalid track positions
        # - valid start position
        #
        # NOTE: carry_over might be false, then keep it false
        carry_over[i] = carry_over[i] and not (is_track or pos.is_valid)

        if __debug__:
            logger.debug('carry over: i={}, time={}, carry_over={}'.format(
                i, aux.data.time[i], carry_over[i]
            ))

    return index, result, ctx.prune(cutoff_last), carry_over

#
# decode position locally and globally
#

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline Position decode_pos_air_global(
        Position location, PyObject* aux, Py_ssize_t i, Py_ssize_t j
) noexcept:
    # NOTE: `location` argument is ignored; it is needed to match
    #       `decode_pos_srf_global` signature
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux

    return position_air_global(
        pd.cpr_coord[i, 0], pd.cpr_coord[i, 1],
        pd.cpr_coord[j, 0], pd.cpr_coord[j, 1],
        pd.cpr_fmt[j],
    )

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline Position decode_pos_srf_global(
        Position location, PyObject* aux, Py_ssize_t i, Py_ssize_t j
) noexcept:
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux

    return position_srf_global(
        location.longitude, location.latitude,
        pd.cpr_coord[i, 0], pd.cpr_coord[i, 1],
        pd.cpr_coord[j, 0], pd.cpr_coord[j, 1],
        pd.cpr_fmt[j],
    )

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline Position decode_pos_air_local(
        Position location, PyObject* aux, Py_ssize_t i
) noexcept:
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux

    return position_air_local(
        location.longitude, location.latitude,
        pd.cpr_coord[i, 0], pd.cpr_coord[i, 1],
        pd.cpr_fmt[i],
    )

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline Position decode_pos_srf_local(
        Position location, PyObject* aux, Py_ssize_t i
) noexcept:
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux

    return position_srf_local(
        location.longitude, location.latitude,
        pd.cpr_coord[i, 0], pd.cpr_coord[i, 1],
        pd.cpr_fmt[i],
    )

cpdef inline Position position_air_local(
        double ref_lon,
        double ref_lat,
        double cpr_lon,
        double cpr_lat,
        uint8_t is_odd,
) noexcept:
    return position_any_local(ref_lon, ref_lat, cpr_lon, cpr_lat, is_odd, 360)

cpdef inline Position position_srf_local(
        double ref_lon,
        double ref_lat,
        double cpr_lon,
        double cpr_lat,
        uint8_t is_odd,
) noexcept:
    return position_any_local(ref_lon, ref_lat, cpr_lon, cpr_lat, is_odd, 90)

@cython.cdivision(True)
cpdef inline Position position_air_global(
        double cpr_lon_prev,
        double cpr_lat_prev,
        double cpr_lon_next,
        double cpr_lat_next,
        uint8_t cpr_fmt_next,
) noexcept:
    cdef:
        double cpr_lon_odd, cpr_lon_even, cpr_lat_odd, cpr_lat_even
        uint8_t nl
        double longitude, latitude

        uint8_t is_odd = cpr_fmt_next

    cpr_lon_even, cpr_lat_even, cpr_lon_odd, cpr_lat_odd = coord_swap(
        is_odd,
        cpr_lon_prev, cpr_lat_prev,
        cpr_lon_next, cpr_lat_next,
    )

    lat_even, lat_odd = latitude_from_cpr(cpr_lat_even, cpr_lat_odd, 360)
    latitude = lat_odd if is_odd else lat_even

    nl = latitude_nl(lat_even, lat_odd)
    if nl == NL_INVALID:
        return Position(0, 0, False)

    longitude = longitude_from_cpr(cpr_lon_even, cpr_lon_odd, is_odd, nl, 360)
    return Position(longitude, latitude, True)

@cython.cdivision(True)
cpdef inline Position position_srf_global(
        double location_lon,
        double location_lat,
        double cpr_lon_prev,
        double cpr_lat_prev,
        double cpr_lon_next,
        double cpr_lat_next,
        uint8_t cpr_fmt_next,
) noexcept:
    cdef:
        double cpr_lon_odd, cpr_lon_even, cpr_lat_odd, cpr_lat_even
        uint8_t nl
        double longitude, latitude

        uint8_t is_odd = cpr_fmt_next

    cpr_lon_even, cpr_lat_even, cpr_lon_odd, cpr_lat_odd = coord_swap(
        is_odd,
        cpr_lon_prev, cpr_lat_prev,
        cpr_lon_next, cpr_lat_next,
    )

    lat_even, lat_odd = latitude_from_cpr(cpr_lat_even, cpr_lat_odd, 90)
    if location_lat < 0:
        lat_even = lat_even - 90
        lat_odd = lat_odd - 90
    latitude = lat_odd if is_odd else lat_even

    nl = latitude_nl(lat_even, lat_odd)
    if nl == NL_INVALID:
        return Position(0, 0, False)

    longitude = longitude_from_cpr(cpr_lon_even, cpr_lon_odd, is_odd, nl, 90)
    longitude = find_srf_longitude(location_lon, longitude)

    return Position(longitude, latitude, True)

@cython.cdivision(True)
cpdef inline Position position_any_local(
        double longitude,
        double latitude,
        double cpr_lon,
        double cpr_lat,
        uint8_t is_odd,
        double nl_base,
) noexcept:
    cdef:
        double d_lon, d_lat
        double j, m
        uint8_t ni
        double lon, lat

    assert is_odd == 0 or is_odd == 1

    d_lat = nl_base / (60 - is_odd)
    assert d_lat > 0.0

    j = floor(latitude / d_lat) \
        + floor(0.5 + cmod(latitude, d_lat) / d_lat - cpr_lat)
    lat = d_lat * (j + cpr_lat)

    ni = cpr_nl(lat) - is_odd
    d_lon = nl_base / ni if ni > 0 else nl_base
    assert d_lon > 0.0

    m = floor(longitude / d_lon) \
        + floor(0.5 + cmod(longitude, d_lon) / d_lon - cpr_lon)
    lon = d_lon * (m + cpr_lon)

    return Position(lon, lat, True)

#
# determining track of an aircraft
#

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline (Position, t_bool) aircraft_position(
        PosDecoderCtx ctx,
        PyObject* aux,
        Py_ssize_t i,
        PositionTime last,
        t_time time_delta
):
    """
    Determine start position or track position of an aircraft.
    """
    cdef:
        t_bool is_track
        PosDecoder p_decoder

        PosDecoderAuxData pd = <PosDecoderAuxData> aux

    if __debug__:
        logger.debug('track: i={}, time={:.6f}, icao={:6x}, valid={}, time_delta={:.6f}'.format(
            i, pd.data.time[i], pd.data.icao[i], last.position.is_valid, time_delta
        ))
    assert last.position.is_valid and time_delta > 0 or not last.position.is_valid

    is_track = last.position.is_valid and time_delta <= TIME_POS_TRACK
    if is_track:
        p_decoder = pos_decoder(pd.is_surface[i])
        pos = p_decoder.local_pos(last.position, aux, i)
        assert pos.is_valid

        # [icao9871]_, section C.2.6.10.3, greater or equal, then fail
        is_track = grid_distance(pos, last.position) < p_decoder.max_dist_pos_local
        if __debug__ and not is_track:
            logger.debug('track, distance invalid: i={}'.format(i))

    # when distance test fails for the track (see grid distance check
    # above), then
    #
    # - duplicate address processing should start
    # - and the current track should be continued using the last position
    #   (`last` variable) and next ads-b message
    #
    # vmodes has no concept of duplicate track at the moment, so it ignores
    # the invalid position, and tries to start new track
    if not is_track:
        pos = start_track(i, <PyObject*> ctx.receiver, aux)
        if __debug__:
            logger.debug('start: i={}, time={:.6f}, icao={:6x}, odd={}, valid={}, ({:.8f}, {:.8f})'.format(
                i, pd.data.time[i], pd.data.icao[i], pd.cpr_fmt[i],
                pos.is_valid, pos.longitude, pos.latitude
            ))

    # note: if track was active, and vmodes failed to start new track
    # (is_track == 0 and pos.is_valid == 0), then track is stopped; vmodes
    # shall invalidate last position; otherwise track might be continued

    return pos, is_track

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef Position start_track(
        Py_ssize_t start,
        PyObject *receiver,
        PyObject *aux,
):
    """
    Initialize track of an aircraft.
    """
    cdef:
        Py_ssize_t i_ref_2, i_ver_1, i_ver_2
        Position s_pos, v_pos, l_pos
        PosDecoder s_pos_dec, v_pos_dec

        Py_ssize_t i_ref_1 = start
        Receiver rcv = <Receiver> receiver
        PosDecoderAuxData pd = <PosDecoderAuxData> aux

        Position not_found = Position(0, 0, False)

    s_pos_dec = pos_decoder(pd.is_surface[start])
    i_ref_2 = find_message_global(check_next_message, s_pos_dec.max_time, i_ref_1, aux)
    if __debug__:
        logger.debug('start: i={}, i-pair={}'.format(i_ref_1, i_ref_2))
    if i_ref_2 == -1:
        return not_found

    i_ver_1 = find_message_global(check_next_pair, TIME_NEXT_MESSAGE_PAIR, i_ref_2, aux)
    if __debug__:
        logger.debug('start: i={}, i-pair={}, ver={}'.format(
            i_ref_1, i_ref_2, i_ver_1
        ))
    if i_ver_1 == -1:
        return not_found

    v_pos_dec = pos_decoder(pd.is_surface[i_ver_1])
    i_ver_2 = find_message_global(check_next_message, v_pos_dec.max_time, i_ver_1, aux)
    if __debug__:
        logger.debug('start: i={}, i-pair={}, ver={}, ver-pair={}'.format(
            i_ref_1, i_ref_2, i_ver_1, i_ver_2
        ))
    if i_ver_2 == -1:
        return not_found

    assert i_ref_1 < i_ref_2 < i_ver_1 < i_ver_2 < pd.size
    assert pd.is_surface[i_ref_1] == pd.is_surface[i_ref_2]
    assert pd.is_surface[i_ver_1] == pd.is_surface[i_ver_2]
    assert pd.cpr_fmt[i_ref_1] == 1 - pd.cpr_fmt[i_ref_2]
    assert pd.cpr_fmt[i_ver_1] == 1 - pd.cpr_fmt[i_ver_2]

    s_pos = s_pos_dec.global_pos(rcv.location, aux, i_ref_1, i_ref_2)
    if not s_pos.is_valid or grid_distance(s_pos, rcv.location) > GRID_RECEIVER_VER:
        if __debug__:
            if s_pos.is_valid:
                logger.debug('start position invalid: i={}'.format(i_ref_1))
            else:
                logger.debug(
                    'start position receiver distance test failed: i={}'
                    .format(i_ref_1)
                )
        return not_found

    v_pos = v_pos_dec.global_pos(rcv.location, aux, i_ver_1, i_ver_2)
    if not v_pos.is_valid:
        if __debug__:
            logger.debug('ver position invalid: i={}'.format(i_ref_1))
        return not_found

    l_pos = v_pos_dec.local_pos(s_pos, aux, i_ver_2)
    assert l_pos.is_valid
    if grid_distance(v_pos, l_pos) > v_pos_dec.max_dist_pos_ver:
        if __debug__:
            logger.debug('ver position distance test failed: i={}'.format(i_ref_1))
        return not_found

    assert s_pos.is_valid
    return s_pos

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline Py_ssize_t find_message_global(
        t_func_check_message check_f,
        t_time max_time,
        Py_ssize_t i,
        PyObject *aux
) noexcept:
    cdef:
        Py_ssize_t j
        MessageCheck msg_check

        PosDecoderAuxData pd = <PosDecoderAuxData> aux
        Py_ssize_t result = -1

    for j in range(i + 1, pd.size):
        msg_check = check_f(max_time, i, j, aux)
        if msg_check == MessageCheck.FOUND:
            result = j
            break
        elif msg_check == MessageCheck.NO_DATA:
            break

        assert msg_check == MessageCheck.NOT_FOUND

    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef MessageCheck check_next_message(
        t_time max_time,
        Py_ssize_t i,
        Py_ssize_t j,
        PyObject *aux,
) noexcept:
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux
        t_bool valid_time = pd.data.time[j] - pd.data.time[i] <= max_time

        MessageCheck result

    if not valid_time:
        result = MessageCheck.NO_DATA
    elif pd.data.icao[i] == pd.data.icao[j] and pd.is_surface[i] == pd.is_surface[j] and pd.cpr_fmt[i] == 1 - pd.cpr_fmt[j]:
        result = MessageCheck.FOUND
    else:
        result = MessageCheck.NOT_FOUND

    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef MessageCheck check_next_pair(
        t_time max_time,
        Py_ssize_t i,
        Py_ssize_t j,
        PyObject *aux,
) noexcept:
    cdef:
        PosDecoderAuxData pd = <PosDecoderAuxData> aux
        t_bool valid_time = pd.data.time[j] - pd.data.time[i] <= max_time

        MessageCheck result

    if not valid_time:
        result = MessageCheck.NO_DATA
    elif pd.data.icao[i] == pd.data.icao[j]:
        result = MessageCheck.FOUND
    else:
        result = MessageCheck.NOT_FOUND

    return result

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.initializedcheck(False)
cdef inline PosDecoder pos_decoder(t_bool is_surface) noexcept:
    """
    Get position decoder structure

    .. seealso:: PosDecoder
    """
    assert 0 <= is_surface <= 1
    return POS_DECODER[is_surface]

#
# coordinate decoding
#

@cython.cdivision(True)
cdef inline double longitude_from_cpr(
        double cpr_lon_even,
        double cpr_lon_odd,
        uint32_t is_odd,
        int32_t nl,
        double nl_base,
) noexcept:
    cdef:
        double m, cpr_base, longitude
        int32_t ni

    # for longitude decoding, a later message is a significant one
    #
    # is_odd -> t0 < t1 -> even message is significant:
    # - cpr_base = cpr_lon_even
    # - cpr_ni = max(nl, 1) = max(nl - is_odd, 1)
    #
    # not is_odd -> t0 > t1 -> odd message is significant:
    # - crp_base = cpr_lon_odd
    # - cpr_ni = max(nl, 1) = max(nl - is_odd, 1)
    cpr_base = cpr_lon_odd if is_odd else cpr_lon_even
    ni = max(nl - is_odd, 1)

    m = floor(cpr_lon_even * (nl - 1) - cpr_lon_odd * nl + 0.5)
    longitude = (nl_base / ni) * (cmod(m, ni) + cpr_base)

    return adjust_value(longitude, 180, 360)

cdef inline (double, double) latitude_from_cpr(
        double cpr_lat_even,
        double cpr_lat_odd,
        double d_lat_base,
) noexcept:
    cdef:
        double j, air_d_lat_even, air_d_lat_odd
        double lat_even, lat_odd

    j = floor(59 * cpr_lat_even - 60 * cpr_lat_odd + 0.5)

    air_d_lat_even = d_lat_base / 60
    air_d_lat_odd = d_lat_base / 59

    lat_even = air_d_lat_even * (cmod(j, 60) + cpr_lat_even)
    lat_odd = air_d_lat_odd * (cmod(j, 59) + cpr_lat_odd)

    lat_even = adjust_value(lat_even, 270, 360)
    lat_odd = adjust_value(lat_odd, 270, 360)
    return lat_even, lat_odd

cdef inline double find_srf_longitude(double location_lon, double longitude) noexcept:
    """
    Find solution for longitude of surface position.

    There are four possible solutions. find the closest one to the
    longitude of emitter location `location_lon`.

    See [icao9871]_, section C.2.6.8.
    """
    cdef:
        double c_lon, c_lon_dist, lon_dist
        uint32_t k

        double result = longitude

    assert -180 <= longitude <= 180

    lon_dist = fabs(result - location_lon)
    for k in range(90, 271, 90):  # 90, 180, 270
        c_lon = cmod(longitude + k + 180, 360) - 180
        c_lon_dist = fabs(c_lon - location_lon)
        if c_lon_dist < lon_dist:
            result = c_lon

    assert -180 <= result <= 180
    return result

cpdef inline uint8_t latitude_nl(double lat_even, double lat_odd) noexcept:
    """
    Calculate and check longitude zone number NL.

    Return 0 (invalid longitude zone number) if NL differs for both
    latitude values.
    """
    cdef:
        uint8_t nl
        double abs_lat

    nl = cpr_nl(lat_even)
    abs_lat = norm_latitude(lat_odd)

    # NOTE: NL_ARRAY order is descending
    if NL_ARRAY[nl - 1] >= abs_lat > NL_ARRAY[nl]:
        return nl
    else:
        return NL_INVALID

@cython.cdivision(True)
cpdef inline uint8_t cpr_nl(double latitude) noexcept:
    """
    Calculate number of longitude zone for given latitude.

    :param latitude: Input latitude.
    """
    cdef:
        uint8_t nl
        double abs_lat

    abs_lat = norm_latitude(latitude)
    nl = bisect_rev_right(NL_ARRAY, abs_lat, NL_NUM)

    assert 1 <= nl <= NL_NUM  # [icao9871]_, section C.2.6.2, point (d)
    return nl

cdef inline (double, double, double, double) coord_swap(
        uint8_t is_odd,
        double lon1,
        double lat1,
        double lon2,
        double lat2,
) noexcept:
    if not is_odd:
        lon1, lon2 = lon2, lon1
        lat1, lat2 = lat2, lat1
    return lon1, lat1, lon2, lat2

cdef inline double norm_latitude(double latitude) noexcept:
    """
    Normalize latitude so its value is in [0, 90] range.

    The function is used when calculating longitude zone for given
    latitude.
    """
    cdef double abs_lat

    abs_lat = fabs(latitude)
    if abs_lat > 90:
        abs_lat = cmod(abs_lat, 90)

    assert 0 <= abs_lat <= 90
    return abs_lat

#
# math and distance functions
#

cpdef double pos_distance(Position p1, Position p2) noexcept:
    """
    Calculate distance between two WGS84 positions using equirectangular
    projection.

    See also https://en.wikipedia.org/wiki/Equirectangular_projection.

    :param p1: First position.
    :param p2: Second position.
    """
    return R_EARTH * sqrt(grid_distance(p1, p2))

cdef inline double grid_distance(Position p1, Position p2) noexcept:
    cdef:
        double rx1 = radians(p1.longitude)
        double ry1 = radians(p1.latitude)
        double rx2 = radians(p2.longitude)
        double ry2 = radians(p2.latitude)

        double dx, dy

    dx = (rx2 - rx1) * cos((ry1 + ry2) / 2)
    dy = ry2 - ry1
    return dx ** 2 + dy ** 2

@cython.cdivision(True)
cdef inline double cmod(double x, double y) noexcept:
    """
    Get reminder of `x / y` division as defined by ICAO.

    For modulus function defined by ICAO, see [icao9871]_, section 2.6.2.

    .. note::

       For negative `x`, the function is different than `fmod` C function
       or Python's `math.fmod` function, and is similar to the modulo
       operator in the Python language.

    """
    assert y > 0.0
    return x - y * floor(x / y)

cdef inline double radians(double degree) noexcept:
    return degree * PI_DEG

cdef inline double adjust_value(
        double value,
        int32_t limit,
        int32_t correction,
) noexcept:
    return value - correction if value >= limit else value

#
# other utilities
#

cdef uint8_t bisect_rev_right(double[] arr, double val, Py_ssize_t size) noexcept:
    # NOTE: based on functions from Python's bisect module
    # find index where to insert item `val` in reverse sorted list `arr`;
    # if val is equal an item in `arr`, then it is inserted *before*; this
    # function is intented to be used with `cpr_nl` function only
    cdef:
        uint8_t mid

        uint8_t lo = 0
        uint8_t hi = size

    assert hi < 127

    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] >= val:
            lo = mid + 1
        else:
            hi = mid

    return lo

cdef inline uint32_t unpack_uint32(const uint8_t* data) noexcept:
    return ntohl((<uint32_t*> data)[0])

# vim: sw=4:et:ai
