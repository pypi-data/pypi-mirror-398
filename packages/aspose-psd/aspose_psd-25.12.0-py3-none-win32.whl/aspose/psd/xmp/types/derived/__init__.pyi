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

class Rational(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents XMP Rational.'''
    
    def __init__(self, numerator : int, denominator : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.Rational` class.
        
        :param numerator: The numerator.
        :param denominator: The denominator.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets thestring contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def numerator(self) -> int:
        '''Gets the numerator.'''
        raise NotImplementedError()
    
    @property
    def denominator(self) -> int:
        '''Gets the denominator.'''
        raise NotImplementedError()
    
    @denominator.setter
    def denominator(self, value : int) -> None:
        '''Sets the denominator.'''
        raise NotImplementedError()
    
    @property
    def float_value(self) -> float:
        '''Gets the float value.'''
        raise NotImplementedError()
    

class RenditionClass(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents the XMP Rendition.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.RenditionClass` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, token : str, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.RenditionClass` class.
        
        :param token: The token.
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def token(self) -> str:
        '''Gets the token.'''
        raise NotImplementedError()
    
    @token.setter
    def token(self, value : str) -> None:
        '''Sets the token.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Sets the value.'''
        raise NotImplementedError()
    
    @property
    def defined_values(self) -> List[str]:
        '''The defined values'''
        raise NotImplementedError()


class XmpAgentName(aspose.psd.xmp.types.basic.XmpText):
    '''Represents Agent name, Software organization etc.'''
    
    def __init__(self, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.XmpAgentName` class.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the text value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Sets the text value.'''
        raise NotImplementedError()
    

class XmpGuid(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents XMP global unique identifier.'''
    
    @overload
    def __init__(self, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.XmpGuid` class.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, guid : System.Guid) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.XmpGuid` class.
        
        :param guid: The unique identifier.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def prefix(self) -> str:
        '''Gets the prefix like uuid.'''
        raise NotImplementedError()
    
    @prefix.setter
    def prefix(self, value : str) -> None:
        '''Sets the prefix like uuid.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> System.Guid:
        '''Gets the value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : System.Guid) -> None:
        '''Sets the value.'''
        raise NotImplementedError()
    

class XmpLocale(aspose.psd.xmp.types.basic.XmpText):
    '''Represents language code.'''
    
    def __init__(self, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.XmpLocale` class.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the text value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Sets the text value.'''
        raise NotImplementedError()
    

class XmpMimeType(aspose.psd.xmp.types.basic.XmpText):
    '''Represents MIME type.'''
    
    def __init__(self, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.derived.XmpMimeType` class.
        
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the text value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Sets the text value.'''
        raise NotImplementedError()
    

