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

class WarpSettings:
    '''Parameters of layer with warp'''
    
    @overload
    def __init__(self, mesh_points : List[aspose.psd.PointF], bounds : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.warp.WarpSettings` class.
        
        :param mesh_points: The mesh points of warp
        :param bounds: The bounds of warp image'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, mesh_points : List[aspose.psd.PointF], bounds : aspose.psd.Rectangle, style : aspose.psd.fileformats.psd.layers.warp.WarpStyles) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.warp.WarpSettings` class.
        
        :param mesh_points: The mesh points of warp
        :param bounds: The bounds of warp image
        :param style: The style of warp'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, warp_items : List[aspose.psd.fileformats.psd.layers.layerresources.OSTypeStructure], bounds : aspose.psd.Rectangle) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.warp.WarpSettings` class.
        
        :param warp_items: PS items with warp settings
        :param bounds: The bounds of warp image'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, placed_resource : aspose.psd.fileformats.psd.layers.layerresources.PlacedResource) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.psd.layers.warp.WarpSettings` class.
        
        :param placed_resource: The resource with warp settings'''
        raise NotImplementedError()
    
    @property
    def style(self) -> aspose.psd.fileformats.psd.layers.warp.WarpStyles:
        '''Gets style of warp'''
        raise NotImplementedError()
    
    @style.setter
    def style(self, value : aspose.psd.fileformats.psd.layers.warp.WarpStyles) -> None:
        '''Sets style of warp'''
        raise NotImplementedError()
    
    @property
    def rotate(self) -> aspose.psd.fileformats.psd.layers.warp.WarpRotates:
        '''Gets rotate value'''
        raise NotImplementedError()
    
    @rotate.setter
    def rotate(self, value : aspose.psd.fileformats.psd.layers.warp.WarpRotates) -> None:
        '''Sets rotate value'''
        raise NotImplementedError()
    
    @property
    def value(self) -> float:
        '''Gets value of warp'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : float) -> None:
        '''Sets value of warp'''
        raise NotImplementedError()
    
    @property
    def render_quality(self) -> aspose.psd.fileformats.psd.layers.warp.RenderQuality:
        '''Gets value of warp render quality - between speed and quality'''
        raise NotImplementedError()
    
    @render_quality.setter
    def render_quality(self, value : aspose.psd.fileformats.psd.layers.warp.RenderQuality) -> None:
        '''Sets value of warp render quality - between speed and quality'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.Rectangle:
        '''Gets bounds of warp image'''
        raise NotImplementedError()
    
    @property
    def mesh_points(self) -> List[aspose.psd.PointF]:
        '''Photoshop mesh points'''
        raise NotImplementedError()
    
    @mesh_points.setter
    def mesh_points(self, value : List[aspose.psd.PointF]) -> None:
        '''Photoshop mesh points'''
        raise NotImplementedError()
    
    @property
    def grid_size(self) -> aspose.psd.Size:
        '''Gets the size of the warp grid. Default is 1.'''
        raise NotImplementedError()
    
    @grid_size.setter
    def grid_size(self, value : aspose.psd.Size) -> None:
        '''Sets the size of the warp grid. Default is 1.'''
        raise NotImplementedError()
    

class RenderQuality:
    '''It describes the rendering quality of Warp.'''
    
    TURBO : RenderQuality
    '''The fastest option, but the quality suffers.'''
    VERY_FAST : RenderQuality
    '''If you need it fast, it may be suitable for small curvatures.'''
    FAST : RenderQuality
    '''Allows you to make rendering faster with a small drop in quality.'''
    NORMAL : RenderQuality
    '''Recommended value for most curvatures'''
    GOOD : RenderQuality
    '''Higher than standard quality, slower speed. Recommended for strong distortions.'''
    EXCELLENT : RenderQuality
    '''The slowest option. Recommended for strong distortions and high resolutions.'''

class WarpRotates:
    '''Types of warp rotation'''
    
    HORIZONTAL : WarpRotates
    '''Horizontal warp direction'''
    VERTICAL : WarpRotates
    '''Vertical warp direction'''

class WarpStyles:
    '''Types of support warp styles supported'''
    
    NONE : WarpStyles
    '''It style is set when the layer without deformation'''
    CUSTOM : WarpStyles
    '''Style with arbitrary movement of points'''
    ARC : WarpStyles
    '''Arc style of warp'''
    ARC_UPPER : WarpStyles
    '''Upper Arc style of warp'''
    ARC_LOWER : WarpStyles
    '''Lower Arc style of warp'''
    ARCH : WarpStyles
    '''Arch style of warp'''
    BULGE : WarpStyles
    '''Bulge style of warp'''
    FLAG : WarpStyles
    '''Flag style of warp'''
    FISH : WarpStyles
    '''Fish style of warp'''
    RISE : WarpStyles
    '''Rise style of warp'''
    WAVE : WarpStyles
    '''Wave style of warp'''
    TWIST : WarpStyles
    '''Twist type of warp'''
    SQUEEZE : WarpStyles
    '''Squeeze type of warp'''
    INFLATE : WarpStyles
    '''Inflate type of warp'''

