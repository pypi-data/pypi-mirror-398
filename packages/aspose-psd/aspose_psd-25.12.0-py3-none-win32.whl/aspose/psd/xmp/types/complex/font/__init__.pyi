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

class Font(aspose.psd.xmp.types.complex.ComplexTypeBase):
    '''Represents XMP Font.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.font.Font` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, font_family : str) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.font.Font` class.
        
        :param font_family: Font family.'''
        raise NotImplementedError()
    
    def get_xmp_representation(self) -> str:
        '''Gets the string contained value in XMP format.
        
        :returns: Returns the string contained value in XMP format.'''
        raise NotImplementedError()
    
    @property
    def prefix(self) -> str:
        '''Gets the prefix.'''
        raise NotImplementedError()
    
    @property
    def namespace_uri(self) -> str:
        '''Gets the default namespace URI.'''
        raise NotImplementedError()
    
    @property
    def child_font_files(self) -> List[str]:
        '''Gets the array of file names for the fonts that make up a composite font.'''
        raise NotImplementedError()
    
    @child_font_files.setter
    def child_font_files(self, value : List[str]) -> None:
        '''Sets the array of file names for the fonts that make up a composite font.'''
        raise NotImplementedError()
    
    @property
    def is_composite(self) -> bool:
        '''Gets a value indicating whether this font is composite.'''
        raise NotImplementedError()
    
    @is_composite.setter
    def is_composite(self, value : bool) -> None:
        '''Sets a value indicating whether this font is composite.'''
        raise NotImplementedError()
    
    @property
    def font_face(self) -> str:
        '''Gets the font face.'''
        raise NotImplementedError()
    
    @font_face.setter
    def font_face(self, value : str) -> None:
        '''Sets the font face.'''
        raise NotImplementedError()
    
    @property
    def font_family(self) -> str:
        '''Gets the font family.'''
        raise NotImplementedError()
    
    @font_family.setter
    def font_family(self, value : str) -> None:
        '''Sets the font family.'''
        raise NotImplementedError()
    
    @property
    def font_file_name(self) -> str:
        '''Gets the font file name without full path.'''
        raise NotImplementedError()
    
    @font_file_name.setter
    def font_file_name(self, value : str) -> None:
        '''Sets the font file name without full path.'''
        raise NotImplementedError()
    
    @property
    def font_name(self) -> str:
        '''Gets the PostScript font name.'''
        raise NotImplementedError()
    
    @font_name.setter
    def font_name(self, value : str) -> None:
        '''Sets the PostScript font name.'''
        raise NotImplementedError()
    
    @property
    def font_type(self) -> str:
        '''Gets the font type.'''
        raise NotImplementedError()
    
    @font_type.setter
    def font_type(self, value : str) -> None:
        '''Sets the font type.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets the font version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : str) -> None:
        '''Sets the font version.'''
        raise NotImplementedError()
    

