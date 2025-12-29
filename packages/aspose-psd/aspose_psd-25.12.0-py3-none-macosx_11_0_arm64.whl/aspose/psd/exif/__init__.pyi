from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.psd
import aspose.psd.asynctask
import aspose.psd.brushes
import aspose.psd.coreexceptions
import aspose.psd.coreexceptions.compressors
import aspose.psd.coreexceptions.imageformats
import aspose.psd.customfonthandler
import aspose.psd.dithering
import aspose.psd.evalute
import aspose.psd.exif
import aspose.psd.exif.enums
import aspose.psd.extensions
import aspose.psd.fileformats
import aspose.psd.fileformats.ai
import aspose.psd.fileformats.bmp
import aspose.psd.fileformats.core
import aspose.psd.fileformats.core.blending
import aspose.psd.fileformats.core.vectorpaths
import aspose.psd.fileformats.jpeg
import aspose.psd.fileformats.jpeg2000
import aspose.psd.fileformats.pdf
import aspose.psd.fileformats.png
import aspose.psd.fileformats.psd
import aspose.psd.fileformats.psd.core
import aspose.psd.fileformats.psd.core.rawcolor
import aspose.psd.fileformats.psd.layers
import aspose.psd.fileformats.psd.layers.adjustmentlayers
import aspose.psd.fileformats.psd.layers.animation
import aspose.psd.fileformats.psd.layers.filllayers
import aspose.psd.fileformats.psd.layers.fillsettings
import aspose.psd.fileformats.psd.layers.gradient
import aspose.psd.fileformats.psd.layers.layereffects
import aspose.psd.fileformats.psd.layers.layerresources
import aspose.psd.fileformats.psd.layers.layerresources.strokeresources
import aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures
import aspose.psd.fileformats.psd.layers.smartfilters
import aspose.psd.fileformats.psd.layers.smartfilters.rendering
import aspose.psd.fileformats.psd.layers.smartobjects
import aspose.psd.fileformats.psd.layers.text
import aspose.psd.fileformats.psd.layers.warp
import aspose.psd.fileformats.psd.resources
import aspose.psd.fileformats.psd.resources.enums
import aspose.psd.fileformats.psd.resources.resolutionenums
import aspose.psd.fileformats.tiff
import aspose.psd.fileformats.tiff.enums
import aspose.psd.fileformats.tiff.filemanagement
import aspose.psd.flatarray
import aspose.psd.flatarray.exceptions
import aspose.psd.imagefilters
import aspose.psd.imagefilters.filteroptions
import aspose.psd.imageloadoptions
import aspose.psd.imageoptions
import aspose.psd.interfaces
import aspose.psd.memorymanagement
import aspose.psd.multithreading
import aspose.psd.palettehelper
import aspose.psd.progressmanagement
import aspose.psd.shapes
import aspose.psd.shapesegments
import aspose.psd.sources
import aspose.psd.xmp
import aspose.psd.xmp.schemas
import aspose.psd.xmp.schemas.dublincore
import aspose.psd.xmp.schemas.pdf
import aspose.psd.xmp.schemas.photoshop
import aspose.psd.xmp.schemas.xmpbaseschema
import aspose.psd.xmp.schemas.xmpdm
import aspose.psd.xmp.schemas.xmpmm
import aspose.psd.xmp.schemas.xmprm
import aspose.psd.xmp.types
import aspose.psd.xmp.types.basic
import aspose.psd.xmp.types.complex
import aspose.psd.xmp.types.complex.colorant
import aspose.psd.xmp.types.complex.dimensions
import aspose.psd.xmp.types.complex.font
import aspose.psd.xmp.types.complex.resourceevent
import aspose.psd.xmp.types.complex.resourceref
import aspose.psd.xmp.types.complex.thumbnail
import aspose.psd.xmp.types.complex.version
import aspose.psd.xmp.types.derived

class ExifData(TiffDataTypeController):
    '''EXIF data container.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.ExifData` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, exifdata : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.ExifData` class with data from array.
        
        :param exifdata: Array of EXIF tags together with common and GPS tags.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, common_tags : List[aspose.psd.fileformats.tiff.TiffDataType], exif_tags : List[aspose.psd.fileformats.tiff.TiffDataType], gps_tags : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.ExifData` class with data from array.
        
        :param common_tags: The common tags.
        :param exif_tags: The EXIF tags.
        :param gps_tags: The GPS tags.'''
        raise NotImplementedError()
    
    @overload
    def remove_tag(self, tag : aspose.psd.exif.ExifProperties) -> None:
        '''Remove tag from container
        
        :param tag: The tag to remove'''
        raise NotImplementedError()
    
    @overload
    def remove_tag(self, tag_id : int) -> None:
        '''Remove tag from container
        
        :param tag_id: The tag identifier to remove.'''
        raise NotImplementedError()
    
    @property
    def is_big_endian(self) -> bool:
        '''Gets a value indicating whether the stream EXIF data created from is big endian.'''
        raise NotImplementedError()
    
    @is_big_endian.setter
    def is_big_endian(self, value : bool) -> None:
        '''Sets a value indicating whether the stream EXIF data created from is big endian.'''
        raise NotImplementedError()
    
    @property
    def aperture_value(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the aperture value.'''
        raise NotImplementedError()
    
    @aperture_value.setter
    def aperture_value(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the aperture value.'''
        raise NotImplementedError()
    
    @property
    def body_serial_number(self) -> str:
        '''Gets camera body serial number.'''
        raise NotImplementedError()
    
    @body_serial_number.setter
    def body_serial_number(self, value : str) -> None:
        '''Sets camera body serial number.'''
        raise NotImplementedError()
    
    @property
    def brightness_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the brightness value.'''
        raise NotImplementedError()
    
    @brightness_value.setter
    def brightness_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the brightness value.'''
        raise NotImplementedError()
    
    @property
    def cfa_pattern(self) -> List[int]:
        '''Gets the CFA pattern.'''
        raise NotImplementedError()
    
    @cfa_pattern.setter
    def cfa_pattern(self, value : List[int]) -> None:
        '''Sets the CFA pattern.'''
        raise NotImplementedError()
    
    @property
    def camera_owner_name(self) -> str:
        '''Gets camera owner name'''
        raise NotImplementedError()
    
    @camera_owner_name.setter
    def camera_owner_name(self, value : str) -> None:
        '''Sets camera owner name'''
        raise NotImplementedError()
    
    @property
    def color_space(self) -> aspose.psd.exif.enums.ExifColorSpace:
        '''Gets the color space.'''
        raise NotImplementedError()
    
    @color_space.setter
    def color_space(self, value : aspose.psd.exif.enums.ExifColorSpace) -> None:
        '''Sets the color space.'''
        raise NotImplementedError()
    
    @property
    def components_configuration(self) -> List[int]:
        '''Gets the components configuration.'''
        raise NotImplementedError()
    
    @components_configuration.setter
    def components_configuration(self, value : List[int]) -> None:
        '''Sets the components configuration.'''
        raise NotImplementedError()
    
    @property
    def compressed_bits_per_pixel(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the compressed bits per pixel.'''
        raise NotImplementedError()
    
    @compressed_bits_per_pixel.setter
    def compressed_bits_per_pixel(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the compressed bits per pixel.'''
        raise NotImplementedError()
    
    @property
    def contrast(self) -> aspose.psd.exif.enums.ExifContrast:
        '''Gets the contrast.'''
        raise NotImplementedError()
    
    @contrast.setter
    def contrast(self, value : aspose.psd.exif.enums.ExifContrast) -> None:
        '''Sets the contrast.'''
        raise NotImplementedError()
    
    @property
    def custom_rendered(self) -> aspose.psd.exif.enums.ExifCustomRendered:
        '''Gets the custom rendered.'''
        raise NotImplementedError()
    
    @custom_rendered.setter
    def custom_rendered(self, value : aspose.psd.exif.enums.ExifCustomRendered) -> None:
        '''Sets the custom rendered.'''
        raise NotImplementedError()
    
    @property
    def date_time_digitized(self) -> str:
        '''Gets the date time digitized.'''
        raise NotImplementedError()
    
    @date_time_digitized.setter
    def date_time_digitized(self, value : str) -> None:
        '''Sets the date time digitized.'''
        raise NotImplementedError()
    
    @property
    def date_time_original(self) -> str:
        '''Gets the date time original.'''
        raise NotImplementedError()
    
    @date_time_original.setter
    def date_time_original(self, value : str) -> None:
        '''Sets the date time original.'''
        raise NotImplementedError()
    
    @property
    def device_setting_description(self) -> List[int]:
        '''Gets device settings description'''
        raise NotImplementedError()
    
    @device_setting_description.setter
    def device_setting_description(self, value : List[int]) -> None:
        '''Sets device settings description'''
        raise NotImplementedError()
    
    @property
    def digital_zoom_ratio(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the digital zoom ratio.'''
        raise NotImplementedError()
    
    @digital_zoom_ratio.setter
    def digital_zoom_ratio(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the digital zoom ratio.'''
        raise NotImplementedError()
    
    @property
    def exif_version(self) -> List[int]:
        '''Gets the EXIF version.'''
        raise NotImplementedError()
    
    @exif_version.setter
    def exif_version(self, value : List[int]) -> None:
        '''Sets the EXIF version.'''
        raise NotImplementedError()
    
    @property
    def exposure_bias_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the exposure bias value.'''
        raise NotImplementedError()
    
    @exposure_bias_value.setter
    def exposure_bias_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the exposure bias value.'''
        raise NotImplementedError()
    
    @property
    def exposure_index(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the exposure index.'''
        raise NotImplementedError()
    
    @exposure_index.setter
    def exposure_index(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the exposure index.'''
        raise NotImplementedError()
    
    @property
    def exposure_mode(self) -> aspose.psd.exif.enums.ExifExposureMode:
        '''Gets the exposure mode.'''
        raise NotImplementedError()
    
    @exposure_mode.setter
    def exposure_mode(self, value : aspose.psd.exif.enums.ExifExposureMode) -> None:
        '''Sets the exposure mode.'''
        raise NotImplementedError()
    
    @property
    def exposure_program(self) -> aspose.psd.exif.enums.ExifExposureProgram:
        '''Gets the exposure program.'''
        raise NotImplementedError()
    
    @exposure_program.setter
    def exposure_program(self, value : aspose.psd.exif.enums.ExifExposureProgram) -> None:
        '''Sets the exposure program.'''
        raise NotImplementedError()
    
    @property
    def exposure_time(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the exposure time.'''
        raise NotImplementedError()
    
    @exposure_time.setter
    def exposure_time(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the exposure time.'''
        raise NotImplementedError()
    
    @property
    def f_number(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the F-number.'''
        raise NotImplementedError()
    
    @f_number.setter
    def f_number(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the F-number.'''
        raise NotImplementedError()
    
    @property
    def file_source(self) -> aspose.psd.exif.enums.ExifFileSource:
        '''Gets the file source type.'''
        raise NotImplementedError()
    
    @file_source.setter
    def file_source(self, value : aspose.psd.exif.enums.ExifFileSource) -> None:
        '''Sets the file source type.'''
        raise NotImplementedError()
    
    @property
    def flash(self) -> aspose.psd.exif.enums.ExifFlash:
        '''Gets the flash.'''
        raise NotImplementedError()
    
    @flash.setter
    def flash(self, value : aspose.psd.exif.enums.ExifFlash) -> None:
        '''Sets the flash.'''
        raise NotImplementedError()
    
    @property
    def flash_energy(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the flash energy.'''
        raise NotImplementedError()
    
    @flash_energy.setter
    def flash_energy(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the flash energy.'''
        raise NotImplementedError()
    
    @property
    def flashpix_version(self) -> List[int]:
        '''Gets the flash pix version.'''
        raise NotImplementedError()
    
    @flashpix_version.setter
    def flashpix_version(self, value : List[int]) -> None:
        '''Sets the flash pix version.'''
        raise NotImplementedError()
    
    @property
    def focal_length(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal length.'''
        raise NotImplementedError()
    
    @focal_length.setter
    def focal_length(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal length.'''
        raise NotImplementedError()
    
    @property
    def focal_length_in_35_mm_film(self) -> int:
        '''Gets the focal length in 35 mm film.'''
        raise NotImplementedError()
    
    @focal_length_in_35_mm_film.setter
    def focal_length_in_35_mm_film(self, value : int) -> None:
        '''Sets the focal length in 35 mm film.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_resolution_unit(self) -> aspose.psd.exif.enums.ExifUnit:
        '''Gets the focal plane resolution unit.'''
        raise NotImplementedError()
    
    @focal_plane_resolution_unit.setter
    def focal_plane_resolution_unit(self, value : aspose.psd.exif.enums.ExifUnit) -> None:
        '''Sets the focal plane resolution unit.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_x_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal plane x resolution.'''
        raise NotImplementedError()
    
    @focal_plane_x_resolution.setter
    def focal_plane_x_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal plane x resolution.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_y_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal plane y resolution.'''
        raise NotImplementedError()
    
    @focal_plane_y_resolution.setter
    def focal_plane_y_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal plane y resolution.'''
        raise NotImplementedError()
    
    @property
    def gps_altitude(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS altitude.'''
        raise NotImplementedError()
    
    @gps_altitude.setter
    def gps_altitude(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS altitude.'''
        raise NotImplementedError()
    
    @property
    def gps_altitude_ref(self) -> aspose.psd.exif.enums.ExifGPSAltitudeRef:
        '''Gets the GPS altitude used as the reference altitude.'''
        raise NotImplementedError()
    
    @gps_altitude_ref.setter
    def gps_altitude_ref(self, value : aspose.psd.exif.enums.ExifGPSAltitudeRef) -> None:
        '''Sets the GPS altitude used as the reference altitude.'''
        raise NotImplementedError()
    
    @property
    def gps_area_information(self) -> List[int]:
        '''Gets the GPS area information.'''
        raise NotImplementedError()
    
    @gps_area_information.setter
    def gps_area_information(self, value : List[int]) -> None:
        '''Sets the GPS area information.'''
        raise NotImplementedError()
    
    @property
    def gpsdop(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS DOP (data degree of precision).'''
        raise NotImplementedError()
    
    @gpsdop.setter
    def gpsdop(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS DOP (data degree of precision).'''
        raise NotImplementedError()
    
    @property
    def gps_dest_bearing(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS bearing to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_bearing.setter
    def gps_dest_bearing(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS bearing to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_bearing_ref(self) -> str:
        '''Gets the GPS reference used for giving the bearing to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_bearing_ref.setter
    def gps_dest_bearing_ref(self, value : str) -> None:
        '''Sets the GPS reference used for giving the bearing to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_distance(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS distance to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_distance.setter
    def gps_dest_distance(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS distance to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_distance_ref(self) -> str:
        '''Gets the GPS unit used to express the distance to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_distance_ref.setter
    def gps_dest_distance_ref(self, value : str) -> None:
        '''Sets the GPS unit used to express the distance to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_latitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS latitude of the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_latitude.setter
    def gps_dest_latitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS latitude of the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_latitude_ref(self) -> str:
        '''Gets the GPS value which indicates whether the latitude of the destination point is north or south latitude.'''
        raise NotImplementedError()
    
    @gps_dest_latitude_ref.setter
    def gps_dest_latitude_ref(self, value : str) -> None:
        '''Sets the GPS value which indicates whether the latitude of the destination point is north or south latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_longitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS longitude of the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_longitude.setter
    def gps_dest_longitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS longitude of the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_longitude_ref(self) -> str:
        '''Gets the GPS value which indicates whether the longitude of the destination point is east or west longitude.'''
        raise NotImplementedError()
    
    @gps_dest_longitude_ref.setter
    def gps_dest_longitude_ref(self, value : str) -> None:
        '''Sets the GPS value which indicates whether the longitude of the destination point is east or west longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_differential(self) -> int:
        '''Gets a GPS value which indicates whether differential correction is applied to the GPS receiver.'''
        raise NotImplementedError()
    
    @gps_differential.setter
    def gps_differential(self, value : int) -> None:
        '''Sets a GPS value which indicates whether differential correction is applied to the GPS receiver.'''
        raise NotImplementedError()
    
    @property
    def gps_img_direction(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS direction of the image when it was captured.'''
        raise NotImplementedError()
    
    @gps_img_direction.setter
    def gps_img_direction(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS direction of the image when it was captured.'''
        raise NotImplementedError()
    
    @property
    def gps_img_direction_ref(self) -> str:
        '''Gets the GPS reference for giving the direction of the image when it is captured.'''
        raise NotImplementedError()
    
    @gps_img_direction_ref.setter
    def gps_img_direction_ref(self, value : str) -> None:
        '''Sets the GPS reference for giving the direction of the image when it is captured.'''
        raise NotImplementedError()
    
    @property
    def gps_date_stamp(self) -> str:
        '''Gets the GPS character string recording date and time information relative to UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @gps_date_stamp.setter
    def gps_date_stamp(self, value : str) -> None:
        '''Sets the GPS character string recording date and time information relative to UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @property
    def gps_latitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS latitude.'''
        raise NotImplementedError()
    
    @gps_latitude.setter
    def gps_latitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_latitude_ref(self) -> str:
        '''Gets the GPS latitude is north or south latitude.'''
        raise NotImplementedError()
    
    @gps_latitude_ref.setter
    def gps_latitude_ref(self, value : str) -> None:
        '''Sets the GPS latitude is north or south latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_longitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS longitude.'''
        raise NotImplementedError()
    
    @gps_longitude.setter
    def gps_longitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_longitude_ref(self) -> str:
        '''Gets the GPS longitude is east or west longitude.'''
        raise NotImplementedError()
    
    @gps_longitude_ref.setter
    def gps_longitude_ref(self, value : str) -> None:
        '''Sets the GPS longitude is east or west longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_map_datum(self) -> str:
        '''Gets the GPS geodetic survey data used by the GPS receiver.'''
        raise NotImplementedError()
    
    @gps_map_datum.setter
    def gps_map_datum(self, value : str) -> None:
        '''Sets the GPS geodetic survey data used by the GPS receiver.'''
        raise NotImplementedError()
    
    @property
    def gps_measure_mode(self) -> str:
        '''Gets the GPS measurement mode.'''
        raise NotImplementedError()
    
    @gps_measure_mode.setter
    def gps_measure_mode(self, value : str) -> None:
        '''Sets the GPS measurement mode.'''
        raise NotImplementedError()
    
    @property
    def gps_processing_method(self) -> List[int]:
        '''Gets the GPS character string recording the name of the method used for location finding.'''
        raise NotImplementedError()
    
    @gps_processing_method.setter
    def gps_processing_method(self, value : List[int]) -> None:
        '''Sets the GPS character string recording the name of the method used for location finding.'''
        raise NotImplementedError()
    
    @property
    def gps_satellites(self) -> str:
        '''Gets the GPS satellites used for measurements.'''
        raise NotImplementedError()
    
    @gps_satellites.setter
    def gps_satellites(self, value : str) -> None:
        '''Sets the GPS satellites used for measurements.'''
        raise NotImplementedError()
    
    @property
    def gps_speed(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the speed of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_speed.setter
    def gps_speed(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the speed of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_speed_ref(self) -> str:
        '''Gets the unit used to express the GPS receiver speed of movement.'''
        raise NotImplementedError()
    
    @gps_speed_ref.setter
    def gps_speed_ref(self, value : str) -> None:
        '''Sets the unit used to express the GPS receiver speed of movement.'''
        raise NotImplementedError()
    
    @property
    def gps_status(self) -> str:
        '''Gets the status of the GPS receiver when the image is recorded.'''
        raise NotImplementedError()
    
    @gps_status.setter
    def gps_status(self, value : str) -> None:
        '''Sets the status of the GPS receiver when the image is recorded.'''
        raise NotImplementedError()
    
    @property
    def gps_timestamp(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS time as UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @gps_timestamp.setter
    def gps_timestamp(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS time as UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @property
    def gps_track(self) -> str:
        '''Gets direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_track.setter
    def gps_track(self, value : str) -> None:
        '''Sets direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_track_ref(self) -> str:
        '''Gets the reference for giving the direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_track_ref.setter
    def gps_track_ref(self, value : str) -> None:
        '''Sets the reference for giving the direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_version_id(self) -> List[int]:
        '''Gets the GPS version identifier.'''
        raise NotImplementedError()
    
    @gps_version_id.setter
    def gps_version_id(self, value : List[int]) -> None:
        '''Sets the GPS version identifier.'''
        raise NotImplementedError()
    
    @property
    def gain_control(self) -> aspose.psd.exif.enums.ExifGainControl:
        '''Gets the degree of overall image gain adjustment.'''
        raise NotImplementedError()
    
    @gain_control.setter
    def gain_control(self, value : aspose.psd.exif.enums.ExifGainControl) -> None:
        '''Sets the degree of overall image gain adjustment.'''
        raise NotImplementedError()
    
    @property
    def gamma(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the gamma.'''
        raise NotImplementedError()
    
    @gamma.setter
    def gamma(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the gamma.'''
        raise NotImplementedError()
    
    @property
    def iso_speed(self) -> int:
        '''Gets ISO speed'''
        raise NotImplementedError()
    
    @iso_speed.setter
    def iso_speed(self, value : int) -> None:
        '''Sets ISO speed'''
        raise NotImplementedError()
    
    @property
    def iso_speed_latitude_yyy(self) -> int:
        '''Gets the ISO speed latitude yyy value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @iso_speed_latitude_yyy.setter
    def iso_speed_latitude_yyy(self, value : int) -> None:
        '''Sets the ISO speed latitude yyy value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @property
    def iso_speed_latitude_zzz(self) -> int:
        '''Gets the ISO speed latitude zzz value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @iso_speed_latitude_zzz.setter
    def iso_speed_latitude_zzz(self, value : int) -> None:
        '''Sets the ISO speed latitude zzz value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @property
    def photographic_sensitivity(self) -> int:
        '''Gets the photographic sensitivity.'''
        raise NotImplementedError()
    
    @photographic_sensitivity.setter
    def photographic_sensitivity(self, value : int) -> None:
        '''Sets the photographic sensitivity.'''
        raise NotImplementedError()
    
    @property
    def image_unique_id(self) -> str:
        '''Gets the image unique identifier.'''
        raise NotImplementedError()
    
    @image_unique_id.setter
    def image_unique_id(self, value : str) -> None:
        '''Sets the image unique identifier.'''
        raise NotImplementedError()
    
    @property
    def lens_make(self) -> str:
        '''Gets the maker of lens.'''
        raise NotImplementedError()
    
    @lens_make.setter
    def lens_make(self, value : str) -> None:
        '''Sets the maker of lens.'''
        raise NotImplementedError()
    
    @property
    def lens_model(self) -> str:
        '''Gets the lens model.'''
        raise NotImplementedError()
    
    @lens_model.setter
    def lens_model(self, value : str) -> None:
        '''Sets the lens model.'''
        raise NotImplementedError()
    
    @property
    def lens_serial_number(self) -> str:
        '''Gets the lens serial number.'''
        raise NotImplementedError()
    
    @lens_serial_number.setter
    def lens_serial_number(self, value : str) -> None:
        '''Sets the lens serial number.'''
        raise NotImplementedError()
    
    @property
    def lens_specification(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the lens specification'''
        raise NotImplementedError()
    
    @lens_specification.setter
    def lens_specification(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the lens specification'''
        raise NotImplementedError()
    
    @property
    def light_source(self) -> aspose.psd.exif.enums.ExifLightSource:
        '''Gets the light source.'''
        raise NotImplementedError()
    
    @light_source.setter
    def light_source(self, value : aspose.psd.exif.enums.ExifLightSource) -> None:
        '''Sets the light source.'''
        raise NotImplementedError()
    
    @property
    def maker_note_data(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets the maker note data.'''
        raise NotImplementedError()
    
    @property
    def maker_note_raw_data(self) -> List[int]:
        '''Gets the maker note raw data.'''
        raise NotImplementedError()
    
    @maker_note_raw_data.setter
    def maker_note_raw_data(self, value : List[int]) -> None:
        '''Sets the maker note raw data.'''
        raise NotImplementedError()
    
    @property
    def max_aperture_value(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the maximum aperture value.'''
        raise NotImplementedError()
    
    @max_aperture_value.setter
    def max_aperture_value(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the maximum aperture value.'''
        raise NotImplementedError()
    
    @property
    def metering_mode(self) -> aspose.psd.exif.enums.ExifMeteringMode:
        '''Gets the metering mode.'''
        raise NotImplementedError()
    
    @metering_mode.setter
    def metering_mode(self, value : aspose.psd.exif.enums.ExifMeteringMode) -> None:
        '''Sets the metering mode.'''
        raise NotImplementedError()
    
    @property
    def oecf(self) -> List[int]:
        '''Gets the Opto-Electric Conversion Function (OECF) specified in ISO 14524.'''
        raise NotImplementedError()
    
    @oecf.setter
    def oecf(self, value : List[int]) -> None:
        '''Sets the Opto-Electric Conversion Function (OECF) specified in ISO 14524.'''
        raise NotImplementedError()
    
    @property
    def pixel_x_dimension(self) -> int:
        '''Gets the pixel x dimension.'''
        raise NotImplementedError()
    
    @pixel_x_dimension.setter
    def pixel_x_dimension(self, value : int) -> None:
        '''Sets the pixel x dimension.'''
        raise NotImplementedError()
    
    @property
    def pixel_y_dimension(self) -> int:
        '''Gets the pixel y dimension.'''
        raise NotImplementedError()
    
    @pixel_y_dimension.setter
    def pixel_y_dimension(self, value : int) -> None:
        '''Sets the pixel y dimension.'''
        raise NotImplementedError()
    
    @property
    def properties(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets all the EXIF tags (including common and GPS tags).'''
        raise NotImplementedError()
    
    @properties.setter
    def properties(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets all the EXIF tags (including common and GPS tags).'''
        raise NotImplementedError()
    
    @property
    def recommended_exposure_index(self) -> int:
        '''Gets the recommended exposure index.'''
        raise NotImplementedError()
    
    @recommended_exposure_index.setter
    def recommended_exposure_index(self, value : int) -> None:
        '''Sets the recommended exposure index.'''
        raise NotImplementedError()
    
    @property
    def related_sound_file(self) -> str:
        '''Gets the related sound file.'''
        raise NotImplementedError()
    
    @related_sound_file.setter
    def related_sound_file(self, value : str) -> None:
        '''Sets the related sound file.'''
        raise NotImplementedError()
    
    @property
    def saturation(self) -> aspose.psd.exif.enums.ExifSaturation:
        '''Gets the saturation.'''
        raise NotImplementedError()
    
    @saturation.setter
    def saturation(self, value : aspose.psd.exif.enums.ExifSaturation) -> None:
        '''Sets the saturation.'''
        raise NotImplementedError()
    
    @property
    def scene_capture_type(self) -> aspose.psd.exif.enums.ExifSceneCaptureType:
        '''Gets the scene capture type.'''
        raise NotImplementedError()
    
    @scene_capture_type.setter
    def scene_capture_type(self, value : aspose.psd.exif.enums.ExifSceneCaptureType) -> None:
        '''Sets the scene capture type.'''
        raise NotImplementedError()
    
    @property
    def scene_type(self) -> int:
        '''Gets the scene type.'''
        raise NotImplementedError()
    
    @scene_type.setter
    def scene_type(self, value : int) -> None:
        '''Sets the scene type.'''
        raise NotImplementedError()
    
    @property
    def sensing_method(self) -> aspose.psd.exif.enums.ExifSensingMethod:
        '''Gets the sensing method.'''
        raise NotImplementedError()
    
    @sensing_method.setter
    def sensing_method(self, value : aspose.psd.exif.enums.ExifSensingMethod) -> None:
        '''Sets the sensing method.'''
        raise NotImplementedError()
    
    @property
    def sensitivity_type(self) -> int:
        '''Gets the sensitivity type.'''
        raise NotImplementedError()
    
    @sensitivity_type.setter
    def sensitivity_type(self, value : int) -> None:
        '''Sets the sensitivity type.'''
        raise NotImplementedError()
    
    @property
    def sharpness(self) -> int:
        '''Gets the sharpness.'''
        raise NotImplementedError()
    
    @sharpness.setter
    def sharpness(self, value : int) -> None:
        '''Sets the sharpness.'''
        raise NotImplementedError()
    
    @property
    def shutter_speed_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the shutter speed value.'''
        raise NotImplementedError()
    
    @shutter_speed_value.setter
    def shutter_speed_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the shutter speed value.'''
        raise NotImplementedError()
    
    @property
    def spatial_frequency_response(self) -> List[int]:
        '''Gets the spatial frequency response.'''
        raise NotImplementedError()
    
    @spatial_frequency_response.setter
    def spatial_frequency_response(self, value : List[int]) -> None:
        '''Sets the spatial frequency response.'''
        raise NotImplementedError()
    
    @property
    def spectral_sensitivity(self) -> str:
        '''Gets the spectral sensitivity.'''
        raise NotImplementedError()
    
    @spectral_sensitivity.setter
    def spectral_sensitivity(self, value : str) -> None:
        '''Sets the spectral sensitivity.'''
        raise NotImplementedError()
    
    @property
    def standard_output_sensitivity(self) -> int:
        '''Gets standard output sensitivity'''
        raise NotImplementedError()
    
    @standard_output_sensitivity.setter
    def standard_output_sensitivity(self, value : int) -> None:
        '''Sets standard output sensitivity'''
        raise NotImplementedError()
    
    @property
    def subject_area(self) -> List[int]:
        '''Gets the subject area.'''
        raise NotImplementedError()
    
    @subject_area.setter
    def subject_area(self, value : List[int]) -> None:
        '''Sets the subject area.'''
        raise NotImplementedError()
    
    @property
    def subject_distance(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the subject distance.'''
        raise NotImplementedError()
    
    @subject_distance.setter
    def subject_distance(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the subject distance.'''
        raise NotImplementedError()
    
    @property
    def subject_distance_range(self) -> aspose.psd.exif.enums.ExifSubjectDistanceRange:
        '''Gets the subject distance range.'''
        raise NotImplementedError()
    
    @subject_distance_range.setter
    def subject_distance_range(self, value : aspose.psd.exif.enums.ExifSubjectDistanceRange) -> None:
        '''Sets the subject distance range.'''
        raise NotImplementedError()
    
    @property
    def subject_location(self) -> List[int]:
        '''Gets the subject location.'''
        raise NotImplementedError()
    
    @subject_location.setter
    def subject_location(self, value : List[int]) -> None:
        '''Sets the subject location.'''
        raise NotImplementedError()
    
    @property
    def subsec_time(self) -> str:
        '''Gets the fractions of seconds for the DateTime tag.'''
        raise NotImplementedError()
    
    @subsec_time.setter
    def subsec_time(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTime tag.'''
        raise NotImplementedError()
    
    @property
    def subsec_time_digitized(self) -> str:
        '''Gets the fractions of seconds for the DateTimeDigitized tag.'''
        raise NotImplementedError()
    
    @subsec_time_digitized.setter
    def subsec_time_digitized(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTimeDigitized tag.'''
        raise NotImplementedError()
    
    @property
    def subsec_time_original(self) -> str:
        '''Gets the fractions of seconds for the DateTimeOriginal tag.'''
        raise NotImplementedError()
    
    @subsec_time_original.setter
    def subsec_time_original(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTimeOriginal tag.'''
        raise NotImplementedError()
    
    @property
    def user_comment(self) -> str:
        '''Gets the user comment.'''
        raise NotImplementedError()
    
    @user_comment.setter
    def user_comment(self, value : str) -> None:
        '''Sets the user comment.'''
        raise NotImplementedError()
    
    @property
    def white_balance(self) -> aspose.psd.exif.enums.ExifWhiteBalance:
        '''Gets the white balance.'''
        raise NotImplementedError()
    
    @white_balance.setter
    def white_balance(self, value : aspose.psd.exif.enums.ExifWhiteBalance) -> None:
        '''Sets the white balance.'''
        raise NotImplementedError()
    
    @property
    def white_point(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the chromaticity of the white point of the image.'''
        raise NotImplementedError()
    
    @white_point.setter
    def white_point(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the chromaticity of the white point of the image.'''
        raise NotImplementedError()
    
    @property
    def common_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags, which belong to common section. This applies only to jpeg images, in tiff format tiffOptions are being used instead'''
        raise NotImplementedError()
    
    @common_tags.setter
    def common_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags, which belong to common section. This applies only to jpeg images, in tiff format tiffOptions are being used instead'''
        raise NotImplementedError()
    
    @property
    def exif_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags which belong to EXIF section only.'''
        raise NotImplementedError()
    
    @exif_tags.setter
    def exif_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags which belong to EXIF section only.'''
        raise NotImplementedError()
    
    @property
    def gps_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags, which belong to GPS section only.'''
        raise NotImplementedError()
    
    @gps_tags.setter
    def gps_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags, which belong to GPS section only.'''
        raise NotImplementedError()
    

class JpegExifData(ExifData):
    '''EXIF data container for jpeg files.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.JpegExifData` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, exifdata : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.JpegExifData` class with data from array.
        
        :param exifdata: Array of EXIF tags together with common and GPS tags.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, common_tags : List[aspose.psd.fileformats.tiff.TiffDataType], exif_tags : List[aspose.psd.fileformats.tiff.TiffDataType], gps_tags : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.exif.JpegExifData` class with data from array.
        
        :param common_tags: The common tags.
        :param exif_tags: The EXIF tags.
        :param gps_tags: The GPS tags.'''
        raise NotImplementedError()
    
    @overload
    def remove_tag(self, tag : aspose.psd.exif.ExifProperties) -> None:
        '''Remove tag from container
        
        :param tag: The tag to remove'''
        raise NotImplementedError()
    
    @overload
    def remove_tag(self, tag_id : int) -> None:
        '''Remove tag from container
        
        :param tag_id: The tag identifier to remove.'''
        raise NotImplementedError()
    
    def serialize_exif_data(self) -> List[int]:
        '''Serializes the EXIF data. Writes the tags values and contents. The most influencing size tag is Thumbnail tag contents.
        
        :returns: The serialized EXIF data.'''
        raise NotImplementedError()
    
    @property
    def is_big_endian(self) -> bool:
        '''Gets a value indicating whether the stream EXIF data created from is big endian.'''
        raise NotImplementedError()
    
    @is_big_endian.setter
    def is_big_endian(self, value : bool) -> None:
        '''Sets a value indicating whether the stream EXIF data created from is big endian.'''
        raise NotImplementedError()
    
    @property
    def aperture_value(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the aperture value.'''
        raise NotImplementedError()
    
    @aperture_value.setter
    def aperture_value(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the aperture value.'''
        raise NotImplementedError()
    
    @property
    def body_serial_number(self) -> str:
        '''Gets camera body serial number.'''
        raise NotImplementedError()
    
    @body_serial_number.setter
    def body_serial_number(self, value : str) -> None:
        '''Sets camera body serial number.'''
        raise NotImplementedError()
    
    @property
    def brightness_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the brightness value.'''
        raise NotImplementedError()
    
    @brightness_value.setter
    def brightness_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the brightness value.'''
        raise NotImplementedError()
    
    @property
    def cfa_pattern(self) -> List[int]:
        '''Gets the CFA pattern.'''
        raise NotImplementedError()
    
    @cfa_pattern.setter
    def cfa_pattern(self, value : List[int]) -> None:
        '''Sets the CFA pattern.'''
        raise NotImplementedError()
    
    @property
    def camera_owner_name(self) -> str:
        '''Gets camera owner name'''
        raise NotImplementedError()
    
    @camera_owner_name.setter
    def camera_owner_name(self, value : str) -> None:
        '''Sets camera owner name'''
        raise NotImplementedError()
    
    @property
    def color_space(self) -> aspose.psd.exif.enums.ExifColorSpace:
        '''Gets the color space.'''
        raise NotImplementedError()
    
    @color_space.setter
    def color_space(self, value : aspose.psd.exif.enums.ExifColorSpace) -> None:
        '''Sets the color space.'''
        raise NotImplementedError()
    
    @property
    def components_configuration(self) -> List[int]:
        '''Gets the components configuration.'''
        raise NotImplementedError()
    
    @components_configuration.setter
    def components_configuration(self, value : List[int]) -> None:
        '''Sets the components configuration.'''
        raise NotImplementedError()
    
    @property
    def compressed_bits_per_pixel(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the compressed bits per pixel.'''
        raise NotImplementedError()
    
    @compressed_bits_per_pixel.setter
    def compressed_bits_per_pixel(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the compressed bits per pixel.'''
        raise NotImplementedError()
    
    @property
    def contrast(self) -> aspose.psd.exif.enums.ExifContrast:
        '''Gets the contrast.'''
        raise NotImplementedError()
    
    @contrast.setter
    def contrast(self, value : aspose.psd.exif.enums.ExifContrast) -> None:
        '''Sets the contrast.'''
        raise NotImplementedError()
    
    @property
    def custom_rendered(self) -> aspose.psd.exif.enums.ExifCustomRendered:
        '''Gets the custom rendered.'''
        raise NotImplementedError()
    
    @custom_rendered.setter
    def custom_rendered(self, value : aspose.psd.exif.enums.ExifCustomRendered) -> None:
        '''Sets the custom rendered.'''
        raise NotImplementedError()
    
    @property
    def date_time_digitized(self) -> str:
        '''Gets the date time digitized.'''
        raise NotImplementedError()
    
    @date_time_digitized.setter
    def date_time_digitized(self, value : str) -> None:
        '''Sets the date time digitized.'''
        raise NotImplementedError()
    
    @property
    def date_time_original(self) -> str:
        '''Gets the date time original.'''
        raise NotImplementedError()
    
    @date_time_original.setter
    def date_time_original(self, value : str) -> None:
        '''Sets the date time original.'''
        raise NotImplementedError()
    
    @property
    def device_setting_description(self) -> List[int]:
        '''Gets device settings description'''
        raise NotImplementedError()
    
    @device_setting_description.setter
    def device_setting_description(self, value : List[int]) -> None:
        '''Sets device settings description'''
        raise NotImplementedError()
    
    @property
    def digital_zoom_ratio(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the digital zoom ratio.'''
        raise NotImplementedError()
    
    @digital_zoom_ratio.setter
    def digital_zoom_ratio(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the digital zoom ratio.'''
        raise NotImplementedError()
    
    @property
    def exif_version(self) -> List[int]:
        '''Gets the EXIF version.'''
        raise NotImplementedError()
    
    @exif_version.setter
    def exif_version(self, value : List[int]) -> None:
        '''Sets the EXIF version.'''
        raise NotImplementedError()
    
    @property
    def exposure_bias_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the exposure bias value.'''
        raise NotImplementedError()
    
    @exposure_bias_value.setter
    def exposure_bias_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the exposure bias value.'''
        raise NotImplementedError()
    
    @property
    def exposure_index(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the exposure index.'''
        raise NotImplementedError()
    
    @exposure_index.setter
    def exposure_index(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the exposure index.'''
        raise NotImplementedError()
    
    @property
    def exposure_mode(self) -> aspose.psd.exif.enums.ExifExposureMode:
        '''Gets the exposure mode.'''
        raise NotImplementedError()
    
    @exposure_mode.setter
    def exposure_mode(self, value : aspose.psd.exif.enums.ExifExposureMode) -> None:
        '''Sets the exposure mode.'''
        raise NotImplementedError()
    
    @property
    def exposure_program(self) -> aspose.psd.exif.enums.ExifExposureProgram:
        '''Gets the exposure program.'''
        raise NotImplementedError()
    
    @exposure_program.setter
    def exposure_program(self, value : aspose.psd.exif.enums.ExifExposureProgram) -> None:
        '''Sets the exposure program.'''
        raise NotImplementedError()
    
    @property
    def exposure_time(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the exposure time.'''
        raise NotImplementedError()
    
    @exposure_time.setter
    def exposure_time(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the exposure time.'''
        raise NotImplementedError()
    
    @property
    def f_number(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the F-number.'''
        raise NotImplementedError()
    
    @f_number.setter
    def f_number(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the F-number.'''
        raise NotImplementedError()
    
    @property
    def file_source(self) -> aspose.psd.exif.enums.ExifFileSource:
        '''Gets the file source type.'''
        raise NotImplementedError()
    
    @file_source.setter
    def file_source(self, value : aspose.psd.exif.enums.ExifFileSource) -> None:
        '''Sets the file source type.'''
        raise NotImplementedError()
    
    @property
    def flash(self) -> aspose.psd.exif.enums.ExifFlash:
        '''Gets the flash.'''
        raise NotImplementedError()
    
    @flash.setter
    def flash(self, value : aspose.psd.exif.enums.ExifFlash) -> None:
        '''Sets the flash.'''
        raise NotImplementedError()
    
    @property
    def flash_energy(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the flash energy.'''
        raise NotImplementedError()
    
    @flash_energy.setter
    def flash_energy(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the flash energy.'''
        raise NotImplementedError()
    
    @property
    def flashpix_version(self) -> List[int]:
        '''Gets the flash pix version.'''
        raise NotImplementedError()
    
    @flashpix_version.setter
    def flashpix_version(self, value : List[int]) -> None:
        '''Sets the flash pix version.'''
        raise NotImplementedError()
    
    @property
    def focal_length(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal length.'''
        raise NotImplementedError()
    
    @focal_length.setter
    def focal_length(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal length.'''
        raise NotImplementedError()
    
    @property
    def focal_length_in_35_mm_film(self) -> int:
        '''Gets the focal length in 35 mm film.'''
        raise NotImplementedError()
    
    @focal_length_in_35_mm_film.setter
    def focal_length_in_35_mm_film(self, value : int) -> None:
        '''Sets the focal length in 35 mm film.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_resolution_unit(self) -> aspose.psd.exif.enums.ExifUnit:
        '''Gets the focal plane resolution unit.'''
        raise NotImplementedError()
    
    @focal_plane_resolution_unit.setter
    def focal_plane_resolution_unit(self, value : aspose.psd.exif.enums.ExifUnit) -> None:
        '''Sets the focal plane resolution unit.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_x_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal plane x resolution.'''
        raise NotImplementedError()
    
    @focal_plane_x_resolution.setter
    def focal_plane_x_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal plane x resolution.'''
        raise NotImplementedError()
    
    @property
    def focal_plane_y_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the focal plane y resolution.'''
        raise NotImplementedError()
    
    @focal_plane_y_resolution.setter
    def focal_plane_y_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the focal plane y resolution.'''
        raise NotImplementedError()
    
    @property
    def gps_altitude(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS altitude.'''
        raise NotImplementedError()
    
    @gps_altitude.setter
    def gps_altitude(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS altitude.'''
        raise NotImplementedError()
    
    @property
    def gps_altitude_ref(self) -> aspose.psd.exif.enums.ExifGPSAltitudeRef:
        '''Gets the GPS altitude used as the reference altitude.'''
        raise NotImplementedError()
    
    @gps_altitude_ref.setter
    def gps_altitude_ref(self, value : aspose.psd.exif.enums.ExifGPSAltitudeRef) -> None:
        '''Sets the GPS altitude used as the reference altitude.'''
        raise NotImplementedError()
    
    @property
    def gps_area_information(self) -> List[int]:
        '''Gets the GPS area information.'''
        raise NotImplementedError()
    
    @gps_area_information.setter
    def gps_area_information(self, value : List[int]) -> None:
        '''Sets the GPS area information.'''
        raise NotImplementedError()
    
    @property
    def gpsdop(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS DOP (data degree of precision).'''
        raise NotImplementedError()
    
    @gpsdop.setter
    def gpsdop(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS DOP (data degree of precision).'''
        raise NotImplementedError()
    
    @property
    def gps_dest_bearing(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS bearing to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_bearing.setter
    def gps_dest_bearing(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS bearing to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_bearing_ref(self) -> str:
        '''Gets the GPS reference used for giving the bearing to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_bearing_ref.setter
    def gps_dest_bearing_ref(self, value : str) -> None:
        '''Sets the GPS reference used for giving the bearing to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_distance(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS distance to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_distance.setter
    def gps_dest_distance(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS distance to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_distance_ref(self) -> str:
        '''Gets the GPS unit used to express the distance to the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_distance_ref.setter
    def gps_dest_distance_ref(self, value : str) -> None:
        '''Sets the GPS unit used to express the distance to the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_latitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS latitude of the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_latitude.setter
    def gps_dest_latitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS latitude of the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_latitude_ref(self) -> str:
        '''Gets the GPS value which indicates whether the latitude of the destination point is north or south latitude.'''
        raise NotImplementedError()
    
    @gps_dest_latitude_ref.setter
    def gps_dest_latitude_ref(self, value : str) -> None:
        '''Sets the GPS value which indicates whether the latitude of the destination point is north or south latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_longitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS longitude of the destination point.'''
        raise NotImplementedError()
    
    @gps_dest_longitude.setter
    def gps_dest_longitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS longitude of the destination point.'''
        raise NotImplementedError()
    
    @property
    def gps_dest_longitude_ref(self) -> str:
        '''Gets the GPS value which indicates whether the longitude of the destination point is east or west longitude.'''
        raise NotImplementedError()
    
    @gps_dest_longitude_ref.setter
    def gps_dest_longitude_ref(self, value : str) -> None:
        '''Sets the GPS value which indicates whether the longitude of the destination point is east or west longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_differential(self) -> int:
        '''Gets a GPS value which indicates whether differential correction is applied to the GPS receiver.'''
        raise NotImplementedError()
    
    @gps_differential.setter
    def gps_differential(self, value : int) -> None:
        '''Sets a GPS value which indicates whether differential correction is applied to the GPS receiver.'''
        raise NotImplementedError()
    
    @property
    def gps_img_direction(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the GPS direction of the image when it was captured.'''
        raise NotImplementedError()
    
    @gps_img_direction.setter
    def gps_img_direction(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the GPS direction of the image when it was captured.'''
        raise NotImplementedError()
    
    @property
    def gps_img_direction_ref(self) -> str:
        '''Gets the GPS reference for giving the direction of the image when it is captured.'''
        raise NotImplementedError()
    
    @gps_img_direction_ref.setter
    def gps_img_direction_ref(self, value : str) -> None:
        '''Sets the GPS reference for giving the direction of the image when it is captured.'''
        raise NotImplementedError()
    
    @property
    def gps_date_stamp(self) -> str:
        '''Gets the GPS character string recording date and time information relative to UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @gps_date_stamp.setter
    def gps_date_stamp(self, value : str) -> None:
        '''Sets the GPS character string recording date and time information relative to UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @property
    def gps_latitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS latitude.'''
        raise NotImplementedError()
    
    @gps_latitude.setter
    def gps_latitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_latitude_ref(self) -> str:
        '''Gets the GPS latitude is north or south latitude.'''
        raise NotImplementedError()
    
    @gps_latitude_ref.setter
    def gps_latitude_ref(self, value : str) -> None:
        '''Sets the GPS latitude is north or south latitude.'''
        raise NotImplementedError()
    
    @property
    def gps_longitude(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS longitude.'''
        raise NotImplementedError()
    
    @gps_longitude.setter
    def gps_longitude(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_longitude_ref(self) -> str:
        '''Gets the GPS longitude is east or west longitude.'''
        raise NotImplementedError()
    
    @gps_longitude_ref.setter
    def gps_longitude_ref(self, value : str) -> None:
        '''Sets the GPS longitude is east or west longitude.'''
        raise NotImplementedError()
    
    @property
    def gps_map_datum(self) -> str:
        '''Gets the GPS geodetic survey data used by the GPS receiver.'''
        raise NotImplementedError()
    
    @gps_map_datum.setter
    def gps_map_datum(self, value : str) -> None:
        '''Sets the GPS geodetic survey data used by the GPS receiver.'''
        raise NotImplementedError()
    
    @property
    def gps_measure_mode(self) -> str:
        '''Gets the GPS measurement mode.'''
        raise NotImplementedError()
    
    @gps_measure_mode.setter
    def gps_measure_mode(self, value : str) -> None:
        '''Sets the GPS measurement mode.'''
        raise NotImplementedError()
    
    @property
    def gps_processing_method(self) -> List[int]:
        '''Gets the GPS character string recording the name of the method used for location finding.'''
        raise NotImplementedError()
    
    @gps_processing_method.setter
    def gps_processing_method(self, value : List[int]) -> None:
        '''Sets the GPS character string recording the name of the method used for location finding.'''
        raise NotImplementedError()
    
    @property
    def gps_satellites(self) -> str:
        '''Gets the GPS satellites used for measurements.'''
        raise NotImplementedError()
    
    @gps_satellites.setter
    def gps_satellites(self, value : str) -> None:
        '''Sets the GPS satellites used for measurements.'''
        raise NotImplementedError()
    
    @property
    def gps_speed(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the speed of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_speed.setter
    def gps_speed(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the speed of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_speed_ref(self) -> str:
        '''Gets the unit used to express the GPS receiver speed of movement.'''
        raise NotImplementedError()
    
    @gps_speed_ref.setter
    def gps_speed_ref(self, value : str) -> None:
        '''Sets the unit used to express the GPS receiver speed of movement.'''
        raise NotImplementedError()
    
    @property
    def gps_status(self) -> str:
        '''Gets the status of the GPS receiver when the image is recorded.'''
        raise NotImplementedError()
    
    @gps_status.setter
    def gps_status(self, value : str) -> None:
        '''Sets the status of the GPS receiver when the image is recorded.'''
        raise NotImplementedError()
    
    @property
    def gps_timestamp(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the GPS time as UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @gps_timestamp.setter
    def gps_timestamp(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the GPS time as UTC (Coordinated Universal Time).'''
        raise NotImplementedError()
    
    @property
    def gps_track(self) -> str:
        '''Gets direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_track.setter
    def gps_track(self, value : str) -> None:
        '''Sets direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_track_ref(self) -> str:
        '''Gets the reference for giving the direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @gps_track_ref.setter
    def gps_track_ref(self, value : str) -> None:
        '''Sets the reference for giving the direction of GPS receiver movement.'''
        raise NotImplementedError()
    
    @property
    def gps_version_id(self) -> List[int]:
        '''Gets the GPS version identifier.'''
        raise NotImplementedError()
    
    @gps_version_id.setter
    def gps_version_id(self, value : List[int]) -> None:
        '''Sets the GPS version identifier.'''
        raise NotImplementedError()
    
    @property
    def gain_control(self) -> aspose.psd.exif.enums.ExifGainControl:
        '''Gets the degree of overall image gain adjustment.'''
        raise NotImplementedError()
    
    @gain_control.setter
    def gain_control(self, value : aspose.psd.exif.enums.ExifGainControl) -> None:
        '''Sets the degree of overall image gain adjustment.'''
        raise NotImplementedError()
    
    @property
    def gamma(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the gamma.'''
        raise NotImplementedError()
    
    @gamma.setter
    def gamma(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the gamma.'''
        raise NotImplementedError()
    
    @property
    def iso_speed(self) -> int:
        '''Gets ISO speed'''
        raise NotImplementedError()
    
    @iso_speed.setter
    def iso_speed(self, value : int) -> None:
        '''Sets ISO speed'''
        raise NotImplementedError()
    
    @property
    def iso_speed_latitude_yyy(self) -> int:
        '''Gets the ISO speed latitude yyy value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @iso_speed_latitude_yyy.setter
    def iso_speed_latitude_yyy(self, value : int) -> None:
        '''Sets the ISO speed latitude yyy value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @property
    def iso_speed_latitude_zzz(self) -> int:
        '''Gets the ISO speed latitude zzz value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @iso_speed_latitude_zzz.setter
    def iso_speed_latitude_zzz(self, value : int) -> None:
        '''Sets the ISO speed latitude zzz value of a camera or input device that is defined in ISO 12232.'''
        raise NotImplementedError()
    
    @property
    def photographic_sensitivity(self) -> int:
        '''Gets the photographic sensitivity.'''
        raise NotImplementedError()
    
    @photographic_sensitivity.setter
    def photographic_sensitivity(self, value : int) -> None:
        '''Sets the photographic sensitivity.'''
        raise NotImplementedError()
    
    @property
    def image_unique_id(self) -> str:
        '''Gets the image unique identifier.'''
        raise NotImplementedError()
    
    @image_unique_id.setter
    def image_unique_id(self, value : str) -> None:
        '''Sets the image unique identifier.'''
        raise NotImplementedError()
    
    @property
    def lens_make(self) -> str:
        '''Gets the maker of lens.'''
        raise NotImplementedError()
    
    @lens_make.setter
    def lens_make(self, value : str) -> None:
        '''Sets the maker of lens.'''
        raise NotImplementedError()
    
    @property
    def lens_model(self) -> str:
        '''Gets the lens model.'''
        raise NotImplementedError()
    
    @lens_model.setter
    def lens_model(self, value : str) -> None:
        '''Sets the lens model.'''
        raise NotImplementedError()
    
    @property
    def lens_serial_number(self) -> str:
        '''Gets the lens serial number.'''
        raise NotImplementedError()
    
    @lens_serial_number.setter
    def lens_serial_number(self, value : str) -> None:
        '''Sets the lens serial number.'''
        raise NotImplementedError()
    
    @property
    def lens_specification(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the lens specification'''
        raise NotImplementedError()
    
    @lens_specification.setter
    def lens_specification(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the lens specification'''
        raise NotImplementedError()
    
    @property
    def light_source(self) -> aspose.psd.exif.enums.ExifLightSource:
        '''Gets the light source.'''
        raise NotImplementedError()
    
    @light_source.setter
    def light_source(self, value : aspose.psd.exif.enums.ExifLightSource) -> None:
        '''Sets the light source.'''
        raise NotImplementedError()
    
    @property
    def maker_note_data(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets the maker note data.'''
        raise NotImplementedError()
    
    @property
    def maker_note_raw_data(self) -> List[int]:
        '''Gets the maker note raw data.'''
        raise NotImplementedError()
    
    @maker_note_raw_data.setter
    def maker_note_raw_data(self, value : List[int]) -> None:
        '''Sets the maker note raw data.'''
        raise NotImplementedError()
    
    @property
    def max_aperture_value(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the maximum aperture value.'''
        raise NotImplementedError()
    
    @max_aperture_value.setter
    def max_aperture_value(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the maximum aperture value.'''
        raise NotImplementedError()
    
    @property
    def metering_mode(self) -> aspose.psd.exif.enums.ExifMeteringMode:
        '''Gets the metering mode.'''
        raise NotImplementedError()
    
    @metering_mode.setter
    def metering_mode(self, value : aspose.psd.exif.enums.ExifMeteringMode) -> None:
        '''Sets the metering mode.'''
        raise NotImplementedError()
    
    @property
    def oecf(self) -> List[int]:
        '''Gets the Opto-Electric Conversion Function (OECF) specified in ISO 14524.'''
        raise NotImplementedError()
    
    @oecf.setter
    def oecf(self, value : List[int]) -> None:
        '''Sets the Opto-Electric Conversion Function (OECF) specified in ISO 14524.'''
        raise NotImplementedError()
    
    @property
    def pixel_x_dimension(self) -> int:
        '''Gets the pixel x dimension.'''
        raise NotImplementedError()
    
    @pixel_x_dimension.setter
    def pixel_x_dimension(self, value : int) -> None:
        '''Sets the pixel x dimension.'''
        raise NotImplementedError()
    
    @property
    def pixel_y_dimension(self) -> int:
        '''Gets the pixel y dimension.'''
        raise NotImplementedError()
    
    @pixel_y_dimension.setter
    def pixel_y_dimension(self, value : int) -> None:
        '''Sets the pixel y dimension.'''
        raise NotImplementedError()
    
    @property
    def properties(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets all the EXIF tags (including common and GPS tags).'''
        raise NotImplementedError()
    
    @properties.setter
    def properties(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets all the EXIF tags (including common and GPS tags).'''
        raise NotImplementedError()
    
    @property
    def recommended_exposure_index(self) -> int:
        '''Gets the recommended exposure index.'''
        raise NotImplementedError()
    
    @recommended_exposure_index.setter
    def recommended_exposure_index(self, value : int) -> None:
        '''Sets the recommended exposure index.'''
        raise NotImplementedError()
    
    @property
    def related_sound_file(self) -> str:
        '''Gets the related sound file.'''
        raise NotImplementedError()
    
    @related_sound_file.setter
    def related_sound_file(self, value : str) -> None:
        '''Sets the related sound file.'''
        raise NotImplementedError()
    
    @property
    def saturation(self) -> aspose.psd.exif.enums.ExifSaturation:
        '''Gets the saturation.'''
        raise NotImplementedError()
    
    @saturation.setter
    def saturation(self, value : aspose.psd.exif.enums.ExifSaturation) -> None:
        '''Sets the saturation.'''
        raise NotImplementedError()
    
    @property
    def scene_capture_type(self) -> aspose.psd.exif.enums.ExifSceneCaptureType:
        '''Gets the scene capture type.'''
        raise NotImplementedError()
    
    @scene_capture_type.setter
    def scene_capture_type(self, value : aspose.psd.exif.enums.ExifSceneCaptureType) -> None:
        '''Sets the scene capture type.'''
        raise NotImplementedError()
    
    @property
    def scene_type(self) -> int:
        '''Gets the scene type.'''
        raise NotImplementedError()
    
    @scene_type.setter
    def scene_type(self, value : int) -> None:
        '''Sets the scene type.'''
        raise NotImplementedError()
    
    @property
    def sensing_method(self) -> aspose.psd.exif.enums.ExifSensingMethod:
        '''Gets the sensing method.'''
        raise NotImplementedError()
    
    @sensing_method.setter
    def sensing_method(self, value : aspose.psd.exif.enums.ExifSensingMethod) -> None:
        '''Sets the sensing method.'''
        raise NotImplementedError()
    
    @property
    def sensitivity_type(self) -> int:
        '''Gets the sensitivity type.'''
        raise NotImplementedError()
    
    @sensitivity_type.setter
    def sensitivity_type(self, value : int) -> None:
        '''Sets the sensitivity type.'''
        raise NotImplementedError()
    
    @property
    def sharpness(self) -> int:
        '''Gets the sharpness.'''
        raise NotImplementedError()
    
    @sharpness.setter
    def sharpness(self, value : int) -> None:
        '''Sets the sharpness.'''
        raise NotImplementedError()
    
    @property
    def shutter_speed_value(self) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Gets the shutter speed value.'''
        raise NotImplementedError()
    
    @shutter_speed_value.setter
    def shutter_speed_value(self, value : aspose.psd.fileformats.tiff.TiffSRational) -> None:
        '''Sets the shutter speed value.'''
        raise NotImplementedError()
    
    @property
    def spatial_frequency_response(self) -> List[int]:
        '''Gets the spatial frequency response.'''
        raise NotImplementedError()
    
    @spatial_frequency_response.setter
    def spatial_frequency_response(self, value : List[int]) -> None:
        '''Sets the spatial frequency response.'''
        raise NotImplementedError()
    
    @property
    def spectral_sensitivity(self) -> str:
        '''Gets the spectral sensitivity.'''
        raise NotImplementedError()
    
    @spectral_sensitivity.setter
    def spectral_sensitivity(self, value : str) -> None:
        '''Sets the spectral sensitivity.'''
        raise NotImplementedError()
    
    @property
    def standard_output_sensitivity(self) -> int:
        '''Gets standard output sensitivity'''
        raise NotImplementedError()
    
    @standard_output_sensitivity.setter
    def standard_output_sensitivity(self, value : int) -> None:
        '''Sets standard output sensitivity'''
        raise NotImplementedError()
    
    @property
    def subject_area(self) -> List[int]:
        '''Gets the subject area.'''
        raise NotImplementedError()
    
    @subject_area.setter
    def subject_area(self, value : List[int]) -> None:
        '''Sets the subject area.'''
        raise NotImplementedError()
    
    @property
    def subject_distance(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the subject distance.'''
        raise NotImplementedError()
    
    @subject_distance.setter
    def subject_distance(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the subject distance.'''
        raise NotImplementedError()
    
    @property
    def subject_distance_range(self) -> aspose.psd.exif.enums.ExifSubjectDistanceRange:
        '''Gets the subject distance range.'''
        raise NotImplementedError()
    
    @subject_distance_range.setter
    def subject_distance_range(self, value : aspose.psd.exif.enums.ExifSubjectDistanceRange) -> None:
        '''Sets the subject distance range.'''
        raise NotImplementedError()
    
    @property
    def subject_location(self) -> List[int]:
        '''Gets the subject location.'''
        raise NotImplementedError()
    
    @subject_location.setter
    def subject_location(self, value : List[int]) -> None:
        '''Sets the subject location.'''
        raise NotImplementedError()
    
    @property
    def subsec_time(self) -> str:
        '''Gets the fractions of seconds for the DateTime tag.'''
        raise NotImplementedError()
    
    @subsec_time.setter
    def subsec_time(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTime tag.'''
        raise NotImplementedError()
    
    @property
    def subsec_time_digitized(self) -> str:
        '''Gets the fractions of seconds for the DateTimeDigitized tag.'''
        raise NotImplementedError()
    
    @subsec_time_digitized.setter
    def subsec_time_digitized(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTimeDigitized tag.'''
        raise NotImplementedError()
    
    @property
    def subsec_time_original(self) -> str:
        '''Gets the fractions of seconds for the DateTimeOriginal tag.'''
        raise NotImplementedError()
    
    @subsec_time_original.setter
    def subsec_time_original(self, value : str) -> None:
        '''Sets the fractions of seconds for the DateTimeOriginal tag.'''
        raise NotImplementedError()
    
    @property
    def user_comment(self) -> str:
        '''Gets the user comment.'''
        raise NotImplementedError()
    
    @user_comment.setter
    def user_comment(self, value : str) -> None:
        '''Sets the user comment.'''
        raise NotImplementedError()
    
    @property
    def white_balance(self) -> aspose.psd.exif.enums.ExifWhiteBalance:
        '''Gets the white balance.'''
        raise NotImplementedError()
    
    @white_balance.setter
    def white_balance(self, value : aspose.psd.exif.enums.ExifWhiteBalance) -> None:
        '''Sets the white balance.'''
        raise NotImplementedError()
    
    @property
    def white_point(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the chromaticity of the white point of the image.'''
        raise NotImplementedError()
    
    @white_point.setter
    def white_point(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the chromaticity of the white point of the image.'''
        raise NotImplementedError()
    
    @property
    def common_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags, which belong to common section. This applies only to jpeg images, in tiff format tiffOptions are being used instead'''
        raise NotImplementedError()
    
    @common_tags.setter
    def common_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags, which belong to common section. This applies only to jpeg images, in tiff format tiffOptions are being used instead'''
        raise NotImplementedError()
    
    @property
    def exif_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags which belong to EXIF section only.'''
        raise NotImplementedError()
    
    @exif_tags.setter
    def exif_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags which belong to EXIF section only.'''
        raise NotImplementedError()
    
    @property
    def gps_tags(self) -> List[aspose.psd.fileformats.tiff.TiffDataType]:
        '''Gets tags, which belong to GPS section only.'''
        raise NotImplementedError()
    
    @gps_tags.setter
    def gps_tags(self, value : List[aspose.psd.fileformats.tiff.TiffDataType]) -> None:
        '''Sets tags, which belong to GPS section only.'''
        raise NotImplementedError()
    
    @property
    def artist(self) -> str:
        '''Gets the artist.'''
        raise NotImplementedError()
    
    @artist.setter
    def artist(self, value : str) -> None:
        '''Sets the artist.'''
        raise NotImplementedError()
    
    @property
    def bits_per_sample(self) -> List[int]:
        '''Gets the bits per sample.'''
        raise NotImplementedError()
    
    @bits_per_sample.setter
    def bits_per_sample(self, value : List[int]) -> None:
        '''Sets the bits per sample.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> int:
        '''Gets the compression.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : int) -> None:
        '''Sets the compression.'''
        raise NotImplementedError()
    
    @property
    def copyright(self) -> str:
        '''Gets the copyright.'''
        raise NotImplementedError()
    
    @copyright.setter
    def copyright(self, value : str) -> None:
        '''Sets the copyright.'''
        raise NotImplementedError()
    
    @property
    def date_time(self) -> str:
        '''Gets the date time.'''
        raise NotImplementedError()
    
    @date_time.setter
    def date_time(self, value : str) -> None:
        '''Sets the date time.'''
        raise NotImplementedError()
    
    @property
    def image_description(self) -> str:
        '''Gets the image description.'''
        raise NotImplementedError()
    
    @image_description.setter
    def image_description(self, value : str) -> None:
        '''Sets the image description.'''
        raise NotImplementedError()
    
    @property
    def image_length(self) -> int:
        '''Gets the image length.'''
        raise NotImplementedError()
    
    @image_length.setter
    def image_length(self, value : int) -> None:
        '''Sets the image length.'''
        raise NotImplementedError()
    
    @property
    def image_width(self) -> int:
        '''Gets the image width.'''
        raise NotImplementedError()
    
    @image_width.setter
    def image_width(self, value : int) -> None:
        '''Sets the image width.'''
        raise NotImplementedError()
    
    @property
    def make(self) -> str:
        '''Gets the manufacturer of the recording equipment.'''
        raise NotImplementedError()
    
    @make.setter
    def make(self, value : str) -> None:
        '''Sets the manufacturer of the recording equipment.'''
        raise NotImplementedError()
    
    @property
    def model(self) -> str:
        '''Gets the model.'''
        raise NotImplementedError()
    
    @model.setter
    def model(self, value : str) -> None:
        '''Sets the model.'''
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.psd.exif.enums.ExifOrientation:
        '''Gets the orientation.'''
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.psd.exif.enums.ExifOrientation) -> None:
        '''Sets the orientation.'''
        raise NotImplementedError()
    
    @property
    def photometric_interpretation(self) -> int:
        '''Gets the photometric interpretation.'''
        raise NotImplementedError()
    
    @photometric_interpretation.setter
    def photometric_interpretation(self, value : int) -> None:
        '''Sets the photometric interpretation.'''
        raise NotImplementedError()
    
    @property
    def planar_configuration(self) -> int:
        '''Gets the planar configuration.'''
        raise NotImplementedError()
    
    @planar_configuration.setter
    def planar_configuration(self, value : int) -> None:
        '''Sets the planar configuration.'''
        raise NotImplementedError()
    
    @property
    def primary_chromaticities(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the chromaticity of the three primary colors of the image.'''
        raise NotImplementedError()
    
    @primary_chromaticities.setter
    def primary_chromaticities(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the chromaticity of the three primary colors of the image.'''
        raise NotImplementedError()
    
    @property
    def reference_black_white(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the reference black white.'''
        raise NotImplementedError()
    
    @reference_black_white.setter
    def reference_black_white(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the reference black white.'''
        raise NotImplementedError()
    
    @property
    def resolution_unit(self) -> aspose.psd.exif.enums.ExifUnit:
        '''Gets the resolution unit.'''
        raise NotImplementedError()
    
    @resolution_unit.setter
    def resolution_unit(self, value : aspose.psd.exif.enums.ExifUnit) -> None:
        '''Sets the resolution unit.'''
        raise NotImplementedError()
    
    @property
    def samples_per_pixel(self) -> int:
        '''Gets the samples per pixel.'''
        raise NotImplementedError()
    
    @samples_per_pixel.setter
    def samples_per_pixel(self, value : int) -> None:
        '''Sets the samples per pixel.'''
        raise NotImplementedError()
    
    @property
    def software(self) -> str:
        '''Gets the software.'''
        raise NotImplementedError()
    
    @software.setter
    def software(self, value : str) -> None:
        '''Sets the software.'''
        raise NotImplementedError()
    
    @property
    def thumbnail(self) -> aspose.psd.RasterImage:
        '''Gets the thumbnail image.'''
        raise NotImplementedError()
    
    @thumbnail.setter
    def thumbnail(self, value : aspose.psd.RasterImage) -> None:
        '''Sets the thumbnail image.'''
        raise NotImplementedError()
    
    @property
    def transfer_function(self) -> List[int]:
        '''Gets the transfer function.'''
        raise NotImplementedError()
    
    @transfer_function.setter
    def transfer_function(self, value : List[int]) -> None:
        '''Sets the transfer function.'''
        raise NotImplementedError()
    
    @property
    def x_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the x resolution.'''
        raise NotImplementedError()
    
    @x_resolution.setter
    def x_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the x resolution.'''
        raise NotImplementedError()
    
    @property
    def y_cb_cr_coefficients(self) -> List[aspose.psd.fileformats.tiff.TiffRational]:
        '''Gets the matrix coefficients for transformation from RGB to YCbCr image data.'''
        raise NotImplementedError()
    
    @y_cb_cr_coefficients.setter
    def y_cb_cr_coefficients(self, value : List[aspose.psd.fileformats.tiff.TiffRational]) -> None:
        '''Sets the matrix coefficients for transformation from RGB to YCbCr image data.'''
        raise NotImplementedError()
    
    @property
    def y_cb_cr_positioning(self) -> aspose.psd.exif.enums.ExifYCbCrPositioning:
        '''Gets the position of chrominance components in relation to the luminance component.'''
        raise NotImplementedError()
    
    @y_cb_cr_positioning.setter
    def y_cb_cr_positioning(self, value : aspose.psd.exif.enums.ExifYCbCrPositioning) -> None:
        '''Sets the position of chrominance components in relation to the luminance component.'''
        raise NotImplementedError()
    
    @property
    def y_cb_cr_sub_sampling(self) -> List[int]:
        '''Gets the sampling ratio of chrominance components in relation to the luminance component.'''
        raise NotImplementedError()
    
    @y_cb_cr_sub_sampling.setter
    def y_cb_cr_sub_sampling(self, value : List[int]) -> None:
        '''Sets the sampling ratio of chrominance components in relation to the luminance component.'''
        raise NotImplementedError()
    
    @property
    def y_resolution(self) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Gets the y resolution.'''
        raise NotImplementedError()
    
    @y_resolution.setter
    def y_resolution(self, value : aspose.psd.fileformats.tiff.TiffRational) -> None:
        '''Sets the y resolution.'''
        raise NotImplementedError()
    
    @property
    def MAX_EXIF_SEGMENT_SIZE(self) -> int:
        '''The maximum EXIF segment size in bytes allowed.'''
        raise NotImplementedError()


class TiffDataTypeController:
    '''Represents general class for working with tiff data types.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    

class ExifProperties:
    '''Exif tags list'''
    
    IMAGE_WIDTH : ExifProperties
    '''The number of columns of image data, equal to the number of pixels per row.'''
    IMAGE_LENGTH : ExifProperties
    '''The number of rows of image data.'''
    BITS_PER_SAMPLE : ExifProperties
    '''The number of bits per image component. In this standard each component of the image is 8 bits, so the value for this tag is 8.'''
    COMPRESSION : ExifProperties
    '''The compression scheme used for the image data. When a primary image is JPEG compressed, this designation is not necessary and is omitted.'''
    PHOTOMETRIC_INTERPRETATION : ExifProperties
    '''The pixel composition.'''
    IMAGE_DESCRIPTION : ExifProperties
    '''A character string giving the title of the image. It may be a comment such as "1988 company picnic" or the like.'''
    MAKE : ExifProperties
    '''The manufacturer of the recording equipment. This is the manufacturer of the DSC, scanner, video digitizer or other equipment that generated the image. When the field is left blank, it is treated as unknown.'''
    MODEL : ExifProperties
    '''The model name or model number of the equipment. This is the model name or number of the DSC, scanner, video digitizer or other equipment that generated the image. When the field is left blank, it is treated as unknown.'''
    ORIENTATION : ExifProperties
    '''The image orientation viewed in terms of rows and columns.'''
    SAMPLES_PER_PIXEL : ExifProperties
    '''The number of components per pixel. Since this standard applies to RGB and YCbCr images, the value set for this tag is 3.'''
    X_RESOLUTION : ExifProperties
    '''The number of pixels per ResolutionUnit in the ImageWidth direction. When the image resolution is unknown, 72 [dpi] is designated.'''
    Y_RESOLUTION : ExifProperties
    '''The number of pixels per ResolutionUnit in the ImageLength direction. The same value as XResolution is designated.'''
    PLANAR_CONFIGURATION : ExifProperties
    '''Indicates whether pixel components are recorded in a chunky or planar format. If this field does not exist, the TIFF default of 1 (chunky) is assumed.'''
    RESOLUTION_UNIT : ExifProperties
    '''The unit for measuring XResolution and YResolution. The same unit is used for both XResolution and YResolution. If the image resolution is unknown, 2 (inches) is designated.'''
    TRANSFER_FUNCTION : ExifProperties
    '''A transfer function for the image, described in tabular style. Normally this tag is not necessary, since color space is specified in the color space information ColorSpace tag.'''
    SOFTWARE : ExifProperties
    '''This tag records the name and version of the software or firmware of the camera or image input device used to generate the image. The detailed format is not specified, but it is recommended that the example shown below be followed. When the field is left blank, it is treated as unknown.'''
    DATE_TIME : ExifProperties
    '''The date and time of image creation. In Exif standard, it is the date and time the file was changed.'''
    ARTIST : ExifProperties
    '''This tag records the name of the camera owner, photographer or image creator. The detailed format is not specified, but it is recommended that the information be written as in the example below for ease of Interoperability. When the field is left blank, it is treated as unknown. Ex.) "Camera owner, John Smith; Photographer, Michael Brown; Image creator, Ken James"'''
    WHITE_POINT : ExifProperties
    '''The chromaticity of the white point of the image. Normally this tag is not necessary, since color space is specified in the colorspace information ColorSpace tag.'''
    PRIMARY_CHROMATICITIES : ExifProperties
    '''The chromaticity of the three primary colors of the image. Normally this tag is not necessary, since colorspace is specified in the colorspace information ColorSpace tag.'''
    Y_CB_CR_COEFFICIENTS : ExifProperties
    '''The matrix coefficients for transformation from RGB to YCbCr image data.'''
    Y_CB_CR_SUB_SAMPLING : ExifProperties
    '''The sampling ratio of chrominance components in relation to the luminance component.'''
    Y_CB_CR_POSITIONING : ExifProperties
    '''The position of chrominance components in relation to the
    luminance component. This field is designated only for
    JPEG compressed data or uncompressed YCbCr data. The TIFF
    default is 1 (centered); but when Y:Cb:Cr = 4:2:2 it is
    recommended in this standard that 2 (co-sited) be used to
    record data, in order to improve the image quality when viewed
    on TV systems. When this field does not exist, the reader shall
    assume the TIFF default. In the case of Y:Cb:Cr = 4:2:0, the
    TIFF default (centered) is recommended. If the reader
    does not have the capability of supporting both kinds of
    YCbCrPositioning, it shall follow the TIFF default regardless
    of the value in this field. It is preferable that readers "
    be able to support both centered and co-sited positioning.'''
    REFERENCE_BLACK_WHITE : ExifProperties
    '''The reference black point value and reference white point
    value. No defaults are given in TIFF, but the values below are given as defaults here.
    The color space is declared
    in a color space information tag, with the default
    being the value that gives the optimal image characteristics
    Interoperability these conditions'''
    COPYRIGHT : ExifProperties
    '''Copyright information. In this standard the tag is used to
    indicate both the photographer and editor copyrights. It is
    the copyright notice of the person or organization claiming
    rights to the image. The Interoperability copyright
    statement including date and rights should be written in this
    field; e.g., "Copyright, John Smith, 19xx. All rights
    reserved.". In this standard the field records both the
    photographer and editor copyrights, with each recorded in a
    separate part of the statement. When there is a clear distinction
    between the photographer and editor copyrights, these are to be
    written in the order of photographer followed by editor copyright,
    separated by NULL (in this case since the statement also ends with
    a NULL, there are two NULL codes). When only the photographer
    copyright is given, it is terminated by one NULL code . When only
    the editor copyright is given, the photographer copyright part
    consists of one space followed by a terminating NULL code, then
    the editor copyright is given. When the field is left blank, it is
    treated as unknown.'''
    EXPOSURE_TIME : ExifProperties
    '''Exposure time, given in seconds.'''
    F_NUMBER : ExifProperties
    '''The F number.'''
    EXPOSURE_PROGRAM : ExifProperties
    '''The class of the program used by the camera to set exposure when the picture is taken.'''
    SPECTRAL_SENSITIVITY : ExifProperties
    '''Indicates the spectral sensitivity of each channel of the camera used.'''
    PHOTOGRAPHIC_SENSITIVITY : ExifProperties
    '''Indicates the ISO Speed and ISO Latitude of the camera or input device as specified in ISO 12232.'''
    OECF : ExifProperties
    '''Indicates the Opto-Electric Conversion Function (OECF) specified in ISO 14524.'''
    EXIF_VERSION : ExifProperties
    '''The exif version.'''
    DATE_TIME_ORIGINAL : ExifProperties
    '''The date and time when the original image data was generated.'''
    DATE_TIME_DIGITIZED : ExifProperties
    '''The date time digitized.'''
    COMPONENTS_CONFIGURATION : ExifProperties
    '''The components configuration.'''
    COMPRESSED_BITS_PER_PIXEL : ExifProperties
    '''Specific to compressed data; states the compressed bits per pixel.'''
    SHUTTER_SPEED_VALUE : ExifProperties
    '''The shutter speed value.'''
    APERTURE_VALUE : ExifProperties
    '''The lens aperture value.'''
    BRIGHTNESS_VALUE : ExifProperties
    '''The brightness value.'''
    EXPOSURE_BIAS_VALUE : ExifProperties
    '''The exposure bias value.'''
    MAX_APERTURE_VALUE : ExifProperties
    '''The max aperture value.'''
    SUBJECT_DISTANCE : ExifProperties
    '''The distance to the subject, given in meters.'''
    METERING_MODE : ExifProperties
    '''The metering mode.'''
    LIGHT_SOURCE : ExifProperties
    '''The kind light source.'''
    FLASH : ExifProperties
    '''Indicates the status of flash when the image was shot.'''
    FOCAL_LENGTH : ExifProperties
    '''The actual focal length of the lens, in mm.'''
    SUBJECT_AREA : ExifProperties
    '''This tag indicates the location and area of the main subject in the overall scene.'''
    MAKER_NOTE : ExifProperties
    '''A tag for manufacturers of Exif writers to record any desired information. The contents are up to the manufacturer, but this tag should not be used for any other than its intended purpose.'''
    USER_COMMENT : ExifProperties
    '''A tag for Exif users to write keywords or comments on the image besides those in ImageDescription, and without the character code limitations of the ImageDescription tag.'''
    SUBSEC_TIME : ExifProperties
    '''A tag used to record fractions of seconds for the DateTime tag.'''
    SUBSEC_TIME_ORIGINAL : ExifProperties
    '''A tag used to record fractions of seconds for the DateTimeOriginal tag.'''
    SUBSEC_TIME_DIGITIZED : ExifProperties
    '''A tag used to record fractions of seconds for the DateTimeDigitized tag.'''
    FLASHPIX_VERSION : ExifProperties
    '''The Flashpix format version supported by a FPXR file.'''
    COLOR_SPACE : ExifProperties
    '''The color space information tag (ColorSpace) is always recorded as the color space specifier.'''
    RELATED_SOUND_FILE : ExifProperties
    '''The related sound file.'''
    FLASH_ENERGY : ExifProperties
    '''Indicates the strobe energy at the time the image is captured, as measured in Beam Candle Power Seconds(BCPS).'''
    SPATIAL_FREQUENCY_RESPONSE : ExifProperties
    '''This tag records the camera or input device spatial frequency table and SFR values in the direction of image width, image height, and diagonal direction, as specified in ISO 12233.'''
    FOCAL_PLANE_X_RESOLUTION : ExifProperties
    '''Indicates the number of pixels in the image width (X) direction per FocalPlaneResolutionUnit on the camera focal plane.'''
    FOCAL_PLANE_Y_RESOLUTION : ExifProperties
    '''Indicates the number of pixels in the image height (Y) direction per FocalPlaneResolutionUnit on the camera focal plane.'''
    FOCAL_PLANE_RESOLUTION_UNIT : ExifProperties
    '''Indicates the unit for measuring FocalPlaneXResolution and FocalPlaneYResolution. This value is the same as the ResolutionUnit.'''
    SUBJECT_LOCATION : ExifProperties
    '''Indicates the location of the main subject in the scene. The value of this tag represents the pixel at the center of the main subject relative to the left edge, prior to rotation processing as per the Rotation tag.'''
    EXPOSURE_INDEX : ExifProperties
    '''Indicates the exposure index selected on the camera or input device at the time the image is captured.'''
    SENSING_METHOD : ExifProperties
    '''Indicates the image sensor type on the camera or input device.'''
    FILE_SOURCE : ExifProperties
    '''The file source.'''
    SCENE_TYPE : ExifProperties
    '''Indicates the type of scene. If a DSC recorded the image, this tag value shall always be set to 1, indicating that the image was directly photographed.'''
    CFA_PATTERN : ExifProperties
    '''Indicates the color filter array (CFA) geometric pattern of the image sensor when a one-chip color area sensor is used. It does not apply to all sensing methods.'''
    CUSTOM_RENDERED : ExifProperties
    '''This tag indicates the use of special processing on image data, such as rendering geared to output. When special processing is performed, the reader is expected to disable or minimize any further processing.'''
    EXPOSURE_MODE : ExifProperties
    '''This tag indicates the exposure mode set when the image was shot. In auto-bracketing mode, the camera shoots a series of frames of the same scene at different exposure settings.'''
    WHITE_BALANCE : ExifProperties
    '''This tag indicates the white balance mode set when the image was shot.'''
    DIGITAL_ZOOM_RATIO : ExifProperties
    '''This tag indicates the digital zoom ratio when the image was shot. If the numerator of the recorded value is 0, this indicates that digital zoom was not used.'''
    FOCAL_LENGTH_IN_35_MM_FILM : ExifProperties
    '''This tag indicates the equivalent focal length assuming a 35mm film camera, in mm. A value of 0 means the focal length is unknown. Note that this tag differs from the FocalLength tag.'''
    SCENE_CAPTURE_TYPE : ExifProperties
    '''This tag indicates the type of scene that was shot. It can also be used to record the mode in which the image was shot.'''
    GAIN_CONTROL : ExifProperties
    '''This tag indicates the degree of overall image gain adjustment.'''
    CONTRAST : ExifProperties
    '''This tag indicates the direction of contrast processing applied by the camera when the image was shot.'''
    SATURATION : ExifProperties
    '''This tag indicates the direction of saturation processing applied by the camera when the image was shot.'''
    SHARPNESS : ExifProperties
    '''This tag indicates the direction of sharpness processing applied by the camera when the image was shot'''
    DEVICE_SETTING_DESCRIPTION : ExifProperties
    '''This tag indicates information on the picture-taking conditions of a particular camera model. The tag is used only to indicate the picture-taking conditions in the reader.'''
    SUBJECT_DISTANCE_RANGE : ExifProperties
    '''This tag indicates the distance to the subject.'''
    IMAGE_UNIQUE_ID : ExifProperties
    '''The image unique id.'''
    GPS_VERSION_ID : ExifProperties
    '''Indicates the version of GPSInfoIFD.'''
    GPS_LATITUDE_REF : ExifProperties
    '''Indicates whether the latitude is north or south latitude.'''
    GPS_LATITUDE : ExifProperties
    '''Indicates the latitude. The latitude is expressed as three RATIONAL values giving the degrees, minutes, and
    seconds, respectively. If latitude is expressed as degrees, minutes and seconds, a typical format would be
    dd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are given up to two
    decimal places, the format would be dd/1,mmmm/100,0/1.'''
    GPS_LONGITUDE_REF : ExifProperties
    '''Indicates whether the longitude is east or west longitude.'''
    GPS_LONGITUDE : ExifProperties
    '''Indicates the longitude. The longitude is expressed as three RATIONAL values giving the degrees, minutes, and
    seconds, respectively. If longitude is expressed as degrees, minutes and seconds, a typical format would be
    ddd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are given up to two
    decimal places, the format would be ddd/1,mmmm/100,0/1.'''
    GPS_ALTITUDE_REF : ExifProperties
    '''Indicates the altitude used as the reference altitude. If the reference is sea level and the altitude is above sea level,
    0 is given. If the altitude is below sea level, a value of 1 is given and the altitude is indicated as an absolute value in
    the GPSAltitude tag.'''
    GPS_ALTITUDE : ExifProperties
    '''Indicates the altitude based on the reference in GPSAltitudeRef. Altitude is expressed as one RATIONAL value.
    The reference unit is meters.'''
    GPS_TIMESTAMP : ExifProperties
    '''Indicates the time as UTC (Coordinated Universal Time). TimeStamp is expressed as three RATIONAL values
    giving the hour, minute, and second.'''
    GPS_SATELLITES : ExifProperties
    '''Indicates the GPS satellites used for measurements. This tag can be used to describe the number of satellites,
    their ID number, angle of elevation, azimuth, SNR and other information in ASCII notation. The format is not
    specified. If the GPS receiver is incapable of taking measurements, value of the tag shall be set to NULL.'''
    GPS_STATUS : ExifProperties
    '''Indicates the status of the GPS receiver when the image is recorded.'''
    GPS_MEASURE_MODE : ExifProperties
    '''Indicates the GPS measurement mode. - 2- or 3- dimensional.'''
    GPSDOP : ExifProperties
    '''Indicates the GPS DOP (data degree of precision). An HDOP value is written during two-dimensional measurement,
    and PDOP during three-dimensional measurement.'''
    GPS_SPEED_REF : ExifProperties
    '''Indicates the unit used to express the GPS receiver speed of movement. \'K\' \'M\' and \'N\' represents kilometers per
    hour, miles per hour, and knots.'''
    GPS_SPEED : ExifProperties
    '''Indicates the speed of GPS receiver movement.'''
    GPS_TRACK_REF : ExifProperties
    '''Indicates the reference for giving the direction of GPS receiver movement. \'T\' denotes true direction and \'M\' is
    magnetic direction.'''
    GPS_TRACK : ExifProperties
    '''Indicates the direction of GPS receiver movement. The range of values is from 0.00 to 359.99.'''
    GPS_IMG_DIRECTION_REF : ExifProperties
    '''Indicates the reference for giving the direction of the image when it is captured. \'T\' denotes true direction and \'M\' is
    magnetic direction.'''
    GPS_IMG_DIRECTION : ExifProperties
    '''Indicates the direction of the image when it was captured. The range of values is from 0.00 to 359.99.'''
    GPS_MAP_DATUM : ExifProperties
    '''Indicates the geodetic survey data used by the GPS receiver.'''
    GPS_DEST_LATITUDE_REF : ExifProperties
    '''Indicates whether the latitude of the destination point is north or south latitude. The ASCII value \'N\' indicates north
    latitude, and \'S\' is south latitude.'''
    GPS_DEST_LATITUDE : ExifProperties
    '''Indicates the latitude of the destination point. The latitude is expressed as three RATIONAL values giving the
    degrees, minutes, and seconds, respectively. If latitude is expressed as degrees, minutes and seconds, a typical
    format would be dd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are
    given up to two decimal places, the format would be dd/1,mmmm/100,0/1.'''
    GPS_DEST_LONGITUDE_REF : ExifProperties
    '''Indicates whether the longitude of the destination point is east or west longitude. ASCII \'E\' indicates east longitude,
    and \'W\' is west longitude.'''
    GPS_DEST_LONGITUDE : ExifProperties
    '''Indicates the longitude of the destination point. The longitude is expressed as three RATIONAL values giving the
    degrees, minutes, and seconds, respectively. If longitude is expressed as degrees, minutes and seconds, a typical
    format would be ddd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are
    given up to two decimal places, the format would be ddd/1,mmmm/100,0/1.'''
    GPS_DEST_BEARING_REF : ExifProperties
    '''Indicates the reference used for giving the bearing to the destination point. \'T\' denotes true direction and \'M\' is
    magnetic direction.'''
    GPS_DEST_BEARING : ExifProperties
    '''Indicates the bearing to the destination point. The range of values is from 0.00 to 359.99.'''
    GPS_DEST_DISTANCE_REF : ExifProperties
    '''Indicates the unit used to express the distance to the destination point. \'K\', \'M\' and \'N\' represent kilometers, miles
    and knots.'''
    GPS_DEST_DISTANCE : ExifProperties
    '''Indicates the distance to the destination point.'''
    GPS_PROCESSING_METHOD : ExifProperties
    '''A character string recording the name of the method used for location finding.
    The first byte indicates the character code used, and this is followed by the name
    of the method.'''
    GPS_AREA_INFORMATION : ExifProperties
    '''A character string recording the name of the GPS area. The first byte indicates
    the character code used, and this is followed by the name of the GPS area.'''
    GPS_DATE_STAMP : ExifProperties
    '''A character string recording date and time information relative to UTC
    (Coordinated Universal Time). The format is YYYY:MM:DD.'''
    GPS_DIFFERENTIAL : ExifProperties
    '''Indicates whether differential correction is applied to the GPS receiver.'''
    STRIP_OFFSETS : ExifProperties
    '''For each strip, the byte offset of that strip. It is recommended that this be selected so the number of strip bytes does not exceed 64 Kbytes.
    Aux tag.'''
    JPEG_INTERCHANGE_FORMAT : ExifProperties
    '''The offset to the start byte (SOI) of JPEG compressed thumbnail data. This is not used for primary image JPEG data.'''
    JPEG_INTERCHANGE_FORMAT_LENGTH : ExifProperties
    '''The number of bytes of JPEG compressed thumbnail data. This is not used for primary image JPEG data. JPEG thumbnails are not divided but are recorded as a continuous JPEG bitstream from SOI to EOI. Appn and COM markers should not be recorded. Compressed thumbnails must be recorded in no more than 64 Kbytes, including all other data to be recorded in APP1.'''
    EXIF_IFD_POINTER : ExifProperties
    '''A pointer to the Exif IFD. Interoperability, Exif IFD has the same structure as that of the IFD specified in TIFF. ordinarily, however, it does not contain image data as in the case of TIFF.'''
    GPS_IFD_POINTER : ExifProperties
    '''The gps ifd pointer.'''
    ROWS_PER_STRIP : ExifProperties
    '''The number of rows per strip. This is the number of rows in the image of one strip when an image is divided into strips.'''
    STRIP_BYTE_COUNTS : ExifProperties
    '''The total number of bytes in each strip.'''
    PIXEL_X_DIMENSION : ExifProperties
    '''Information specific to compressed data. When a compressed file is recorded, the valid width of the meaningful image shall be recorded in this tag, whether or not there is padding data or a restart marker.'''
    PIXEL_Y_DIMENSION : ExifProperties
    '''Information specific to compressed data. When a compressed file is recorded, the valid height of the meaningful image shall be recorded in this tag'''
    GAMMA : ExifProperties
    '''Gamma value'''
    SENSITIVITY_TYPE : ExifProperties
    '''Type of photographic sensitivity'''
    STANDARD_OUTPUT_SENSITIVITY : ExifProperties
    '''Indicates standard output sensitivity of camera'''
    RECOMMENDED_EXPOSURE_INDEX : ExifProperties
    '''Indicates recommended exposure index'''
    ISO_SPEED : ExifProperties
    '''Information about iso speed value as defined in ISO 12232'''
    ISO_SPEED_LATITUDE_YYY : ExifProperties
    '''This tag indicates ISO speed latitude yyy value as defined in ISO 12232'''
    ISO_SPEED_LATITUDE_ZZZ : ExifProperties
    '''This tag indicates ISO speed latitude zzz value as defined in ISO 12232'''
    CAMERA_OWNER_NAME : ExifProperties
    '''Contains camera owner name'''
    BODY_SERIAL_NUMBER : ExifProperties
    '''Contains camera body serial number'''
    LENS_MAKE : ExifProperties
    '''This tag records lens manufacturer'''
    LENS_MODEL : ExifProperties
    '''This tag records lens`s model name and model number'''
    LENS_SERIAL_NUMBER : ExifProperties
    '''This tag records the serial number of interchangable lens'''
    LENS_SPECIFICATION : ExifProperties
    '''This tag notes minimum focal length, maximum focal length, minimum F number in the minimum focal length and minimum F number in maximum focal length'''

