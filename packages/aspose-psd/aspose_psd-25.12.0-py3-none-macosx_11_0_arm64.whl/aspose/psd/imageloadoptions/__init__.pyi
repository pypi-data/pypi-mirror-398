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

class Jpeg2000LoadOptions(aspose.psd.LoadOptions):
    '''JPEG2000 load options'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.imageloadoptions.Jpeg2000LoadOptions` class.'''
        raise NotImplementedError()
    
    @property
    def data_recovery_mode(self) -> aspose.psd.DataRecoveryMode:
        '''Gets the data recovery mode.'''
        raise NotImplementedError()
    
    @data_recovery_mode.setter
    def data_recovery_mode(self, value : aspose.psd.DataRecoveryMode) -> None:
        '''Sets the data recovery mode.'''
        raise NotImplementedError()
    
    @property
    def data_background_color(self) -> aspose.psd.Color:
        '''Gets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @data_background_color.setter
    def data_background_color(self, value : aspose.psd.Color) -> None:
        '''Sets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @property
    def use_icc_profile_conversion(self) -> bool:
        '''Gets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @use_icc_profile_conversion.setter
    def use_icc_profile_conversion(self, value : bool) -> None:
        '''Sets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @property
    def buffer_size_hint(self) -> int:
        '''Gets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @buffer_size_hint.setter
    def buffer_size_hint(self, value : int) -> None:
        '''Sets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @property
    def maximum_decoding_time(self) -> int:
        '''Gets the maximum decoding time in seconds (this option can be used on very slow on memory machines to prevent hanging on process on very big images - resolution more than 5500x6500 pixels).'''
        raise NotImplementedError()
    
    @maximum_decoding_time.setter
    def maximum_decoding_time(self, value : int) -> None:
        '''Sets the maximum decoding time in seconds (this option can be used on very slow on memory machines to prevent hanging on process on very big images - resolution more than 5500x6500 pixels).'''
        raise NotImplementedError()
    

class PngLoadOptions(aspose.psd.LoadOptions):
    '''The png load options.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def data_recovery_mode(self) -> aspose.psd.DataRecoveryMode:
        '''Gets the data recovery mode.'''
        raise NotImplementedError()
    
    @data_recovery_mode.setter
    def data_recovery_mode(self, value : aspose.psd.DataRecoveryMode) -> None:
        '''Sets the data recovery mode.'''
        raise NotImplementedError()
    
    @property
    def data_background_color(self) -> aspose.psd.Color:
        '''Gets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @data_background_color.setter
    def data_background_color(self, value : aspose.psd.Color) -> None:
        '''Sets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @property
    def use_icc_profile_conversion(self) -> bool:
        '''Gets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @use_icc_profile_conversion.setter
    def use_icc_profile_conversion(self, value : bool) -> None:
        '''Sets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @property
    def buffer_size_hint(self) -> int:
        '''Gets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @buffer_size_hint.setter
    def buffer_size_hint(self, value : int) -> None:
        '''Sets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @property
    def strict_mode(self) -> bool:
        '''Gets a value indicating whether [strict mode].'''
        raise NotImplementedError()
    
    @strict_mode.setter
    def strict_mode(self, value : bool) -> None:
        '''Sets a value indicating whether [strict mode].'''
        raise NotImplementedError()
    

class PsdLoadOptions(aspose.psd.LoadOptions):
    '''Psd load options'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def data_recovery_mode(self) -> aspose.psd.DataRecoveryMode:
        '''Gets the data recovery mode.'''
        raise NotImplementedError()
    
    @data_recovery_mode.setter
    def data_recovery_mode(self, value : aspose.psd.DataRecoveryMode) -> None:
        '''Sets the data recovery mode.'''
        raise NotImplementedError()
    
    @property
    def data_background_color(self) -> aspose.psd.Color:
        '''Gets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @data_background_color.setter
    def data_background_color(self, value : aspose.psd.Color) -> None:
        '''Sets the :py:class:`aspose.psd.Image` background :py:class:`aspose.psd.Color`.'''
        raise NotImplementedError()
    
    @property
    def use_icc_profile_conversion(self) -> bool:
        '''Gets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @use_icc_profile_conversion.setter
    def use_icc_profile_conversion(self, value : bool) -> None:
        '''Sets a value indicating whether ICC profile conversion should be applied.'''
        raise NotImplementedError()
    
    @property
    def buffer_size_hint(self) -> int:
        '''Gets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @buffer_size_hint.setter
    def buffer_size_hint(self, value : int) -> None:
        '''Sets the buffer size hint which is defined max allowed size for all internal buffers.'''
        raise NotImplementedError()
    
    @property
    def load_effects_resource(self) -> bool:
        '''Gets a value indicating whether [load effects resource] (by default resource is not loaded). When set this option only supported effects will be rendered to final merged image.'''
        raise NotImplementedError()
    
    @load_effects_resource.setter
    def load_effects_resource(self, value : bool) -> None:
        '''Sets a value indicating whether [load effects resource] (by default resource is not loaded). When set this option only supported effects will be rendered to final merged image.'''
        raise NotImplementedError()
    
    @property
    def use_disk_for_load_effects_resource(self) -> bool:
        '''Gets a value indicating whether [use disk for load effects resource] (by default used disk to load effects resource, but can be used memory if it is enought by setting this value to false).'''
        raise NotImplementedError()
    
    @use_disk_for_load_effects_resource.setter
    def use_disk_for_load_effects_resource(self, value : bool) -> None:
        '''Sets a value indicating whether [use disk for load effects resource] (by default used disk to load effects resource, but can be used memory if it is enought by setting this value to false).'''
        raise NotImplementedError()
    
    @property
    def read_only_mode(self) -> bool:
        '''Gets a value indicating whether [use read only mode]. This is read-only mode, supported for identical compatibility with Adobe Photoshop.
        When this option is set, all changes applied for layers will not be saved to final image. All data is used from ImageData section, so it is identical to Photoshop.
        By default all loaded images are not identical to Adobe Photoshop compatible.'''
        raise NotImplementedError()
    
    @read_only_mode.setter
    def read_only_mode(self, value : bool) -> None:
        '''Sets a value indicating whether [use read only mode]. This is read-only mode, supported for identical compatibility with Adobe Photoshop.
        When this option is set, all changes applied for layers will not be saved to final image. All data is used from ImageData section, so it is identical to Photoshop.
        By default all loaded images are not identical to Adobe Photoshop compatible.'''
        raise NotImplementedError()
    
    @property
    def read_only_type(self) -> aspose.psd.imageloadoptions.ReadOnlyMode:
        '''Gets the read-only mode used when loading a PSD image.'''
        raise NotImplementedError()
    
    @read_only_type.setter
    def read_only_type(self, value : aspose.psd.imageloadoptions.ReadOnlyMode) -> None:
        '''Sets the read-only mode used when loading a PSD image.'''
        raise NotImplementedError()
    
    @property
    def ignore_text_layer_width_on_update(self) -> bool:
        '''Gets a value indicating whether PSD text layer fixed width will be ignored on UpdateText operation execution.'''
        raise NotImplementedError()
    
    @ignore_text_layer_width_on_update.setter
    def ignore_text_layer_width_on_update(self, value : bool) -> None:
        '''Sets a value indicating whether PSD text layer fixed width will be ignored on UpdateText operation execution.'''
        raise NotImplementedError()
    
    @property
    def ignore_alpha_channel(self) -> bool:
        '''Gets a value indicating whether [ignore alpha channel].'''
        raise NotImplementedError()
    
    @ignore_alpha_channel.setter
    def ignore_alpha_channel(self, value : bool) -> None:
        '''Sets a value indicating whether [ignore alpha channel].'''
        raise NotImplementedError()
    
    @property
    def allow_warp_repaint(self) -> bool:
        '''Gets whether to save with the rendered image, with or without a warp transform.'''
        raise NotImplementedError()
    
    @allow_warp_repaint.setter
    def allow_warp_repaint(self, value : bool) -> None:
        '''Sets whether to save with the rendered image, with or without a warp transform.'''
        raise NotImplementedError()
    
    @property
    def allow_non_changed_layer_repaint(self) -> bool:
        '''Gets whether to preserve original layer pixels during rendering if the layer has not been modified.'''
        raise NotImplementedError()
    
    @allow_non_changed_layer_repaint.setter
    def allow_non_changed_layer_repaint(self, value : bool) -> None:
        '''Sets whether to preserve original layer pixels during rendering if the layer has not been modified.'''
        raise NotImplementedError()
    

class ReadOnlyMode:
    '''Specifies the read-only modes available when loading a PSD image.'''
    
    NONE : ReadOnlyMode
    '''No read-only restrictions are applied.
    The image can be fully modified.'''
    DEFAULT : ReadOnlyMode
    '''Default mode. The image is fully read-only and cannot be modified.'''
    METADATA_EDIT : ReadOnlyMode
    '''Allows editing of image metadata while keeping image content read-only.'''

