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

class ColorantBase(aspose.psd.xmp.types.complex.ComplexTypeBase):
    '''Represents XMP Colorant type.'''
    
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
    def mode(self) -> aspose.psd.xmp.types.complex.colorant.ColorMode:
        '''Gets :py:class:`aspose.psd.xmp.types.complex.colorant.ColorMode`.'''
        raise NotImplementedError()
    
    @property
    def swatch_name(self) -> str:
        '''Gets the name of the swatch.'''
        raise NotImplementedError()
    
    @swatch_name.setter
    def swatch_name(self, value : str) -> None:
        '''Sets the name of the swatch.'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.xmp.types.complex.colorant.ColorType:
        '''Gets the type of the color.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.xmp.types.complex.colorant.ColorType) -> None:
        '''Sets the type of the color.'''
        raise NotImplementedError()
    

class ColorantCmyk(ColorantBase):
    '''Represents CMYK Colorant.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantCmyk` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, black : float, cyan : float, magenta : float, yellow : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantCmyk` class.
        
        :param black: The black component value.
        :param cyan: The cyan color component value.
        :param magenta: The magenta component value.
        :param yellow: The yellow component value.'''
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
    def mode(self) -> aspose.psd.xmp.types.complex.colorant.ColorMode:
        '''Gets :py:class:`aspose.psd.xmp.types.complex.colorant.ColorMode`.'''
        raise NotImplementedError()
    
    @property
    def swatch_name(self) -> str:
        '''Gets the name of the swatch.'''
        raise NotImplementedError()
    
    @swatch_name.setter
    def swatch_name(self, value : str) -> None:
        '''Sets the name of the swatch.'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.xmp.types.complex.colorant.ColorType:
        '''Gets the type of the color.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.xmp.types.complex.colorant.ColorType) -> None:
        '''Sets the type of the color.'''
        raise NotImplementedError()
    
    @property
    def black(self) -> float:
        '''Gets the black component value.'''
        raise NotImplementedError()
    
    @black.setter
    def black(self, value : float) -> None:
        '''Sets the black component value.'''
        raise NotImplementedError()
    
    @property
    def cyan(self) -> float:
        '''Gets the cyan component value.'''
        raise NotImplementedError()
    
    @cyan.setter
    def cyan(self, value : float) -> None:
        '''Sets the cyan component value.'''
        raise NotImplementedError()
    
    @property
    def magenta(self) -> float:
        '''Gets the magenta component value.'''
        raise NotImplementedError()
    
    @magenta.setter
    def magenta(self, value : float) -> None:
        '''Sets the magenta component value.'''
        raise NotImplementedError()
    
    @property
    def yellow(self) -> float:
        '''Gets the yellow component value.'''
        raise NotImplementedError()
    
    @yellow.setter
    def yellow(self, value : float) -> None:
        '''Sets the yellow component value.'''
        raise NotImplementedError()
    
    @property
    def COLOR_VALUE_MAX(self) -> float:
        '''Color max value in CMYK colorant.'''
        raise NotImplementedError()

    @property
    def COLOR_VALUE_MIN(self) -> float:
        '''Color min value in CMYK colorant.'''
        raise NotImplementedError()


class ColorantLab(ColorantBase):
    '''Represents LAB Colorant.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantLab` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, a : int, b : int, l : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantLab` class.
        
        :param a: A component.
        :param b: B component.
        :param l: L component.'''
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
    def mode(self) -> aspose.psd.xmp.types.complex.colorant.ColorMode:
        '''Gets :py:class:`aspose.psd.xmp.types.complex.colorant.ColorMode`.'''
        raise NotImplementedError()
    
    @property
    def swatch_name(self) -> str:
        '''Gets the name of the swatch.'''
        raise NotImplementedError()
    
    @swatch_name.setter
    def swatch_name(self, value : str) -> None:
        '''Sets the name of the swatch.'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.xmp.types.complex.colorant.ColorType:
        '''Gets the type of the color.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.xmp.types.complex.colorant.ColorType) -> None:
        '''Sets the type of the color.'''
        raise NotImplementedError()
    
    @property
    def a(self) -> int:
        '''Gets the A component.'''
        raise NotImplementedError()
    
    @a.setter
    def a(self, value : int) -> None:
        '''Sets the A component.'''
        raise NotImplementedError()
    
    @property
    def b(self) -> int:
        '''Gets the B component.'''
        raise NotImplementedError()
    
    @b.setter
    def b(self, value : int) -> None:
        '''Sets the B component.'''
        raise NotImplementedError()
    
    @property
    def l(self) -> float:
        '''Gets the L component.'''
        raise NotImplementedError()
    
    @l.setter
    def l(self, value : float) -> None:
        '''Sets the L component.'''
        raise NotImplementedError()
    
    @property
    def MIN_A(self) -> int:
        '''The minimum A component value'''
        raise NotImplementedError()

    @property
    def MAX_A(self) -> int:
        '''The maximum A component value'''
        raise NotImplementedError()

    @property
    def MIN_B(self) -> int:
        '''The minimum B component value'''
        raise NotImplementedError()

    @property
    def MAX_B(self) -> int:
        '''The maximum A component value'''
        raise NotImplementedError()

    @property
    def MIN_L(self) -> float:
        '''The minimum L component value'''
        raise NotImplementedError()

    @property
    def MAX_L(self) -> float:
        '''The maximum A component value'''
        raise NotImplementedError()


class ColorantRgb(ColorantBase):
    '''Represents RGB Colorant.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantRgb` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, red : int, green : int, blue : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.xmp.types.complex.colorant.ColorantRgb` class.
        
        :param red: The red component value.
        :param green: The green component value.
        :param blue: The blue component value.'''
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
    def mode(self) -> aspose.psd.xmp.types.complex.colorant.ColorMode:
        '''Gets :py:class:`aspose.psd.xmp.types.complex.colorant.ColorMode`.'''
        raise NotImplementedError()
    
    @property
    def swatch_name(self) -> str:
        '''Gets the name of the swatch.'''
        raise NotImplementedError()
    
    @swatch_name.setter
    def swatch_name(self, value : str) -> None:
        '''Sets the name of the swatch.'''
        raise NotImplementedError()
    
    @property
    def color_type(self) -> aspose.psd.xmp.types.complex.colorant.ColorType:
        '''Gets the type of the color.'''
        raise NotImplementedError()
    
    @color_type.setter
    def color_type(self, value : aspose.psd.xmp.types.complex.colorant.ColorType) -> None:
        '''Sets the type of the color.'''
        raise NotImplementedError()
    
    @property
    def red(self) -> int:
        '''Gets the red component value.'''
        raise NotImplementedError()
    
    @red.setter
    def red(self, value : int) -> None:
        '''Sets the red component value.'''
        raise NotImplementedError()
    
    @property
    def green(self) -> int:
        '''Gets the green component value.'''
        raise NotImplementedError()
    
    @green.setter
    def green(self, value : int) -> None:
        '''Sets the green component value.'''
        raise NotImplementedError()
    
    @property
    def blue(self) -> int:
        '''Gets the blue component value.'''
        raise NotImplementedError()
    
    @blue.setter
    def blue(self, value : int) -> None:
        '''Sets the blue component value.'''
        raise NotImplementedError()
    

class ColorMode:
    '''Represents color mode.'''
    
    CMYK : ColorMode
    '''CMYK color mode.'''
    RGB : ColorMode
    '''RGB color mode.'''
    LAB : ColorMode
    '''LAB color mode.'''

class ColorType:
    '''Type of color.'''
    
    PROCESS : ColorType
    '''Process color type.'''
    SPOT : ColorType
    '''Spot color type.'''

