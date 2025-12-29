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

class JFIFData:
    '''The jfif segment.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.jpeg.JFIFData` class.'''
        raise NotImplementedError()
    
    @property
    def density_units(self) -> aspose.psd.fileformats.jpeg.JfifDensityUnits:
        '''Gets the density units.'''
        raise NotImplementedError()
    
    @density_units.setter
    def density_units(self, value : aspose.psd.fileformats.jpeg.JfifDensityUnits) -> None:
        '''Sets the density units.'''
        raise NotImplementedError()
    
    @property
    def thumbnail(self) -> aspose.psd.RasterImage:
        '''Gets the thumbnail.'''
        raise NotImplementedError()
    
    @thumbnail.setter
    def thumbnail(self, value : aspose.psd.RasterImage) -> None:
        '''Sets the thumbnail.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> int:
        '''Gets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Sets the version.'''
        raise NotImplementedError()
    
    @property
    def x_density(self) -> int:
        '''Gets the x density.'''
        raise NotImplementedError()
    
    @x_density.setter
    def x_density(self, value : int) -> None:
        '''Sets the x density.'''
        raise NotImplementedError()
    
    @property
    def y_density(self) -> int:
        '''Gets the y density.'''
        raise NotImplementedError()
    
    @y_density.setter
    def y_density(self, value : int) -> None:
        '''Sets the y density.'''
        raise NotImplementedError()
    

class JpegLsPresetCodingParameters:
    '''Defines the JPEG-LS preset coding parameters as defined in ISO/IEC 14495-1, C.2.4.1.1.
    JPEG-LS defines a default set of parameters, but custom parameters can be used.
    When used these parameters are written into the encoded bit stream as they are needed for the decoding process.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def maximum_sample_value(self) -> int:
        '''Gets the maximum possible value for any image sample in a scan.
        This must be greater than or equal to the actual maximum value for the components in a scan.'''
        raise NotImplementedError()
    
    @maximum_sample_value.setter
    def maximum_sample_value(self, value : int) -> None:
        '''Sets the maximum possible value for any image sample in a scan.
        This must be greater than or equal to the actual maximum value for the components in a scan.'''
        raise NotImplementedError()
    
    @property
    def threshold1(self) -> int:
        '''Gets the first quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @threshold1.setter
    def threshold1(self, value : int) -> None:
        '''Sets the first quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @property
    def threshold2(self) -> int:
        '''Gets the second quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @threshold2.setter
    def threshold2(self, value : int) -> None:
        '''Sets the second quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @property
    def threshold3(self) -> int:
        '''Gets the third quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @threshold3.setter
    def threshold3(self, value : int) -> None:
        '''Sets the third quantization threshold value for the local gradients.'''
        raise NotImplementedError()
    
    @property
    def reset_value(self) -> int:
        '''Gets the value at which the counters A, B, and N are halved.'''
        raise NotImplementedError()
    
    @reset_value.setter
    def reset_value(self, value : int) -> None:
        '''Sets the value at which the counters A, B, and N are halved.'''
        raise NotImplementedError()
    

class JfifDensityUnits:
    '''The jfif density units.'''
    
    NO_UNITS : JfifDensityUnits
    '''The no units.'''
    PIXELS_PER_INCH : JfifDensityUnits
    '''The pixels per inch.'''
    PIXELS_PER_CM : JfifDensityUnits
    '''The pixels per cm.'''

class JpegCompressionColorMode:
    '''Сolor mode for jpeg images.'''
    
    GRAYSCALE : JpegCompressionColorMode
    '''The Grayscale image.'''
    Y_CB_CR : JpegCompressionColorMode
    '''YCbCr image, standard option for jpeg images.'''
    CMYK : JpegCompressionColorMode
    '''4-component CMYK image.'''
    YCCK : JpegCompressionColorMode
    '''The ycck color jpeg image. Needs icc profile for saving.'''
    RGB : JpegCompressionColorMode
    '''The RGB Color mode.'''

class JpegCompressionMode:
    '''Compression mode for jpeg images.'''
    
    BASELINE : JpegCompressionMode
    '''The baseline compression.'''
    PROGRESSIVE : JpegCompressionMode
    '''The progressive compression.'''
    LOSSLESS : JpegCompressionMode
    '''The lossless compression.'''
    JPEG_LS : JpegCompressionMode
    '''The JPEG-LS compression.'''

class JpegLsInterleaveMode:
    '''Defines the interleave mode for multi-component (color) pixel data.'''
    
    NONE : JpegLsInterleaveMode
    '''The data is encoded and stored as component for component: RRRGGGBBB.'''
    LINE : JpegLsInterleaveMode
    '''The interleave mode is by line. A full line of each component is encoded before moving to the next line.'''
    SAMPLE : JpegLsInterleaveMode
    '''The data is encoded and stored by sample. For color images this is the format like RGBRGBRGB.'''

class SampleRoundingMode:
    '''Defines a way in which an n-bit value is converted to an 8-bit value.'''
    
    EXTRAPOLATE : SampleRoundingMode
    '''Extrapolate an 8-bit value to fit it into n bits, where 1 < n < 8.
    The number of all possible 8-bit values is 1 << 8 = 256, from 0 to 255.
    The number of all possible n-bit values is 1 << n, from 0 to (1 << n) - 1.
    The most reasonable n-bit value Vn corresponding to some 8-bit value V8 is equal to Vn = V8 >> (8 - n).'''
    TRUNCATE : SampleRoundingMode
    '''Truncate an 8-bit value to fit it into n bits, where 1 < n < 8.
    The number of all possible n-bit values is 1 << n, from 0 to (1 << n) - 1.
    The most reasonable n-bit value Vn corresponding to some 8-bit value V8 is equal to Vn = V8 & ((1 << n) - 1).'''

