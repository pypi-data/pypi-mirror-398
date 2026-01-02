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

from .. import types as vmt
from ._data import PosDecoderCtx, PosDecoderAuxData, IcaoPosition

def cpr_coordidnates(data: vmt.Message) -> vmt.CprCoordinate: ...

def decode_positions(ctx: PosDecoderCtx, data: PosDecoderAuxData) \
    -> tuple[vmt.BIndex, vmt.Position, IcaoPosition, vmt.BIndex]: ...

def position_air_local(
        longitude: float,
        latitude: float,
        cpr_lon: float,
        cpr_lat: float,
        cpr_fmt: bool,
) -> vmt.CPosition: ...

def position_srf_local(
        location_lon: float,
        location_lat: float,
        cpr_lon_prev: float,
        cpr_lat_prev: float,
        cpr_lon_next: float,
        cpr_lat_next: float,
        cpr_fmt_next: bool,
) -> vmt.CPosition: ...

def position_air_global(
        cpr_lon_prev: float,
        cpr_lat_prev: float,
        cpr_lon_next: float,
        cpr_lat_next: float,
        cpr_fmt_next: bool,
) -> vmt.CPosition: ...

def position_srf_global(
        location_lon: float,
        location_lat: float,
        cpr_lon_prev: float,
        cpr_lat_prev: float,
        cpr_lon_next: float,
        cpr_lat_next: float,
        cpr_fmt_next: bool,
) -> vmt.CPosition: ...

def pos_distance(p1: vmt.CPosition, p2: vmt.CPosition) -> float: ...
def cpr_nl(longitude: float) -> int: ...
def latitude_nl(lat_even: float, lat_odd: float) -> int: ...

# vim: sw=4:et:ai
