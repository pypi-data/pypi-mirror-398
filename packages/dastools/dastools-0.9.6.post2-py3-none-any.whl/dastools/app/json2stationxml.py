#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""json2stationxml tool

This file is part of dastools.

dastools is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

dastools is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If
not, see https://www.gnu.org/licenses/.

   :Copyright:
       2021 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz-potsdam.de>, GEOFON, GFZ Potsdam
"""

import argparse
import json
import sys
import logging
from dastools import __version__
from dastools.core import DASMetadata
from dastools.core import ChannelGroupModel
from dastools.utils import kml2channels
from dastools.utils import dasrcn2stationxml
from pydantic import ValidationError


def main():
    # Check verbosity in the output
    msg = 'Read and convert metadata from DAS-RCN to StationXML.'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-l', '--loglevel', help='Verbosity in the output.', default='INFO',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'])
    parser.add_argument('--coords', help='KML file with coordinates for each channel', type=str,
                        default=None)
    parser.add_argument('--gain', type=float, default=1.0,
                        help='Gain to be included in the response of the StationXML file')
    parser.add_argument('-V', '--version', action='version', version='json2stationxml v%s' % __version__)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input file in json format as proposed by the DAS-RCN group.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='File where the stationXML data should be saved')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel, stream=sys.stdout)
    logs = logging.getLogger('json2stationxml')
    logs.setLevel(args.loglevel)

    indict = json.load(args.infile)
    o = DASMetadata(**indict)

    numchans = o.Overview.Interrogator[0].Acquisition[0].number_of_channels

    # Integrate channels if it was requested
    if args.coords is not None:
        # Read and create a Channel Group instance
        try:
            # Create a list of channels from a KML file
            chgrp = ChannelGroupModel(cable_id=o.Overview.Cable[0].cable_id,
                                      fiber_id=o.Overview.Cable[0].Fiber[0].fiber_id,
                                      Channel=kml2channels(args.coords))
            o.Overview.Interrogator[0].Acquisition[0].Channel_Group.append(chgrp)
        except ValidationError as e:
            logs.error('Error while creating a ChannelGroup')
            print(e.errors())
            sys.exit(-2)
    # Generate a StationXML file as output
    dasrcn2stationxml(o, gain=args.gain).write(args.outfile, encoding='unicode')


if __name__ == '__main__':
    main()
