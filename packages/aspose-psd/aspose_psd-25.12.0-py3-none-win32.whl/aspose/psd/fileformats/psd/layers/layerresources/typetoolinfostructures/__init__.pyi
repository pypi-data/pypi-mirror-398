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

class AliasStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The alias structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.AliasStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def data_length(self) -> int:
        '''Gets the exact data length in bytes.'''
        raise NotImplementedError()
    
    @property
    def full_path(self) -> str:
        '''Gets the full path.'''
        raise NotImplementedError()
    
    @full_path.setter
    def full_path(self, value : str) -> None:
        '''Sets the full path.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class BooleanStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The boolean structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.BooleanStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> bool:
        '''Gets a boolean value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : bool) -> None:
        '''Sets a boolean value.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class ClassStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The class structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, structure_key : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ClassStructure` class.
        
        :param key_name: Name of the key.
        :param class_id: The class ID.
        :param structure_key: The structure key.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the class ID.'''
        raise NotImplementedError()
    
    @property
    def class_name(self) -> str:
        '''Gets the class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the class name.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY_CLSS(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()

    @property
    def STRUCTURE_KEY_TYPE(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()

    @property
    def STRUCTURE_KEY_GLBC(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class DescriptorStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The descriptor structure'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_name : str, structures : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure` class.
        
        :param key_name: The key name.
        :param class_id: The class identifier.
        :param class_name: Name of the class.
        :param structures: The structures.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def class_name(self) -> str:
        '''Gets the class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the class name.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the class ID.'''
        raise NotImplementedError()
    
    @property
    def structures(self) -> List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]:
        '''Gets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @structures.setter
    def structures(self, value : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Sets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class DoubleStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The double structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DoubleStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> float:
        '''Gets the double value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : float) -> None:
        '''Sets the double value.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class EnumeratedDescriptorStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The enumerated descriptor structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, type_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, enum_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.EnumeratedDescriptorStructure` class.
        
        :param key_name: The key name.
        :param type_id: The type ID.
        :param enum_name: The enum name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def type_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the type ID.'''
        raise NotImplementedError()
    
    @type_id.setter
    def type_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the type ID.'''
        raise NotImplementedError()
    
    @property
    def enum_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the enum name.'''
        raise NotImplementedError()
    
    @enum_name.setter
    def enum_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the enum name.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''The enumerated descriptor key.'''
        raise NotImplementedError()


class EnumeratedReferenceStructure(EnumeratedDescriptorStructure):
    '''Enumerated reference structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, type_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, enum_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.EnumeratedReferenceStructure` class.
        
        :param key_name: The key name.
        :param class_id: The class ID.
        :param type_id: The type ID.
        :param enum_name: The enum name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def type_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the type ID.'''
        raise NotImplementedError()
    
    @type_id.setter
    def type_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the type ID.'''
        raise NotImplementedError()
    
    @property
    def enum_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the enum name.'''
        raise NotImplementedError()
    
    @enum_name.setter
    def enum_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the enum name.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''The enumerated descriptor key.'''
        raise NotImplementedError()

    @property
    def class_name(self) -> str:
        '''Gets the class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the class name.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the class ID.'''
        raise NotImplementedError()
    
    @property
    def ENUMERATED_STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class IntegerStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The integer structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.IntegerStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> int:
        '''Gets an integer value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : int) -> None:
        '''Sets an integer value.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''The integer structure key.'''
        raise NotImplementedError()


class ListStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The list structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ListStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def items_count(self) -> int:
        '''Gets the items count.'''
        raise NotImplementedError()
    
    @property
    def types(self) -> List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]:
        '''Gets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @types.setter
    def types(self, value : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Sets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class NameStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The Name structure (key: 0x6E616D65, which spells "name" in ASCII) is a simple
    structure used to store a Unicode or Pascal-style string representing the name of an
    element, such as a layer, path, or adjustment.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.NameStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the value of a Name structure.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Sets the value of a Name structure.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''The Name structure key.'''
        raise NotImplementedError()


class ObjectArrayStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''Defines the ObjectArrayStructure class that usually holds :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitArrayStructure` array.
    It is used in the PSD file resources, such as PlLd Resource and SoLd Resource.'''
    
    @overload
    def __init__(self, key_name : str, class_id_name : str, structures : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ObjectArrayStructure` class.
        
        :param key_name: Name of the key.
        :param class_id_name: Name of the class identifier.
        :param structures: The structures.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, key : int, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_name : str, structures : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ObjectArrayStructure` class.
        
        :param key: The integer key.
        :param key_name: The key name.
        :param class_id: The class identifier.
        :param class_name: Name of the class.
        :param structures: The structures.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the object array structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def structure_count(self) -> int:
        '''Gets the object array substructure count.'''
        raise NotImplementedError()
    
    @property
    def class_name(self) -> str:
        '''Gets the object array class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the object array class name.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the object array class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the object array class ID.'''
        raise NotImplementedError()
    
    @property
    def structures(self) -> List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]:
        '''Gets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @structures.setter
    def structures(self, value : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Sets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the \'ObAr\' structure key.'''
        raise NotImplementedError()


class OffsetStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The offset structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.OffsetStructure` class.
        
        :param key_name: The key name.
        :param class_id: The class ID.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def class_name(self) -> str:
        '''Gets the class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the class name.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the class ID.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> int:
        '''Gets the integer value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : int) -> None:
        '''Sets the integer value.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class PathStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The path structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.PathStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def prefix(self) -> str:
        '''Gets the path prefix.'''
        raise NotImplementedError()
    
    @prefix.setter
    def prefix(self, value : str) -> None:
        '''Sets the path prefix.'''
        raise NotImplementedError()
    
    @property
    def path(self) -> str:
        '''Gets the path.'''
        raise NotImplementedError()
    
    @path.setter
    def path(self, value : str) -> None:
        '''Sets the path.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class PropertyStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The property structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, class_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID, key_id : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.PropertyStructure` class.
        
        :param key_name: Name of the key.
        :param class_id: The class ID.
        :param key_id: The key ID.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def class_name(self) -> str:
        '''Gets the class name.'''
        raise NotImplementedError()
    
    @class_name.setter
    def class_name(self, value : str) -> None:
        '''Sets the class name.'''
        raise NotImplementedError()
    
    @property
    def class_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the class ID.'''
        raise NotImplementedError()
    
    @class_id.setter
    def class_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the class ID.'''
        raise NotImplementedError()
    
    @property
    def key_id(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key ID.'''
        raise NotImplementedError()
    
    @key_id.setter
    def key_id(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key ID.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class RawDataStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The raw data structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.RawDataStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        '''Gets the data.'''
        raise NotImplementedError()
    
    @data.setter
    def data(self, value : List[int]) -> None:
        '''Sets the data.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class ReferenceStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The reference structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ReferenceStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def items(self) -> List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]:
        '''Gets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @items.setter
    def items(self, value : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]) -> None:
        '''Sets a copy of an array of structures.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class StringStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The string structure.'''
    
    @overload
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.StringStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.StringStructure` class with value.
        
        :param key_name: The key name.
        :param value: The value.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
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
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class UnitArrayStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''Defines the UnitArrayStructure class that holds :py:class:`float` values array and their measure unit.
    It is used in the PSD file resources, usually by :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.ObjectArrayStructure`.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, unit_type : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes, values : List[float]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitArrayStructure` class.
        
        :param key_name: Name of the key.
        :param unit_type: Type of the unit.
        :param values: The values.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets this unit array structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def unit_type(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes:
        '''Gets the measure unit type of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitArrayStructure` values.'''
        raise NotImplementedError()
    
    @unit_type.setter
    def unit_type(self, value : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes) -> None:
        '''Sets the measure unit type of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitArrayStructure` values.'''
        raise NotImplementedError()
    
    @property
    def value_count(self) -> int:
        '''Gets the value count.'''
        raise NotImplementedError()
    
    @property
    def values(self) -> List[float]:
        '''Gets the unit array structure values.'''
        raise NotImplementedError()
    
    @values.setter
    def values(self, value : List[float]) -> None:
        '''Sets the unit array structure values.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Defines the \'UnFl\' :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitArrayStructure` key.'''
        raise NotImplementedError()


class UnitStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The unit structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitStructure` class.
        
        :param key_name: The key name.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def unit_type(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes:
        '''Gets the unit type.'''
        raise NotImplementedError()
    
    @unit_type.setter
    def unit_type(self, value : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnitTypes) -> None:
        '''Sets the unit type.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> float:
        '''Gets the value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : float) -> None:
        '''Sets the value.'''
        raise NotImplementedError()
    
    @property
    def STRUCTURE_KEY(self) -> int:
        '''Identifies the structure key.'''
        raise NotImplementedError()


class UnknownStructure(aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure):
    '''The unknown structure.'''
    
    def __init__(self, key_name : aspose.psd.fileformats.psd.layers.layerresources.ClassID, key : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.UnknownStructure` class.
        
        :param key_name: The key name.
        :param key: The structure key.'''
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def save_without_key_name(self, stream_container : aspose.psd.StreamContainer) -> None:
        '''Saves the structure to the specified stream container.
        
        :param stream_container: The stream container.'''
        raise NotImplementedError()
    
    def get_header_length(self) -> int:
        '''Gets the header length.
        
        :returns: The header length'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the structure key.'''
        raise NotImplementedError()
    
    @property
    def key_name(self) -> aspose.psd.fileformats.psd.layers.layerresources.ClassID:
        '''Gets the key name.'''
        raise NotImplementedError()
    
    @key_name.setter
    def key_name(self, value : aspose.psd.fileformats.psd.layers.layerresources.ClassID) -> None:
        '''Sets the key name.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure` length in bytes.'''
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        '''Gets the data.'''
        raise NotImplementedError()
    
    @data.setter
    def data(self, value : List[int]) -> None:
        '''Sets the data.'''
        raise NotImplementedError()
    

class UnitTypes:
    '''The unit types.'''
    
    ANGLE : UnitTypes
    '''Angle unit.'''
    DENSITY : UnitTypes
    '''Density unit.'''
    DISTANCE : UnitTypes
    '''Distance unit.'''
    NONE : UnitTypes
    '''Undefined unit.'''
    PERCENT : UnitTypes
    '''Percent unit.'''
    PIXELS : UnitTypes
    '''Pixels unit.'''
    POINTS : UnitTypes
    '''Points unit.'''
    MILLIMETERS : UnitTypes
    '''Millimeters unit.'''

