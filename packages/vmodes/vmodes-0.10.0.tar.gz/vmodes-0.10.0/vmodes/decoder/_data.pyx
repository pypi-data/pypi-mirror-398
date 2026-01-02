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

import cython
import numpy as np
from cython import Py_ssize_t

cimport numpy as cnp
from libc.stdint cimport uint8_t

cdef class Receiver:
    def __cinit__(
            self,
            double longitude,
            double latitude,
            double range=666000
    ):
        self.location = Position(longitude, latitude, True)
        self.range = range

@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class PosDecoderCtx:
    def __cinit__(
            self,
            Receiver receiver,
            PosDecoderAuxData carry_over=None,
            dict icao_position=None,
    ):
        self.receiver = receiver
        self.carry_over = PosDecoderAuxData.empty() if carry_over is None else carry_over
        self.icao_position = {} if icao_position is None else icao_position

    cdef PositionTime get(self, t_icao icao, t_time time):
        cdef PositionTime last = self.icao_position.get(icao)

        if last is None:
            last = PositionTime(time)
            self.icao_position[icao] = last
            assert not last.position.is_valid

        return last

    cdef void unset(self, t_icao icao):
        cdef PositionTime last = self.icao_position.get(icao)
        if last is not None:
            last.position.is_valid = 0

    cdef dict prune(self, t_time cutoff):
        cdef:
            t_icao icao
            PositionTime last

        return {
            icao: last for icao, last in self.icao_position.items()
            if last.time >= cutoff
        }


@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class PositionTime:
    def __cinit__(self, t_time time):
        self.time = time
        self.position = Position(0, 0, False)

@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class PosDecoderAuxData:
    def __cinit__(
            self,
            PosDecoderData data,
            t_bool[:] is_surface,
            uint8_t[:] cpr_fmt,
            double[:, :] cpr_coord,
    ):
        assert data.size == len(is_surface) == len(cpr_fmt) == len(cpr_coord)

        self.data = data
        self.is_surface = is_surface
        self.cpr_fmt = cpr_fmt
        self.cpr_coord = cpr_coord

        self.size = data.size

    @staticmethod
    cdef PosDecoderAuxData empty():
        cdef:
            PosDecoderData data = PosDecoderData.empty()
            cnp.ndarray[t_bool, ndim=1, cast=True] is_surface = np.zeros(0, dtype=np.bool_)
            cnp.ndarray[cnp.uint8_t, ndim=1, cast=True] cpr_fmt = np.zeros(0, dtype=np.bool_)
            cnp.ndarray[cnp.double_t, ndim=2] cpr_coord = np.zeros((0, 2), dtype=np.double)

        return PosDecoderAuxData(data, is_surface, cpr_fmt, cpr_coord)

@cython.no_gc_clear
@cython.final
@cython.freelist(1000)
cdef class PosDecoderData:
    def __cinit__(
            self,
            uint8_t[:, :] data,
            t_time[:] time,
            t_icao[:] icao,
            uint8_t[:] typecode,
    ):
        assert len(data) == len(time) == len(icao) == len(typecode)

        self.data = data
        self.time = time
        self.icao = icao
        self.typecode = typecode

        self.size = len(data)

    @staticmethod
    cdef PosDecoderData empty():
        cdef:
            cnp.ndarray[cnp.uint8_t, ndim=2] data = np.zeros((0, 14), dtype=np.uint8)
            cnp.ndarray[t_time, ndim=1] time = np.zeros(0, dtype=np.double)
            cnp.ndarray[t_icao, ndim=1] icao = np.zeros(0, dtype=np.uint32)
            cnp.ndarray[cnp.uint8_t, ndim=1] tc = np.zeros(0, dtype=np.uint8)

        return PosDecoderData(data, time, icao, tc)

# vim: sw=4:et:ai
