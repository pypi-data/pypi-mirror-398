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

class AnimatedDataSectionResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The Animated Data Section Plug-In resource.'''
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def key_name(self) -> str:
        '''The resource key name.'''
        raise NotImplementedError()
    
    @property
    def animated_data_section(self) -> aspose.psd.fileformats.psd.layers.layerresources.AnimatedDataSectionStructure:
        '''Gets the animated data section structure.'''
        raise NotImplementedError()
    

class BackgroundColorResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The resource with border information of image print settings.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the background color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the background color.'''
        raise NotImplementedError()
    

class BorderInformationResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The resource with border information of image print settings.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def width(self) -> float:
        '''Gets the border width.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        '''Sets the border width.'''
        raise NotImplementedError()
    
    @property
    def unit(self) -> aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit:
        '''Gets the border units.'''
        raise NotImplementedError()
    
    @unit.setter
    def unit(self, value : aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit) -> None:
        '''Sets the border units.'''
        raise NotImplementedError()
    

class CaptionDigestResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''CaptionDigest resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def digest(self) -> List[int]:
        '''Gets the digest.'''
        raise NotImplementedError()
    
    @digest.setter
    def digest(self, value : List[int]) -> None:
        '''Sets the digest.'''
        raise NotImplementedError()
    

class ColorHalftoneInformationResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Halftoning resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def halftone_data(self) -> List[int]:
        '''Gets the halftone data.'''
        raise NotImplementedError()
    
    @halftone_data.setter
    def halftone_data(self, value : List[int]) -> None:
        '''Sets the halftone data.'''
        raise NotImplementedError()
    

class ColorTransferFunctionsResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Color transfer resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def color_transfer_data(self) -> List[int]:
        '''Gets the color transfer data.'''
        raise NotImplementedError()
    
    @color_transfer_data.setter
    def color_transfer_data(self, value : List[int]) -> None:
        '''Sets the color transfer data.'''
        raise NotImplementedError()
    

class DocumentSpecificIdsResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Document Specific Ids resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the identifier.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the identifier.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()


class FixedPointDecimal:
    '''Fixed-point decimal, with 16-bit integer and 16-bit fraction.'''
    
    @overload
    def __init__(self, integer : int, fraction : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.resources.FixedPointDecimal` class.
        
        :param integer: The integer.
        :param fraction: The fraction.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, value : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.resources.FixedPointDecimal` class. Split the high and low words of a 32-bit integer into a fixed-point number.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, value : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.resources.FixedPointDecimal` class.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    def to_double(self) -> float:
        '''Converts current fixed point decimal to double.
        
        :returns: The converted value.'''
        raise NotImplementedError()
    
    @property
    def integer(self) -> int:
        '''Gets the integer.'''
        raise NotImplementedError()
    
    @integer.setter
    def integer(self, value : int) -> None:
        '''Sets the integer.'''
        raise NotImplementedError()
    
    @property
    def fraction(self) -> int:
        '''Gets the fraction.'''
        raise NotImplementedError()
    
    @fraction.setter
    def fraction(self, value : int) -> None:
        '''Sets the fraction.'''
        raise NotImplementedError()
    

class GlobalAltitudeResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Global altitude resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def altitude(self) -> int:
        '''Gets the altitude.'''
        raise NotImplementedError()
    
    @altitude.setter
    def altitude(self, value : int) -> None:
        '''Sets the altitude.'''
        raise NotImplementedError()
    

class GlobalAngleResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Global angle resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def global_angle(self) -> int:
        '''Gets the global angle.'''
        raise NotImplementedError()
    
    @global_angle.setter
    def global_angle(self, value : int) -> None:
        '''Sets the global angle.'''
        raise NotImplementedError()
    

class GridAndGuidesResouce(aspose.psd.fileformats.psd.ResourceBlock):
    '''Represents the grid and guides resource.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def guides(self) -> List[aspose.psd.fileformats.psd.resources.GuideResource]:
        '''Gets the guides.'''
        raise NotImplementedError()
    
    @guides.setter
    def guides(self, value : List[aspose.psd.fileformats.psd.resources.GuideResource]) -> None:
        '''Sets the guides.'''
        raise NotImplementedError()
    
    @property
    def guide_count(self) -> int:
        '''Gets the guide resource blocks count.'''
        raise NotImplementedError()
    
    @property
    def header_version(self) -> int:
        '''Gets the header version. This value should be always 1.'''
        raise NotImplementedError()
    
    @header_version.setter
    def header_version(self, value : int) -> None:
        '''Sets the header version. This value should be always 1.'''
        raise NotImplementedError()
    
    @property
    def grid_cycle_x(self) -> int:
        '''Gets the horizontal grid cycle. The default is 576.'''
        raise NotImplementedError()
    
    @grid_cycle_x.setter
    def grid_cycle_x(self, value : int) -> None:
        '''Sets the horizontal grid cycle. The default is 576.'''
        raise NotImplementedError()
    
    @property
    def grid_cycle_y(self) -> int:
        '''Gets the vertical grid cycle. The default is 576.'''
        raise NotImplementedError()
    
    @grid_cycle_y.setter
    def grid_cycle_y(self, value : int) -> None:
        '''Sets the vertical grid cycle. The default is 576.'''
        raise NotImplementedError()
    

class GuideResource:
    '''The guide resource block.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def location(self) -> int:
        '''Gets the location of guide in document coordinates.'''
        raise NotImplementedError()
    
    @location.setter
    def location(self, value : int) -> None:
        '''Sets the location of guide in document coordinates.'''
        raise NotImplementedError()
    
    @property
    def direction(self) -> aspose.psd.fileformats.psd.resources.GuideDirection:
        '''Gets the direction of guide.'''
        raise NotImplementedError()
    
    @direction.setter
    def direction(self, value : aspose.psd.fileformats.psd.resources.GuideDirection) -> None:
        '''Sets the direction of guide.'''
        raise NotImplementedError()
    
    @property
    def GUIDE_RESOURCE_SIZE(self) -> int:
        '''The guide resource block size.'''
        raise NotImplementedError()


class IccProfileResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Represents the ICC profile resource.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()


class IccUntaggedResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Icc untagged resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def profile(self) -> int:
        '''Gets the profile.'''
        raise NotImplementedError()
    
    @profile.setter
    def profile(self, value : int) -> None:
        '''Sets the profile.'''
        raise NotImplementedError()
    

class LayerGroupInformationResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Layer group information resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def groups(self) -> List[int]:
        '''Gets the groups.'''
        raise NotImplementedError()
    
    @groups.setter
    def groups(self, value : List[int]) -> None:
        '''Sets the groups.'''
        raise NotImplementedError()
    

class LayerGroupsEnabledResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Layer groups enabled resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def ds(self) -> List[int]:
        '''Gets the i ds.'''
        raise NotImplementedError()
    
    @ds.setter
    def ds(self, value : List[int]) -> None:
        '''Sets the i ds.'''
        raise NotImplementedError()
    

class LayerSelectionIdsResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Layer selection ids resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def count(self) -> int:
        '''Gets the count.'''
        raise NotImplementedError()
    
    @count.setter
    def count(self, value : int) -> None:
        '''Sets the count.'''
        raise NotImplementedError()
    
    @property
    def layer_ids(self) -> List[int]:
        '''Gets the layer ids.'''
        raise NotImplementedError()
    
    @layer_ids.setter
    def layer_ids(self, value : List[int]) -> None:
        '''Sets the layer ids.'''
        raise NotImplementedError()
    

class LayerStateInformationResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Layer state information resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def layer_index(self) -> int:
        '''Gets the index of the layer.'''
        raise NotImplementedError()
    
    @layer_index.setter
    def layer_index(self, value : int) -> None:
        '''Sets the index of the layer.'''
        raise NotImplementedError()
    

class PixelAspectRatioResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Pixel aspect ration resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def aspect_ratio(self) -> float:
        '''Gets the aspect ratio.'''
        raise NotImplementedError()
    
    @aspect_ratio.setter
    def aspect_ratio(self, value : float) -> None:
        '''Sets the aspect ratio.'''
        raise NotImplementedError()
    

class PrintFlagsResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Print flags resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def center_crop_mark(self) -> int:
        '''Gets the center crop mark.'''
        raise NotImplementedError()
    
    @center_crop_mark.setter
    def center_crop_mark(self, value : int) -> None:
        '''Sets the center crop mark.'''
        raise NotImplementedError()
    
    @property
    def bleed_width(self) -> int:
        '''Gets the width of the bleed.'''
        raise NotImplementedError()
    
    @bleed_width.setter
    def bleed_width(self, value : int) -> None:
        '''Sets the width of the bleed.'''
        raise NotImplementedError()
    
    @property
    def bleed_scale(self) -> int:
        '''Gets the bleed scale.'''
        raise NotImplementedError()
    
    @bleed_scale.setter
    def bleed_scale(self, value : int) -> None:
        '''Sets the bleed scale.'''
        raise NotImplementedError()
    

class PrintScaleResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Print Scale resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def style(self) -> int:
        '''Gets the style.'''
        raise NotImplementedError()
    
    @style.setter
    def style(self, value : int) -> None:
        '''Sets the style.'''
        raise NotImplementedError()
    
    @property
    def x_location(self) -> float:
        '''Gets the x location.'''
        raise NotImplementedError()
    
    @x_location.setter
    def x_location(self, value : float) -> None:
        '''Sets the x location.'''
        raise NotImplementedError()
    
    @property
    def y_location(self) -> float:
        '''Gets the y location.'''
        raise NotImplementedError()
    
    @y_location.setter
    def y_location(self, value : float) -> None:
        '''Sets the y location.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> float:
        '''Gets the scale.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : float) -> None:
        '''Sets the scale.'''
        raise NotImplementedError()
    

class QuickMaskInformationResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Quick mask information resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def channel_id(self) -> int:
        '''Gets the channel identifier.'''
        raise NotImplementedError()
    
    @channel_id.setter
    def channel_id(self, value : int) -> None:
        '''Sets the channel identifier.'''
        raise NotImplementedError()
    
    @property
    def is_mask_empty(self) -> bool:
        '''Gets a value indicating whether this instance is mask empty.'''
        raise NotImplementedError()
    
    @is_mask_empty.setter
    def is_mask_empty(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is mask empty.'''
        raise NotImplementedError()
    

class ResolutionInfoResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The resolution info resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def h_dpi(self) -> aspose.psd.fileformats.psd.resources.FixedPointDecimal:
        '''Horizontal DPI.'''
        raise NotImplementedError()
    
    @h_dpi.setter
    def h_dpi(self, value : aspose.psd.fileformats.psd.resources.FixedPointDecimal) -> None:
        '''Horizontal DPI.'''
        raise NotImplementedError()
    
    @property
    def v_dpi(self) -> aspose.psd.fileformats.psd.resources.FixedPointDecimal:
        '''Vertical DPI.'''
        raise NotImplementedError()
    
    @v_dpi.setter
    def v_dpi(self, value : aspose.psd.fileformats.psd.resources.FixedPointDecimal) -> None:
        '''Vertical DPI.'''
        raise NotImplementedError()
    
    @property
    def h_res_display_unit(self) -> aspose.psd.fileformats.psd.resources.resolutionenums.ResolutionUnit:
        '''Display units for horizontal resolution.  This only affects the
        user interface; the resolution is still stored in the PSD file
        as pixels/inch.'''
        raise NotImplementedError()
    
    @h_res_display_unit.setter
    def h_res_display_unit(self, value : aspose.psd.fileformats.psd.resources.resolutionenums.ResolutionUnit) -> None:
        '''Display units for horizontal resolution.  This only affects the
        user interface; the resolution is still stored in the PSD file
        as pixels/inch.'''
        raise NotImplementedError()
    
    @property
    def v_res_display_unit(self) -> aspose.psd.fileformats.psd.resources.resolutionenums.ResolutionUnit:
        '''Display units for vertical resolution.'''
        raise NotImplementedError()
    
    @v_res_display_unit.setter
    def v_res_display_unit(self, value : aspose.psd.fileformats.psd.resources.resolutionenums.ResolutionUnit) -> None:
        '''Display units for vertical resolution.'''
        raise NotImplementedError()
    
    @property
    def width_display_unit(self) -> aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit:
        '''Gets the width display unit.'''
        raise NotImplementedError()
    
    @width_display_unit.setter
    def width_display_unit(self, value : aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit) -> None:
        '''Sets the width display unit.'''
        raise NotImplementedError()
    
    @property
    def height_display_unit(self) -> aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit:
        '''Gets the height display unit.'''
        raise NotImplementedError()
    
    @height_display_unit.setter
    def height_display_unit(self, value : aspose.psd.fileformats.psd.resources.resolutionenums.PhysicalUnit) -> None:
        '''Sets the height display unit.'''
        raise NotImplementedError()
    

class Thumbnail4Resource(ThumbnailResource):
    '''Represents the thumbnail resource for psd 4.0.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def jpeg_options(self) -> aspose.psd.imageoptions.JpegOptions:
        '''Gets the JPEG options. Suitable when thumbnail resource is saved into JPEG file format only. This option has no effect when RAW format is defined.'''
        raise NotImplementedError()
    
    @jpeg_options.setter
    def jpeg_options(self, value : aspose.psd.imageoptions.JpegOptions) -> None:
        '''Sets the JPEG options. Suitable when thumbnail resource is saved into JPEG file format only. This option has no effect when RAW format is defined.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> aspose.psd.fileformats.psd.resources.ThumbnailFormat:
        '''Gets the thumbnail data format.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : aspose.psd.fileformats.psd.resources.ThumbnailFormat) -> None:
        '''Sets the thumbnail data format.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets the width of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Sets the width of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets the height of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Sets the height of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @property
    def width_bytes(self) -> int:
        '''Gets the row width in bytes.'''
        raise NotImplementedError()
    
    @property
    def total_size(self) -> int:
        '''Gets the total data size.'''
        raise NotImplementedError()
    
    @property
    def size_after_compression(self) -> int:
        '''Gets the size after compression. Used for consistency check.'''
        raise NotImplementedError()
    
    @property
    def bits_pixel(self) -> int:
        '''Gets the bits pixel.'''
        raise NotImplementedError()
    
    @bits_pixel.setter
    def bits_pixel(self, value : int) -> None:
        '''Sets the bits pixel.'''
        raise NotImplementedError()
    
    @property
    def planes_count(self) -> int:
        '''Gets the planes count.'''
        raise NotImplementedError()
    
    @planes_count.setter
    def planes_count(self, value : int) -> None:
        '''Sets the planes count.'''
        raise NotImplementedError()
    
    @property
    def thumbnail_argb_32_data(self) -> List[int]:
        '''Gets the 32-bit ARGB thumbnail data.'''
        raise NotImplementedError()
    
    @thumbnail_argb_32_data.setter
    def thumbnail_argb_32_data(self, value : List[int]) -> None:
        '''Sets the 32-bit ARGB thumbnail data.'''
        raise NotImplementedError()
    
    @property
    def thumbnail_data(self) -> List[aspose.psd.Color]:
        '''Gets the thumbnail data.'''
        raise NotImplementedError()
    
    @thumbnail_data.setter
    def thumbnail_data(self, value : List[aspose.psd.Color]) -> None:
        '''Sets the thumbnail data.'''
        raise NotImplementedError()
    

class ThumbnailResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The thumbnail resource block.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def jpeg_options(self) -> aspose.psd.imageoptions.JpegOptions:
        '''Gets the JPEG options. Suitable when thumbnail resource is saved into JPEG file format only. This option has no effect when RAW format is defined.'''
        raise NotImplementedError()
    
    @jpeg_options.setter
    def jpeg_options(self, value : aspose.psd.imageoptions.JpegOptions) -> None:
        '''Sets the JPEG options. Suitable when thumbnail resource is saved into JPEG file format only. This option has no effect when RAW format is defined.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> aspose.psd.fileformats.psd.resources.ThumbnailFormat:
        '''Gets the thumbnail data format.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : aspose.psd.fileformats.psd.resources.ThumbnailFormat) -> None:
        '''Sets the thumbnail data format.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets the width of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Sets the width of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets the height of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Sets the height of thumbnail in pixels.'''
        raise NotImplementedError()
    
    @property
    def width_bytes(self) -> int:
        '''Gets the row width in bytes.'''
        raise NotImplementedError()
    
    @property
    def total_size(self) -> int:
        '''Gets the total data size.'''
        raise NotImplementedError()
    
    @property
    def size_after_compression(self) -> int:
        '''Gets the size after compression. Used for consistency check.'''
        raise NotImplementedError()
    
    @property
    def bits_pixel(self) -> int:
        '''Gets the bits pixel.'''
        raise NotImplementedError()
    
    @bits_pixel.setter
    def bits_pixel(self, value : int) -> None:
        '''Sets the bits pixel.'''
        raise NotImplementedError()
    
    @property
    def planes_count(self) -> int:
        '''Gets the planes count.'''
        raise NotImplementedError()
    
    @planes_count.setter
    def planes_count(self, value : int) -> None:
        '''Sets the planes count.'''
        raise NotImplementedError()
    
    @property
    def thumbnail_argb_32_data(self) -> List[int]:
        '''Gets the 32-bit ARGB thumbnail data.'''
        raise NotImplementedError()
    
    @thumbnail_argb_32_data.setter
    def thumbnail_argb_32_data(self, value : List[int]) -> None:
        '''Sets the 32-bit ARGB thumbnail data.'''
        raise NotImplementedError()
    
    @property
    def thumbnail_data(self) -> List[aspose.psd.Color]:
        '''Gets the thumbnail data.'''
        raise NotImplementedError()
    
    @thumbnail_data.setter
    def thumbnail_data(self, value : List[aspose.psd.Color]) -> None:
        '''Sets the thumbnail data.'''
        raise NotImplementedError()
    

class TransparencyIndexResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The transparency index resource block.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def transparency_index(self) -> int:
        '''Gets the transparency color index.'''
        raise NotImplementedError()
    
    @transparency_index.setter
    def transparency_index(self, value : int) -> None:
        '''Sets the transparency color index.'''
        raise NotImplementedError()
    

class UnicodeAlphaNamesResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Unicode alpha names resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def alpha_names(self) -> str:
        '''Gets the alpha names.'''
        raise NotImplementedError()
    
    @alpha_names.setter
    def alpha_names(self, value : str) -> None:
        '''Sets the alpha names.'''
        raise NotImplementedError()
    

class UnknownResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''The unknown resource. When a resource block is not recognized then this resource block is created.'''
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def data(self) -> List[int]:
        '''Gets the resource data.'''
        raise NotImplementedError()
    

class UrlListResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Url list resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def count(self) -> int:
        '''Gets the count.'''
        raise NotImplementedError()
    
    @count.setter
    def count(self, value : int) -> None:
        '''Sets the count.'''
        raise NotImplementedError()
    
    @property
    def longs(self) -> List[int]:
        '''Gets the longs.'''
        raise NotImplementedError()
    
    @longs.setter
    def longs(self, value : List[int]) -> None:
        '''Sets the longs.'''
        raise NotImplementedError()
    
    @property
    def ids(self) -> List[int]:
        '''Gets the ids.'''
        raise NotImplementedError()
    
    @ids.setter
    def ids(self, value : List[int]) -> None:
        '''Sets the ids.'''
        raise NotImplementedError()
    
    @property
    def texts(self) -> List[str]:
        '''Gets the texts.'''
        raise NotImplementedError()
    
    @texts.setter
    def texts(self, value : List[str]) -> None:
        '''Sets the texts.'''
        raise NotImplementedError()
    

class VersionInfoResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Version Info resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def has_real_merged_data(self) -> bool:
        '''Gets a value indicating whether this instance has real merged data.'''
        raise NotImplementedError()
    
    @has_real_merged_data.setter
    def has_real_merged_data(self, value : bool) -> None:
        '''Sets a value indicating whether this instance has real merged data.'''
        raise NotImplementedError()
    
    @property
    def reader_name(self) -> str:
        '''Gets the name of the reader.'''
        raise NotImplementedError()
    
    @reader_name.setter
    def reader_name(self, value : str) -> None:
        '''Sets the name of the reader.'''
        raise NotImplementedError()
    
    @property
    def writer_name(self) -> str:
        '''Gets the name of the writer.'''
        raise NotImplementedError()
    
    @writer_name.setter
    def writer_name(self, value : str) -> None:
        '''Sets the name of the writer.'''
        raise NotImplementedError()
    
    @property
    def file_version(self) -> int:
        '''Gets the file version.'''
        raise NotImplementedError()
    
    @file_version.setter
    def file_version(self, value : int) -> None:
        '''Sets the file version.'''
        raise NotImplementedError()
    

class WatermarkResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Watermark resource'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def is_watermark(self) -> bool:
        '''Gets a value indicating whether this instance is watermark.'''
        raise NotImplementedError()
    
    @is_watermark.setter
    def is_watermark(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is watermark.'''
        raise NotImplementedError()
    

class WorkingPathResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Working path resource.'''
    
    def __init__(self, data_bytes : List[int]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.resources.WorkingPathResource` class.
        
        :param data_bytes: The data of the vector path.'''
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required PSD version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def paths(self) -> List[aspose.psd.fileformats.core.vectorpaths.VectorPathRecord]:
        '''Gets the path records.'''
        raise NotImplementedError()
    
    @paths.setter
    def paths(self, value : List[aspose.psd.fileformats.core.vectorpaths.VectorPathRecord]) -> None:
        '''Sets the path records.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def is_disabled(self) -> bool:
        '''Gets a value indicating whether this instance is disabled.'''
        raise NotImplementedError()
    
    @is_disabled.setter
    def is_disabled(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is disabled.'''
        raise NotImplementedError()
    
    @property
    def is_not_linked(self) -> bool:
        '''Gets a value indicating whether this instance is not linked.'''
        raise NotImplementedError()
    
    @is_not_linked.setter
    def is_not_linked(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is not linked.'''
        raise NotImplementedError()
    
    @property
    def is_inverted(self) -> bool:
        '''Gets a value indicating whether this instance is inverted.'''
        raise NotImplementedError()
    
    @is_inverted.setter
    def is_inverted(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is inverted.'''
        raise NotImplementedError()
    

class XmpResource(aspose.psd.fileformats.psd.ResourceBlock):
    '''Represents the XMP metadata resource.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream : aspose.psd.StreamContainer) -> None:
        '''Saves the resource block to the specified stream.
        
        :param stream: The stream to save the resource block to.'''
        raise NotImplementedError()
    
    def validate_values(self) -> None:
        '''Validates the resource values.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the resource signature. Should be always \'8BIM\'.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the unique identifier for the resource.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the resource name. Pascal string, padded to make the size even (a null name consists of two bytes of 0).'''
        raise NotImplementedError()
    
    @property
    def data_size(self) -> int:
        '''Gets the resource data size in bytes.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the resource block size in bytes including its data.'''
        raise NotImplementedError()
    
    @property
    def minimal_version(self) -> int:
        '''Gets the minimal required psd version.'''
        raise NotImplementedError()
    
    @property
    def RESOUCE_BLOCK_SIGNATURE(self) -> int:
        '''The regular Photoshop resource signature.'''
        raise NotImplementedError()

    @property
    def RESOUCE_BLOCK_ME_SA_SIGNATURE(self) -> int:
        '''The resource signature of ImageReady.'''
        raise NotImplementedError()

    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Get or set XMP data container'''
        raise NotImplementedError()
    
    @xmp_data.setter
    def xmp_data(self, value : aspose.psd.xmp.XmpPacketWrapper) -> None:
        '''Get or set XMP data container'''
        raise NotImplementedError()
    

class GuideDirection:
    '''The guide direction.'''
    
    VERTICAL : GuideDirection
    '''Vertical guide direction.'''
    HORIZONTAL : GuideDirection
    '''Horizontal guide direction.'''

class ThumbnailFormat:
    '''Specifies thumbnail data format.'''
    
    K_RAW_RGB : ThumbnailFormat
    '''Raw RGB format.'''
    K_JPEG_RGB : ThumbnailFormat
    '''Compressed Jpeg format.'''

