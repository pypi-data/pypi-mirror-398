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

class BigRectangularFilterOptions(FilterOptionsBase):
    '''Big Rectangular Filter Options'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    

class BilateralSmoothingFilterOptions(FilterOptionsBase):
    '''The Bilateral Smoothing Filter Options.'''
    
    @overload
    def __init__(self, size : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.BilateralSmoothingFilterOptions` class.
        
        :param size: Size of the kernal.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.BilateralSmoothingFilterOptions` class.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the size of the kernel.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the size of the kernel.'''
        raise NotImplementedError()
    
    @property
    def spatial_factor(self) -> float:
        '''Gets the spatial factor.'''
        raise NotImplementedError()
    
    @spatial_factor.setter
    def spatial_factor(self, value : float) -> None:
        '''Sets the spatial factor.'''
        raise NotImplementedError()
    
    @property
    def spatial_power(self) -> float:
        '''Gets the spatial power.'''
        raise NotImplementedError()
    
    @spatial_power.setter
    def spatial_power(self, value : float) -> None:
        '''Sets the spatial power.'''
        raise NotImplementedError()
    
    @property
    def color_factor(self) -> float:
        '''Gets the color factor.'''
        raise NotImplementedError()
    
    @color_factor.setter
    def color_factor(self, value : float) -> None:
        '''Sets the color factor.'''
        raise NotImplementedError()
    
    @property
    def color_power(self) -> float:
        '''Gets the color power.'''
        raise NotImplementedError()
    
    @color_power.setter
    def color_power(self, value : float) -> None:
        '''Sets the color power.'''
        raise NotImplementedError()
    

class ConvolutionFilterOptions(FilterOptionsBase):
    '''The convolution filter.'''
    
    @property
    def factor(self) -> float:
        '''Gets the factor.'''
        raise NotImplementedError()
    
    @factor.setter
    def factor(self, value : float) -> None:
        '''Sets the factor.'''
        raise NotImplementedError()
    
    @property
    def bias(self) -> int:
        '''Gets the bias.'''
        raise NotImplementedError()
    
    @bias.setter
    def bias(self, value : int) -> None:
        '''Sets the bias.'''
        raise NotImplementedError()
    

class DeconvolutionFilterOptions(FilterOptionsBase):
    '''Deconvolution Filter Options, abstract class'''
    
    @property
    def snr(self) -> float:
        '''Gets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @snr.setter
    def snr(self, value : float) -> None:
        '''Sets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @property
    def brightness(self) -> float:
        '''Gets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @brightness.setter
    def brightness(self, value : float) -> None:
        '''Sets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @property
    def grayscale(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @grayscale.setter
    def grayscale(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @property
    def is_partial_loaded(self) -> bool:
        '''Gets a value indicating whether this instance is partial loaded.'''
        raise NotImplementedError()
    

class FilterOptionsBase:
    '''Filter Options Base, abstract class'''
    

class GaussWienerFilterOptions(DeconvolutionFilterOptions):
    '''Gauss Wiener Filter Options
    Deblur gauss'''
    
    @overload
    def __init__(self, radius : int, smooth : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.GaussWienerFilterOptions` class.
        
        :param radius: The radius.
        :param smooth: The smooth.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.GaussWienerFilterOptions` class.
        With default settings.'''
        raise NotImplementedError()
    
    @property
    def snr(self) -> float:
        '''Gets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @snr.setter
    def snr(self, value : float) -> None:
        '''Sets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @property
    def brightness(self) -> float:
        '''Gets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @brightness.setter
    def brightness(self, value : float) -> None:
        '''Sets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @property
    def grayscale(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @grayscale.setter
    def grayscale(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @property
    def is_partial_loaded(self) -> bool:
        '''Gets a value indicating whether this instance is partial loaded.'''
        raise NotImplementedError()
    
    @property
    def radius(self) -> int:
        '''Gets the radius.'''
        raise NotImplementedError()
    
    @radius.setter
    def radius(self, value : int) -> None:
        '''Sets the radius.'''
        raise NotImplementedError()
    
    @property
    def smooth(self) -> float:
        '''Gets the smooth.'''
        raise NotImplementedError()
    
    @smooth.setter
    def smooth(self, value : float) -> None:
        '''Sets the smooth.'''
        raise NotImplementedError()
    

class GaussianBlurFilterOptions(ConvolutionFilterOptions):
    '''The Gaussian blur'''
    
    @overload
    def __init__(self, radius : int, sigma : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.GaussianBlurFilterOptions` class.
        
        :param radius: The radius.
        :param sigma: The sigma.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.GaussianBlurFilterOptions` class.
        With default settings.'''
        raise NotImplementedError()
    
    @property
    def factor(self) -> float:
        '''Gets the factor.'''
        raise NotImplementedError()
    
    @factor.setter
    def factor(self, value : float) -> None:
        '''Sets the factor.'''
        raise NotImplementedError()
    
    @property
    def bias(self) -> int:
        '''Gets the bias.'''
        raise NotImplementedError()
    
    @bias.setter
    def bias(self, value : int) -> None:
        '''Sets the bias.'''
        raise NotImplementedError()
    
    @property
    def radius(self) -> int:
        '''Gets the radius.'''
        raise NotImplementedError()
    
    @radius.setter
    def radius(self, value : int) -> None:
        '''Sets the radius.'''
        raise NotImplementedError()
    
    @property
    def sigma(self) -> float:
        '''Gets the sigma.'''
        raise NotImplementedError()
    
    @sigma.setter
    def sigma(self, value : float) -> None:
        '''Sets the sigma.'''
        raise NotImplementedError()
    

class MedianFilterOptions(FilterOptionsBase):
    '''Median filter'''
    
    def __init__(self, size : int) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.MedianFilterOptions` class.
        
        :param size: The size of filter rectangle.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the size.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the size.'''
        raise NotImplementedError()
    

class MotionWienerFilterOptions(DeconvolutionFilterOptions):
    '''Deconvolution filter options
    deblur motion'''
    
    def __init__(self, length : int, smooth : float, angle : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.MotionWienerFilterOptions` class.
        
        :param length: The length.
        :param smooth: The smooth.
        :param angle: The angle in gradus.'''
        raise NotImplementedError()
    
    @property
    def snr(self) -> float:
        '''Gets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @snr.setter
    def snr(self, value : float) -> None:
        '''Sets the SNR(signal-to-noise ratio)
        recommended range 0.002 - 0.009, default value = 0.007'''
        raise NotImplementedError()
    
    @property
    def brightness(self) -> float:
        '''Gets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @brightness.setter
    def brightness(self, value : float) -> None:
        '''Sets the brightness.
        recommended range 1 - 1.5
        default value = 1.15'''
        raise NotImplementedError()
    
    @property
    def grayscale(self) -> bool:
        '''Gets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @grayscale.setter
    def grayscale(self, value : bool) -> None:
        '''Sets a value indicating whether this :py:class:`aspose.psd.imagefilters.filteroptions.DeconvolutionFilterOptions` is grayscale.
        Return grayscale mode or RGB mode.'''
        raise NotImplementedError()
    
    @property
    def is_partial_loaded(self) -> bool:
        '''Gets a value indicating whether this instance is partial loaded.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length.'''
        raise NotImplementedError()
    
    @length.setter
    def length(self, value : int) -> None:
        '''Sets the length.'''
        raise NotImplementedError()
    
    @property
    def smooth(self) -> float:
        '''Gets the smooth.'''
        raise NotImplementedError()
    
    @smooth.setter
    def smooth(self, value : float) -> None:
        '''Sets the smooth.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the angle in gradus.'''
        raise NotImplementedError()
    
    @angle.setter
    def angle(self, value : float) -> None:
        '''Sets the angle in gradus.'''
        raise NotImplementedError()
    

class SharpenFilterOptions(ConvolutionFilterOptions):
    '''The Sharpen filter options'''
    
    @overload
    def __init__(self, size : int, sigma : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.SharpenFilterOptions` class.
        
        :param size: Size of the kernel.
        :param sigma: The sigma.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imagefilters.filteroptions.SharpenFilterOptions` class.
        With default settings.'''
        raise NotImplementedError()
    
    @property
    def factor(self) -> float:
        '''Gets the factor.'''
        raise NotImplementedError()
    
    @factor.setter
    def factor(self, value : float) -> None:
        '''Sets the factor.'''
        raise NotImplementedError()
    
    @property
    def bias(self) -> int:
        '''Gets the bias.'''
        raise NotImplementedError()
    
    @bias.setter
    def bias(self, value : int) -> None:
        '''Sets the bias.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the size.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the size.'''
        raise NotImplementedError()
    
    @property
    def sigma(self) -> float:
        '''Gets the sigma.'''
        raise NotImplementedError()
    
    @sigma.setter
    def sigma(self, value : float) -> None:
        '''Sets the sigma.'''
        raise NotImplementedError()
    

class SmallRectangularFilterOptions(FilterOptionsBase):
    '''Small rectangular filter options'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    

