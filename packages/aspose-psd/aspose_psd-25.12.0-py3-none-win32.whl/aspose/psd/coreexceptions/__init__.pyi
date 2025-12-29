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

class CompressorException(FrameworkException):
    '''The compressor exception.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.CompressorException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class DataMissmatchError:
    '''Data mismatch exception class'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.DataMissmatchError` class.
        
        :param message: The message that describes the error.'''
        raise NotImplementedError()
    

class FrameworkException:
    '''The PSD framework exception. This class is a core class for all Aspose.PSD exceptions.
    Introduced to discriminate between the exceptions thrown by the Aspose.PSD engine and all other exception types.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.FrameworkException` class.
        
        :param message: The message.'''
        raise NotImplementedError()
    

class ImageCreateException(ImageException):
    '''The image create exception. Occurs during image creation.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.ImageCreateException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class ImageException:
    '''The image exception.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.ImageException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class ImageLoadException(ImageException):
    '''The image load exception. Occurs during image loading.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.ImageLoadException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class ImageSaveException(ImageException):
    '''The image save exception. Occurs during image saving.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.ImageSaveException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class IndexOutOFRangeException:
    '''The compressor exception.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.CompressorException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class LimitMemoryException:
    '''The limit memory exception. Occurs when memory usage should be reduced.'''
    
    @overload
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.LimitMemoryException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str, reduce_memory_factor : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.LimitMemoryException` class.
        
        :param message: The exception message.
        :param reduce_memory_factor: The reduce memory factor.'''
        raise NotImplementedError()
    
    @property
    def reduce_memory_factor(self) -> int:
        '''Gets the reduce memory factor.'''
        raise NotImplementedError()
    
    @reduce_memory_factor.setter
    def reduce_memory_factor(self, value : int) -> None:
        '''Sets the reduce memory factor.'''
        raise NotImplementedError()
    

class OperationInterruptedException(FrameworkException):
    '''Occurs when an operation is interrupted.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.OperationInterruptedException` class.
        
        :param message: The exception message.'''
        raise NotImplementedError()
    

class RdOptimizationError:
    '''RD optimization error exception class'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.RdOptimizationError` class.
        
        :param message: The message that describes the error.'''
        raise NotImplementedError()
    

class StreamReadException(FrameworkException):
    '''The stream reading exception. Caused when stream reading failed due to incorrect offset and bytes count request.'''
    
    @overload
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.StreamReadException` class.
        
        :param message: The message.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str, expected_read_count : int, actual_read_count : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.StreamReadException` class.
        
        :param message: The message.
        :param expected_read_count: The expected read count.
        :param actual_read_count: The actual read count.'''
        raise NotImplementedError()
    
    @property
    def expected_read_count(self) -> int:
        '''Gets the expected read bytes count.'''
        raise NotImplementedError()
    
    @property
    def actual_read_count(self) -> int:
        '''Gets the actual read bytes count.'''
        raise NotImplementedError()
    

class XmpException(FrameworkException):
    '''The exception that is thrown when XMP has invalid structure.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.XmpException` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.coreexceptions.XmpException` class.
        
        :param message: The message.'''
        raise NotImplementedError()
    

