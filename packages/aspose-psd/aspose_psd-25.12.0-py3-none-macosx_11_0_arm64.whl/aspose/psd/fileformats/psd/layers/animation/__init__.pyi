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

class Frame:
    '''The options of time line frame item.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the frame id.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the frame id.'''
        raise NotImplementedError()
    
    @property
    def delay(self) -> int:
        '''Gets the frame delay value in centa-seconds.
        For example, in 1 second contains 100 centa-seconds.'''
        raise NotImplementedError()
    
    @delay.setter
    def delay(self, value : int) -> None:
        '''Sets the frame delay value in centa-seconds.
        For example, in 1 second contains 100 centa-seconds.'''
        raise NotImplementedError()
    
    @property
    def layer_states(self) -> List[aspose.psd.fileformats.psd.layers.animation.LayerState]:
        '''Gets ot sets the layer states of frame.'''
        raise NotImplementedError()
    
    @layer_states.setter
    def layer_states(self, value : List[aspose.psd.fileformats.psd.layers.animation.LayerState]) -> None:
        '''Gets ot sets the layer states of frame.'''
        raise NotImplementedError()
    
    @property
    def disposal_method(self) -> aspose.psd.fileformats.psd.layers.animation.FrameDisposalMethod:
        '''Gets the disposal method of frame.'''
        raise NotImplementedError()
    
    @disposal_method.setter
    def disposal_method(self, value : aspose.psd.fileformats.psd.layers.animation.FrameDisposalMethod) -> None:
        '''Sets the disposal method of frame.'''
        raise NotImplementedError()
    

class LayerState:
    '''The options of time line layer state.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Gets the layer id.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Sets the layer id.'''
        raise NotImplementedError()
    
    @property
    def enabled(self) -> bool:
        '''Gets the enabled state.'''
        raise NotImplementedError()
    
    @enabled.setter
    def enabled(self, value : bool) -> None:
        '''Sets the enabled state.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blending mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blending mode.'''
        raise NotImplementedError()
    
    @property
    def position_offset(self) -> aspose.psd.Point:
        '''Gets the layer position offset related to the actual layer position.'''
        raise NotImplementedError()
    
    @position_offset.setter
    def position_offset(self, value : aspose.psd.Point) -> None:
        '''Sets the layer position offset related to the actual layer position.'''
        raise NotImplementedError()
    
    @property
    def horizontal_fx_rf(self) -> float:
        '''Gets the HorizontalFXRf value.'''
        raise NotImplementedError()
    
    @horizontal_fx_rf.setter
    def horizontal_fx_rf(self, value : float) -> None:
        '''Sets the HorizontalFXRf value.'''
        raise NotImplementedError()
    
    @property
    def vertical_fx_rf(self) -> float:
        '''Gets the VerticalFXRf value.'''
        raise NotImplementedError()
    
    @vertical_fx_rf.setter
    def vertical_fx_rf(self, value : float) -> None:
        '''Sets the VerticalFXRf value.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value.'''
        raise NotImplementedError()
    
    @property
    def fill_opacity(self) -> float:
        '''Gets the fill opacity value.'''
        raise NotImplementedError()
    
    @fill_opacity.setter
    def fill_opacity(self, value : float) -> None:
        '''Sets the fill opacity value.'''
        raise NotImplementedError()
    
    @property
    def state_effects(self) -> aspose.psd.fileformats.psd.layers.animation.LayerStateEffects:
        '''Gets the layer state effects.'''
        raise NotImplementedError()
    

class LayerStateEffects:
    '''The layer state effects.'''
    
    def add_drop_shadow(self) -> aspose.psd.fileformats.psd.layers.layereffects.DropShadowEffect:
        '''Adds the drop shadow effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.DropShadowEffect` class.'''
        raise NotImplementedError()
    
    def add_inner_shadow(self) -> aspose.psd.fileformats.psd.layers.layereffects.InnerShadowEffect:
        '''Adds the inner shadow effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.InnerShadowEffect` class.'''
        raise NotImplementedError()
    
    def add_outer_glow(self) -> aspose.psd.fileformats.psd.layers.layereffects.OuterGlowEffect:
        '''Adds the outer glow effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.OuterGlowEffect` class.'''
        raise NotImplementedError()
    
    def add_stroke(self, fill_type : aspose.psd.fileformats.psd.layers.fillsettings.FillType) -> aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect:
        '''Adds the stroke effect.
        
        :param fill_type: The type stroke fill.
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.StrokeEffect` class.'''
        raise NotImplementedError()
    
    def add_color_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.ColorOverlayEffect:
        '''Adds the color overlay effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.ColorOverlayEffect` class.'''
        raise NotImplementedError()
    
    def add_gradient_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.GradientOverlayEffect:
        '''Adds the gradient overlay effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.GradientOverlayEffect` class.'''
        raise NotImplementedError()
    
    def add_pattern_overlay(self) -> aspose.psd.fileformats.psd.layers.layereffects.PatternOverlayEffect:
        '''Adds the pattern overlay effect.
        
        :returns: The new instance of the :py:class:`aspose.psd.fileformats.psd.layers.layereffects.PatternOverlayEffect` class.'''
        raise NotImplementedError()
    
    def clear_layer_style(self) -> None:
        '''Clears all layer style effects.'''
        raise NotImplementedError()
    
    def remove_effect_at(self, index : int) -> None:
        '''Removes the the layer effect at the specific index.
        
        :param index: The index of layer effect.'''
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
    def effects(self) -> List[aspose.psd.fileformats.psd.layers.layereffects.ILayerEffect]:
        '''Gets the layer effects.'''
        raise NotImplementedError()
    

class Timeline:
    '''The time line options model.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the PsdImage\'s and Timeline data to the specified file location in the specified format according to save options.
        
        :param file_path: The file path.
        :param options: The options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, output_stream : io._IOBase, options : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the PsdImage\'s and Timeline data to the specified stream in the specified format according to save options.
        
        :param output_stream: The output stream.
        :param options: The options.'''
        raise NotImplementedError()
    
    def switch_active_frame(self, target_active_frame_index : int) -> None:
        '''Switches the active frame to targeted.
        
        :param target_active_frame_index: The target frame index.'''
        raise NotImplementedError()
    
    @property
    def af_st(self) -> int:
        '''Gets the AFSt value.'''
        raise NotImplementedError()
    
    @af_st.setter
    def af_st(self, value : int) -> None:
        '''Sets the AFSt value.'''
        raise NotImplementedError()
    
    @property
    def fs_id(self) -> int:
        '''Gets the FsID value.'''
        raise NotImplementedError()
    
    @fs_id.setter
    def fs_id(self, value : int) -> None:
        '''Sets the FsID value.'''
        raise NotImplementedError()
    
    @property
    def active_frame_index(self) -> int:
        '''Gets the active frame index.'''
        raise NotImplementedError()
    
    @property
    def loopes_count(self) -> int:
        '''Gets the count of loops.'''
        raise NotImplementedError()
    
    @loopes_count.setter
    def loopes_count(self, value : int) -> None:
        '''Sets the count of loops.'''
        raise NotImplementedError()
    
    @property
    def frames(self) -> List[aspose.psd.fileformats.psd.layers.animation.Frame]:
        '''Gets the list of frames.'''
        raise NotImplementedError()
    
    @frames.setter
    def frames(self, value : List[aspose.psd.fileformats.psd.layers.animation.Frame]) -> None:
        '''Gets the list of frames.'''
        raise NotImplementedError()
    

class FrameDisposalMethod:
    '''The frame disposal method specifies whether to discard the current frame before displaying the next frame.
    You select a disposal method for animations that include background transparency to specify whether the current
    frame will be visible through the transparent areas of the next frame.'''
    
    AUTOMATIC : FrameDisposalMethod
    '''Determines a disposal method for the current frame automatically, discarding the current frame if the next frame contains layer transparency.
    For most animations, the Automatic option (default) yields the desired results.'''
    DO_NOT_DISPOSE : FrameDisposalMethod
    '''Preserves the current frame as the next frame is added to the display.
    The current frame (and preceding frames) may show through transparent areas of the next frame.'''
    DISPOSE : FrameDisposalMethod
    '''Discards the current frame from the display before the next frame is displayed.
    Only a single frame is displayed at any time (and the current frame does not appear through the transparent areas of the next frame).'''

