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

class AiDataSection(aspose.psd.DisposableObject):
    '''The Ai format Data Section'''
    
    def get_data(self) -> str:
        '''Gets the string data.
        
        :returns: The string data of section'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    

class AiFinalizeSection(AiSection):
    '''The Ai format Finalize Section'''
    
    def get_data(self) -> str:
        '''Gets the string data.
        
        :returns: The string data of section'''
        raise NotImplementedError()
    

class AiHeader:
    '''The Adobe illustrator File Header'''
    
    @property
    def creator(self) -> str:
        '''Gets the creator.'''
        raise NotImplementedError()
    
    @creator.setter
    def creator(self, value : str) -> None:
        '''Sets the creator.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets the title.'''
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        '''Sets the title.'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> str:
        '''Gets the creation date.'''
        raise NotImplementedError()
    
    @creation_date.setter
    def creation_date(self, value : str) -> None:
        '''Sets the creation date.'''
        raise NotImplementedError()
    
    @property
    def document_process_colors(self) -> str:
        '''Gets the document process colors.'''
        raise NotImplementedError()
    
    @document_process_colors.setter
    def document_process_colors(self, value : str) -> None:
        '''Sets the document process colors.'''
        raise NotImplementedError()
    
    @property
    def document_proc_sets(self) -> str:
        '''Gets the document proc sets.'''
        raise NotImplementedError()
    
    @document_proc_sets.setter
    def document_proc_sets(self, value : str) -> None:
        '''Sets the document proc sets.'''
        raise NotImplementedError()
    
    @property
    def bounding_box(self) -> aspose.psd.Rectangle:
        '''Gets the bounding box.'''
        raise NotImplementedError()
    
    @bounding_box.setter
    def bounding_box(self, value : aspose.psd.Rectangle) -> None:
        '''Sets the bounding box.'''
        raise NotImplementedError()
    
    @property
    def color_usage(self) -> str:
        '''Gets the color usage.'''
        raise NotImplementedError()
    
    @color_usage.setter
    def color_usage(self, value : str) -> None:
        '''Sets the color usage.'''
        raise NotImplementedError()
    
    @property
    def template_box(self) -> aspose.psd.RectangleF:
        '''Gets the template box.'''
        raise NotImplementedError()
    
    @template_box.setter
    def template_box(self, value : aspose.psd.RectangleF) -> None:
        '''Sets the template box.'''
        raise NotImplementedError()
    
    @property
    def tile_box(self) -> aspose.psd.RectangleF:
        '''Gets the tile box.'''
        raise NotImplementedError()
    
    @tile_box.setter
    def tile_box(self, value : aspose.psd.RectangleF) -> None:
        '''Sets the tile box.'''
        raise NotImplementedError()
    
    @property
    def document_preview(self) -> str:
        '''Gets the document preview.'''
        raise NotImplementedError()
    
    @document_preview.setter
    def document_preview(self, value : str) -> None:
        '''Sets the document preview.'''
        raise NotImplementedError()
    

class AiImage(aspose.psd.Image):
    '''The Adobe Illustrator (AI)  Image.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`aspose.psd.fileformats.ai.AiImage` class.'''
        raise NotImplementedError()
    
    @overload
    def save(self) -> None:
        '''Saves the image data to the underlying stream.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, options : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the object\'s data to the specified file location in the specified file format according to save options.
        
        :param file_path: The file path.
        :param options: The options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use sourse bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase, options_base : aspose.psd.ImageOptionsBase, bounds_rectangle : aspose.psd.Rectangle) -> None:
        '''Saves the image\'s data to the specified stream in the specified file format according to save options.
        
        :param stream: The stream to save the image\'s data to.
        :param options_base: The save options.
        :param bounds_rectangle: The destination image bounds rectangle. Set the empty rectangle for use source bounds.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase) -> None:
        '''Saves the object\'s data to the specified stream.
        
        :param stream: The stream to save the object\'s data to.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_path : str, over_write : bool) -> None:
        '''Saves the object\'s data to the specified file location.
        
        :param file_path: The file path to save the object\'s data to.
        :param over_write: if set to ``true`` over write the file contents, otherwise append will occur.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(file_path : str) -> bool:
        '''Determines whether image can be loaded from the specified file path.
        
        :param file_path: The file path.
        :returns: ``true`` if image can be loaded from the specified file; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(file_path : str, load_options : aspose.psd.LoadOptions) -> bool:
        '''Determines whether image can be loaded from the specified file path and optionally using the specified open options.
        
        :param file_path: The file path.
        :param load_options: The load options.
        :returns: ``true`` if image can be loaded from the specified file; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(stream : io._IOBase) -> bool:
        '''Determines whether image can be loaded from the specified stream.
        
        :param stream: The stream to load from.
        :returns: ``true`` if image can be loaded from the specified stream; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def can_load(stream : io._IOBase, load_options : aspose.psd.LoadOptions) -> bool:
        '''Determines whether image can be loaded from the specified stream and optionally using the specified ``loadOptions``.
        
        :param stream: The stream to load from.
        :param load_options: The load options.
        :returns: ``true`` if image can be loaded from the specified stream; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_file_format(file_path : str) -> aspose.psd.FileFormat:
        '''Gets the file format.
        
        :param file_path: The file path.
        :returns: The determined file format.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_file_format(stream : io._IOBase) -> aspose.psd.FileFormat:
        '''Gets the file format.
        
        :param stream: The stream.
        :returns: The determined file format.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_fitting_rectangle(rectangle : aspose.psd.Rectangle, width : int, height : int) -> aspose.psd.Rectangle:
        '''Gets rectangle which fits the current image.
        
        :param rectangle: The rectangle to get fitting rectangle for.
        :param width: The object width.
        :param height: The object height.
        :returns: The fitting rectangle or exception if no fitting rectangle can be found.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def get_fitting_rectangle(rectangle : aspose.psd.Rectangle, pixels : List[int], width : int, height : int) -> aspose.psd.Rectangle:
        '''Gets rectangle which fits the current image.
        
        :param rectangle: The rectangle to get fitting rectangle for.
        :param pixels: The 32-bit ARGB pixels.
        :param width: The object width.
        :param height: The object height.
        :returns: The fitting rectangle or exception if no fitting rectangle can be found.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(file_path : str, load_options : aspose.psd.LoadOptions) -> aspose.psd.Image:
        '''Loads a new image from the specified file.
        
        :param file_path: The file path to load image from.
        :param load_options: The load options.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(file_path : str) -> aspose.psd.Image:
        '''Loads a new image from the specified file.
        
        :param file_path: The file path to load image from.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(stream : io._IOBase, load_options : aspose.psd.LoadOptions) -> aspose.psd.Image:
        '''Loads a new image from the specified stream.
        
        :param stream: The stream to load image from.
        :param load_options: The load options.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def load(stream : io._IOBase) -> aspose.psd.Image:
        '''Loads a new image from the specified stream.
        
        :param stream: The stream to load image from.
        :returns: The loaded image.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the image.
        
        :param new_width: The new width.
        :param new_height: The new height.
        :param resize_type: The resize type.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the image.
        
        :param new_width: The new width.
        :param new_height: The new height.
        :param settings: The resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize(self, new_width : int, new_height : int) -> None:
        '''Resizes the image. The default :py:attr:`aspose.psd.ResizeType.NEAREST_NEIGHBOUR_RESAMPLE` is used.
        
        :param new_width: The new width.
        :param new_height: The new height.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int) -> None:
        '''Resizes the width proportionally. The default :py:attr:`aspose.psd.ResizeType.NEAREST_NEIGHBOUR_RESAMPLE` is used.
        
        :param new_width: The new width.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_width_proportionally(self, new_width : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the width proportionally.
        
        :param new_width: The new width.
        :param settings: The image resize settings.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, resize_type : aspose.psd.ResizeType) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param resize_type: Type of the resize.'''
        raise NotImplementedError()
    
    @overload
    def resize_height_proportionally(self, new_height : int, settings : aspose.psd.ImageResizeSettings) -> None:
        '''Resizes the height proportionally.
        
        :param new_height: The new height.
        :param settings: The image resize settings.'''
        raise NotImplementedError()
    
    def cache_data(self) -> None:
        '''Caches the data and ensures no additional data loading will be performed from the underlying :py:attr:`aspose.psd.DataStreamSupporter.data_stream_container`.'''
        raise NotImplementedError()
    
    @staticmethod
    def create(image_options : aspose.psd.ImageOptionsBase, width : int, height : int) -> aspose.psd.Image:
        '''Creates a new image using the specified create options.
        
        :param image_options: The image options.
        :param width: The width.
        :param height: The height.
        :returns: The newly created image.'''
        raise NotImplementedError()
    
    def can_save(self, options : aspose.psd.ImageOptionsBase) -> bool:
        '''Determines whether image can be saved to the specified file format represented by the passed save options.
        
        :param options: The save options to use.
        :returns: ``true`` if image can be saved to the specified file format represented by the passed save options; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def get_default_options(self, args : List[Any]) -> aspose.psd.ImageOptionsBase:
        '''Gets the default options.
        
        :param args: The arguments.
        :returns: Default options'''
        raise NotImplementedError()
    
    def get_original_options(self) -> aspose.psd.ImageOptionsBase:
        '''Gets the options based on the original file settings.
        This can be helpful to keep bit-depth and other parameters of the original image unchanged.
        For example, if we load a black-white PNG image with 1 bit per pixel and then save it using the
        :py:func:`aspose.psd.DataStreamSupporter.save` method, the output PNG image with 8-bit per pixel will be produced.
        To avoid it and save PNG image with 1-bit per pixel, use this method to get corresponding saving options and pass them
        to the :py:func:`aspose.psd.Image.save` method as the second parameter.
        
        :returns: The options based on the original file settings.'''
        raise NotImplementedError()
    
    def rotate_flip(self, rotate_flip_type : aspose.psd.RotateFlipType) -> None:
        '''Rotates, flips, or rotates and flips the image.
        
        :param rotate_flip_type: Type of the rotate flip.'''
        raise NotImplementedError()
    
    def set_palette(self, palette : aspose.psd.IColorPalette, update_colors : bool) -> None:
        '''Sets the image palette.
        
        :param palette: The palette to set.
        :param update_colors: if set to ``true`` colors will be updated according to the new palette; otherwise color indexes remain unchanged. Note that unchanged indexes may crash the image on loading if some indexes have no corresponding palette entries.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_proportional_width(width : int, height : int, new_height : int) -> int:
        '''Gets a proportional width.
        
        :param width: The width.
        :param height: The height.
        :param new_height: The new height.
        :returns: The proportional width.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_proportional_height(width : int, height : int, new_width : int) -> int:
        '''Gets a proportional height.
        
        :param width: The width.
        :param height: The height.
        :param new_width: The new width.
        :returns: The proportional height.'''
        raise NotImplementedError()
    
    def add_layer(self, layer : aspose.psd.fileformats.ai.AiLayerSection) -> None:
        '''Adds the AI layer section.
        
        :param layer: The AI layer section.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def data_stream_container(self) -> aspose.psd.StreamContainer:
        '''Gets the object\'s data stream.'''
        raise NotImplementedError()
    
    @property
    def is_cached(self) -> bool:
        '''Gets a value indicating whether object\'s data is cached currently and no data reading is required.'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets the image bits per pixel count.'''
        raise NotImplementedError()
    
    @property
    def bounds(self) -> aspose.psd.Rectangle:
        '''Gets the image bounds.'''
        raise NotImplementedError()
    
    @property
    def container(self) -> aspose.psd.Image:
        '''Gets the :py:class:`aspose.psd.Image` container.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets the image height.'''
        raise NotImplementedError()
    
    @property
    def palette(self) -> aspose.psd.IColorPalette:
        '''Gets the color palette. The color palette is not used when pixels are represented directly.'''
        raise NotImplementedError()
    
    @palette.setter
    def palette(self, value : aspose.psd.IColorPalette) -> None:
        '''Sets the color palette. The color palette is not used when pixels are represented directly.'''
        raise NotImplementedError()
    
    @property
    def use_palette(self) -> bool:
        '''Gets a value indicating whether the image palette is used.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> aspose.psd.Size:
        '''Gets the image size.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets the image width.'''
        raise NotImplementedError()
    
    @property
    def interrupt_monitor(self) -> aspose.psd.multithreading.InterruptMonitor:
        '''Gets the interrupt monitor.'''
        raise NotImplementedError()
    
    @interrupt_monitor.setter
    def interrupt_monitor(self, value : aspose.psd.multithreading.InterruptMonitor) -> None:
        '''Sets the interrupt monitor.'''
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
    def auto_adjust_palette(self) -> bool:
        '''Gets a value indicating whether automatic adjust palette.'''
        raise NotImplementedError()
    
    @auto_adjust_palette.setter
    def auto_adjust_palette(self, value : bool) -> None:
        '''Sets a value indicating whether automatic adjust palette.'''
        raise NotImplementedError()
    
    @property
    def has_background_color(self) -> bool:
        '''Gets a value indicating whether image has background color.'''
        raise NotImplementedError()
    
    @has_background_color.setter
    def has_background_color(self, value : bool) -> None:
        '''Sets a value indicating whether image has background color.'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> aspose.psd.FileFormat:
        '''Gets a value of file format.'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.psd.Color:
        '''Gets a value for the background color.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.psd.Color) -> None:
        '''Sets a value for the background color.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> aspose.psd.fileformats.ai.AiFormatVersion:
        '''Gets the version of Adobe Illustrator format.'''
        raise NotImplementedError()
    
    @property
    def header(self) -> aspose.psd.fileformats.ai.AiHeader:
        '''Gets the header.'''
        raise NotImplementedError()
    
    @property
    def setup_section(self) -> aspose.psd.fileformats.ai.AiSetupSection:
        '''Gets the setup section.'''
        raise NotImplementedError()
    
    @property
    def finalize_section(self) -> aspose.psd.fileformats.ai.AiFinalizeSection:
        '''Gets the finalize section.'''
        raise NotImplementedError()
    
    @property
    def data_section(self) -> aspose.psd.fileformats.ai.AiDataSection:
        '''Gets the data section.'''
        raise NotImplementedError()
    
    @property
    def layers(self) -> List[aspose.psd.fileformats.ai.AiLayerSection]:
        '''Gets the layer sections.'''
        raise NotImplementedError()
    
    @property
    def xmp_data(self) -> aspose.psd.xmp.XmpPacketWrapper:
        '''Gets the XMP metadata.'''
        raise NotImplementedError()
    
    @property
    def active_page_index(self) -> int:
        '''Gets the index of the active page.'''
        raise NotImplementedError()
    
    @active_page_index.setter
    def active_page_index(self, value : int) -> None:
        '''Sets the index of the active page.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''The number of pages.
        For the old AI format images always equal 0.'''
        raise NotImplementedError()
    

class AiLayerSection(AiDataSection):
    '''The Ai format Layer Section'''
    
    def get_data(self) -> str:
        '''Gets the string data.
        
        :returns: The string data of section'''
        raise NotImplementedError()
    
    def add_raster_image(self, raster_image : aspose.psd.fileformats.ai.AiRasterImageSection) -> None:
        '''Adds the raster image.
        
        :param raster_image: The raster image.'''
        raise NotImplementedError()
    
    @property
    def disposed(self) -> bool:
        '''Gets a value indicating whether this instance is disposed.'''
        raise NotImplementedError()
    
    @property
    def is_template(self) -> bool:
        '''Gets a value indicating whether this layer is a template layer.'''
        raise NotImplementedError()
    
    @is_template.setter
    def is_template(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is a template layer.'''
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        '''Gets a value indicating whether this layer is locked.
        Prevents changes to the item.'''
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is locked.
        Prevents changes to the item.'''
        raise NotImplementedError()
    
    @property
    def is_shown(self) -> bool:
        '''Gets a value indicating whether this layer is shown.
        Displays all artwork contained in the layer on the artboard if true.'''
        raise NotImplementedError()
    
    @is_shown.setter
    def is_shown(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is shown.
        Displays all artwork contained in the layer on the artboard if true.'''
        raise NotImplementedError()
    
    @property
    def is_printed(self) -> bool:
        '''Gets a value indicating whether this layer is printed.
        Makes the artwork contained in the layer printable if true.'''
        raise NotImplementedError()
    
    @is_printed.setter
    def is_printed(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is printed.
        Makes the artwork contained in the layer printable if true.'''
        raise NotImplementedError()
    
    @property
    def is_preview(self) -> bool:
        '''Gets a value indicating whether this layer is preview.
        Displays the artwork contained in the layer in color instead of as outlines.'''
        raise NotImplementedError()
    
    @is_preview.setter
    def is_preview(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is preview.
        Displays the artwork contained in the layer in color instead of as outlines.'''
        raise NotImplementedError()
    
    @property
    def is_images_dimmed(self) -> bool:
        '''Gets a value indicating whether this layer is dimmed.
        Reduces the intensity of linked images and bitmap images contained in the layer.'''
        raise NotImplementedError()
    
    @is_images_dimmed.setter
    def is_images_dimmed(self, value : bool) -> None:
        '''Sets a value indicating whether this layer is dimmed.
        Reduces the intensity of linked images and bitmap images contained in the layer.'''
        raise NotImplementedError()
    
    @property
    def dim_value(self) -> int:
        '''Gets the dim value as percentage.
        Reduces the intensity of linked images and bitmap images contained in the layer to the specified percentage.'''
        raise NotImplementedError()
    
    @dim_value.setter
    def dim_value(self, value : int) -> None:
        '''Sets the dim value as percentage.
        Reduces the intensity of linked images and bitmap images contained in the layer to the specified percentage.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the layer name.
        Specifies the name of the item as it appears in the Layers panel.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Sets the layer name.
        Specifies the name of the item as it appears in the Layers panel.'''
        raise NotImplementedError()
    
    @property
    def color_number(self) -> int:
        '''Gets the color number. -1 is the custom color value from Red, Green, Blue properties.
        Specifies the layer’s color setting.'''
        raise NotImplementedError()
    
    @color_number.setter
    def color_number(self, value : int) -> None:
        '''Sets the color number. -1 is the custom color value from Red, Green, Blue properties.
        Specifies the layer’s color setting.'''
        raise NotImplementedError()
    
    @property
    def has_multi_layer_masks(self) -> bool:
        '''Gets a value indicating whether this instance has multilayer masks.'''
        raise NotImplementedError()
    
    @has_multi_layer_masks.setter
    def has_multi_layer_masks(self, value : bool) -> None:
        '''Sets a value indicating whether this instance has multilayer masks.'''
        raise NotImplementedError()
    
    @property
    def color_index(self) -> int:
        '''Gets the index of the color.
        This argument can take on values between –1 and 26. Each integer
        represents a color that can be assigned to the layer for user
        identification purposes.'''
        raise NotImplementedError()
    
    @color_index.setter
    def color_index(self, value : int) -> None:
        '''Sets the index of the color.
        This argument can take on values between –1 and 26. Each integer
        represents a color that can be assigned to the layer for user
        identification purposes.'''
        raise NotImplementedError()
    
    @property
    def red(self) -> int:
        '''Gets the red color component.'''
        raise NotImplementedError()
    
    @red.setter
    def red(self, value : int) -> None:
        '''Sets the red color component.'''
        raise NotImplementedError()
    
    @property
    def green(self) -> int:
        '''Gets the green color component.'''
        raise NotImplementedError()
    
    @green.setter
    def green(self, value : int) -> None:
        '''Sets the green color component.'''
        raise NotImplementedError()
    
    @property
    def blue(self) -> int:
        '''Gets the blue color component.'''
        raise NotImplementedError()
    
    @blue.setter
    def blue(self, value : int) -> None:
        '''Sets the blue color component.'''
        raise NotImplementedError()
    
    @property
    def raster_images(self) -> List[aspose.psd.fileformats.ai.AiRasterImageSection]:
        '''Gets the raster images.'''
        raise NotImplementedError()
    

class AiRasterImageSection:
    '''The AI Raster Image Section'''
    
    @property
    def name(self) -> str:
        '''Gets the name of the raster image.'''
        raise NotImplementedError()
    
    @property
    def pixels(self) -> List[int]:
        '''Gets the array of int color pixels.'''
        raise NotImplementedError()
    
    @property
    def offset_x(self) -> float:
        '''Gets the offset X.'''
        raise NotImplementedError()
    
    @property
    def offset_y(self) -> float:
        '''Gets the offset Y.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets the width.'''
        raise NotImplementedError()
    
    @property
    def angle(self) -> float:
        '''Gets the angle.'''
        raise NotImplementedError()
    
    @property
    def left_bottom_shift(self) -> float:
        '''Gets the left bottom shift.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets the height.'''
        raise NotImplementedError()
    
    @property
    def image_rectangle(self) -> aspose.psd.Rectangle:
        '''Gets the image rectangle.'''
        raise NotImplementedError()
    

class AiSection:
    '''The Ai format base section'''
    
    def get_data(self) -> str:
        '''Gets the string data.
        
        :returns: The string data of section'''
        raise NotImplementedError()
    

class AiSetupSection(AiSection):
    '''The Ai format Setup Section'''
    
    def get_data(self) -> str:
        '''Gets the string data.
        
        :returns: The string data of section'''
        raise NotImplementedError()
    

class AiFormatVersion:
    '''The Adobe Illustrator Version'''
    
    PS_ADOBE_EPSF : AiFormatVersion
    '''The PS-Adobe EPSF Header'''
    PS_ADOBE20 : AiFormatVersion
    '''The PS-Adobe-2.0 Header'''
    PS_ADOBE30 : AiFormatVersion
    '''The PS-Adobe-3.0 Header'''
    PDF14 : AiFormatVersion
    '''The PDF-1.4 Header'''
    PDF15 : AiFormatVersion
    '''The PDF-1.5 Header'''
    PDF16 : AiFormatVersion
    '''The PDF-1.6 Header'''
    PDF17 : AiFormatVersion
    '''The PDF-1.7 Header'''

