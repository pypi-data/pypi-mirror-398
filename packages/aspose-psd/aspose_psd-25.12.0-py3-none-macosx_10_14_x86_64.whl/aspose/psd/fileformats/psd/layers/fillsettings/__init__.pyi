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

class BaseFillSettings(IFillSettings):
    '''Base fill effect settings'''
    
    @property
    def fill_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.FillType:
        '''Gets the type of the fill.'''
        raise NotImplementedError()
    

class ColorFillSettings(BaseFillSettings):
    '''Color fill effect settings'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def fill_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.FillType:
        '''The fill type'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    

class GradientColorPoint(aspose.psd.fileformats.psd.layers.IGradientColorPoint):
    '''The Gradient Color Point.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientColorPoint` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, color : aspose.psd.Color, location : int, median_point_location : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientColorPoint` class.
        
        :param color: Color point on gradient.
        :param location: The location of the color point on the gradient.
        :param median_point_location: The median gradient point location.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    
    @property
    def location(self) -> int:
        '''Gets the point location on gradient.'''
        raise NotImplementedError()
    
    @location.setter
    def location(self, value : int) -> None:
        '''Sets the point location on gradient.'''
        raise NotImplementedError()
    
    @property
    def median_point_location(self) -> int:
        '''Gets the median gradient point location.'''
        raise NotImplementedError()
    
    @median_point_location.setter
    def median_point_location(self, value : int) -> None:
        '''Sets the median gradient point location.'''
        raise NotImplementedError()
    
    @property
    def raw_color(self) -> aspose.psd.fileformats.psd.core.rawcolor.RawColor:
        '''Gets the color of the raw.'''
        raise NotImplementedError()
    
    @raw_color.setter
    def raw_color(self, value : aspose.psd.fileformats.psd.core.rawcolor.RawColor) -> None:
        '''Sets the color of the raw.'''
        raise NotImplementedError()
    
    @property
    def color_mode(self) -> int:
        '''Mode for the color to follow'''
        raise NotImplementedError()
    
    @color_mode.setter
    def color_mode(self, value : int) -> None:
        '''Mode for the color to follow'''
        raise NotImplementedError()
    

class GradientFillSettings(BaseFillSettings):
    '''Base gradient definition class. It contains common properties for both types of gradient (Solid and Noise).'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def fill_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.FillType:
        '''The fill type.'''
        raise NotImplementedError()
    
    @property
    def align_with_layer(self) -> bool:
        '''Gets a value indicating whether [align with layer].'''
        raise NotImplementedError()
    
    @align_with_layer.setter
    def align_with_layer(self, value : bool) -> None:
        '''Sets a value indicating whether [align with layer].'''
        raise NotImplementedError()
    
    @property
    def dither(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @dither.setter
    def dither(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @property
    def reverse(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @reverse.setter
    def reverse(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the angle.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> int:
        '''Gets the scale.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : int) -> None:
        '''Sets the scale.'''
        raise NotImplementedError()
    
    @property
    def horizontal_offset(self) -> float:
        '''Gets the horizontal offset in percentage.'''
        raise NotImplementedError()
    
    @horizontal_offset.setter
    def horizontal_offset(self, value : float) -> None:
        '''Sets the horizontal offset in percentage.'''
        raise NotImplementedError()
    
    @property
    def vertical_offset(self) -> float:
        '''Gets the vertical offset in percentage.'''
        raise NotImplementedError()
    
    @vertical_offset.setter
    def vertical_offset(self, value : float) -> None:
        '''Sets the vertical offset in percentage.'''
        raise NotImplementedError()
    
    @property
    def gradient_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.GradientType:
        '''Gets the type of the gradient.'''
        raise NotImplementedError()
    
    @gradient_type.setter
    def gradient_type(self, value : aspose.psd.fileformats.psd.layers.fillsettings.GradientType) -> None:
        '''Sets the type of the gradient.'''
        raise NotImplementedError()
    
    @property
    def gradient(self) -> aspose.psd.fileformats.psd.layers.gradient.BaseGradient:
        '''Gets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    
    @gradient.setter
    def gradient(self, value : aspose.psd.fileformats.psd.layers.gradient.BaseGradient) -> None:
        '''Sets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    

class GradientMapSettings:
    '''Gradient settings class for gradient map layer. It contains common properties for both types of gradient (Solid and Noise).'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def dither(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @dither.setter
    def dither(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @property
    def reverse(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @reverse.setter
    def reverse(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @property
    def gradient(self) -> aspose.psd.fileformats.psd.layers.gradient.BaseGradient:
        '''Gets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    
    @gradient.setter
    def gradient(self, value : aspose.psd.fileformats.psd.layers.gradient.BaseGradient) -> None:
        '''Sets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    

class GradientTransparencyPoint(IGradientTransparencyPoint):
    '''Gradient Transparency Point'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.GradientTransparencyPoint` class.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    
    @property
    def location(self) -> int:
        '''Gets the location.'''
        raise NotImplementedError()
    
    @location.setter
    def location(self, value : int) -> None:
        '''Sets the location.'''
        raise NotImplementedError()
    
    @property
    def median_point_location(self) -> int:
        '''Gets the median point location.'''
        raise NotImplementedError()
    
    @median_point_location.setter
    def median_point_location(self, value : int) -> None:
        '''Sets the median point location.'''
        raise NotImplementedError()
    

class IColorFillSettings:
    '''Base interface for fill settings'''
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    

class IFillSettings:
    '''Base interface for fill settings'''
    
    @property
    def fill_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.FillType:
        '''Gets the type of the fill.'''
        raise NotImplementedError()
    

class IGradientFillSettings:
    '''Base interface for Gradient fill settings.'''
    
    @property
    def align_with_layer(self) -> bool:
        '''Gets a value indicating whether [align with layer].'''
        raise NotImplementedError()
    
    @align_with_layer.setter
    def align_with_layer(self, value : bool) -> None:
        '''Sets a value indicating whether [align with layer].'''
        raise NotImplementedError()
    
    @property
    def dither(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IGradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @dither.setter
    def dither(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IGradientFillSettings` is dither.'''
        raise NotImplementedError()
    
    @property
    def reverse(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IGradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @reverse.setter
    def reverse(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IGradientFillSettings` is reverse.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the angle.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> int:
        '''Gets the scale.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : int) -> None:
        '''Sets the scale.'''
        raise NotImplementedError()
    
    @property
    def horizontal_offset(self) -> float:
        '''Gets the horizontal offset.'''
        raise NotImplementedError()
    
    @horizontal_offset.setter
    def horizontal_offset(self, value : float) -> None:
        '''Sets the horizontal offset.'''
        raise NotImplementedError()
    
    @property
    def vertical_offset(self) -> float:
        '''Gets the vertical offset.'''
        raise NotImplementedError()
    
    @vertical_offset.setter
    def vertical_offset(self, value : float) -> None:
        '''Sets the vertical offset.'''
        raise NotImplementedError()
    
    @property
    def gradient_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.GradientType:
        '''Gets the type of the gradient.'''
        raise NotImplementedError()
    
    @gradient_type.setter
    def gradient_type(self, value : aspose.psd.fileformats.psd.layers.fillsettings.GradientType) -> None:
        '''Sets the type of the gradient.'''
        raise NotImplementedError()
    
    @property
    def gradient(self) -> aspose.psd.fileformats.psd.layers.gradient.BaseGradient:
        '''Gets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    
    @gradient.setter
    def gradient(self, value : aspose.psd.fileformats.psd.layers.gradient.BaseGradient) -> None:
        '''Sets specific gradient definition instance (Solid/Noise).'''
        raise NotImplementedError()
    

class IGradientTransparencyPoint:
    '''Base interface for fill settings'''
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    
    @property
    def location(self) -> int:
        '''Gets the location. Value range 0-4096.'''
        raise NotImplementedError()
    
    @location.setter
    def location(self, value : int) -> None:
        '''Sets the location. Value range 0-4096.'''
        raise NotImplementedError()
    
    @property
    def median_point_location(self) -> int:
        '''Gets the median point location. Value range 0-4096.'''
        raise NotImplementedError()
    
    @median_point_location.setter
    def median_point_location(self, value : int) -> None:
        '''Sets the median point location. Value range 0-4096.'''
        raise NotImplementedError()
    

class IPatternFillSettings:
    '''Interface for Pattern fill settings'''
    
    @property
    def angle(self) -> float:
        '''Gets the angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the angle.'''
        raise NotImplementedError()
    
    @property
    def linked(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IPatternFillSettings` is linked.'''
        raise NotImplementedError()
    
    @linked.setter
    def linked(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.IPatternFillSettings` is linked.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> float:
        '''Gets the scale.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : float) -> None:
        '''Sets the scale.'''
        raise NotImplementedError()
    
    @property
    def point_type(self) -> str:
        '''Gets the type of the point.'''
        raise NotImplementedError()
    
    @point_type.setter
    def point_type(self, value : str) -> None:
        '''Sets the type of the point.'''
        raise NotImplementedError()
    
    @property
    def pattern_name(self) -> str:
        '''Gets the name of the pattern.'''
        raise NotImplementedError()
    
    @pattern_name.setter
    def pattern_name(self, value : str) -> None:
        '''Sets the name of the pattern.'''
        raise NotImplementedError()
    
    @property
    def pattern_id(self) -> str:
        '''Gets the pattern identifier.'''
        raise NotImplementedError()
    
    @pattern_id.setter
    def pattern_id(self, value : str) -> None:
        '''Sets the pattern identifier.'''
        raise NotImplementedError()
    
    @property
    def horizontal_offset(self) -> int:
        '''Gets the horizontal offset.'''
        raise NotImplementedError()
    
    @horizontal_offset.setter
    def horizontal_offset(self, value : int) -> None:
        '''Sets the horizontal offset.'''
        raise NotImplementedError()
    
    @property
    def vertical_offset(self) -> int:
        '''Gets the vertical offset.'''
        raise NotImplementedError()
    
    @vertical_offset.setter
    def vertical_offset(self, value : int) -> None:
        '''Sets the vertical offset.'''
        raise NotImplementedError()
    
    @property
    def pattern_data(self) -> List[int]:
        '''Gets the pattern data.'''
        raise NotImplementedError()
    
    @pattern_data.setter
    def pattern_data(self, value : List[int]) -> None:
        '''Sets the pattern data.'''
        raise NotImplementedError()
    
    @property
    def pattern_width(self) -> int:
        '''Gets the width of the pattern.'''
        raise NotImplementedError()
    
    @pattern_width.setter
    def pattern_width(self, value : int) -> None:
        '''Sets the width of the pattern.'''
        raise NotImplementedError()
    
    @property
    def pattern_height(self) -> int:
        '''Gets the height of the pattern.'''
        raise NotImplementedError()
    
    @pattern_height.setter
    def pattern_height(self, value : int) -> None:
        '''Sets the height of the pattern.'''
        raise NotImplementedError()
    

class PatternFillSettings(BaseFillSettings):
    '''Pattern fill effect settings'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def generate_lfx_2_resource_nodes(point_type : str, color : aspose.psd.Color, pattern_name : str, identifier : str, scale : float, linked : bool, offset : aspose.psd.PointF) -> System.Collections.Generic.IEnumerable`1[[Aspose.PSD.FileFormats.Psd.Layers.LayerResources.OSTypeStructure]]:
        '''Generates the LFX2 resource nodes.
        
        :param point_type: Type of the point.
        :param color: The color.
        :param pattern_name: Name of the pattern.
        :param identifier: The identifier.
        :param scale: The scale.
        :param linked: if set to ``true`` [linked].
        :param offset: The offset.
        :returns: List of :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure`'''
        raise NotImplementedError()
    
    @property
    def fill_type(self) -> aspose.psd.fileformats.psd.layers.fillsettings.FillType:
        '''The fill type'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    
    @property
    def linked(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.PatternFillSettings` is linked.'''
        raise NotImplementedError()
    
    @linked.setter
    def linked(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.fillsettings.PatternFillSettings` is linked.'''
        raise NotImplementedError()
    
    @property
    def scale(self) -> float:
        '''Gets the scale.'''
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : float) -> None:
        '''Sets the scale.'''
        raise NotImplementedError()
    
    @property
    def align_with_layer(self) -> bool:
        '''Gets a value indicating whether [link with layer].'''
        raise NotImplementedError()
    
    @align_with_layer.setter
    def align_with_layer(self, value : bool) -> None:
        '''Sets a value indicating whether [link with layer].'''
        raise NotImplementedError()
    
    @property
    def point_type(self) -> str:
        '''Gets the type of the point.'''
        raise NotImplementedError()
    
    @point_type.setter
    def point_type(self, value : str) -> None:
        '''Sets the type of the point.'''
        raise NotImplementedError()
    
    @property
    def pattern_name(self) -> str:
        '''Gets the name of the pattern.'''
        raise NotImplementedError()
    
    @pattern_name.setter
    def pattern_name(self, value : str) -> None:
        '''Sets the name of the pattern.'''
        raise NotImplementedError()
    
    @property
    def pattern_id(self) -> str:
        '''Gets the pattern identifier.'''
        raise NotImplementedError()
    
    @pattern_id.setter
    def pattern_id(self, value : str) -> None:
        '''Sets the pattern identifier.'''
        raise NotImplementedError()
    
    @property
    def horizontal_offset(self) -> int:
        '''Gets the horizontal offset.'''
        raise NotImplementedError()
    
    @horizontal_offset.setter
    def horizontal_offset(self, value : int) -> None:
        '''Sets the horizontal offset.'''
        raise NotImplementedError()
    
    @property
    def vertical_offset(self) -> int:
        '''Gets the vertical offset.'''
        raise NotImplementedError()
    
    @vertical_offset.setter
    def vertical_offset(self, value : int) -> None:
        '''Sets the vertical offset.'''
        raise NotImplementedError()
    
    @property
    def pattern_data(self) -> List[int]:
        '''Gets the pattern data.'''
        raise NotImplementedError()
    
    @pattern_data.setter
    def pattern_data(self, value : List[int]) -> None:
        '''Sets the pattern data.'''
        raise NotImplementedError()
    
    @property
    def pattern_width(self) -> int:
        '''Gets the width of the pattern.'''
        raise NotImplementedError()
    
    @pattern_width.setter
    def pattern_width(self, value : int) -> None:
        '''Sets the width of the pattern.'''
        raise NotImplementedError()
    
    @property
    def pattern_height(self) -> int:
        '''Gets the height of the pattern.'''
        raise NotImplementedError()
    
    @pattern_height.setter
    def pattern_height(self, value : int) -> None:
        '''Sets the height of the pattern.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the angle.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the angle.'''
        raise NotImplementedError()
    

class FillType:
    '''The Fill Type'''
    
    COLOR : FillType
    '''The color fill type'''
    GRADIENT : FillType
    '''The gradient fill type'''
    PATTERN : FillType
    '''The pattern fill type'''

class GradientType:
    '''Gradient type'''
    
    LINEAR : GradientType
    '''The linear gradient type'''
    RADIAL : GradientType
    '''The radial gradient type'''
    ANGLE : GradientType
    '''The angle gradient type'''
    REFLECTED : GradientType
    '''The reflected gradient type'''
    DIAMOND : GradientType
    '''The diamond gradient type'''
    SHAPE_BURST : GradientType
    '''The shape burst gradient type'''

