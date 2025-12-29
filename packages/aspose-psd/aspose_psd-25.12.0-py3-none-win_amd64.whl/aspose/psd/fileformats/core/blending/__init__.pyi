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

class BlendMode:
    '''The layer blend mode.'''
    
    NORMAL : BlendMode
    '''Normal blend mode.'''
    DARKEN : BlendMode
    '''Darken blend mode.'''
    LIGHTEN : BlendMode
    '''Lighten blend mode.'''
    HUE : BlendMode
    '''Hue blend mode.'''
    SATURATION : BlendMode
    '''Saturation blend mode.'''
    COLOR : BlendMode
    '''Color blend mode.'''
    LUMINOSITY : BlendMode
    '''Luminosity blend mode.'''
    MULTIPLY : BlendMode
    '''Multiply blend mode.'''
    SCREEN : BlendMode
    '''Screen blend mode.'''
    DISSOLVE : BlendMode
    '''Dissolve blend mode.'''
    OVERLAY : BlendMode
    '''Overlay blend mode.'''
    HARD_LIGHT : BlendMode
    '''Hard light blend mode.'''
    SOFT_LIGHT : BlendMode
    '''Soft light blend mode.'''
    DIFFERENCE : BlendMode
    '''Difference blend mode.'''
    EXCLUSION : BlendMode
    '''Exclusion blend mode.'''
    COLOR_DODGE : BlendMode
    '''Color dodge blend mode.'''
    COLOR_BURN : BlendMode
    '''Color burn blend mode.'''
    LINEAR_BURN : BlendMode
    '''Linear burn blend mode.'''
    LINEAR_DODGE : BlendMode
    '''Linear dodge blend mode.'''
    VIVID_LIGHT : BlendMode
    '''Vivid light blend mode.'''
    LINEAR_LIGHT : BlendMode
    '''Linear light blend mode.'''
    PIN_LIGHT : BlendMode
    '''Pin light blend mode.'''
    HARD_MIX : BlendMode
    '''Hard mix blend mode.'''
    PASS_THROUGH : BlendMode
    '''Pass through blend mode.'''
    DARKER_COLOR : BlendMode
    '''Darker color blend mode.'''
    LIGHTER_COLOR : BlendMode
    '''Lighter color blend mode.'''
    SUBTRACT : BlendMode
    '''Subtract blend mode.'''
    DIVIDE : BlendMode
    '''Divide blend mode.'''
    ABSENT : BlendMode
    '''Blend mode is absent or not set yet.'''

