#!/usr/bin/env python3
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
Build setup for the VModeS library.
"""

import numpy
from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        [
            Extension(
                'vmodes.decoder._position',
                ['vmodes/decoder/_position.pyx'],
                include_dirs=[numpy.get_include()],
            ),
            Extension(
                'vmodes.decoder._data',
                ['vmodes/decoder/_data.pyx'],
                include_dirs=[numpy.get_include()],
            ),
        ],
        compiler_directives={
            'embedsignature': True,
            'embedsignature.format': 'python',
            'language_level': 3,
            'profile': False,
        },
    ),
)

# vim: sw=4:et:ai
