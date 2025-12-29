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

class AudioChannelType:
    '''Represents audio channel type.'''
    
    @property
    def mono(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the mono audio channel.'''
        raise NotImplementedError()

    @property
    def stereo(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the stereo audio channel.'''
        raise NotImplementedError()

    @property
    def audio51(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the 5.1 audio channel.'''
        raise NotImplementedError()

    @property
    def audio71(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the 7.1 audio channel.'''
        raise NotImplementedError()

    @property
    def audio_16_channel(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the 16 audio channel.'''
        raise NotImplementedError()

    @property
    def other_channel(self) -> aspose.psd.xmp.schemas.xmpdm.AudioChannelType:
        '''Gets the other channel.'''
        raise NotImplementedError()


class AudioSampleType:
    '''Represents Audio sample type in :py:class:`aspose.psd.xmp.schemas.xmpdm.XmpDynamicMediaPackage`.'''
    
    @property
    def sample_8_int(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents 8Int audio sample.'''
        raise NotImplementedError()

    @property
    def sample_16_int(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents 16Int audio sample.'''
        raise NotImplementedError()

    @property
    def sample_24_int(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents 24Int audio sample.'''
        raise NotImplementedError()

    @property
    def sample_32_int(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents 32Int audio sample.'''
        raise NotImplementedError()

    @property
    def sample_32_float(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents 32Float audio sample.'''
        raise NotImplementedError()

    @property
    def compressed(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents Compressed audio sample.'''
        raise NotImplementedError()

    @property
    def packed(self) -> aspose.psd.xmp.schemas.xmpdm.AudioSampleType:
        '''Represents Packed audio sample.'''
        raise NotImplementedError()


class ProjectLink(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents path of the project.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Returns string contained value in XMP format.
        
        :returns: Returns string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def path(self) -> str:
        '''Gets full path to the project.'''
        raise NotImplementedError()
    
    @path.setter
    def path(self, value : str) -> None:
        '''Sets full path to the project.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.psd.xmp.schemas.xmpdm.ProjectType:
        '''Gets file type.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.psd.xmp.schemas.xmpdm.ProjectType) -> None:
        '''Sets file type.'''
        raise NotImplementedError()
    

class Time(aspose.psd.xmp.types.XmpTypeBase):
    '''Representation of a time value in seconds.'''
    
    def __init__(self, scale : aspose.psd.xmp.types.derived.Rational, value : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.xmpdm.Time` class.
        
        :param scale: The scale.
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> aspose.psd.xmp.types.derived.Rational:
        '''Gets scale for the time value.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : aspose.psd.xmp.types.derived.Rational) -> None:
        '''Sets scale for the time value.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> int:
        '''Gets time value in the specified scale.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : int) -> None:
        '''Sets time value in the specified scale.'''
        raise NotImplementedError()
    

class TimeFormat:
    '''Represents time format in :py:class:`aspose.psd.xmp.schemas.xmpdm.Timecode`.'''
    
    def equals(self, other : aspose.psd.xmp.schemas.xmpdm.TimeFormat) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @property
    def timecode24(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode24.'''
        raise NotImplementedError()

    @property
    def timecode25(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode25.'''
        raise NotImplementedError()

    @property
    def drop_timecode2997(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the drop timecode2997.'''
        raise NotImplementedError()

    @property
    def non_drop_timecode2997(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the non drop timecode2997.'''
        raise NotImplementedError()

    @property
    def timecode30(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode30.'''
        raise NotImplementedError()

    @property
    def timecode50(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode50.'''
        raise NotImplementedError()

    @property
    def drop_timecode5994(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the drop timecode5994.'''
        raise NotImplementedError()

    @property
    def non_drop_timecode5994(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the non drop timecode5994.'''
        raise NotImplementedError()

    @property
    def timecode60(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode60.'''
        raise NotImplementedError()

    @property
    def timecode23976(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the timecode23976.'''
        raise NotImplementedError()


class Timecode(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents timecode value in video.'''
    
    def __init__(self, format : aspose.psd.xmp.schemas.xmpdm.TimeFormat, time_value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.xmpdm.Timecode` class.
        
        :param format: The time format.
        :param time_value: The time value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Returns the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.schemas.xmpdm.Timecode) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> aspose.psd.xmp.schemas.xmpdm.TimeFormat:
        '''Gets the format used in the :py:attr:`aspose.psd.xmp.schemas.xmpdm.Timecode.time_value`.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : aspose.psd.xmp.schemas.xmpdm.TimeFormat) -> None:
        '''Sets the format used in the :py:attr:`aspose.psd.xmp.schemas.xmpdm.Timecode.time_value`.'''
        raise NotImplementedError()
    
    @property
    def time_value(self) -> str:
        '''Gets the time value in the specified format.'''
        raise NotImplementedError()
    
    @time_value.setter
    def time_value(self, value : str) -> None:
        '''Sets the time value in the specified format.'''
        raise NotImplementedError()
    

class XmpDynamicMediaPackage(aspose.psd.xmp.XmpPackage):
    '''Represents XMP Dynamic Media namespace.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def contains_key(self, key : str) -> bool:
        '''Determines whether the specified key contains key.
        
        :param key: The key to be checked.
        :returns: Returns true if the specified key contains key.'''
        raise NotImplementedError()
    
    def add_value(self, key : str, value : str) -> None:
        '''Adds string property.
        
        :param key: The string representation of key that is identified with added value.
        :param value: The string value.'''
        raise NotImplementedError()
    
    def remove(self, key : str) -> bool:
        '''Remove the value with the specified key.
        
        :param key: The string representation of key that is identified with removed value.
        :returns: Returns true if the value with the specified key was removed.'''
        raise NotImplementedError()
    
    def clear(self) -> None:
        '''Clears this instance.'''
        raise NotImplementedError()
    
    def set_value(self, key : str, value : aspose.psd.xmp.IXmlValue) -> None:
        '''Sets the value.
        
        :param key: The string representation of key that is identified with added value.
        :param value: The value to add to.'''
        raise NotImplementedError()
    
    def set_xmp_type_value(self, key : str, value : aspose.psd.xmp.types.XmpTypeBase) -> None:
        '''Sets the XMP type value.
        
        :param key: The string representation of key that is identified with set value.
        :param value: The value to set to.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    
    def set_abs_peak_audio_file_path(self, uri : str) -> None:
        '''Sets the absolute peak audio file path.
        
        :param uri: The absolute path to the file’s peak audio file.'''
        raise NotImplementedError()
    
    def set_alblum(self, album : str) -> None:
        '''Sets the alblum.
        
        :param album: The album.'''
        raise NotImplementedError()
    
    def set_alt_tape_name(self, alt_tape_name : str) -> None:
        '''Sets the alternative tape name.
        
        :param alt_tape_name: Alternative tape name.'''
        raise NotImplementedError()
    
    def set_alt_time_code(self, timecode : aspose.psd.xmp.schemas.xmpdm.Timecode) -> None:
        '''Sets the alternative time code.
        
        :param timecode: Time code.'''
        raise NotImplementedError()
    
    def set_artist(self, artist : str) -> None:
        '''Sets the artist.
        
        :param artist: The artist.'''
        raise NotImplementedError()
    
    def set_audio_channel_type(self, audio_channel_type : aspose.psd.xmp.schemas.xmpdm.AudioChannelType) -> None:
        '''Sets the audio channel type.
        
        :param audio_channel_type: Audio channel type.'''
        raise NotImplementedError()
    
    def set_audio_sample_rate(self, rate : int) -> None:
        '''Sets the audio sample rate.
        
        :param rate: The audio sample rate.'''
        raise NotImplementedError()
    
    def set_audio_sample_type(self, audio_sample_type : aspose.psd.xmp.schemas.xmpdm.AudioSampleType) -> None:
        '''Sets the audio sample type.
        
        :param audio_sample_type: The audio sample type.'''
        raise NotImplementedError()
    
    def set_camera_angle(self, camera_angle : str) -> None:
        '''Sets the camera angle.
        
        :param camera_angle: The camera angle.'''
        raise NotImplementedError()
    
    def set_camera_label(self, camera_label : str) -> None:
        '''Sets the camera label.
        
        :param camera_label: The camera label.'''
        raise NotImplementedError()
    
    def set_camera_move(self, camera_move : str) -> None:
        '''Sets the camera move.
        
        :param camera_move: The camera move.'''
        raise NotImplementedError()
    
    def set_client(self, client : str) -> None:
        '''Sets the client.
        
        :param client: The client.'''
        raise NotImplementedError()
    
    def set_comment(self, comment : str) -> None:
        '''Sets the comment.
        
        :param comment: The comment.'''
        raise NotImplementedError()
    
    def set_composer(self, composer : str) -> None:
        '''Sets the composer.
        
        :param composer: The composer.'''
        raise NotImplementedError()
    
    def set_director(self, director : str) -> None:
        '''Sets the director.
        
        :param director: The director.'''
        raise NotImplementedError()
    
    def set_director_photography(self, director_photography : str) -> None:
        '''Sets the director of photography.
        
        :param director_photography: The director of photography.'''
        raise NotImplementedError()
    
    def set_duration(self, duration : aspose.psd.xmp.schemas.xmpdm.Time) -> None:
        '''Sets the duration.
        
        :param duration: The duration.'''
        raise NotImplementedError()
    
    def set_engineer(self, engineer : str) -> None:
        '''Sets the engineer.
        
        :param engineer: The engineer.'''
        raise NotImplementedError()
    
    def set_file_data_rate(self, rate : aspose.psd.xmp.types.derived.Rational) -> None:
        '''Sets the file data rate.
        
        :param rate: The file data rate in megabytes per second.'''
        raise NotImplementedError()
    
    def set_genre(self, genre : str) -> None:
        '''Sets the genre.
        
        :param genre: The genre.'''
        raise NotImplementedError()
    
    def set_good(self, good : bool) -> None:
        '''Sets the good.
        
        :param good: if set to ``true`` a shot is a keeper.'''
        raise NotImplementedError()
    
    def set_instrument(self, instrument : str) -> None:
        '''Sets the instrument.
        
        :param instrument: The instrument.'''
        raise NotImplementedError()
    
    def set_intro_time(self, intro_time : aspose.psd.xmp.schemas.xmpdm.Time) -> None:
        '''Sets the intro time.
        
        :param intro_time: The intro time.'''
        raise NotImplementedError()
    
    def set_key(self, key : str) -> None:
        '''Sets the audio’s musical key.
        
        :param key: The audio’s musical key. One of: C, C#, D, D#, E, F, F#, G, G#, A, A#, and B.'''
        raise NotImplementedError()
    
    def set_log_comment(self, comment : str) -> None:
        '''Sets the user\'s log comment.
        
        :param comment: The comment.'''
        raise NotImplementedError()
    
    @property
    def xml_namespace(self) -> str:
        '''Gets the XML namespace.'''
        raise NotImplementedError()
    
    @property
    def prefix(self) -> str:
        '''Gets the prefix.'''
        raise NotImplementedError()
    
    @property
    def namespace_uri(self) -> str:
        '''Gets the namespace URI.'''
        raise NotImplementedError()
    

class ProjectType:
    '''Represents project type in :py:class:`aspose.psd.xmp.schemas.xmpdm.XmpDynamicMediaPackage`.'''
    
    MOVIE : ProjectType
    '''The movie project type'''
    STILL : ProjectType
    '''The still project type'''
    AUDIO : ProjectType
    '''The audio project type'''
    CUSTOM : ProjectType
    '''The custom project type'''

