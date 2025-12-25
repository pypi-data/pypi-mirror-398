#!/usr/bin/env python3

###################################################################################################
# (C) 2021 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences, Potsdam, Germany  #
#                                                                                                 #
# This file is part of dastools.                                                                  #
#                                                                                                 #
# dastools is free software: you can redistribute it and/or modify it under the terms of the GNU  #
# General Public License as published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                                                 #
#                                                                                                 #
# dastools is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without   #
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU   #
# General Public License for more details.                                                        #
#                                                                                                 #
# You should have received a copy of the GNU General Public License along with this program. If   #
# not, see https://www.gnu.org/licenses/.                                                         #
###################################################################################################

"""Tests to check that dasconv.py is working

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

   :Copyright:
       2019-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""

from datetime import datetime
from obspy.core.trace import Stats
from dastools.app.dasconv import nslc
from dastools.app.dasconv import str2date

"""Test the functionality of dasconv.py

"""


def test_nslc():
    stats = Stats({'network': 'GE',
                   'station': 'STAT1',
                   'location': '',
                   'channel': 'HHZ'})
    assert nslc(stats) == 'GE.STAT1..HHZ'


def test_str2date():
    dt = datetime(2023, 1, 2, 3, 4, 5)
    assert str2date('2023-01-02T03:04:05') == dt
    assert str2date(None) is None
    assert str2date('') is None
