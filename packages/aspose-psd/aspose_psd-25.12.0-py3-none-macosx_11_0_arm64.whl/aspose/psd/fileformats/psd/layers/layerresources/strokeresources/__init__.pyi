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

class IStrokeSettings:
    '''Stroke settings of Shapes.'''
    
    @property
    def line_cap(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType:
        '''Stroke line cap type.'''
        raise NotImplementedError()
    
    @line_cap.setter
    def line_cap(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType) -> None:
        '''Stroke line cap type.'''
        raise NotImplementedError()
    
    @property
    def line_join(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType:
        '''Stroke line join type.'''
        raise NotImplementedError()
    
    @line_join.setter
    def line_join(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType) -> None:
        '''Stroke line join type.'''
        raise NotImplementedError()
    
    @property
    def enabled(self) -> bool:
        '''Stroke is enabled.'''
        raise NotImplementedError()
    
    @enabled.setter
    def enabled(self, value : bool) -> None:
        '''Stroke is enabled.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> float:
        '''Stroke line width.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : float) -> None:
        '''Stroke line width.'''
        raise NotImplementedError()
    
    @property
    def line_dash_set(self) -> List[float]:
        '''Gets array of line dashes.'''
        raise NotImplementedError()
    
    @line_dash_set.setter
    def line_dash_set(self, value : List[float]) -> None:
        '''Sets array of line dashes.'''
        raise NotImplementedError()
    
    @property
    def fill(self) -> aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings:
        '''Gets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @fill.setter
    def fill(self, value : aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings) -> None:
        '''Sets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @property
    def line_alignment(self) -> aspose.psd.fileformats.psd.layers.layereffects.StrokePosition:
        '''Gets Stroke style line alignment.'''
        raise NotImplementedError()
    
    @line_alignment.setter
    def line_alignment(self, value : aspose.psd.fileformats.psd.layers.layereffects.StrokePosition) -> None:
        '''Sets Stroke style line alignment.'''
        raise NotImplementedError()
    

class StrokeSettings(IStrokeSettings):
    '''Stroke settings of Shapes.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def line_cap(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType:
        '''Gets Stroke line cap type.'''
        raise NotImplementedError()
    
    @line_cap.setter
    def line_cap(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType) -> None:
        '''Sets Stroke line cap type.'''
        raise NotImplementedError()
    
    @property
    def line_join(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType:
        '''Gets Stroke line join type.'''
        raise NotImplementedError()
    
    @line_join.setter
    def line_join(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType) -> None:
        '''Sets Stroke line join type.'''
        raise NotImplementedError()
    
    @property
    def enabled(self) -> bool:
        '''Gets Stroke is enabled.'''
        raise NotImplementedError()
    
    @enabled.setter
    def enabled(self, value : bool) -> None:
        '''Sets Stroke is enabled.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> float:
        '''Gets Stroke line width.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : float) -> None:
        '''Sets Stroke line width.'''
        raise NotImplementedError()
    
    @property
    def line_dash_set(self) -> List[float]:
        '''Gets array of line dashes.'''
        raise NotImplementedError()
    
    @line_dash_set.setter
    def line_dash_set(self, value : List[float]) -> None:
        '''Sets array of line dashes.'''
        raise NotImplementedError()
    
    @property
    def fill(self) -> aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings:
        '''Gets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @fill.setter
    def fill(self, value : aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings) -> None:
        '''Sets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @property
    def line_alignment(self) -> aspose.psd.fileformats.psd.layers.layereffects.StrokePosition:
        '''Gets Stroke style line alignment.'''
        raise NotImplementedError()
    
    @line_alignment.setter
    def line_alignment(self, value : aspose.psd.fileformats.psd.layers.layereffects.StrokePosition) -> None:
        '''Sets Stroke style line alignment.'''
        raise NotImplementedError()
    

class VscgResource(aspose.psd.fileformats.psd.layers.LayerResource):
    '''Vector Stroke Content Data resource.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer, psd_version : int) -> None:
        '''Saves the resource to the specified stream container.
        
        :param stream_container: The stream container to save to.
        :param psd_version: The PSD version.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the signature.'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the layer resource key.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the layer resource length in bytes.'''
        raise NotImplementedError()
    
    @property
    def psd_version(self) -> int:
        '''Gets the minimal psd version required for layer resource. 0 indicates no restrictions.'''
        raise NotImplementedError()
    
    @property
    def RESOURCE_SIGNATURE(self) -> int:
        '''The common resource signature.'''
        raise NotImplementedError()

    @property
    def PSB_RESOURCE_SIGNATURE(self) -> int:
        '''The PSB-specific resource signature.'''
        raise NotImplementedError()

    @property
    def key_for_data(self) -> int:
        '''Gets integer key that defines what kind of fill settings is stored in the resource:
        * Color - 0x536f436f - SoCoResource.TypeToolKey
        * Gradient - 0x4764466c - GdFlResource.TypeToolKey
        * Pattern - 0x5074466c - PtFlResource.TypeToolKey
        Warning! The value of property KeyForData should match the type of Fill settings stored in Items structures.'''
        raise NotImplementedError()
    
    @property
    def items(self) -> List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure]:
        '''Gets the array of structure items.
        **Warning:** The `Items` array values must match with the `KeyForData` property, which determines the type of fill settings stored in the structures within `Items`.'''
        raise NotImplementedError()
    
    @property
    def TYPE_TOOL_KEY(self) -> int:
        '''The type tool info key.'''
        raise NotImplementedError()


class VstkResource(aspose.psd.fileformats.psd.layers.LayerResource):
    '''Resource class VstkResource. Contains information about Vector Stroke Data.
    Resource should be initialized either by AssignItems method from ResourceLoader,
    either by assigning values to properties of the class.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def save(self, stream_container : aspose.psd.StreamContainer, psd_version : int) -> None:
        '''Saves the resource to the specified stream container.
        
        :param stream_container: The stream container to save to.
        :param psd_version: The PSD version.'''
        raise NotImplementedError()
    
    @property
    def signature(self) -> int:
        '''Gets the signature.'''
        raise NotImplementedError()
    
    @property
    def key(self) -> int:
        '''Gets the layer resource key.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the layer resource length in bytes.'''
        raise NotImplementedError()
    
    @property
    def psd_version(self) -> int:
        '''Gets the minimal psd version required for layer resource. 0 indicates no restrictions.'''
        raise NotImplementedError()
    
    @property
    def RESOURCE_SIGNATURE(self) -> int:
        '''The common resource signature.'''
        raise NotImplementedError()

    @property
    def PSB_RESOURCE_SIGNATURE(self) -> int:
        '''The PSB-specific resource signature.'''
        raise NotImplementedError()

    @property
    def stroke_style_version(self) -> int:
        '''Gets the stroke style version.'''
        raise NotImplementedError()
    
    @stroke_style_version.setter
    def stroke_style_version(self, value : int) -> None:
        '''Sets the stroke style version.'''
        raise NotImplementedError()
    
    @property
    def stroke_enabled(self) -> bool:
        '''Gets a value indicating whether stroke effect enabled.'''
        raise NotImplementedError()
    
    @stroke_enabled.setter
    def stroke_enabled(self, value : bool) -> None:
        '''Sets a value indicating whether stroke effect enabled.'''
        raise NotImplementedError()
    
    @property
    def fill_enabled(self) -> bool:
        '''Gets a value indicating whether Stroke fill enabled.'''
        raise NotImplementedError()
    
    @fill_enabled.setter
    def fill_enabled(self, value : bool) -> None:
        '''Sets a value indicating whether Stroke fill enabled.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_dash_offset(self) -> int:
        '''Gets the stroke style line dash offset.'''
        raise NotImplementedError()
    
    @stroke_style_line_dash_offset.setter
    def stroke_style_line_dash_offset(self, value : int) -> None:
        '''Sets the stroke style line dash offset.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_miter_limit(self) -> float:
        '''Gets the stroke style miter limit.'''
        raise NotImplementedError()
    
    @stroke_style_miter_limit.setter
    def stroke_style_miter_limit(self, value : float) -> None:
        '''Sets the stroke style miter limit.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_cap_type(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType:
        '''Gets the type of the stroke style line cap.'''
        raise NotImplementedError()
    
    @stroke_style_line_cap_type.setter
    def stroke_style_line_cap_type(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineCapType) -> None:
        '''Sets the type of the stroke style line cap.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_cap_width(self) -> float:
        '''Gets Stroke line cap width.'''
        raise NotImplementedError()
    
    @stroke_style_line_cap_width.setter
    def stroke_style_line_cap_width(self, value : float) -> None:
        '''Sets Stroke line cap width.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_width(self) -> float:
        '''Gets Stroke line width.'''
        raise NotImplementedError()
    
    @stroke_style_line_width.setter
    def stroke_style_line_width(self, value : float) -> None:
        '''Sets Stroke line width.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_join_type(self) -> aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType:
        '''Gets Stroke style line join type.'''
        raise NotImplementedError()
    
    @stroke_style_line_join_type.setter
    def stroke_style_line_join_type(self, value : aspose.psd.fileformats.psd.layers.layerresources.strokeresources.LineJoinType) -> None:
        '''Sets Stroke style line join type.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_alignment(self) -> aspose.psd.fileformats.psd.layers.layereffects.StrokePosition:
        '''Gets Stroke style line alignment.'''
        raise NotImplementedError()
    
    @stroke_style_line_alignment.setter
    def stroke_style_line_alignment(self, value : aspose.psd.fileformats.psd.layers.layereffects.StrokePosition) -> None:
        '''Sets Stroke style line alignment.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_scale_lock(self) -> bool:
        '''Gets Stroke style scale lock.'''
        raise NotImplementedError()
    
    @stroke_style_scale_lock.setter
    def stroke_style_scale_lock(self, value : bool) -> None:
        '''Sets Stroke style scale lock.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_stroke_adjust(self) -> bool:
        '''Gets Stroke adjust.'''
        raise NotImplementedError()
    
    @stroke_style_stroke_adjust.setter
    def stroke_style_stroke_adjust(self, value : bool) -> None:
        '''Sets Stroke adjust.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets Stroke Blend mode.'''
        raise NotImplementedError()
    
    @stroke_style_blend_mode.setter
    def stroke_style_blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets Stroke Blend mode.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_opacity(self) -> int:
        '''Gets Stroke style opacity (0-100%).'''
        raise NotImplementedError()
    
    @stroke_style_opacity.setter
    def stroke_style_opacity(self, value : int) -> None:
        '''Sets Stroke style opacity (0-100%).'''
        raise NotImplementedError()
    
    @property
    def stroke_style_resolution(self) -> float:
        '''Gets Stroke style resolution.'''
        raise NotImplementedError()
    
    @stroke_style_resolution.setter
    def stroke_style_resolution(self, value : float) -> None:
        '''Sets Stroke style resolution.'''
        raise NotImplementedError()
    
    @property
    def fill_settings(self) -> aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings:
        '''Gets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @fill_settings.setter
    def fill_settings(self, value : aspose.psd.fileformats.psd.layers.fillsettings.IFillSettings) -> None:
        '''Sets Fill settings of the Stroke.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_content(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''Gets Stroke entity. Property determines fill settings of the stroke.'''
        raise NotImplementedError()
    
    @stroke_style_content.setter
    def stroke_style_content(self, value : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure) -> None:
        '''Sets Stroke entity. Property determines fill settings of the stroke.'''
        raise NotImplementedError()
    
    @property
    def stroke_style_line_dash_set(self) -> List[float]:
        '''Gets array of line dashes.'''
        raise NotImplementedError()
    
    @stroke_style_line_dash_set.setter
    def stroke_style_line_dash_set(self, value : List[float]) -> None:
        '''Sets array of line dashes.'''
        raise NotImplementedError()
    
    @property
    def TYPE_TOOL_KEY(self) -> int:
        '''The type tool info key.'''
        raise NotImplementedError()


class LineCapType:
    '''Line Cap type.'''
    
    ROUND_CAP : LineCapType
    '''Round cap type.'''
    SQUARE_CAP : LineCapType
    '''Square cap type.'''
    BUTT_CAP : LineCapType
    '''Butt cap type.'''

class LineJoinType:
    '''Line Join type.'''
    
    BEVEL_JOIN : LineJoinType
    '''Bevel join type.'''
    ROUND_JOIN : LineJoinType
    '''Rounnd join type.'''
    MITER_JOIN : LineJoinType
    '''Miter join type.'''

