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

class FileCreateSource(FileSource):
    '''Represents a file source for creation.'''
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.sources.FileCreateSource` class.
        
        :param file_path: The file path to create.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, is_temporal : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.sources.FileCreateSource` class.
        
        :param file_path: The file path to create.
        :param is_temporal: If set to ``true`` the created file will be temporal.'''
        raise NotImplementedError()
    
    def get_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the stream container.
        
        :returns: the stream container.'''
        raise NotImplementedError()
    
    @property
    def is_temporal(self) -> bool:
        '''Gets a value indicating whether file will be temporal.'''
        raise NotImplementedError()
    
    @property
    def file_path(self) -> str:
        '''Gets the file path to create.'''
        raise NotImplementedError()
    

class FileOpenSource(FileSource):
    '''Represents a file source for opening.'''
    
    def __init__(self, file_path : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.sources.FileOpenSource` class.
        
        :param file_path: The file path to open.'''
        raise NotImplementedError()
    
    def get_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the stream container.
        
        :returns: the stream container.'''
        raise NotImplementedError()
    
    @property
    def is_temporal(self) -> bool:
        '''Gets a value indicating whether file will be temporal.'''
        raise NotImplementedError()
    
    @property
    def file_path(self) -> str:
        '''Gets the file path to open.'''
        raise NotImplementedError()
    

class FileSource(aspose.psd.Source):
    '''Represents a file source which is capable of files manipulation.'''
    
    def get_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the stream container.
        
        :returns: the stream container.'''
        raise NotImplementedError()
    
    @property
    def is_temporal(self) -> bool:
        '''Gets a value indicating whether file will be temporal.'''
        raise NotImplementedError()
    

class StreamSource(aspose.psd.Source):
    '''Represents a stream source.'''
    
    @overload
    def __init__(self, stream : io._IOBase) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.sources.StreamSource` class.
        
        :param stream: The stream to open.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, dispose_stream : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.sources.StreamSource` class.
        
        :param stream: The stream to open.
        :param dispose_stream: if set to ``true`` the stream will be disposed.'''
        raise NotImplementedError()
    
    def get_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the stream container.
        
        :returns: the stream container.'''
        raise NotImplementedError()
    
    @property
    def stream(self) -> io._IOBase:
        '''Gets the stream.'''
        raise NotImplementedError()
    
    @property
    def dispose_stream(self) -> bool:
        '''Gets a value indicating whether stream should be disposed whenever container gets disposed.'''
        raise NotImplementedError()
    

