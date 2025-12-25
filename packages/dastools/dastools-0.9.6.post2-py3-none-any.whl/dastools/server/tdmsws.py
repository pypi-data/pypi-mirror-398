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

"""tdmsws WS - prototype

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


import cherrypy
import argparse
from cherrypy.process import plugins
import os
from datetime import datetime
import configparser
from dastools.input.tdms import TDMS
from dastools.utils import str2date
from obspy import Trace
from io import BytesIO


def errormessage(code, text):
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


class TdmswsAPI(object):
    """Main class including the dispatcher."""

    def __init__(self, experiment, directory='.'):
        """Constructor of the TdmswsAPI object."""
        # Save parameters
        self.__experiment = experiment
        self.__directory = directory

        # Get extra fields from the cfg file
        cfgfile = configparser.RawConfigParser()
        cfgfile.read(os.path.join(directory, 'tdsmws.cfg'))
        self.__net = cfgfile.get('NSLC', 'network', fallback='XX')
        self.__cha = cfgfile.get('NSLC', 'channel', fallback='FH1')

        # Special case for the empty location. Change '' for '--'
        self.__loc = cfgfile.get('NSLC', 'location', fallback='--')
        if self.__loc == '':
            self.__loc = '--'

        self.dataselect = DataselectAPI(experiment, directory)
        self.station = StationAPI(experiment, directory)

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/html'

        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp = fin.read()
        except FileNotFoundError:
            texthelp = """<html>
                            <head>tdmsws</head>
                            <body>
                              Default help for the tdmsws service (GEOFON).
                            </body>
                          </html>"""

        return texthelp.encode('utf-8')


@cherrypy.expose
@cherrypy.popargs('wsversion')
class StationAPI(object):
    """Object dispatching methods related to access to streams."""

    def __init__(self, experiment, directory='.'):
        """Constructor of the StationAPI class."""
        # Save parameters
        self.__experiment = experiment
        self.__directory = directory

        # Get extra fields from the cfg file
        cfgfile = configparser.RawConfigParser()
        cfgfile.read(os.path.join(directory, 'tdsmws.cfg'))
        self.__net = cfgfile.get('NSLC', 'network', fallback='XX')
        self.__cha = cfgfile.get('NSLC', 'channel', fallback='FH1')

        # Special case for the empty location. Change '' for '--'
        self.__loc = cfgfile.get('NSLC', 'location', fallback='--')
        if self.__loc == '':
            self.__loc = '--'

        self.__sitename = cfgfile.get('General', 'siteName', fallback='Unknown sitename')

    @cherrypy.expose
    def index(self, wsversion='1'):
        if wsversion != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        cherrypy.response.headers['Content-Type'] = 'text/html'
        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp = fin.read()
        except FileNotFoundError:
            texthelp = """<html>
                            <head>tdsmws - Station</head>
                            <body>
                              Default help for the Station web service (GEOFON).
                            </body>
                          </html>"""

        return texthelp.encode('utf-8')

    @cherrypy.expose
    def default(self, *args, **kwargs):
        """Use default method to process application.wadl because the dot is not supported in method names"""
        cherrypy.log('default method: %s %s' % (args, kwargs))
        if args[0] != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        if args[1] != 'application.wadl':
            # Send Error 400
            message = 'Unknown method "%s"' % args[1]
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        project_dir = os.path.dirname(__file__)

        try:
            with open(os.path.join(project_dir, '../data/station.wadl')) as fin:
                text = fin.read()
                cherrypy.response.headers['Content-Type'] = 'application/xml'
                return text.encode('utf-8')
        except FileNotFoundError:
            pass

        # Send Error 400
        message = 'application.wadl not found!'
        # self.__log.error(message)
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        raise cherrypy.HTTPError(400,  errormessage(400, message))

    @cherrypy.expose
    def version(self, wsversion='1'):
        """Return the version of this implementation.

        :returns: Version of the system
        :rtype: string
        """
        if wsversion != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        stationwsversion = '1.1.0'
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return stationwsversion.encode('utf-8')

    @cherrypy.expose
    def query(self, network='*', net='*', station='*', sta='*', location='*', loc='*', channel='*', cha='*',
              starttime=None, start=None, endtime=None, end=None, minlatitude=-90.0, minlat=-90.0, maxlatitude=90.0,
              maxlat=90.0, minlongitude=-180.0, minlon=-180.0, maxlongitude=180.0, maxlon=180.0, format='xml',
              level='station', wsversion='1', **kwargs):
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
        :param format: Format of result, either xml or text. Default value is xml (StationXML)
        :type format: str
        :returns: miniSEED data
        :rtype: bytearray
        :raises: cherrypy.HTTPError
        """

        """Constructor of the StationAPI class."""
        # Check parameters
        # WS version
        if wsversion != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        # Format
        # Only text format is currently implemented
        if format != 'text':
            # Send Error 400
            message = 'Only format=text is currently supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400,  errormessage(400, message))

        # Network
        if network not in ('*', self.__net) or net not in ('*', self.__net):
            cherrypy.response.status = 204
            return

        # Location
        if location not in ('*', self.__loc) or loc not in ('*', self.__loc):
            cherrypy.response.status = 204
            return

        # Channel
        if channel not in ('*', self.__cha) or cha not in ('*', self.__cha):
            cherrypy.response.status = 204
            return

        # Station and sta
        # Discard the most comprehensive case of '*' and keep the most restricted one
        auxsta = station if sta == '*' else sta

        # Starttime and start
        # Discard the most comprehensive case of None and keep the most restricted one
        starttime = starttime if start is None else start

        # Endtime and end
        # Discard the most comprehensive case of None and keep the most restricted one
        endtime = endtime if end is None else end

        # Station(s)
        try:
            liststa = [] if auxsta == '*' else [int(x) for x in auxsta.split(',')]
        except Exception:
            # Send Error 400
            message = 'Wrong formatted list of stations (%s).' % sta
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400,  errormessage(400, message))

        if starttime is not None:
            try:
                startdt = str2date(starttime)
            except Exception:
                # Send Error 400
                message = 'Error converting the "starttime" parameter (%s).' % starttime
                # self.__log.error(message)
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                raise cherrypy.HTTPError(400, errormessage(400, message))
        else:
            startdt = None

        if endtime is not None:
            try:
                enddt = str2date(endtime)
            except Exception:
                # Send Error 400
                message = 'Error converting the "endtime" parameter (%s).' % endtime
                # self.__log.error(message)
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                raise cherrypy.HTTPError(400, errormessage(400, message))
        else:
            enddt = None

        if level == 'response':
            # Send Error 400
            message = 'Response level not valid in text format'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return self.__generatemetadata(liststa, startdt, enddt, level)

    def __generatemetadata(self, streams, starttime=None, endtime=None, level='station'):
        """Generator to extract metadata based on the selection

        :param streams: List of streams (integers) to be extracted
        :type streams: list
        :param starttime: Start time of the time window to access
        :type starttime: datetime
        :param endtime: End time of the time window to access
        :type endtime: datetime
        :param level: Level of metadata ('network', 'station', 'channel', 'response')
        :type level: str
        :returns: miniSEED data
        :rtype: bytearray
        """

        # Check parameters
        if level not in ('network', 'station', 'channel', 'response'):
            raise Exception('Level parameter invalid (%s)' % level)

        # TODO Misspelling which could possibly be fixed in the future
        latkey = 'SystemInfomation.GPS.Latitude'
        lonkey = 'SystemInfomation.GPS.Longitude'
        elevkey = 'SystemInfomation.GPS.Altitude'
        srkey = 'SamplingFrequency[Hz]'

        if level == 'network':
            t = TDMS(self.__experiment, directory=self.__directory, starttime=starttime, endtime=endtime, iterate='M')
            with t:
                # t.readMetadata()
                yield '# Network|Description|StartTime|EndTime|TotalStations\n'
                text = '%s|Description|%s|%s|%s\n' % (self.__net, t.starttime.isoformat(), t.endtime.isoformat(),
                                                      t.numchannels)
                yield text
            return

        if level == 'response':
            raise Exception('Response level not implemented!')

        # Level station and channel
        if level == 'station':
            yield '# Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime\n'
        else:
            yield '# Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|Sensor ' \
                'Description|Scale|ScaleFrequency|ScaleUnits|SampleRate|StartTime|EndTime\n'

        # List of channels or None (all channels)
        channels = streams if len(streams) else None

        # Cycle through files, not channels, and merge epochs in a dictionary
        t = TDMS(self.__experiment, directory=self.__directory, starttime=starttime, endtime=endtime, iterate='M',
                 channels=channels)
        result = dict()
        with t:
            lat = None
            lon = None
            elev = None
            samprate = None
            for data in t:
                if lat is None:
                    lat = data[latkey]
                if lon is None:
                    lon = data[lonkey]
                if elev is None:
                    elev = data[elevkey]
                if samprate is None:
                    samprate = data[srkey]

                if data['data']:

                    stt = data['starttime']
                    ent = data['endtime']
                    if level == 'station':
                        key = '%s|%s|%s|%s|%s|%s' % (self.__net, data['id'], lat, lon, elev, self.__sitename)
                    else:
                        key = '%s|%s|%s|%s|%s|%s|%s|depth|azimuth|dip|DAS|Scale|ScaleFrequency|ScaleUnits|%s' % \
                              (self.__net, data['id'], self.__loc if self.__loc != '--' else '', self.__cha,
                               lat, lon, elev, samprate)

                    if key in result:
                        # Get the minimum starttime
                        stt = stt if stt < result[key][0] else result[key][0]
                        # Get the maximum endtime
                        ent = ent if ent > result[key][1] else result[key][1]

                    result[key] = (stt, ent)

        # Send the epoch(s)
        for key in result:
            # Key is in the proper format for station or channel level. We only need to add the start and end time
            text = '%s|%s|%s\n' % (key, stt.isoformat(), ent.isoformat())

            yield text
        return


@cherrypy.expose
@cherrypy.popargs('wsversion')
class DataselectAPI(object):
    """Object dispatching methods related to access to streams."""

    def __init__(self, experiment, directory='.'):
        """Constructor of the DataselectAPI class."""
        # Save parameters
        self.__experiment = experiment
        self.__directory = directory

        # Get extra fields from the cfg file
        cfgfile = configparser.RawConfigParser()
        cfgfile.read(os.path.join(directory, 'tdsmws.cfg'))
        self.__net = cfgfile.get('NSLC', 'network', fallback='XX')
        self.__cha = cfgfile.get('NSLC', 'channel', fallback='FH1')

        # Special case for the empty location. Change '' for '--'
        self.__loc = cfgfile.get('NSLC', 'location', fallback='--')
        if self.__loc == '':
            self.__loc = '--'

    @cherrypy.expose
    def index(self, wsversion='1'):
        if wsversion != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        cherrypy.response.headers['Content-Type'] = 'text/html'
        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp = fin.read()
        except FileNotFoundError:
            texthelp = """<html>
                            <head>tdsmws - Dataselect</head>
                            <body>
                              Default help for the Dataselect service (GEOFON).
                            </body>
                          </html>"""

        return texthelp.encode('utf-8')

    @cherrypy.expose
    def default(self, *args, **kwargs):
        """Use default method to process application.wadl because the dot is not supported in method names"""
        cherrypy.log('default method: %s %s' % (args, kwargs))
        if args[0] != '1':
            # Send Error 400
            message = 'Only Dataselect-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        if args[1] != 'application.wadl':
            # Send Error 400
            message = 'Unknown method "%s"' % args[1]
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        project_dir = os.path.dirname(__file__)

        try:
            with open(os.path.join(project_dir, '../data/dataselect.wadl')) as fin:
                text = fin.read()
                cherrypy.response.headers['Content-Type'] = 'application/xml'
                return text.encode('utf-8')
        except FileNotFoundError:
            pass

        # Send Error 400
        message = 'application.wadl not found!'
        # self.__log.error(message)
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        raise cherrypy.HTTPError(400,  errormessage(400, message))

    @cherrypy.expose
    def version(self, wsversion='1'):
        """Return the version of this implementation.

        :returns: Version of the system
        :rtype: string
        """
        if wsversion != '1':
            # Send Error 400
            message = 'Only Station-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        dataselectversion = '1.1.0'
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return dataselectversion.encode('utf-8')

    @cherrypy.expose
    def query(self, network='*', net='*', station='*', sta='*', location='*', loc='*', channel='*', cha='*',
              starttime=None, start=None, endtime=None, end=None, wsversion='1', **kwargs):
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
        :param wsversion: Major version of the Dataselect web service
        :type wsversion: str
        :returns: miniSEED data
        :rtype: bytearray
        :raises: cherrypy.HTTPError
        """

        # Check parameters
        if wsversion != '1':
            # Send Error 400
            message = 'Only Dataselect-WS version 1 is supported'
            # self.__log.error(message)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400, errormessage(400, message))

        # Network
        if network not in ('*', self.__net) or net not in ('*', self.__net):
            cherrypy.response.status = 204
            return

        # Location
        if location not in ('*', self.__loc) or loc not in ('*', self.__loc):
            cherrypy.response.status = 204
            return

        # Channel
        if channel not in ('*', self.__cha) or cha not in ('*', self.__cha):
            cherrypy.response.status = 204
            return

        # Station and sta
        # Discard the most comprehensive case of '*' and keep the most restricted one
        auxsta = station if sta == '*' else sta

        # Starttime and start
        # Discard the most comprehensive case of None and keep the most restricted one
        starttime = starttime if start is None else start

        # Endtime and end
        # Discard the most comprehensive case of None and keep the most restricted one
        endtime = endtime if end is None else end

        # Station(s)
        try:
            liststa = [] if auxsta == '*' else [int(x) for x in auxsta.split(',')]
        except Exception:
            # Send Error 400
            message = 'Wrong formatted list of stations (%s).' % sta
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            raise cherrypy.HTTPError(400,  errormessage(400, message))

        if starttime is not None:
            try:
                startdt = str2date(starttime)
            except Exception:
                # Send Error 400
                message = 'Error converting the "starttime" parameter (%s).' % starttime
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                raise cherrypy.HTTPError(400, errormessage(400, message))
        else:
            startdt = None

        if endtime is not None:
            try:
                enddt = str2date(endtime)
            except Exception:
                # Send Error 400
                message = 'Error converting the "endtime" parameter (%s).' % endtime
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                raise cherrypy.HTTPError(400, errormessage(400, message))
        else:
            enddt = None

        cherrypy.response.headers['Content-Type'] = 'application/vnd.fdsn.mseed'
        return self.__generatemseed(liststa, startdt, enddt)

    def __generatemseed(self, streams, starttime=None, endtime=None):
        """Generator to extract miniSEED data based on the selection

        :param streams: List of streams (integers) to be extracted
        :type streams: list
        :param starttime: Start time of the time window to access
        :type starttime: datetime
        :param endtime: End time of the time window to access
        :type endtime: datetime
        :returns: miniSEED data
        :rtype: bytearray
        """

        channels = streams if len(streams) else None

        t = TDMS(self.__experiment, directory=self.__directory, starttime=starttime, endtime=endtime,
                 channels=channels)
        with t:
            for data in t:
                # Create the Trace
                tr0 = Trace(data=data[0], header=data[1])
                auxout = BytesIO()
                tr0.write(auxout, format='MSEED', reclen=512)
                yield auxout.getvalue()
                auxout.close()

        return


def main():
    """Run the tdmsws service implementing a Dataselect-WS on top of TDMS files"""

    desc = 'tdmsws is an FDSN Dataselect implementation to read TDMS files'
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
        config['General'] = {'experiment': 'filename', 'loglevel': 'INFO', 'siteName': 'Site description for StationWS'}
        config['NSLC'] = {'network': 'XX', 'location': '', 'channel': 'FH1'}
        # Write to tdmsws.cfg
        with open('tdmsws.cfg', 'w') as configfile:
            config.write(configfile)
        return

    # Open the configuration file in the current directory
    config.read('tdmsws.cfg')
    
    # Read general parameters
    experiment = config.get('General', 'experiment')

    server_config = {
        'global': {
            'tools.proxy.on': True,
            'server.socket_host': 'localhost',
            'server.socket_port': 7000,
            'engine.autoreload_on': False,
            'log.access_file': 'access.log',
            'log.error_file': 'error.log'
        }
    }
    # Update the global CherryPy configuration
    cherrypy.config.update(server_config)
    cherrypy.tree.mount(TdmswsAPI(experiment), '/fdsnws')

    plugins.Daemonizer(cherrypy.engine).subscribe()
    if hasattr(cherrypy.engine, 'signal_handler'):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, 'console_control_handler'):
        cherrypy.engine.console_control_handler.subscribe()

    # Always start the engine; this will start all other services
    try:
        cherrypy.engine.start()
    except Exception:
        # Assume the error has been logged already via bus.log.
        raise
    else:
        cherrypy.engine.block()


if __name__ == "__main__":
    main()
