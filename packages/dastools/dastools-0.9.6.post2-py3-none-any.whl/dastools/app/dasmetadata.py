#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""dasmetadata tool

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
       2021-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""

import click
import sys
import json
import requests
from pathlib import Path
from typing import Literal
from pydantic import ValidationError
from jsonschema import validate as validateJSON
from dastools.input import str2class
from dastools.input import checkDASdata
from dastools import __version__
from dastools.utils import str2date
from dastools.utils import printmetadata
from dastools.utils import dasrcn2stationxml
from dastools.utils import dasrcn2datacite
from dastools.utils import kml2channels
from dastools.utils import csv2channels
from dastools.utils import doi2dasrcn
from dastools.utils import stationcode2int
from dastools.basemodels import DASMetadata
from dastools.basemodels import ChannelGroupModel
from dastools.basemodels import merge


dasclasses = ['OptoDAS', 'TDMS', 'Febus', 'OptaSense']


@click.group()
@click.version_option(__version__)
def cli():
    pass


@click.command()
@click.option('--experiment', type=str,
              help='Experiment to read and process. It is usually the first part of the filenames.')
@click.option('--directory', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.',
              help='Directory where files are located (default: ".")')
@click.option('--start', type=str, default=None,
              help='Start of the selected time window.\nFormat: 2019-02-01T00:01:02.123456Z')
@click.option('--end', type=str, default=None,
              help='End of the selected time window.\nFormat: 2019-02-01T00:01:02.123456Z')
@click.option('--inputfmt', type=click.Choice(dasclasses, case_sensitive=False), default=None,
              help='Format of the data files')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='Filename to save the output')
def showraw(experiment: str = None, directory: str = '.', start: str = None, end: str = None,
            chstart: int = None, chstop: int = None, chstep: int = 1,
            inputfmt: Literal['OptoDAS', 'TDMS', 'Febus'] = None, outfile: click.File('wt') = sys.stdout,
            empty: bool = False, quick: bool = True):
    """Show raw metadata from the headers of the raw data"""
    start = str2date(start)
    end = str2date(end)

    if end is not None and start is not None and start >= end:
        click.echo('ERROR: End time is smaller than start time.', err=True)
        sys.exit(-2)

    # If there are no input format try to guess it from the file extension filtering them with the parameters provided
    if inputfmt is None:
        # Check data format from the dataset (if any)
        try:
            clsdas = checkDASdata(experiment, Path(directory))
        except Exception:
            click.echo('ERROR: Data format could not be detected!', err=True)
            sys.exit(-2)
    else:
        clsdas = str2class(inputfmt)

    if isinstance(chstart, int) and isinstance(chstop, int):
        chlist = list(range(chstart, chstop, chstep))
    else:
        chlist = None
    dasobj = clsdas(experiment, directory=directory, starttime=start, endtime=end,
                    channels=chlist, loglevel='WARNING')
    printmetadata(dasobj.metadata, outfile)
    return


# help = 'Input file in JSON format as proposed by the DAS-RCN group.')
@click.command()
@click.option('--infile', type=click.File('rt'), default=sys.stdin,
              help='Input file in JSON format as proposed by the DAS-RCN group.')
@click.option('--gain', type=float, default=1.0,
              help='Gain to be included in the response of the StationXML file')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='File where the stationXML data should be saved')
def json2stationxml(infile: click.File('rt') = sys.stdin, gain: float = 1.0,
                    outfile: click.File('wt') = sys.stdout):
    """Convert JSON metadata to StationXML"""
    try:
        indict = json.load(infile)
    except Exception:
        click.echo('ERROR reading the input file  with JSON metadata', err=True)
        sys.exit(-2)
    o = DASMetadata(**indict)

    # Generate a StationXML file as output
    dasrcn2stationxml(o, gain=gain).write(outfile, encoding='unicode')
    return


# help = 'Input file in JSON format as proposed by the DAS-RCN group.')
@click.command()
@click.option('--infile', type=click.File('rt'), default=sys.stdin,
              help='Input file in JSON format as proposed by the DAS-RCN group.')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='File where the stationXML data should be saved')
def json2datacite(infile: click.File('rt') = sys.stdin, outfile: click.File('wt') = sys.stdout):
    """Convert JSON metadata to Datacite"""
    try:
        indict = json.load(infile)
    except Exception:
        click.echo('ERROR reading the input file with JSON metadata', err=True)
        sys.exit(-2)
    o = DASMetadata(**indict)
    outfile.write(dasrcn2datacite(o))
    return


@click.command()
@click.option('--experiment', type=str,
              help='Experiment to read and process. It is usually the first part of the filenames.')
@click.option('--directory', type=str, default='.',
              help='Directory where files are located (default: ".")')
@click.option('--start', type=str, default=None,
              help='Start of the selected time window.\nFormat: 2019-02-01T00:01:02.123456Z')
@click.option('--end', type=str, default=None,
              help='End of the selected time window.\nFormat: 2019-02-01T00:01:02.123456Z')
@click.option('--inputfmt', type=click.Choice(dasclasses, case_sensitive=False), default=None,
              help='Format of the data files')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='Filename to save the output')
@click.option('--outputfmt', type=click.Choice(['json', 'stationxml'], case_sensitive=True),
              default=None, help='Format of the output')
@click.option('--empty', default=False, is_flag=True,
              help='Create an empty instance of metadata in standard format. If this parameter is present, all other parameters will be ignored.')
def create(experiment: str = None, directory: str = '.', start: str = None, end: str = None,
           chstart: int = None, chstop: int = None, chstep: int = 1,
           inputfmt: Literal['OptoDAS', 'TDMS', 'Febus'] = None, outfile: click.File('wt') = sys.stdout, outputfmt: str = 'json',
           empty: bool = False, quick: bool = True):
    """Create DAS metadata or StationXML for a DAS dataset"""
    if empty:
        outfile.write(json.dumps(DASMetadata().model_dump(mode='json', by_alias=True), indent=2))
        return

    start = str2date(start)
    end = str2date(end)

    if end is not None and start is not None and start >= end:
        click.echo('ERROR: End time is smaller than start time.', err=True)
        sys.exit(-2)

    # If there are no input format try to guess it from the file extension filtering them with the parameters provided
    if inputfmt is None:
        # Check data format from the dataset (if any)
        try:
            clsdas = checkDASdata(experiment, Path(directory))
        except Exception:
            click.echo('ERROR: Data format could not be detected!', err=True)
            sys.exit(-2)
    else:
        clsdas = str2class(inputfmt)

    if isinstance(chstart, int) and isinstance(chstop, int):
        chlist = list(range(chstart, chstop, chstep))
    else:
        chlist = None
    dasobj = clsdas(experiment, directory=directory, starttime=start, endtime=end,
                    channels=chlist, loglevel='WARNING')
    # progress = tqdm(dasobj)

    o = dasobj.dasrcn

    # Output format is stationxml
    if outputfmt == 'stationxml':
        # Generate a StationXML file as output
        dasrcn2stationxml(o).write(outfile, encoding='unicode')
        return

    # Output format is json
    try:
        json.dump(o.model_dump(mode='json', by_alias=True), outfile, indent=2)
        # pprint(json.dumps(o.model_dump(mode='json')), stream=stream)
    except ValidationError as e:
        click.echo('ERROR while creating main metadata', err=True)
        click.echo(e.errors(), err=True)
        sys.exit(-2)


@click.command()
@click.argument('doi', type=str, default=None)
@click.option('--infile', type=click.File('rt'), default=sys.stdin,
              help='Input file in JSON format as proposed by the DAS-RCN group.')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='File where the modified JSON metadata should be saved')
def add_datacite(doi: str, infile: click.File('rt') = sys.stdin,
                 outfile: click.File('wt') = sys.stdout):
    """Complete the DAS metadata with information from Datacite metadata via a DOI"""
    try:
        indict = json.load(infile)
    except Exception:
        click.echo('ERROR reading the input file  with JSON metadata', err=True)
        sys.exit(-2)
    o = DASMetadata(**indict)
    # numchans = o.interrogators[0].acquisitions[0].number_of_channels
    # Integrate channels if it was requested
    if doi is None:
        click.echo("ERROR: No DOI has been provided!", err=True)
        sys.exit(-2)

    # Read DOI and create an instance of DASMetadata
    try:
        doidata = doi2dasrcn(doi)
        # print(doidata)
    except ValidationError as e:
        click.echo('ERROR while retrieving DOI', err=True)
        click.echo(e.errors(), err=True)
        sys.exit(-2)
    except Exception as e:
        click.echo('ERROR reading DOI', err=True)
        click.echo(str(e), err=True)
        sys.exit(-2)
    result = merge(o, doidata)
    json.dump(result.model_dump(mode='json', by_alias=True), outfile, indent=2)


@click.command()
@click.argument('coords', type=str, default=None)
@click.option('--infile', type=click.File('rt'), default=sys.stdin,
              help='Input file in JSON format as proposed by the DAS-RCN group.')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='File where the modified JSON metadata should be saved')
def add_coords(coords: str = None, infile: click.File('rt') = sys.stdin,
               outfile: click.File('wt') = sys.stdout):
    """Complete coordinates in the DAS metadata from a CSV or KML file

    The expected structure of the CSV file is the following:
    1) channelID as expected in the output metadata (e.g. A1234, B4321). No more than 5 characters.
    2) latitude as a float
    3) longitude as a float
    4) elevation in meters as a float (optional)
    5) distance along fiber in meters as a float (optional)
"""
    try:
        indict = json.load(infile)
    except Exception:
        click.echo('ERROR reading the input file with JSON metadata', err=True)
        sys.exit(-2)
    o = DASMetadata(**indict)
    # numchans = o.interrogators[0].acquisitions[0].number_of_channels
    # Integrate channels if it was requested
    if coords is None:
        click.echo("ERROR: No coordinates have been provided!", err=True)
        sys.exit(-2)
    # Read and create a Channel Group instance
    try:
        # Read coordinates from a KML file
        if coords.endswith('.kml'):
            newchannels = kml2channels(coords)
            # Create a list of channels from a KML file
            chgrp = ChannelGroupModel(cable_id=o.cables[0].cable_id,
                                      fiber_id=o.cables[0].fibers[0].fiber_id,
                                      channels=newchannels)
        # Read coordinates from a CSV file
        elif coords.endswith('.csv'):
            newchannels = csv2channels(coords)
            # Create a list of channels from a CSV file
            chgrp = ChannelGroupModel(cable_id=o.cables[0].cable_id,
                                      fiber_id=o.cables[0].fibers[0].fiber_id,
                                      channels=newchannels)
        else:
            click.echo('ERROR: Unrecognized file format. Only "kml" or "csv" files are accepted.', err=True)
            sys.exit(-2)

        # Print a warning if the number of channels read are not exactly the same as the ones present in the data
        if len(chgrp.channels) != o.interrogators[0].acquisitions[0].number_of_channels:
            click.echo('Warning: %d channels processed, but there should be %d' % (len(chgrp.channels),
                                                                                   o.interrogators[0].acquisitions[0].number_of_channels),
                       err=True)

        # If there is no information in the metadata, create a list and include everything as it is
        if not len(o.interrogators[0].acquisitions[0].channel_groups):
            o.interrogators[0].acquisitions[0].channel_groups = [chgrp]
        # But if there is data, just update the coordinates and elevation
        else:
            cg = o.interrogators[0].acquisitions[0].channel_groups[0]
            # Order the list of Channels to do a faster update
            cg.channels.sort(key=lambda chan: chan.channel_id)
            newchannels.sort(key=lambda chan: chan.channel_id)

            oldidx = 0
            newidx = 0
            # Loop through channels and update with the closest(!) ID. This means that if there are missing
            # coordinates we will fill that with the previous or the next one
            while oldidx < len(cg.channels):
                if (cg.channels[oldidx].channel_id <= newchannels[newidx].channel_id) or (newidx == len(newchannels)-1):
                    cg.channels[oldidx].x_coordinate = newchannels[newidx].x_coordinate
                    cg.channels[oldidx].y_coordinate = newchannels[newidx].y_coordinate
                    cg.channels[oldidx].elevation_above_sea_level = newchannels[newidx].elevation_above_sea_level
                    oldidx = oldidx+1
                else:
                    newidx = newidx+1

    except ValidationError as e:
        click.echo('ERROR while creating a ChannelGroup!', err=True)
        click.echo(e.errors(), err=True)
        sys.exit(-2)
    json.dump(o.model_dump(mode='json', by_alias=True), outfile, indent=2)


# help = 'Input file in JSON format as proposed by the DAS-RCN group.')
@click.command()
@click.option('--infile', type=click.File('rt'), default=sys.stdin,
              help='Input file in JSON format as proposed by the DAS-RCN group.')
@click.option('--outfile', type=click.File('wt'), default=sys.stdout,
              help='Output file with attributes removed in case of a NULL value')
def remove_nulls(infile: click.File('rt') = sys.stdin, outfile: click.File('wt') = sys.stdout):
    """Remove attributes with NULL value"""
    try:
        indict = json.load(infile)
    except Exception:
        click.echo('ERROR reading the input file with JSON metadata', err=True)
        sys.exit(-2)
    o = DASMetadata(**indict)
    json.dump(o.model_dump(mode='json', by_alias=True, exclude_none=True), outfile, indent=2)
    return


# help = 'Input file in JSON format as proposed by the DAS-RCN group.')
@click.command()
@click.argument('jsonfile', type=click.File('rt'), default=sys.stdin)
def validate(jsonfile: click.File('rt') = sys.stdin):
    """Validate JSON metadata"""
    try:
        indict = json.load(jsonfile)
    except Exception:
        click.echo('ERROR reading the input file with JSON metadata', err=True)
        sys.exit(-2)

    try:
        o = DASMetadata(**indict)
    except Exception as e:
        click.echo(str(e), err=True)

    click.echo('Checking JSON schema...')
    # Get the latest version of the DAS metadata schema
    schema = requests.get('https://raw.githubusercontent.com/FDSN/DAS-metadata/refs/heads/main/schema/DAS-Metadata.v2.0.schema.json')
    try:
        validateJSON(instance=indict, schema=json.loads(schema.text))
        # click.echo('Metadata is valid!')
    except Exception as e:
        click.echo('\n'.join(str(e).splitlines()[:20]), err=True)

    # Check channel IDs
    click.echo('Checking channel names...')
    for i in o.interrogators:
        for a in i.acquisitions:
            for cg in a.channel_groups:
                for c in cg.channels:
                    try:
                        stationcode2int(c.channel_id)
                    except Exception:
                        click.echo("Warning! I don't know how to interpret %s" % (c.channel_id,), err=True)

    # Check unicity of IDs
    click.echo('Checking references...')
    cabfib = set()
    for cab in o.cables:
        for fib in cab.fibers:
            cabfib.add((cab.cable_id, fib.fiber_id))

    for i in o.interrogators:
        for a in i.acquisitions:
            for cg in a.channel_groups:
                if (cg.cable_id, cg.fiber_id) not in cabfib:
                    click.echo('Reference to cable %s and fiber %s is wrong!' % (cg.cable_id, cg.fiber_id), err=True)

    return


cli.add_command(create)
cli.add_command(showraw)
cli.add_command(add_coords)
cli.add_command(add_datacite)
cli.add_command(json2stationxml)
cli.add_command(json2datacite)
cli.add_command(remove_nulls)
cli.add_command(validate)

# msg = 'Read and convert metadata from different DAS formats to standard representations.'
# parser = argparse.ArgumentParser(description=msg)
# parser.add_argument('-V', '--version', action='version', version='dasmetadata v%s' % __version__)
# parser.add_argument('-l', '--loglevel', help='Verbosity in the output.', default='INFO',
#                     choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'])

if __name__ == '__main__':
    cli()
