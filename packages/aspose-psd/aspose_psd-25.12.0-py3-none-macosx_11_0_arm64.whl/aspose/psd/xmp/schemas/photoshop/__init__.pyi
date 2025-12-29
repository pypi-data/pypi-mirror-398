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

class Layer(aspose.psd.xmp.types.XmpTypeBase):
    '''Represents Photoshop text layer.'''
    
    @overload
    def __init__(self, layer_name : str, layer_text : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.photoshop.Layer` class.
        
        :param layer_name: Name of the layer.
        :param layer_text: The layer text.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.schemas.photoshop.Layer` class.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Returns string contained value in XMP format.
        
        :returns: Returns string contained value in XMP format.'''
        raise NotImplementedError()
    
    def equals(self, other : aspose.psd.xmp.schemas.photoshop.Layer) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the text layer.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the name of the text layer.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets the text content of the layer.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Sets the text content of the layer.'''
        raise NotImplementedError()
    

class PhotoshopPackage(aspose.psd.xmp.XmpPackage):
    '''Represents Adobe Photoshop namespace.'''
    
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
    
    def set_authors_position(self, authors_position : str) -> None:
        '''Sets the authors position.
        
        :param authors_position: The authors position.'''
        raise NotImplementedError()
    
    def set_caption_writer(self, caption_writer : str) -> None:
        '''Sets the caption writer.
        
        :param caption_writer: The caption writer.'''
        raise NotImplementedError()
    
    def set_category(self, category : str) -> None:
        '''Sets the category.
        
        :param category: The category.'''
        raise NotImplementedError()
    
    def set_city(self, city : str) -> None:
        '''Sets the city.
        
        :param city: The city name.'''
        raise NotImplementedError()
    
    def set_color_mode(self, color_mode : aspose.psd.xmp.schemas.photoshop.ColorMode) -> None:
        '''Sets the color mode.
        
        :param color_mode: The color mode.'''
        raise NotImplementedError()
    
    def set_country(self, country : str) -> None:
        '''Sets the country.
        
        :param country: The country.'''
        raise NotImplementedError()
    
    def set_credit(self, credit : str) -> None:
        '''Sets the credit.
        
        :param credit: The credit.'''
        raise NotImplementedError()
    
    def set_created_date(self, created_date : datetime) -> None:
        '''Sets created date.
        
        :param created_date: The created date.'''
        raise NotImplementedError()
    
    def set_document_ancestors(self, ancestors : List[str]) -> None:
        '''Sets the document ancestors.
        
        :param ancestors: The ancestors.'''
        raise NotImplementedError()
    
    def set_headline(self, headline : str) -> None:
        '''Sets the headline.
        
        :param headline: The headline.'''
        raise NotImplementedError()
    
    def set_history(self, history : str) -> None:
        '''Sets the history.
        
        :param history: The history.'''
        raise NotImplementedError()
    
    def set_icc_profile(self, icc_profile : str) -> None:
        '''Sets the icc profile.
        
        :param icc_profile: The icc profile.'''
        raise NotImplementedError()
    
    def set_instructions(self, instructions : str) -> None:
        '''Sets the instructions.
        
        :param instructions: The instructions.'''
        raise NotImplementedError()
    
    def set_source(self, source : str) -> None:
        '''Sets the source.
        
        :param source: The source.'''
        raise NotImplementedError()
    
    def set_state(self, state : str) -> None:
        '''Sets the state.
        
        :param state: The state.'''
        raise NotImplementedError()
    
    def set_supplemental_categories(self, supplemental_categories : List[str]) -> None:
        '''Sets supplemental categories.
        
        :param supplemental_categories: The supplemental categories.'''
        raise NotImplementedError()
    
    def set_transmission_reference(self, transmission_reference : str) -> None:
        '''Sets the transmission reference.
        
        :param transmission_reference: The transmission reference.'''
        raise NotImplementedError()
    
    def set_urgency(self, urgency : int) -> None:
        '''Sets the urgency.
        
        :param urgency: The urgency.'''
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
    def URGENCY_MAX(self) -> int:
        '''Urgency max value.'''
        raise NotImplementedError()

    @property
    def URGENCY_MIN(self) -> int:
        '''Urgency min value.'''
        raise NotImplementedError()


class ColorMode:
    '''Represents color mode in :py:class:`aspose.psd.xmp.schemas.photoshop.PhotoshopPackage`.'''
    
    BITMAP : ColorMode
    '''Bitmap color mode.'''
    GRAY_SCALE : ColorMode
    '''Gray scale color mode.'''
    INDEXED_COLOR : ColorMode
    '''The indexed color.'''
    RGB : ColorMode
    '''RGB color.'''
    CMYK : ColorMode
    '''CMYK color mode.'''
    MULTI_CHANNEL : ColorMode
    '''Multi-channel color.'''
    DUOTONE : ColorMode
    '''Duo-tone color.'''
    LAB_COLOR : ColorMode
    '''LAB color.'''

