#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""dastools helper functions and utilities

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
       2019-2025 GFZ Helmholtz Centre for Geosciences, Potsdam, Germany
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz.de>, GEOFON, GFZ Potsdam
"""

import datetime
import json
import sys
import os
import csv
from typing import TextIO
from typing import Union
from typing import List
import pprint
import logging
import urllib.request as ul
from urllib.parse import urlparse
from obspy.core.trace import Stats
from dastools.basemodels import DASMetadata
from dastools.basemodels import ChannelModel
from dastools.basemodels import CableModel
from dastools.basemodels import PI
from xml.etree.ElementTree import parse
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from jinja2 import Environment
from jinja2 import FileSystemLoader
from math import floor


def stationcode2int(id: str) -> int:
    result = (ord(id[0])-65)*10000 + int(id[1:])
    return result


def int2stationcode(id: int) -> str:
    smallid = int(id % 10000)
    let = chr(int(floor(id / 10000)) + 65)
    return "%c%04d" % (let, smallid)


def kml2channels(file: str) -> List[ChannelModel]:
    result = list()
    top = parse(source=file)
    # print(top.tag)
    root = top.getroot()
    if not root.tag.endswith('kml'):
        raise Exception('Not a valid KML file')
    # Extract the namespace from the root node
    namesp = root.tag[:-len('kml')]
    docum = root.find(namesp + 'Document')
    folder = docum.find(namesp + 'Folder')
    for placemark in folder.findall(namesp + 'Placemark'):
        point = placemark.find(namesp + 'Point')
        # coords will have longitude(0), latitude(1) and elevation(2)
        coords = point.find(namesp + 'coordinates').text.strip().split(',')
        chaid = placemark.find(namesp + 'name').text
        try:
            # Correct the channel ID if is expressed as int
            chaid = int2stationcode(int(chaid))
        except ValueError:
            pass

        chan = ChannelModel(channel_id=chaid,
                            x_coordinate=float(coords[1]), y_coordinate=float(coords[0]),
                            elevation_above_sea_level=float(coords[2]),
                            distance_along_fiber=0.0)
        # print(chan)
        result.append(chan)
    return result


def csv2channels(file: str) -> List[ChannelModel]:
    """Read a CSV file and create a list of ChannelModel

    All lines starting with '#' will be ignored as comments.
    The expected structure of the CSV file is the following:
    1) channelID as expected in the output metadata (e.g. A1234, B4321). No more than 5 characters.
       If this is just an integer, it will be transformed to the notation A0001...A9999, B0001,...
    2) latitude as a float
    3) longitude as a float
    4) elevation in meters as a float (optional)
    5) distance along fiber in meters as a float (optional)
    """
    result = list()
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for cha in reader:
            if cha[0].startswith('#'):
                continue
            try:
                # Correct the channel ID if is expressed as int
                cha[0] = int2stationcode(int(cha[0]))
            except ValueError:
                pass

            elev = 0 if len(cha) <= 3 else float(cha[3])
            dist = 0 if len(cha) <= 4 else float(cha[4])
            chan = ChannelModel(channel_id=cha[0], x_coordinate=float(cha[2]), y_coordinate=float(cha[1]),
                                elevation_above_sea_level=elev,
                                distance_along_fiber=dist)
            result.append(chan)
    return result


def dasrcn2stationxml(dasrcn: DASMetadata, gain: float = 1.0) -> ElementTree:
    top = Element('FDSNStationXML', {'xmlns': 'http://www.fdsn.org/xml/station/1', 'schemaVersion': '1.2'})
    src = SubElement(top, 'Source')
    src.text = 'dasmetadata'
    created = SubElement(top, 'Created')
    created.text = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    netw = SubElement(top, 'Network',
                      {'code': dasrcn.network_code,
                       'startDate': dasrcn.start_date.isoformat(),
                       'endDate': dasrcn.end_date.isoformat()})
    desc = SubElement(netw, 'Description')
    desc.text = dasrcn.purpose_of_data_collection
    if dasrcn.digital_object_identifier:
        doi = SubElement(netw, 'Identifier', {'type': 'DOI'})
        doi.text = dasrcn.digital_object_identifier

    try:
        assert len(dasrcn.interrogators[0].acquisitions[0].channel_groups)
        assert len(dasrcn.interrogators[0].acquisitions[0].channel_groups[0].channels)
    except Exception:
        logging.warning('No channels seem to be present in metadata!')
        return ElementTree(top)

    for acq in dasrcn.interrogators[0].acquisitions:
        stt = acq.acquisition_start_time.isoformat()
        ent = acq.acquisition_end_time.isoformat()
        for cha in acq.channel_groups[0].channels:
            station = SubElement(netw, 'Station',
                                 {'code': str(cha.channel_id), 'startDate': stt, 'endDate': ent})
            lat = SubElement(station, 'Latitude', {'unit': "degrees"})
            lat.text = str(cha.y_coordinate)
            lon = SubElement(station, 'Longitude', {'unit': "degrees"})
            lon.text = str(cha.x_coordinate)
            ele = SubElement(station, 'Elevation', {'unit': "m"})
            ele.text = str(cha.elevation_above_sea_level)
            site = SubElement(station, 'Site')
            name = SubElement(site, 'Name')
            name.text = 'Sampling point %s (fibre), %s' % (cha.channel_id, dasrcn.country)
            chaxml = SubElement(station, 'Channel', {'code': 'HSF', 'startDate': stt, 'endDate': ent,
                                                     'locationCode': ''})
            lat = SubElement(chaxml, 'Latitude', {'unit': "degrees"})
            lat.text = str(cha.y_coordinate)
            lon = SubElement(chaxml, 'Longitude', {'unit': "degrees"})
            lon.text = str(cha.x_coordinate)
            ele = SubElement(chaxml, 'Elevation', {'unit': "m"})
            ele.text = str(cha.elevation_above_sea_level)
            dep = SubElement(chaxml, 'Depth', {'unit': "m"})
            dep.text = str(cha.depth_below_surface if cha.depth_below_surface is not None else 0.0)
            # azi = SubElement(chaxml, 'Azimuth')
            # azi.text = str(cha.strike)
            dip = SubElement(chaxml, 'Dip', {'unit': "degrees"})
            dip.text = str(cha.dip if cha.dip is not None else 0.0)
            spr = SubElement(chaxml, 'SampleRate')
            spr.text = str(acq.acquisition_sample_rate)
            # sprr = SubElement(chaxml, 'SampleRateRatio')
            # nums = SubElement(sprr, 'NumberSamples')
            # nums.text = str(int(acq.acquisition_sample_rate))
            # numsec = SubElement(sprr, 'NumberSeconds')
            # numsec.text = '1'
            sens = SubElement(chaxml, 'Sensor')
            senstype = SubElement(sens, 'Type')
            senstype.text = "DAS"
            sensdesc = SubElement(sens, 'Description')
            sensdesc.text = "Manufacturer: %s; Model: %s" % (dasrcn.interrogators[0].manufacturer,
                                                             dasrcn.interrogators[0].model)
            spr.text = str(acq.acquisition_sample_rate)
            resp = SubElement(chaxml, 'Response')
            # Instrument Sensitivity
            instsens = SubElement(resp, 'InstrumentSensitivity')
            instsensval = SubElement(instsens, 'Value')
            instsensval.text = str(gain)
            instsensfreq = SubElement(instsens, 'Frequency')
            instsensfreq.text = '1.0'
            instsensiu = SubElement(instsens, 'InputUnits')
            instsensiuname = SubElement(instsensiu, 'Name')
            instsensiuname.text = 'm/m/s'
            instsensiudesc = SubElement(instsensiu, 'Description')
            instsensiudesc.text = 'Linear Strain Rate unit'
            instsensou = SubElement(instsens, 'OutputUnits')
            instsensouname = SubElement(instsensou, 'Name')
            instsensouname.text = 'count'
            # # Stage 1
            # stage1 = SubElement(resp, 'Stage', {'number': '1'})
            # pz1 = SubElement(stage1, 'PolesZeros')
            # pz1iu = SubElement(pz1, 'InputUnits')
            # pz1iuname = SubElement(pz1iu, 'Name')
            # pz1iuname.text = 'COUNTS'
            # pz1ou = SubElement(pz1, 'OutputUnits')
            # pz1ouname = SubElement(pz1ou, 'Name')
            # pz1ouname.text = 'V'
            # pz1tft = SubElement(pz1, 'PzTransferFunctionType')
            # pz1tft.text = 'LAPLACE (RADIANS/SECOND)'
            # pz1nfact = SubElement(pz1, 'NormalizationFactor')
            # pz1nfact.text = '1'
            # pz1nfreq = SubElement(pz1, 'NormalizationFrequency')
            # pz1nfreq.text = '0'
            # Stage 2
            stage2 = SubElement(resp, 'Stage', {'number': '1'})
            coef2 = SubElement(stage2, 'Coefficients')
            coef2iu = SubElement(coef2, 'InputUnits')
            coef2iuname = SubElement(coef2iu, 'Name')
            coef2iuname.text = 'm/m/s'
            coef2iudesc = SubElement(coef2iu, 'Description')
            coef2iudesc.text = 'Linear Strain Rate unit'
            coef2ou = SubElement(coef2, 'OutputUnits')
            coef2ouname = SubElement(coef2ou, 'Name')
            coef2ouname.text = 'count'
            coef2tft = SubElement(coef2, 'CfTransferFunctionType')
            coef2tft.text = 'DIGITAL'
            coef2num = SubElement(coef2, 'Numerator')
            coef2num.text = '1.0'
            decim = SubElement(stage2, 'Decimation')
            decimsr = SubElement(decim, 'InputSampleRate')
            decimsr.text = str(acq.acquisition_sample_rate)
            decimfact = SubElement(decim, 'Factor')
            decimfact.text = '1'
            decimoff = SubElement(decim, 'Offset')
            decimoff.text = '0'
            decimdel = SubElement(decim, 'Delay')
            decimdel.text = '0'
            decimcorr = SubElement(decim, 'Correction')
            decimcorr.text = '0'
            stage2gain = SubElement(stage2, 'StageGain')
            st2gainvalue = SubElement(stage2gain, 'Value')
            st2gainvalue.text = str(gain)
            st2gainfreq = SubElement(stage2gain, 'Frequency')
            st2gainfreq.text = '1.0'

    return ElementTree(top)


def dasrcn2datacite(dasrcn: DASMetadata) -> str:
    environment = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "data")))
    template = environment.get_template("datacite.xml")
    west = east = north = south = None

    # Read the cable_bounding_box
    cbb = dasrcn.cables[0].cable_bounding_box
    if cbb[0] or cbb[1] or cbb[2] or cbb[3]:
        south = cbb[0]
        north = cbb[1]
        west = cbb[2]
        east = cbb[3]
    elif len(dasrcn.interrogators[0].acquisitions[0].channel_groups[0].channels):
        for ch in dasrcn.interrogators[0].acquisitions[0].channel_groups[0].channels:
            west = ch.x_coordinate if (west is None) or (west < ch.x_coordinate) else west
            east = ch.x_coordinate if (east is None) or (ch.x_coordinate < east) else east
            north = ch.y_coordinate if (north is None) or (north < ch.y_coordinate) else north
            south = ch.y_coordinate if (south is None) or (ch.y_coordinate < south) else south

    context = {
        "doi": dasrcn.digital_object_identifier,
        "creators": [{"name": pi.name} for pi in dasrcn.principal_investigator],
        "title": dasrcn.purpose_of_data_collection,
        "geolocation": {"place": dasrcn.location,
                        "west": west,
                        "east": east,
                        "north": north,
                        "south": south},
        "pubyear": dasrcn.end_date.year,
        "starttime": dasrcn.start_date,
        "endtime": dasrcn.end_date,
        "fundingagency": dasrcn.funding_agency
    }
    return template.render(context)


def doi2dasrcn(doi: str) -> DASMetadata:
    # Remove the prefix/schema to use the rest in the URL
    # It will be added again at the end of this function
    try:
        parts = urlparse(doi)
        if parts.scheme in ('http', 'https') and 'doi.org' in parts.netloc:
            # Take into account the case of https://doi.org/10.1785/0220230325
            doi = parts.path.removeprefix('/')
        elif parts.scheme in ('doi', ''):
            # Take into account the case of doi:10.1785/0220230325 or 10.1785/0220230325
            doi = parts.path.removeprefix('/')
        else:
            raise Exception('Unknown DOI format! Try 10.XXXX/YYYYY or doi:10.XXXX/YYYYY')
    except Exception as e:
        raise e
    if doi.startswith('doi:'):
        doi = doi.removeprefix('doi:')
    url = "https://api.datacite.org/dois/%s" % (doi,)
    req = ul.Request(url)
    u = ul.urlopen(req, timeout=15)
    data = json.load(u)

    cbb = [0, 0, 0, 0]
    location = 'COMPLETE: Geographic location of the installation'
    for item in data['data']['attributes']['geoLocations']:
        if 'geoLocationBox' in item:
            coords = item['geoLocationBox']
            cbb = [float(coords['southBoundLatitude']),
                   float(coords['northBoundLatitude']),
                   float(coords['westBoundLongitude']),
                   float(coords['eastBoundLongitude'])]
        elif 'geoLocationPlace' in item:
            location = item['geoLocationPlace']

    cable = CableModel(cable_bounding_box=cbb)
    # print(data)
    pis = list()
    for creator in data['data']['attributes']['creators']:
        pis.append(PI(name=creator['name'],
                      email='COMPLETE!',
                      address='COMPLETE: Physical address and institution'))
    # print(pis)
    # print(type(pis[0]))
    for contrib in data['data']['attributes']['contributors']:
        if contrib['contributorType'] == "ContactPerson":
            contact = contrib['name']
            break
    else:
        contact = 'COMPLETE!'

    for t in data['data']['attributes']['titles']:
        title = t['title']
        break
    else:
        title = ''

    fund = ''
    for funding in data['data']['attributes']['fundingReferences']:
        fund = funding['funderName'] if not len(fund) else '%s, %s' % (fund, funding['funderName'])

    for desc in data['data']['attributes']['descriptions']:
        comment = desc['description']
        break
    else:
        comment = ''
    result = DASMetadata(location=location,
                         principal_investigator=pis,
                         point_of_contact=contact,
                         funding_agency=fund,
                         digital_object_identifier=doi,
                         purpose_of_data_collection=title,
                         comment=comment,
                         cables=[cable])
    return result


def downloadfile(filename, url):
    """Download a file from the URL passed as parameter

    :param filename: Name of the file to download
    :type filename: str
    :param url: URL where the file is located
    :type url: str
    """
    req = ul.Request(url)

    u = ul.urlopen(req, timeout=15)
    with open(filename, 'wb') as fout:
        fout.write(u.read())


def printmetadata(data, stream: TextIO = sys.stdout):
    """Print the data in a pretty format
    """
    pp = pprint.PrettyPrinter(indent=4, stream=stream)
    # if isinstance(data, dict):
    pp.pprint(data)
    # else:
    #    print(data)


def nslc(dataheader: Union[dict, Stats]) -> str:
    """Get a NSLC code from a dictionary with its components

    :param dataheader: Dictionary with components of a NSLC code
    :type dataheader: dict
    :return: NSLC code
    :rtype: str
    :raise KeyError: if keys 'network', 'station', 'location', or 'channel' are not present
    """
    return '%s.%s.%s.%s' % (dataheader['network'].upper(), dataheader['station'].upper(),
                            dataheader['location'].upper(), dataheader['channel'].upper())


def str2date(dstr: str) -> Union[datetime.datetime, None]:
    """Transform a string to a datetime

    :param dstr: A datetime in ISO format.
    :type dstr: str
    :return: A datetime represented the converted input.
    :rtype: datetime.datetime
    :raise ValueError: if no integers are found as components of the string
    """
    # In case of empty string
    if (dstr is None) or (not len(dstr)):
        return None

    dateparts = dstr.replace('-', ' ').replace('T', ' ')
    dateparts = dateparts.replace(':', ' ').replace('.', ' ')
    dateparts = dateparts.replace('Z', '').split()
    # Consider the case in which just the first digits of microseconds
    # are given and complete with 0's to have 6 digits
    if len(dateparts) == 7:
        dateparts[6] = dateparts[6] + '0' * (6 - len(dateparts[6]))

    return datetime.datetime(*map(int, dateparts))
