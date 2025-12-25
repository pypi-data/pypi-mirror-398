#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""
Dastools FDSN web services

``dasws`` is the FDSN Station-WS and Dataselect web service on top of DAS data

You need to run this application from the console or configure it to be run automatically at start-up.

   :Platform:
       Linux
   :Copyright:
       2019-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GNU General Public License v3

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""

##################################################################
#
# First all the imports
#
##################################################################


import uvicorn
import logging
import argparse
import os
import configparser
from dastools.basemodels import NetworkStationWS
from dastools.basemodels import StationStationWS
from dastools.basemodels import ChannelStationWS
from dastools.utils import str2date
from dastools.utils import int2stationcode
from dastools.server import __version__
from dastools.input.das import Das
from dastools.input.tdms import TDMSReader
from dastools.input.optodas import OptoDASReader
from fastapi import FastAPI
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import StreamingResponse
from fastapi import status
from obspy.core import Trace
from io import BytesIO
from math import floor
from fnmatch import fnmatch


class XMLResponse(Response):
    media_type = "application/xml"

    def render(self, content) -> bytes:
        return super().render(content)
        # return dumps({'response': content}).encode("utf-8")


class ConfigWS(object):
    """Class reading the configuration of DasWS. It is based in the pythonic implementation
    of the Singleton design pattern."""
    config = None

    def __new__(cls):
        if cls.config is None:
            cfgfile = 'dasws.cfg'

            # Open configuration file
            config = configparser.RawConfigParser()
            # here = os.path.dirname(__file__)
            # config.read(os.path.join(here, cfgfile))
            config.read(cfgfile)

            cls.config = dict()
            # Read connection parameters
            cls.config['experiment'] = config.get('General', 'experiment')
            cls.config['directory'] = config.get('General', 'directory')
            cls.config['format'] = config.get('General', 'format', fallback='TDMS')
            cls.config['loglevel'] = config.get('General', 'loglevel', fallback='INFO')

            cls.config['net'] = config.get('NSLC', 'net', fallback='XX')
            cls.config['loc'] = config.get('NSLC', 'loc', fallback='')
            cls.config['cha'] = config.get('NSLC', 'cha', fallback='HSF')

            cls.config['sitename'] = config.get('General', 'sitename', fallback='Unknown sitename')

            logging.info('Configuration read: %s' % ConfigWS)

            # Reading experiment
            if cls.config['format'] == 'TDMS':
                dascls = TDMSReader
            elif cls.config['format'] == 'OptoDAS':
                dascls = OptoDASReader
            else:
                raise Exception('Format %s not recognized!' % cls.config['format'])

            cls.config['data'] = dascls(cls.config['experiment'], cls.config['directory'],
                                        networkcode=cls.config['net'], channelcode=cls.config['cha'],
                                        loglevel=cls.config['loglevel'])
            # Create list with the line for the level=network
            cls.config['network'] = list()
            cls.config['network'].append(NetworkStationWS(net=cls.config['net'], sitename=cls.config['sitename'],
                                                          start=cls.config['data'].starttime,
                                                          end=cls.config['data'].endexperiment,
                                                          numstations=cls.config['data'].numchannels))

            # Create list with the lines for the level=station
            cls.config['station'] = list()
            for c in cls.config['data'].channels:
                # First character must be a letter. Default: 'A'
                # If there are more than 10000 channels the letter will be changed to 'B' and so on
                stc = int2stationcode(c)
                cls.config['station'].append(StationStationWS(net=cls.config['net'], sta=stc,
                                                              lat=0.0, lon=0.0, elev=0.0,
                                                              sitename=cls.config['sitename'],
                                                              start=cls.config['data'].starttime,
                                                              end=cls.config['data'].endexperiment))

            # Create list with the lines for the level=channel
            cls.config['channel'] = list()
            for c in cls.config['data'].channels:
                # First character must be a letter. Default: 'A'
                # If there are more than 10000 channels the letter will be changed to 'B' and so on
                stc = int2stationcode(c)
                cls.config['channel'].append(ChannelStationWS(net=cls.config['net'], sta=stc,
                                                              loc=cls.config['loc'], cha=cls.config['cha'],
                                                              lat=0, lon=0, elev=0, depth=0, azimuth=0, dip=0,
                                                              sensor='', scale=0, scalefreq=0, scaleunits='',
                                                              samplerate=cls.config['data'].sampling_rate,
                                                              start=cls.config['data'].starttime,
                                                              end=cls.config['data'].endexperiment))
            # Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|SensorDescription|Scale|ScaleFreq|ScaleUnits|SampleRate|StartTime|EndTime
            # print('ConfigWS', cls.config)
        return cls.config


def errormessage(code, text) -> str:
    template = """Error {0}: {1}

{1}

Usage details are available from <SERVICE DOCUMENTATION URI>

Request:
<SUBMITTED URL>

Request Submitted:
<UTC DATE TIME>

Service version:
<3-LEVEL VERSION>
"""
    return template.format(code, text)


approot = FastAPI()
stationws = FastAPI()
dataselect = FastAPI()
approot.mount("/fdsnws/station/1", stationws)
approot.mount("/fdsnws/dataselect/1", dataselect)


@stationws.get("/", response_class=HTMLResponse)
async def stationroot():
    htmlpage = """<body><h1>DAS FDSN web services</h1>Check the
    <a href="https://www.fdsn.org/webservices/fdsnws-station-1.1.pdf">Station-WS</a> specification
     if you don\'t know this service.</body>."""
    return htmlpage


@dataselect.get("/", response_class=HTMLResponse)
async def dsroot():
    htmlpage = """<body><h1>DAS FDSN web services</h1>Check the
    <a href="https://www.fdsn.org/webservices/fdsnws-dataselect-1.1.pdf">Dataselect</a> specifications
     if you don\'t know this service.</body>."""
    return htmlpage


@dataselect.get("/version", response_class=PlainTextResponse)
async def dsversion():
    """Return the version of the Dataselect web service

    :returns: Version of the system
    :rtype: string
    """
    return __version__


@stationws.get("/version", response_class=PlainTextResponse)
async def stversion():
    """Return the version of the Station web service

    :returns: Version of the system
    :rtype: string
    """
    return __version__


@dataselect.get("/application.wadl", response_class=XMLResponse)
async def dsapplicationwadl():
    project_dir = os.path.dirname(__file__)
    try:
        with open(os.path.join(project_dir, '../data/dataselect.wadl')) as fin:
            text = fin.read()
            return XMLResponse(content=text)
    except FileNotFoundError:
        pass
    # Send Error 400
    message = 'application.wadl not found!'
    # messdict = {'code': 0, 'message': message}
    return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))


@stationws.get("/application.wadl", response_class=XMLResponse)
async def stapplicationwadl():
    project_dir = os.path.dirname(__file__)
    try:
        with open(os.path.join(project_dir, '../data/station.wadl')) as fin:
            text = fin.read()
            return XMLResponse(content=text)
    except FileNotFoundError:
        pass
    # Send Error 400
    message = 'application.wadl not found!'
    # messdict = {'code': 0, 'message': message}
    return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))


@stationws.get("/query", response_class=PlainTextResponse)
async def stquery(network: str = '*', net: str = '*', station: str = '*', sta: str = '*', location: str = '*',
                  loc: str = '*', channel: str = '*', cha: str = '*', starttime: str = None, start: str = None,
                  endtime: str = None, end: str = None, minlatitude: float = -90.0, minlat: float = -90.0,
                  maxlatitude: float = 90.0, maxlat: float = 90.0, minlongitude: float = -180.0,
                  minlon: float = -180.0, maxlongitude: float = 180.0, maxlon: float = 180.0, format: str = 'xml',
                  level: str = 'station'):
    """Get metadata in text format (xml not implemented)

    :param network: Usually the network code configured in the cfg file. It is included just to satisfy the standard
    :type network: str
    :param net: Alias of network
    :type net: str
    :param station: Comma-separated integers identifying of streams to retrieve
    :type station: str
    :param sta: Alias of station
    :type sta: str
    :param location: Usually the location code configured in the cfg file. Included just to satisfy the standard
    :type location: str
    :param loc: Alias of location
    :type loc: str
    :param channel: Usually the channel code configured in the cfg file. It is included just to satisfy the standard
    :type channel: str
    :param cha: Alias of channel
    :type cha: str
    :param starttime: Start time of the time window to access
    :type starttime: str
    :param start: Alias of starttime
    :type start: str
    :param endtime: End time of the time window to access
    :type endtime: str
    :param end: Alias of endtime
    :type end: str
    :param format: Format of result, either xml or text. Default value is xml (StationXML)
    :type format: str
    :returns: miniSEED data
    :rtype: bytearray
    :raises: cherrypy.HTTPError
    """

    cfgparams = ConfigWS()
    # Format
    # Only text format is currently implemented
    if format != 'text':
        # Send Error 400
        message = 'Only format=text is currently supported'
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    # Unify both names for the NSLC parameters
    auxnet = network if net == '*' else net
    auxsta = station if sta == '*' else sta
    auxloc = location if loc == '*' else loc
    auxcha = channel if cha == '*' else cha

    # Network
    if auxnet not in ('*', cfgparams['net']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")
    # Location
    if auxloc not in ('*', cfgparams['loc']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")
    # Channel
    if auxcha not in ('*', cfgparams['cha']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")

    if level == 'response':
        # Send Error 400
        message = 'Response level not valid in text format'
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    # Starttime and start: Discard the most comprehensive case of None and keep the most restricted one
    starttime = starttime if start is None else start

    # Endtime and end: Discard the most comprehensive case of None and keep the most restricted one
    endtime = endtime if end is None else end

    # Station(s)
    try:
        liststa = ['*'] if auxsta == '*' else auxsta.split(',')
    except Exception:
        # Send Error 400
        message = 'Wrong formatted list of stations (%s).' % sta
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    try:
        startdt = str2date(starttime) if starttime is not None else None
    except Exception:
        # Send Error 400
        message = 'Error converting the "starttime" parameter (%s).' % starttime
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    try:
        enddt = str2date(endtime) if endtime is not None else None
    except Exception:
        # Send Error 400
        message = 'Error converting the "endtime" parameter (%s).' % endtime
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    if level == 'network':
        result = '# Network|Description|StartTime|EndTime|TotalStations\n'
    elif level == 'station':
        result = '# Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime\n'
    elif level == 'channel':
        result = '# Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|SensorDescription|Scale|ScaleFreq|ScaleUnits|SampleRate|StartTime|EndTime\n'
    else:
        message = 'Only levels "network", or "station", or "channel" is supported'
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errormessage(400, message))

    # Print the output lines based on the tuples in the selected level (network: 5 components; station: 8, etc)
    nodata = True
    for s in cfgparams[level]:
        if level != 'network':
            for sta in liststa:
                if not fnmatch(s.sta, sta):
                    continue
                else:
                    break
            else:
                continue
        result += '%s\n' % (s,)
        nodata = False

    # If no stations pass the filters then send 204
    if nodata:
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")
    return result


def trace2mseed(t: Das):
    """Iterator that takes a Das object and returns chunks of the same data, but in miniseed format"""
    with t:
        for data in t:
            # Create the Trace
            tr0 = Trace(data=data[0], header=data[1])
            auxout = BytesIO()
            tr0.write(auxout, format='MSEED', reclen=512)
            yield auxout.getvalue()
            auxout.close()


@dataselect.get("/query", response_class=StreamingResponse)
def dsquery(net: str = '*', sta: str = '*', loc: str = '*', cha: str = '*',
            network: str = '*', station: str = '*', location: str = '*', channel: str = '*',
            start: str = None, starttime: str = None,
            end: str = None, endtime: str = None):
    """Get data in miniSEED format.

    :param network: Usually the network code configured in the cfg file. It is included just to satisfy the standard
    :type network: str
    :param net: Alias of network
    :type net: str
    :param station: Comma-separated integers identifying of streams to retrieve
    :type station: str
    :param sta: Alias of station
    :type sta: str
    :param location: Usually the location code configured in the cfg file. Included just to satisfy the standard
    :type location: str
    :param loc: Alias of location
    :type loc: str
    :param channel: Usually the channel code configured in the cfg file. It is included just to satisfy the standard
    :type channel: str
    :param cha: Alias of channel
    :type cha: str
    :param starttime: Start time of the time window to access
    :type starttime: str
    :param start: Alias of starttime
    :type start: str
    :param endtime: End time of the time window to access
    :type endtime: str
    :param end: Alias of endtime
    :type end: str
    :returns: miniSEED data
    :rtype: bytearray
    """
    cfgparams = ConfigWS()

    # Unify both names for the NSLC parameters
    auxnet = network if net == '*' else net
    auxsta = station if sta == '*' else sta
    auxloc = location if loc == '*' else loc
    auxcha = channel if cha == '*' else cha

    # Network
    if auxnet not in ('*', cfgparams['net']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")
    # Location
    if auxloc not in ('*', cfgparams['loc']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")
    # Channel
    if auxcha not in ('*', cfgparams['cha']):
        return PlainTextResponse(status_code=status.HTTP_204_NO_CONTENT, content="")

    # Starttime and start: Discard the most comprehensive case of None and keep the most restricted one
    starttime = starttime if start is None else start

    # Endtime and end: Discard the most comprehensive case of None and keep the most restricted one
    endtime = endtime if end is None else end

    if starttime is not None:
        try:
            startdt = str2date(starttime)
        except Exception:
            # Send Error 400
            message = 'Error converting the "starttime" parameter (%s).' % starttime
            return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=message)
    else:
        startdt = None

    if endtime is not None:
        try:
            enddt = str2date(endtime)
        except Exception:
            # Send Error 400
            message = 'Error converting the "endtime" parameter (%s).' % endtime
            return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=message)
    else:
        enddt = None

    # Reading experiment
    if cfgparams['format'].lower() == 'tdms':
        dascls = TDMSReader
    elif cfgparams['format'].lower() == 'optodas':
        dascls = OptoDASReader
    else:
        # Send Error 400
        message = 'Format "%s" not recognized! Supported formats are: "optodas" and "tdms".' % (cfgparams['format'],)
        return PlainTextResponse(status_code=status.HTTP_400_BAD_REQUEST, content=message)

    try:
        liststa = [x for x in map(int, sta.split(','))]
    except Exception:
        liststa = cfgparams['data'].channels

    # print(liststa)
    t = dascls(experiment=cfgparams['experiment'], directory=cfgparams['directory'], channels=liststa,
               starttime=startdt, endtime=enddt)

    return StreamingResponse(trace2mseed(t), media_type='application/vnd.fdsn.mseed')


def main():
    """Run the dasws service implementing a FDSN web services on top of DAS files"""

    desc = 'dasws offers FDSN web services (i.e. StationWS, Dataselect) reading directly from DAS raw files'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-mc', '--minimalconfig', action='store_true', default=False,
                        help='Generate a minimal configuration file.')
    parser.add_argument('-l', '--log', default='WARNING', choices=['DEBUG', 'WARNING', 'INFO', 'DEBUG'],
                        help='Increase the verbosity level.')
    args = parser.parse_args()

    # Read configuration
    config = configparser.RawConfigParser()

    if args.minimalconfig:
        # Create default sections and options for the configfile
        config['General'] = {'experiment': 'experiment', 'directory': '.', 'format': 'TDMS',
                             'loglevel': 'INFO', 'sitename': 'Site description for StationWS'}
        config['NSLC'] = {'net': 'XX', 'loc': '', 'cha': 'HSF'}
        # Write to dasws.cfg
        with open('dasws.cfg', 'w') as configfile:
            config.write(configfile)
        return

    # Open the configuration file in the current directory
    config.read('dasws.cfg')
    loglevel = config.get('General', 'loglevel', fallback='INFO')
    logging.basicConfig(level=loglevel)
    uvicorn.run("dastools.server.dasws:approot", host='0.0.0.0', port=8080, log_level=loglevel.lower())


if __name__ == "__main__":
    main()
