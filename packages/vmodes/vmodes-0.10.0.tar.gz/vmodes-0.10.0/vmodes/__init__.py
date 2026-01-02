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
Vectorized decoding of Mode S and ADS-B aircraft data.

VModeS is a library for vectorized decoding of Mode S and ADS-B messages
sent by an aircraft.

The library decodes the following Mode S and ADS-B aircraft data

- ICAO address
- aircraft callsign
- aircraft category
- surface and airborne positions
- altitude
- position uncertainty

VModeS decodes and validates surface and airborne positions according to
ICAO standard. See [icao9871]_ for details.

Decoding of data is implemented using NumPy and Cython. Most of the
functions use NumPy arrays for both input and output.

The library is designed for real-time, streaming, and batching applications.
In particular, special care was taken when implementing decoding of aircraft
positions to meet demands of such applications.

Decoding of Data
================
Decoding functions, implemented by VModeS library, require Mode S and ADS-B
messages in binary format. Some functions, like aircraft position decoding,
need time of a message (Unix time) as well.

Output of a function is usually a NumPy array ([numpy]_). Output always has
the same number of items as the input. If decoding of a specific value in
the input is not possible, then a corresponding entry in the output NumPy
array is masked.

Basic decoding of aircraft messages is illustrated with the example below.
It shows decoding of downlink format, ICAO address, type code, and call
sign information. The input and outputs are discussed in more detail after
the example.

    >>> import vmodes
    >>> import numpy as np
    >>> from binascii import unhexlify

    >>> data_hex = ['a8281d3030000000000000850d4a', '8d406b902015a678d4d220000000', '904ca3da121010603d04f5df3ecf', '8d4ca4ed5861634672f4709ed8c9']
    >>> data = [unhexlify(m) for m in data_hex]

    >>> messages = vmodes.message_array(data)
    >>> df = vmodes.df(messages)
    >>> icao = vmodes.icao(messages, df)
    >>> tc = vmodes.typecode(messages, df)
    >>> callsign = vmodes.callsign(messages, tc)

    >>> names = ['message', 'df', 'icao', 'typecode', 'callsign']
    >>> icao_hex = np.vectorize(hex, otypes=[np.str_])(icao)
    >>> items = [data_hex, df, tc, icao_hex, callsign]
    >>> result = np.rec.fromarrays(items, names=names)
    >>> result
    rec.array([('a8281d3030000000000000850d4a', 21,  0, '0x896217', ''),
               ('8d406b902015a678d4d220000000', 17,  4, '0x406b90', 'EZY85MH_'),
               ('904ca3da121010603d04f5df3ecf', 18,  2, '0x4ca3da', 'DAA_OPS5'),
               ('8d4ca4ed5861634672f4709ed8c9', 17, 11, '0x4ca4ed', '')],
              dtype=[('message', '<U28'), ('df', 'u1'), ('icao', 'u1'), ('typecode', '<U8'), ('callsign', '<U8')])

Result of most of decoding functions is a NumPy array::

    >>> type(df)
    <class 'numpy.ndarray'>
    >>> type(icao)
    <class 'numpy.ma.MaskedArray'>
    >>> type(callsign)
    <class 'numpy.ma.MaskedArray'>

Aircraft messages cannot always be decoded

- type code is available for downlink formats `17` and `18`
- calls sign is available for type code values from `1` to `4`

When decoding of an input value is not possible, then a corresponding entry
in an output is masked::

    >>> df
    array([21, 17, 18, 17], dtype=uint8)

    >>> tc
    masked_array(data=[--, 4, 2, 11],
                 mask=[ True, False, False, False],
           fill_value=np.uint64(999999),
                dtype=uint8)

    >>> callsign
    masked_array(data=[--, 'EZY85MH_', 'DAA_OPS5', --],
                 mask=[ True, False, False,  True],
           fill_value='N/A',
                dtype='<U8')

Retrieve valid values from an array::

    >>> callsign.compressed()
    array(['EZY85MH_', 'DAA_OPS5'], dtype='<U8')

or use `data_index` utility function::

    >>> idx = vmodes.data_index(callsign)
    >>> idx
    array([False,  True,  True, False])
    >>> callsign[idx]
    masked_array(data=['EZY85MH_', 'DAA_OPS5'],
                 mask=[False, False],
           fill_value='N/A',
                dtype='<U8')


Acknowledgements
================

This library is inspired by pyModeS project by Junzi Sun. Learn more about
Mode S and ADS-B data with his book at

    https://mode-s.org/decode/

References
==========

.. [numpy] Harris, C.R., Millman, K.J., van der Walt, S.J. et al.,
           Array programming with NumPy,
           Nature 585, 357-362 (2020),
           DOI: 10.1038/s41586-020-2649-2,
           https://numpy.org/

.. [sun1090mhz] Sun, Junzi,
                The 1090 Megahertz Riddle: A Guide to Decoding Mode S and ADS-B Signals,
                TU Delft OPEN Publishing (2021),
                ISBN: 978-94-6366-402-8,
                DOI: 10.34641/mg.11,
                https://mode-s.org/decode/

.. [icao9871] Doc 9871, Technical Provisions for Mode S Services and Extended Squitter,
              International Civil Aviation Organization (2012),
              ISBN: 978-92-9249-042-3
"""

from importlib.metadata import version

from .ctor import message_array
from .types import Time, Message, DownlinkFormat, TypeCode, Icao, Altitude, \
    Position, PositionData
from .decoder._data import PosDecoderCtx, PosDecoderData, PosDecoderAuxData, \
    Receiver
from .decoder.msg_info import df, typecode
from .decoder.aircraft import icao, callsign, category
from .decoder.position import nuc_p, cpr_format_type, position
from .decoder.altitude import altitude
from .util import data_index

__version__ = version('vmodes')

__all__ = [
    'Altitude',
    'DownlinkFormat',
    'Icao',
    'Message',
    'PosDecoderAuxData',
    'PosDecoderCtx',
    'PosDecoderData',
    'Position',
    'PositionData',
    'Receiver',
    'Time',
    'TypeCode',
    'altitude',
    'callsign',
    'category',
    'cpr_format_type',
    'data_index',
    'df',
    'icao',
    'message_array',
    'nuc_p',
    'position',
    'typecode',
]

# vim: sw=4:et:ai
