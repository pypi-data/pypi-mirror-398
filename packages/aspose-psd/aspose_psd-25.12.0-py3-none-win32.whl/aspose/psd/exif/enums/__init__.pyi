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

class ExifColorSpace:
    '''exif color space enum.'''
    
    S_RGB : ExifColorSpace
    '''SRGB color space.'''
    ADOBE_RGB : ExifColorSpace
    '''Adobe rgb color space.'''
    UNCALIBRATED : ExifColorSpace
    '''Uncalibrated color space.'''

class ExifContrast:
    '''exif normal soft hard enum.'''
    
    NORMAL : ExifContrast
    '''Normal contrast.'''
    LOW : ExifContrast
    '''Low contrast.'''
    HIGH : ExifContrast
    '''High contrast.'''

class ExifCustomRendered:
    '''exif custom rendered enum.'''
    
    NORMAL_PROCESS : ExifCustomRendered
    '''Normal render process.'''
    CUSTOM_PROCESS : ExifCustomRendered
    '''Custom render process.'''

class ExifExposureMode:
    '''exif exposure mode enum.'''
    
    AUTO : ExifExposureMode
    '''Auto exposure.'''
    MANUAL : ExifExposureMode
    '''Manual exposure.'''
    AUTO_BRACKET : ExifExposureMode
    '''Auto bracket.'''

class ExifExposureProgram:
    '''exif exposure program enum.'''
    
    NOTDEFINED : ExifExposureProgram
    '''Not defined.'''
    MANUAL : ExifExposureProgram
    '''Manual program.'''
    AUTO : ExifExposureProgram
    '''Auto exposure.'''
    APERTUREPRIORITY : ExifExposureProgram
    '''Aperture priority.'''
    SHUTTERPRIORITY : ExifExposureProgram
    '''Shutter priority.'''
    CREATIVEPROGRAM : ExifExposureProgram
    '''Creative program.'''
    ACTIONPROGRAM : ExifExposureProgram
    '''Action program.'''
    PORTRAITMODE : ExifExposureProgram
    '''Portrait mode.'''
    LANDSCAPEMODE : ExifExposureProgram
    '''Landscape mode.'''

class ExifFileSource:
    '''exif file source enum.'''
    
    OTHERS : ExifFileSource
    '''The others.'''
    FILM_SCANNER : ExifFileSource
    '''Film scanner.'''
    REFLEXION_PRINT_SCANNER : ExifFileSource
    '''Reflexion print scanner.'''
    DIGITAL_STILL_CAMERA : ExifFileSource
    '''Digital still camera.'''

class ExifFlash:
    '''Flash mode.'''
    
    NOFLASH : ExifFlash
    '''No flash fired.'''
    FIRED : ExifFlash
    '''Flash fired.'''
    FIRED_RETURN_LIGHT_NOT_DETECTED : ExifFlash
    '''Flash fired, return light not detected.'''
    FIRED_RETURN_LIGHT_DETECTED : ExifFlash
    '''Flash fired, return light detected.'''
    YES_COMPULSORY : ExifFlash
    '''Flash fired, compulsory flash mode.'''
    YES_COMPULSORY_RETURN_LIGHT_NOT_DETECTED : ExifFlash
    '''Flash fired, compulsory mode, return light not detected.'''
    YES_COMPULSORY_RETURN_LIGHT_DETECTED : ExifFlash
    '''Flash fired, compulsory mode, return light detected.'''
    NO_COMPULSORY : ExifFlash
    '''Flash did not fire, compulsory flash mode.'''
    NO_DID_NOT_FIRE_RETURN_LIGHT_NOT_DETECTED : ExifFlash
    '''Flash did not fire, return light not detected.'''
    NO_AUTO : ExifFlash
    '''Flash did not fire, auto mode.'''
    YES_AUTO : ExifFlash
    '''Flash firedm auto mode.'''
    YES_AUTO_RETURN_LIGHT_NOT_DETECTED : ExifFlash
    '''Flash fired, auto mode, return light not detected.'''
    YES_AUTO_RETURN_LIGHT_DETECTED : ExifFlash
    '''Flash fired, auto mode, return light detected.'''
    NO_FLASH_FUNCTION : ExifFlash
    '''No flash function.'''

class ExifGPSAltitudeRef:
    '''exif gps altitude ref enum.'''
    
    ABOVE_SEA_LEVEL : ExifGPSAltitudeRef
    '''Above sea level.'''
    BELOW_SEA_LEVEL : ExifGPSAltitudeRef
    '''Below sea level.'''

class ExifGainControl:
    '''exif gain control enum.'''
    
    NONE : ExifGainControl
    '''No gain control.'''
    LOW_GAIN_UP : ExifGainControl
    '''Low gain up.'''
    HIGH_GAIN_UP : ExifGainControl
    '''High gain up.'''
    LOW_GAIN_DOWN : ExifGainControl
    '''Low gain down.'''
    HIGH_GAIN_DOWN : ExifGainControl
    '''High gain down.'''

class ExifLightSource:
    '''The exif light source.'''
    
    UNKNOWN : ExifLightSource
    '''The unknown.'''
    DAYLIGHT : ExifLightSource
    '''The daylight.'''
    FLUORESCENT : ExifLightSource
    '''The fluorescent.'''
    TUNGSTEN : ExifLightSource
    '''The tungsten.'''
    FLASH : ExifLightSource
    '''The flash.'''
    FINEWEATHER : ExifLightSource
    '''The fineweather.'''
    CLOUDYWEATHER : ExifLightSource
    '''The cloudyweather.'''
    SHADE : ExifLightSource
    '''The shade.'''
    DAYLIGHT_FLUORESCENT : ExifLightSource
    '''The daylight fluorescent.'''
    DAY_WHITE_FLUORESCENT : ExifLightSource
    '''The day white fluorescent.'''
    COOL_WHITE_FLUORESCENT : ExifLightSource
    '''The cool white fluorescent.'''
    WHITE_FLUORESCENT : ExifLightSource
    '''The white fluorescent.'''
    STANDARDLIGHT_A : ExifLightSource
    '''The standardlight a.'''
    STANDARDLIGHT_B : ExifLightSource
    '''The standardlight b.'''
    STANDARDLIGHT_C : ExifLightSource
    '''The standardlight c.'''
    D55 : ExifLightSource
    '''The d55 value(5500K).'''
    D65 : ExifLightSource
    '''The d65 value(6500K).'''
    D75 : ExifLightSource
    '''The d75 value(7500K).'''
    D50 : ExifLightSource
    '''The d50 value(5000K).'''
    IS_OSTUDIOTUNGSTEN : ExifLightSource
    '''The iso studio tungsten lightsource.'''
    OTHERLIGHTSOURCE : ExifLightSource
    '''The otherlightsource.'''

class ExifMeteringMode:
    '''exif metering mode enum.'''
    
    UNKNOWN : ExifMeteringMode
    '''Undefined mode'''
    AVERAGE : ExifMeteringMode
    '''Average metering'''
    CENTERWEIGHTEDAVERAGE : ExifMeteringMode
    '''Center weighted average.'''
    SPOT : ExifMeteringMode
    '''Spot metering'''
    MULTI_SPOT : ExifMeteringMode
    '''Multi spot metering'''
    MULTI_SEGMENT : ExifMeteringMode
    '''Multi segment metering.'''
    PARTIAL : ExifMeteringMode
    '''Partial metering.'''
    OTHER : ExifMeteringMode
    '''For other modes.'''

class ExifOrientation:
    '''Exif image orientation.'''
    
    TOP_LEFT : ExifOrientation
    '''Top left. Default orientation.'''
    TOP_RIGHT : ExifOrientation
    '''Top right. Horizontally reversed.'''
    BOTTOM_RIGHT : ExifOrientation
    '''Bottom right. Rotated by 180 degrees.'''
    BOTTOM_LEFT : ExifOrientation
    '''Bottom left. Rotated by 180 degrees and then horizontally reversed.'''
    LEFT_TOP : ExifOrientation
    '''Left top. Rotated by 90 degrees counterclockwise and then horizontally reversed.'''
    RIGHT_TOP : ExifOrientation
    '''Right top. Rotated by 90 degrees clockwise.'''
    RIGHT_BOTTOM : ExifOrientation
    '''Right bottom. Rotated by 90 degrees clockwise and then horizontally reversed.'''
    LEFT_BOTTOM : ExifOrientation
    '''Left bottom. Rotated by 90 degrees counterclockwise.'''

class ExifSaturation:
    '''exif saturation enum.'''
    
    NORMAL : ExifSaturation
    '''Normal saturation.'''
    LOW : ExifSaturation
    '''Low saturation.'''
    HIGH : ExifSaturation
    '''High saturation.'''

class ExifSceneCaptureType:
    '''exif scene capture type enum.'''
    
    STANDARD : ExifSceneCaptureType
    '''Standard scene.'''
    LANDSCAPE : ExifSceneCaptureType
    '''Landscape scene.'''
    PORTRAIT : ExifSceneCaptureType
    '''Portrait scene.'''
    NIGHT_SCENE : ExifSceneCaptureType
    '''Night scene.'''

class ExifSensingMethod:
    '''exif sensing method enum.'''
    
    NOTDEFINED : ExifSensingMethod
    '''Not defined.'''
    ONE_CHIP_COLOR_AREA : ExifSensingMethod
    '''One chip color area.'''
    TWO_CHIP_COLOR_AREA : ExifSensingMethod
    '''Two chip color area.'''
    THREE_CHIP_COLOR_AREA : ExifSensingMethod
    '''Three chip color area.'''
    COLORSEQUENTIALAREA : ExifSensingMethod
    '''Color Sequential area.'''
    TRILINEARSENSOR : ExifSensingMethod
    '''Trilinear sensor.'''
    COLORSEQUENTIALLINEAR : ExifSensingMethod
    '''Color sequential linear sensor.'''

class ExifSubjectDistanceRange:
    '''exif subject distance range enum.'''
    
    UNKNOWN : ExifSubjectDistanceRange
    '''Unknown subject distance range'''
    MACRO : ExifSubjectDistanceRange
    '''Macro range'''
    CLOSE_VIEW : ExifSubjectDistanceRange
    '''Close view.'''
    DISTANT_VIEW : ExifSubjectDistanceRange
    '''Distant view.'''

class ExifUnit:
    '''exif unit enum.'''
    
    NONE : ExifUnit
    '''Undefined units'''
    INCH : ExifUnit
    '''Inch units'''
    CM : ExifUnit
    '''Metric centimeter units'''

class ExifWhiteBalance:
    '''exif white balance enum.'''
    
    AUTO : ExifWhiteBalance
    '''Auto white balance'''
    MANUAL : ExifWhiteBalance
    '''Manual  white balance'''

class ExifYCbCrPositioning:
    '''exif y cb cr positioning enum.'''
    
    CENTERED : ExifYCbCrPositioning
    '''Centered YCbCr'''
    CO_SITED : ExifYCbCrPositioning
    '''Co-sited position'''

