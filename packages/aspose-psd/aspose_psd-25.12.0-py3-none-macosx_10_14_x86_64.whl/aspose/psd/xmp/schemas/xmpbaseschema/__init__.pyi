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

class XmpBasicPackage(aspose.psd.xmp.XmpPackage):
    '''Represents XMP basic namespace.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.xmpbaseschema.XmpBasicPackage` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, prefix : str, namespace_uri : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.xmpbaseschema.XmpBasicPackage` class.
        
        :param prefix: The prefix.
        :param namespace_uri: The namespace URI.'''
        raise NotImplementedError()
    
    @overload
    def set_created_date(self, created_date : datetime) -> None:
        '''Adds resource created date.
        
        :param created_date: Created date.'''
        raise NotImplementedError()
    
    @overload
    def set_created_date(self, created_date : str) -> None:
        '''Adds resource created date.
        
        :param created_date: Created date.'''
        raise NotImplementedError()
    
    @overload
    def set_metadata_date(self, metadata_date : datetime) -> None:
        '''Adds metadata last changed date.
        
        :param metadata_date: Metadata date.'''
        raise NotImplementedError()
    
    @overload
    def set_metadata_date(self, metadata_date : str) -> None:
        '''Adds metadata last changed date.
        
        :param metadata_date: Metadata date.'''
        raise NotImplementedError()
    
    @overload
    def set_modify_date(self, modified_date : datetime) -> None:
        '''Adds resource last modified date.
        
        :param modified_date: Last modified date.'''
        raise NotImplementedError()
    
    @overload
    def set_modify_date(self, modified_date : str) -> None:
        '''Adds resource last modified date.
        
        :param modified_date: Last modified date.'''
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
    
    def set_creator_tool(self, creator_tool : str) -> None:
        '''Sets the creator tool.
        
        :param creator_tool: Name of tool.'''
        raise NotImplementedError()
    
    def set_identifier(self, idenfifier : List[str]) -> None:
        '''Sets the identifier.
        
        :param idenfifier: The idenfifier.'''
        raise NotImplementedError()
    
    def set_label(self, label : str) -> None:
        '''Sets the label.
        
        :param label: The label.'''
        raise NotImplementedError()
    
    def set_rating(self, choise : int) -> None:
        '''Sets rating.
        
        :param choise: From -1 till 5'''
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
    
    @property
    def RATING_REJECTED(self) -> int:
        '''Rating rejected value.'''
        raise NotImplementedError()

    @property
    def RATING_MIN(self) -> int:
        '''Rating min value.'''
        raise NotImplementedError()

    @property
    def RATING_MAX(self) -> int:
        '''Rating max value.'''
        raise NotImplementedError()


