from pydantic import BaseModel
from pydantic import Field
from typing import List
from typing import Optional
from typing import Union
from typing import Literal
from datetime import datetime
from datetime import date
from datetime import timezone
from pydantic import constr


def merge(first: BaseModel, second: BaseModel):
    assert isinstance(first, type(second))
    result = first.model_copy(update=second.model_dump(exclude_defaults=True, exclude_none=True, exclude_unset=True),
                              deep=True)
    # Trick to convert to a valid model from an incomplete dict
    return result.model_validate(result.model_dump())


class ChannelModel(BaseModel):
    channel_id: str = Field(max_length=8, default='A0001')
    distance_along_fiber: float
    x_coordinate: float
    y_coordinate: float
    elevation_above_sea_level: Optional[float] = None
    depth_below_surface: Optional[float] = None
    strike: Optional[float] = None
    dip: Optional[float] = None


class ChannelGroupModel(BaseModel):
    channel_group_id: str = Field(max_length=8, default='chgrp01')
    cable_id: str = Field(max_length=8, default='cable01')
    fiber_id: str = Field(max_length=8, default='fiber01')
    coordinate_generation_date: Union[datetime, date] = datetime.now(tz=timezone.utc)
    coordinate_system: Literal['geographic', 'UTM', 'local'] = 'geographic'
    reference_frame: str = 'WGS84'
    location_method: Optional[str] = ''
    distance_along_fiber_unit: str = Field(default='meter')
    x_coordinate_unit: Literal['decimal degree', 'meter'] = Field(default='meter')
    uncertainty_in_x_coordinate: Optional[float] = None
    uncertainty_in_x_coordinate_unit: Optional[str] = Field(default='meter')
    y_coordinate_unit: Literal['decimal degree', 'meter'] = Field(default='meter')
    uncertainty_in_y_coordinate: Optional[float] = None
    uncertainty_in_y_coordinate_unit: Optional[str] = Field(default='meter')
    elevation_above_sea_level_unit: Optional[str] = Field(default='meter')
    uncertainty_in_elevation: Optional[float] = None
    uncertainty_in_elevation_unit: Optional[str] = Field(default='meter')
    depth_below_surface_unit: Optional[str] = Field(default='meter')
    uncertainty_in_depth: Optional[float] = None
    uncertainty_in_depth_unit: Optional[str] = Field(default='meter')
    strike_unit: Optional[str] = Field(default='degree')
    uncertainty_in_strike: Optional[float] = None
    uncertainty_in_strike_unit: Optional[str] = Field(default='degree')
    dip_unit: Optional[str] = Field(default='degree')
    uncertainty_in_dip: Optional[float] = None
    uncertainty_in_dip_unit: Optional[str] = Field(default='degree')
    first_usable_channel_id: Optional[str] = ''
    last_usable_channel_id: Optional[str] = ''
    comment: Optional[str] = ''
    channels: Optional[List[ChannelModel]] = Field(default=list())


class AcquisitionModel(BaseModel):
    acquisition_id: str = Field(max_length=8, default='acqui01')
    acquisition_start_time: Union[datetime, date] = datetime(1980, 1, 1)
    acquisition_end_time: Union[datetime, date] = datetime(2999, 12, 31)
    acquisition_sample_rate: Union[float, None] = Field(gt=0, default=None)
    acquisition_sample_rate_unit: str = Field(default='hertz')
    gauge_length: Union[float, None] = Field(gt=0, default=None)
    gauge_length_unit: str = Field(default='meter')
    unit_of_measure: Literal['count', 'strain', 'strain-rate', 'velocity', 'COMPLETE!'] = Field(default='COMPLETE!')
    number_of_channels: Union[int, None] = Field(gt=0, default=None)
    spatial_sampling_interval: Union[float, None] = Field(gt=0, default=None)
    spatial_sampling_interval_unit: str = Field(default='meter')
    pulse_rate: Optional[float] = Field(ge=0, default=None)
    pulse_rate_unit: Optional[str] = Field(default='hertz')
    pulse_width: Optional[float] = None
    pulse_width_unit: Optional[str] = Field(default='nanoseconds')
    comment: Optional[str] = ''
    channel_groups: List[ChannelGroupModel] = Field(default=list())


class InterrogatorModel(BaseModel):
    interrogator_id: str = Field(max_length=8, default='inter01')
    manufacturer: str = 'COMPLETE!'
    model: str = 'COMPLETE!'
    serial_number: Optional[str] = ''
    firmware_version: Optional[str] = ''
    comment: Optional[str] = ''
    acquisitions: List[AcquisitionModel] = Field(default=[AcquisitionModel()])


class FiberModel(BaseModel):
    fiber_id: str = Field(max_length=8, default='fiber01')
    fiber_geometry: str = 'COMPLETE!'
    fiber_mode: Literal['single-mode', 'multi-mode', 'other'] = Field(default='single-mode')
    fiber_refraction_index: float = Field(default=1.4681)
    fiber_winding_angle: Optional[float] = None
    fiber_winding_angle_unit: Optional[str] = Field(default='degree')
    fiber_start_location: Optional[float] = Field(ge=0, default=None)
    fiber_start_location_unit: Optional[str] = Field(default='meter')
    fiber_end_location: Optional[float] = Field(ge=0, default=None)
    fiber_end_location_unit: Optional[str] = Field(default='meter')
    fiber_optical_length: Optional[float] = Field(ge=0, default=None)
    fiber_optical_length_unit: Optional[str] = Field(default='meter')
    fiber_one_way_attenuation: Optional[float] = Field(ge=0, default=None)
    fiber_one_way_attenuation_unit: Literal['decibels/meter', 'decibels/kilometer'] = Field(default='decibels/meter')
    comment: Optional[str] = ''


class CableModel(BaseModel):
    cable_id: str = Field(max_length=8, default='cable01')
    cable_bounding_box: List[float] = Field(default=[0, 0, 0, 0])
    cable_owner: Optional[str] = ''
    cable_installation_date: Optional[Union[datetime, date]] = None
    cable_removal_date: Optional[Union[datetime, date]] = None
    cable_characteristics: Optional[str] = ''
    cable_environment: Optional[str] = ''
    cable_installation_environment: Optional[str] = ''
    cable_model: Optional[str] = ''
    cable_outside_diameter: Optional[float] = None
    cable_outside_diameter_unit: Optional[str] = Field(default='millimeter')
    comment: Optional[str] = ''
    fibers: List[FiberModel] = Field(default=[FiberModel()])


class PI(BaseModel):
    name: str = Field(default='COMPLETE!')
    email: str = Field(default='COMPLETE!')
    address: str = Field(default='COMPLETE: Physical address and institution')


class DASMetadata(BaseModel):
    sch: Literal['https://www.fdsn.org/schemas/DAS-Metadata-FDSN/2.0'] = Field(default='https://www.fdsn.org/schemas/DAS-Metadata-FDSN/2.0',
                                                                               alias='schema')
    version: str = Field(default='2.0')
    network_code: constr(max_length=8, to_upper=True, strip_whitespace=True) = 'UNKNOWN'
    location: str = Field(default='COMPLETE: Geographic location of the installation')
    country: constr(min_length=3, max_length=3, to_upper=True, strip_whitespace=True) = 'ABC'
    principal_investigator: List[PI] = Field(default=[PI()])
    point_of_contact: str = Field(default='COMPLETE!')
    point_of_contact_email: str = Field(default='COMPLETE!')
    point_of_contact_address: str = Field(default='COMPLETE: Physical address and institution')
    start_date: date = date(1980, 1, 1)
    end_date: date = date(2999, 12, 31)
    funding_agency: Optional[str] = ''
    project_number: Optional[str] = ''
    digital_object_identifier: Optional[str] = Field(default='10.XXXX/COMPLETE!')
    purpose_of_data_collection: Optional[str] = ''
    comment: str = Field(default='Automatically generated by dasmetadata (dastools).')
    interrogators: List[InterrogatorModel] = Field(default=[InterrogatorModel()])
    cables: List[CableModel] = Field(default=[CableModel()])


class NetworkStationWS(BaseModel):
    net: str
    sitename: str
    start: datetime
    end: datetime
    numstations: int

    def __str__(self) -> str:
        return "{0}|{1}|{2}|{3}|{4}".format(self.net, self.sitename, self.start.isoformat(),
                                            self.end.isoformat(), self.numstations)


# Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime
class StationStationWS(BaseModel):
    net: str
    sta: str
    lat: float
    lon: float
    elev: float
    sitename: str
    start: datetime
    end: datetime

    def __str__(self) -> str:
        return "{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}".format(self.net, self.sta, self.lat, self.lon, self.elev,
                                                        self.sitename, self.start.isoformat(),
                                                        self.end.isoformat())


# Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|
# SensorDescription|Scale|ScaleFreq|ScaleUnits|SampleRate|StartTime|EndTime
class ChannelStationWS(BaseModel):
    net: str
    sta: str
    loc: str
    cha: str
    lat: float
    lon: float
    elev: float
    depth: float
    azimuth: float
    dip: float
    sensor: str
    scale: float
    scalefreq: float
    scaleunits: str
    samplerate: float
    start: datetime
    end: datetime

    def __str__(self) -> str:
        auxstr = "{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}|{10}|{11}|{12}|{13}|{14}|{15}|{16}"
        return auxstr.format(self.net, self.sta, self.loc, self.cha, self.lat, self.lon, self.elev,
                             self.depth, self.azimuth, self.dip, self.sensor, self.scale, self.scalefreq,
                             self.scaleunits, self.samplerate, self.start.isoformat(), self.end.isoformat())
