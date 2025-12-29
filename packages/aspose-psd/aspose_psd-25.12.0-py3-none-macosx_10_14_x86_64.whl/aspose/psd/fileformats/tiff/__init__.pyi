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

class TiffDataType:
    '''The tiff data type.'''
    
    @staticmethod
    def read_tag(data_stream : aspose.psd.fileformats.tiff.filemanagement.TiffStreamReader, position : int) -> aspose.psd.fileformats.tiff.TiffDataType:
        '''Reads the tag data.
        
        :param data_stream: The data stream.
        :param position: The tag position.
        :returns: The read tag.'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares the current instance with another object of the same type and returns an integer that indicates whether the current instance precedes, follows, or occurs in the same position in the sort order as the other object.
        
        :param obj: An object to compare with this instance.
        :returns: A 32-bit signed integer that indicates the relative order of the objects being compared. The return value has these meanings:
        Value
        Meaning
        Less than zero
        This instance is less than ``obj``.
        Zero
        This instance is equal to ``obj``.
        Greater than zero
        This instance is greater than ``obj``.'''
        raise NotImplementedError()
    
    def deep_clone(self) -> aspose.psd.fileformats.tiff.TiffDataType:
        '''Performs a deep clone of this instance.
        
        :returns: A deep clone of the current instance.'''
        raise NotImplementedError()
    
    def write_tag(self, data_stream : aspose.psd.fileformats.tiff.filemanagement.TiffStreamWriter, additional_data_offset : int) -> None:
        '''Writes the tag data.
        
        :param data_stream: The data stream.
        :param additional_data_offset: The offset to write additional data to.'''
        raise NotImplementedError()
    
    def write_additional_data(self, data_stream : aspose.psd.fileformats.tiff.filemanagement.TiffStreamWriter) -> int:
        '''Writes the additional tag data.
        
        :param data_stream: The data stream.
        :returns: The actual bytes written.'''
        raise NotImplementedError()
    
    @property
    def count(self) -> int:
        '''Gets the count of elements.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets tag id integer representation.'''
        raise NotImplementedError()
    
    @property
    def tag_id(self) -> aspose.psd.fileformats.tiff.enums.TiffTags:
        '''Gets the tag id.'''
        raise NotImplementedError()
    
    @property
    def tag_type(self) -> aspose.psd.fileformats.tiff.enums.TiffDataTypes:
        '''Gets the tag type.'''
        raise NotImplementedError()
    
    @property
    def aligned_data_size(self) -> int:
        '''Gets the additional data size in bytes (in case the 12 bytes is not enough to fit the tag data).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the additional data size in bytes (in case the 12 bytes is not enough to fit the tag data).'''
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        '''Gets the value this data type contains.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : Any) -> None:
        '''Sets the value this data type contains.'''
        raise NotImplementedError()
    
    @property
    def is_valid(self) -> bool:
        '''Gets a value indicating whether tag data is valid. The valid tag contains data which may be preserved. The invalid tag cannot be stored.'''
        raise NotImplementedError()
    

class TiffExifIfd:
    '''The TIFF Exif image file directory class.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffExifIfd` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, ifd_offset : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffExifIfd` class.
        
        :param ifd_offset: A pointer to the Exif IFD.'''
        raise NotImplementedError()
    
    @property
    def has_value(self) -> bool:
        '''Gets a value indicating whether this instance has value.'''
        raise NotImplementedError()
    
    @property
    def offset(self) -> int:
        '''Gets the pointer to EXIF IFD.'''
        raise NotImplementedError()
    
    @offset.setter
    def offset(self, value : int) -> None:
        '''Sets the pointer to EXIF IFD.'''
        raise NotImplementedError()
    

class TiffRational:
    '''The tiff rational type.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffRational` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, value : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffRational` class.
        
        :param value: The nominator value.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, nominator : int, denominator : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffRational` class.
        
        :param nominator: The nominator.
        :param denominator: The denominator.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float, epsilon : float) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :param epsilon: The error allowed.
        :returns: A rational number having error less than ``epsilon``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :returns: A rational number having error less than :py:attr:`aspose.psd.fileformats.tiff.TiffRational.EPSILON`.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float, epsilon : float) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :param epsilon: The error allowed.
        :returns: A rational number having error less than ``epsilon``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float) -> aspose.psd.fileformats.tiff.TiffRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :returns: A rational number having error less than :py:attr:`aspose.psd.fileformats.tiff.TiffRational.EPSILON`.'''
        raise NotImplementedError()
    
    @property
    def denominator(self) -> int:
        '''Gets the denominator.'''
        raise NotImplementedError()
    
    @property
    def nominator(self) -> int:
        '''Gets the nominator.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> float:
        '''Gets the float value.'''
        raise NotImplementedError()
    
    @property
    def value_d(self) -> float:
        '''Gets the double value.'''
        raise NotImplementedError()
    
    @property
    def EPSILON(self) -> float:
        '''The epsilon for fraction calculation'''
        raise NotImplementedError()


class TiffSRational:
    '''The tiff rational type.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffSRational` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, value : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffRational` class.
        
        :param value: The nominator value.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, nominator : int, denominator : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.tiff.TiffSRational` class.
        
        :param nominator: The nominator.
        :param denominator: The denominator.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float, epsilon : float) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :param epsilon: The error allowed.
        :returns: A rational number having error less than ``epsilon``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :returns: A rational number having error less than :py:attr:`aspose.psd.fileformats.tiff.TiffSRational.EPSILON`.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float, epsilon : float) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :param epsilon: The error allowed.
        :returns: A rational number having error less than ``epsilon``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def approximate_fraction(value : float) -> aspose.psd.fileformats.tiff.TiffSRational:
        '''Approximates the provided value to a fraction.
        
        :param value: The value.
        :returns: A rational number having error less than :py:attr:`aspose.psd.fileformats.tiff.TiffSRational.EPSILON`.'''
        raise NotImplementedError()
    
    @property
    def denominator(self) -> int:
        '''Gets the denominator.'''
        raise NotImplementedError()
    
    @property
    def nominator(self) -> int:
        '''Gets the nominator.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> float:
        '''Gets the float value.'''
        raise NotImplementedError()
    
    @property
    def value_d(self) -> float:
        '''Gets the double value.'''
        raise NotImplementedError()
    
    @property
    def EPSILON(self) -> float:
        '''The epsilon for fraction calculation'''
        raise NotImplementedError()


