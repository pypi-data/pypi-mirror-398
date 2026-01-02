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

from cython import Py_ssize_t

from cpython.ref cimport PyObject
from libc.stdint cimport uint8_t, uint32_t

ctypedef double t_time    # Unix time, usually of a position
ctypedef uint32_t t_icao  # ICAO address of an aircraft
ctypedef uint8_t t_bool   # boolean value (or index)

ctypedef MessageCheck (*t_func_check_message) \
        (t_time, Py_ssize_t, Py_ssize_t, PyObject*) noexcept

ctypedef Position (*t_func_position_local) \
        (Position, PyObject*, Py_ssize_t) noexcept

ctypedef Position (*t_func_position_global) \
        (Position, PyObject*, Py_ssize_t, Py_ssize_t) noexcept

cdef enum MessageCheck:
    NO_DATA     # stop looking for messages
    NOT_FOUND   # messagge not found, look for more
    FOUND       # message is found

cdef struct Position:
    double longitude
    double latitude
    t_bool is_valid

# Surface or airborne positions decoding functions and data.
#
# :var local_pos: Function to locally determine a position.
# :var global_pos: Function to globally determine a position.
# :var max_time: Maximum time allowed between an even and an odd position
#     message.
# :var max_dist_pos_ver: Maximum distance allowed when verifying
#     a globally determined position.
#
# .. seealso:: pos_decoder
cdef struct PosDecoder:
    t_func_position_local local_pos
    t_func_position_global global_pos
    double max_time
    double max_dist_pos_ver
    double max_dist_pos_local

cdef class Receiver:
    """
    Mode S and ADS-B messages receiver location and range.

    :var location: Receiver location.
    :var range: Receiver location range (in meters).
    """
    cdef:
        Position location
        double range

cdef class PositionTime:
    cdef:
        public double time
        public Position position

cdef class PosDecoderData:
    """
    Data required for decoding of aircraft positions.

    Input contains Mode S messages, which can be narrowed down to position
    ADS-B messages with type code data.

    :var data: Mode S messages.
    :var time: Time of receiving of Mode S messages.
    :var icao: Airplane ICAO address.
    :var typecode: ADS-B message type code information.
    :var size: Number of records in the data.
    """
    cdef:
        public uint8_t[:, :] data
        public double[:] time
        public t_icao[:] icao
        public uint8_t[:] typecode
        public Py_ssize_t size

    @staticmethod
    cdef PosDecoderData empty()

cdef class PosDecoderAuxData:
    """
    Auxilary data for position decoding.

    Contains data for position ADS-B messages only.

    :var data: Data required for decoding of aircraft positions.
    :var is_surface: True if ADS-B message is for a surface position.
    :var cpr_fmt: True if ADS-B message is odd position message.
    :var cpr_coord: Position compact data (CPR coordinates).
    :var size: Number of records in the data.
    """
    cdef:
        public PosDecoderData data
        public t_bool[:] is_surface
        public uint8_t[:] cpr_fmt
        public double[:, :] cpr_coord
        public Py_ssize_t size

    @staticmethod
    cdef PosDecoderAuxData empty()

cdef class PosDecoderCtx:
    """
    Context for aircraft position decoding.

    Dictionary key of most recent position is an ICAO address of an
    aircraft.

    :var receiver: Mode S and ADS-B messages receiver information.
    :var carry_over: Carry over data for next position decoding.
    :var icao_position: Most recent position of an aircraft.
    """
    cdef:
        public Receiver receiver
        public PosDecoderAuxData carry_over
        public dict icao_position

    cdef PositionTime get(self, t_icao, double)
    cdef void unset(self, t_icao)
    cdef dict prune(self, double)

# vim: sw=4:et:ai
