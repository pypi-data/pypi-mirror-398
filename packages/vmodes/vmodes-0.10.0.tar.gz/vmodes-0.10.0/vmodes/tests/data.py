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
import typing as tp

NO_COORD = np.nan
EMPTY_STATE: dict[str, list[tp.Any]] = {
    'icao': [], 'time': [], 'position': [], 'valid': [], 'carry_over_time': [],
    'prev_position': [],
}

# legend for a stream of messages
#
#   . - any non-position message
#   o - position message, odd cpr format type
#   e - position message, even cpr format type
#   i - message for non-valid position
#   [a] - all following position messages are airborne ones
#   [s] - all following position messages are surface ones
#   [f] - following message fails some check
#   <space> - new chunk of messages in a stream

# test: no crash, when no ads-b position messages in input
# stream: ...
P_MSG_0 = (
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
)
P_STATE_0 = (EMPTY_STATE,)

# test: last known airborne position is reused in a next chunk of messages
#       in a stream
# stream: [a].o.e..e.o. .ee. .i..o.
P_MSG_1 = (
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212323.707462, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.254611, '8d4ca4ed5861a345e0f4bf8d3262', (-5.21980286, 52.90942383)),  # 4ca4ed 17 11 a 0
    (0, 1676212324.593688,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.297388, '8d4ca4ed5861934616f4a174496e', (-5.22209167, 52.91065979)),  # 4ca4ed 17 11 a 0
    (0, 1676212325.620938,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.898300, '8d4ca4ed586186afaefc022b21cb', (-5.22305734, 52.91122695)),  # 4ca4ed 17 11 a 1  last known position
    (0, 1676212326.333228, '8d4ca4ed990d011d986420804acb',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -

    (1, 1676212326.600000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212326.665183, '8d4ca4ed586173465af47d7a165b', (-5.22483826, 52.91221619)),  # 4ca4ed 17 11 a 0
    (1, 1676212327.212929, '8d4ca4ed5861634672f4709ed8c9', (-5.22583008, 52.91276550)),  # 4ca4ed 17 11 a 0  last known position
    (1, 1676212327.100000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -

    (2, 1676212327.814243, '8d4ca4edf82300060048784c3105',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 31 n -
    # the following ads-b message fails track distance check; it triggers
    # track restart, so let's comment it out as it is out of scope for this
    # test
    # (2, 1676212327.817334, '8d4ca4ed586165bfd578531f21ce',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1  invalid
    (2, 1676212327.973889, '8d4ca4ed990d001d98681f359b25',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (2, 1676212328.348986,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (2, 1676212328.351835, '8d4ca4ed586156b024fbc321d7af', (-5.22800119, 52.91397353)),  # 4ca4ed 17 11 a 1
    (2, 1676212328.460821, '8d4ca4ed990d001d986820cb1a05',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
)
P_STATE_1 = (
    {'icao': [0x4ca4ed], 'time': [1676212325.898300], 'position': [(-5.22305734, 52.91122695)], 'valid': [True], 'prev_position': [], 'carry_over_time': []},
    {'icao': [0x4ca4ed], 'time': [1676212327.212929], 'position': [(-5.22583008, 52.91276550)], 'valid': [True], 'prev_position': [], 'carry_over_time': []},
    {'icao': [0x4ca4ed], 'time': [1676212328.351835], 'position': [(-5.22800119, 52.91397353)], 'valid': [True], 'prev_position': [], 'carry_over_time': []},
)

# test: use ads-b position messages from one previous chunk to determine
#       global position, validate that position, and calculate new positions;
#       positions from the previous chunk are stored as "previous positions"
# stream: [a].o.e..e .o..ee.
P_MSG_2 = (
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212323.707462, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1  validated here
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.254611, '8d4ca4ed5861a345e0f4bf8d3262',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 0  (-5.21980286, 52.90942383)
    (0, 1676212324.593688,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.297388, '8d4ca4ed5861934616f4a174496e',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 0  (-5.22209167, 52.91065979)

    (1, 1676212325.620938,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212325.898300, '8d4ca4ed586186afaefc022b21cb', (-5.22305734, 52.91122695)),  # 4ca4ed 17 11 a 1
    (1, 1676212326.333228, '8d4ca4ed990d011d986420804acb',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (1, 1676212326.600000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212326.665183, '8d4ca4ed586173465af47d7a165b', (-5.22483826, 52.91221619)),  # 4ca4ed 17 11 a 0
    (1, 1676212327.212929, '8d4ca4ed5861634672f4709ed8c9', (-5.22583008, 52.91276550)),  # 4ca4ed 17 11 a 0
    (1, 1676212327.100000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
)
P_STATE_2 = (
    {
        'icao': [0x4ca4ed],
        'time': [1676212323.707462],
        'position': [(0, 0)],
        'valid': [False],
        'carry_over_time': [1676212323.707462, 1676212324.254611, 1676212325.297388],
        'prev_position': [],
    },
    {
        'icao': [0x4ca4ed],
        'time': [1676212327.212929],
        'position': [(-5.22583008, 52.91276550)],
        'valid': [True],
        'carry_over_time': [],
        'prev_position': [(-5.21980286, 52.90942383), (-5.22209167, 52.91065979)],
    },
)

# test: use ads-b position messages from two previous chunks to determine
#       global position, validate that position, and calculate new positions;
#       positions from the previous chunks are stored as "previous positions"
# stream: [a].o.e ..e .o..ee.
P_MSG_3 = (
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212323.707462, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1  validated here
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.254611, '8d4ca4ed5861a345e0f4bf8d3262',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 0  (-5.21980286, 52.90942383)

    (1, 1676212324.593688,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212325.297388, '8d4ca4ed5861934616f4a174496e',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 0  (-5.22209167, 52.91065979)

    (2, 1676212325.620938,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (2, 1676212325.898300, '8d4ca4ed586186afaefc022b21cb', (-5.22305734, 52.91122695)),  # 4ca4ed 17 11 a 1
    (2, 1676212326.333228, '8d4ca4ed990d011d986420804acb',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (2, 1676212326.600000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (2, 1676212326.665183, '8d4ca4ed586173465af47d7a165b', (-5.22483826, 52.91221619)),  # 4ca4ed 17 11 a 0
    (2, 1676212327.212929, '8d4ca4ed5861634672f4709ed8c9', (-5.22583008, 52.91276550)),  # 4ca4ed 17 11 a 0
    (2, 1676212327.100000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
)
P_STATE_3 = (
    {
        'icao': [0x4ca4ed],
        'time': [1676212323.707462],
        'position': [(0, 0)],
        'valid': [False],
        'carry_over_time': [1676212323.707462, 1676212324.254611],
        'prev_position': [],
    },
    {
        'icao': [0x4ca4ed],
        'time': [1676212323.707462],
        'position': [(0, 0)],
        'valid': [False],
        'carry_over_time': [1676212323.707462, 1676212324.254611, 1676212325.297388],
        'prev_position': [],
    },
    {
        'icao': [0x4ca4ed],
        'time': [1676212327.212929],
        'position': [(-5.22583008, 52.91276550)],
        'valid': [True],
        'carry_over_time': [],
        'prev_position': [(-5.21980286, 52.90942383), (-5.22209167, 52.91065979)],
    },
)

# test: carry over data of ads-b messages is correct; use of carry over data
#       does not generate additional positions
# stream: [a]o[+50s]o[+10s].o.e..e.o ..ee.
P_MSG_4 = (
    (0, 1676212272.000000, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212312.000000, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1  can generate additional previous message
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212323.707462, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.254611, '8d4ca4ed5861a345e0f4bf8d3262', (-5.21980286, 52.90942383)),  # 4ca4ed 17 11 a 0
    (0, 1676212324.593688,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.297388, '8d4ca4ed5861934616f4a174496e', (-5.22209167, 52.91065979)),  # 4ca4ed 17 11 a 0
    (0, 1676212325.620938,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.898300, '8d4ca4ed586186afaefc022b21cb', (-5.22305734, 52.91122695)),  # 4ca4ed 17 11 a 1

    (1, 1676212326.333228, '8d4ca4ed990d011d986420804acb',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (1, 1676212326.600000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (1, 1676212326.665183, '8d4ca4ed586173465af47d7a165b', (-5.22483826, 52.91221619)),  # 4ca4ed 17 11 a 0
    (1, 1676212327.212929, '8d4ca4ed5861634672f4709ed8c9', (-5.22583008, 52.91276550)),  # 4ca4ed 17 11 a 0
    (1, 1676212327.100000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
)
P_STATE_4 = (
    {
        'icao': [0x4ca4ed],
        'time': [1676212325.898300],
        'position': [(-5.22305734, 52.91122695)],
        'valid': [True],
        'carry_over_time': [1676212312.000000],
        'prev_position': [],
    },
    {
        'icao': [0x4ca4ed],
        'time': [1676212327.212929],
        'position': [(-5.22583008, 52.91276550)],
        'valid': [True],
        'carry_over_time': [],
        'prev_position': [],
    },
)

# test: last known surface position is reused in a next chunk of messages
#       in a stream; a positions fail local reasonabless test
# stream: [s]o[+6s]o.[+46s]e..o.o.o.e e.
P_MSG_5 = (
    (0, 1704108111.759284, '8c4ca98c3810041bc544b1cd83ac',       (NO_COORD, NO_COORD)),  # 4ca98c 17 07 s 1  even message > 50 sec
    (0, 1704108118.323862, '8c4ca98c3810041bc544b1cd83ac',       (NO_COORD, NO_COORD)),  # 4ca98c 17 07 s 1  next position fails reasonabless test (local)
    (0, 1704108118.487454, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108164.525671, '8c4ca98c3920027ba12107e70fc7',       (NO_COORD, NO_COORD)),  # 4ca98c 17 07 s 0
    (0, 1704108167.914949, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108169.604120, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108169.874646, '8c4ca98c3910041bad449fb14ad9', (-6.26287348, 53.43105252)),  # 4ca98c 17 07 s 1
    (0, 1704108172.112674, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108173.201341, '8c4ca98c3900041bab449acfbe08', (-6.26297446, 53.43104088)),  # 4ca98c 17 07 s 1
    (0, 1704108173.808476, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108176.698019, '8c4ca98c3900041baf4495074f44', (-6.26307544, 53.43106415)),  # 4ca98c 17 07 s 1
    (0, 1704108176.870261, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
    (0, 1704108177.135960, '8c4ca98c3900027b9d20f3892355', (-6.26308986, 53.43106842)),  # 4ca98c 17 07 s 0

    (1, 1704108178.124581, '8c4ca98c3900027b9f20f26d7fde', (-6.26310948, 53.43107986)),  # 4ca98c 17 07 s 0
    (1, 1704108178.614104, '8c4ca98cf9002202804a30209afd',       (NO_COORD, NO_COORD)),  # 4ca98c 17 31 n -
)
P_STATE_5 = (
    {
        'icao': [0x4ca98c],
        'time': [1704108177.135960],
        'position': [(-6.26308986, 53.43106842)],
        'valid': [True],
        'carry_over_time': [1704108111.759284],
        'prev_position': [],
    },
    EMPTY_STATE | {'icao': [0x4ca98c], 'time': [1704108178.124581], 'position': [(-6.26310948, 53.43107986)], 'valid': [True]},
)

# test: surface position reasonabless test is performed with airborne
#       position data
# stream: [s]eeo.[a]o...ee
P_MSG_6 = (
    (0, 1704695698.847369, '8c4ca304427a22755f1d7b6bf695',       (NO_COORD, NO_COORD)),  # 4ca304 17 08 s 0
    (0, 1704695699.435441, '8c4ca304427a22755d1d7e8f9228', (-6.28045218, 53.42191315)),  # 4ca304 17 08 s 0
    (0, 1704695700.268926, '8c4ca304428a24158b413f6ca703', (-6.28032236, 53.42191664)),  # 4ca304 17 08 s 1
    (0, 1704695721.396960, '8d4ca304ea11a935151c00ae0974',       (NO_COORD, NO_COORD)),  # 4ca304 17 29 n -
    (0, 1704695721.618800, '8d4ca3046003b70548d0de5aec12', (-6.26883114, 53.42129982)),  # 4ca304 17 12 a 1
    (0, 1704695721.994547, '8d4ca30499087e81b00c1f090e4e',       (NO_COORD, NO_COORD)),  # 4ca304 17 19 n -
    (0, 1704695725.278382,               '5d4ca3046296d5',       (NO_COORD, NO_COORD)),  # 4ca304 11 -- n -
    (0, 1704695725.869060, '8d4ca30499088e81f06c1f28efae',       (NO_COORD, NO_COORD)),  # 4ca304 17 19 n -
    (0, 1704695726.426409, '8d4ca3046003d39d2ec835626a24', (-6.26369803, 53.42097473)),  # 4ca304 17 12 a 0
    (0, 1704695726.593740,               '5d4ca3046296d4',       (NO_COORD, NO_COORD)),  # 4ca304 11 -- n -
    (0, 1704695726.797714, '8d4ca30499089081f0981f6919a5',       (NO_COORD, NO_COORD)),  # 4ca304 17 19 n -
    (0, 1704695727.393335, '8d4ca304f80300060048786b2920',       (NO_COORD, NO_COORD)),  # 4ca304 17 31 n -
    (0, 1704695727.843414, '8d4ca3046003f39d2ac8493688b2', (-6.26212856, 53.42088318)),  # 4ca304 17 12 a 0
)
P_STATE_6 = (
    EMPTY_STATE | {'icao': [0x4ca304], 'time': [1704695727.843414], 'position': [(-6.26212856, 53.42088318)], 'valid': [True]},
)

# test: when track position distance check fails, then new track is started
# stream: [a].o.e..e.o..ee..[f]o..o.o..o..o.e.o..o....ooo..e
P_MSG_7 = (
    (0, 1676212322.500000,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212323.707462, '8d4ca4ed5861a6af48fc38424c44',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212324.104649, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212324.254611, '8d4ca4ed5861a345e0f4bf8d3262', (-5.21980286, 52.90942383)),  # 4ca4ed 17 11 a 0
    (0, 1676212324.593688,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212324.594973,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.297388, '8d4ca4ed5861934616f4a174496e', (-5.22209167, 52.91065979)),  # 4ca4ed 17 11 a 0
    (0, 1676212325.620938,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212325.898300, '8d4ca4ed586186afaefc022b21cb', (-5.22305734, 52.91122695)),  # 4ca4ed 17 11 a 1
    (0, 1676212326.333228, '8d4ca4ed990d011d986420804acb',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212326.600000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212326.665183, '8d4ca4ed586173465af47d7a165b', (-5.22483826, 52.91221619)),  # 4ca4ed 17 11 a 0
    (0, 1676212327.212929, '8d4ca4ed5861634672f4709ed8c9', (-5.22583008, 52.91276550)),  # 4ca4ed 17 11 a 0
    (0, 1676212327.100000,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212327.814243, '8d4ca4edf82300060048784c3105',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 31 n -
    # next message fails track distance check, and new track should be
    # started
    (0, 1676212327.817334, '8d4ca4ed586165bfd578531f21ce',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212327.973889, '8d4ca4ed990d001d98681f359b25',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212328.348986,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    # the following message is used to restart the track, so no position
    (0, 1676212328.351835, '8d4ca4ed586156b024fbc321d7af',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 11 a 1
    (0, 1676212328.460821, '8d4ca4ed990d001d986820cb1a05',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212328.855781, '8d4ca4ed586156b040fbb5db84f5', (-5.22909982, 52.91462526)),  # 4ca4ed 17 11 a 1
    (0, 1676212329.396130,               '5d4ca4edb27614',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212330.529941,               '5d4ca4edb27622',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212330.532141, '8d4ca4ed586136b08afb8d6cc9c4', (-5.23223877, 52.91634770)),  # 4ca4ed 17 11 a 1
    (0, 1676212331.200100,               '5d4ca4edb2766a',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212331.467754, '8d4ca4ed990cff1d986c20febda4',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212331.687493, '8d4ca4ed586126b0befb71f6e08b', (-5.23443604, 52.91755806)),  # 4ca4ed 17 11 a 1
    (0, 1676212332.558668, '8d4ca4ede1068000000000bd2140',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 28 n -
    (0, 1676212332.785085, '8d4ca4ed586103477af3e255b751', (-5.23666382, 52.91880798)),  # 4ca4ed 17 11 a 0
    (0, 1676212332.790807, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212333.709801, '8d4ca4ed585ff6b11cfb3f8309e4', (-5.23835972, 52.91974601)),  # 4ca4ed 17 11 a 1
    (0, 1676212333.871370, '8d4ca4ed990cff1d78701f8d3e52',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212334.095896, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212334.206041, '8d4ca4ed585ff6b138fb31f17088', (-5.23945836, 52.92039774)),  # 4ca4ed 17 11 a 1
    (0, 1676212334.306877, '8d4ca4ed990cff1d78701f8d3e52',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212334.577871,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212334.579199,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212334.582105,               '5d4ca4edb2762f',       (NO_COORD, NO_COORD)),  # 4ca4ed 11 -- n -
    (0, 1676212334.856491, '8d4ca4ed585fe6b152fb237bae5a', (-5.24055699, 52.92100292)),  # 4ca4ed 17 11 a 1
    (0, 1676212335.286291, '8d4ca4ed585fe6b166fb182a7e71', (-5.24142020, 52.92146844)),  # 4ca4ed 17 11 a 1
    (0, 1676212335.671210, '8d4ca4ed585fd6b17efb0cc8b5a7', (-5.24236189, 52.92202707)),  # 4ca4ed 17 11 a 1
    (0, 1676212336.758811, '8d4ca4edea1978677b1c086aa538',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 29 n -
    (0, 1676212336.762796, '8d4ca4ed990cff1d7874204b8972',       (NO_COORD, NO_COORD)),  # 4ca4ed 17 19 n -
    (0, 1676212336.866846, '8d4ca4ed585fc34838f37b96d62f', (-5.24452209, 52.92315674)),  # 4ca4ed 17 11 a 0
)
P_STATE_7 = (
    {
        'icao': [0x4ca4ed],
        'time': [1676212336.866846],
        'position': [(-5.24452209, 52.92315674)],
        'valid': [True],
        'prev_position': [],
        'carry_over_time': [1676212327.817334]
    },
)

# test: succession of positions failing validation tests
P_MSG_8 = (
    (0, 1685906090.088710,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906090.089628,               '5f4d212b23d2c3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906090.095008,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906090.308773,               '5f4d212b23d2aa',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906090.310256,               '5f4d212b23d2aa',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906090.573124, '8f4d212b505f66bfa2f35f5f104d',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906091.335280,               '5f4d212b23d2ec',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906091.615340, '8f4d212b505f53569ceb97badead',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906091.773911, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906092.005275, '8f4d212b505f53569ceb97badead',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906092.212293,               '5f4d212b23d2e1',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906092.214153,               '5f4d212b23d2e1',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906092.705086, '8f4d212b505f36c008f32bc69cf6',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906092.863764,               '5f4d212b23d2ec',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906093.194535,               '5f4d212b23d2ec',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906093.195733,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906093.196030,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906093.200553, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906093.201189,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906093.636510, '8f4d212b505f1356feeb61a9c131',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906093.797960, '8f4d212b2020d2b2c39820c87601',       (NO_COORD, NO_COORD)),  # 4d212b 17 04 n -
    (0, 1685906093.799151, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906093.960815,               '5f4d212b23d2ec',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.015470, '8f4d212b505f1356feeb61a9c131',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906094.029383,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.175875,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.179552,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.182280,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.183168,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.338890, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906094.346519,               '5f4d212b23d2aa',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906094.669860, '8f4d212b505df6c068f2f6515482',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906094.784452, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906095.274467, '8f4d212b505df6c068f2f6515482',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906095.608965, '8f4d212b505dd35766eb2b75a964',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906095.818485, '8f4d212b78ef0b80000000ad6a83',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906095.925306,               '5f4d212b23d2e1',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906095.926222,               '5f4d212b23d2e1',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906095.927930,               '5f4d212b23d2e1',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906096.641911, '8f4d212b505dc6c0c8f2c2aec078',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906096.808331, '8f4d212b78ef0b60000000d3b10c',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906097.015899,               '5f4d212b23d2ec',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906097.184199,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906097.184833,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906097.185131,               '5f4d212b23d2a4',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906097.186606, '8f4d212b505dc6c0c8f2c2aec078',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906097.352183, '8f4d212b78ef0b60000000d3b10c',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906097.522004, '8f4d212b505da357c8eaf301d45a',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906097.733665, '8f4d212b78ef0b60000000d3b10c',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906098.068154,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.070166,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.162923,               '5f4d212b23d283',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.167047,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.170359,               '5f4d212b23d2e3',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.173252, '8f4d212b505da357c8eaf301d45a',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906098.178578,               '5f4d212b23d2aa',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.181269,               '5d4d212b74280c',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.182748,               '5d4d212b74280c',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.281439,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906098.663460, '8d4d212b2020d2b2c398207894f1',       (NO_COORD, NO_COORD)),  # 4d212b 17 04 n -
    (0, 1685906098.670321, '8d4d212b78ef0b600000006353fc',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906098.816064, '8d4d212b505d86c130f28b9d0d90',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906099.315811,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906099.596306, '8d4d212b78ef0b600000006353fc',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906099.598121, '8d4d212b505d735840eab0329b3c',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906099.803135,               '5d4d212b742847',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906099.804676,               '5d4d212b742847',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906099.805601,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906100.140253,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906100.785274, '8d4d212b505d56c1a6f2490aa179',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906100.787078, '8d4d212b78eecb600000002e5567',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906100.953682,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906101.064912,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906101.065210,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906101.066390,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906101.071815,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906101.227589, '8d4d212b78eecb600000002e5567',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906101.716664, '8d4d212b505d3358a8ea7abfe3b5',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906102.048967,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.049563,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.052217,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.053147,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.055508,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.057025,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.152404,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.260114,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906102.640182, '8d4d212b505d16c206f21518466a',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906102.913734, '8d4d212b78eecb600000002e5567',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906103.080957,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906103.087521, '8d4d212b505d16c206f21518466a',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906103.249960, '8d4d212b78eecb600000002e5567',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906103.524511,               '5d4d212b742847',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906103.524862,               '5d4d212b742847',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906103.730500, '8d4d212b505d03590aea44704ee9',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906103.730812, '8d4d212b2020d2b2c398207894f1',       (NO_COORD, NO_COORD)),  # 4d212b 17 04 n -
    (0, 1685906103.743568, '8d4d212b78eecb600000002e5567',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906104.775142,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906104.782263, '8d4d212b505be6c266f1e0e8a1b8',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906104.783735, '8d4d212b78eec0000000004c42ad',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906105.006178,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906105.007650,               '5d4d212b742802',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906105.270968, '8d4d212b78eec0000000004c42ad',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906105.273531, '8d4d212b505be6c266f1e0e8a1b8',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 1
    (0, 1685906105.277300,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906105.553524, '8d4d212b505bd3596cea0e26981d',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906105.706132,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906105.708873, '8d4d212b780000000000001ee2fa',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906105.865099,               '5d4d212b74284f',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.033058,               '5d4d212b74284a',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.037235,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.136485,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.137512,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.137812,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.139938,               '5d4d212b74280c',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.140240,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.141207,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.143280,               '5d4d212b74280c',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.143891,               '5d4d212b74280c',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.145432,               '5d4d212b742845',       (NO_COORD, NO_COORD)),  # 4d212b 11 -- n -
    (0, 1685906106.248775, '8d4d212b780000000000001ee2fa',       (NO_COORD, NO_COORD)),  # 4d212b 17 15 a 0
    (0, 1685906106.255485, '8d4d212b505bd3596cea0e26981d',       (NO_COORD, NO_COORD)),  # 4d212b 17 10 a 0
    (0, 1685906106.789711, '8d4d212b505bb6c2ccf1acc307ec', (-5.43069894, 53.02514028)),  # 4d212b 17 10 a 1
    (0, 1685906107.189121, '8d4d212b505bb6c2ccf1acc307ec', (-5.43069894, 53.02514028)),  # 4d212b 17 10 a 1
    (0, 1685906107.731962, '8d4d212b505b9359cee9d846ac4e', (-5.43273926, 53.02619934)),  # 4d212b 17 10 a 0
    (0, 1685906108.275695, '8d4d212b505b9359cee9d846ac4e', (-5.43273926, 53.02619934)),  # 4d212b 17 10 a 0
)
P_STATE_8 = (
    {
        'icao': [0x4d212b],
        'time': [1685906108.275695],
        'position': [(-5.43273926, 53.02619934)],
        'valid': [True],
        'prev_position': [],
        'carry_over_time': [
            1685906090.573124, 1685906091.615340, 1685906091.773911,
            1685906092.005275, 1685906092.705086, 1685906093.200553,
            1685906093.636510, 1685906093.799151, 1685906094.015470,
            1685906094.338890, 1685906094.669860, 1685906094.784452,
            1685906095.274467, 1685906095.608965, 1685906095.818485,
            1685906096.641911, 1685906096.808331, 1685906097.186606,
            1685906097.352183, 1685906097.522004, 1685906097.733665,
            1685906098.173252, 1685906098.670321, 1685906098.816064,
            1685906099.596306, 1685906099.598121, 1685906100.785274,
            1685906100.787078, 1685906101.227589, 1685906101.716664,
            1685906102.640182, 1685906102.913734, 1685906103.087521,
            1685906103.249960, 1685906103.730500, 1685906103.743568,
            1685906104.782263, 1685906104.783735, 1685906105.270968,
            1685906105.273531, 1685906105.708873, 1685906106.248775,
        ]
    },
)

# TODO: NL change unit test required
POSITION_DATA = [
    (P_MSG_0, P_STATE_0),
    (P_MSG_1, P_STATE_1),
    (P_MSG_2, P_STATE_2),
    (P_MSG_3, P_STATE_3),
    (P_MSG_4, P_STATE_4),
    (P_MSG_5, P_STATE_5),
    (P_MSG_6, P_STATE_6),
    (P_MSG_7, P_STATE_7),
    (P_MSG_8, P_STATE_8),
]

# vim: sw=4:et:ai
