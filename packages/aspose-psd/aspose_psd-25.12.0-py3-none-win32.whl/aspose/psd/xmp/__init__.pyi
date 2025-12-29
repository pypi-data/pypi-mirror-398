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

class IXmlValue:
    '''Converts xmp values to the XML string representation.'''
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    

class LangAlt(IXmlValue):
    '''Represents XMP Language Alternative.'''
    
    @overload
    def __init__(self, default_value : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.LangAlt` class.
        
        :param default_value: The default value.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.LangAlt` class.'''
        raise NotImplementedError()
    
    def add_language(self, language : str, value : str) -> None:
        '''Adds the language.
        
        :param language: The language.
        :param value: The language value.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    

class Namespaces:
    '''Contains namespaces used in RDF document.'''
    
    @property
    def XML(self) -> str:
        '''Xml namespace.'''
        raise NotImplementedError()

    @property
    def RDF(self) -> str:
        '''Resource definition framework namespace.'''
        raise NotImplementedError()

    @property
    def DUBLIN_CORE(self) -> str:
        '''Dublic Core namespace.'''
        raise NotImplementedError()

    @property
    def XMP_BASIC(self) -> str:
        '''XMP Basic namespace.'''
        raise NotImplementedError()

    @property
    def XMP_RIGHTS(self) -> str:
        '''XMP Rights Management namespace.'''
        raise NotImplementedError()

    @property
    def XMP_MM(self) -> str:
        '''XMP digital asset management namespace.'''
        raise NotImplementedError()

    @property
    def XMP_DM(self) -> str:
        '''XMP Dynamic Media namespace.'''
        raise NotImplementedError()

    @property
    def PDF(self) -> str:
        '''Adobe PDF namespace.'''
        raise NotImplementedError()

    @property
    def PHOTOSHOP(self) -> str:
        '''Adobe Photoshop namespace.'''
        raise NotImplementedError()

    @property
    def XMP_GRAPHICS(self) -> str:
        '''XMP graphics namespace.'''
        raise NotImplementedError()

    @property
    def XMP_GRAPHICS_THUMBNAIL(self) -> str:
        '''XMP graphics namespace.'''
        raise NotImplementedError()

    @property
    def XMP_TYPE_FONT(self) -> str:
        '''XMP Font type.'''
        raise NotImplementedError()

    @property
    def XMP_TYPE_DIMENSIONS(self) -> str:
        '''XMP Dimensions type.'''
        raise NotImplementedError()

    @property
    def XMP_TYPE_RESOURCE_REF(self) -> str:
        '''XMP ResourceRef URI.'''
        raise NotImplementedError()

    @property
    def XMP_TYPE_RESOURCE_EVENT(self) -> str:
        '''XMP ResourceEvent URI.'''
        raise NotImplementedError()

    @property
    def XMP_TYPE_VERSION(self) -> str:
        '''XMP Version.'''
        raise NotImplementedError()


class XmpArray(IXmlValue):
    '''Represents Xmp Array in :py:class:`aspose.psd.xmp.XmpPackage`. TODO: Array may contain complex data.'''
    
    @overload
    def __init__(self, type : aspose.psd.xmp.XmpArrayType, items : List[str]) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpArray` class.
        
        :param type: The type of array.
        :param items: The items list.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, type : aspose.psd.xmp.XmpArrayType) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpArray` class.
        
        :param type: The type of array.'''
        raise NotImplementedError()
    
    def add_item(self, item : str) -> None:
        '''Adds new item.
        
        :param item: The item to be added to list of items.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    
    @property
    def values(self) -> List[str]:
        '''Gets array of values inside :py:class:`aspose.psd.xmp.XmpArray`.'''
        raise NotImplementedError()
    

class XmpArrayHelper:
    '''The helper class for processing RDF logic'''
    
    @staticmethod
    def get_rdf_code(xmp_array_type : aspose.psd.xmp.XmpArrayType) -> str:
        '''Gets the RDF code for specific :py:class:`aspose.psd.xmp.XmpArrayType`.
        
        :param xmp_array_type: Type of the XMP array.
        :returns: Returns the RDF code for specific :py:class:`aspose.psd.xmp.XmpArrayType`.'''
        raise NotImplementedError()
    

class XmpElementBase:
    '''Represents base xmp element contains attributes.'''
    
    def add_attribute(self, attribute : str, value : str) -> None:
        '''Adds the attribute.
        
        :param attribute: The attribute.
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_attribute(self, attribute : str) -> str:
        '''Gets the attribute.
        
        :param attribute: The attribute.
        :returns: Returns the attribute for specified attribute name.'''
        raise NotImplementedError()
    
    def clear_attributes(self) -> None:
        '''Removes all attributes.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.XmpElementBase) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    

class XmpHeaderPi(IXmlValue):
    '''Represents XMP header processing instruction.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpHeaderPi` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, guid : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpHeaderPi` class.
        
        :param guid: The unique identifier.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.XmpHeaderPi) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @property
    def guid(self) -> str:
        '''Represents Header Guid.'''
        raise NotImplementedError()
    
    @guid.setter
    def guid(self, value : str) -> None:
        '''Represents Header Guid.'''
        raise NotImplementedError()
    

class XmpMeta(XmpElementBase):
    '''Represents xmpmeta. Optional.
    The purpose of this element is to identify XMP metadata within general XML text that might contain other non-XMP uses of RDF.'''
    
    @overload
    def __init__(self, toolkit_version : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpMeta` class.
        
        :param toolkit_version: Adobe XMP toolkit version.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpMeta` class.'''
        raise NotImplementedError()
    
    @overload
    def equals(self, other : aspose.psd.xmp.XmpMeta) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @overload
    def equals(self, other : aspose.psd.xmp.XmpElementBase) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    def add_attribute(self, attribute : str, value : str) -> None:
        '''Adds the attribute.
        
        :param attribute: The attribute.
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_attribute(self, attribute : str) -> str:
        '''Gets the attribute.
        
        :param attribute: The attribute.
        :returns: Returns the attribute for specified attribute name.'''
        raise NotImplementedError()
    
    def clear_attributes(self) -> None:
        '''Removes all attributes.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts XMP value to the XML representation.
        
        :returns: Returns the XMP value converted to the XML representation.'''
        raise NotImplementedError()
    
    @property
    def adobe_xmp_toolkit(self) -> str:
        '''Gets or set Adobe Xmp toolkit version.'''
        raise NotImplementedError()
    
    @adobe_xmp_toolkit.setter
    def adobe_xmp_toolkit(self, value : str) -> None:
        '''Set Adobe Xmp toolkit version.'''
        raise NotImplementedError()
    

class XmpPackage(IXmlValue):
    '''Defines the XmpPackage class that represents base abstraction for XMP package.'''
    
    def contains_key(self, key : str) -> bool:
        '''Determines whether the specified key contains key.
        
        :param key: The key to be checked.
        :returns: Returns true if the specified key contains key.'''
        raise NotImplementedError()
    
    def add_value(self, key : str, value : str) -> None:
        '''Adds the value.
        
        :param key: The string representation of key that is identified with added value.
        :param value: The value to add to.'''
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
    

class XmpPackageBaseCollection:
    '''Represents collection of :py:class:`aspose.psd.xmp.XmpPackage`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def add(self, package : aspose.psd.xmp.XmpPackage) -> None:
        '''Adds new instance of :py:class:`aspose.psd.xmp.XmpPackage`.
        
        :param package: The XMP package to add.'''
        raise NotImplementedError()
    
    def remove(self, package : aspose.psd.xmp.XmpPackage) -> None:
        '''Removes the specified XMP package.
        
        :param package: The XMP package to remove.'''
        raise NotImplementedError()
    
    def get_packages(self) -> List[aspose.psd.xmp.XmpPackage]:
        '''Get array of :py:class:`aspose.psd.xmp.XmpPackage`.
        
        :returns: Returns an array of XMP packages.'''
        raise NotImplementedError()
    
    def get_package(self, namespace_uri : str) -> aspose.psd.xmp.XmpPackage:
        '''Gets :py:class:`aspose.psd.xmp.XmpPackage` by it\'s namespaceURI.
        
        :param namespace_uri: The namespace URI to get package for.
        :returns: Returns XMP package for specified namespace Uri.'''
        raise NotImplementedError()
    
    def clear(self) -> None:
        '''Clear all :py:class:`aspose.psd.xmp.XmpPackage` inside collection.'''
        raise NotImplementedError()
    
    @property
    def count(self) -> int:
        '''Gets the number of elements in the collection.'''
        raise NotImplementedError()
    

class XmpPacketWrapper:
    '''Contains serialized xmp package including header and trailer.'''
    
    @overload
    def __init__(self, header : aspose.psd.xmp.XmpHeaderPi, trailer : aspose.psd.xmp.XmpTrailerPi, xmp_meta : aspose.psd.xmp.XmpMeta) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpPacketWrapper` class.
        
        :param header: The XMP header of processing instruction.
        :param trailer: The XMP trailer of processing instruction.
        :param xmp_meta: The XMP metadata.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpPacketWrapper` class.'''
        raise NotImplementedError()
    
    def add_package(self, package : aspose.psd.xmp.XmpPackage) -> None:
        '''Adds the package.
        
        :param package: The package.'''
        raise NotImplementedError()
    
    def get_package(self, namespace_uri : str) -> aspose.psd.xmp.XmpPackage:
        '''Gets package by namespace URI.
        
        :param namespace_uri: The package schema URI.
        :returns: Returns the XMP package for specified namespace URI.'''
        raise NotImplementedError()
    
    def contains_package(self, namespace_uri : str) -> bool:
        '''Determines whethere package is exist in xmp wrapper.
        
        :param namespace_uri: Package schema uri.
        :returns: Returns true if package with specified namespace Uri exist in XMP wrapper.'''
        raise NotImplementedError()
    
    def remove_package(self, package : aspose.psd.xmp.XmpPackage) -> None:
        '''Removes the XMP package.
        
        :param package: The package.'''
        raise NotImplementedError()
    
    def clear_packages(self) -> None:
        '''Removes all :py:class:`aspose.psd.xmp.XmpPackage` inside XMP.'''
        raise NotImplementedError()
    
    @property
    def header_pi(self) -> aspose.psd.xmp.XmpHeaderPi:
        '''Gets the header processing instruction.'''
        raise NotImplementedError()
    
    @property
    def meta(self) -> aspose.psd.xmp.XmpMeta:
        '''Gets the XMP meta. Optional.'''
        raise NotImplementedError()
    
    @meta.setter
    def meta(self, value : aspose.psd.xmp.XmpMeta) -> None:
        '''Gets the XMP meta. Optional.'''
        raise NotImplementedError()
    
    @property
    def trailer_pi(self) -> aspose.psd.xmp.XmpTrailerPi:
        '''Gets the trailer processing instruction.'''
        raise NotImplementedError()
    
    @property
    def packages(self) -> List[aspose.psd.xmp.XmpPackage]:
        '''Gets array of :py:class:`aspose.psd.xmp.XmpPackage` inside XMP.'''
        raise NotImplementedError()
    
    @property
    def packages_count(self) -> int:
        '''Gets amount of packages inside XMP structure.'''
        raise NotImplementedError()
    

class XmpRdfRoot(XmpElementBase):
    '''Represents rdf:RDF element.
    A single XMP packet shall be serialized using a single rdf:RDF XML element. The rdf:RDF element content shall consist of only zero or more rdf:Description elements.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def add_attribute(self, attribute : str, value : str) -> None:
        '''Adds the attribute.
        
        :param attribute: The attribute.
        :param value: The value.'''
        raise NotImplementedError()
    
    def get_attribute(self, attribute : str) -> str:
        '''Gets the attribute.
        
        :param attribute: The attribute.
        :returns: Returns the attribute for specified attribute name.'''
        raise NotImplementedError()
    
    def clear_attributes(self) -> None:
        '''Removes all attributes.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.XmpElementBase) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    def register_namespace_uri(self, prefix : str, namespace_uri : str) -> None:
        '''Adds namespace uri by prefix. Prefix may start without xmlns.
        
        :param prefix: The prefix.
        :param namespace_uri: Package schema uri.'''
        raise NotImplementedError()
    
    def get_namespace_uri(self, prefix : str) -> str:
        '''Gets namespace URI by specific prefix. Prefix may start without xmlns.
        
        :param prefix: The prefix.
        :returns: Returns a package schema URI.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts xmp value to the xml representation.
        
        :returns: Returns XMP value converted to XML string.'''
        raise NotImplementedError()
    

class XmpTrailerPi(IXmlValue):
    '''Represents XMP trailer processing instruction.'''
    
    @overload
    def __init__(self, is_writable : bool) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpTrailerPi` class.
        
        :param is_writable: Inditacates whether trailer is writable.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.XmpTrailerPi` class.'''
        raise NotImplementedError()
    
    def get_xml_value(self) -> str:
        '''Converts xmp value to the xml representation.
        
        :returns: Returns XML representation of XMP.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.XmpTrailerPi) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @property
    def is_writable(self) -> bool:
        '''Gets a value indicating whether this instance is writable.'''
        raise NotImplementedError()
    
    @is_writable.setter
    def is_writable(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is writable.'''
        raise NotImplementedError()
    

class XmpArrayType:
    '''Represents array type in :py:class:`aspose.psd.xmp.XmpArray`.'''
    
    UNORDERED : XmpArrayType
    '''The unordered array.'''
    ORDERED : XmpArrayType
    '''The ordered array.'''
    ALTERNATIVE : XmpArrayType
    '''The alternative array.'''

