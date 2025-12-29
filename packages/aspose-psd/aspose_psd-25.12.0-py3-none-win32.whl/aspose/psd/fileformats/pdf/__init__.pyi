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

class PdfCoreOptions:
    '''The common options for convertion to PDF'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def headings_outline_levels(self) -> int:
        '''Specifies how many levels of outline items to include in the document outline.
        0 - no outline, 1 - one outline level and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @headings_outline_levels.setter
    def headings_outline_levels(self, value : int) -> None:
        '''Specifies how many levels of outline items to include in the document outline.
        0 - no outline, 1 - one outline level and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @property
    def expanded_outline_levels(self) -> int:
        '''Specifies how many levels in the document outline to show expanded when the PDF file is viewed.
        0 - the document outline is not expanded.
        1 - first level items in the document are expanded and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @expanded_outline_levels.setter
    def expanded_outline_levels(self, value : int) -> None:
        '''Specifies how many levels in the document outline to show expanded when the PDF file is viewed.
        0 - the document outline is not expanded.
        1 - first level items in the document are expanded and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @property
    def bookmarks_outline_level(self) -> int:
        '''Specifies at which level in the document outline to display bookmark objects.
        0 - not displayed.
        1 at first level and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @bookmarks_outline_level.setter
    def bookmarks_outline_level(self, value : int) -> None:
        '''Specifies at which level in the document outline to display bookmark objects.
        0 - not displayed.
        1 at first level and so on.
        Default is 0.'''
        raise NotImplementedError()
    
    @property
    def jpeg_quality(self) -> int:
        '''Specifies the quality of JPEG compression for images (if JPEG compression is used).
        Default is 95.'''
        raise NotImplementedError()
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int) -> None:
        '''Specifies the quality of JPEG compression for images (if JPEG compression is used).
        Default is 95.'''
        raise NotImplementedError()
    
    @property
    def pdf_compliance(self) -> aspose.psd.PdfComplianceVersion:
        '''Gets the PDF compliance.'''
        raise NotImplementedError()
    
    @pdf_compliance.setter
    def pdf_compliance(self, value : aspose.psd.PdfComplianceVersion) -> None:
        '''Sets the PDF compliance.'''
        raise NotImplementedError()
    

class PdfDocumentInfo:
    '''This class represents set of metadata for document description.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def keywords(self) -> str:
        '''Gets keywords of the document.'''
        raise NotImplementedError()
    
    @keywords.setter
    def keywords(self, value : str) -> None:
        '''Sets keywords of the document.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title of the document.'''
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        '''Sets title of the document.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author of the document.'''
        raise NotImplementedError()
    
    @author.setter
    def author(self, value : str) -> None:
        '''Sets author of the document.'''
        raise NotImplementedError()
    
    @property
    def subject(self) -> str:
        '''Gets subject of the document.'''
        raise NotImplementedError()
    
    @subject.setter
    def subject(self, value : str) -> None:
        '''Sets subject of the document.'''
        raise NotImplementedError()
    

