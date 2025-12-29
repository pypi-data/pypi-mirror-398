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

class BaseGradient:
    '''Base gradient definition class. It contains common properties for both types of gradient (Solid and Noise).'''
    
    @property
    def gradient_name(self) -> str:
        '''Gets the name of the gradient.'''
        raise NotImplementedError()
    
    @gradient_name.setter
    def gradient_name(self, value : str) -> None:
        '''Sets the name of the gradient.'''
        raise NotImplementedError()
    
    @property
    def gradient_mode(self) -> aspose.psd.fileformats.psd.layers.gradient.GradientKind:
        '''Gets the mode for this gradient.
        Determines \'Gradient Type\' = \'Solid/Noise\' (0/1).'''
        raise NotImplementedError()
    

class NoiseGradient(BaseGradient):
    '''Noise gradient definition class.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def gradient_name(self) -> str:
        '''Gets the name of the gradient.'''
        raise NotImplementedError()
    
    @gradient_name.setter
    def gradient_name(self, value : str) -> None:
        '''Sets the name of the gradient.'''
        raise NotImplementedError()
    
    @property
    def gradient_mode(self) -> aspose.psd.fileformats.psd.layers.gradient.GradientKind:
        '''Gets the mode for this gradient.
        Determines \'Gradient Type\' = \'Solid/Noise\' (0/1).'''
        raise NotImplementedError()
    
    @property
    def rnd_number_seed(self) -> int:
        '''Gets the random number seed used to generate colors for Noise gradient'''
        raise NotImplementedError()
    
    @rnd_number_seed.setter
    def rnd_number_seed(self, value : int) -> None:
        '''Sets the random number seed used to generate colors for Noise gradient'''
        raise NotImplementedError()
    
    @property
    def show_transparency(self) -> bool:
        '''Gets the flag for showing transparency.'''
        raise NotImplementedError()
    
    @show_transparency.setter
    def show_transparency(self, value : bool) -> None:
        '''Sets the flag for showing transparency.'''
        raise NotImplementedError()
    
    @property
    def use_vector_color(self) -> bool:
        '''Gets the flag for using vector color.'''
        raise NotImplementedError()
    
    @use_vector_color.setter
    def use_vector_color(self, value : bool) -> None:
        '''Sets the flag for using vector color.'''
        raise NotImplementedError()
    
    @property
    def roughness(self) -> int:
        '''Gets the Roughness factor.'''
        raise NotImplementedError()
    
    @roughness.setter
    def roughness(self, value : int) -> None:
        '''Sets the Roughness factor.'''
        raise NotImplementedError()
    
    @property
    def color_model(self) -> aspose.psd.fileformats.psd.layers.gradient.NoiseColorModel:
        '''Gets the Color Model - RGB/HSB/LAB (3/4/6).'''
        raise NotImplementedError()
    
    @color_model.setter
    def color_model(self, value : aspose.psd.fileformats.psd.layers.gradient.NoiseColorModel) -> None:
        '''Sets the Color Model - RGB/HSB/LAB (3/4/6).'''
        raise NotImplementedError()
    
    @property
    def minimum_color(self) -> aspose.psd.fileformats.psd.core.rawcolor.RawColor:
        '''Gets the Minimum color of PixelDataFormat.'''
        raise NotImplementedError()
    
    @minimum_color.setter
    def minimum_color(self, value : aspose.psd.fileformats.psd.core.rawcolor.RawColor) -> None:
        '''Sets the Minimum color of PixelDataFormat.'''
        raise NotImplementedError()
    
    @property
    def maximum_color(self) -> aspose.psd.fileformats.psd.core.rawcolor.RawColor:
        '''Gets the Maximum color of PixelDataFormat.'''
        raise NotImplementedError()
    
    @maximum_color.setter
    def maximum_color(self, value : aspose.psd.fileformats.psd.core.rawcolor.RawColor) -> None:
        '''Sets the Maximum color of PixelDataFormat.'''
        raise NotImplementedError()
    
    @property
    def expansion_count(self) -> int:
        '''Gets the Expansion count ( = 2 for Photoshop 6.0).'''
        raise NotImplementedError()
    
    @expansion_count.setter
    def expansion_count(self, value : int) -> None:
        '''Sets the Expansion count ( = 2 for Photoshop 6.0).'''
        raise NotImplementedError()
    

class SolidGradient(BaseGradient):
    '''Gradient fill effect settings.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def generate_lfx_2_resource_nodes() -> System.Collections.Generic.List`1[[Aspose.PSD.FileFormats.Psd.Layers.LayerResources.OSTypeStructure]]:
        '''Generates the LFX2 resource nodes.
        
        :returns: Generated List of :py:class:`aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure`'''
        raise NotImplementedError()
    
    def add_color_point(self) -> aspose.psd.fileformats.psd.layers.fillsettings.GradientColorPoint:
        '''Adds the color point.
        
        :returns: Created color point'''
        raise NotImplementedError()
    
    def add_transparency_point(self) -> aspose.psd.fileformats.psd.layers.fillsettings.GradientTransparencyPoint:
        '''Adds the color point.
        
        :returns: Created transparency point'''
        raise NotImplementedError()
    
    def remove_transparency_point(self, point : aspose.psd.fileformats.psd.layers.fillsettings.IGradientTransparencyPoint) -> None:
        '''Removes the transparency point.
        
        :param point: The point.'''
        raise NotImplementedError()
    
    def remove_color_point(self, point : aspose.psd.fileformats.psd.layers.IGradientColorPoint) -> None:
        '''Removes the color point.
        
        :param point: The point.'''
        raise NotImplementedError()
    
    @property
    def gradient_name(self) -> str:
        '''Gets the name of the gradient.'''
        raise NotImplementedError()
    
    @gradient_name.setter
    def gradient_name(self, value : str) -> None:
        '''Sets the name of the gradient.'''
        raise NotImplementedError()
    
    @property
    def gradient_mode(self) -> aspose.psd.fileformats.psd.layers.gradient.GradientKind:
        '''Gets the mode for this gradient.
        Determines \'Gradient Type\' = \'Solid/Noise\' (0/1).'''
        raise NotImplementedError()
    
    @property
    def color_points(self) -> List[aspose.psd.fileformats.psd.layers.IGradientColorPoint]:
        '''Gets the color points.'''
        raise NotImplementedError()
    
    @color_points.setter
    def color_points(self, value : List[aspose.psd.fileformats.psd.layers.IGradientColorPoint]) -> None:
        '''Sets the color points.'''
        raise NotImplementedError()
    
    @property
    def transparency_points(self) -> List[aspose.psd.fileformats.psd.layers.fillsettings.IGradientTransparencyPoint]:
        '''Gets the transparency points.'''
        raise NotImplementedError()
    
    @transparency_points.setter
    def transparency_points(self, value : List[aspose.psd.fileformats.psd.layers.fillsettings.IGradientTransparencyPoint]) -> None:
        '''Sets the transparency points.'''
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
    def interpolation(self) -> int:
        '''Gets ot sets Interpolation. Determines Smoothness, when \'Gradient Type\' = \'Solid\'. Value range: 0-4096.'''
        raise NotImplementedError()
    
    @interpolation.setter
    def interpolation(self, value : int) -> None:
        '''Gets ot sets Interpolation. Determines Smoothness, when \'Gradient Type\' = \'Solid\'. Value range: 0-4096.'''
        raise NotImplementedError()
    

class GradientKind:
    '''Gradient type enum.'''
    
    SOLID : GradientKind
    '''Solid Gradient kind'''
    NOISE : GradientKind
    '''Noise Gradient kind'''

class NoiseColorModel:
    '''Color Model
    When \'Gradient type\' = \'Noise\', we can assign \'Color Model\' to RGB/SHB/LAB (3/4/6)'''
    
    RGB : NoiseColorModel
    '''RGB color model.'''
    HSB : NoiseColorModel
    '''HSB color model.'''
    LAB : NoiseColorModel
    '''LAB color mdoel.'''

