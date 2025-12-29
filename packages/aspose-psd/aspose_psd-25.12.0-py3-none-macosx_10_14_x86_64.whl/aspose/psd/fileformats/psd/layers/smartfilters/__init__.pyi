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

class AddNoiseSmartFilter(SmartFilter):
    '''The AddNoise smart filter.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.smartfilters.AddNoiseSmartFilter` class.'''
        raise NotImplementedError()
    
    def apply(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.RasterImage` image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    def apply_to_mask(self, layer_with_mask : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.fileformats.psd.layers.Layer` mask data.
        
        :param layer_with_mask: The layer with mask data.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter:
        '''Makes the memberwise clone of the current instance of the type.
        
        :returns: Returns the memberwise clone of the current instance of the type.'''
        raise NotImplementedError()
    
    @property
    def source_descriptor(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''The source descriptor structure with smart filter data.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the smart filter name.'''
        raise NotImplementedError()
    
    @property
    def filter_id(self) -> int:
        '''Gets the smart filter type identifier.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Sets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value of smart filter.'''
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
    def distribution(self) -> aspose.psd.fileformats.psd.layers.smartfilters.NoiseDistribution:
        '''Gets the distribution of noise filter.'''
        raise NotImplementedError()
    
    @distribution.setter
    def distribution(self, value : aspose.psd.fileformats.psd.layers.smartfilters.NoiseDistribution) -> None:
        '''Sets the distribution of noise filter.'''
        raise NotImplementedError()
    
    @property
    def amount_noise(self) -> float:
        '''Gets The noise value amount.'''
        raise NotImplementedError()
    
    @amount_noise.setter
    def amount_noise(self, value : float) -> None:
        '''Sets The noise value amount.'''
        raise NotImplementedError()
    
    @property
    def is_monochromatic(self) -> bool:
        '''Gets the value of monochromatic.'''
        raise NotImplementedError()
    
    @is_monochromatic.setter
    def is_monochromatic(self, value : bool) -> None:
        '''Sets the value of monochromatic.'''
        raise NotImplementedError()
    
    @property
    def FILTER_TYPE(self) -> int:
        '''The identifier of current smart filter.'''
        raise NotImplementedError()


class GaussianBlurSmartFilter(SmartFilter):
    '''The GaussianBlur smart filter.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.smartfilters.GaussianBlurSmartFilter` class.'''
        raise NotImplementedError()
    
    def apply(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.RasterImage` image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    def apply_to_mask(self, layer_with_mask : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.fileformats.psd.layers.Layer` mask data.
        
        :param layer_with_mask: The layer with mask data.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter:
        '''Makes the memberwise clone of the current instance of the type.
        
        :returns: Returns the memberwise clone of the current instance of the type.'''
        raise NotImplementedError()
    
    @property
    def source_descriptor(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''The source descriptor structure with smart filter data.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the smart filter name.'''
        raise NotImplementedError()
    
    @property
    def filter_id(self) -> int:
        '''Gets the smart filter type identifier.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Sets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value of smart filter.'''
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
    def radius(self) -> float:
        '''Gets the radius of gaussian smart filter.'''
        raise NotImplementedError()
    
    @radius.setter
    def radius(self, value : float) -> None:
        '''Sets the radius of gaussian smart filter.'''
        raise NotImplementedError()
    
    @property
    def FILTER_TYPE(self) -> int:
        '''The identifier of current smart filter.'''
        raise NotImplementedError()


class SharpenSmartFilter(SmartFilter):
    '''The Sharpen smart filter.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.smartfilters.SharpenSmartFilter` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, source_descriptor : aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.smartfilters.SharpenSmartFilter` class.
        
        :param source_descriptor: The descriptor structure with smart filter info.'''
        raise NotImplementedError()
    
    def apply(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.RasterImage` image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    def apply_to_mask(self, layer_with_mask : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.fileformats.psd.layers.Layer` mask data.
        
        :param layer_with_mask: The layer with mask data.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter:
        '''Makes the memberwise clone of the current instance of the type.
        
        :returns: Returns the memberwise clone of the current instance of the type.'''
        raise NotImplementedError()
    
    @property
    def source_descriptor(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''The source descriptor structure with smart filter data.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the smart filter name.'''
        raise NotImplementedError()
    
    @property
    def filter_id(self) -> int:
        '''Gets the smart filter type identifier.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Sets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value of smart filter.'''
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
    def FILTER_TYPE(self) -> int:
        '''The identifier of current smart filter.'''
        raise NotImplementedError()


class SmartFilter:
    '''The class to process a base logic of smart filters.'''
    
    def apply(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.RasterImage` image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    def apply_to_mask(self, layer_with_mask : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.fileformats.psd.layers.Layer` mask data.
        
        :param layer_with_mask: The layer with mask data.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter:
        '''Makes the memberwise clone of the current instance of the type.
        
        :returns: Returns the memberwise clone of the current instance of the type.'''
        raise NotImplementedError()
    
    @property
    def source_descriptor(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''The source descriptor structure with smart filter data.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the smart filter name.'''
        raise NotImplementedError()
    
    @property
    def filter_id(self) -> int:
        '''Gets the smart filter type identifier.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Sets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blending mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blending mode.'''
        raise NotImplementedError()
    

class SmartFilters:
    '''The smart filters of :py:class:`aspose.psd.fileformats.psd.layers.smartobjects.SmartObjectLayer`.'''
    
    def update_resource_values(self) -> None:
        '''Updates the smart filter data into the :py:class:`aspose.psd.fileformats.psd.layers.layerresources.SmartObjectResource`.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter mask.'''
        raise NotImplementedError()
    
    @property
    def is_valid_at_position(self) -> bool:
        '''Gets the is valid at position status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def is_mask_enabled(self) -> bool:
        '''Gets the is mask enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def is_mask_linked(self) -> bool:
        '''Gets the is mask linked status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def is_mask_extend_with_white(self) -> bool:
        '''Gets the is mask exted with white status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def filters(self) -> List[aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter]:
        '''Gets the smart filters.'''
        raise NotImplementedError()
    
    @filters.setter
    def filters(self, value : List[aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter]) -> None:
        '''Sets the smart filters.'''
        raise NotImplementedError()
    

class UnknownSmartFilter(SmartFilter):
    '''The class to hold unknown smart filter data.'''
    
    def apply(self, raster_image : aspose.psd.RasterImage) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.RasterImage` image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    def apply_to_mask(self, layer_with_mask : aspose.psd.fileformats.psd.layers.Layer) -> None:
        '''Applies the current filter to input :py:class:`aspose.psd.fileformats.psd.layers.Layer` mask data.
        
        :param layer_with_mask: The layer with mask data.'''
        raise NotImplementedError()
    
    def clone(self) -> aspose.psd.fileformats.psd.layers.smartfilters.SmartFilter:
        '''Makes the memberwise clone of the current instance of the type.
        
        :returns: Returns the memberwise clone of the current instance of the type.'''
        raise NotImplementedError()
    
    @property
    def source_descriptor(self) -> aspose.psd.fileformats.psd.layers.layerresources.typetoolinfostructures.DescriptorStructure:
        '''The source descriptor structure with smart filter data.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the smart filter name.'''
        raise NotImplementedError()
    
    @property
    def filter_id(self) -> int:
        '''Gets the smart filter type identifier.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Gets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Sets the is enabled status of the smart filter.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets the opacity value of smart filter.'''
        raise NotImplementedError()
    
    @property
    def blend_mode(self) -> aspose.psd.fileformats.core.blending.BlendMode:
        '''Gets the blending mode.'''
        raise NotImplementedError()
    
    @blend_mode.setter
    def blend_mode(self, value : aspose.psd.fileformats.core.blending.BlendMode) -> None:
        '''Sets the blending mode.'''
        raise NotImplementedError()
    

class NoiseDistribution:
    '''The distribution of noise filter.'''
    
    UNIFORM : NoiseDistribution
    '''The uniform noise distribution.'''
    GAUSSIAN : NoiseDistribution
    '''The gaussian noise distribution.'''

