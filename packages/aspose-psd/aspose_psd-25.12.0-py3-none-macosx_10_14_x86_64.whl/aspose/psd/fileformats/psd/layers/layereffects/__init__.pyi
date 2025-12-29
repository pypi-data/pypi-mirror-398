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

class BlendingOptions:
    '''BlendingOptions. It\'s a wrapper for BaseFxResource which provides api for layer effects'''
    
    def add_color_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.ColorOverlayEffect:
        '''Adds the color overlay.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.ColorOverlayEffect` object'''
        raise NotImplementedError()
    
    def add_gradient_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.GradientOverlayEffect:
        '''Adds the Gradient overlay.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.GradientOverlayEffect` object'''
        raise NotImplementedError()
    
    def add_pattern_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.PatternOverlayEffect:
        '''Adds the Pattern overlay.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.PatternOverlayEffect` object'''
        raise NotImplementedError()
    
    def add_drop_shadow(self) -> aspose.psd.fileformats.psd.layers.layereffects.DropShadowEffect:
        '''Adds the drop shadow effect.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.DropShadowEffect` object'''
        raise NotImplementedError()
    
    def add_outer_glow(self) -> aspose.psd.fileformats.psd.layers.layereffects.OuterGlowEffect:
        '''Adds the outer glow effect.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.OuterGlowEffect` object'''
        raise NotImplementedError()
    
    def add_inner_shadow(self) -> aspose.psd.fileformats.psd.layers.layereffects.InnerShadowEffect:
        '''Adds the inner shadow effect.
        
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.InnerShadowEffect` object'''
        raise NotImplementedError()
    
    def add_stroke(self, fill_type : aspose.psd.fileformats.psd.layers.fillsettings.FillType) -> aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect:
        '''Adds the stroke effect.
        
        :param fill_type: The type of fill to fill the stroke.
        :returns: Created :py:class:`aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect` object.'''
        raise NotImplementedError()
    
    @property
    def effects(self) -> List[aspose.psd.fileformats.psd.layers.layereffects.ILayerEffect]:
        '''Gets the effects.'''
        raise NotImplementedError()
    
    @effects.setter
    def effects(self, value : List[aspose.psd.fileformats.psd.layers.layereffects.ILayerEffect]) -> None:
        '''Gets the effects.'''
        raise NotImplementedError()
    
    @property
    def are_effects_enabled(self) -> bool:
        '''Gets the visibility of all layer effects.'''
        raise NotImplementedError()
    
    @are_effects_enabled.setter
    def are_effects_enabled(self, value : bool) -> None:
        '''Sets the visibility of all layer effects.'''
        raise NotImplementedError()
    

class ColorOverlayEffect(ILayerEffect):
    '''Color Overlay Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
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
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    

class DropShadowEffect(IShadowEffect):
    '''Drop Shadow Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
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
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> int:
        '''Gets the angle in degrees.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : int) -> None:
        '''Sets the angle in degrees.'''
        raise NotImplementedError()
    
    @property
    def use_global_light(self) -> bool:
        '''Gets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @use_global_light.setter
    def use_global_light(self, value : bool) -> None:
        '''Sets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @property
    def distance(self) -> int:
        '''Gets the distance in pixels.'''
        raise NotImplementedError()
    
    @distance.setter
    def distance(self, value : int) -> None:
        '''Sets the distance in pixels.'''
        raise NotImplementedError()
    
    @property
    def spread(self) -> int:
        '''Gets the intensity as a percent.'''
        raise NotImplementedError()
    
    @spread.setter
    def spread(self, value : int) -> None:
        '''Sets the intensity as a percent.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the blur value in pixels.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the blur value in pixels.'''
        raise NotImplementedError()
    
    @property
    def noise(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @noise.setter
    def noise(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    
    @property
    def knocks_out(self) -> bool:
        '''Gets a value indicating whether [knocks out].'''
        raise NotImplementedError()
    
    @knocks_out.setter
    def knocks_out(self, value : bool) -> None:
        '''Sets a value indicating whether [knocks out].'''
        raise NotImplementedError()
    

class GradientOverlayEffect(ILayerEffect):
    '''Gradient Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
        raise NotImplementedError()
    
    @property
    def settings(self) -> aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings:
        '''Gets the settings.'''
        raise NotImplementedError()
    
    @settings.setter
    def settings(self, value : aspose.psd.fileformats.psd.layers.fillsettings.GradientFillSettings) -> None:
        '''Sets the settings.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    

class ILayerEffect:
    '''Interface for Layer Effects'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity where 255 = 100%'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity where 255 = 100%'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
        raise NotImplementedError()
    

class IShadowEffect:
    '''Interface for Shadow Layer Effects'''
    
    @property
    def color(self) -> aspose.psd.Color:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.psd.Color) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> int:
        '''Gets the angle in degrees.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : int) -> None:
        '''Sets the angle in degrees.'''
        raise NotImplementedError()
    
    @property
    def use_global_light(self) -> bool:
        '''Gets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @use_global_light.setter
    def use_global_light(self, value : bool) -> None:
        '''Sets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @property
    def distance(self) -> int:
        '''Gets the distance in pixels.'''
        raise NotImplementedError()
    
    @distance.setter
    def distance(self, value : int) -> None:
        '''Sets the distance in pixels.'''
        raise NotImplementedError()
    
    @property
    def spread(self) -> int:
        '''Gets the intensity as a percent.'''
        raise NotImplementedError()
    
    @spread.setter
    def spread(self, value : int) -> None:
        '''Sets the intensity as a percent.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the blur value in pixels.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the blur value in pixels.'''
        raise NotImplementedError()
    
    @property
    def noise(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @noise.setter
    def noise(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    

class InnerShadowEffect(IShadowEffect):
    '''Inner Shadow Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
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
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> int:
        '''Gets the angle in degrees.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : int) -> None:
        '''Sets the angle in degrees.'''
        raise NotImplementedError()
    
    @property
    def use_global_light(self) -> bool:
        '''Gets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @use_global_light.setter
    def use_global_light(self, value : bool) -> None:
        '''Sets a value indicating whether [use this angle in all of the layer effects].'''
        raise NotImplementedError()
    
    @property
    def distance(self) -> int:
        '''Gets the distance in pixels.'''
        raise NotImplementedError()
    
    @distance.setter
    def distance(self, value : int) -> None:
        '''Sets the distance in pixels.'''
        raise NotImplementedError()
    
    @property
    def spread(self) -> int:
        '''Gets the spread (choke) as percentage.'''
        raise NotImplementedError()
    
    @spread.setter
    def spread(self, value : int) -> None:
        '''Sets the spread (choke) as percentage.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the blur value in pixels.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the blur value in pixels.'''
        raise NotImplementedError()
    
    @property
    def noise(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @noise.setter
    def noise(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    

class OuterGlowEffect(ILayerEffect):
    '''Outer Glow Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def fill_color(self) -> aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings:
        '''Gets the color.'''
        raise NotImplementedError()
    
    @fill_color.setter
    def fill_color(self, value : aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings) -> None:
        '''Sets the color.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect type'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    
    @property
    def intensity(self) -> int:
        '''Gets the angle in degrees.'''
        raise NotImplementedError()
    
    @intensity.setter
    def intensity(self, value : int) -> None:
        '''Sets the angle in degrees.'''
        raise NotImplementedError()
    
    @property
    def is_anti_aliasing(self) -> bool:
        '''Gets enabled AntiAliasing effect'''
        raise NotImplementedError()
    
    @is_anti_aliasing.setter
    def is_anti_aliasing(self, value : bool) -> None:
        '''Sets enabled AntiAliasing effect'''
        raise NotImplementedError()
    
    @property
    def spread(self) -> int:
        '''Gets the intensity as a percent.'''
        raise NotImplementedError()
    
    @spread.setter
    def spread(self, value : int) -> None:
        '''Sets the intensity as a percent.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the blur value in pixels.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Gets the blur value in pixels.'''
        raise NotImplementedError()
    
    @property
    def noise(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @noise.setter
    def noise(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    
    @property
    def is_soft_blend(self) -> bool:
        '''Gets a value indicating whether [knocks out].'''
        raise NotImplementedError()
    
    @is_soft_blend.setter
    def is_soft_blend(self, value : bool) -> None:
        '''Sets a value indicating whether [knocks out].'''
        raise NotImplementedError()
    
    @property
    def range(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @range.setter
    def range(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    
    @property
    def jitter(self) -> int:
        '''Gets the noise.'''
        raise NotImplementedError()
    
    @jitter.setter
    def jitter(self, value : int) -> None:
        '''Sets the noise.'''
        raise NotImplementedError()
    

class PatternOverlayEffect(ILayerEffect):
    '''Pattern Layer effect'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect type'''
        raise NotImplementedError()
    
    @property
    def settings(self) -> aspose.psd.fileformats.psd.layers.fillsettings.PatternFillSettings:
        '''Gets the settings.'''
        raise NotImplementedError()
    
    @settings.setter
    def settings(self, value : aspose.psd.fileformats.psd.layers.fillsettings.PatternFillSettings) -> None:
        '''Sets the settings.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    

class StrokeEffect(ILayerEffect):
    '''The Adobe® Photoshop® stroke effect for the PSD layer.'''
    
    def get_effect_bounds(self, layer_bounds : aspose.psd.Rectangle, global_angle : int) -> aspose.psd.Rectangle:
        '''Calculate and gets the bounds of effect pixels based on input layer pixels bounds.
        
        :param layer_bounds: The layer pixels bounds.
        :param global_angle: The global angle to calculate global light angle.
        :returns: The bounds of effect pixels based on input layer pixels bounds.'''
        raise NotImplementedError()
    
    @property
    def effect_type(self) -> aspose.psd.fileformats.psd.layers.layereffects.LayerEffectsTypes:
        '''Gets a type of effect'''
        raise NotImplementedError()
    
    @property
    def overprint(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect` will blend stroke against current layer contents.'''
        raise NotImplementedError()
    
    @overprint.setter
    def overprint(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect` will blend stroke against current layer contents.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> aspose.psd.fileformats.psd.layers.layereffects.StrokePosition:
        '''Gets the position of the stroke effect to control the alignment of your stroke to the PSD layer content.
        The value can be :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.INSIDE` to draw stroke inside of the PSD layer content,
        or :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.OUTSIDE` to draw stroke around of PSD layer content,
        and :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.CENTER` to draw stroke both inside and outside.'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : aspose.psd.fileformats.psd.layers.layereffects.StrokePosition) -> None:
        '''Sets the position of the stroke effect to control the alignment of your stroke to the PSD layer content.
        The value can be :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.INSIDE` to draw stroke inside of the PSD layer content,
        or :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.OUTSIDE` to draw stroke around of PSD layer content,
        and :py:attr:`aspose.psd.fileformats.psd.layers.layereffects.StrokePosition.CENTER` to draw stroke both inside and outside.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the width of stroke effect.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the width of stroke effect.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blend mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blend mode.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Gets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Sets a value indicating whether this instance is visible.'''
        raise NotImplementedError()
    
    @property
    def fill_settings(self) -> aspose.psd.fileformats.psd.layers.fillsettings.BaseFillSettings:
        '''Gets the fill settings.'''
        raise NotImplementedError()
    
    @fill_settings.setter
    def fill_settings(self, value : aspose.psd.fileformats.psd.layers.fillsettings.BaseFillSettings) -> None:
        '''Sets the fill settings.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> int:
        '''Gets the opacity.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : int) -> None:
        '''Sets the opacity.'''
        raise NotImplementedError()
    

class LayerEffectsTypes:
    '''Layer blending effects.'''
    
    DROP_SHADOW : LayerEffectsTypes
    '''The drop shadow.'''
    OUTER_GLOW : LayerEffectsTypes
    '''The outer glow.'''
    PATTERN_OVERLAY : LayerEffectsTypes
    '''The pattern overlay.'''
    GRADIENT_OVERLAY : LayerEffectsTypes
    '''The gradient overlay.'''
    COLOR_OVERLAY : LayerEffectsTypes
    '''The color overlay.'''
    SATIN : LayerEffectsTypes
    '''The satin Effect Type.'''
    INNER_GLOW : LayerEffectsTypes
    '''The inner glow.'''
    INNER_SHADOW : LayerEffectsTypes
    '''The inner shadow.'''
    STROKE : LayerEffectsTypes
    '''The stroke.'''
    BEVEL_EMBOSS : LayerEffectsTypes
    '''The bevel emboss.'''

class StrokePosition:
    '''The position setting controls the alignment of your stroke to the layer it\'s applied to in the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect`.'''
    
    INSIDE : StrokePosition
    '''The stroke will be created from the edge of the shape and grow inward, to the center of the object.'''
    CENTER : StrokePosition
    '''The stroke will be created from the edge of the shape and grow both inwards and outwards.'''
    OUTSIDE : StrokePosition
    '''The stroke will be created from the edge of the shape and will grow outwards, away from the object.'''

